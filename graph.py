import pandas as pd
import plotly.express as px
from process_data import get_graphing_data
from dash import dcc

def graph( ticker:str, things_to_capture:list, data:dict ):
    thing = things_to_capture[0]
    fig = px.scatter(data[thing]['dataframe'], x="end", y="val", labels= {"val": "Value ($)", "end": "Quarter End"})
    return fig

def dash_graph( ticker:str, things_to_capture:list ) -> dcc.Graph:
    data = get_graphing_data( ticker, things_to_capture)
    fig = graph( ticker, things_to_capture, data )
    return dcc.Graph( figure=fig )

if __name__ == '__main__':
    things_to_capture = [ "GrossProfit", "CostOfRevenue" ]
    ticker = "MSFT"
    data = get_graphing_data( ticker, things_to_capture)
    fig = graph( ticker, things_to_capture, data )
    fig.show()