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



# ***
# Sidebar / Left-side pane
# ***

def upload_file():
    return dcc.Upload(
        id='upload-data',
        children=[html.A('Load from files', className="nav-item nav-link active btn")],
        multiple = False
    )

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

title = 'Data analysis made easy:'
content = html.Div(id="content_div", 
    children=[
        html.H4(children=title),
        html.Hr(),
        DATA_ANALYSIS_OPTIONS,
        DATA_RESULTS,
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
])


# ##############
# Main program call

if __name__ == '__main__':
    app.run_server(debug=True)