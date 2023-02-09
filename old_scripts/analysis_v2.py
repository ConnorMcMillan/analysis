# -*- coding: utf-8 -*-
import os
import re
import numpy as np
#from scipy.interpolate import interp1d
#from bs4 import BeautifulSoup as bs
#import requests
import pandas as pd
from datetime import datetime, timedelta
#import matplotlib.pyplot as plt
import math
import sqlite3
#from WBA_models import get_bond_rate,DCF_intrinsic_value,DCF_discount_rate,avg_BVC,BB_intrinsic_value,BB_discount_rate
#from get_10K_tables_v4 import get_10K_tables_v4,get_10K_filings_lines
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
ticker = 'NVDA'
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
net_income = [get_item(['NetIncomeLoss'],numbers_lines) for numbers_lines in numbers_lines_list]
shares_outstanding = [get_item(['WeightedAverageNumberOfSharesOutstandingBasic','CommonStockSharesOutstanding'],numbers_lines) for numbers_lines in numbers_lines_list]

# if can't find shares out in 10K, back calculate from EPS
for i in range(len(shares_outstanding)):
    if shares_outstanding[i]==0:
        EPS_i = get_item(['EarningsPerShareBasic'],numbers_lines_list[i])
        shares_out_i = net_income[i]/EPS_i
        print('shares_outstanding[{}]'.format(i),'back calculated')
        shares_outstanding[i] = shares_out_i

EPS = [net_in/shares_out for net_in,shares_out in zip(net_income,shares_outstanding)]
total_stockholders_equity = [get_item(['StockholdersEquity','StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],numbers_lines) for numbers_lines in numbers_lines_list]
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

revenue = [get_item(['Revenues','SalesRevenueNet','RevenueFromContractWithCustomerExcludingAssessedTax','SalesRevenueServicesNet','SalesRevenueGoodsNet'],numbers_lines) for numbers_lines in numbers_lines_list]
cost_of_revenue = [get_item(['CostOfRevenue','CostOfGoodsSold','CostOfGoodsAndServicesSold'],numbers_lines) for numbers_lines in numbers_lines_list]
gross_profit_margin_ratio = [(rev-cost_of_rev)/rev for rev,cost_of_rev in zip(revenue,cost_of_revenue)]
income_from_operations = [get_item(['OperatingIncomeLoss'],numbers_lines) for numbers_lines in numbers_lines_list]
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
total_assets = [get_item(['Assets'],numbers_lines) for numbers_lines in numbers_lines_list]
total_liabilities_and_stockholders_equity = [get_item(['LiabilitiesAndStockholdersEquity'],numbers_lines) for numbers_lines in numbers_lines_list]
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
current_assets = [get_item(['AssetsCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]
current_liabilities = [get_item(['LiabilitiesCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]
current_ratio = [current_asst/current_liab for current_asst,current_liab in zip(current_assets,current_liabilities)]

# accounts receivable turnover ratio. relevant if company sells on credit
# measure of how quickly company is able to collect payment WBA: a ratio of 5-7 is optimal but can vary depending on the industry
accounts_receivable = [get_item(['AccountsReceivableNetCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]
accounts_receivable_turnover_ratio = [rev/acct_receivable for rev,acct_receivable in zip(revenue,accounts_receivable)]

# accounts payable turnover. relevant if company buys on credit
# measure of good credit and ability to get 'free' short term loans WBA: 2-6 is optimal
accounts_payable = [get_item(['AccountsPayableAndAccruedLiabilitiesCurrent','AccountsPayableCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]

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
depreciation = [get_item(['Depreciation','DepreciationAmortizationAndAccretionNet','CostOfGoodsAndServicesSoldDepreciation'],numbers_lines) for numbers_lines in numbers_lines_list]
# solvency ratio. measure of cash flow per dollar of both short term and long term liabilites
solvency_ratio = [(net_income-depreciation)/total_liabilities for net_income,total_liabilities,depreciation in zip(net_income,total_liabilities,depreciation)]

# interest coverage ratio WBA: >5
#interest_and_other = [get_item(['InterestExpense','InterestRevenueExpenseNet'],numbers_lines) for numbers_lines in numbers_lines_list]
nonoperating_income_expense = [get_item(['NonoperatingIncomeExpense','TotalOtherExpense','OtherNonoperatingIncomeExpense','OtherNonoperatingIncome'],numbers_lines) for numbers_lines in numbers_lines_list]

interest_coverage_ratio = [income_from_ops/nonop_income_expense for income_from_ops,nonop_income_expense in zip(income_from_operations,nonoperating_income_expense)]
#%%
# satement of cash flow ratio analysis

# free cash flow per share
operating_CF = [get_item(['NetCashProvidedByUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'],numbers_lines) for numbers_lines in numbers_lines_list]
PPE = [get_item(['PaymentsToAcquirePropertyPlantAndEquipment','PurchasesOfPropertyAndEquipmentAndIntangibleAssets','PaymentsToAcquireProductiveAssets'],numbers_lines) for numbers_lines in numbers_lines_list]
PPE = [item*-1 for item in PPE if item>0]
FCF = [(oper_CF-PlntPropEquip)/shares_out for oper_CF,PlntPropEquip,shares_out in zip(operating_CF,PPE,shares_outstanding)]

# percent that shareholders gain per dollar of revenue (sales) WBA: FCF/revenue > .05
FCF_to_revenue = [FCF_share/rev for FCF_share,rev in zip(FCF,revenue)]

# investing cash flow to operating cash flow ratio | percent of operating income spent on maintaining and investing in company growth
investing_CF = [get_item(['NetCashProvidedByUsedInInvestingActivities','NetCashProvidedByUsedInInvestingActivitiesContinuingOperations'],numbers_lines) for numbers_lines in numbers_lines_list]
investing_CF_to_operating_CF = [invest_CF/oper_CF for invest_CF,oper_CF in zip(investing_CF,operating_CF)]
#%%
dates_list = list(filing_dates)
dates = [datetime.strptime(date,'%Y-%m-%d') for date in dates_list]
dates_nums = [datetime.strptime(date,'%Y-%m-%d').toordinal() for date in dates_list]
dates_nums = np.array(dates_nums)
dates_labels = [datetime.strftime(date,'%b %Y') for date in dates]
#%%
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~
# free cash flow analysis
#~~~~~~~~~~~~~~~~~~~~~~~~
# step 1 estimate free cash flow n years into the future
# -estimate the growth rate (GR) of FCF
# -past FCF and ROE good start to estimate future GR

# calculate the growth rate of free cash flow each past year
GR_FCF = [(FCF[i]-FCF[i-1])/FCF[i-1]*100 for i in range(1,len(FCF))]

# sustainable growth rate
#dividends = [get_item(['PaymentsOfDividends','PaymentsOfDividendsAndDividendEquivalentsOnCommonStockAndRestrictedStockUnits','PaymentsOfDividendsCommonStock'],numbers_lines) for numbers_lines in numbers_lines_list]
dividends = [get_item(['DividendsCommonStock','PaymentsOfDividendsAndDividendEquivalentsOnCommonStockAndRestrictedStockUnits', \
                       'PaymentsOfDividendsCommonStock','PaymentsOfDividendsPreferredStockAndPreferenceStock','PaymentOfIntercompanyDividends'],numbers_lines) for numbers_lines in numbers_lines_list]

#dividends = [get_item(['PaymentsOfDividendsPreferredStockAndPreferenceStock'],numbers_lines) for numbers_lines in numbers_lines_list]    
    
dividends = [div*-1 if div<0 else div for div in dividends if div is not None]
DPS = [div/shares_out for div,shares_out in zip(dividends,shares_outstanding)]

#retention_ratio = [(1-DivPS/EarnPS) for DivPS,EarnPS in zip(DPS,EPS)]
payout_ratio = [(DivPS/EarnPS) for DivPS,EarnPS in zip(DPS,EPS)]
retention_ratio = [(1-PR) for PR in payout_ratio]

SGR = [ROEqt*RR for ROEqt,RR in zip(ROE,retention_ratio)]

# internal growth rate
IGR = [ROAsst*RR for ROAsst,RR in zip(ROA,retention_ratio)]

#%%
# NOTE: I think this is the correct cash and cash
cash_and_cash = [get_item(['CashAndCashEquivalentsAtCarryingValue'],numbers_lines) for numbers_lines in numbers_lines_list]

#MS = [get_item(['MarketableSecuritiesCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]
MS = [get_item(['MarketableSecuritiesCurrent','AvailableForSaleSecuritiesCurrent','AvailableForSaleSecuritiesDebtSecuritiesCurrent'],numbers_lines) for numbers_lines in numbers_lines_list]

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
clean_data_path = r'C:\Users\Owner\Documents\Analysis_Database\clean_data.db'
conn = sqlite3.connect(clean_data_path)
data_output.to_sql(ticker,con=conn,if_exists='replace',index=False)
#%%
#
## need to estimate a growth rate of FCF for the next n years
#
#plt.style.use('seaborn')
#fig1,(ax1a,ax1b) = plt.subplots(2,sharex=True)
#
#tailing_GR_FCF = tailing_avg(GR_FCF,period='whole')
#tailing_GR_FCF3 = tailing_avg(GR_FCF,period=3)
#tailing_GR_FCF5 = tailing_avg(GR_FCF,period=5)
#
#ax1a.plot(dates,FCF,'-o',color='b',label='FCF')
#ax1b.plot(dates[len(dates)-len(GR_FCF):],GR_FCF,'-o',color='b',label='growth rate')
#ax1b.plot(dates[len(dates)-len(tailing_GR_FCF):],tailing_GR_FCF,label='tailing avg')
#ax1b.plot(dates[len(dates)-len(tailing_GR_FCF3):],tailing_GR_FCF3,label='3-period tailing avg')
#ax1b.plot(dates[len(dates)-len(tailing_GR_FCF5):],tailing_GR_FCF5,label='5-period tailing avg')
#
#highest_num = round_high_num(GR_FCF)[0]
#lowest_num = round_high_num(GR_FCF)[1]
#
#ax1a.set_title('FCF (per share)',fontsize=20)
#ax1a.yaxis.set_tick_params(labelsize=30)
#ax1a.axhline(0,color='black')
#ax1a.annotate((str(round(FCF[-1],2))),xy=(dates[-1],FCF[-1]),size=20)
#
#
#ax1b.set_title('YoY Growth FCF',size=20)
#ax1b.yaxis.set_tick_params(labelsize=30)
#ax1b.set_ylim(lowest_num,highest_num)
#ax1b.set_yscale('symlog')
#ax1b.set_xticks(dates_nums)
#ax1b.set_xticklabels(dates_labels)
#ax1b.xaxis.set_tick_params(rotation=45, labelsize=30)
#ax1b.legend(fontsize=20,loc='upper left')
#ax1b.axhline(0,color='black')
#
#
#y_labels,y_locs = plt.yticks()
#y_labels = [str(int(y))+'%' for y in y_labels]
#ax1b.set_yticklabels(y_labels)
#for index,(i,j) in enumerate(zip(dates[1:],GR_FCF)):
#    ax1b.annotate((str(round(j))+'%'),xy=(i,j),size=20)
##%%
#fig2,(ax2a,ax2b) = plt.subplots(2,sharex=True)
#
#tailing_SGR = tailing_avg(SGR,period='whole')
#tailing_SGR3 = tailing_avg(SGR,period=3)
#tailing_SGR5 = tailing_avg(SGR,period=5)
#
#ax2a.plot(dates_nums,SGR,'-o',color='b',label='SGR')
#ax2a.plot(dates,tailing_SGR,label='tailing avg')
#ax2a.plot(dates[len(dates)-len(tailing_SGR3):],tailing_SGR3,label='3-period tailing avg')
#ax2a.plot(dates[len(dates)-len(tailing_SGR5):],tailing_SGR5,label='5-period tailing avg')
#
#ax2a.annotate((str(round(SGR[-1],2))),xy=(dates[-1],SGR[-1]),size=20)
#ax2a.annotate((str(round(tailing_SGR[-1],2))),xy=(dates[-1],tailing_SGR[-1]),size=20)
#ax2a.annotate((str(round(tailing_SGR3[-1],2))),xy=(dates[-1],tailing_SGR3[-1]),size=20)
#ax2a.annotate((str(round(tailing_SGR5[-1],2))),xy=(dates[-1],tailing_SGR5[-1]),size=20)
#
#
#tailing_IGR = tailing_avg(IGR,period='whole')
#tailing_IGR3 = tailing_avg(IGR,period=3)
#tailing_IGR5 = tailing_avg(IGR,period=5)
#
#
#ax2b.plot(dates_nums,IGR,'-o',color='g',label='IGR')
#ax2b.plot(dates,tailing_IGR,label='tailing avg')
#ax2b.plot(dates[len(dates)-len(tailing_IGR3):],tailing_IGR3,label='3-period tailing avg')
#ax2b.plot(dates[len(dates)-len(tailing_IGR5):],tailing_IGR5,label='5-period tailing avg')
#
#ax2b.annotate((str(round(IGR[-1],2))),xy=(dates[-1],IGR[-1]),size=20)
#ax2b.annotate((str(round(tailing_IGR[-1],2))),xy=(dates[-1],tailing_IGR[-1]),size=20)
#ax2b.annotate((str(round(tailing_IGR3[-1],2))),xy=(dates[-1],tailing_IGR3[-1]),size=20)
#ax2b.annotate((str(round(tailing_IGR5[-1],2))),xy=(dates[-1],tailing_IGR5[-1]),size=20)
#
#ax2b.set_xticks(dates_nums)
#ax2b.set_xticklabels(dates_labels)
#ax2b.xaxis.set_tick_params(rotation=45, labelsize=30)
#ax2a.yaxis.set_tick_params(labelsize=30)
#ax2b.yaxis.set_tick_params(labelsize=30)
#ax2a.axhline(0,color='black')
#ax2b.axhline(0,color='black')
#
#ax2a.set_title('SGR',fontsize=20)
#ax2b.set_title('IGR',fontsize=20)
#ax2a.legend(fontsize=20)
#ax2b.legend(fontsize=20)
##%%
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Discounted FCF model parameters
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
## larger of 2.0% growth or 10 year bond rate
#bond_rate_10yr = get_bond_rate(term='10 yr')[0]/100
#if bond_rate_10yr >= 0.020:
#    LGR = bond_rate_10yr
#else:
#    LGR = .020
##%%
#    
#    
## average of 5-yr SGR tailing average and 5-yr GR FCF tailing avgerage
#GR_5yr_tailing = (tailing_SGR5[-1]+tailing_GR_FCF5[-1]/100)/2
#GR_3yr_tailing = (tailing_SGR3[-1]+tailing_GR_FCF3[-1]/100)/2
#
#GR_5yr_avg = tailing_SGR5[-1]
#
## try 5yr growth rate from yahoo, if 'N/A': 5yr trailing average SGR,FCF average
#if yahoo_5yr_growth(ticker)=='N/A':
#    GR_5years = np.ones(5)*GR_5yr_tailing
#else:
#    GR_5years = np.ones(5)*yahoo_5yr_growth(ticker)
#    
#
## future growth rate from years 6-10 lesser of 5yr, 3yr, or LGR rate
#if GR_5yr_tailing < GR_5years[0]:    
#    GR_next_5years = np.linspace(GR_5years[0],GR_5yr_tailing,7)[1:-1]
#    print('5yr')
#elif GR_3yr_tailing <=GR_5years[0]:
#    GR_next_5years = np.linspace(GR_5years[0],GR_3yr_tailing,7)[1:-1]
#    print('3yr')
#elif LGR <= GR_5years[0]:
#    GR_next_5years = np.linspace(GR_5years[0],LGR,7)[1:-1]
#    print('LGR')
#
#GR_years = np.concatenate([GR_5years,GR_next_5years])
##%%
## DCF intrnisic value model parameters
#n=5
#DR_low = .08
#DR_hi = .12
#DR_range = np.linspace(DR_low*100,DR_hi*100,int(DR_hi*100-DR_low*100+1))/100
#BYFCF = FCF[-1]
#GR_years = GR_years[:n]
#LGR = .03
## adjust for current information
##SGR[-1] = yahoo_5yr_growth(ticker)
#
#DCF_intrinsic_val_list = []
#for DR in DR_range:
#    intrinsic_val_list = []
#    for GR,BYFCF in zip(SGR,FCF):
#        GR_years = np.ones(n)*GR
#        print('GR = {0} | FCF = {1}'.format(GR,BYFCF))
#        
#        val = DCF_intrinsic_value(DR,BYFCF,GR_years,LGR,n=n)
#        intrinsic_val_list.append(val[0])
#    DCF_intrinsic_val_list.append(intrinsic_val_list)
#    break
##%%
## DCF intrnisic value model parameters
##    ~~~~~~~~~editing~~~~~~~~~~#
## only using SGR as growth rate of FCF
#n=5
#DR_low = .08
#DR_hi = .12
#DR_range = np.linspace(DR_low*100,DR_hi*100,int(DR_hi*100-DR_low*100+1))/100
#BYFCF = FCF[-1]
#GR_years = GR_years[:n]
#LGR = .03
#
#DCF_intrinsic_val_list = []
#for DR in DR_range:
#    intrinsic_val_list = []
#    SGR_years = []
#    for i,(GR,BYFCF) in enumerate(zip(SGR,FCF)):
##        GR_years = np.ones(n)*GR
#        
#        SGR_years.append(GR)
#        if i>=4:
#            GR_avg = tailing_avg(SGR_years,period=5)[-1]
#        if i<4:            
#            GR_avg = tailing_avg(SGR_years,period=i+1)[-1]
#        GR_years = np.ones(5)*GR_avg
#            
#        
#        print('GR = {0} | FCF = {1}'.format(GR_avg,BYFCF))
#        
#        val = DCF_intrinsic_value(DR,BYFCF,GR_years,LGR,n=n)
#        intrinsic_val_list.append(val[0])
#    DCF_intrinsic_val_list.append(intrinsic_val_list)
##%%
#
## get 1yr avg analyst price target form yahoo 
#quote_table = si.get_quote_table(ticker, dict_result=False)
#analyst_1yr_target = quote_table.iloc[0][1]
## get corresponding discount rate from anaylst target
#DRo = .10
#DCF_analyst_1yr_DR = DCF_discount_rate(DRo,analyst_1yr_target,BYFCF,GR_years,LGR,n=n)
##%%
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## plotting DCF intrinsic value model
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
## fit spline to intrinsic values
#DCF_cspline_list = []
#DCF_cspline_dates_nums = [hist_dates_nums[0]]+ dates_nums.tolist()+[hist_dates_nums[-1]]
#for intrinsic_val_list,DR in zip(DCF_intrinsic_val_list,DR_range):
#    DCF_cspline_val_list = [intrinsic_val_list[0]]+intrinsic_val_list+[intrinsic_val_list[-1]]
#    DCF_cspline = interp1d(DCF_cspline_dates_nums,DCF_cspline_val_list,kind='quadratic')
#    DCF_cspline_list.append(DCF_cspline)
##%%
## get anaylst intrinsic value list from back-calculated discount rate
#anaylst_intrinsic_val_list = []
#for GR,BYFCF in zip(SGR,FCF):
#    GR_years = np.ones(n)*GR
#    val = DCF_intrinsic_value(DCF_analyst_1yr_DR,BYFCF,GR_years,LGR,n=n)
#    anaylst_intrinsic_val_list.append(val[0])
#
## spline for analyst target value
#DCF_analyst_spline_val_list = anaylst_intrinsic_val_list
##DCF_analyst_spline_val_list = [intrinsic_val_list[0]]+DCF_analyst_spline_val_list+[DCF_analyst_spline_val_list[-1]]
#DCF_analyst_spline_val_list = [DCF_analyst_spline_val_list[0]]+DCF_analyst_spline_val_list+[DCF_analyst_spline_val_list[-1]]
#
#DCF_analyst_spline = interp1d(DCF_cspline_dates_nums,DCF_analyst_spline_val_list,kind='cubic')
#
##%%
#fig3, ax3 = plt.subplots()
#
#fig3.suptitle('DCF model',size=60)
#
## plot historical closing price data
#ax3.set_title('n={0} LGR={1}'.format(n,LGR),size=40)
#ax3.plot(hist_dates_nums,[ticker_hist[date] for date in hist_dates])
#
## plot intrinsic value for each discount rate
#for spline,DR,intrinsic_val_list in zip(DCF_cspline_list,DR_range,DCF_intrinsic_val_list):
#    ax3.plot(hist_dates_nums,spline(hist_dates_nums),'-',color='g',label=str(DR*100)+'%')
#    ax3.plot(dates_nums,intrinsic_val_list,'o',color='g')
#
## annotate IV splines
#end_intrinsic_vals = [intrinsic_val_list[-1] for intrinsic_val_list in DCF_intrinsic_val_list]
#for DR,end_intrinsic_val in zip(DR_range,end_intrinsic_vals):
#    ax3.annotate(str(round(DR*100,2))+'%',xy=(dates[-1],end_intrinsic_val),size=20)
#
## plot analyst target with back-calculated discount rate
#ax3.plot(dates_nums,anaylst_intrinsic_val_list,'o',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   
#ax3.plot(dates_nums[-1],anaylst_intrinsic_val_list[-1],'o',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
#ax3.plot(hist_dates_nums,DCF_analyst_spline(hist_dates_nums),'-',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
#ax3.plot(hist_dates_nums[:hist_dates_nums.index(dates_nums[-1])+1],DCF_analyst_spline(hist_dates_nums[:hist_dates_nums.index(dates_nums[-1])+1]),'-',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   
#
## annotate analyst spline
#ax3.annotate(str(round(DCF_analyst_1yr_DR*100,2))+'%',xy=(dates[-1],analyst_1yr_target),size=20)
#    
## format axis
#ax3.set_xticks(dates_nums)
#ax3.set_xticklabels(dates_labels)
#ax3.xaxis.set_tick_params(rotation=45, labelsize=30)
#ax3.yaxis.set_tick_params(labelsize=30)
#ax3.axhline(0,color='black')
#xlim_hi = ax3.get_xlim()[1]   
##%%
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## plotting BB intrinsic value model
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#len(BVPS)
#years_between = len(BVPS)-1
#GRBV = avg_BVC(BVPS[0],BVPS[-1],years_between)
#
#DR_range
#BB_intrinsic_val_list = []
#for DR in DR_range:
#    BVPS_current_list = []
#    intrinsic_val_list = []
#    for index,BVPS_current in enumerate(BVPS):
#        BVPS_current_list.append(BVPS_current)
#        if index==0:
#            continue
#        
#        years_between = len(BVPS_current_list)-1
#        GRBV = avg_BVC(BVPS_current_list[0],BVPS_current_list[-1],years_between)
#    
#        intrinisc_val = BB_intrinsic_value(DR,BVPS_current,GRBV,n=5,Div=0)
#        intrinsic_val_list.append(intrinisc_val)
#    BB_intrinsic_val_list.append(intrinsic_val_list)
##%%
## calculate analyst DR through BB model given analyst price target
#DRo = .10
#GRBV = avg_BVC(BVPS[0],BVPS[-1],len(BVPS)-1)
#BB_analyst_1yr_DR = BB_discount_rate(DRo,analyst_1yr_target,BVPS[-1],GRBV,n=n,Div=0)
##%%
## build a spline for each discount rate
#BB_cspline_list = []
#BB_cspline_dates_nums = dates_nums[1:].tolist()+[hist_dates_nums[-1]]
#for intrinsic_val_list,DR in zip(BB_intrinsic_val_list,DR_range):
#    BB_cspline_val_list = intrinsic_val_list+[intrinsic_val_list[-1]]
#    BB_cspline = interp1d(BB_cspline_dates_nums,BB_cspline_val_list,kind='cubic')
#    BB_cspline_list.append(BB_cspline)
#
#anaylst_intrinsic_val_list = []
#BVPS_current_list = []
#for index,BVPS_current in enumerate(BVPS):
#    BVPS_current_list.append(BVPS_current)
#    if index==0:
#        continue
#    years_between = len(BVPS_current_list)-1
#    GRBV = avg_BVC(BVPS_current_list[0],BVPS_current_list[-1],years_between)
#    val = BB_intrinsic_value(BB_analyst_1yr_DR,BVPS_current,GRBV,n=n)
#    anaylst_intrinsic_val_list.append(val)
#
## spline for analyst target value
#BB_analyst_spline_val_list = anaylst_intrinsic_val_list
#BB_analyst_spline_val_list = BB_analyst_spline_val_list+[BB_analyst_spline_val_list[-1]]
#BB_analyst_spline = interp1d(BB_cspline_dates_nums,BB_analyst_spline_val_list,kind='cubic')
##%%
#fig4, ax4 = plt.subplots()
#
#fig4.suptitle('BB model',size=60)
#
## plot historical closing price data
#ax4.set_title('n={0} LGR={1}'.format(n,LGR),size=40)
#
## plot historical closing price data
#ax4.plot(hist_dates_nums,[ticker_hist[date] for date in hist_dates])
#
## plot intrinsic value for each discount rate
#for spline,DR,intrinsic_val_list in zip(BB_cspline_list,DR_range,BB_intrinsic_val_list):
#    ax4.plot(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):],spline(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):]),'-',color='g',label=str(DR*100)+'%')
#    ax4.plot(dates_nums[1:],intrinsic_val_list,'o',color='g')
#
## annotate IV splines
#end_intrinsic_vals = [intrinsic_val_list[-1] for intrinsic_val_list in BB_intrinsic_val_list]
#for DR,end_intrinsic_val in zip(DR_range,end_intrinsic_vals):
#    ax4.annotate(str(round(DR*100,2))+'%',xy=(dates[-1],end_intrinsic_val),size=20)
#
## plot analyst target with back-calculated discount rate
#ax4.plot(dates_nums[1:],anaylst_intrinsic_val_list,'o',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   
#ax4.plot(dates_nums[-1],anaylst_intrinsic_val_list[-1],'o',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
#ax4.plot(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):],BB_analyst_spline(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):]),'-',color='orange',label=str(BB_analyst_1yr_DR*100)+'%')   
#ax4.plot(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):],BB_analyst_spline(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):]),'-',color='g',label=str(BB_analyst_1yr_DR*100)+'%')   
#
## annotate analyst spline
#ax4.annotate(str(round(BB_analyst_1yr_DR*100,2))+'%',xy=(dates[-1],analyst_1yr_target),size=20)
#    
## format axis
#ax4.set_xticks(dates_nums)
#ax4.set_xticklabels(dates_labels)
#ax4.xaxis.set_tick_params(rotation=45, labelsize=30)
#ax4.yaxis.set_tick_params(labelsize=30)
#ax4.axhline(0,color='black')
##%%
##~~~~~~~~~~~~~~~~~~~~~~~
## plot solvency analysis
##~~~~~~~~~~~~~~~~~~~~~~~
#
#fig5,(ax5) = plt.subplots(nrows=2, ncols=2,sharex=True,sharey=False)
#
#fig5.suptitle('Solvency Analysis',size=60)
#
## upper left
#ax5[0,0].set_title('DE ratio',size=20)
#ax5[0,0].plot(dates,DE_ratio,'-o',color='blue',zorder=3)
#
#ax5[0,0].fill_between(dates,.50,DE_ratio,where=(.50>np.array(DE_ratio)),color='lightgreen',zorder=0,interpolate=True)
#ax5[0,0].fill_between(dates,.50,DE_ratio,where=(.50<=np.array(DE_ratio)),color='lightyellow',zorder=0,interpolate=True)
#
#ax5[0,0].axhline(0,color='black',zorder=3)
#ax5[0,0].set_xlim([ax5[0,0].get_xlim()[0],ax5[0,0].get_xlim()[1]])
#ax5[0,0].set_ylim(0,max(DE_ratio)*2)
#ax5[0,0].set_axisbelow(False)
#ax5[0,0].yaxis.set_tick_params(labelsize=20)
#ax5[0,0].annotate(str(round(DE_ratio[-1],2)),xy=(dates[-1],DE_ratio[-1]),size=20)
#
## upper right
#ax5[0,1].set_title('LE ratio',size=20)
#ax5[0,1].plot(dates,LE_ratio,'-o',color='blue',zorder=3)
#
#ax5[0,1].fill_between(dates,.80,LE_ratio,where=(.80>np.array(LE_ratio)),color='lightgreen',zorder=0,interpolate=True)
#ax5[0,1].fill_between(dates,.80,LE_ratio,where=(.80<=np.array(LE_ratio)),color='lightyellow',zorder=0,interpolate=True)
#
#ax5[0,1].axhline(0,color='black',zorder=3)
#ax5[0,1].set_xlim([ax5[0,0].get_xlim()[0],ax5[0,0].get_xlim()[1]])
#ax5[0,1].set_ylim(0,max(LE_ratio)*2)
#ax5[0,1].set_axisbelow(False)
#ax5[0,1].yaxis.set_tick_params(labelsize=20)
#ax5[0,1].annotate(str(round(LE_ratio[-1],2)),xy=(dates[-1],LE_ratio[-1]),size=20)
#
## lower left
#ax5[1,0].set_title('Solvency Ratio',size=20)
#ax5[1,0].plot(dates,solvency_ratio,'-o',color='blue',zorder=3)
#
#ax5[1,0].fill_between(dates,.20,solvency_ratio,where=(.20<np.array(solvency_ratio)),color='lightgreen',zorder=0,interpolate=True)
#ax5[1,0].fill_between(dates,.20,solvency_ratio,where=(.20>=np.array(solvency_ratio)),color='lightyellow',zorder=0,interpolate=True)
#
#ax5[1,0].axhline(0,color='black',zorder=3)
#ax5[1,0].set_ylim(min(solvency_ratio)*2,max(solvency_ratio)*2)
#
#ax5[1,0].set_xticks(dates_nums)
#ax5[1,0].set_xticklabels(dates_labels)
#ax5[1,0].xaxis.set_tick_params(rotation=45, labelsize=20)
#ax5[1,0].yaxis.set_tick_params(labelsize=20)
#ax5[1,0].annotate(str(round(solvency_ratio[-1],2)),xy=(dates[-1],solvency_ratio[-1]),size=20)
#
## lower right
#ax5[1,1].set_title('Interest Coverage Ratio',size=20)
#ax5[1,1].plot(dates,interest_coverage_ratio,'-o',color='blue',zorder=3)
#
## lgoical expressions for shading
#logical1 = [-5>=np.array(interest_coverage_ratio)]
#logical2 = [0<np.array(interest_coverage_ratio)]
#combined_logical = np.logical_or(logical1,logical2)
#ax5[1,1].fill_between(dates,-5,interest_coverage_ratio,where=(-5<=np.array(interest_coverage_ratio)),color='lightyellow',zorder=0,interpolate=True)
#ax5[1,1].fill_between(dates,-5,interest_coverage_ratio,where=(combined_logical[0]),color='lightgreen',zorder=0,interpolate=True)
#
#ax5[1,1].set_yscale('symlog')
#y_labels,y_locs = plt.yticks()
#y_labels = [str(int(y)) for y in y_labels]
#ax5[1,1].set_yticklabels(y_labels)
#ax5[1,1].axhline(0,color='black',zorder=3)
#ax5[1,1].set_xticks(dates_nums)
#ax5[1,1].set_xticklabels(dates_labels)
#ax5[1,1].xaxis.set_tick_params(rotation=45, labelsize=20)
#ax5[1,1].yaxis.set_tick_params(labelsize=20)
#ax5[1,1].annotate(str(round(interest_coverage_ratio[-1],2)),xy=(dates_nums[-1],interest_coverage_ratio[-1]),size=20)
##%%
##~~~~~~~~~~~~~~~~~~~~~~~~
## plot liquidity analysis
##~~~~~~~~~~~~~~~~~~~~~~~~
#
#fig6, ax6 = plt.subplots(2,sharex=True,sharey=False)
#fig6.suptitle('Liquidity Analysis',size=60)
#
#ax6[0].set_title('Current Ratio',size=20)
#ax6[0].plot(dates,current_ratio,'o')
#ax6[0].plot(dates,current_ratio,'-')
#
#ax6[0].fill_between(dates,1,5,color='palegreen',zorder=0,interpolate=True)
#ax6[0].fill_between(dates,1.5,2.5,color='lightgreen',zorder=0,interpolate=True)
#
#ax6[0].yaxis.set_tick_params(labelsize=30)
#ax6[0].axhline(0,color='black',zorder=3)
#ax6[0].annotate(str(round(current_ratio[-1],2)),xy=(dates_nums[-1],current_ratio[-1]),size=20)
#
## plot quick ratio (liquid assets)/(current liabilites)
#ax6[1].set_title('Quick Ratio',size=20)
#ax6[1].plot(dates,quick_ratio,'o')
#ax6[1].plot(dates,quick_ratio,'-')
#
#ax6[1].set_xticks(dates_nums)
#ax6[1].set_xticklabels(dates_labels)
#ax6[1].xaxis.set_tick_params(rotation=45, labelsize=30)
#ax6[1].yaxis.set_tick_params(labelsize=30)
#ax6[1].axhline(0,color='black',zorder=3)
#ax6[1].annotate(str(round(quick_ratio[-1],2)),xy=(dates_nums[-1],quick_ratio[-1]),size=20)
#
#
##accounts_receivable_turnover_ratio
##%%
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## plot profitability analysis
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#fig7, ax7 = plt.subplots(3,sharex=True,sharey=False)
#
#fig7.suptitle('Profitability Analysis',size=60)
#
#ax7[0].set_title('ROE | ROA',size=20)
#ax7[0].plot(dates,ROE,'-o',label='ROE')
#ax7[0].plot(dates,ROA,'-o',label='ROA')
#ax7[0].yaxis.set_tick_params(labelsize=30)
#ax7[0].axhline(0,color='black',zorder=3)
#ax7[0].legend(fontsize='x-large')
#ax7[0].annotate(str(round(ROE[-1],2)),xy=(dates_nums[-1],ROE[-1]),size=20)
#ax7[0].annotate(str(round(ROA[-1],2)),xy=(dates_nums[-1],ROA[-1]),size=20)
#
#ax7[1].set_title('PE',size=20)
#ax7[1].plot(dates,PE_ratio,'-o',label='PE')
#ax7[1].fill_between(dates,10,PE_ratio,where=(10>=np.array(PE_ratio)),color='lightgreen',zorder=0,interpolate=True)
#ax7[1].fill_between(dates,10,PE_ratio,where=(10<np.array(PE_ratio)),color='gold',zorder=0,interpolate=True)
#
#ax7[1].set_yticklabels(y_labels)
#ax7[1].yaxis.set_tick_params(labelsize=30)
#ax7[1].axhline(0,color='black',zorder=3)
#ax7[1].set_yscale('symlog')
#ax7[1].annotate(str(round(PE_ratio[-1],2)),xy=(dates_nums[-1],PE_ratio[-1]),size=20)
#
#ax7[2].set_title('EPS',size=20)
#ax7[2].plot(dates,EPS,'-o')
#ax7[2].set_xticks(dates_nums)
#ax7[2].set_xticklabels(dates_labels)
#ax7[2].xaxis.set_tick_params(rotation=45, labelsize=30)
#ax7[2].yaxis.set_tick_params(labelsize=30)
#ax7[2].axhline(0,color='black',zorder=3)
#ax7[2].annotate(str(round(EPS[-1],2)),xy=(dates_nums[-1],EPS[-1]),size=20)
##%%
##~~~~~~~~~~~~~~~~~~~~~~
## plot valuation ratios
##~~~~~~~~~~~~~~~~~~~~~~
#
#fig8, ax8 = plt.subplots(3,sharex=True,sharey=False)
#
#fig8.suptitle('Valuation Analysis',size=60)
#
#ax8[0].set_title('BVPS',size=20)
#ax8[0].plot(dates,BVPS,'-o',label='BVPS')
#ax8[0].yaxis.set_tick_params(labelsize=30)
#ax8[0].axhline(0,color='black',zorder=3)
#ax8[0].annotate(str(round(BVPS[-1],2)),xy=(dates_nums[-1],BVPS[-1]),size=20)
#
#
#ax8[1].set_title('PB Ratio',size=20)
#ax8[1].plot(dates,PB_ratio,'-o',label='PB ratio')
#ax8[1].fill_between(dates,1.5,PB_ratio,where=(1.5>=np.array(PE_ratio)),color='lightgreen',zorder=0,interpolate=True)
#ax8[1].fill_between(dates,1.5,PB_ratio,where=(1.5<np.array(PE_ratio)),color='gold',zorder=0,interpolate=True)
#ax8[1].set_yticklabels(y_labels)
#ax8[1].yaxis.set_tick_params(labelsize=30)
#ax8[1].axhline(0,color='black',zorder=3)
#ax8[1].annotate(str(round(PB_ratio[-1],2)),xy=(dates_nums[-1],PB_ratio[-1]),size=20)
#
#ax8[2].set_title('EPS',size=20)
#ax8[2].plot(dates,EPS,'-o')
#ax8[2].set_xticks(dates_nums)
#ax8[2].set_xticklabels(dates_labels)
#ax8[2].xaxis.set_tick_params(rotation=45, labelsize=30)
#ax8[2].yaxis.set_tick_params(labelsize=30)
#ax8[2].axhline(0,color='black',zorder=3)
#ax8[2].annotate(str(round(EPS[-1],2)),xy=(dates_nums[-1],EPS[-1]),size=20)
#
##%%
#fig1.set_size_inches(32, 18) 
#fig2.set_size_inches(32, 18) 
#fig3.set_size_inches(32, 18) 
#fig4.set_size_inches(32, 18)
#fig5.set_size_inches(32, 18)
#fig6.set_size_inches(32, 18) 
#fig7.set_size_inches(32, 18) 
#fig8.set_size_inches(32, 18)
#
#figure_list = [fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8]
#
#import matplotlib.backends.backend_pdf
#
#pdf = matplotlib.backends.backend_pdf.PdfPages("{}_output.pdf".format(ticker))
#for fig in figure_list: ## will open an empty extra figure :(
#    pdf.savefig( fig )
#pdf.close()
##%%    
#
#
#
#
