#!/usr/bin/env python
import pandas as pd
import logging
import os
import json
import time

import plotly.express as px
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, State, Input, Output, callback, ctx, Patch, no_update, ALL
import openai
from openai import OpenAI
import httpx
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M',
)

# Initialize OpenAI client - assuming you have the API key set in environment variable
# Replace with your actual API key and base URL
openai_api_key = "sk-Upattg2kt62WTYMOVjkVbA"
openai_api_base = "https://aiportal-api.aws.lanl.gov/v1" # Or your custom base URL

client = openai.OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
    http_client=httpx.Client(verify=False)
)

dash.register_page(__name__, path='/')

# Function to generate AI summary
def generate_ai_summary(data_frames, selected_pathogen, model="meta.llama3-70b-instruct-v1:0"):
    """
    Generate an AI summary of the pathogen data using OpenAI API
    """
    try:
        # Prepare the data for summary
        if selected_pathogen == 'all pathogens':
            summary_text = "Summary of all pathogens in wastewater:\n\n"
            for idx, config in enumerate(layout_config):
                if idx in data_frames:
                    df = data_frames[idx]
                    pathogen = config['pathogen']
                    latest_date = df['Date'].max()
                    df_latest = df[df['Date'] == latest_date]
                    summary_text += f"- {pathogen}: Latest data from {latest_date}\n"
                    for _, row in df_latest.iterrows():
                        summary_text += f"  {row['Fraction']}: {row['Value']} {config.get('plot_yaxis_title', 'units')}\n"
                    if 'analysis' in config:
                        summary_text += f"  Trend: {config['analysis'].get('trend', 'N/A')}\n"
        else:
            # Get data for selected pathogen only
            summary_text = f"Summary of {selected_pathogen} in wastewater:\n\n"
            for idx, config in enumerate(layout_config):
                if config['pathogen'] == selected_pathogen and idx in data_frames:
                    df = data_frames[idx]
                    latest_date = df['Date'].max()
                    one_month_ago = (datetime.strptime(latest_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
                    df_latest = df[df['Date'] == latest_date]
                    df_month = df[df['Date'] >= one_month_ago]
                    
                    summary_text += f"Latest data from {latest_date}\n"
                    for _, row in df_latest.iterrows():
                        summary_text += f"{row['Fraction']}: {row['Value']} {config.get('plot_yaxis_title', 'units')}\n"
                    
                    # Calculate month-over-month trend
                    if len(df_month) > 1:
                        grouped = df_month.groupby('Fraction')['Value'].agg(['mean', 'min', 'max'])
                        summary_text += "\nMonth summary:\n"
                        for frac, stats in grouped.iterrows():
                            summary_text += f"{frac}: Mean={stats['mean']:.2f}, Range={stats['min']:.2f}-{stats['max']:.2f}\n"
                    
                    if 'analysis' in config:
                        summary_text += f"\nTrend analysis: {config['analysis'].get('trend', 'N/A')}\n"
                        summary_text += f"Description: {config['analysis'].get('description', 'N/A')}\n"
                    
                    summary_text += f"\nData description: {config.get('description', '')}\n"
        
        logging.info("Sending request to OpenAI API")
        # Call OpenAI API to generate summary
        response = client.chat.completions.create(
            model=model, 
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes wastewater pathogen data. Provide clear insights about trends and significance of the data."},
                {"role": "user", "content": f"Summarize the wastewater viral surveillance data for the last 7 days for a briefing in 1 paragraph. Focus on: 1) Key trends (increases/decreases) by pathogens; 2) Notable new detections;: \n\n{summary_text}"}
            ],
            max_tokens=500
        )
        
        summary = response.choices[0].message.content
        logging.info("AI summary generated successfully")
        
        return summary
    except Exception as e:
        logging.error(f"Error generating AI summary: {e}")
        return f"Error generating AI summary: {str(e)}"

# Define styles
PLOT_STYLE = {
    'marginTop': '1rem',
    # 'maxWidth': '80rem',
    "padding": "0rem 1rem",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "margin-top": "2rem",
    "padding": "2rem 1rem",
}

# styling the sidebar
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "3rem",
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow-y": "auto",
    "max-height": "calc(100vh - 3rem)"
}

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
                    # title=config["plot_title"], 
                    color='Fraction',
                    height=700,
                    template='ggplot2')
    fig.update_layout(
        yaxis_title=config["plot_yaxis_title"], 
        xaxis_title=config["plot_xaxis_title"],
        xaxis_range=[min_date, max_date],  # Set default view to last 6 months
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
        type="date",
        range=[(max_date - pd.DateOffset(years=1)).date(), 
               max_date.date()]
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
                            dbc.Col(dcc.Graph(id=graph_id, figure=fig), width=12, lg=12)
                        ],
                    )
                ], className="mb-3")
            ],
            id=block_id,
            className='mx-lg-auto',
            style=PLOT_STYLE
        )
    )

# ---------------------------
# Create Trend Cards (Left Sidebar)
# ---------------------------
# Define mapping of trend to Bootstrap badge color:
trend_badge_color = {"increasing": "danger", "decreasing": "success", "stable": "warning"}

trend_cards = []
for idx, config in enumerate(layout_config):
    if 'analysis' in config:
        # determine badge color based on trend
        badge_color = "warning"

        for trend_text in trend_badge_color:
            if trend_text in config['analysis']['trend']:
                badge_color = trend_badge_color[trend_text]
                break

        # Use dbc.Badge to display the trend with a colored background
        trend_badge = dbc.Badge(f"Trend: {config['analysis']['trend']}", color=badge_color, className="ms-1")

        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H6(config["pathogen"], className="card-title"),
                    html.P(trend_badge),
                    html.P(config['analysis']['description'], style={"font-size": "0.8rem"}),
                    dbc.CardLink("Click here for more details...", 
                                 id=f"trend-figure-link{idx+1}",
                                 href="#", 
                                 style={"font-size": "0.8rem", "color": "gray"})
                ]
            ),
            className="mb-3 trend-card",
            style={},
            id=f"trend-card{idx+1}"
        )
        trend_cards.append(card)
    else:
        continue

modal = html.Div(
    [
        dbc.Modal(
            id="trend-modal",
            size="xl",
            centered=True,
            is_open=False,
        )
    ]
)

# ---------------------------
# Nav bar (top bar)
# ---------------------------

options = [{'label': 'all pathogens', 'value': 'all pathogens'}]
pathnames = []
for idx in data_frames:
    config = layout_config[idx]
    path_val = config['pathogen']
    if path_val not in pathnames:
        pathnames.append(path_val)
        options.append({'label': path_val, 'value': path_val})
        
# Define navigation bar
dropdown = dcc.Dropdown(
    id="pathogen-menu-id",
    className="me-2",
    options=options,
    value='all pathogens',
    placeholder="all pathogens",
)

# AI summary button moved to navbar
summary_button = dbc.Button(
    "✦⁺₊ AI Summary", 
    id="generate-ai-summary-btn", 
    color="light", 
    className="ms-2", 
    size="sm",
    outline=True
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
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Row(
                    [
                        dbc.Col(dropdown, className="me-2"),
                        dbc.Col(summary_button, width="auto")
                    ],
                    className="ms-auto flex-nowrap mt-3 mt-md-0",
                    align="center"
                ),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            )
        ]
    ),
    color="dark",
    dark=True,
    className='fixed-top container-fluid',
)


# ---------------------------
# Define the Overall Layout with Two Columns
# ---------------------------

sidebar = html.Div(
    trend_cards+[html.Div(html.Span("test...", id='update-time-id'))],
    style=SIDEBAR_STYLE)

# Create AI summary card component - initially hidden
ai_summary_card = dbc.Card(
    [
        dbc.CardHeader("AI Summary"),
        dbc.CardBody(
            [
                html.P("", id="ai-summary-text"),
                dbc.Spinner(color="secondary", type="grow", size="sm", id="ai-summary-loading"),
            ]
        ),
    ],
    id="ai-summary-card",
    className="mb-4, mt-4",
    style={"display": "none"}
)

# Add the AI summary card to the main content
main_content = html.Div([
    ai_summary_card,
    html.Div(viz_layout_children)
], style=CONTENT_STYLE)

layout = dbc.Container([
    dcc.Location(id='url', refresh='callback-nav'),
    modal,
    navbar,
    sidebar,
    main_content
    # dbc.Row([
    #     dbc.Col(
    #         sidebar,
    #         xs=12, md=3, lg=2,  # Responsive widths
    #         # style={"marginTop": "5rem", "paddingLeft": "2rem"}
    #     ),
    #     dbc.Col(
    #         main_content,
    #         xs=12, md=9, lg=10,  # Responsive widths
    #         # style={"marginTop": "5rem"}
    #     )
    # ])
], fluid=True)

# ---------------------------
# Callbacks
# ---------------------------

# Callback to initialize chart dropdowns and update block display based on pathogen selection
@callback(
    *[Output(f"trend-card{idx+1}", 'style') for idx in range(len(layout_config)) if 'analysis' in layout_config[idx]],
    *[Output(f"chart{idx+1}-block-id", 'style') for idx in data_frames],
    Input('pathogen-menu-id', 'value'),
    prevent_initial_call=True
)
def init_page(pathogen):
    global data_frames, layout_config
    graphs = []
    show_blocks = []

    for idx in range(len(layout_config)):
        if 'analysis' in layout_config[idx]:
            config = layout_config[idx]
            style_patch = Patch()
            if pathogen == 'all pathogens' or pathogen == config['pathogen'] or not pathogen:
                style_patch["display"] = "block"
                show_blocks.append(style_patch)
            else:
                style_patch["display"] = "none"
                show_blocks.append(style_patch)

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

    return show_blocks

# Callback to update time stamp
@callback(
    Output('update-time-id', 'children'),
    Input('pathogen-menu-id', 'value'),
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
        time_stamp = "Last updated: " + utc_dt.astimezone(mt_timezone).strftime('%Y-%m-%d %H:%M')
    else:
        time_stamp = "Unknown"

    return time_stamp


# add callback for toggling the collapse on small screens
@callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# Callback for generating AI summary block visibility
@callback(
    Output("ai-summary-text", "children", allow_duplicate=True),
    Output("ai-summary-loading", "style", allow_duplicate=True),
    Output("ai-summary-card", "style"),
    [Input("generate-ai-summary-btn", "n_clicks")],
    prevent_initial_call=True
)
def update_ai_summary_block(n_clicks):
    if n_clicks:
        return "", {"display": "block"}, {"display": "block"}
    return no_update

# Callback for generating AI summary
@callback(
    Output("ai-summary-text", "children"),
    Output("ai-summary-loading", "style"),
    [Input("generate-ai-summary-btn", "n_clicks")],
    [State("pathogen-menu-id", "value")],
    prevent_initial_call=True
)
def update_ai_summary(n_clicks, selected_pathogen):
    if n_clicks:        
        # Generate summary
        summary = generate_ai_summary(data_frames, selected_pathogen)
        # Hide loading spinner but keep card visible
        loading_style = {"display": "none"}

        return summary, loading_style

    return no_update, no_update

# Add callback to update modal content when trend card is clicked
@callback(
    [
        Output("trend-modal", "is_open"),
        Output("trend-modal", "children")
    ],
    [
        Input(f"trend-figure-link{idx+1}", "n_clicks") for idx in range(len(layout_config)) if 'analysis' in layout_config[idx]
    ],
    prevent_initial_call=True,
)
def toggle_modal(*n_clicks):
    # Get the ID of the card that was clicked
    triggered_id = ctx.triggered_id if ctx.triggered_id else None
    
    logging.debug(f"Triggered ID: {triggered_id}")
    
    if not triggered_id:
        return False, no_update
    
    # Extract index from triggered_id (e.g., "trend-card1" -> 1)
    card_idx = int(triggered_id.replace("trend-figure-link", "")) - 1
    
    # Get the config for this card
    config = layout_config[card_idx]
    
    if 'analysis' not in config or 'figure' not in config['analysis']:
        return False, no_update
    
    # Create modal content with the correct figure and information
    modal_content = [
        dbc.ModalHeader(dbc.ModalTitle(f"{config.get('pathogen', 'Analysis')}"), close_button=True),
        dbc.ModalBody([
            html.Img(src=config['analysis']['figure'], 
                     style={"width": "100%", "height": "auto"}),
            html.P(config['analysis']['description'], 
                   className="mt-3")
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-centered", className="ms-auto", n_clicks=0)
        )
    ]
    
    return True, modal_content

# Add callback to close the modal when close button is clicked
@callback(
    Output("trend-modal", "is_open", allow_duplicate=True),
    [Input("close-centered", "n_clicks")],
    prevent_initial_call=True
)
def close_modal(n_clicks):
    if n_clicks:
        return False
    return no_update


# Run the server
if __name__ == '__main__':
    run_server(host="127.0.0.1", 
                   port=8765,
                   threaded=False,
                   debug=True, 
                   use_reloader=False
    )