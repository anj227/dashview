"""
read_data:  Read data from variaous sources and store it as Panda DataFrame (DF)

Source of data: 
    1) CSV file 
    2) EXCEL 
    3) DB connection:
        3a) MySQL
        3b) Postgress 
        3c) SQLite ..
    4) Parquet file format 

Output: Pandas DF 
"""
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

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
import styles

# Local files..
import read_data as local_read_data
from app import app
from app import server

navbar = html.Nav(className = "nav nav-pills", children=[
        html.A('Rename', className="nav-item nav-link active"),
        html.A('Describe', className="nav-item nav-link")
        ])

LOADED_DF_NAMES = {}  # dict of dict -- keys: df_names, value: {'source_file', 'last_updated'}
ACTIVE_DF = ''
dcc.Store('active_df': '')
dcc.Store('loaded_dfs': '')

LOADED_DFS = dict()

def upload_file():
    return dcc.Upload(
        id='upload-data',
        children=[html.A('Load from files', className="nav-item nav-link active btn")],
        # Allow multiple files to be uploaded
        multiple = False
    )

loaded_names = ""


sidebar = html.Div(
    [
        html.H4("Loaded Data"),
        html.Hr(),
        dbc.Nav(
            [   html.Div(id="div_loaded_dfs", children=[] ),
                html.Div(id='disp_button', children=[]),
                upload_file(),
        
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=styles.SIDEBAR_STYLE,
)

# ##############
# Data analysis options: Using Pandas
# Buttons and Display div.

DATA_ANALYSIS_OPTIONS = html.Div(
    id="div_data_analysis_options", 
    children = [
            # html.Button("Desc", id={'type': 'da_button', 'index': 'da_describe'}),
            # html.Button("Shape", id={'type': 'da_button', 'index': 'da_shape'}),
            # html.Button("Columns", id={'type': 'da_button', 'index': 'da_columns'}),
            html.Nav(className = "nav nav-pills justify-content-right", children=[
                html.A('Desc', className="nav-item nav-link active py-1", 
                    id={'type': 'da_button', 'index': 'da_describe'}),
                html.A('Shape', className="nav-item nav-link py-1", 
                    id={'type': 'da_button', 'index': 'da_shape'}),
                html.A('Columns', className="nav-item nav-link py-1", 
                    id={'type': 'da_button', 'index': 'da_columns'})
                ])

        ]
    )
DATA_RESULTS = html.Div(id='div_data_results', children=[], className='styles.REDBG')
FILENAME = ''
title = f'Data analysis made easy: {FILENAME}'
content = html.Div(id="content_div", 
    children=[
        html.H4(children=title),
        DATA_ANALYSIS_OPTIONS,
        DATA_RESULTS,
        html.Div(id="output-data-upload", children=[])
    ], 
    style=styles.CONTENT_STYLE)

app.layout = html.Div([
    html.Div([sidebar, content])
])

# ##############
# When a new DF is loaded, update the list of loaded data
# Return data to the callback (update_output) to update the left-panel display 

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
            Output(component_id='div_loaded_dfs', component_property='children'),
            Output(component_id='loaded_dfs', component_property='data')
        ],
        Input(component_id='upload-data', component_property='contents'),
        State(component_id='upload-data', component_property='filename'),
        State(component_id='upload-data', component_property='last_modified'),
        State('div_loaded_dfs', 'children'),         
        Input({'type': 'df_button', 'index': ALL}, 'n_clicks'), 
        State('loaded_dfs', 'data')
    )
# Function following immediately (wrapped) will get executed when input changes
def update_output(content, file_name, file_date, loaded_dfs_children, button_clicks, loaded_dfs_data):
    trig = dash.callback_context.triggered[0]
    df_names = ""
    load_files_content = loaded_dfs_children
    df_content = html.Div()
    loaded_dfs_to_store = loaded_dfs_data

    if content is not None:
        if trig['prop_id'].startswith('upload-data.contents'):

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

# ##############
# Main program call

if __name__ == '__main__':
    app.run_server(debug=True)