from graph import graph
from get_data import get_data
from process_data import process_data

ticker = "CRM"
# get_data( ticker )
things_to_capture = [ "GrossProfit" ]
data = process_data( ticker, things_to_capture )
print( data )
graph( ticker, things_to_capture, data )
