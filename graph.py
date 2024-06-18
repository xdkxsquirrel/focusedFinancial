
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# all_data = pd.read_csv( 'all_data.csv' )

# Revenues
# Assets
# AssetsCurrent
# BuildingsAndImprovementsGross
# CapitalLeaseObligationsIncurred
# CashAndCashEquivalentsAtCarryingValue
# CashAndCashEquivalentsPeriodIncreaseDecrease
# CommonStockDividendsPerShareDeclared USD/shares
# CommonStockSharesOutstanding shares
# CostOfGoodsSold
# CostOfRevenue
# CostsAndExpenses
# Depreciation
# EarningsPerShareBasic
# EarningsPerShareDiluted
# FinanceLeaseLiability
# Liabilities
# LongTermDebt
# NetIncomeLoss
# OperatingExpenses
# OperatingIncomeLoss
# OperatingLeaseCost





# capex = change in PropertyPlantAndEquipmentGross + Depreciation

## Growth is Good
# Revenues
# Cashflow / Share
# Net Income
# Cash
# Equity
# ROCE = OperatingIncomeLoss / (AssetsCurrent - LiabilitiesCurrent)
# ROIC
# Interest Cover = Earnings before interest and taxes / Interest Expense (1.5 or lower = BAD) Looking for 20x
# Gross Margin
# Cash Convertion > 95% = OperatingIncomeLoss - capex

# Service Based Monopoly?
# Predictable?
# Too Hard?

## Growth is Bad
# Shares Outstanding
# Debt
# 

## Depends
# PE
# Price / Cashflow
def graph( ticker:str, things_to_capture:list, data:dict ):
    thing = things_to_capture[0]
    fig = px.scatter(data[thing]['dataframe'], x="end", y="val", labels= {"val": "Value ($)", "end": "Quarter End"})
    fig.show()


# Return on capital employed is calculated by dividing net operating profit, or 
# earnings before interest and taxes, by capital employed. Another way to calculate it is by 
# dividing earnings before interest and taxes by the difference between total assets and current liabilities.