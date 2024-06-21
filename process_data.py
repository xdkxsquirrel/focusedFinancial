import json
import pandas as pd
import numpy as np

def process_data( ticker:str, things_to_capture:list ) -> dict:
    def get_average_of_thing( thing_dict:dict ):
        previous_thing = 0
        thing_percentages = []
        for index, row in thing_dict['dataframe'].iterrows():
            if int(row['fy']) > 2012:
                if previous_thing != 0:
                    thing_percentages.append( (row['val'] - previous_thing) / previous_thing * 100)
                previous_thing = row['val']
        data_to_return[thing]['average'] = np.average( thing_percentages )
        data_to_return[thing]['averages'] = thing_percentages

    data_to_return = dict()
    f = open( "database\\" + ticker + ".json" )
    data = json.load( f )
    
    for thing in things_to_capture:
        try:
            data_to_return[thing] = dict()
            thing_df = pd.DataFrame(data["facts"]["us-gaap"][thing]["units"]["USD"])
            annual_thing_df = thing_df.loc[thing_df['form'] == '10-K']
            annual_thing_df = annual_thing_df[annual_thing_df['frame'].notna()]
            annual_thing_df = annual_thing_df[~annual_thing_df['frame'].str.contains('Q')]
            data_to_return[thing]['dataframe'] = annual_thing_df
            get_average_of_thing( data_to_return[thing] )
        except Exception as e:
            print( f"Ticker: {ticker} Thing: {thing} | {repr(e)}")

    return data_to_return

def get_graphing_data( ticker:str, things_to_capture:list ):
    data_to_return = dict()
    f = open( "database\\" + ticker + ".json" )
    data = json.load( f )
    
    for thing in things_to_capture:
        try:
            data_to_return[thing] = dict()
            thing_df = pd.DataFrame(data["facts"]["us-gaap"][thing]["units"]["USD"])
            annual_thing_df = thing_df.loc[thing_df['form'] == '10-K']
            annual_thing_df = annual_thing_df[annual_thing_df['frame'].notna()]
            annual_thing_df = annual_thing_df[~annual_thing_df['frame'].str.contains('Q')]
            data_to_return[thing]['dataframe'] = annual_thing_df
        except Exception as e:
            print( f"Ticker: {ticker} Thing: {thing} | {repr(e)}")

    return data_to_return

def process_all_data( things_to_capture:list, save_data:bool=False ) -> pd.DataFrame:
    from os import walk
    f = []
    for ( dirpath, dirnames, filenames ) in walk( "database\\" ):
        f.extend( filenames )

    tickers = []

    all_data = dict()
    csv_dict = dict()

    for filename in f:
        extension = filename.find( ".json" )
        tickers.append( filename[0:extension] )
        all_data[filename[0:extension]] = process_data( filename[0:extension], things_to_capture )

    csv_dict['Ticker'] = tickers

    for thing in things_to_capture:
        thing_data = []
        for ticker in tickers:
            try:
                thing_data.append( all_data[ticker][thing]['average'] )
            except Exception as e:
                print( f"Ticker: {ticker} Thing: {thing} | {repr(e)}")
                thing_data.append( np.NaN )
        csv_dict[thing] = thing_data
        
    df = pd.DataFrame( csv_dict )
    if save_data:
        df.to_csv( "all_data.csv" )
    return df

if __name__ == '__main__':
    things_to_capture = [ "GrossProfit", "CostOfRevenue" ]
    process_all_data( things_to_capture, True )