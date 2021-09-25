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

# ######### To do: Change global variables to dcc.Store data 
# To change 
# LOADED_DF_NAMES -- dict of dict 
# ACTIVE_DF 
# LOADED_DFS  --> Rename to LOADED_DFS_CONTENT 
# 


LOADED_DF_NAMES = {}  # dict of dict -- keys: df_names, value: {'source_file', 'last_updated'}
ACTIVE_DF = ''
# dcc.Store('active_df': '')
# dcc.Store('loaded_dfs': '')

LOADED_DFS = dict()


def update_loaded_files_navContent(loaded_dfs_children, new_df_name):
    
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


# ##############
# Callback for Uploading a file, or changing the Displayed data (Active DF)

@app.callback(
        [Output(component_id='output-data-upload', component_property='children'),
            Output(component_id='div_loaded_dfs', component_property='children')
        ],
        Input(component_id='upload-data', component_property='contents'),
        State(component_id='upload-data', component_property='filename'),
        State(component_id='upload-data', component_property='last_modified'),
        State('div_loaded_dfs', 'children'),         
        Input({'type': 'df_button', 'index': ALL}, 'n_clicks')
    )
# Function following immediately (wrapped) will get executed when input changes
def update_output(content, file_name, file_date, loaded_dfs_children, button_clicks):
    trig = dash.callback_context.triggered[0]
    df_names = ""
    load_files_content = loaded_dfs_children
    df_content = html.Div()
    if trig['prop_id'].startswith('upload-data.contents'):

        if content is not None:
            # Load data first and then parse it..

            n = len(LOADED_DF_NAMES)
            new_df_name = 'df_' + str(n)
            LOADED_DFS[new_df_name] = local_read_data.load_data(content, file_name, file_date)
            df_temp = LOADED_DFS[new_df_name]

            if not df_temp.empty:
                LOADED_DF_NAMES[new_df_name] = {
                    'source_file': file_name, 
                    'last_updated': file_date
                }

            if not df_temp.empty:
                df_content = [local_read_data.parse_contents(df_temp, file_name, file_date)]
                # Add the new DF to the list of 'Loaded Data'
                load_files_content = update_loaded_files_navContent(loaded_dfs_children, new_df_name)
            else:
                df_content = html.P(error_string)
                # The list of 'Loaded Data' is unchanged
                load_files_content = loaded_dfs_children
    else:
        if button_clicks != []:
            
            df_content = refresh_DF_display(button_clicks)
    return df_content, load_files_content
