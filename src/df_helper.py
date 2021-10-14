import pandas as pd 
import json 


def get_json_from_dtype(dft):
    # dft = df.dtypes 
    aj = pd.Series.to_json(dft)
    print(aj)
    return aj

def get_dict_from_saved_json(aj):
    # aj is created from get_json_from_dtype - 
    bb = json.loads(aj)
    xx = {}
    for k in bb:
        xx[k] = bb[k]['name']
    return xx 

def df_to_dict(df):
    df_dict = df.to_dict('records')
    return df_dict

def dict_to_df(di, column_types=None, column_list=None):

    df = pd.DataFrame.from_dict(di)
    
    if column_list is not None:
        # Re-order the columns:
        df = df[column_list]

    if column_types is not None:
        # First convert string (json) to dict 
        dft_dict = get_dict_from_saved_json(column_types)
        print(column_types)
        print(dft_dict)
        df = df.astype(dft_dict)  #.astype({0: float, 1:str})
    print(df)
    print('--^^^^^ in dict_to_df ^^^^^^')
    return df 
