import io
import dash
from dash import dash_table, html, dcc
from dash.dependencies import Input, Output, State, MATCH, ALL

import numpy as np 
import pandas as pd

import styles
from app import app
import plot_data as plot_data 
import settings as global_settings

def get_column_type(dtype_kind):
    # print(dtype_kind)
    # Mapping ref: https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind
    dtype_kind_mapping = global_settings.DTYPE_MAPPING
    if dtype_kind in list(dtype_kind_mapping.keys()):
        return dtype_kind_mapping[dtype_kind]
    else:
        return '?? Unknown datatype'

def get_table_with_clickable_data(df_new):
    dash_table_obj = html.Div(
        id="div_with_column_info",
        children=[
            html.Div(id='click-data', style={'whiteSpace': 'pre-wrap'}),
            dash_table.DataTable(
                id='table',
                data=df_new.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df_new.columns]
            ),
        ]
    )
    return dash_table_obj

def display_df_edit_options(df):
    # Right now do it for adding column based on some math..
    cols = df.columns
    example_text = ""
    if len(cols) > 1:
        example_text = f"New_Column = {cols[0]} + {cols[1]}"
    else:
        example_text = f"New_Column = 2 * {cols[0]} "
    res = html.Div( id = 'get_edit_options_div',
        children = [
            html.P("Provide formula in terms of existing columns: "),
            html.P("Example: "),
            html.P(example_text),
            dcc.Textarea(
                id="new_column_formula_txt", 
                value="",
                placeholder = "Formula",
                style={'width': '100%', 'height': "2em"},
            ),
            html.Button('Submit', id='new_column_formula_txt_button', n_clicks=0),
            html.Hr()
        ])
    return res 

def display_additional_da_options():
    options = global_settings.DA_OPTIONS
    comp = dcc.RadioItems(
        id={'type': 'da_radio_item', 'index': 'da_radio_item'},
        className='px-3',
        options=[  {'label': opt, 'value': opt} for opt in options ],
        value=options[0], 
        labelStyle = { 'cursor': 'pointer', 'margin-left':'20px', }
    )
    return comp 

def display_df_column_info(df):
    cols = df.columns 
    all_lines = []
    for col in cols: 
        null_val_count = df[col].isna().sum()
        data_type = get_column_type(df[col].dtypes.kind)
        # Additional data to display: mean(), max(), min(), distinct()
        all_lines.append([col, null_val_count, data_type])

    my_array = np.array(all_lines)
    df_columns = ['Column Name', 'Null Count',  'Data type']
    df_new = pd.DataFrame(my_array, columns = df_columns)
    df_content = get_table_with_clickable_data(df_new)
    return df_content

def display_df_correlation(df):
    corr = df.corr()
    corr = corr.reset_index()

    return dash_table.DataTable(
            data=corr.to_dict('records'),
            columns=[{'name': i, 'id': i, 'deletable': False, 'renamable': False} for i in corr.columns],
            fixed_rows={ 'headers': True, 'data': 0 },
            
            style_table={
                'overflow': 'scroll', 'font-size': '0.8em'
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

def display_df_shape(df):
    tup = df.shape
    num_rows = tup[0]
    num_cols = tup[1]
    res = [
        html.P(f"Rows:    {num_rows}" ),
        html.P(f"Columns: {num_cols}" )
    ]
    return res 

def get_data_analysis_output(action, df):
    #print(df)
    #print('----------')
    print(action)
    if action == 'Shape':
        res = display_df_shape(df)
    elif action == 'da_columns':
        res = display_df_column_info(df)
    elif action == 'da_Plot':
        res = plot_data.create_interactive_plot(df)
    elif action =='da_options':
        res = display_additional_da_options()
    elif action == 'da_edits':
        res = display_df_edit_options(df)
    elif action == 'Correlation':
        res = display_df_correlation(df)
    else:
        res = html.P("Need to perform action: " + action)

    return res 