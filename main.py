from graph import dash_graph
from get_data import get_data
from process_data import process_data, process_all_data
from dash import Dash, html, dcc, Input, Output, callback, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import logging
import webbrowser
import sys
from flask import Flask, request
from enum import Enum

freqs = []

def create_graphs( freq_Z_bodies_df:pd.DataFrame, colors ):
    freqs = []

    impedance_fig = make_subplots( rows=1, cols=1, subplot_titles = ["Z Body Magnitude"], shared_xaxes = False )
    phase_fig = make_subplots( rows=1, cols=1, subplot_titles = ["Z Body Phase"], shared_xaxes = False )

    i = 0
    for freq in freqs:
        linspace_x = np.linspace( 0, 100, len( freq_Z_bodies_df[str(freq) + "_Z_body"] ) )

        impedance_fig.add_trace( go.Scatter( x = linspace_x, y = freq_Z_bodies_df[str(freq) + "_Z_body_mag"], name=str(freq), line_color=colors[i] ), row=1, col=1)
        phase_fig.add_trace( go.Scatter( x = linspace_x, y = freq_Z_bodies_df[str(freq) + "_Z_body_phase"], name=str(freq), line_color=colors[i] ), row=1, col=1 )
        i+=1

def get_app_layout( server:Flask ) -> Dash:    
    app = Dash( "Focused Financial", server=server )
    app.layout = html.Div( children=[
        html.H1( children="Focused Financial Stock Assessor" ),

        dbc.Row([
            dbc.Col([
                html.Label( "Capture Stock Data", style={"margin-left": "15px"} ),
                dcc.Input( id="ticker-for-data-input", value="", debounce=True, style={"margin-left": "15px"} ),
                html.Div( id="ticker-for-data-output", style={"margin-left": "45px"} ),
            ]),
        ]),

        dbc.Row([
            dbc.Col([
                html.Label( "Graph a Stock", style={"margin-left": "15px"} ),
                dcc.Input( id="ticker-for-graph-input", value="", debounce=True, style={"margin-left": "15px"} ),
            ]),
        ]),

        dbc.Row([
            dbc.Col([
                html.Button( "Process All Stocks", id="process-all-stocks-button", n_clicks=0, style={"margin-left": "15px"} ),
            ]),
        ]),

        html.Br(),
        html.Br(),

        dbc.Row( [], id="main-display" ),
    ] )
    return app

def create_dash_gui() -> None:
    server = Flask(__name__)
    app = get_app_layout( server )

    @callback(
        Output( "ticker-for-data-output", "children" ),
        Input( "ticker-for-data-input", "value" ),
        prevent_initial_call=True
    )
    def process_ticker_for_data( ticker ):
        if ticker == '':
            return ''
        get_data( ticker )
        return f"Collected data for {ticker}"
    
    @callback(
        Output( "main-display", "children", allow_duplicate=True ),
        Input( "process-all-stocks-button", "n_clicks" ),
        prevent_initial_call=True
    )
    def process_all_stocks_data( n_clicks ):
        things_to_capture = [ "GrossProfit", "CostOfRevenue" ]
        df = process_all_data( things_to_capture )

        return dash_table.DataTable(df.to_dict('records'), [{"name": i, "id": i} for i in df.columns])
    
    @callback(
        Output( "main-display", "children" ),
        Input( "ticker-for-graph-input", "value" ),
        prevent_initial_call=True
    )
    def graph_stock( ticker ):
        things_to_capture = [ "GrossProfit", "CostOfRevenue" ]
        return dash_graph( ticker, things_to_capture )

    app.run( debug=True )    

if __name__ == '__main__':
    create_dash_gui()
