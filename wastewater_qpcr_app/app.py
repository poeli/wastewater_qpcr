import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

# External stylesheets
external_stylesheets = [
    dbc.themes.BOOTSTRAP, 
    dbc.icons.FONT_AWESOME,
    'assets/styles.css'
]

# Initialize Dash app
app = dash.Dash(__name__, 
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    prevent_initial_callbacks="initial_duplicate",
    use_pages=True
)

app.title = "Wastewater qPCR"
server = app.server

if __name__ == '__main__':
    # Disable debug mode to avoid pkgutil.find_loader error in Python 3.14+
    app.run(debug=False, port=8765)