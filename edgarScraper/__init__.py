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
                            "Equity":4, "Debt":5, "Cash":6, "Shares Outstanding":7, "Dividend":8,
                            "R&D":9, "S&M":10, "G&A":11, "Capex":12, "Operating Cash Flow":13}
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

            def parseIncomeStatementData( df : pd.DataFrame, multiplier : int ):
                grabNextValue = False
                for _ , row in df.iterrows( ):
                    stringSearchArray = [
                    ["cost of revenue"],
                    ["revenue"],
                    ["net income"],
                    ["research"],
                    ["administrative"],
                    ["marketing"],
                    ["shares outstanding"]]

                    if isinstance( row[0], str ):
                        if any( ele in row[0].lower( ) for ele in stringSearchArray[0] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Cost of Revenue"]] = int( row[1] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[1] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Revenue"]] = int( row[1] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[2] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Net Income"]] = int( row[1] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[3] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["R&D"]] = int( row[1] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[4] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["G&A"]] = int( row[1] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[5] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["S&M"]] = int( row[1] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[6] ):
                            grabNextValue = True
                        elif grabNextValue:
                            grabNextValue = False
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Shares Outstanding"]] = int( row[1] ) * multiplier
                
            def parseBalanceSheetData( df : pd.DataFrame, multiplier : int ):
                ppe = 0
                lease = 0
                capex = 0

                stringSearchArray = [
                    ["cash equivalents"],
                    ["total stock"],
                    ["total liabilities"],
                    ["equipment"],
                    ["lease"],
                    ["capital expenditure"]]

                for _ , row in df.iterrows( ):
                    if isinstance( row[0], str ):
                        if any( ele in row[0].lower( ) for ele in stringSearchArray[0] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Cash"]] = int( row[1] ) * multiplier
                                elif not isnan( row[2] ):
                                    self.currentData[self.columnsDict["Cash"]] = int( row[2] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[1] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Equity"]] = int( row[1] ) * multiplier
                                elif not isnan( row[2] ):
                                    self.currentData[self.columnsDict["Equity"]] = int( row[2] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[2] ):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Debt"]] = int( row[1] ) * multiplier
                                elif not isnan( row[2] ):
                                    self.currentData[self.columnsDict["Debt"]] = int( row[2] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[3] ):
                            if not isinstance( row[1], str ):
                                if ppe == 0:
                                    if not isnan( row[1] ):
                                        ppe = int( row[1] ) * multiplier
                                    elif not isnan( row[2] ):
                                        ppe = int( row[2] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[4] ):
                            if not isinstance( row[1], str ):
                                if lease == 0:
                                    if not isnan( row[1] ):
                                        lease = int( row[1] ) * multiplier
                                    elif not isnan( row[2] ):
                                        lease = int( row[2] ) * multiplier
                        elif any( ele in row[0].lower( ) for ele in stringSearchArray[5] ):
                            if not isinstance( row[1], str ):
                                if capex == 0:
                                    if not isnan( row[1] ):
                                        capex = int( row[1] ) * multiplier
                                    elif not isnan( row[2] ):
                                        capex = int( row[2] ) * multiplier
                        if capex == 0:
                            self.currentData[self.columnsDict["Capex"]] = ppe + lease
                        else:
                            self.currentData[self.columnsDict["Capex"]] = capex

            def parseCashflowStatementData( df : pd.DataFrame, multiplier : int ):
                stringSearchArray = [
                    ["cash from operations"]]

                for _ , row in df.iterrows( ):
                    if isinstance( row[0], str ):
                        if any(ele in row[0].lower( ) for ele in stringSearchArray[0]):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Operating Cash Flow"]] = int( row[1] ) * multiplier

            def parseStockholdersStatementData( df : pd.DataFrame ):
                stringSearchArray = [
                    ["cash dividends"]]

                for _ , row in df.iterrows( ):
                    if isinstance( row[0], str ):
                        if any(ele in row[0].lower( ) for ele in stringSearchArray[0]):
                            if not isinstance( row[1], str ):
                                if not isnan( row[1] ):
                                    self.currentData[self.columnsDict["Dividend"]] = row[1]


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
                gotStockholders = False
                multiplier = 1
                year = 0
                while not (gotIncome and gotBalance and gotCashflow and gotStockholders):
                    worksheet = pd.read_excel( filename, sheet_name = i, engine = "openpyxl" )
                    i+=1

                    if ("income" in worksheet.columns[0].lower( )) and (not gotIncome):
                        if "$ in millions" in worksheet.columns[0].lower( ):
                            multiplier = 1000000
                        elif "millions" in worksheet.iloc[0][0].lower():
                            multiplier = 1000000
                        elif "$ in thousands" in worksheet.columns[0].lower( ):
                            multiplier = 1000
                        year = int(worksheet.iloc[0][1].rsplit( ",", 1 )[-1])
                        parseIncomeStatementData( worksheet, multiplier )
                        gotIncome = True
                    elif ("balance" in worksheet.columns[0].lower( )) and (not gotBalance):
                        parseBalanceSheetData( worksheet, multiplier )
                        gotBalance = True
                    elif ("cash" in worksheet.columns[0].lower( )) and (not gotCashflow):
                        parseCashflowStatementData( worksheet, multiplier )
                        gotCashflow = True
                    elif ("stockholders" in worksheet.columns[0].lower( )) and (not gotStockholders):
                        parseStockholdersStatementData( worksheet )
                        gotStockholders = True

                self.currentData[self.columnsDict["Free Cash Flow"]] = self.currentData[self.columnsDict["Operating Cash Flow"]] - self.currentData[self.columnsDict["Capex"]]
                df = pd.DataFrame( [self.currentData], columns=self.columns, index=[year] )
                self.financialStatements = pd.concat([df, self.financialStatements], axis=0)                  
                deleteFile( filename )
                fileNumber+=1

        getListOfTenKs( )
        getListOfFinancialExcel( )
        saveExcelSheets( )
        parseExcelSheets( )

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