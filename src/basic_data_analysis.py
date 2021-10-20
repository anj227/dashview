import io
import dash
from dash import dash_table, html, dcc
from dash.dependencies import Input, Output, State, MATCH, ALL
import plotly.express as px

import numpy as np 
import pandas as pd

import styles
from app import app
import plot_data as plot_data 
import settings as global_settings

def get_column_type(dtype_kind):
    # Mapping ref: https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind
    dtype_kind_mapping = global_settings.DTYPE_MAPPING
    if dtype_kind in list(dtype_kind_mapping.keys()):
        return dtype_kind_mapping[dtype_kind]
    else:
        return '?? Unknown datatype'

def display_table_column_info(df_new):
    dash_table_obj = html.Div(
        id="div_with_column_info",  # ID not userd
        children=[
            html.Div(id='additional_column_info_div', style={'whiteSpace': 'pre-wrap'}),
            dash_table.DataTable(
                id='table_column_info',
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
            dcc.Textarea(id={'type': 'edit_info_text', 'index': 'df_edit'}, 
                value="add_column", disabled=True, hidden='hidden'),
            html.Button('Submit', id={'type': 'submit_edits', 'index': 'df_edit'}, n_clicks=0),  
            # like da_button
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
    df_content = display_table_column_info(df_new)
    return df_content

# From dash website:
def style_row_by_top_values(df, nlargest=2):
    numeric_columns = df.columns
    numeric_columns = numeric_columns.drop(['id', 'index'])

    styles = []
    for i in range(len(df)):
        row = df.loc[i, numeric_columns].sort_values(ascending=False)
        for j in range(nlargest):
            styles.append({
                'if': {
                    'filter_query': '{{id}} = {}'.format(i),
                    'column_id': row.keys()[j]
                },
                'backgroundColor': '#39CCCC',
                'color': 'white'
            })
    first_col_style = {'if': {'column_id': 'index'}, 'backgroundColor': '#EAEAEA','fontWeight': 'bold'}
    styles.append(first_col_style)
    return styles

# {'if': {'filter_query': '{id} = 3', 'column_id': 'sepal_width'}, 
#   'backgroundColor': '#39CCCC', 'color': 'white'}
def style_row_by_value(df, columns_to_exclude=[], value_formatting={}):
    nlargest = 2
    numeric_columns = df.columns
    numeric_columns = numeric_columns.drop(columns_to_exclude)
    
    styles = []
    for i in range(len(df)):     # Going row by row..
        row = df.loc[i, numeric_columns]
        for ks in row.keys():
            row
            styles.append(
                {
                    'if': {'column_id': 'petal_length',"row_index": x},
                    'backgroundColor': '#3D9970','color': 'white'
                } 
                for x in df[df['petal_length']>0.5].id 
            )
    first_col_style = {'if': {'column_id': 'index'}, 'backgroundColor': '#EAEAEA','fontWeight': 'bold'}
    styles.append(first_col_style)
    return styles


def display_df_correlation(df):
    corr_df = df.corr()

    for col in corr_df.columns:
        corr_df[col]=corr_df[col].map('{:,.4f}'.format)
    
    corr_df = corr_df.reset_index()
    
    corr_df['id'] = corr_df.index
    
    columns_to_exclude = ['id', 'index']
    value_formatting = {
        1: {'max': -0.5, 'min': -1, 'bgColor': '#FFAAAA'}, 
        2: {'max':  0.5, 'min': -0.5, 'bgColor': '#AAFFAA'},
        3: {'max':  1.0, 'min': 0.5, 'bgColor': '#AAAAFF'},
    }
    res = dash_table.DataTable(
            data=corr_df.to_dict('records'),
            #columns=[{'name': i, 'id': i, 'deletable': False, 'renamable': False} for i in corr_df.columns],
            columns=[{'name': i, 'id': i} for i in corr_df.columns if i != 'id'],
            fixed_rows={ 'headers': True, 'data': 0 },
            
            style_table={
                'overflow': 'scroll', 'font-size': '0.8em'
            },
            
            style_header={
                'backgroundColor': '#EAEAEA',
                'fontWeight': 'bold'
            },
            #style_data_conditional=style_row_by_value(corr_df, columns_to_exclude, value_formatting),
            style_data_conditional = style_row_by_top_values(corr_df)
        )
    return res 

def display_df_shape(df):
    tup = df.shape
    num_rows = tup[0]
    num_cols = tup[1]
    res = [
        html.P(f"Rows:    {num_rows}" ),
        html.P(f"Columns: {num_cols}" )
    ]
    return res 

def display_df_scatter_matrix(df):
    # Numerical columns
    df_num = df.select_dtypes(include=[np.number], exclude=[np.datetime64, 'datetime']) 
    cols = list(df_num.columns)

    # Non numerical columns:
    df_non_num = df.select_dtypes(exclude=[np.number, np.datetime64, 'datetime'])    
    cols_non_num = list(df_non_num.columns)

    all_cols = list(df.select_dtypes(exclude=[np.datetime64, 'datetime']).columns)
    if len(cols_non_num) > 0:
        colX = cols_non_num[0]
        colY = cols 
    else:
        colX = cols[0]
        colY = cols[1:]

    print(cols, cols_non_num, all_cols)
    fig = px.scatter_matrix(df,
        dimensions=colY,
        color=colX,
        )
    output = html.Div([
        html.Label('Labels'),
        dcc.Dropdown(
            id={'type': 'da_plot_input2', 'index': 'x-axis-dropdown'}, 
            options=[ {'label': col, 'value': col} for col in all_cols ],
            value=colX,
            multi=False,
            placeholder="X-axis",
            style=styles.xy_dropdown
        ),
        dcc.Graph(id='graph_id2', figure=fig),
    ])
    return output 

def get_data_analysis_output(action, df, active_df_name):
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
    elif action == 'Scatter Matrix':
        res = display_df_scatter_matrix(df)
    else:
        res = html.P("Need to perform action: " + action)

    return res 