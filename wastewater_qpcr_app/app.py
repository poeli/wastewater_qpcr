import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from apps import wastewater_qpcr
from uuid import uuid1
import os
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M',
)

ref_url = 'index'
launch_uid = str(uuid1())

# external stylesheets
external_stylesheets = [
    dbc.themes.BOOTSTRAP, 
    dbc.icons.FONT_AWESOME,
]

app = dash.Dash(__name__, 
    external_stylesheets = external_stylesheets,
    suppress_callback_exceptions = True,
    # background_callback_manager=background_callback_manager,
    # long_callback_manager=long_callback_manager,
)

app.title = "Wastewater qPCR"
# app._favicon = "favicon.ico"

# building the navigation bar
dropdown = dbc.DropdownMenu(
    id = "pathogen-menu-id",
    children=[
        dbc.DropdownMenuItem("SARS-CoV-2", href="/"),
    ],
    nav = True,
    in_navbar = True,
    label = "SARS-CoV-2",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        # dbc.Col(html.Img(src="/assets/virus-solid-white.png", height="27px")),
                        dbc.Col([
                            html.Span([
                                    html.I(className="fa-solid fa-droplet"),
                                ],
                                className="me-2",
                                style={"font-size": "1.1rem", "color": "white"}
                            ),
                            dbc.NavbarBrand("LANL Wastewater", className="ml-1")
                        ]),
                    ],
                    align="center",
                ),
                href="/",
                className="text-decoration-none"
            ),
            dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    # right align dropdown menu with ml-auto className
                    [dropdown], className="ml-auto", navbar=True
                ),
                id="navbar-collapse2",
                navbar=True,
            ),
            html.Div([
                dcc.Dropdown(
                    id="selected-uuid-id",
                    options=[{'label': 'test', 'value': 'test'}],
                    placeholder="Results selection",
                    style={'width': '15rem'},
                    className='small',
                )],
                className='d-flex'
            ),
        ]
    ),
    color="dark",
    dark=True,
    className='w-100 fixed-top container-fluid',
)

# embedding the navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh='callback-nav'),
    navbar,
    html.Div(id='page-content'),
])

#### callback
@callback(
    Output('page-content', 'children'),
    [
        Input('url', 'pathname'),
        Input('url', 'search'),
    ],
)
def display_page(pathname, search):

    if pathname == '/' or pathname == '/#':
        return wastewater_qpcr.layout
    else:
        return "404"

# clientside_callback(
#     """
#     function(uuid) {
#         if (uuid != 'undefined'){
#             window.location.href = "/LANL Wastewater?uuid="+uuid
#         }
#     }
#     """,
#     Output('clientside-callback-temp', 'data'),
#     Input('selected-uuid-id', "value"),
#     prevent_initial_call=True
# )

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", 
                   port=8765,
                   threaded=False,
                   debug=False, 
                   use_reloader=False
                  )
