# https://www.kaggle.com/code/svendaj/extracting-data-from-sec-edgar-restful-apis

import re, time
import json
import requests

TIME_TO_SLEEP = 2

header = {
  "User-Agent": "donovan.bidlack@gmail.com"
}

def get_data( ticker:str ):
    def getCIK( ticker ):
        url = "http://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany"
        regexCIK = re.compile( r".*CIK=(\d{10}).*" )
        while True:
            time.sleep( TIME_TO_SLEEP )
            f = requests.get( url.format( ticker ), headers=header )
            results = regexCIK.findall( f.text )
            if len(results):
                results[0] = int(re.sub("\\.[0]*", ".", results[0]))
                break
        return str(results[0])

    CIK = getCIK(ticker)
    outfile = "database\\" + ticker + ".json"
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{str(CIK).zfill(10)}.json"
    company_facts = requests.get(url, headers=header).json()
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(company_facts, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    tickers = ["AAPL", "ABNB", "ACN", "ADBE", "ADI", "ADP", "ADSK", "ALL", "AMAT", "AMD", "AMZN", "APH",
        "AVGO", "AXP", "BIIB", "BKNG", "BMY", "BSX", "BWA", "CAH", "CAT", "CF", "CI", "CL", "CLF",
        "CLX", "CMG", "CMI", "COF", "COST", "CRM", "CSCO", "CTAS", "CTSH", "CVS", "DFS", "DHR", "EA",
        "EL", "EW", "EXPD", "F", "FAST", "FFIV", "GOOGL", "GPC", "GRMN", "GWW", "HON", "HRL", "HSY", 
        "HUM", "IBM", "INTC", "INTU", "ISRG", "ITW", "JNJ", "JNPR", "JPM", "K", "KHC", "KLAC", "KMB",
        "KO", "LEN", "LRCX", "MA", "MAS", "MCHP", "MCO", "MET", "META", "MKC", "MNST", "MSFT", "NFLX",
        "NKE", "NOW", "NTAP", "NUE", "NVDA", "PAYX", "PG", "PGR", "PHM", "QCOM", "RHI", "ROK", "SBUX",
        "SEE", "SNA", "TEAM", "TTD", "UBER", "UNH", "UPS", "V", "WM", "ZM"]
    for ticker in tickers:
        get_data( ticker )
        print( f"Got {ticker}" )
    print( "DONE" )
