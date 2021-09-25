import dash
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css']

app = dash.Dash(__name__, 
	suppress_callback_exceptions=True, 
	external_stylesheets=external_stylesheets
)
server = app.server