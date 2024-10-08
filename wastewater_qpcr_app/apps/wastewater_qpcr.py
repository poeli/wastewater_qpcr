#!/usr/bin/env python
import pandas as pd
from uuid import uuid1
import logging
import json
import os

import plotly.express as px
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, State, Input, Output, set_props, Patch, no_update, callback, ctx


# dash.register_page(__name__, path='/', title='RAPTER')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M',
)

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

layout = html.Div(
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
    global df1, df1_std, df2

    # df1
    data_file = 'assets/data/LIVE-qPCR-Daily_Trend.tsv'
    std_file = 'assets/data/LIVE-qPCR-Daily_Trend_std.tsv'
    df1 = process_data(data_file, std_file)

    # df2
    data_file = 'assets/data/PPMoV-qPCR-Daily_Trend.tsv'
    df2 = process_data(data_file)

    return df1['Fraction'].unique().tolist(), df1['Fraction'].unique().tolist(), df2['Fraction'].unique().tolist(), df2['Fraction'].unique().tolist()



@callback(
        Output('chart1-graph-id', 'figure'),
        [
            Input('chart1-f-id', 'value'),
        ],
)
def update_figure1(chart1_f):
    global df1

    logging.debug(f"[data][update_figure1] chart1_f: {chart1_f}")

    # df1
    if chart1_f:
        idx = df1['Fraction'].isin(chart1_f)
    else:
        idx = df1['Date'].notna()
        

    fig = px.line(df1[idx], 
                x='Date', 
                y='Value', 
                error_y="Value_std",
                title='Concentration of SARS-CoV-2 in LANL wastewater', 
                color='Fraction',
                # width=900,
                height=700,
                template='ggplot2')

    fig.update_layout(yaxis_title='SARS-CoV-2 Virions / L', xaxis_title='Date')

    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(label="ALL", step="all")
            ])
        ),
        rangeslider=dict(
            visible=True,
            # bgcolor="#636EFA",
            thickness=0.1
        ),
        type="date"
    )

    fig.update_traces(
        error_y_color="#AAAAAA",
        error_y_width=0.04,
        mode="markers+lines",
        hovertemplate=None
    )

    fig.update_layout(hovermode="x unified")

    return fig

    

@callback(
        Output('chart2-graph-id', 'figure'),
        [
            Input('chart2-f-id', 'value'),
        ],
)
def update_figure2(chart2_f):
    global df2

    logging.debug(f"[data][data_check_url] triggered_id: {dash.callback_context.triggered_id}")

    # df2
    if chart2_f:
        idx = df2['Fraction'].isin(chart2_f)
    else:
        idx = df2['Date'].notna()

    fig = px.line(df2[idx], 
                x='Date', 
                y='Value', 
                title='SARS-CoV-2 concentration normalized against the PMMoV concentration', 
                color='Fraction',
                # width=900,
                height=700,
                template='ggplot2')

    fig.update_layout(yaxis_title='SARS-CoV-2 Virions / L', xaxis_title='Date')


    fig.update_xaxes(
        # rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(label="ALL", step="all")
            ])
        ),
        rangeslider=dict(
            visible=True,
            # bgcolor="#636EFA",
            thickness=0.1
        ),
        type="date"
    )

    fig.update_traces(
        error_y_color="#AAAAAA",
        error_y_width=0.04,
        mode="markers+lines",
        hovertemplate=None
    )

    fig.update_layout(hovermode="x unified")


    return fig