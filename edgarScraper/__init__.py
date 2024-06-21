import re
import requests
from bs4 import BeautifulSoup
import time
from argparse import ArgumentParser as ap
import pandas as pd
import os
from math import isnan
import win32com.client as win32

NUMBER_OF_TIMES_TO_LOOP = 10
R_NUMBERS_TO_CHECK = 30
TIME_TO_SLEEP = 2
HEADERS = {"user-agent": "Focused Financial"}

class Scraper:

    def __init__( self, ticker : str ):
        self.ticker = ticker
        self.tenKList = []
        self.financialExcelList = []
        self.getCIK( )
        self.columnsDict = {"Net Income":0, "Free Cash Flow":1, "Revenue":2, "Cost of Revenue":3, 
                            "Equity":4, "Total Liabilities":5, "Cash":6, "Shares Outstanding":7,
                            "R&D":8, "S&M":9, "G&A":10, "Capex":11, "Operating Cash Flow":12,
                            "Gross Margin":13, "Long-term Debt":14, "Dividends":15}
        self.columns = []
        for key in self.columnsDict:
            self.columns.append(key)
        self.currentData = []
        self.financialStatements = pd.DataFrame()

    def getCIK( self ):
        url = "http://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany"
        regexCIK = re.compile( r".*CIK=(\d{10}).*" )
        while True:
            time.sleep( TIME_TO_SLEEP )
            f = requests.get( url.format( self.ticker ), headers=HEADERS )
            results = regexCIK.findall( f.text )
            if len(results):
                results[0] = int(re.sub("\.[0]*", ".", results[0]))
                break
        self.CIK = str(results[0])

    def getStatements( self ):
        def getListOfTenKs( ):
            url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}&type=10-K&dateb=&owner=exclude&count=40&search_text="
            while True:
                time.sleep( TIME_TO_SLEEP )
                f = requests.get( url.format( self.CIK ), headers=HEADERS )
                soup = BeautifulSoup( f.content, "html5lib" )
                for link in soup.findAll( "a", href=True, id="documentsbutton" ):
                    linkUrl = link["href"]
                    if link.findPrevious( "td" ).findPrevious( "td" ).contents[0] == "10-K":
                        self.tenKList.append( "http://www.sec.gov{}".format( linkUrl[:linkUrl.rindex('/')+1] ) )
                    if len( self.tenKList ) >= 10:
                        return
                if len( self.tenKList ):
                    return

        def getListOfFinancialExcel( ):
            for tenKUrl in self.tenKList:
                time.sleep( TIME_TO_SLEEP )
                f = requests.get( "{}Financial_Report.xlsx".format( tenKUrl ), headers=HEADERS )
                if f.status_code == 200:
                    self.financialExcelList.append( "{}Financial_Report.xlsx".format( tenKUrl ) )
                else:
                    f = requests.get( "{}Financial_Report.xls".format( tenKUrl ), headers=HEADERS )
                    if f.status_code == 200:
                        self.financialExcelList.append( "{}Financial_Report.xls".format( tenKUrl ) )
                    else:
                        print( "Missing Excel File" )
        
        def saveExcelSheets( ):
            def convertXlsToXlsx( filename : str ):
                excel = win32.gencache.EnsureDispatch('Excel.Application')
                wb = excel.Workbooks.Open( filename )
                wb.SaveAs( filename+"x", FileFormat = 51 )
                wb.Close()
                excel.Application.Quit()
                os.remove( filename )


            def downloadFile( url : str, number : int ):
                f = requests.get( url, headers=HEADERS )
                open( str( number ) + url.rsplit('/', 1)[-1], "wb" ).write( f.content )

            fileNumber = 0
            for excelUrl in self.financialExcelList:
                downloadFile( excelUrl, fileNumber )
                if excelUrl.rsplit('.', 1)[-1] == 'xls':
                    convertXlsToXlsx( os.getcwd() + "\\" + str(fileNumber) + excelUrl.rsplit('/', 1)[-1] )
                fileNumber += 1

        def parseExcelSheets( ):
            def deleteFile( filename : str ):
                if os.path.exists( filename ):
                    os.remove( filename )

            def cleanDataFrame( df : pd.DataFrame ) -> pd.DataFrame:
                df = df.drop( [0] )
                for i in range( len(list(df)) ):
                    df.rename( columns = {list(df)[i]: str(i)}, inplace = True )
                df.drop_duplicates( subset=['0'], inplace=True )
                df.dropna( axis="columns", thresh=len(df) - 10, inplace=True)
                df.dropna( inplace=True )
                for i in range( len(list(df)) ):
                    df.rename( columns = {list(df)[i]: str(i)}, inplace = True )
                df = df[df["1"] != "'"]
                return df

            def parseIncomeStatementData( df : pd.DataFrame, multiplier : int ):
                # List of values we want to capture and how they 
                # might be labled in the excel sheet
                valuesDict = {
                    "Revenue": ["Revenue"],
                    "Cost of Revenue": ["Cost of revenue"],
                    "Gross Margin": ["Gross margin"],
                    "Net Income": ["Net income"],
                    "R&D": ["Research and development"],
                    "G&A": ["General and administrative"],
                    "S&M": ["Sales and Marketing"] }

                df = cleanDataFrame( df )                

                # Find and save the values we want
                for key, value in valuesDict.items():
                    for i in range(len(value)):
                        currentValue = df.loc[df["0"].str.contains(value[i], case=False)]
                        if not currentValue.empty:
                            self.currentData[self.columnsDict[key]] = \
                                currentValue.iloc[0]['1'] * multiplier
                
            def parseBalanceSheetData( df : pd.DataFrame, multiplier : int ):
                # List of values we want to capture and how they 
                # might be labled in the excel sheet
                valuesDict = {
                    "Cash": ["Cash and cash equivalents"],
                    "Equity": ["Total stockholders"],
                    "Total Liabilities": ["Total liabilities"],
                    "PPE": ["Property and equipment"],
                    "Lease": ["lease"],
                    "Capex": ["capital expenditure"],
                    "Long-term Debt": ["Long-term debt"],
                    "Shares Outstanding": ["Common stock"]}

                ppe = 0
                lease = 0
                capex = 0

                df = cleanDataFrame( df ) 
            
                df = df[df["0"] != "Current portion of long-term debt"]
                # Find and save the values we want
                for key, value in valuesDict.items():
                    for i in range(len(value)):
                        currentValue = df.loc[df["0"].str.contains(value[i], case=False)]
                        if not currentValue.empty:
                            if key == "PPE":
                                ppe = currentValue.iloc[0]['1'] * multiplier
                            elif key == "Lease":
                                lease = currentValue.iloc[0]['1'] * multiplier
                            elif key == "Capex":
                                capex = currentValue.iloc[0]['1'] * multiplier
                            else:
                                self.currentData[self.columnsDict[key]] = \
                                    currentValue.iloc[0]['1'] * multiplier

                # Special case for capex calculation TODO:Needs to be improved.
                if capex == 0:
                    self.currentData[self.columnsDict["Capex"]] = lease + ppe
                else:
                    self.currentData[self.columnsDict["Capex"]] = capex

            def parseCashflowStatementData( df : pd.DataFrame, multiplier : int ):
                # List of values we want to capture and how they 
                # might be labled in the excel sheet
                valuesDict = {
                    "Operating Cash Flow": ["Net cash from operations"],
                    "Dividends": ["Common stock cash dividends paid"] }

                df = cleanDataFrame( df )
                
                # Find and save the values we want
                for key, value in valuesDict.items():
                    for i in range(len(value)):
                        currentValue = df.loc[df["0"].str.contains(value[i], case=False)]
                        if not currentValue.empty:
                            if key == "Dividends":
                                self.currentData[self.columnsDict[key]] = \
                                    currentValue.iloc[0]['1'] * -multiplier
                            else:
                                self.currentData[self.columnsDict[key]] = \
                                    currentValue.iloc[0]['1'] * multiplier

            fileNumber = 0
            for excelUrl in self.financialExcelList:
                self.currentData = []
                for _ in range(len(self.columns)):
                    self.currentData.append(0)
                filename = str(fileNumber) + excelUrl.rsplit( "/", 1 )[-1]
                filename = filename.rsplit( ".", 1 )[0] + ".xlsx"
                i = 1
                gotIncome = False
                gotBalance = False
                gotCashflow = False
                multiplier = 1
                year = 0
                while not (gotIncome and gotBalance and gotCashflow):
                    worksheet = pd.read_excel( filename, sheet_name = i, engine = "openpyxl" )
                    i+=1

                    if ("income" in worksheet.columns[0].lower( )) and (not gotIncome):
                        if "$ in millions" in worksheet.columns[0].lower( ):
                            multiplier = 1000000
                        elif "millions" in worksheet.iloc[0][0].lower():
                            multiplier = 1000000
                        elif "$ in thousands" in worksheet.columns[0].lower( ):
                            multiplier = 1000
                        # year = int(worksheet.iloc[0][1].rsplit( ",", 1 )[-1])
                        parseIncomeStatementData( worksheet, multiplier )
                        gotIncome = True
                    elif ("balance" in worksheet.columns[0].lower( )) and (not gotBalance):
                        parseBalanceSheetData( worksheet, multiplier )
                        gotBalance = True
                    elif ("cash" in worksheet.columns[0].lower( )) and (not gotCashflow):
                        parseCashflowStatementData( worksheet, multiplier )
                        gotCashflow = True

                # self.currentData[self.columnsDict["Free Cash Flow"]] = \
                #     self.currentData[self.columnsDict["Operating Cash Flow"]] \
                #         - self.currentData[self.columnsDict["Capex"]]
                df = pd.DataFrame( [self.currentData], columns=self.columns, index=[year] )
                self.financialStatements = pd.concat([df, self.financialStatements], axis=0)                  
                deleteFile( filename )
                fileNumber+=1

        getListOfTenKs( )
        getListOfFinancialExcel( )
        saveExcelSheets( )
        # parseExcelSheets( )

def main():
    parser = ap( description="Get Financial Statement Data From SEC Edgar." )
    parser.add_argument( "ticker", type=str, help="Stock Ticker" )
    parser.add_argument( "-f", "--filename", type=str, required=False, help="CSV Output Filename" )
    args = parser.parse_args( )
    edgarScraper = Scraper( args.ticker )
    edgarScraper.getStatements()

    if args.filename:
        edgarScraper.financialStatements.to_csv( args.filename )
    else:
        edgarScraper.financialStatements.to_csv( "{}statements.csv".format( args.ticker ) )

if __name__ == "__main__":
    main()
