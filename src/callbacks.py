# ##############
# When a new DF is loaded, update the list of loaded data
# Return data to the callback (update_output) to update the left-panel display 


import base64
import datetime
import io
import json

import dash
from dash.dependencies import Input, Output, State, MATCH, ALL
import dash_bootstrap_components as dbc
from dash import html, dash_table, dcc
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd

# Local files..
import styles
import callbacks 
import read_data as local_read_data
from app import app
from app import server


LOADED_DF_NAMES = {}  # dict of dict -- keys: df_names, value: {'source_file', 'last_updated'}
ACTIVE_DF = ''
LOADED_DFS = dict()


def update_loaded_files_navContent(loaded_dfs_children, new_df_name):
    print(loaded_dfs_children)
    ids = []
    for i in range(len(loaded_dfs_children)):
        df_id = loaded_dfs_children[i]['props']['children']
        if df_id is not None:
            ids.append(df_id)
    print(ids)
    if new_df_name not in ids:
        new_comp = html.Button(new_df_name, id={'type': 'df_button', 'index': f'submit_{new_df_name}'} )
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
            chosen_df_name = tmp_json['index'].replace('submit_', '')
    return chosen_df_name

def refresh_DF_display(clicks):
    trig = dash.callback_context.triggered[0]
    # sample output:  {'prop_id': 'submit_nothing.n_clicks', 'value': 2}
    new_df = ''
    if trig != '':
        prop = trig['prop_id']
        if prop != '.':
            tmp_b = prop.replace('.n_clicks', '')
            tmp_json = json.loads(tmp_b)
            new_df = tmp_json['index'].replace('submit_', '')
    
    df_temp = LOADED_DFS[new_df]
    add_info = LOADED_DF_NAMES[new_df]
    file_name = add_info['source_file']
    file_date = add_info['last_updated']

    df_content = [local_read_data.parse_contents(df_temp, file_name, file_date)]
    return df_content

# ##############
# Callback for changing output of data analysis steps

@app.callback(
    Output(component_id='div_data_results', component_property='children'),
    Input({'type': 'da_button', 'index': ALL}, 'n_clicks')
    )
# Function to execute: 
def update_data_analysis_results(button_clicks):
    trig = dash.callback_context.triggered[0]
    print(trig)
    res = html.P("I know... I need to refresh some results here.." + str(trig))
    return res 


# New callbacks:
# 1. load_data --> triggers when upload-data is changed 
#       --> results into changing stored values of loaded_df_info
# 2. Change in loaded_df_info triggers definition of active_df 
#       --> active_df can also change when df selection is changed 
# 3. When active_df is changed 
#       --> changes the display on the output-data-upload (display_data)
# 4. When da_buttons are clicked, or if active_df is changed
#       --> changes output of data analysis window.
# 
# ##############
# Callback for loading new data:
@app.callback(
        [ 
            Output('loaded_df_info', 'data'),
            Output('loaded_df_content', 'data')
        ],
        Input(component_id='upload-data', component_property='contents'),
        State(component_id='upload-data', component_property='filename'),
        State(component_id='upload-data', component_property='last_modified'),
        Input('loaded_df_info', 'data'),
        Input('loaded_df_content', 'data')
    )
def upload_new_data(content, file_name, file_date, current_df_info, current_df_content):
    # First backup 
    trig = dash.callback_context.triggered[0]

    new_df_name = 'df_0'
    new_df_content = {}
    new_df_info = {}
    if current_df_info is not None:
        new_df_name = f'df_{len(current_df_info)}'
        new_df_content = current_df_content
        new_df_info = current_df_info
    
    if trig['prop_id'].startswith('upload-data.contents'):
        if content is not None:
            # Load data first and then parse it..

            df_temp = local_read_data.load_data(content, file_name, file_date)
            new_df_content[new_df_name] = df_temp.to_dict('records')
            if not df_temp.empty:
                new_df_info[new_df_name] = {
                        'source_file': file_name, 
                        'last_updated': file_date
                    }
            
    return current_df_info, current_df_content

# Callback for changing what is an active DF 
@app.callback(
        Output('active_df_name', 'data'),
        Input('loaded_df_info', 'data'), 
        Input({'type': 'df_button', 'index': ALL}, 'n_clicks'), 
    )
def update_active_df_name(current_df_info, button_clicks):
    # Assume you need to display last updated value.
    trig = dash.callback_context.triggered[0]
    print(trig)
    print('----- what triggered it ^^^-------')
    print(button_clicks)
    print('---- button clicks -----')
    latest_df_name = None 
    if '"type":"df_button"' in trig['prop_id']:
        # Data didn't change -- only the click on the DF name..
        latest_df_name = get_active_df_name_from_button(button_clicks)
    else:
        if current_df_info is not None: 
            print(current_df_info)
            latest_df_name = list(current_df_info.keys())[-1]
    print('Latest df name: ', latest_df_name)
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
    if active_df_name is not None: 
        df_dict = current_df_content[active_df_name]
        df_temp = pd.DataFrame.from_dict(df_dict)
        if not df_temp.empty:
            df_info = current_df_info[active_df_name]
            file_name = df_info['source_file']
            file_date = df_info['last_updated']
            df_content = [local_read_data.parse_contents(df_temp, file_name, file_date)]
        
    return df_content

# Update div_loaded_dfs as new DFs are loaded..
@app.callback(
        Output(component_id='div_loaded_dfs', component_property='children'),
        Input('active_df_name', 'data'),
        State('div_loaded_dfs', 'children'),         
    )
def update_displayed_df_list(active_df_name, loaded_dfs_children):
    # Assume you need to display last updated value.
    df_content = html.Div()
    load_files_content = loaded_dfs_children

    if active_df_name is not None: 
        load_files_content = update_loaded_files_navContent(loaded_dfs_children, active_df_name)
        
    return load_files_content
# ##############
# Callback for Uploading a file, or changing the Displayed data (Active DF)

