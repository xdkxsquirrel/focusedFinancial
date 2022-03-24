from argparse import ArgumentParser as ap
import pandas as pd
import yfinance as yf
from plotly.subplots import make_subplots as sp
import plotly.graph_objects as go
import numpy_financial as np

NUMBER_OF_YEARS = 10

class GraphFinancials:

    def __init__( self, ticker : str, financialStatements : pd.DataFrame, growthRate : float, peForCalculations : int, marr : float ):
        self.ticker = ticker
        self.financialStatements = financialStatements
        self.growthRate = growthRate
        self.peForCalculations = peForCalculations
        self.marr = marr

    def graphFinancials( self ):
        tickerInfo = yf.Ticker( self.ticker ).info
        currentPrice = tickerInfo["currentPrice"]
        marketCap = tickerInfo["marketCap"]
        dividendYield = tickerInfo["dividendYield"]
        dividend = tickerInfo["dividendRate"]
        payoutRatio = tickerInfo["payoutRatio"]
        sharesOutstanding = tickerInfo["sharesOutstanding"]

        def getFairPrice( ) -> float:
            currentEarnings = self.financialStatements.iloc[-1]["Net Income"]
            futureValue = np.fv( self.growthRate, NUMBER_OF_YEARS, 0, -currentEarnings )
            presentValue = -1 * np.pv( self.marr, NUMBER_OF_YEARS, 0, futureValue )
            return (presentValue / sharesOutstanding) * self.peForCalculations

        def getBuyPrice( ) -> str:
            return "{:.2f}".format(getFairPrice()/2)

        def getSellPrice( ) -> str:
            return "{:.2f}".format(getFairPrice()*2)

        def getROE( ) -> list:
            roeList = []
            for index, row in self.financialStatements.iterrows():
                roeList.append( row["Net Income"] / row["Equity"])
            return roeList

        def getROIC( ) -> list:
            roicList = []
            for index, row in self.financialStatements.iterrows():
                roicList.append( (row["Net Income"] - row["Dividends"]) / (row["Equity"] + row["Total Liabilities"]) )
            return roicList

        def getGrowth( financial : str ) -> list:
            growthList = [0]
            previousValue = 0
            first = True
            for index, row in self.financialStatements.iterrows():
                if first:
                    first = False
                    previousValue = row[financial]
                else:
                    growthList.append( (row[financial] - previousValue) / previousValue )
                    previousValue = row[financial]
            return growthList

        xValues = self.financialStatements.index
        fig = sp( rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02 )

        # Cashflow Graph
        yValues = ["Net Income", "Free Cash Flow", "Revenue", "R&D", "S&M", "G&A", "Capex"]
        colorValues = ["#0A9D00", "#0FFF00", "#5FFF54", "#000FFF", "#AC7600", "#FFaF00", "#FF0000"]
        for i in range(len(yValues)):
            fig.add_trace( go.Bar( name=yValues[i], x=xValues, y=self.financialStatements[yValues[i]], 
                marker=dict(color=colorValues[i]) ), row=1, col=1 )

        # Balance Sheet Graph
        yValues = ["Cash", "Equity", "Total Liabilities", "Long-term Debt", "Shares Outstanding"]
        colorValues = ["#0A9D00", "#005006", "#FF0000", "#960000", "#000FFF"]
        for i in range(len(yValues)):
            fig.add_trace( go.Bar( name=yValues[i], x=xValues, y=self.financialStatements[yValues[i]],
                marker=dict(color=colorValues[i]) ), row=2, col=1 )

        # Growths
        colorValues = ["#003EFF", "#0000FF"]
        fig.add_trace( go.Scatter( name="ROE", x=xValues, y=getROE(),
            line=dict(width=2, color=colorValues[0]), marker=dict(color=colorValues[0]) ), row=3, col=1 )
        fig.add_trace( go.Scatter( name="ROIC", x=xValues, y=getROIC(),
            line=dict(width=2, color=colorValues[1]), marker=dict(color=colorValues[1]) ), row=3, col=1 )
        yValues = ["Net Income", "Revenue", "Free Cash Flow", "Equity"]
        colorValues = ["#0A9D00", "#5FFF54", "#0FFF00", "#005006"]
        for i in range(len(yValues)):
            fig.add_trace( go.Scatter( name=yValues[i] + " Growth Rate", x=xValues, y=getGrowth( yValues[i] ), 
                line=dict(width=2, color=colorValues[i]), marker=dict(color=colorValues[i]) ), row=3, col=1 )

        # Top Text Values
        textValues = []
        textValues.append( ["Price", "${}".format(currentPrice)] )
        textValues.append( ["Buy Price", getBuyPrice()] )
        textValues.append( ["Sell Price", getSellPrice()] )
        textValues.append( ["Dividend", "${}".format(dividend)] )
        textValues.append( ["Dividend Yield", "%{:.2f}".format(dividendYield*100)] )
        textValues.append( ["Payout Ratio", "%{:.2f}".format(payoutRatio*100)] )
        textValues.append( ["", ""] )
        textValues.append( ["Market Cap", "${}".format(marketCap)] )
        for i in range(len(textValues)):
            fig.add_annotation(text=textValues[i][0], xref="paper", yref="paper", x=(i+1)*0.1, y=1.08, showarrow=False)
            fig.add_annotation(text=textValues[i][1], xref="paper", yref="paper", x=(i+1)*0.1, y=1.06, showarrow=False)

        fig.add_annotation(text="Expected Growth Rate: %{}".format(self.growthRate*100), xref="paper", yref="paper", x=.1, y=1.03, showarrow=False)
        fig.add_annotation(text="PE for Calculations: {}".format(self.peForCalculations), xref="paper", yref="paper", x=.5, y=1.03, showarrow=False)
        fig.add_annotation(text="MARR: %{}".format(self.marr*100), xref="paper", yref="paper", x=.8, y=1.03, showarrow=False)

        fig.update_layout( title_text=self.ticker )
        fig.show( )

def main():
    parser = ap( description="Graph financial data grabbed from edgarScraper" )
    parser.add_argument( "ticker", type=str, help="Stock Ticker" )
    parser.add_argument( "-f", "--filename", type=str, required=False, help="CSV Input Filename" )
    parser.add_argument( "-g", "--growthRate", type=float, required=False, help="Expected Growth Rate of Company" )
    parser.add_argument( "-p", "--peForCalculations", type=int, required=False, help="PE to do calculations on" )
    parser.add_argument( "-m", "--marr", type=float, required=False, help="Minimum acceptable rate of return" )
    args = parser.parse_args( )

    if args.filename:
        financialStatements = pd.read_csv( args.filename, index_col=0 )
    else:
        financialStatements = pd.read_csv( "{}statements.csv".format( args.ticker ), index_col=0 )

    growthRate = .25
    peForCacluations = 22
    marr = .12
    if args.growthRate:
        growthRate = args.growthRate
    if args.peForCalculations:
        peForCacluations = args.peForCacluations
    if args.marr:
        marr = args.marr
    
    graph = GraphFinancials( args.ticker, financialStatements, growthRate, peForCacluations, marr )
    graph.graphFinancials()

if __name__ == "__main__":
    main()
