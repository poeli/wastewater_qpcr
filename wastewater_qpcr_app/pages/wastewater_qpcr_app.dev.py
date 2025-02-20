#!/usr/bin/env python
import pandas as pd
import logging
import os
import json
import time

import plotly.express as px
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, State, Input, Output, callback, ctx, Patch, no_update

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M',
)

dash.register_page(__name__, path='/dev/')

# Define styles
CONTENT_STYLE = {
    'marginTop': '1rem',
    'maxWidth': '80rem',
    "padding": "0rem 1rem",
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
                html.Span(id='update-time-id')
            ],
            className='d-flex fs-6'
            ),
        ]
    ),
    color="dark",
    dark=True,
    className='fixed-top container-fluid',
)

# Containers for graph layouts and data frames
viz_layout_children = []
data_frames = {}  # To store data frames for each graph
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

# Function to process data files
def process_data(data_file, std_file=None):
    df = pd.DataFrame()
    logging.debug(f"process_data: data_file={data_file}, std_file={std_file}")  # ADDED
    try:
        df = pd.read_csv(data_file, sep='\t')
        df = df.set_index('DATE').unstack().reset_index().rename(
            columns={'DATE': 'Fraction', 'level_0': 'Date', 0: 'Value'}
        )
        df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce').dt.strftime('%Y-%m-%d')
        df = df[df['Date'].notnull()].reset_index(drop=True)
        df.fillna(0, inplace=True)
        logging.debug(f"Processed data: {data_file} {df.shape} {df.tail()}")
    except Exception as err:
        logging.error(f"Error processing data file {data_file}: {err}")
        raise

    if std_file and os.path.exists(std_file):
        try:
            df_std = pd.read_csv(std_file, sep='\t')
            df_std = df_std.set_index('DATE').unstack().reset_index().rename(
                columns={'DATE': 'Fraction', 'level_0': 'Date', 0: 'Value'}
            )
            df_std['Date'] = pd.to_datetime(df_std['Date'], format='mixed', errors='coerce').dt.strftime('%Y-%m-%d')
            df_std = df_std[df_std['Date'].notnull()].reset_index(drop=True)
            df_std.fillna(0, inplace=True)
            df = df.merge(df_std, on=['Date', 'Fraction'], how='left', suffixes=('', '_std'))
            logging.info(f"Processed std data: {std_file} {df.shape} {df.tail()}")
        except Exception as err:
            logging.error(f"Error processing std file {std_file}: {err}")
    
    return df

# Function to generate figure
def update_figure(plot_data):
    
    # Calculate date range for x-axis
    max_date = pd.to_datetime(plot_data['Date']).max() + pd.DateOffset(weeks=1)
    min_date = pd.to_datetime(plot_data['Date']).min() - pd.DateOffset(weeks=1)
    
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
        xaxis_title=config["plot_xaxis_title"],
        xaxis_range=[min_date, max_date]  # Set default view to last 6 months
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


# Process each configuration's data and build graph layout blocks
for idx, config in enumerate(layout_config):
    data_file = config['plot_data_tsv']
    std_file = config.get('plot_std_tsv')
    check_files.extend([data_file, std_file] if std_file else [data_file])
    
    try:
        df = process_data(data_file, std_file)
        data_frames[idx] = df
    except Exception as e:
        logging.error(f"Failed to process data for graph {idx+1}: {e}")

    # Skip if no data is available
    if idx not in data_frames:
        logging.error(f"Skipping config {idx+1}")
        continue
    
    # Generate figure
    fig = update_figure(df)

    # Build graph block
    block_id = f"chart{idx+1}-block-id"
    graph_id = f"chart{idx+1}-graph-id"

    logging.info(f"Appending plot: {config['title']}")

    viz_layout_children.append(
        html.Div(
            [
                html.H4(
                    config["title"],
                    className="mr-3",
                    style={'display':'inline-block'}
                ),
                html.P(config["description"]),
                html.Div([
                    dbc.Row(
                        [
                            dcc.Loading(dbc.Col(
                                dcc.Graph(id=graph_id, figure=fig), width=12, lg=12
                            )),
                        ],
                    )
                ], className="mb-3")
            ],
            id=block_id,
            className='mx-lg-auto',
            style=CONTENT_STYLE
        )
    )

# ---------------------------
# Calculate Trend Function
# ---------------------------
def calculate_trend(df, weeks=4):
    import pymannkendall as mk
    
    try:
        start_date = pd.to_datetime(df['Date']).max() - pd.DateOffset(weeks=weeks)

        # Filter the DataFrame to include only rows after the start date
        df_filtered = df[pd.to_datetime(df['Date']) >= start_date].sort_values(['Fraction', 'Date']).reset_index(drop=True)
        result = mk.original_test(df_filtered['Value'])
        
        return result.trend, result.p, result.Tau
    except Exception as e:
        logging.error(f"Error calculating trend: {e}")
        return "Error", None, None

# ---------------------------
# Create Trend Cards (Left Sidebar)
# ---------------------------
# Define mapping of trend to Bootstrap badge color:
trend_badge_color = {"increasing": "danger", "decreasing": "success", "no trend": "warning"}

trend_cards = []
for idx, config in enumerate(layout_config):
    if idx in data_frames:
        trend_1m, pval_1m, tau_1m = calculate_trend(data_frames[idx], 4)
        trend_6m, pval_6m, tau_6m = calculate_trend(data_frames[idx], 26)
    else:
        trend_1m = "No Data"
        trend_6m = "No Data"
    
    # Use dbc.Badge to display the trend with a colored background
    trend_badge_1m = dbc.Badge(f"1M: {trend_1m.capitalize()}", color=trend_badge_color.get(trend_1m, "secondary"), className="ms-1")
    trend_badge_6m = dbc.Badge(f"6M: {trend_6m.capitalize()}", color=trend_badge_color.get(trend_6m, "secondary"), className="ms-1")
    
    card = dbc.Card(
        [
            dbc.CardHeader(config["pathogen"]),
            dbc.CardBody(
                [
                    html.P([trend_badge_6m, trend_badge_1m]),
                    html.P(f"Using the Mann-Kendall trend test on the {config['title']} F3 data, with the significance level of 0.5, the p-value of {pval_1m:.3} and the Kendall's Tau of {tau_1m:.3}.", style={"font-size": "0.7rem"})
                ]
            )
        ],
        className="mb-3",
        style={},
        id=f"trend-card{idx+1}"
    )
    trend_cards.append(card)

# ---------------------------
# Define the Overall Layout with Two Columns
# ---------------------------
layout = dbc.Container([
    dcc.Location(id='url', refresh='callback-nav'),
    navbar,
    dbc.Row([
        dbc.Col(
            html.Div(trend_cards),
            width=2,
            style={"marginTop": "5rem", "paddingLeft": "2rem"}
        ),
        dbc.Col(
            html.Div(viz_layout_children),
            width=10,
            style={"marginTop": "5rem"}
        )
    ])
], fluid=True)

# ---------------------------
# Callbacks
# ---------------------------

# Callback to update the pathogen dropdown menu
@callback(
    Output('pathogen-menu-id', 'options', allow_duplicate=True),
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def update_dropdown_menu(pathname):
    global data_frames, layout_config
    options = [{'label': 'all pathogens', 'value': 'all pathogens'}]
    pathnames = []
    for idx in data_frames:
        config = layout_config[idx]
        path_val = config['pathogen']
        if path_val not in pathnames:
            pathnames.append(path_val)
            options.append({'label': path_val, 'value': path_val})
    return options

# Callback to initialize chart dropdowns and update block display based on pathogen selection
@callback(
    *[Output(f"trend-card{idx+1}", 'style', allow_duplicate=True) for idx in data_frames],
    *[Output(f"chart{idx+1}-block-id", 'style', allow_duplicate=True) for idx in data_frames],
    Input('pathogen-menu-id', 'value'),
    prevent_initial_call=True
)
def init_page(pathogen):
    global data_frames, layout_config
    graphs = []
    show_blocks = []

    for idx in data_frames:
        config = layout_config[idx]

        style_patch = Patch()
        if pathogen == 'all pathogens' or pathogen == config['pathogen'] or not pathogen:
            style_patch["display"] = "block"
            show_blocks.append(style_patch)
            graphs.append(update_figure(data_frames[idx]))
        else:
            style_patch["display"] = "none"
            show_blocks.append(style_patch)
            graphs.append(no_update)

    return show_blocks + show_blocks

# Callback to update time stamp
@callback(
    Output('update-time-id', 'children', allow_duplicate=True),
    Input('pathogen-menu-id', 'value'),
    prevent_initial_call=True
)
def update_time(pathogen):
    # Determine the latest update time across all data files
    latest_time = 0
    for file in check_files:
        if file and os.path.exists(file):
            ti = os.path.getmtime(file)
            if ti > latest_time:
                latest_time = ti
    
    if latest_time:
        import pytz
        from datetime import timezone, datetime
        utc_dt = datetime.fromtimestamp(latest_time, tz=timezone.utc)
        mt_timezone = pytz.timezone('America/Denver')
        time_stamp = utc_dt.astimezone(mt_timezone).strftime('%Y-%m-%d %H:%M') + ' updated'
    else:
        time_stamp = "Unknown"

    return time_stamp


# Run the server
if __name__ == '__main__':
    run_server(host="127.0.0.1", 
                   port=8765,
                   threaded=False,
                   debug=True, 
                   use_reloader=False
    )