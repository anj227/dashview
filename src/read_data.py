

import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
from dash import html, dash_table, dcc
import plotly.express as px
import pandas as pd

def generate_table(dataframe, max_rows=1000):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])

def display_dash_table(dataframe, max_rows=10):
    n_rows = dataframe.shape[0]
    n = min(n_rows, max_rows)   # get the number of rows to display..
    df = dataframe.head(n)
    return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        )

def load_data(contents, filename, date):
    content_type, content_string = contents.split(',')
    error_string = ""
    decoded = base64.b64decode(content_string)
    df = pd.DataFrame()
    try:
        if '.csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif '.xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif '.ods' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        error_string="Error loading data.. "
    return df

def parse_contents(df, filename, date):
    print('Trying to parse at load time..')
    max_lines = 10
    return html.Div([
        html.P('File name: ' + filename  + ' Modified at: ' + str(datetime.datetime.fromtimestamp(date)) ),
        display_dash_table(df, max_lines),

        html.Hr(),  # horizontal line
    ])

