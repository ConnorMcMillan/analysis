# -*- coding: utf-8 -*-

#from get_10K_tables_v3 import get_10K_tables_v3,get_10K_filings_lines
from get_10K_tables_v4 import get_10K_tables_v4,get_10K_filings_lines

from get_fin_statements_v4 import get_BSv4, get_ISv4, get_SCFv4
import os
import re
import numpy as np
from scipy.interpolate import interp1d
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import requests as r
import yfinance as yf
import yahoo_fin.stock_info as si
from datetime import datetime
import matplotlib.pyplot as plt
import math
from WBA_models import get_bond_rate,DCF_intrinsic_value,DCF_discount_rate,avg_BVC,BB_intrinsic_value,BB_discount_rate
#%%
#def get_CIK(ticker):
#    DEFAULT_TICKERS = [ticker]
#    URL = 'http://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany'
#    CIK_RE = re.compile(r'.*CIK=(\d{10}).*')
#    
#    cik_dict = {}
#    for ticker in DEFAULT_TICKERS:
#        f = r.get(URL.format(ticker),stream=True)
#        results = CIK_RE.findall(f.text)
#        if len(results):
#            cik_dict[str(ticker).lower()] = str(results[0])
#
#    CIK_num = cik_dict[ticker.lower()][3:]
#    return int(CIK_num)
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
cwd = r'C:\Users\Owner\Documents\Analysis'
#CIK = 1326801 # FB ticker CIK number
#ticker = 'FB'
ticker = 'FB'
CIK = get_CIK(ticker)
print('~'*50)
print('begin analysis for {}'.format(ticker))
print('~'*50)
print(' ')
print('Searching master10K.csv')

company_lines = get_10K_filings_lines(CIK,cwd)

#company_lines = pd.read_csv('testing_df')
print(' ')
print('~'*50)
print('begin scraping of SEC database')
print('~'*50)
#%%
tables_from_10Ks = []
for i in range(len(company_lines)):
#    print(i,company_lines[i:i+1][:]['txt extension'])
    company_line = company_lines[i:i+1][:]
    
    tables_from_10K,urls,parse_output = get_10K_tables_v4(company_line)
    tables_from_10Ks.append(tables_from_10K[0])
    if i ==5:
        break
#tables_from_10Ks,urls = get_10K_tables_v3(company_lines)
#%%
BS_list, shares_out_list, BS_check, BS_multiplier_list, shares_out_multiplier_list, shares_out_string_list = get_BSv4(tables_from_10Ks,company_lines)
IS_list, IS_check, IS_multiplier_list = get_ISv4(tables_from_10Ks,company_lines)
SCF_list, SCF_check, SCF_multiplier_list = get_SCFv4(tables_from_10Ks,company_lines)
#%%
BS_list = [BS.dropna() for BS in BS_list]
IS_list = [IS.dropna() for IS in IS_list]
SCF_list = [SCF.dropna() for SCF in SCF_list]
BS_dict_list = []
IS_dict_list = []
SCF_dict_list = []
# make list of dictionaries for each finanical statement
for BS,IS,SCF in zip(BS_list,IS_list,SCF_list):
    BS_dict = dict(zip(BS[0].str.lower(),BS[1]))
    IS_dict = dict(zip(IS[0].str.lower(),IS[1]))
    SCF_dict = dict(zip(SCF[0].str.lower(),SCF[1]))
    
    BS_dict_list.append(BS_dict)
    IS_dict_list.append(IS_dict)
    SCF_dict_list.append(SCF_dict)
#%%
def get_term(term,statement_dict,match='exact'):
    '''
    gets value for regex 'term' that matches a key in dict
    match = 'exact' if the term matches the entire dict key
    match = 'any' if the term matches part of the dict key
    not case sensitive
    '''
    keys_list = list(statement_dict.keys())
    keys_list = [key.lower() for key in keys_list]
    try:
        for key in keys_list:
            if key is None:
                continue
            if match=='exact':
                if re.fullmatch(term,key):
                    value = statement_dict[key]
                    print('KEY: {0} | Value = {1}'.format(key,value))
                    break
                
            if match=='any':
                if re.search(term,key):
                    value = statement_dict[key]
                    print('KEY: {0} | Value = {1}'.format(key,value))
                    break
        return value
    
    except:
        print('KEY: not found | Value = 0')            
        return 0
#%%
def get_best_term(term,statement_dict):
    '''
    gets value for regex 'term' that matches a key in dict
    match = 'exact' if the term matches the entire dict key
    match = 'any' if the term matches part of the dict key
    not case sensitive
    '''
    keys_list = list(statement_dict.keys())
    keys_list = [key.lower() for key in keys_list]
    
    score_list = []
    for key in keys_list:
        find = re.findall(term,key)
        score = find
        
    try:
        for key in keys_list:
            if key is None:
                continue
            if match=='exact':
                if re.fullmatch(term,key):
                    value = statement_dict[key]
                    print('KEY: {0} | Value = {1}'.format(key,value))
                    break
                
            if match=='any':
                if re.search(term,key):
                    value = statement_dict[key]
                    print('KEY: {0} | Value = {1}'.format(key,value))
                    break
        return value
    
    except:
        print('KEY: not found | Value = 0')            
        return 0

#%%
net_income = [get_term('net\s*income',IS_dict,match='any') for IS_dict in IS_dict_list]
# earnings per share
EPS = [net_in/shares_out for net_in,shares_out in zip(net_income,shares_out_list)]

total_stockholders_equity = [get_term('total\s*(stockholders\'|shareholders’|shareholders\'|shareholders)\s*equity',BS_dict,match='any') for BS_dict in BS_dict_list]
# book value per share
BVPS = [total_stock_equity/shares_out for total_stock_equity,shares_out in zip(total_stockholders_equity,shares_out_list)]
#%%

def yahoo_5yr_growth(ticker):
# get analyst projections for future growth
#    ticker = 'FB'
    yahoo_url = r'https://finance.yahoo.com/quote/'+ticker+'/analysis?p='+ticker
    yahoo_request = requests.get(yahoo_url)
    yahoo_soup = bs(yahoo_request.content,'lxml')
    yahoo_tables_body = [[[td.get_text(strip=True) for td in tr.find_all('td')] for tr in table.find_all('tr')] for table in yahoo_soup.find_all('table')]
    yahoo_tables_headers = [[[th.get_text(strip=True) for th in tr.find_all('th')] for tr in table.find_all('tr')] for table in yahoo_soup.find_all('table')]
    yahoo_tables = [pd.DataFrame(yahoo_tables_body,columns = yahoo_tables_headers[0]) for yahoo_tables_body,yahoo_tables_headers in zip(yahoo_tables_body,yahoo_tables_headers)]
    
    # 5 year growth estimates
    growth_table = yahoo_tables[5]
#    growth_estimates_index = growth_table.index
    growth_estimates_headers = growth_table.columns
    growth_estimates = growth_table[growth_estimates_headers[0:2]]
    next_5_years = growth_estimates.iloc[5][1]
    next_5_years = next_5_years.replace('%','')
    next_5_years = float(next_5_years)/100
    return next_5_years
#%%
today = datetime.today().strftime('%Y-%m-%d')
ticker_obj = yf.Ticker(ticker)
# start at beginning of month
st_date = re.sub('\d{2}$','01',company_lines.iloc[0]['date'])
ticker_hist = ticker_obj.history(start=st_date,end=today)
hist_dates = ticker_hist.index.strftime('%Y-%m-%d')
hist_dates_nums = [datetime.strptime(date,'%Y-%m-%d') for date in hist_dates]
hist_dates_nums = [date.toordinal() for date in hist_dates_nums]
ticker_hist = dict(zip(hist_dates,ticker_hist['Close']))
filing_dates = company_lines['date']
#%%
# find the market value of the stock when 10K was filed
market_price = [ticker_hist[filing_date] for filing_date in filing_dates]

# price to earnings ratio (market price)/(EPS) WBA: PE < 15 or 6.67% return at least
PE_ratio = [market_price/EP_share for market_price,EP_share in zip(market_price,EPS)]

# price to book ratio (market price)/(book value per share) WBA: PB< 1.5
PB_ratio = [market_price/BV_share for market_price,BV_share in zip(market_price,BVPS)]

#%%
# income statement ratio analysis

# gross profit margin ratio
revenue = [get_term('(?:total)?\s*(?:net)?\s*(revenue|sales)',IS_dict,match='any') for IS_dict in IS_dict_list]
cost_of_revenue = [get_term('cost\s*of\s*(revenue|sales)',IS_dict,match='any') for IS_dict in IS_dict_list]
gross_profit_margin_ratio = [(rev-cost_of_rev)/rev for rev,cost_of_rev in zip(revenue,cost_of_revenue)]
income_from_operations = [get_term('income\s*from\s*operations|operating\s*income',IS_dict,match='any') for IS_dict in IS_dict_list]
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
total_assets = [get_term('total\s*assets',BS_dict,match='any') for BS_dict in BS_dict_list]
total_liabilities_and_stockholders_equity = [get_term('total\s*liabilities\s*and\s*(stockholders\'|shareholders’|shareholders\'|shareholders)\s*equity',BS_dict,match='any') for BS_dict in BS_dict_list]
# total short term and long term liabilities
total_liabilities = [total_liabilities_and_stock_equity-total_stock_equity for total_liabilities_and_stock_equity,total_stock_equity in zip(total_liabilities_and_stockholders_equity,total_stockholders_equity)]
#total_equity = [total_assets-total_liabilities for total_assets,total_liabilities in zip(total_assets,total_liabilities)]
ROE = [net_in/total_stock_equity for net_in,total_stock_equity in zip(net_income,total_stockholders_equity)]
ROE_percent = [ROE*100 for ROE in ROE]

# return on assets ROA or return on invenstment ROI
ROA = [net_in/total_asst for net_in,total_asst in zip(net_income,total_assets)]

#~~~~~~~~~~~~~~~~~
# liquidity ratios
#~~~~~~~~~~~~~~~~~
# current ratio (current assets)/(current liabilities) WBA: loose: 1 < current rato < 5 | tight: 1.5 < current rato < 2.5
# financing structure, good measure of risk
current_assets = [get_term('total\s*current\s*assets',BS_dict,match='any') for BS_dict in BS_dict_list]
current_liabilities = [get_term('total\s*current\s*liabilities',BS_dict,match='any') for BS_dict in BS_dict_list]
current_ratio = [current_asst/current_liab for current_asst,current_liab in zip(current_assets,current_liabilities)]

# accounts receivable turnover ratio. relevant if company sells on credit
# measure of how quickly company is able to collect payment WBA: a ratio of 5-7 is optimal but can vary depending on the industry
accounts_receivable = [get_term('accounts receivable',BS_dict,match='any') for BS_dict in BS_dict_list]
accounts_receivable_turnover_ratio = [rev/acct_receivable for rev,acct_receivable in zip(revenue,accounts_receivable)]

# accounts payable turnover. relevant if company buys on credit
# measure of good credit and ability to get 'free' short term loans WBA: 2-6 is optimal
accounts_payable = [get_term('accounts payable',BS_dict,match='any') for BS_dict in BS_dict_list]
accounts_payable_turnover_ratio = [rev/acct_payable for rev,acct_payable in zip(revenue,accounts_payable)]

#~~~~~~~~~~~~~~~~
# solvency ratios
#~~~~~~~~~~~~~~~~
# debt/equity ratio (total liabilities-current_liabilities)/(total equity) WBA: DE < .50

# interest bearing debt/equity | interest bearing debt per dollar of equity
DE_ratio = [(total_liab-current_liab)/total_stock_equity for total_liab,total_stock_equity,current_liab in zip(total_liabilities,total_stockholders_equity,current_liabilities)]

# liabilities/equity ratio WBA: LE <.80 considered low risk
# includes non interest-bearing debt as well as interest bearing
LE_ratio = [total_liab/total_stock_equity for total_liab,total_stock_equity in zip(total_liabilities,total_stockholders_equity)] 

depreciation = [get_term('depreciation',SCF_dict,match='any') for SCF_dict in SCF_dict_list]
# solvency ratio. measure of cash flow per dollar of short term and long term liabilites
solvency_ratio = [(net_income-depreciation)/total_liabilities for net_income,total_liabilities,depreciation in zip(net_income,total_liabilities,depreciation)]

# interest coverage ratio WBA: >5
interest_and_other = [get_term('(?:interest)?\s*(?:and)?\s*other\s*(income|expense)',IS_dict,match='any') for IS_dict in IS_dict_list]
interest_coverage_ratio = [income_from_ops/int_and_other for income_from_ops,int_and_other in zip(income_from_operations,interest_and_other)]
#%%
# satement of cash flow ratio analysis

# free cash flow per share
operating_CF = [get_term('operating activities',SCF_dict,match='any') for SCF_dict in SCF_dict_list]
PPE = [get_term('(purchase|purchases|acquisition)\s*of\s*(property.*equipment|equipment.*property)',SCF_dict,match='any') for SCF_dict in SCF_dict_list]
FCF = [(oper_CF+PlntPropEquip)/shares_out for oper_CF,PlntPropEquip,shares_out in zip(operating_CF,PPE,shares_out_list)]

# percent that shareholders gain per dollar of revenue (sales) WBA: FCF/revenue > .05
FCF_to_revenue = [FCF_share/rev for FCF_share,rev in zip(FCF,revenue)]

# investing cash flow to operating cash flow ratio | percent of operating income spent on maintaining and investing in company growth
investing_CF = [get_term('cash.+investing\s*activities',SCF_dict,match='any') for SCF_dict in SCF_dict_list]
investing_CF_to_operating_CF = [invest_CF/oper_CF for invest_CF,oper_CF in zip(investing_CF,operating_CF)]
#%%
dates_list = list(filing_dates)
dates = [datetime.strptime(date,'%Y-%m-%d') for date in dates_list]
dates_nums = [datetime.strptime(date,'%Y-%m-%d').toordinal() for date in dates_list]
dates_nums = np.array(dates_nums)
dates_labels = [datetime.strftime(date,'%b %Y') for date in dates]
#%%
def round_high_num(x_list,place=10):
    cleaned = [value for value in x_list if not math.isnan(value)]
    rounded = []
    for x in cleaned:
        if x>0:
            x -= x % -place        
            rounded.append(x)
        else:
            x -= x % place
            rounded.append(x)
    return [max(rounded),min(rounded)]

def tailing_avg(array,period='whole'):
    if period =='whole':
        n = len(array)
        avgs = []
        rolling_sum=0
        for i in range(n):
            rolling_sum +=array[i]
            rolling_avg = rolling_sum/(i+1)    
            avgs.append(rolling_avg) 
    else:
        period = period
        n=len(array)
        avgs = []
        for i in range(n):
            if i+1>=period:
                period_sum = sum(array[i+1-period:i+1])
                period_avg = period_sum/period
                avgs.append(period_avg)
    return avgs
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
dividends = [get_term('dividend',SCF_dict,match='any') for SCF_dict in SCF_dict_list]
dividends = [div*-1 if div<0 else div for div in dividends]
DPS = [div/shares_out for div,shares_out in zip(dividends,shares_out_list)]
retention_ratio = [(1-DivPS/EarnPS) for DivPS,EarnPS in zip(DPS,EPS)]
SGR = [ROEquit*RR for ROEquit,RR in zip(ROE,retention_ratio)]

# internal growth rate
IGR = [ROAsst*RR for ROAsst,RR in zip(ROA,retention_ratio)]

#%%
# need to estimate a growth rate of FCF for the next n years

plt.style.use('seaborn')
fig1,(ax1a,ax1b) = plt.subplots(2,sharex=True)

tailing_GR_FCF = tailing_avg(GR_FCF,period='whole')
tailing_GR_FCF3 = tailing_avg(GR_FCF,period=3)
tailing_GR_FCF5 = tailing_avg(GR_FCF,period=5)

ax1a.plot(dates,FCF,'-o',color='b',label='FCF')
ax1b.plot(dates[len(dates)-len(GR_FCF):],GR_FCF,'-o',color='b',label='growth rate')
ax1b.plot(dates[len(dates)-len(tailing_GR_FCF):],tailing_GR_FCF,label='tailing avg')
ax1b.plot(dates[len(dates)-len(tailing_GR_FCF3):],tailing_GR_FCF3,label='3-period tailing avg')
ax1b.plot(dates[len(dates)-len(tailing_GR_FCF5):],tailing_GR_FCF5,label='5-period tailing avg')

highest_num = round_high_num(GR_FCF)[0]
lowest_num = round_high_num(GR_FCF)[1]

ax1a.set_title('FCF (per share)',fontsize=20)
ax1a.yaxis.set_tick_params(labelsize=30)
ax1a.axhline(0,color='black')
ax1a.annotate((str(round(FCF[-1],2))),xy=(dates[-1],FCF[-1]),size=20)


ax1b.set_title('YoY Growth FCF',size=20)
ax1b.yaxis.set_tick_params(labelsize=30)
ax1b.set_ylim(lowest_num,highest_num)
ax1b.set_yscale('symlog')
ax1b.set_xticks(dates_nums)
ax1b.set_xticklabels(dates_labels)
ax1b.xaxis.set_tick_params(rotation=45, labelsize=30)
ax1b.legend(fontsize=20,loc='upper left')
ax1b.axhline(0,color='black')


y_labels,y_locs = plt.yticks()
y_labels = [str(int(y))+'%' for y in y_labels]
ax1b.set_yticklabels(y_labels)
for index,(i,j) in enumerate(zip(dates[1:],GR_FCF)):
    ax1b.annotate((str(round(j))+'%'),xy=(i,j),size=20)
#%%
fig2,(ax2a,ax2b) = plt.subplots(2,sharex=True)

tailing_SGR = tailing_avg(SGR,period='whole')
tailing_SGR3 = tailing_avg(SGR,period=3)
tailing_SGR5 = tailing_avg(SGR,period=5)

ax2a.plot(dates_nums,SGR,'-o',color='b',label='SGR')
ax2a.plot(dates,tailing_SGR,label='tailing avg')
ax2a.plot(dates[len(dates)-len(tailing_SGR3):],tailing_SGR3,label='3-period tailing avg')
ax2a.plot(dates[len(dates)-len(tailing_SGR5):],tailing_SGR5,label='5-period tailing avg')

ax2a.annotate((str(round(SGR[-1],2))),xy=(dates[-1],SGR[-1]),size=20)
ax2a.annotate((str(round(tailing_SGR[-1],2))),xy=(dates[-1],tailing_SGR[-1]),size=20)
ax2a.annotate((str(round(tailing_SGR3[-1],2))),xy=(dates[-1],tailing_SGR3[-1]),size=20)
ax2a.annotate((str(round(tailing_SGR5[-1],2))),xy=(dates[-1],tailing_SGR5[-1]),size=20)


tailing_IGR = tailing_avg(IGR,period='whole')
tailing_IGR3 = tailing_avg(IGR,period=3)
tailing_IGR5 = tailing_avg(IGR,period=5)


ax2b.plot(dates_nums,IGR,'-o',color='g',label='IGR')
ax2b.plot(dates,tailing_IGR,label='tailing avg')
ax2b.plot(dates[len(dates)-len(tailing_IGR3):],tailing_IGR3,label='3-period tailing avg')
ax2b.plot(dates[len(dates)-len(tailing_IGR5):],tailing_IGR5,label='5-period tailing avg')

ax2b.annotate((str(round(IGR[-1],2))),xy=(dates[-1],IGR[-1]),size=20)
ax2b.annotate((str(round(tailing_IGR[-1],2))),xy=(dates[-1],tailing_IGR[-1]),size=20)
ax2b.annotate((str(round(tailing_IGR3[-1],2))),xy=(dates[-1],tailing_IGR3[-1]),size=20)
ax2b.annotate((str(round(tailing_IGR5[-1],2))),xy=(dates[-1],tailing_IGR5[-1]),size=20)

ax2b.set_xticks(dates_nums)
ax2b.set_xticklabels(dates_labels)
ax2b.xaxis.set_tick_params(rotation=45, labelsize=30)
ax2a.yaxis.set_tick_params(labelsize=30)
ax2b.yaxis.set_tick_params(labelsize=30)
ax2a.axhline(0,color='black')
ax2b.axhline(0,color='black')

ax2a.set_title('SGR',fontsize=20)
ax2b.set_title('IGR',fontsize=20)
ax2a.legend(fontsize=20)
ax2b.legend(fontsize=20)
#%%
FCF_margin = [FCF/revenue*shares_out_list for FCF,revenue,shares_out_list in zip(FCF,revenue,shares_out_list)]
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Discounted FCF model parameters
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# larger of 2.0% growth or 10 year bond rate
bond_rate_10yr = get_bond_rate(term='10 yr')[0]/100
if bond_rate_10yr >= 0.020:
    LGR = bond_rate_10yr
else:
    LGR = .020
#%%
# average of 5-yr SGR tailing average and 5-yr GR FCF tailing avgerage
GR_5years = np.ones(5)*yahoo_5yr_growth(ticker)

GR_5yr_tailing = (tailing_SGR5[-1]+tailing_GR_FCF5[-1]/100)/2
GR_3yr_tailing = (tailing_SGR3[-1]+tailing_GR_FCF3[-1]/100)/2

# future growth rate from years 6-10 lesser of 5yr, 3yr, or LGR rate
if GR_5yr_tailing <= GR_5years[0]:    
    GR_next_5years = np.linspace(GR_5years[0],GR_5yr_tailing,7)[1:-1]
    print('5yr')
elif GR_3yr_tailing <=GR_5years[0]:
    GR_next_5years = np.linspace(GR_5years[0],GR_3yr_tailing,7)[1:-1]
    print('3yr')
elif LGR <= GR_5years[0]:
    GR_next_5years = np.linspace(GR_5years[0],LGR,7)[1:-1]
    print('LGR')

GR_years = np.concatenate([GR_5years,GR_next_5years])
#%%
# DCF intrnisic value model parameters
n=5
DR_low = .08
DR_hi = .12
DR_range = np.linspace(DR_low*100,DR_hi*100,int(DR_hi*100-DR_low*100+1))/100
BYFCF = FCF[-1]
GR_years = GR_years[:n]
LGR = .03
# adjust for current information
SGR[-1] = yahoo_5yr_growth(ticker)

DCF_intrinsic_val_list = []
for DR in DR_range:
    intrinsic_val_list = []
    for GR,BYFCF in zip(SGR,FCF):
        GR_years = np.ones(n)*GR
        print('GR = {0} | FCF = {1}'.format(GR,BYFCF))
        
        val = DCF_intrinsic_value(DR,BYFCF,GR_years,LGR,n=n)
        intrinsic_val_list.append(val[0])
    DCF_intrinsic_val_list.append(intrinsic_val_list)
#%%

# get 1yr avg analyst price target form yahoo 
quote_table = si.get_quote_table(ticker, dict_result=False)
analyst_1yr_target = quote_table.iloc[0][1]
# get corresponding discount rate from anaylst target
DRo = .10
DCF_analyst_1yr_DR = DCF_discount_rate(DRo,analyst_1yr_target,BYFCF,GR_years,LGR,n=n)
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plotting DCF intrinsic value model
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# fit spline to intrinsic values
DCF_cspline_list = []
DCF_cspline_dates_nums = [hist_dates_nums[0]]+ dates_nums.tolist()+[hist_dates_nums[-1]]
for intrinsic_val_list,DR in zip(DCF_intrinsic_val_list,DR_range):
    DCF_cspline_val_list = [intrinsic_val_list[0]]+intrinsic_val_list+[intrinsic_val_list[-1]]
    DCF_cspline = interp1d(DCF_cspline_dates_nums,DCF_cspline_val_list,kind='cubic')
    DCF_cspline_list.append(DCF_cspline)
#%%
# get anaylst intrinsic value list from back-calculated discount rate
anaylst_intrinsic_val_list = []
for GR,BYFCF in zip(SGR,FCF):
    GR_years = np.ones(n)*GR
    val = DCF_intrinsic_value(DCF_analyst_1yr_DR,BYFCF,GR_years,LGR,n=n)
    anaylst_intrinsic_val_list.append(val[0])

# spline for analyst target value
DCF_analyst_spline_val_list = anaylst_intrinsic_val_list
DCF_analyst_spline_val_list = [intrinsic_val_list[0]]+DCF_analyst_spline_val_list+[DCF_analyst_spline_val_list[-1]]
DCF_analyst_spline = interp1d(DCF_cspline_dates_nums,DCF_analyst_spline_val_list,kind='cubic')
#%%
fig3, ax3 = plt.subplots()

fig3.suptitle('DCF model'.format(n,LGR),size=60)

# plot historical closing price data
ax3.set_title('n={0} LGR={1}'.format(n,LGR),size=40)
ax3.plot(hist_dates_nums,[ticker_hist[date] for date in hist_dates])

# plot intrinsic value for each discount rate
for spline,DR,intrinsic_val_list in zip(DCF_cspline_list,DR_range,DCF_intrinsic_val_list):
    ax3.plot(hist_dates_nums,spline(hist_dates_nums),'-',color='g',label=str(DR*100)+'%')
    ax3.plot(dates_nums,intrinsic_val_list,'o',color='g')

# annotate IV splines
end_intrinsic_vals = [intrinsic_val_list[-1] for intrinsic_val_list in DCF_intrinsic_val_list]
for DR,end_intrinsic_val in zip(DR_range,end_intrinsic_vals):
    ax3.annotate(str(round(DR*100,2))+'%',xy=(dates[-1],end_intrinsic_val),size=20)

# plot analyst target with back-calculated discount rate
ax3.plot(dates_nums,anaylst_intrinsic_val_list,'o',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   
ax3.plot(dates_nums[-1],anaylst_intrinsic_val_list[-1],'o',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
ax3.plot(hist_dates_nums,DCF_analyst_spline(hist_dates_nums),'-',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
ax3.plot(hist_dates_nums[:hist_dates_nums.index(dates_nums[-1])+1],DCF_analyst_spline(hist_dates_nums[:hist_dates_nums.index(dates_nums[-1])+1]),'-',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   

# annotate analyst spline
ax3.annotate(str(round(DCF_analyst_1yr_DR*100,2))+'%',xy=(dates[-1],analyst_1yr_target),size=20)
    
# format axis
ax3.set_xticks(dates_nums)
ax3.set_xticklabels(dates_labels)
ax3.xaxis.set_tick_params(rotation=45, labelsize=30)
ax3.yaxis.set_tick_params(labelsize=30)
ax3.axhline(0,color='black')
xlim_hi = ax3.get_xlim()[1]   
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plotting BB intrinsic value model
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

len(BVPS)
years_between = len(BVPS)-1
GRBV = avg_BVC(BVPS[0],BVPS[-1],years_between)

DR_range
BB_intrinsic_val_list = []
for DR in DR_range:
    BVPS_current_list = []
    intrinsic_val_list = []
    for index,BVPS_current in enumerate(BVPS):
        BVPS_current_list.append(BVPS_current)
        if index==0:
            continue
        
        years_between = len(BVPS_current_list)-1
        GRBV = avg_BVC(BVPS_current_list[0],BVPS_current_list[-1],years_between)
    
        intrinisc_val = BB_intrinsic_value(DR,BVPS_current,GRBV,n=5,Div=0)
        intrinsic_val_list.append(intrinisc_val)
    BB_intrinsic_val_list.append(intrinsic_val_list)
#%%
# calculate analyst DR through BB model given analyst price target
DRo = .10
GRBV = avg_BVC(BVPS[0],BVPS[-1],len(BVPS)-1)
BB_analyst_1yr_DR = BB_discount_rate(DRo,analyst_1yr_target,BVPS[-1],GRBV,n=n,Div=0)
#%%
# build a spline for each discount rate
BB_cspline_list = []
BB_cspline_dates_nums = dates_nums[1:].tolist()+[hist_dates_nums[-1]]
for intrinsic_val_list,DR in zip(BB_intrinsic_val_list,DR_range):
    BB_cspline_val_list = intrinsic_val_list+[intrinsic_val_list[-1]]
    BB_cspline = interp1d(BB_cspline_dates_nums,BB_cspline_val_list,kind='cubic')
    BB_cspline_list.append(BB_cspline)

anaylst_intrinsic_val_list = []
BVPS_current_list = []
for index,BVPS_current in enumerate(BVPS):
    BVPS_current_list.append(BVPS_current)
    if index==0:
        continue
    years_between = len(BVPS_current_list)-1
    GRBV = avg_BVC(BVPS_current_list[0],BVPS_current_list[-1],years_between)
    val = BB_intrinsic_value(BB_analyst_1yr_DR,BVPS_current,GRBV,n=n)
    anaylst_intrinsic_val_list.append(val)

# spline for analyst target value
BB_analyst_spline_val_list = anaylst_intrinsic_val_list
BB_analyst_spline_val_list = BB_analyst_spline_val_list+[BB_analyst_spline_val_list[-1]]
BB_analyst_spline = interp1d(BB_cspline_dates_nums,BB_analyst_spline_val_list,kind='cubic')
#%%
fig4, ax4 = plt.subplots()

fig4.suptitle('BB model',size=60)

# plot historical closing price data
ax4.set_title('n={0} LGR={1}'.format(n,LGR),size=40)

# plot historical closing price data
ax4.plot(hist_dates_nums,[ticker_hist[date] for date in hist_dates])

# plot intrinsic value for each discount rate
for spline,DR,intrinsic_val_list in zip(BB_cspline_list,DR_range,BB_intrinsic_val_list):
    ax4.plot(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):],spline(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):]),'-',color='g',label=str(DR*100)+'%')
    ax4.plot(dates_nums[1:],intrinsic_val_list,'o',color='g')

# annotate IV splines
end_intrinsic_vals = [intrinsic_val_list[-1] for intrinsic_val_list in BB_intrinsic_val_list]
for DR,end_intrinsic_val in zip(DR_range,end_intrinsic_vals):
    ax4.annotate(str(round(DR*100,2))+'%',xy=(dates[-1],end_intrinsic_val),size=20)

# plot analyst target with back-calculated discount rate
ax4.plot(dates_nums[1:],anaylst_intrinsic_val_list,'o',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   
ax4.plot(dates_nums[-1],anaylst_intrinsic_val_list[-1],'o',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
ax4.plot(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):],BB_analyst_spline(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):]),'-',color='orange',label=str(BB_analyst_1yr_DR*100)+'%')   
ax4.plot(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):],BB_analyst_spline(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):]),'-',color='g',label=str(BB_analyst_1yr_DR*100)+'%')   

# annotate analyst spline
ax4.annotate(str(round(BB_analyst_1yr_DR*100,2))+'%',xy=(dates[-1],analyst_1yr_target),size=20)
    
# format axis
ax4.set_xticks(dates_nums)
ax4.set_xticklabels(dates_labels)
ax4.xaxis.set_tick_params(rotation=45, labelsize=30)
ax4.yaxis.set_tick_params(labelsize=30)
ax4.axhline(0,color='black')
#%%
#~~~~~~~~~~~~~~~~~~~~~~~
# plot solvency analysis
#~~~~~~~~~~~~~~~~~~~~~~~

fig5,(ax5) = plt.subplots(nrows=2, ncols=2,sharex=True,sharey=False)

fig5.suptitle('Solvency Analysis',size=60)

# upper left
ax5[0,0].set_title('DE ratio',size=20)
ax5[0,0].plot(dates,DE_ratio,'-o',color='blue',zorder=3)

ax5[0,0].fill_between(dates,.50,DE_ratio,where=(.50>np.array(DE_ratio)),color='lightgreen',zorder=0,interpolate=True)
ax5[0,0].fill_between(dates,.50,DE_ratio,where=(.50<=np.array(DE_ratio)),color='lightyellow',zorder=0,interpolate=True)

ax5[0,0].axhline(0,color='black',zorder=3)
ax5[0,0].set_xlim([ax5[0,0].get_xlim()[0],ax5[0,0].get_xlim()[1]])
ax5[0,0].set_ylim(0,max(DE_ratio)*2)
ax5[0,0].set_axisbelow(False)
ax5[0,0].yaxis.set_tick_params(labelsize=20)
ax5[0,0].annotate(str(round(DE_ratio[-1],2)),xy=(dates[-1],DE_ratio[-1]),size=20)

# upper right
ax5[0,1].set_title('LE ratio',size=20)
ax5[0,1].plot(dates,LE_ratio,'-o',color='blue',zorder=3)

ax5[0,1].fill_between(dates,.80,LE_ratio,where=(.80>np.array(LE_ratio)),color='lightgreen',zorder=0,interpolate=True)
ax5[0,1].fill_between(dates,.80,LE_ratio,where=(.80<=np.array(LE_ratio)),color='lightyellow',zorder=0,interpolate=True)

ax5[0,1].axhline(0,color='black',zorder=3)
ax5[0,1].set_xlim([ax5[0,0].get_xlim()[0],ax5[0,0].get_xlim()[1]])
ax5[0,1].set_ylim(0,max(LE_ratio)*2)
ax5[0,1].set_axisbelow(False)
ax5[0,1].yaxis.set_tick_params(labelsize=20)
ax5[0,1].annotate(str(round(LE_ratio[-1],2)),xy=(dates[-1],LE_ratio[-1]),size=20)

# lower left
ax5[1,0].set_title('Solvency Ratio',size=20)
ax5[1,0].plot(dates,solvency_ratio,'-o',color='blue',zorder=3)

ax5[1,0].fill_between(dates,.20,solvency_ratio,where=(.20<np.array(solvency_ratio)),color='lightgreen',zorder=0,interpolate=True)
ax5[1,0].fill_between(dates,.20,solvency_ratio,where=(.20>=np.array(solvency_ratio)),color='lightyellow',zorder=0,interpolate=True)

ax5[1,0].axhline(0,color='black',zorder=3)
ax5[1,0].set_ylim(min(solvency_ratio)*2,max(solvency_ratio)*2)

ax5[1,0].set_xticks(dates_nums)
ax5[1,0].set_xticklabels(dates_labels)
ax5[1,0].xaxis.set_tick_params(rotation=45, labelsize=20)
ax5[1,0].yaxis.set_tick_params(labelsize=20)
ax5[1,0].annotate(str(round(solvency_ratio[-1],2)),xy=(dates[-1],solvency_ratio[-1]),size=20)

# lower right
ax5[1,1].set_title('Interest Coverage Ratio',size=20)
ax5[1,1].plot(dates,interest_coverage_ratio,'-o',color='blue',zorder=3)

# lgoical expressions for shading
logical1 = [-5>=np.array(interest_coverage_ratio)]
logical2 = [0<np.array(interest_coverage_ratio)]
combined_logical = np.logical_or(logical1,logical2)
ax5[1,1].fill_between(dates,-5,interest_coverage_ratio,where=(-5<=np.array(interest_coverage_ratio)),color='lightyellow',zorder=0,interpolate=True)
ax5[1,1].fill_between(dates,-5,interest_coverage_ratio,where=(combined_logical[0]),color='lightgreen',zorder=0,interpolate=True)

ax5[1,1].set_yscale('symlog')
y_labels,y_locs = plt.yticks()
y_labels = [str(int(y)) for y in y_labels]
ax5[1,1].set_yticklabels(y_labels)
ax5[1,1].axhline(0,color='black',zorder=3)
ax5[1,1].set_xticks(dates_nums)
ax5[1,1].set_xticklabels(dates_labels)
ax5[1,1].xaxis.set_tick_params(rotation=45, labelsize=20)
ax5[1,1].yaxis.set_tick_params(labelsize=20)
ax5[1,1].annotate(str(round(interest_coverage_ratio[-1],2)),xy=(dates_nums[-1],interest_coverage_ratio[-1]),size=20)
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~
# plot liquidity analysis
#~~~~~~~~~~~~~~~~~~~~~~~~

cash_and_cash = [get_term('cash',BS_dict,match='any') for BS_dict in BS_dict_list]
MS = [get_term('marketable securities',BS_dict) for BS_dict in BS_dict_list]
liquid_assets = [cash_cash+MrktSec+acct_receivable for cash_cash,MrktSec,acct_receivable in zip(cash_and_cash,MS,accounts_receivable)]
# quick ratio (liquid assets)/(current liabilites)
quick_ratio = [liquid_asst/current_liab for liquid_asst,current_liab in zip(liquid_assets,current_liabilities)]

fig6, ax6 = plt.subplots(2,sharex=True,sharey=False)
fig6.suptitle('Liquidity Analysis',size=60)

ax6[0].set_title('Current Ratio',size=20)
ax6[0].plot(dates,current_ratio,'o')
ax6[0].plot(dates,current_ratio,'-')

ax6[0].fill_between(dates,1,5,color='palegreen',zorder=0,interpolate=True)
ax6[0].fill_between(dates,1.5,2.5,color='lightgreen',zorder=0,interpolate=True)

ax6[0].yaxis.set_tick_params(labelsize=30)
ax6[0].axhline(0,color='black',zorder=3)
ax6[0].annotate(str(round(current_ratio[-1],2)),xy=(dates_nums[-1],current_ratio[-1]),size=20)

# plot quick ratio (liquid assets)/(current liabilites)
ax6[1].set_title('Quick Ratio',size=20)
ax6[1].plot(dates,quick_ratio,'o')
ax6[1].plot(dates,quick_ratio,'-')

ax6[1].set_xticks(dates_nums)
ax6[1].set_xticklabels(dates_labels)
ax6[1].xaxis.set_tick_params(rotation=45, labelsize=30)
ax6[1].yaxis.set_tick_params(labelsize=30)
ax6[1].axhline(0,color='black',zorder=3)
ax6[1].annotate(str(round(quick_ratio[-1],2)),xy=(dates_nums[-1],quick_ratio[-1]),size=20)


#accounts_receivable_turnover_ratio
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plot profitability analysis
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~
fig7, ax7 = plt.subplots(3,sharex=True,sharey=False)

fig7.suptitle('Profitability Analysis',size=60)

ax7[0].set_title('ROE | ROA',size=20)
ax7[0].plot(dates,ROE,'-o',label='ROE')
ax7[0].plot(dates,ROA,'-o',label='ROA')
ax7[0].yaxis.set_tick_params(labelsize=30)
ax7[0].axhline(0,color='black',zorder=3)
ax7[0].legend(fontsize='x-large')
ax7[0].annotate(str(round(ROE[-1],2)),xy=(dates_nums[-1],ROE[-1]),size=20)
ax7[0].annotate(str(round(ROA[-1],2)),xy=(dates_nums[-1],ROA[-1]),size=20)

ax7[1].set_title('PE',size=20)
ax7[1].plot(dates,PE_ratio,'-o',label='PE')
ax7[1].fill_between(dates,10,PE_ratio,where=(10>=np.array(PE_ratio)),color='lightgreen',zorder=0,interpolate=True)
ax7[1].fill_between(dates,10,PE_ratio,where=(10<np.array(PE_ratio)),color='gold',zorder=0,interpolate=True)

ax7[1].set_yticklabels(y_labels)
ax7[1].yaxis.set_tick_params(labelsize=30)
ax7[1].axhline(0,color='black',zorder=3)
ax7[1].set_yscale('symlog')
ax7[1].annotate(str(round(PE_ratio[-1],2)),xy=(dates_nums[-1],PE_ratio[-1]),size=20)

ax7[2].set_title('EPS',size=20)
ax7[2].plot(dates,EPS,'-o')
ax7[2].set_xticks(dates_nums)
ax7[2].set_xticklabels(dates_labels)
ax7[2].xaxis.set_tick_params(rotation=45, labelsize=30)
ax7[2].yaxis.set_tick_params(labelsize=30)
ax7[2].axhline(0,color='black',zorder=3)
ax7[2].annotate(str(round(EPS[-1],2)),xy=(dates_nums[-1],EPS[-1]),size=20)
#%%
#~~~~~~~~~~~~~~~~~~~~~~
# plot valuation ratios
#~~~~~~~~~~~~~~~~~~~~~~

fig8, ax8 = plt.subplots(3,sharex=True,sharey=False)

fig8.suptitle('Valuation Analysis',size=60)

ax8[0].set_title('BVPS',size=20)
ax8[0].plot(dates,BVPS,'-o',label='BVPS')
ax8[0].yaxis.set_tick_params(labelsize=30)
ax8[0].axhline(0,color='black',zorder=3)
ax8[0].annotate(str(round(BVPS[-1],2)),xy=(dates_nums[-1],BVPS[-1]),size=20)

# price to book ratio (market price)/(book value per share) WBA: PB< 1.5
PB_ratio = [market_price/BVPS for market_price,BVPS in zip(market_price,BVPS)]

ax8[1].set_title('PB Ratio',size=20)
ax8[1].plot(dates,PB_ratio,'-o',label='PB ratio')
ax8[1].fill_between(dates,1.5,PB_ratio,where=(1.5>=np.array(PE_ratio)),color='lightgreen',zorder=0,interpolate=True)
ax8[1].fill_between(dates,1.5,PB_ratio,where=(1.5<np.array(PE_ratio)),color='gold',zorder=0,interpolate=True)
ax8[1].set_yticklabels(y_labels)
ax8[1].yaxis.set_tick_params(labelsize=30)
ax8[1].axhline(0,color='black',zorder=3)
ax8[1].annotate(str(round(PB_ratio[-1],2)),xy=(dates_nums[-1],PB_ratio[-1]),size=20)

ax8[2].set_title('EPS',size=20)
ax8[2].plot(dates,EPS,'-o')
ax8[2].set_xticks(dates_nums)
ax8[2].set_xticklabels(dates_labels)
ax8[2].xaxis.set_tick_params(rotation=45, labelsize=30)
ax8[2].yaxis.set_tick_params(labelsize=30)
ax8[2].axhline(0,color='black',zorder=3)
ax8[2].annotate(str(round(EPS[-1],2)),xy=(dates_nums[-1],EPS[-1]),size=20)

#%%
fig1.set_size_inches(32, 18) 
fig2.set_size_inches(32, 18) 
fig3.set_size_inches(32, 18) 
fig4.set_size_inches(32, 18)
fig5.set_size_inches(32, 18)
fig6.set_size_inches(32, 18) 
fig7.set_size_inches(32, 18) 
fig8.set_size_inches(32, 18)

figure_list = [fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8]

import matplotlib.backends.backend_pdf

pdf = matplotlib.backends.backend_pdf.PdfPages("{}_output.pdf".format(ticker))
for fig in figure_list: ## will open an empty extra figure :(
    pdf.savefig( fig )
pdf.close()
#%%
# save a dataframe of all 

output_headers = ['dates_list','dates_nums','net_income','EPS','total_stockholders_equity','BVPS','market_price','PE_ratio','PB_ratio',' \
revenue','cost_of_revenue','gross_profit_margin_ratio','income_from_operations',' \
operating_margin_ratio','net_income_margin_ratio','total_assets','total_liabilities_and_stockholders_equity',' \
total_liabilities','ROE','ROE_percent','ROA','current_assets','current_liabilities','current_ratio',' \
accounts_receivable','accounts_receivable_turnover_ratio','accounts_payable',' \
accounts_payable_turnover_ratio','DE_ratio','LE_ratio','depreciation','solvency_ratio','interest_and_other',' \
interest_coverage_ratio','operating_CF','PPE','FCF','FCF_to_revenue','investing_CF',' \
investing_CF_to_operating_CF','GR_FCF','dividends','DPS','retention_ratio','SGR','IGR','FCF_margin',' \
cash_and_cash','MS','liquid_assets','quick_ratio','PB_ratio']

data_output = pd.DataFrame([dates_list,dates_nums,net_income,EPS,total_stockholders_equity,BVPS,market_price,PE_ratio,PB_ratio, \
revenue,cost_of_revenue,gross_profit_margin_ratio,income_from_operations, \
operating_margin_ratio,net_income_margin_ratio,total_assets,total_liabilities_and_stockholders_equity, \
total_liabilities,ROE,ROE_percent,ROA,current_assets,current_liabilities,current_ratio, \
accounts_receivable,accounts_receivable_turnover_ratio,accounts_payable, \
accounts_payable_turnover_ratio,DE_ratio,LE_ratio,depreciation,solvency_ratio,interest_and_other, \
interest_coverage_ratio,operating_CF,PPE,FCF,FCF_to_revenue,investing_CF, \
investing_CF_to_operating_CF,GR_FCF,dividends,DPS,retention_ratio,SGR,IGR,FCF_margin, \
cash_and_cash,MS,liquid_assets,quick_ratio,PB_ratio]).transpose()
data_output.columns = output_headers
    




