#!/usr/bin/env python
import pandas as pd
import logging
import os
import json
import time

import plotly.express as px
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, State, Input, Output, callback, ctx, Patch

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M',
)

ref_url = 'index'

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
)

app.title = "Wastewater qPCR"
server = app.server

# Define styles
CONTENT_STYLE = {
    'marginTop': '4rem',
    "marginLeft": "10rem",
    "marginRight": "10rem",
    "padding": "2rem 1rem",
}

# Define navigation bar
dropdown = dcc.Dropdown(
        id="pathogen-menu-id",
        className="me-2",
        options=[
            {'label': 'all pathogens', 'value': 'all pathogens'}
        ],
        value='all pathogens',
        placeholder="all pathogens",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
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
                    [dropdown], className="ml-auto", navbar=True
                ),
                id="navbar-collapse2",
                navbar=True,
            ),
            html.Div([
                "Updated on ",
                html.Span(id='update-time-id')
                ],
                className='d-flex'
            ),
        ]
    ),
    color="dark",
    dark=True,
    className='w-100 fixed-top container-fluid',
)

# Dynamically generate visualization layout based on layout_config
viz_layout_children = []
data_frames = {}  # To store data frames for each graph
latest_update_times = []  # To track latest update times for all data files
check_files = []

# Load layout configuration from JSON
layout_config_file = 'assets/data/layout.json'
try:
    with open(layout_config_file, 'r') as file:
        layout_config = json.load(file)
    logging.info(f"Loaded layout configuration from {layout_config_file}")
except Exception as e:
    logging.error(f"Failed to load layout configuration: {e}")
    layout_config = []


# Function to process data
def process_data(data_file, std_file=None):
    df = pd.DataFrame()

    try:
        df = pd.read_csv(data_file, sep='\t')
        df = df.set_index('DATE').unstack().reset_index().rename(
            columns={'DATE': 'Fraction', 'level_0': 'Date', 0: 'Value'}
        )
        df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce').dt.strftime('%Y-%m-%d')
        df = df[df['Date'].notnull()].reset_index(drop=True)
        df.fillna(0, inplace=True)
        logging.info(f"Processed data: {data_file} {df.shape} {df.tail()}")
    except Exception as err:
        logging.error(f"Error processing data file {data_file}: {err}")
        raise

    if std_file and os.path.exists(std_file):
        try:
            df_std = pd.read_csv(std_file, sep='\t')
            df_std = df_std.set_index('DATE').unstack().reset_index().rename(columns={'DATE': 'Fraction', 'level_0': 'Date', 0: 'Value'})
            df_std['Date'] = pd.to_datetime(df_std['Date'], format='mixed', errors='coerce').dt.strftime('%Y-%m-%d')
            df_std = df_std[df_std['Date'].notnull()].reset_index(drop=True)
            df_std.fillna(0, inplace=True)
            df = df.merge(df_std, on=['Date', 'Fraction'], how='left', suffixes=('', '_std'))
            logging.info(f"Processed data: {std_file} {df.shape} {df.tail()}")
        except Exception as err:
            logging.error(f"Error processing std file {std_file}: {err}")
    
    return df

for idx, config in enumerate(layout_config):
    data_file = config['plot_data_tsv']
    std_file = config.get('plot_std_tsv')
    check_files.extend([data_file, std_file] if std_file else [data_file])
    
    # Process data
    try:
        df = process_data(data_file, std_file)
        data_frames[idx] = df
    except Exception as e:
        logging.error(f"Failed to process data for graph {idx+1}: {e}")

    # check if the data exist
    if not idx in data_frames:
        logging.error(f"Skipping config {idx+1}")
        continue
    
    # Append each graph's layout to viz_layout_children
    block_id = f"chart{idx+1}-block-id"
    graph_id = f"chart{idx+1}-graph-id"
    dropdown_id = f"chart{idx+1}-f-id"

    logging.info(f"Appending plots: {config['title']}")

    viz_layout_children.append(
        html.Div(
            [
                html.H4(
                    config["title"],
                    className="mr-3",
                    style={'display':'inline-block'}
                ),
                html.P(
                    config["description"]
                ),
                html.Div([
                    dbc.Row(
                        [
                            dbc.Col([
                                        html.Span("Choose fraction"),
                                        dcc.Dropdown(
                                            id=dropdown_id,
                                            options=[],  # To be populated in callback
                                            searchable=False,
                                            multi=True
                                        ),
                                    ], width=12, lg=11
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dcc.Loading(dbc.Col(
                                dcc.Graph(id=graph_id), width=12, lg=12
                            )),
                        ],
                    )],
                    className="mt-3"
                )
            ],
            id=block_id,
            style=CONTENT_STYLE
        )
    )

# Define the overall layout
app.layout = html.Div([
    dcc.Location(id='url', refresh='callback-nav'),
    navbar,
    html.Div(viz_layout_children, id='graphs-container')
])
    


# Callback to initialize all dropdown options and set default values
@app.callback(
    Output('pathogen-menu-id', 'options'),
    Input('url', 'pathname'),
)
def update_dropdown_menu(pathname):
    global data_frames, layout_config
    
    options = [
        {'label': 'all pathogens', 'value': 'all pathogens'}
    ]

    pathnames = []

    for idx in data_frames:
        config = layout_config[idx]
        pathname = config['pathogen']
        if pathname not in pathnames:
            pathnames.append(pathname)
            options.append({'label': pathname, 'value': pathname})
    
    return options

# Callback to initialize all dropdown options and set default values
@app.callback(
    Output('update-time-id', 'children'),
    *[
        Output(f"chart{idx+1}-f-id", 'options') for idx in data_frames
    ],
    *[
        Output(f"chart{idx+1}-f-id", 'value') for idx in data_frames
    ],
    *[
        Output(f"chart{idx+1}-block-id", 'style') for idx in data_frames
    ],
    Input('pathogen-menu-id', 'value'),
)
def init_page(pathogen):
    global data_frames, layout_config
    
    dropdown_options = []
    dropdown_values = []
    show_blocks = []
    
    for idx in data_frames:
        config = layout_config[idx]
        df = data_frames[idx]
        fractions = df['Fraction'].unique().tolist()
        dropdown_options.append([{'label': frac, 'value': frac} for frac in fractions])
        dropdown_values.append(fractions)  # Set all fractions as default selected

        style_patch = Patch()  # Initialize Patch object
        if pathogen == 'all pathogens' or pathogen == config['pathogen'] or not pathogen:
            style_patch["display"] = "block"
            show_blocks.append(style_patch)
        else:
            style_patch["display"] = "none"
            show_blocks.append(style_patch)
            
    
    # Determine the latest update time across all data files
    latest_time = 0
    for file in check_files:
        if file and os.path.exists(file):
            ti = os.path.getmtime(file)
            if ti > latest_time:
                latest_time = ti
    
    if latest_time:
        import pytz
        from datetime import timezone, datetime, timedelta
        utc_dt = datetime.fromtimestamp(ti, tz=timezone.utc)
        mt_timezone = pytz.timezone('America/Denver')
        time_stamp = utc_dt.astimezone(mt_timezone).strftime('%Y-%m-%d %H:%M:%S MT')
    else:
        time_stamp = "Unknown"

    return [time_stamp] + dropdown_options + dropdown_values + show_blocks

# Dynamically create callbacks for each graph based on layout_config
for idx in data_frames:
    config = layout_config[idx]
    graph_id = f"chart{idx+1}-graph-id"
    dropdown_id = f"chart{idx+1}-f-id"

    def generate_callback(idx, config):
        def update_figure(selected_fractions):
            df = data_frames.get(idx)
            if df is None:
                return {}
            
            if selected_fractions:
                mask = df['Fraction'].isin(selected_fractions)
            else:
                mask = df['Date'].notna()
            
            plot_data = df[mask]
            fig = px.line(plot_data, 
                          x='Date', 
                          y='Value',
                          error_y=('Value_std' if 'Value_std' in plot_data.columns else None),
                          title=config["plot_title"], 
                          color='Fraction',
                          height=700,
                          template='ggplot2')
            
            fig.update_layout(
                yaxis_title=config["plot_yaxis_title"], 
                xaxis_title=config["plot_xaxis_title"]
            )
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
            fig.update_traces(error_y_color="#AAAAAA", error_y_width=0.04, mode="markers+lines", hovertemplate=None)
            fig.update_layout(hovermode="x unified")
            
            return fig

        return callback(
            Output(graph_id, 'figure'),
            [Input(dropdown_id, 'value')],
        )(update_figure)

    # Register the callback for the current graph
    generate_callback(idx, config)

# Health check endpoint
@app.server.route('/healthz')
def healthz():
    # Perform any necessary health checks here
    # For example, check database connectivity, etc.
    # Return a 200 status code if everything is healthy
    return 'OK', 200

# Run the server
if __name__ == '__main__':
    app.run_server(host="127.0.0.1", 
                   port=8765,
                   threaded=False,
                   debug=True, 
                   use_reloader=False
    )
