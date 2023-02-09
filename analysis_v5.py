# -*- coding: utf-8 -*-
import os
import re
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
import sqlite3
import yfinance as yf
#%%
def get_CIK(ticker):
    with open('ticker-cik.txt','r') as f:
        content = f.readlines()
        for line in content:     
            tick = re.findall('[A-Za-z]*',line)[0]
            cik = int([i for i in re.findall('(\d*)',line) if i!=''][0])
            if tick==ticker.lower():
                break
    return cik
#%%
ticker = 'BAC'
cik = get_CIK(ticker)
#%%
# check to see how much data has already been processed for this ticker
clean_data_path = r'C:\Users\Owner\Documents\Analysis_Database\clean_data.db'
conn = sqlite3.connect(clean_data_path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(ticker))
table_check = c.fetchall()
#%%
submissions_database_path = r'C:\Users\Owner\Documents\Analysis_database\submissions.db'
conn = sqlite3.connect(submissions_database_path)
submission_lines = pd.read_sql("SELECT * FROM submissions WHERE cik={} and form='10-K'".format(cik),conn)
conn.close()
#%%
adsh_list = submission_lines['adsh']
period_list_raw = submission_lines['period']
period_list = [str(int(float(period))) for period in period_list_raw]
filing_list = [re.sub(r'(\d{4})(\d{2})(\d{2})',r'\1-\2-\3',submission_line) for submission_line in submission_lines['filed']]

update_dates_list = []
if len(table_check)!=0:
    if ticker in table_check[0]:
        table_exists = True
        conn = sqlite3.connect(clean_data_path)
        c = conn.cursor()
        c.execute("SELECT dates_list FROM {}".format(ticker))
        dates_in_table = c.fetchall()

        
        for filing_date,date_in_table in zip(filing_list,dates_in_table):
            if not date_in_table[0]==filing_date:
                update_dates_list.append(filing_date)
                print(ticker,'table no processed data for',date_in_table[0])
    else:
        table_exists = False
else:
    table_exists = False
# adjust for the lines that already have data
adsh_list = adsh_list[0:len(adsh_list)-len(update_dates_list)]
period_list = period_list[0:len(period_list)-len(update_dates_list)]
filing_list = filing_list[0:len(filing_list)-len(update_dates_list)]
#%%
company_lines_database_path = r'C:\Users\Owner\Documents\Analysis_database\company_lines.db'
conn = sqlite3.connect(company_lines_database_path)
company_lines = pd.read_sql("SELECT * FROM company_lines WHERE cik={} and form='10-K'".format(cik),conn)
conn.close()
company_lines = company_lines.iloc[-len(submission_lines):]
#%%
numbers_database_path = r'C:\Users\Owner\Documents\Analysis_database\numbers.db'
conn = sqlite3.connect(numbers_database_path)
numbers_lines_list = []

for index,(adsh,period_raw,filed) in enumerate(zip(adsh_list,period_list,filing_list)):
    print('searching for data filed {}|'.format(filed))
    numbers_lines = pd.read_sql("""
                         SELECT adsh,tag,uom,value,ddate,qtrs,coreg 
                         FROM numbers 
                         WHERE adsh='{}' and ddate=(SELECT(MAX({})) 
                         FROM numbers) and qtrs in (0,4) and coreg IS NULL""".format(adsh,period_raw),conn)
    numbers_lines_list.append(numbers_lines)
conn.close()
#%%
def loop(item,table):
    for i in range(len(table)):
        line = table.iloc[i][['tag','uom','value']]
        tag = line[0]
        uom = line[1]
        value = line[2]

        if item==tag:
            item_match = True
            break
        else:
            item_match = False
    return item_match,tag,uom,value

def get_item(item_list,table):   
    for item in item_list:           
        item_match,tag,uom,value = loop(item,table)
        if item_match:
            t = tag
            unit = uom
            val = value
            break
        else:
            t = 'not found'
            unit = 'not found'
            val = 0
    if math.isnan(val):
        val = 0
    print (t,' | ',val,' | ',unit)
    return val
#%%
import webbrowser
def open_doc(company_lines):
    if isinstance(company_lines,pd.DataFrame):
        for i in range(len(company_lines)):
            line = company_lines.iloc[i]
            html_extension = line['html_extension']    
            url = 'www.sec.gov/Archives/'+html_extension
            webbrowser.open_new_tab(url)
    if isinstance(company_lines,pd.Series):
            html_extension = company_lines['html_extension']
            url = 'www.sec.gov/Archives/'+html_extension
            webbrowser.open_new_tab(url)

def open_text(table):
    table.to_csv('temp.csv',sep='\t')
    os.startfile("temp.csv")
    
def get_regex_val(regex,table):
    t = 'not found'
    unit = 'not found'
    val = 'not found'
    for i in range(len(table)):
        line = table.iloc[i][['tag','uom','value']]
        tag = line[0]
        uom = line[1]
        value = line[2]
        if re.findall(regex,str(value).replace(',','')):
            t = tag
            unit = uom
            val = value
            print (t,' | ',val,' | ',unit,' | index=',i)
    print (t,' | ',val,' | ',unit,' | index=',i)
    
def get_regex_tag(regex,table):
    t = 'not found'
    unit = 'not found'
    val = 'not found'
    for i in range(len(table)):
        line = table.iloc[i][['tag','uom','value']]
        tag = line[0]
        uom = line[1]
        value = line[2]
        if re.findall(regex,tag.lower()):
            t = tag
            unit = uom
            val = value
            print (t,' | ',val,' | ',unit,' | index=',i)
    print (t,' | ',val,' | ',unit,' | index=',i)
#%%
print('~'*50)
print('NET INCOME')
net_income = [get_item(['NetIncomeLoss','ProfitLoss'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)

print('SHARES OUTSTANDING')
shares_outstanding = [get_item(['WeightedAverageNumberOfSharesOutstandingBasic','CommonStockSharesOutstanding'],numbers_lines) for numbers_lines in numbers_lines_list]
# if can't find shares out in 10K, back calculate from EPS
for i in range(len(shares_outstanding)):
    if shares_outstanding[i]==0:
        EPS_i = get_item(['EarningsPerShareBasic'],numbers_lines_list[i])
        shares_out_i = net_income[i]/EPS_i
        print('shares_outstanding[{}]'.format(i),'back calculated')
        shares_outstanding[i] = shares_out_i
print('~'*50)
print('STOCKHOLDER\'S EQUITY')
total_stockholders_equity = [get_item(['StockholdersEquity','StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('REVENUE')
revenue = [get_item(['Revenues','SalesRevenueNet','RevenueFromContractWithCustomerExcludingAssessedTax','SalesRevenueServicesNet','SalesRevenueGoodsNet'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('COST OF REVENUE')

cost_of_revenue = [get_item(['CostOfRevenue','CostOfGoodsSold','CostOfGoodsAndServicesSold'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('OPERATING INCOME')

income_from_operations = [get_item(['OperatingIncomeLoss'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('TOTAL ASSETS')

total_assets = [get_item(['Assets'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('TOTAL LIABILITIES')

total_liabilities_and_stockholders_equity = [get_item(['LiabilitiesAndStockholdersEquity'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('CURRENT ASSETS')

current_assets = [get_item(['AssetsCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('CURRENT LIABILITES')

current_liabilities = [get_item(['LiabilitiesCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('DEPRECIATION')

depreciation = [get_item(['Depreciation','DepreciationAmortizationAndAccretionNet','CostOfGoodsAndServicesSoldDepreciation'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('ACCOUNTS RECEIVABLE')

accounts_receivable = [get_item(['AccountsReceivableNetCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('ACCOUNTS PAYABLE')

accounts_payable = [get_item(['AccountsPayableAndAccruedLiabilitiesCurrent','AccountsPayableCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('NON-OPERATING INCOME/EXPENSE')

nonoperating_income_expense = [get_item(['NonoperatingIncomeExpense','TotalOtherExpense','OtherNonoperatingIncomeExpense','InterestAndOtherNet','OtherNonoperatingIncome'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('OPERATING CASH FLOW')

operating_CF = [get_item(['NetCashProvidedByUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('PLANT, PROPERTY, EQUIPMENT')

PPE = [get_item(['PaymentsToAcquirePropertyPlantAndEquipment','PurchasesOfPropertyAndEquipmentAndIntangibleAssets','PaymentsToAcquireProductiveAssets','PaymentsForProceedsFromProductiveAssets'],numbers_lines) for numbers_lines in numbers_lines_list]
PPE = [item*-1 for item in PPE if item>0]
FCF = [(oper_CF+PlntPropEquip)/shares_out for oper_CF,PlntPropEquip,shares_out in zip(operating_CF,PPE,shares_outstanding)]
print('~'*50)
print('INVESTING CASH FLOWS')

investing_CF = [get_item(['NetCashProvidedByUsedInInvestingActivities','NetCashProvidedByUsedInInvestingActivitiesContinuingOperations'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('DIVIDENDS')

dividends = [get_item(['DividendsCommonStock','PaymentsOfDividendsAndDividendEquivalentsOnCommonStockAndRestrictedStockUnits', \
                       'PaymentsOfDividendsCommonStock','PaymentsOfDividendsPreferredStockAndPreferenceStock','PaymentOfIntercompanyDividends'],numbers_lines) for numbers_lines in numbers_lines_list]

dividends = [div*-1 if div<0 else div for div in dividends if div is not None]
print('~'*50)
print('CASH AND CASH EQUIVALENTS')

cash_and_cash = [get_item(['CashAndCashEquivalentsAtCarryingValue','CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)
print('MARKETABLE SECURITIES')

MS = [get_item(['MarketableSecuritiesCurrent','AvailableForSaleSecuritiesCurrent','AvailableForSaleSecuritiesDebtSecuritiesCurrent','AvailableForSaleSecurities','ShortTermInvestments'],numbers_lines) for numbers_lines in numbers_lines_list]
print('~'*50)

#%%


EPS = [net_in/shares_out for net_in,shares_out in zip(net_income,shares_outstanding)]

BVPS = [total_stock_equity/shares_out for total_stock_equity,shares_out in zip(total_stockholders_equity,shares_outstanding)]
#%%
today = datetime.today().strftime('%Y-%m-%d')
ticker_obj = yf.Ticker(ticker)
# start history 14 days prior to actual statement data for plotting purposes
st_date = re.sub(r'(\d{4})(\d{2})(\d{2})',r'\1-\2-\3',submission_lines.iloc[0]['filed'])
st_date_obj = datetime.strptime(st_date,'%Y-%m-%d')-timedelta(days=14)
st_date_adjusted = st_date_obj.strftime('%Y-%m-%d')
ticker_hist = ticker_obj.history(start=st_date_adjusted,end=today)
hist_dates = ticker_hist.index.strftime('%Y-%m-%d')
#hist_dates_objs = [datetime.strptime(date,'%Y-%m-%d') for date in hist_dates]
#hist_dates_nums = [date.toordinal() for date in hist_dates_objs]
ticker_hist = dict(zip(hist_dates,ticker_hist['Close']))
filing_dates = [re.sub(r'(\d{4})(\d{2})(\d{2})',r'\1-\2-\3',submission_line) for submission_line in submission_lines['filed']]
#%%
def ticker_history(filing_date):
    try:
        val = ticker_hist[filing_date]
    except:
        val = np.nan
    return val

# find the market value of the stock when 10K was filed
market_price = [ticker_history(filing_date) for filing_date in filing_dates]

# price to earnings ratio (market price)/(EPS) WBA: PE < 15 or 6.67% return at least
PE_ratio = [market_price/EP_share for market_price,EP_share in zip(market_price,EPS)]

# price to book ratio (market price)/(book value per share) WBA: PB< 1.5
PB_ratio = [market_price/BV_share for market_price,BV_share in zip(market_price,BVPS)]
#%%
# income statement ratio analysis

# gross profit margin ratio

gross_profit_margin_ratio = [(rev-cost_of_rev)/rev for rev,cost_of_rev in zip(revenue,cost_of_revenue)]
operating_margin_ratio = [income_from_ops/rev for income_from_ops,rev in zip(income_from_operations,revenue)]

# net income margin ratio
net_income_margin_ratio = [net_in/rev for net_in,rev in zip(net_income,revenue)]

#%%
# balance sheet ratio analysis

#~~~~~~~~~~~~~~~~~~~~~
# profitability ratios
#~~~~~~~~~~~~~~~~~~~~~
# return on equity, ROE (net_income/equity) WBA: ROE > .08 or 8% over last 10 years, differs on sector
# measure of return
# total short term and long term liabilities
total_liabilities = [total_liabilities_and_stock_equity-total_stock_equity for total_liabilities_and_stock_equity,total_stock_equity in zip(total_liabilities_and_stockholders_equity,total_stockholders_equity)]
#total_equity = [total_assets-total_liabilities for total_assets,total_liabilities in zip(total_assets,total_liabilities)]
ROE = [net_in/total_stock_equity for net_in,total_stock_equity in zip(net_income,total_stockholders_equity)]
ROE_percent = [ROE*100 for ROE in ROE]

# return on assets ROA or return on invenstment ROI
ROA = [net_in/total_asst for net_in,total_asst in zip(net_income,total_assets)]
#%%
#~~~~~~~~~~~~~~~~~
# liquidity ratios
#~~~~~~~~~~~~~~~~~
# current ratio (current assets)/(current liabilities) WBA: loose: 1 < current rato < 5 | tight: 1.5 < current rato < 2.5
# financing structure, good measure of risk
current_ratio = [current_asst/current_liab for current_asst,current_liab in zip(current_assets,current_liabilities)]

# accounts receivable turnover ratio. relevant if company sells on credit
# measure of how quickly company is able to collect payment WBA: a ratio of 5-7 is optimal but can vary depending on the industry
accounts_receivable_turnover_ratio = [rev/acct_receivable for rev,acct_receivable in zip(revenue,accounts_receivable)]

# accounts payable turnover. relevant if company buys on credit
# measure of good credit and ability to get 'free' short term loans WBA: 2-6 is optimal

accounts_payable_turnover_ratio = [rev/acct_payable for rev,acct_payable in zip(revenue,accounts_payable)]
#%%
#~~~~~~~~~~~~~~~~
# solvency ratios
#~~~~~~~~~~~~~~~~
# debt/equity ratio (total liabilities-current_liabilities)/(total equity) WBA: DE < .50

# interest bearing debt/equity | interest bearing debt per dollar of equity
DE_ratio = [(total_liab-current_liab)/total_stock_equity for total_liab,total_stock_equity,current_liab in zip(total_liabilities,total_stockholders_equity,current_liabilities)]

# liabilities/equity ratio WBA: LE <.80 considered low risk
# includes non interest-bearing debt as well as interest bearing
LE_ratio = [total_liab/total_stock_equity for total_liab,total_stock_equity in zip(total_liabilities,total_stockholders_equity)] 

# NOTE: may need to include amortization
# NOTE: forget about solvency ratio
# solvency ratio. measure of cash flow per dollar of both short term and long term liabilites
solvency_ratio = [(net_income-depreciation)/total_liabilities for net_income,total_liabilities,depreciation in zip(net_income,total_liabilities,depreciation)]

# interest coverage ratio WBA: >5
#interest_and_other = [get_item(['InterestExpense','InterestRevenueExpenseNet'],numbers_lines) for numbers_lines in numbers_lines_list]

interest_coverage_ratio = [income_from_ops/nonop_income_expense for income_from_ops,nonop_income_expense in zip(income_from_operations,nonoperating_income_expense)]
#%%
# satement of cash flow ratio analysis

# free cash flow per share

# percent that shareholders gain per dollar of revenue (sales) WBA: FCF/revenue > .05
FCF_to_revenue = [FCF_share/rev for FCF_share,rev in zip(FCF,revenue)]

# investing cash flow to operating cash flow ratio | percent of operating income spent on maintaining and investing in company growth
investing_CF_to_operating_CF = [invest_CF/oper_CF for invest_CF,oper_CF in zip(investing_CF,operating_CF)]
#%%
dates_list = list(filing_dates)
dates = [datetime.strptime(date,'%Y-%m-%d') for date in dates_list]
dates_nums = [datetime.strptime(date,'%Y-%m-%d').toordinal() for date in dates_list]
dates_nums = np.array(dates_nums)
dates_labels = [datetime.strftime(date,'%b %Y') for date in dates]
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~
# free cash flow analysis
#~~~~~~~~~~~~~~~~~~~~~~~~
# step 1 estimate free cash flow n years into the future
# -estimate the growth rate (GR) of FCF
# -past FCF and ROE good start to estimate future GR

# calculate the growth rate of free cash flow each past year
GR_FCF = [(FCF[i]-FCF[i-1])/abs(FCF[i-1])*100 for i in range(1,len(FCF))]

# sustainable growth rate
#dividends = [get_item(['PaymentsOfDividends','PaymentsOfDividendsAndDividendEquivalentsOnCommonStockAndRestrictedStockUnits','PaymentsOfDividendsCommonStock'],numbers_lines) for numbers_lines in numbers_lines_list]
DPS = [div/shares_out for div,shares_out in zip(dividends,shares_outstanding)]

#retention_ratio = [(1-DivPS/EarnPS) for DivPS,EarnPS in zip(DPS,EPS)]
payout_ratio = [(DivPS/EarnPS) for DivPS,EarnPS in zip(DPS,EPS)]
retention_ratio = [(1-PR) for PR in payout_ratio]

# sustainable growth rate
SGR = [ROEqt*RR for ROEqt,RR in zip(ROE,retention_ratio)]

# internal growth rate
IGR = [ROAsst*RR for ROAsst,RR in zip(ROA,retention_ratio)]
#%%
# NOTE: I think this is the correct cash and cash

#MS = [get_item(['MarketableSecuritiesCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]

liquid_assets = [cash_cash+MrktSec+acct_receivable for cash_cash,MrktSec,acct_receivable in zip(cash_and_cash,MS,accounts_receivable)]

# quick ratio (liquid assets)/(current liabilites)
quick_ratio = [liquid_asst/current_liab for liquid_asst,current_liab in zip(liquid_assets,current_liabilities)]
FCF_margin = [FCF/revenue*shares_outs for FCF,revenue,shares_outs in zip(FCF,revenue,shares_outstanding)]

# price to book ratio (market price)/(book value per share) WBA: PB< 1.5
PB_ratio = [market_price/BVPS for market_price,BVPS in zip(market_price,BVPS)]
#%%
output_headers = ['dates_list','dates_nums','net_income','EPS','shares_outstanding','total_stockholders_equity','BVPS','market_price','PE_ratio','PB_ratio', \
'revenue','cost_of_revenue','gross_profit_margin_ratio','income_from_operations', \
'operating_margin_ratio','net_income_margin_ratio','total_assets','total_liabilities_and_stockholders_equity', \
'total_liabilities','ROE','ROE_percent','ROA','current_assets','current_liabilities','current_ratio', \
'accounts_receivable','accounts_receivable_turnover_ratio','accounts_payable', \
'accounts_payable_turnover_ratio','DE_ratio','LE_ratio','depreciation','solvency_ratio','nonoperating_income_expense', \
'interest_coverage_ratio','operating_CF','PPE','FCF','FCF_to_revenue','investing_CF', \
'investing_CF_to_operating_CF','GR_FCF','dividends','DPS','retention_ratio','SGR','IGR','FCF_margin', \
'cash_and_cash','MS','liquid_assets','quick_ratio']

dates_nums = [int(date) for date in dates_nums]
data_output = pd.DataFrame([dates_list,dates_nums,net_income,EPS,shares_outstanding,total_stockholders_equity,BVPS,market_price,PE_ratio,PB_ratio, \
revenue,cost_of_revenue,gross_profit_margin_ratio,income_from_operations, \
operating_margin_ratio,net_income_margin_ratio,total_assets,total_liabilities_and_stockholders_equity, \
total_liabilities,ROE,ROE_percent,ROA,current_assets,current_liabilities,current_ratio, \
accounts_receivable,accounts_receivable_turnover_ratio,accounts_payable, \
accounts_payable_turnover_ratio,DE_ratio,LE_ratio,depreciation,solvency_ratio,nonoperating_income_expense, \
interest_coverage_ratio,operating_CF,PPE,FCF,FCF_to_revenue,investing_CF, \
investing_CF_to_operating_CF,GR_FCF,dividends,DPS,retention_ratio,SGR,IGR,FCF_margin, \
cash_and_cash,MS,liquid_assets,quick_ratio]).transpose()

data_output.columns = output_headers
#%%
print('table exists =',table_exists)
if table_exists:
    clean_data_path = r'C:\Users\Owner\Documents\Analysis_Database\clean_data.db'
    conn = sqlite3.connect(clean_data_path)
    data_output.to_sql(ticker,con=conn,if_exists='append',index=False)

if not table_exists:
    clean_data_path = r'C:\Users\Owner\Documents\Analysis_Database\clean_data.db'
    conn = sqlite3.connect(clean_data_path)
    data_output.to_sql(ticker,con=conn,if_exists='replace',index=False)
#%%