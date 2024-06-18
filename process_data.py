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
    f = open(ticker + ".json")
    data = json.load(f)
    
    for thing in things_to_capture:
        data_to_return[thing] = dict()
        thing_df = pd.DataFrame(data["facts"]["us-gaap"][thing]["units"]["USD"])
        annual_thing_df = thing_df.loc[thing_df['form'] == '10-K']
        annual_thing_df = annual_thing_df[annual_thing_df['frame'].notna()]
        annual_thing_df = annual_thing_df[~annual_thing_df['frame'].str.contains('Q')]
        data_to_return[thing]['dataframe'] = annual_thing_df
        get_average_of_thing( data_to_return[thing] )

    return data_to_return