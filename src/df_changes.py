import dash
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash import dash_table, html, dcc
from dash.exceptions import PreventUpdate

# Local files..

from app import app
from app import server

def provide_column_type_change_options(column_name, column_type):

    available_types = ['Date', 'DateTime', 'Integer', 'Float', 'String']
    if column_type in available_types:
        available_types.remove(column_type)
    opt_comp = dcc.RadioItems(
        id='data_change_options_id',  
        className='px-3',
        options=[  {'label': opt, 'value': opt} for opt in available_types ],
        value=available_types[0], 
        labelStyle = { 'cursor': 'pointer', 'margin-left':'20px', }
    )
    comp = html.Div(
        children=[
            dcc.Textarea(id='column_name', value=column_name, disabled=True, hidden='hidden'),
            html.H5(f"Current data type for {column_name}:  {column_type}"),
            html.P("Choose the new datatype: "),
            html.P(""),
            opt_comp,
            dcc.Textarea(id={'type': 'edit_info_text', 'index': 'column_type_change'}, value='', disabled=True, hidden='hidden'),
            html.Button('Submit', id={'type': 'submit_edits', 'index': 'column_change'}, n_clicks=0),  
            html.Hr(),
        ])
    return comp 

@app.callback(
    Output({'type': 'edit_info_text', 'index': 'column_type_change'}, 'value'),
    Input(component_id='data_change_options_id', component_property='value'),
    State(component_id='column_name', component_property='value'),
    )
def get_updated_option_value(in_value, column_name):
    ret = f'{column_name}, {in_value}' 
    return ret 