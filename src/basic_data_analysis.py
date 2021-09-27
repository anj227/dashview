import io
import dash
from dash import dash_table, html
import styles
import numpy as np 
import pandas as pd

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
            data_type = 'tmp Integer' # df[col].dtypes
            # Additional data to display: mean(), max(), min(), distinct()
            all_lines.append([col, null_val_count, data_type])

        my_array = np.array(all_lines)
        df_columns = ['Column Name', 'Null Count',  'Data type']
        df_new = pd.DataFrame(my_array, columns = df_columns)
        df_content = dash_table.DataTable(
            data=df_new.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_new.columns]
        )
        return df_content
    else:
        return html.P("Need to perform action: " + action)
