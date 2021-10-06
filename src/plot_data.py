
import dash
from dash import dash_table, html, dcc
import plotly.express as px
import styles

VALID_PLOT_TYPES = ['line', 'scatter', 'bar', 'scatter_matrix']
def get_figure(df, colX=None, colY=None, plot_type='line'):
    cols = list(df.columns)
    if colX is None:
        colX = df.columns[0]
    if colY is None:
        colY = [df.columns[1]]

    print('------ plot type: ', plot_type)
    if plot_type == 'line':
        fig = px.line(df, x=colX, y=colY)
    elif plot_type == 'scatter':
        fig = px.scatter(df, x=colX, y=colY)
    elif plot_type == 'bar':
        fig = px.bar(df, x=colX, y=colY, barmode='group')
    elif plot_type == 'scatter_matrix':
        # px.bar(data_canada, x='year', y='pop')
        fig = px.scatter_matrix(df,
            dimensions=colY, 
            color=colX,
            )
    return fig 

def create_interactive_plot(df, colX=None, colY=None):
    cols = list(df.columns)
    fig = get_figure(df, colX, colY)
    output = html.Div([
        # -- drop down example
        html.Label('Graph Type'),
        dcc.Dropdown(
            id={'type': 'da_plot_input', 'index': 'plot_type'}, 
            options=[ {'label': ptype, 'value': ptype} for ptype in VALID_PLOT_TYPES ],
            value='line',
            multi=False,
            placeholder="Plot Types",
            style=styles.xy_dropdown
            
        ),
        html.Br(),
        html.Label('X-axis'),
        dcc.Dropdown(
            id={'type': 'da_plot_input', 'index': 'x-axis-dropdown'}, 
            options=[ {'label': col, 'value': col} for col in cols ],
            value=df.columns[0],
            multi=False,
            placeholder="X-axis",
            style=styles.xy_dropdown
        ),
        html.Label('Y-axis'),
        dcc.Dropdown(
            id={'type': 'da_plot_input', 'index': 'y-axis-dropdown'}, 
            options=[ {'label': col, 'value': col} for col in cols ],
            value=[df.columns[1]],
            multi=True,
            placeholder="Y-axis",
            style=styles.xy_dropdown
        ),
        
        html.Div(id='x-y-axis-selection-container'),
        # -- End of example 
        dcc.Graph(id='graph_id', figure=fig),
    ])
    return output 
