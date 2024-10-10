#!/usr/bin/env python
import pandas as pd
import logging
import os

import plotly.express as px
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, State, Input, Output, set_props, Patch, no_update, callback, ctx
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M',
)

ref_url = 'index'

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

server = app.server

app.title = "Wastewater qPCR"
# app._favicon = "favicon.ico"


layout_config = {}

# loading
# launch_uid = None
# launch_uid = str(uuid1())
df1 = pd.DataFrame()
df1_std = pd.DataFrame()
df2 = pd.DataFrame()

SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': '4em',
    'left': 0,
    'bottom': 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow-y": "scroll",
}

# the style arguments for the main content page.
CONTENT_STYLE = {
    'marginTop': '4rem',
    "marginLeft": "10rem",
    "marginRight": "10rem",
    "padding": "2rem 1rem",
}

TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#191970'
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9'
}


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

# # define the modal. In this case it only shows the progress bar and a cancel button
# modal = dbc.Modal(
#             [
#                 dbc.ModalHeader(
#                     dbc.ModalTitle("Running analysis"),
#                     close_button=False
#                     # ^^ important, otherwise the user can close the modal
#                     #    but the callback will be running still
#                 ),
#                 dbc.ModalBody([
#                     dbc.Progress(
#                         value=0, id="modal-progress-bar-id", animated=True, striped=True
#                     ),
#                 ]),
#                 dbc.ModalFooter(
#                     dbc.Button(
#                         "Cancel",
#                         id="modal-cancel-analysis-btn-id",
#                         className="ms-auto",
#                         n_clicks=0
#                     )
#                 )
#             ],
#             id="modal-run-analysis-id",
#             is_open=False,
#             backdrop="static",
#             keyboard=True
#             # ^^ important, otherwise the user can close the modal via the ESC button
#             #    but the callback will be running still
#         )

viz_layout = html.Div(
    [
        html.Div(
            [
                html.H4(
                    "Concentration of SARS-CoV-2 in LANL wastewater",
                    className="mr-3",
                    style={'display':'inline-block'}
                ),
                html.P(
                    "Live qPCR Daily Trend. F1: RNA extracted from unconcentrated WW, just 1 ml of WW from the sample we collect that day. F2: RNA extracted from the pellet fraction from centrifuging WW. F3: RNA extracted from the filter that the supernatant from centrifuging WW passed through."
                ),
                html.Div([
                    dbc.Row(
                        [
                            dbc.Col([
                                        html.Span("Choose fraction"),
                                        dcc.Dropdown(
                                            id="chart1-f-id",
                                            options=[],
                                            searchable=False,
                                            multi=True
                                        ),
                                    ],width=12, lg=11
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(id="chart1-graph-id"), width=12, lg=12
                            ),
                        ],
                    )],
                    className="mt-3"
                )
            ],
            style=CONTENT_STYLE
        ),
        html.Div(
            [
                html.H4(
                    "SARS-CoV-2 concentration normalized against the PMMoV concentration",
                    className="mr-3",
                    style={'display':'inline-block'}
                ),
                html.P(
                    "PPMoV qPCR Daily Trend. F1: RNA extracted from unconcentrated WW, just 1 ml of WW from the sample we collect that day. F2: RNA extracted from the pellet fraction from centrifuging WW. F3: RNA extracted from the filter that the supernatant from centrifuging WW passed through."
                ),
                html.Div([
                    dbc.Row(
                        [
                            dbc.Col([
                                        html.Span("Choose fraction"),
                                        dcc.Dropdown(
                                            id="chart2-f-id",
                                            options=[],
                                            searchable=False,
                                            multi=True
                                        ),
                                    ],width=12, lg=11
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(id="chart2-graph-id"), width=12, lg=12
                            ),
                        ],
                    )],
                    className="mt-1"
                )
            ],
            style=CONTENT_STYLE
        ),
    ]
)

# embedding the navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh='callback-nav'),
    navbar,
    viz_layout,
])

# functions
def process_data(data_file, std_file=None):
    df = pd.DataFrame()

    if os.path.exists(data_file):
        df = pd.read_csv(data_file, sep='\t')
        df = df.set_index('DATE').unstack().reset_index().rename(columns={'DATE': 'Fraction', 'level_0': 'Date', 0: 'Value'})
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y').dt.strftime('%Y-%m-%d')
        df.fillna(0, inplace=True)

    if std_file and os.path.exists(std_file):
        df_std = pd.read_csv(std_file, sep='\t')
        df_std = df_std.set_index('DATE').unstack().reset_index().rename(columns={'DATE': 'Fraction', 'level_0': 'Date', 0: 'Value'})
        df_std['Date'] = pd.to_datetime(df_std['Date'], format='%m/%d/%y').dt.strftime('%Y-%m-%d')
        df_std.fillna(0, inplace=True)
        df = df.merge(df_std, on=['Date', 'Fraction'], how='left', suffixes=('', '_std'))

    return df

# init
@callback(
        Output('chart1-f-id', 'options'),
        Output('chart1-f-id', 'value'),
        Output('chart2-f-id', 'options'),
        Output('chart2-f-id', 'value'),
        [
            Input('url', 'pathname'),
        ],
)
def init_page(pathname):
    global layout_config, df1, df1_std, df2
    import json

    # Load the JSON layout configuration file
    with open('assets/data/layout.json', 'r') as file:
        layout_config = json.load(file)

    logging.debug(layout_config)

    # Define file paths based on the layout configuration
    config1 = layout_config[0]
    config2 = layout_config[1]

    # df1
    data_file = config1['plot_data_tsv']
    std_file = config1['plot_std_tsv']
    df1 = process_data(data_file, std_file)

    # df2
    data_file = config2['plot_data_tsv']
    df2 = process_data(data_file)

    return df1['Fraction'].unique().tolist(), df1['Fraction'].unique().tolist(), df2['Fraction'].unique().tolist(), df2['Fraction'].unique().tolist()


# Update figure 1 based on JSON configuration
@callback(
    Output('chart1-graph-id', 'figure'),
    [Input('chart1-f-id', 'value')],
)
def update_figure1(chart1_f):
    global df1, layout_config

    config1 = layout_config[0]

    logging.debug(f"[data][update_figure1] chart1_f: {chart1_f}")

    if chart1_f:
        idx = df1['Fraction'].isin(chart1_f)
    else:
        idx = df1['Date'].notna()
        
    fig = px.line(df1[idx], 
                  x='Date', 
                  y='Value', 
                  error_y="Value_std",
                  title=config1["plot_title"], 
                  color='Fraction',
                  height=700,
                  template='ggplot2')

    fig.update_layout(yaxis_title=config1["plot_yaxis_title"], xaxis_title=config1["plot_xaxis_title"])
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(label="ALL", step="all")
            ]
        ),
        rangeslider=dict(visible=True, thickness=0.1),
        type="date"
    )
    fig.update_traces(error_y_color="#AAAAAA", error_y_width=0.04, mode="markers+lines")
    fig.update_layout(hovermode="x unified")

    return fig

# Update figure 2 based on JSON configuration
@callback(
    Output('chart2-graph-id', 'figure'),
    [Input('chart2-f-id', 'value')],
)
def update_figure2(chart2_f):
    global df2, layout_config

    config2 = layout_config[1]

    logging.debug(f"[data][update_figure2] chart2_f: {chart2_f}")

    if chart2_f:
        idx = df2['Fraction'].isin(chart2_f)
    else:
        idx = df2['Date'].notna()
        
    fig = px.line(df2[idx], 
                  x='Date', 
                  y='Value', 
                  title=config2["plot_title"], 
                  color='Fraction',
                  height=700,
                  template='ggplot2')

    fig.update_layout(yaxis_title=config2["plot_yaxis_title"], xaxis_title=config2["plot_xaxis_title"])
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(label="ALL", step="all")
            ]
        ),
        rangeslider=dict(visible=True, thickness=0.1),
        type="date"
    )
    fig.update_traces(error_y_color="#AAAAAA", error_y_width=0.04, mode="markers+lines")
    fig.update_layout(hovermode="x unified")

    return fig
if __name__ == '__main__':
    app.run_server(host="127.0.0.1", 
                   port=8765,
                   threaded=False,
                   debug=False, 
                   use_reloader=False
                  )
