

import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
from dash import html, dash_table, dcc
import plotly.express as px
import pandas as pd


# Local files..
import styles

def display_dash_table(dataframe, max_rows=1000):
    n_rows = dataframe.shape[0]
    n = min(n_rows, max_rows)   # get the number of rows to display..
    df = dataframe.head(n)
    print('--- Column order in display_dash_table: ')
    print(df.columns)
    print('--------')
    return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i, 'deletable': True, 'renamable': False} for i in df.columns],
            fixed_rows={ 'headers': True, 'data': 0 },
            # For data export: 
            # export_format='xlsx',
            # export_headers='display',
            # merge_duplicate_headers=True,

            page_size=30,
            page_action="native",
            page_current= 0,

            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="single",  # Multi
            
            # column_selectable="single",
            # row_selectable="multi",
            # row_deletable=True,
            # selected_columns=[],
            # selected_rows=[],
            
            style_table={
                'height': '70%', 'overflow': 'scroll', 'font-size': '0.8em'
            },
            style_data={
                'width': '150px', 'minWidth': '150px', 'maxWidth': '150px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },

            style_header={
                'backgroundColor': '#EAEAEA',
                'fontWeight': 'bold'
            },
            # Stripped row:
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#FAFAFA'
                }
            ],
        )

def load_data(contents, filename, date):
    content_type, content_string = contents.split(',')
    error_string = ""
    decoded = base64.b64decode(content_string)
    df = pd.DataFrame()
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'ods' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        error_string="Error loading data.. "
    return df

def remove_df(current_df_info, current_df_content, delete_df_name):
    # Mark df info inactive, and set content to None 
    for indx, cc in enumerate(current_df_info):
        if cc == delete_df_name:
            cc_info = current_df_info[cc]
            if cc_info['active_status']:
                current_df_info[cc]['active_status'] = False
                current_df_content[cc] = None  #  TODO: Should completely remove the ref..
    return current_df_info, current_df_content

def parse_contents(df, filename, date):
    max_lines = 1000
    txt = 'File name: ' + filename  
    if date is not None:
        txt += ', Modified at: ' + str(datetime.datetime.fromtimestamp(date))
    print('DF in parse_contents: ')
    print(df.columns)
    print(df.dtypes)
    print('----------')
    return html.Div([
        html.P(txt, style=styles.INFO_TEXT ),
        display_dash_table(df, max_lines),

        html.Hr(),  # horizontal line
    ])

