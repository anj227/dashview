# ##############
# When a new DF is loaded, update the list of loaded data
# Return data to the callback (update_output) to update the left-panel display 

# Remove most of print statements -- getting cluttered.

import base64
import datetime
from time import gmtime, strftime
import io
import json
from pandas.io.json import dumps

import dash
from dash.dependencies import Input, Output, State, MATCH, ALL
import dash_bootstrap_components as dbc
from dash import html, dash_table, dcc
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd

# Local files..
import styles
import read_data as local_read_data
import plot_data as plot_data 
import basic_data_analysis as bda
import settings as global_settings
import df_changes as dfc
import df_helper as dfh 
from app import app
from app import server



LOADED_DF_NAMES = {}  # dict of dict -- keys: df_names, value: {'source_file', 'last_updated'}
ACTIVE_DF = ''
LOADED_DFS = dict()


DEBUG = True 
def debug(*args):
    if DEBUG:
        print(*args)



def get_df_button_comp(button_df_name, source_data=None):
    button_display_name = button_df_name
    # Add file name to the display, if available.
    if source_data is not None and source_data != "":
        button_display_name += f" ({source_data})"
    
    
    comp = html.Button(button_display_name, 
            id={'type': 'df_button', 'index': f'submit_{button_df_name}'},
            className=f'{button_df_name} btn btn-sm  w-100 text_align_left',
        )
    
    return comp 

def get_df_from_current_content(current_df_content, active_df_name, current_df_info=None):
    df_temp = pd.DataFrame()
    if active_df_name is not None:
        if active_df_name != "":

            df_dict = current_df_content[active_df_name]

            # Convert dict to DF 
            column_types = None
            column_list = None 
            if current_df_info is not None:
                column_types = current_df_info[active_df_name]['saved_column_types']
                column_list = current_df_info[active_df_name]['saved_column_list']

            df_temp = dfh.dict_to_df(df_dict, column_types, column_list)

    return df_temp

def update_loaded_files_navContent(loaded_dfs_children, new_df_name):
    ids = []
    for i in range(len(loaded_dfs_children)):
        df_id = loaded_dfs_children[i]['props']['children']
        if df_id is not None:
            ids.append(df_id)
    if new_df_name not in ids:
        new_comp = get_df_button_comp(new_df_name)
        if loaded_dfs_children is None:
            loaded_dfs_children = [new_comp]
        else:
            loaded_dfs_children.append(new_comp)
        loaded_dfs_children.append( html.Hr() )
    return loaded_dfs_children

# ##############
# Based on the button related to DF names pressed, get the DF name and info, and display content
# Return data to the callback (update_output) to update the display 
def get_active_df_name_from_button(clicks):

    trig = dash.callback_context.triggered[0]
    # sample output:  {'prop_id': 'submit_nothing.n_clicks', 'value': 2}
    chosen_df_name = None 
    if trig != '':
        prop = trig['prop_id']
        if prop != '.':
            tmp_b = prop.replace('.n_clicks', '')
            tmp_json = json.loads(tmp_b)
            value = trig['value']
            if value is not None:
                chosen_df_name = tmp_json['index'].replace('submit_', '')
            
    return chosen_df_name
    
## Change instructions for data changes
@app.callback(
    Output(component_id='edit_ops', component_property='data'),
    Input({'type': 'submit_edits', 'index': ALL}, 'n_clicks'),
    State({'type': 'edit_info_text', 'index': ALL}, 'value'),
    # Input(component_id='ops_type', component_property='value'),  # IS this used anymore??
    prevent_initial_call=True
    )
def update_edit_ops_info(clicks, in_value): # ops_type
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trig = dash.callback_context.triggered[0]
    # Trigger only when submit is clicked.. ignore changes to input text..
    
    trig_prop_id = trig['prop_id']
    if trig_prop_id is None or trig_prop_id == '':
        raise PreventUpdate

    if 'column_change' in trig_prop_id and clicks != [0]:
        col_info = in_value[0]
        cc = col_info.split(',')
        col_name = cc[0].strip()
        col_type = cc[1].strip()
        new_val = {'ops': 'change_column', 'column_name': col_name, 'new_type': col_type}
        
        return new_val
    elif 'df_edit' in trig_prop_id:
        # hard-coded right now.
        new_val = {'ops': 'new_column', 'new_name': 'daily_diff', 'operation': 'df_0.high - df_0.low'}
        
        return new_val
    else:
        raise PreventUpdate

# New callbacks:
# 1. load_data --> triggers when upload-data is changed 
#       --> results into changing stored values of loaded_df_info
# 2. Change in loaded_df_info triggers definition of active_df 
#       --> active_df can also change when df selection is changed 
# 3. When active_df is changed 
#       --> changes the display on the output-data-upload (display_data)
#       --> change the da_output
# 4. When da_buttons are clicked, or if active_df is changed
#       --> changes output of data analysis window.
# 
# ##############
# Callback for loading new data:
@app.callback(
        [ 
        Output('loaded_df_info', 'data'),
        Output('loaded_df_content', 'data'),
        Output(component_id='upload-data', component_property='contents'),
        ],
        Input(component_id='upload-data', component_property='contents'),
        State(component_id='upload-data', component_property='filename'),
        State(component_id='upload-data', component_property='last_modified'),
        State('loaded_df_info', 'data'),          # Changed from input --> state
        State('loaded_df_content', 'data'),        
        Input(component_id='edit_ops', component_property='data'),
        Input(component_id='df_delete', component_property='n_clicks'),
        State('active_df_name', 'data')
    )
def upload_new_data(content, file_name, file_date, current_df_info, current_df_content, 
        edit_ops, delete_click, active_df_name):
    # First backup 
    trig = dash.callback_context.triggered[0]
    trig_prop_id = trig['prop_id']
    n = 0
    new_df_name = f'df_{n}'
    new_df_content = {}
    new_df_info = {}
    edit_ops_to_do = {}
    time_now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    if current_df_info is not None:
        n = len(current_df_info)
        new_df_name = f'df_{n}'
        new_df_content = current_df_content
        new_df_info = current_df_info
    
    if trig_prop_id.startswith('upload-data.contents'):
        if content is not None:
            # Load data first and then parse it..
            df_temp = local_read_data.load_data(content, file_name, file_date)
            
            if not df_temp.empty:
                new_df_content[new_df_name] = dfh.df_to_dict(df_temp)
                new_df_info[new_df_name] = {
                        'source_file': file_name, 
                        'last_updated': file_date,
                        'data_load_counter': n,
                        'active_status': True,
                        'last_df_updated': time_now,
                        'saved_column_list': df_temp.columns,
                        'saved_column_types': dfh.get_json_from_dtype(df_temp.dtypes)
                    }
            return new_df_info, new_df_content,  None

    elif "df_delete" in trig_prop_id:
        if active_df_name is not None:
            new_df_info, new_df_content = local_read_data.remove_df(current_df_info, current_df_content, active_df_name)
            return new_df_info, new_df_content, None
        else:
            raise PreventUpdate

    elif "edit_ops.data" in trig_prop_id:
        df_temp = get_df_from_current_content(current_df_content, active_df_name, current_df_info)
        if not df_temp.empty:
            value = trig['value']
            if value is not None:
                if value['ops'] == 'new_column':
                
                    df_temp = df_temp.assign(open_close = df_temp.Open - df_temp.Close)
                    new_df_content[active_df_name] = dfh.df_to_dict(df_temp)
                    new_df_info[active_df_name]['saved_column_list'] = df_temp.columns
                    new_df_info[active_df_name]['saved_column_types'] = dfh.get_json_from_dtype(df_temp.dtypes)
                    new_df_info[active_df_name]['last_df_updated'] = time_now
                    return new_df_info, new_df_content, None
                elif value['ops'] == 'change_column':
                    df_temp['Date'] = pd.to_datetime(df_temp['Date'], infer_datetime_format=True)
                    new_df_content[active_df_name] = dfh.df_to_dict(df_temp)
                    new_df_info[active_df_name]['saved_column_types'] = dfh.get_json_from_dtype(df_temp.dtypes)
                    new_df_info[active_df_name]['last_df_updated'] = time_now
                    return new_df_info, new_df_content, None
        else:
            raise PreventUpdate

    #if new_df_content == current_df_info:        
    # For all other cases..
    raise PreventUpdate
    # 

# Callback for changing what is an active DF 
@app.callback(
        Output('active_df_name', 'data'),
        Input('loaded_df_info', 'data'), 
        Input({'type': 'df_button', 'index': ALL}, 'n_clicks'), 
        State('active_df_name', 'data'),
    )
def update_active_df_name(current_df_info, button_clicks, current_active_df_name):
    # Assume you need to display last updated value.
    trig = dash.callback_context.triggered[0]
    latest_df_name = None 
    trig_prop_id = trig['prop_id']
    if 'loaded_df_info.data' in trig_prop_id:
        if current_df_info is not None and current_df_info != {}: 
            # Info is changed -- get the latest df:
            n = len(current_df_info)
            max_counter = -1
            for ci in current_df_info:
                cc = current_df_info[ci]
                if cc['active_status'] and cc['data_load_counter'] > max_counter:
                    latest_df_name = ci
                    max_counter = cc['data_load_counter']
                    latest_df_name = ci

    elif '"type":"df_button"' in trig_prop_id:
        # Data didn't change -- only the click on the DF name..
        #if n_clicks is None:
        #    raise PreventUpdate
        #else:
        button_clicked = False 
        for indx, cc in enumerate(button_clicks):
            if cc is not None:
                button_clicked = True 
        if button_clicked: 
            latest_df_name = get_active_df_name_from_button(button_clicks)
        else:
            latest_df_name = current_active_df_name
    else:
        if current_active_df_name is not None:
            latest_df_name = current_active_df_name
    return latest_df_name
    

# Change the displayed values if active_df is changed:
@app.callback(
        Output(component_id='output-data-upload', component_property='children'),
        Input('active_df_name', 'data'),
        State('loaded_df_info', 'data'),
        State('loaded_df_content', 'data')
    )
def update_df_display(active_df_name, current_df_info, current_df_content):
    # Assume you need to display last updated value.
    
    df_content = html.Div()
    #if active_df_name is not None: 
    #    df_dict = current_df_content[active_df_name]
    #    df_temp = pd.DataFrame.from_dict(df_dict)[list (df_dict[0].keys())]
    df_temp = get_df_from_current_content(current_df_content, active_df_name, current_df_info)
    if not df_temp.empty:
        df_info = current_df_info[active_df_name]
        file_name = df_info['source_file']
        file_date = df_info['last_updated']
        df_content = [local_read_data.parse_contents(df_temp, file_name, file_date)]
    else:
        print('df_temp is empty..')
    return df_content

# Update div_loaded_dfs as new DFs are loaded..
@app.callback(
        Output(component_id='div_loaded_dfs', component_property='children'),
        Input('loaded_df_info', 'data'),
        State(component_id='div_loaded_dfs', component_property='children'),
        
    )
def update_displayed_df_list(current_df_info, current_displayed_df): 
    # Assume you need to display last updated value.
    df_content = []

    if current_df_info is None:
        raise PreventUpdate

    
    
    for df_name in current_df_info:
        df_info = current_df_info[df_name]
        if df_info['active_status']:
            file_source = df_info['source_file']
            new_comp = get_df_button_comp(df_name, file_source)
            df_content.append(new_comp)
    
    return df_content

# ##############
# Callback for changing output of data analysis steps

@app.callback(
    Output(component_id='div_data_results', component_property='children'),
    Input({'type': 'da_button', 'index': ALL}, 'n_clicks'),
    Input({'type': 'da_radio_item', 'index': ALL}, 'value'),
    # Input("da_options", "value"),
    State('loaded_df_content', 'data'),
    State('loaded_df_info', 'data'),
    Input('active_df_name', 'data')
    )
# Function to execute: 
def update_data_analysis_results(button_clicks, da_options, current_df_content, current_df_info, active_df_name):
    trig = dash.callback_context.triggered[0]
    action = ""
    trig_prop_id = trig['prop_id']
    mapped_buttons = global_settings.MAPPED_BUTTONS
    for btn in mapped_buttons:
        if btn in trig_prop_id:
            action = btn 
    
    if "da_radio_item" in trig_prop_id:
        val = trig['value']
        valid_values = global_settings.DA_OPTIONS
        if val in valid_values: 
            action = val 
    res = html.P("")
    if trig_prop_id != '.':
        if 'active_df_name.data' in trig_prop_id:
            return res    # Blank out the output..
        elif action != "":
            df_temp = get_df_from_current_content(current_df_content, active_df_name, current_df_info)
            if not df_temp.empty:
                res = bda.get_data_analysis_output(action, df_temp, active_df_name)

    return res

# #################
# Callback for refreshing the plot.. Input: x or y-axis changes

@app.callback(
    # Output(component_id='x-y-axis-selection-container', component_property='children'),
    Output(component_id='graph_id', component_property='figure'),
    Input({'type': 'da_plot_input', 'index': ALL}, 'value'),
        State('loaded_df_content', 'data'),
        State('active_df_name', 'data'),
        State('loaded_df_info', 'data'),
    )
# Function to execute: 
def update_plot(dropdown_value, current_df_content, active_df_name, current_df_info):
    trig = dash.callback_context.triggered[0]
    if trig['prop_id'] != '.':
        json_string = trig['prop_id'].replace('.value', '')
        jz = json.loads(json_string)
        dropdown_id = jz['index']
        df_temp = get_df_from_current_content(current_df_content, active_df_name, current_df_info)
        plot_type = dropdown_value[0]
        colX = dropdown_value[1]
        colY = dropdown_value[2]
        if not df_temp.empty:
            
            fig = plot_data.get_figure(df_temp, colX, colY, plot_type)
        return fig
    else:    
        # Don't do anything..
        raise PreventUpdate   


@app.callback(
    Output('additional_column_info_div', 'children'),
    Input('table_column_info', 'active_cell'),
    State('table_column_info', 'data'),
    State('loaded_df_content', 'data'),
    State('loaded_df_info', 'data'),
    State('active_df_name', 'data')
)
def display_click_data(active_cell, table_data, current_df_content, current_df_info, active_df_name):
    # Expected table row content: {'Column Name': 'High', 'Data type': 'Float', 'Null Count': '0'}
    # For displaying more information about a specific column data clicked.
    if active_cell:
        cell = json.dumps(active_cell, indent=2)    
        row = active_cell['row']
        col = active_cell['column_id']
        value = table_data[row][col]
        
        column_name = table_data[row]['Column Name']
        column_type = table_data[row]['Data type']

        if active_cell['column'] == 2:
            txt1 = 'Current data type: ' + column_type
            # Add options.
            comp = dfc.provide_column_type_change_options(column_name, column_type)
            return comp 
        else:
            
            df_temp = get_df_from_current_content(current_df_content, active_df_name, current_df_info)
            if not df_temp.empty:
                dd = df_temp[column_name].describe().to_dict()
                out = '%s\n------\n' % (value)

                for key in dd.keys():
                    out += '%s: %s \n' % (key, dd[key])
            else:
                out = '%s\n%s' % (cell, value)
    else:
        out = '' # 'no cell selected'
    return out

# To activate buttons..
@app.callback(
    Output({'type': 'da_button', 'index': ALL}, "className"),
    Input({'type': 'da_button', 'index': ALL}, 'n_clicks'),
    State({'type': 'da_button', 'index': ALL}, "className"),
)
def set_active(n_clicks, current_classes):
    trig = dash.callback_context.triggered[0]
    prop_id = trig['prop_id']
    if prop_id == '.':
        raise PreventUpdate
    else:
        tmp_b = prop_id.replace('.n_clicks', '')
        tmp_json = json.loads(tmp_b)
        button_clicked = tmp_json['index']

        new_classes = []
        for btn_classes in current_classes:
            cls = btn_classes.split(' ')
            if button_clicked in cls: 
                if 'active' not in cls: 
                    cls.append('active')
            else:
                if 'active' in cls: 
                    cls.remove('active')
            class_string = " ".join(cls)
            new_classes.append(class_string)
        return new_classes 


@app.callback(
    Output({'type': 'df_button', 'index': ALL}, "className"),
    Input('active_df_name', 'data'),
    State({'type': 'df_button', 'index': ALL}, "className"),
)
def set_active_df_button(active_df_name, current_classes):
    # 
    active_class = 'btn-info' # 'btn-info'
    inactive_class = 'btn-light' # 'btn-light'

    trig = dash.callback_context.triggered[0]
    prop_id = trig['prop_id']
    if active_df_name is None:
        raise PreventUpdate
    if prop_id == '.':
        raise PreventUpdate
    else:
        new_classes = []
        for df_cls in current_classes:
            cls = df_cls.split(' ')
            if active_df_name in cls:
                if active_class not in cls:
                    cls.append(active_class)
                if inactive_class in cls:
                    cls.remove(inactive_class)
            else:
                if active_class in cls:
                    cls.remove(active_class)
                if inactive_class not in cls:
                    cls.append(inactive_class)
            class_string = " ".join(cls)
            new_classes.append(class_string)
        return new_classes







