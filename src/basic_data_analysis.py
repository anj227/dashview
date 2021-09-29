import io
import dash
from dash import dash_table, html, dcc
import styles
import numpy as np 
import pandas as pd
import plotly.express as px

def get_column_type(dtype_kind):
    print(dtype_kind)
    # Mapping ref: https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind
    dtype_kind_mapping = {
        'b': 'Boolean',
        'i': 'Signed Integer', 
        'u': 'Unsigned Integer',
        'f': 'Float',
        'c': 'Complex Float',
        'm': 'Time Delta',
        'M': 'DateTime',
        'O': 'String',        # Is object same as String?
        'S': 'Byte String',
        'U': 'Unicode',
        'V': 'Void',
    }
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

def create_interactive_plot(df):

    cols = list(df.columns)
    col1 = df.columns[0]
    col2 = df.columns[1]
    fig = px.scatter(df, x=col1, y=col2)
    output = html.Div([
        # -- drop down example
        dcc.Dropdown(
            id='x-axis-dropdown',
            options=[ {'label': col, 'value': col} for col in cols ],
            multi=False,
            placeholder="X-axis",
            style=styles.xy_dropdown
        ),
        html.Div(id='x-axis-selection-container'),
        dcc.Dropdown(
            id='y-axis-dropdown',
            options=[ {'label': col, 'value': col} for col in cols ],
            multi=True,
            placeholder="Y-axis",
            style=styles.xy_dropdown
        ),
        html.Div(id='y-axis-selection-container'),
        # -- End of example 
        dcc.Graph(figure=fig),
    ])
    return output 

def get_data_analysis_output(action, df):
    print(df)
    print('----------')
    if action == 'da_shape':
        tup = df.shape
        num_rows = tup[0]
        num_cols = tup[1]
        res = [
            html.P(f"Rows:    {num_rows}" ),
            html.P(f"Columns: {num_cols}" )
        ]
        return res 
    elif action == 'da_columns':
        # Get a list of columns - 
        # For each column, get the total non-null values 
        # 
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
    elif action == 'da_Plot':
        interactive_plot = create_interactive_plot(df)
        return interactive_plot
    else:
        return html.P("Need to perform action: " + action)
