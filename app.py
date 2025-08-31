import os
import dash
from dash import html

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Hello Dash"),
    html.Div("Dash: A web application framework for Python.")
])

if __name__ == '__main__':
    port = int(os.environ.get('DASH_APP_PORT', '8050'))
    app.run(debug=True, port=port)
