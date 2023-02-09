# -*- coding: utf-8 -*-
# C:\Users\Owner\Documents\analysis

import matplotlib.pyplot as plt
import math
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from WBA_models import get_bond_rate,DCF_intrinsic_value,DCF_discount_rate,avg_BVC,BB_intrinsic_value,BB_discount_rate
import yahoo_fin.stock_info as si
from scipy.interpolate import interp1d
import re
import yfinance as yf
import requests
from bs4 import BeautifulSoup as bs
#%%
ticker = 'TWTR'
truncate_data = '2015'
n=10 # years predicting into future 
p=5 # past years data used in tailing growth averages
#%%
clean_data_path = r'C:\Users\Owner\Documents\Analysis_Database\clean_data.db'
conn = sqlite3.connect(clean_data_path)
if truncate_data==False:
    clean_data = pd.read_sql("""SELECT * FROM {}""".format(ticker),con=conn)
else:
    truncate_num = datetime.strptime(truncate_data,'%Y').toordinal()
    clean_data = pd.read_sql("""SELECT * FROM {} WHERE dates_nums>{}""".format(ticker,truncate_num),con=conn)
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

def tailing_geo_avg(array,period='whole',expressed='decimal'):
    """
    input array expressed as decimal or percent in arg3
    """
    if expressed=='decimal':
        array = np.array(array)+1
    if expressed=='percent':
        array = np.array(array)/100+1
        
    if period =='whole':
        n = len(array)
        avgs = []
        rolling_product=1
        for i in range(n):
            rolling_product = array[i]*rolling_product
            rolling_geo_avg = (rolling_product)**(1/n)
            avgs.append(rolling_geo_avg) 
    else:
        period = period
        n=len(array)
        avgs = []
        for i in range(n):
            if i+1>=period:
                period_prod = np.prod(array[i+1-period:i+1])
                period_geo_avg = period_prod**(1/period)
                avgs.append(period_geo_avg)
    return np.array(avgs)-1

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
    if next_5_years!='N/A':
        next_5_years = float(next_5_years)/100
    else:
        next_5_years = 'N/A'
    return next_5_years
#%%
dates_list,dates_nums,net_income,EPS,shares_outstanding,total_stockholders_equity,BVPS,market_price,PE_ratio,PB_ratio, \
revenue,cost_of_revenue,gross_profit_margin_ratio,income_from_operations, \
operating_margin_ratio,net_income_margin_ratio,total_assets,total_liabilities_and_stockholders_equity, \
total_liabilities,ROE,ROE_percent,ROA,current_assets,current_liabilities,current_ratio, \
accounts_receivable,accounts_receivable_turnover_ratio,accounts_payable, \
accounts_payable_turnover_ratio,DE_ratio,LE_ratio,depreciation,solvency_ratio,nonoperating_income_expense, \
interest_coverage_ratio,operating_CF,PPE,FCF,FCF_to_revenue,investing_CF, \
investing_CF_to_operating_CF,GR_FCF,dividends,DPS,retention_ratio,SGR,IGR,FCF_margin, \
cash_and_cash,MS,liquid_assets,quick_ratio = list(clean_data['dates_list']),list(clean_data['dates_nums']),list(clean_data['net_income']),list(clean_data['EPS']),list(clean_data['shares_outstanding']),list(clean_data['total_stockholders_equity']),list(clean_data['BVPS']),list(clean_data['market_price']),list(clean_data['PE_ratio']),list(clean_data['PB_ratio']), \
list(clean_data['revenue']),list(clean_data['cost_of_revenue']),list(clean_data['gross_profit_margin_ratio']),list(clean_data['income_from_operations']), \
list(clean_data['operating_margin_ratio']),list(clean_data['net_income_margin_ratio']),list(clean_data['total_assets']),list(clean_data['total_liabilities_and_stockholders_equity']), \
list(clean_data['total_liabilities']),list(clean_data['ROE']),list(clean_data['ROE_percent']),list(clean_data['ROA']),list(clean_data['current_assets']),list(clean_data['current_liabilities']),list(clean_data['current_ratio']), \
list(clean_data['accounts_receivable']),list(clean_data['accounts_receivable_turnover_ratio']),list(clean_data['accounts_payable']), \
list(clean_data['accounts_payable_turnover_ratio']),list(clean_data['DE_ratio']),list(clean_data['LE_ratio']),list(clean_data['depreciation']),list(clean_data['solvency_ratio']),list(clean_data['nonoperating_income_expense']), \
list(clean_data['interest_coverage_ratio']),list(clean_data['operating_CF']),list(clean_data['PPE']),list(clean_data['FCF']),list(clean_data['FCF_to_revenue']),list(clean_data['investing_CF']), \
list(clean_data['investing_CF_to_operating_CF']),list(clean_data['GR_FCF']),list(clean_data['dividends']),list(clean_data['DPS']),list(clean_data['retention_ratio']),list(clean_data['SGR']),list(clean_data['IGR']),list(clean_data['FCF_margin']), \
list(clean_data['cash_and_cash']),list(clean_data['MS']),list(clean_data['liquid_assets']),list(clean_data['quick_ratio'])
#%%
dates = [datetime.strptime(date,'%Y-%m-%d') for date in dates_list]
dates_labels = [datetime.strftime(date,'%b %Y') for date in dates]
#%%
today = datetime.today().strftime('%Y-%m-%d')
ticker_obj = yf.Ticker(ticker)
# start history 14 days prior to actual statement data for plotting purposes
st_date = re.sub(r'(\d{4})(\d{2})(\d{2})',r'\1-\2-\3',dates_list[0])
st_date_obj = datetime.strptime(st_date,'%Y-%m-%d')-timedelta(days=14)
st_date_adjusted = st_date_obj.strftime('%Y-%m-%d')
ticker_hist = ticker_obj.history(start=st_date_adjusted,end=today)
hist_dates = ticker_hist.index.strftime('%Y-%m-%d')
hist_dates_objs = [datetime.strptime(date,'%Y-%m-%d') for date in hist_dates]
hist_dates_nums = [date.toordinal() for date in hist_dates_objs]
ticker_hist = dict(zip(hist_dates,ticker_hist['Close']))
filing_dates = [re.sub(r'(\d{4})(\d{2})(\d{2})',r'\1-\2-\3',submission_line) for submission_line in dates_list]
#%%

# get growth rates from google sheet
from googleapiclient.discovery import build
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = None
creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
SPREADSHEET_ID = '1HkgkGzyZfaUO80AMMYniIij1_euYKTtj50Xo2E7A0hk'

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range='a1:i12').execute()
values = result.get('values', [])

GR_df = pd.DataFrame(values,index=None)
#%%
GR_list=[]
for i in range(len(GR_df.columns)):
    if i>1:
        GR_list.append([float(x) for x in list(GR_df[i][2:])])
#%%
LGR = 0.02
n = 10
BYFCF = .98
DR = .07
#GR = np.ones(10)*.10

#DCF_intrinsic_value(DR,BYFCF,GR,LGR,n=n)

IV_list = []
for BYFCF,GR in zip(FCF,GR_list):
    IV = DCF_intrinsic_value(DR,BYFCF,GR,LGR,n=n)[0]
    IV_list.append(IV)
#%%
fig1,ax1 = plt.subplots()
plot_title = 'DCF intrinsic value'
fig1.suptitle(plot_title,size=60)

# plot historical closing price data
ax1.set_title('n={0} LGR={1}'.format(n,LGR),size=40)
ax1.plot(hist_dates_nums,[ticker_hist[date] for date in hist_dates])

ax1.plot(dates_nums,IV_list,'o',color='orange')
ax1.step(dates_nums+[hist_dates_nums[-1]],IV_list+[IV_list[-1]], where='post',color='orange')

ax1.set_xticks(dates_nums)
ax1.set_xticklabels(dates_labels)
ax1.xaxis.set_tick_params(rotation=45, labelsize=30)
ax1.yaxis.set_tick_params(labelsize=30)
ax1.axhline(0,color='black')
xlim_hi = ax1.get_xlim()[1]   

xlims = [None,None]
ylims = [None,None]

xlim_upper = xlims[1]
xlim_lower = xlims[0]
ax1.set_xlim(left = xlim_lower,right = xlim_upper)

ylim_upper = ylims[1]
ylim_lower = ylims[0]
ax1.set_ylim(bottom = ylim_lower,top = ylim_upper)

plt.show()
#%%




