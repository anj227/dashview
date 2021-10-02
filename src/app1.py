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

# Local files..
import styles
import callbacks 
import read_data as local_read_data
from app import app
from app import server

ENV = 'development'

# ***
# Sidebar / Left-side pane
# ***

def upload_file():
    return dcc.Upload(
        id='upload-data',
        children=[html.A('Load from files', className="nav-item nav-link active btn btn-sm")],
        multiple = False
    )

title = 'Data analysis made easy:'
sidebar = html.Div(
    [
        html.H5(children=title),
        html.Hr(),
        html.P("Loaded DataFrames"),
        dbc.Nav(
            [   html.Div(id="div_loaded_dfs", children=[] ),
                html.Div(id='disp_button', children=[]),
                html.Hr(),
                upload_file(),
        
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=styles.SIDEBAR_STYLE,
)



# ***
# Content pane
# ***


# ##############
# Data analysis options: Using Pandas
# Buttons and Display div.
DATA_ANALYSIS_OPTIONS = html.Div(
    id="div_data_analysis_options", 
    children = [
            html.Nav(className = "nav nav-pills justify-content-right", children=[
                html.A('Data', className="nav-item nav-link active py-1", 
                    id={'type': 'da_button', 'index': 'da_do_nothing'}),
                html.A('Plot', className="nav-item nav-link py-1", 
                    id={'type': 'da_button', 'index': 'da_Plot'}),
                html.A('Shape', className="nav-item nav-link py-1", 
                    id={'type': 'da_button', 'index': 'da_shape'}),
                html.A('Columns', className="nav-item nav-link py-1", 
                    id={'type': 'da_button', 'index': 'da_columns'}),
                html.A('Edit', className="nav-item nav-link py-1", 
                    id={'type': 'da_button', 'index': 'da_edits'}),
                html.A('Delete', className="nav-item nav-link py-1", 
                    id='df_delete')
                ])
        ]
    )
DF_RESULTS = html.Div(id='div_data_results', children=[] )  # , style=styles.RedBorder
DF_COLUMN_RESULTS = html.Div(id='div_df_col_results', children=[] )  # , style=styles.RedBorder
content = html.Div(id="content_div", 
    children=[
        DATA_ANALYSIS_OPTIONS,
        html.Hr(),
        DF_RESULTS,
        DF_COLUMN_RESULTS,
        html.Div(id="output-data-upload", children=[])
    ], 
    style=styles.CONTENT_STYLE)

# ***
# Whole App
# ***

app.layout = html.Div([
    html.Div([sidebar, content]),

    # dcc.Store inside the app that stores the intermediate value
    dcc.Store(id='loaded_df_info', storage_type='local'),
    dcc.Store(id='loaded_df_content', storage_type='local'),   # , storage_type='session'
    dcc.Store(id='active_df_name', storage_type='local'),
    dcc.Store(id='active_df_content', storage_type='local'),
    dcc.Store(id='edit_ops', storage_type='local'),
])


# ##############
# Main program call

if __name__ == '__main__':
    if ENV == 'development':
        app.run_server(debug=True, port=8050)
    else:
        app.run_server(host='127.0.0.1', port='47518', proxy=None, debug=False, 
            dev_tools_ui=None, dev_tools_props_check=None, dev_tools_serve_dev_bundles=None, 
            dev_tools_hot_reload=None, dev_tools_hot_reload_interval=None, 
            dev_tools_hot_reload_watch_interval=None, dev_tools_hot_reload_max_retry=None, 
            dev_tools_silence_routes_logging=None, dev_tools_prune_errors=None)
    