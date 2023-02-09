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
n=5 # years predicting into future 
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# arithmetic rolling average GR FCF
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

plt.style.use('seaborn')
fig1,(ax1a,ax1b) = plt.subplots(2,sharex=True)

GR_FCF = [rate for rate in GR_FCF if not math.isnan(rate)]
tailing_GR_FCF = tailing_avg(GR_FCF,period='whole')
tailing_GR_FCF3 = tailing_avg(GR_FCF,period=3)
tailing_GR_FCF5 = tailing_avg(GR_FCF,period=5)
tailing_GR_FCFp = tailing_avg(GR_FCF,period=p)


ax1a.plot(dates,FCF,'-o',color='b',label='FCF')
ax1b.plot(dates[len(dates)-len(GR_FCF):],GR_FCF,'-o',color='b',label='growth rate')
ax1b.plot(dates[len(dates)-len(tailing_GR_FCF):],tailing_GR_FCF,label='tailing avg')
ax1b.plot(dates[len(dates)-len(tailing_GR_FCF3):],tailing_GR_FCF3,label='3-period tailing avg')
ax1b.plot(dates[len(dates)-len(tailing_GR_FCF5):],tailing_GR_FCF5,label='5-period tailing avg')
ax1b.plot(dates[len(dates)-len(tailing_GR_FCFp):],tailing_GR_FCFp,label='{}-period tailing avg'.format(p))


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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# geometic rolling average GR FCF
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

plt.style.use('seaborn')
fig13,(ax13a,ax13b) = plt.subplots(2,sharex=True)

GR_FCF = [rate for rate in GR_FCF if not math.isnan(rate)]
tailing_geo_GR_FCF = tailing_geo_avg(GR_FCF,period='whole',expressed='percent')
tailing_geo_GR_FCF3 = tailing_geo_avg(GR_FCF,period=3,expressed='percent')
tailing_geo_GR_FCF5 = tailing_geo_avg(GR_FCF,period=5,expressed='percent')
tailing_geo_GR_FCFp = tailing_geo_avg(GR_FCF,period=p,expressed='percent')


ax13a.plot(dates,FCF,'-o',color='b',label='FCF')
ax13b.plot(dates[len(dates)-len(GR_FCF):],GR_FCF,'-o',color='b',label='growth rate')
ax13b.plot(dates[len(dates)-len(tailing_geo_GR_FCF):],tailing_geo_GR_FCF,label='tailing geo avg')
ax13b.plot(dates[len(dates)-len(tailing_geo_GR_FCF3):],tailing_geo_GR_FCF3,label='3-period geo tailing avg')
ax13b.plot(dates[len(dates)-len(tailing_geo_GR_FCF5):],tailing_geo_GR_FCF5,label='5-period geo tailing avg')
ax13b.plot(dates[len(dates)-len(tailing_geo_GR_FCFp):],tailing_geo_GR_FCFp,label='{}-period geo tailing avg'.format(p))


highest_num = round_high_num(GR_FCF)[0]
lowest_num = round_high_num(GR_FCF)[1]

ax13a.set_title('FCF (per share)',fontsize=20)
ax13a.yaxis.set_tick_params(labelsize=30)
ax13a.axhline(0,color='black')
ax13a.annotate((str(round(FCF[-1],2))),xy=(dates[-1],FCF[-1]),size=20)


ax13b.set_title('YoY Growth FCF',size=20)
ax13b.yaxis.set_tick_params(labelsize=30)
ax13b.set_ylim(lowest_num,highest_num)
ax13b.set_yscale('symlog')
ax13b.set_xticks(dates_nums)
ax13b.set_xticklabels(dates_labels)
ax13b.xaxis.set_tick_params(rotation=45, labelsize=30)
ax13b.legend(fontsize=20,loc='upper left')
ax13b.axhline(0,color='black')


y_labels,y_locs = plt.yticks()
y_labels = [str(int(y))+'%' for y in y_labels]
ax13b.set_yticklabels(y_labels)
for index,(i,j) in enumerate(zip(dates[1:],GR_FCF)):
    ax13b.annotate((str(round(j))+'%'),xy=(i,j),size=20)
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# arithmetic rolling average SGR, IGR
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

fig2,(ax2a,ax2b) = plt.subplots(2,sharex=True)

tailing_SGR = tailing_avg(SGR,period='whole')
tailing_SGR3 = tailing_avg(SGR,period=3)
tailing_SGR5 = tailing_avg(SGR,period=5)
tailing_SGRp = tailing_avg(SGR,period=p)

ax2a.plot(dates_nums,SGR,'-o',color='b',label='SGR')
ax2a.plot(dates,tailing_SGR,label='tailing avg')
ax2a.plot(dates[len(dates)-len(tailing_SGR3):],tailing_SGR3,label='3-period tailing avg')
ax2a.plot(dates[len(dates)-len(tailing_SGR5):],tailing_SGR5,label='5-period tailing avg')
ax2a.plot(dates[len(dates)-len(tailing_SGRp):],tailing_SGRp,label='{}-period tailing avg'.format(p))

ax2a.annotate((str(round(SGR[-1],2))),xy=(dates[-1],SGR[-1]),size=20)
ax2a.annotate((str(round(tailing_SGR[-1],2))),xy=(dates[-1],tailing_SGR[-1]),size=20)
ax2a.annotate((str(round(tailing_SGR3[-1],2))),xy=(dates[-1],tailing_SGR3[-1]),size=20)
ax2a.annotate((str(round(tailing_SGR5[-1],2))),xy=(dates[-1],tailing_SGR5[-1]),size=20)
ax2a.annotate((str(round(tailing_SGRp[-1],2))),xy=(dates[-1],tailing_SGRp[-1]),size=20)


tailing_IGR = tailing_avg(IGR,period='whole')
tailing_IGR3 = tailing_avg(IGR,period=3)
tailing_IGR5 = tailing_avg(IGR,period=5)
tailing_IGRp = tailing_avg(IGR,period=p)


ax2b.plot(dates_nums,IGR,'-o',color='g',label='IGR')
ax2b.plot(dates,tailing_IGR,label='tailing avg')
ax2b.plot(dates[len(dates)-len(tailing_IGR3):],tailing_IGR3,label='3-period tailing avg')
ax2b.plot(dates[len(dates)-len(tailing_IGR5):],tailing_IGR5,label='5-period tailing avg')
ax2b.plot(dates[len(dates)-len(tailing_IGRp):],tailing_IGRp,label='{}-period tailing avg'.format(p))

ax2b.annotate((str(round(IGR[-1],2))),xy=(dates[-1],IGR[-1]),size=20)
ax2b.annotate((str(round(tailing_IGR[-1],2))),xy=(dates[-1],tailing_IGR[-1]),size=20)
ax2b.annotate((str(round(tailing_IGR3[-1],2))),xy=(dates[-1],tailing_IGR3[-1]),size=20)
ax2b.annotate((str(round(tailing_IGR5[-1],2))),xy=(dates[-1],tailing_IGR5[-1]),size=20)
ax2b.annotate((str(round(tailing_IGRp[-1],2))),xy=(dates[-1],tailing_IGRp[-1]),size=20)


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
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## geometric rolling average SGR, IGR
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#fig12,(ax12a,ax12b) = plt.subplots(2,sharex=True)
#
#tailing_geo_SGR = tailing_geo_avg(SGR,period='whole')
#tailing_geo_SGR3 = tailing_geo_avg(SGR,period=3)
#tailing_geo_SGR5 = tailing_geo_avg(SGR,period=5)
#tailing_geo_SGRp = tailing_geo_avg(SGR,period=p)
#
#ax12a.plot(dates_nums,SGR,'-o',color='b',label='SGR')
#ax12a.plot(dates,tailing_geo_SGR,label='tailing geo avg')
#ax12a.plot(dates[len(dates)-len(tailing_geo_SGR3):],tailing_geo_SGR3,label='3-period tailing geo avg')
#ax12a.plot(dates[len(dates)-len(tailing_geo_SGR5):],tailing_geo_SGR5,label='5-period tailing geo avg')
#ax12a.plot(dates[len(dates)-len(tailing_geo_SGRp):],tailing_geo_SGRp,label='{}-period tailing geo avg'.format(p))
#
#ax12a.annotate((str(round(SGR[-1],2))),xy=(dates[-1],SGR[-1]),size=20)
#ax12a.annotate((str(round(tailing_geo_SGR[-1],2))),xy=(dates[-1],tailing_geo_SGR[-1]),size=20)
#ax12a.annotate((str(round(tailing_geo_SGR3[-1],2))),xy=(dates[-1],tailing_geo_SGR3[-1]),size=20)
#ax12a.annotate((str(round(tailing_geo_SGR5[-1],2))),xy=(dates[-1],tailing_geo_SGR5[-1]),size=20)
#ax12a.annotate((str(round(tailing_geo_SGRp[-1],2))),xy=(dates[-1],tailing_geo_SGRp[-1]),size=20)
#
#
#tailing_geo_IGR = tailing_geo_avg(IGR,period='whole')
#tailing_geo_IGR3 = tailing_geo_avg(IGR,period=3)
#tailing_geo_IGR5 = tailing_geo_avg(IGR,period=5)
#tailing_geo_IGRp = tailing_geo_avg(IGR,period=p)
#
#
#ax12b.plot(dates_nums,IGR,'-o',color='g',label='IGR')
#ax12b.plot(dates,tailing_geo_IGR,label='tailing geo avg')
#ax12b.plot(dates[len(dates)-len(tailing_geo_IGR3):],tailing_geo_IGR3,label='3-period tailing geo avg')
#ax12b.plot(dates[len(dates)-len(tailing_geo_IGR5):],tailing_geo_IGR5,label='5-period tailing geo avg')
#ax12b.plot(dates[len(dates)-len(tailing_geo_IGRp):],tailing_geo_IGRp,label='{}-period tailing geo avg'.format(p))
#
#ax12b.annotate((str(round(IGR[-1],2))),xy=(dates[-1],IGR[-1]),size=20)
#ax12b.annotate((str(round(tailing_geo_IGR[-1],2))),xy=(dates[-1],tailing_geo_IGR[-1]),size=20)
#ax12b.annotate((str(round(tailing_geo_IGR3[-1],2))),xy=(dates[-1],tailing_geo_IGR3[-1]),size=20)
#ax12b.annotate((str(round(tailing_geo_IGR5[-1],2))),xy=(dates[-1],tailing_geo_IGR5[-1]),size=20)
#ax12b.annotate((str(round(tailing_geo_IGRp[-1],2))),xy=(dates[-1],tailing_geo_IGRp[-1]),size=20)
#
#ax12b.set_xticks(dates_nums)
#ax12b.set_xticklabels(dates_labels)
#ax12b.xaxis.set_tick_params(rotation=45, labelsize=30)
#ax12a.yaxis.set_tick_params(labelsize=30)
#ax12b.yaxis.set_tick_params(labelsize=30)
#ax12a.axhline(0,color='black')
#ax12b.axhline(0,color='black')
#
#ax12a.set_title('SGR',fontsize=20)
#ax12b.set_title('IGR',fontsize=20)
#ax12a.legend(fontsize=20)
#ax12b.legend(fontsize=20)
#
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Discounted FCF model parameters
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# larger of 2.0% growth (inflation) or 10 year bond rate
bond_rate_10yr = get_bond_rate(term='10 yr')[0]/100
inflation_rate = 0.020
LGR = max(bond_rate_10yr,inflation_rate)
#if bond_rate_10yr >= inflation_rate:
#    LGR = bond_rate_10yr
#else:
#    LGR = inflation_rate
#%%
# USED IN OLD VERSION OF PLOTTING 
#    
## average of 5-yr SGR tailing average and 5-yr GR FCF tailing avgerage
#GR_5yr_tailing = (tailing_SGR5[-1]+tailing_GR_FCF5[-1]/100)/2
#GR_3yr_tailing = (tailing_SGR3[-1]+tailing_GR_FCF3[-1]/100)/2
#GR_pyr_tailing = (tailing_SGRp[-1]+tailing_GR_FCF3[-1]/100)/2
#
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
#
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
#%%
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## using SGR only
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##n=5
#DR_low = .08
#DR_hi = .12
#DR_range = np.linspace(DR_low*100,DR_hi*100,int(DR_hi*100-DR_low*100+1))/100
#
#DCF_intrinsic_val_list = []
#for DR in DR_range:
#    intrinsic_val_list = []
#    SGR_years = []
#    for i,(GR,BYFCF) in enumerate(zip(SGR,FCF)):
#       
#        # take a trailing average of SGR for future GR up to a p year period (normally p=5)
#        SGR_years.append(GR)
#        if i>=p:
#            GR_avg = tailing_avg(SGR_years,period=p)[-1]
#        if i<p:            
#            GR_avg = tailing_avg(SGR_years,period=i+1)[-1]
#        GR_years = np.ones(5)*GR_avg
#        print(GR_avg)
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
#DCF_cspline_dates_nums = [hist_dates_nums[0]]+ dates_nums+[hist_dates_nums[-1]]
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
#fig3.suptitle('SGR based DCF model',size=60)
#
## plot historical closing price data
#ax3.set_title('n={0} LGR={1} p={2}'.format(n,LGR,p),size=40)
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
##ax3.plot(dates_nums,anaylst_intrinsic_val_list,'o',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   
##ax3.plot(dates_nums[-1],anaylst_intrinsic_val_list[-1],'o',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
##ax3.plot(hist_dates_nums,DCF_analyst_spline(hist_dates_nums),'-',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
##ax3.plot(hist_dates_nums[:hist_dates_nums.index(dates_nums[-1])+1],DCF_analyst_spline(hist_dates_nums[:hist_dates_nums.index(dates_nums[-1])+1]),'-',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   
##
### annotate analyst spline
##ax3.annotate(str(round(DCF_analyst_1yr_DR*100,2))+'%',xy=(dates[-1],analyst_1yr_target),size=20)
#    
## format axis
#ax3.set_xticks(dates_nums)
#ax3.set_xticklabels(dates_labels)
#ax3.xaxis.set_tick_params(rotation=45, labelsize=30)
#ax3.yaxis.set_tick_params(labelsize=30)
#ax3.axhline(0,color='black')
#xlim_hi = ax3.get_xlim()[1]   
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## end SGR based FCF model
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#%%
from plotting_functions import plotDCF
#p = 4
fig3,ax3 = plotDCF(SGR,FCF,LGR,n,p, \
                   'SGR based DCF',dates,dates_nums,hist_dates, \
                   hist_dates_nums,ticker_hist,dates_labels)

GR_FCF = [GR/100 for GR in GR_FCF if not math.isnan(GR)]

fig9,ax9 = plotDCF(GR_FCF,FCF,LGR,n,p, \
                   'GRFCF based DCF',dates[1:],dates_nums[1:],hist_dates, \
                   hist_dates_nums,ticker_hist,dates_labels[1:], \
                   xlims = [None,None],ylims = [None,None])

SGR_GRFCF_avg = [(i+j)/2 for i,j in zip(SGR[1:],GR_FCF)]
fig10,ax10 = plotDCF(SGR_GRFCF_avg,FCF,LGR,n,p, \
                     'AVG growth based DCF',dates[1:],dates_nums[1:],hist_dates, \
                     hist_dates_nums,ticker_hist,dates_labels[1:], \
                     xlims = [None,None],ylims = [None,None])
#%%
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## using growth rate of FCF only
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#DR_low = .08
#DR_hi = .12
#DR_range = np.linspace(DR_low*100,DR_hi*100,int(DR_hi*100-DR_low*100+1))/100
#
#GR_FCF = [GR/100 for GR in GR_FCF]
#DCF_intrinsic_val_list = []
#for DR in DR_range:
#    intrinsic_val_list = []
#    GRFCF_years = []
#    for i,(GR,BYFCF) in enumerate(zip([0]+GR_FCF,FCF)):
#        if i==0:
#            continue
#       
#        # take a trailing average of SGR for future GR back p year period (normally p=5)
#        GRFCF_years.append(GR)
#        if i>=p:
#            GR_avg = tailing_avg(GRFCF_years,period=p)[-1]
#        if i<p:            
#            GR_avg = tailing_avg(GRFCF_years,period=i)[-1]
#        GR_years = np.ones(5)*GR_avg
#        print(GR_avg)
#        print('GR = {0} | FCF = {1}'.format(GR_avg,BYFCF))
#        
#        val = DCF_intrinsic_value(DR,BYFCF,GR_years,LGR,n=n)
#        
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
#print('here'*20)
## fit spline to intrinsic values
#DCF_cspline_list = []
#DCF_cspline_dates_nums = [hist_dates_nums[0]]+ dates_nums+[hist_dates_nums[-1]]
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
#fig9, ax9 = plt.subplots()
#
#fig9.suptitle('FCF based DCF model',size=60)
#
## plot historical closing price data
#ax9.set_title('n={0} LGR={1} p={2}'.format(n,LGR,p),size=40)
#ax9.plot(hist_dates_nums,[ticker_hist[date] for date in hist_dates])
#
## plot intrinsic value for each discount rate
#for spline,DR,intrinsic_val_list in zip(DCF_cspline_list,DR_range,DCF_intrinsic_val_list):
#    ax9.plot(hist_dates_nums,spline(hist_dates_nums),'-',color='g',label=str(DR*100)+'%')
#    ax9.plot(dates_nums,intrinsic_val_list,'o',color='g')
#
## annotate IV splines
#end_intrinsic_vals = [intrinsic_val_list[-1] for intrinsic_val_list in DCF_intrinsic_val_list]
#for DR,end_intrinsic_val in zip(DR_range,end_intrinsic_vals):
#    ax9.annotate(str(round(DR*100,2))+'%',xy=(dates[-1],end_intrinsic_val),size=20)
#    
## format axis
#ax9.set_xticks(dates_nums)
#ax9.set_xticklabels(dates_labels)
#ax9.xaxis.set_tick_params(rotation=45, labelsize=30)
#ax9.yaxis.set_tick_params(labelsize=30)
#ax9.axhline(0,color='black')
#xlim_hi = ax9.get_xlim()[1] 
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## end FCF based DCF model
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# plotting BB intrinsic value model
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

len(BVPS)
years_between = len(BVPS)-1
GRBV = avg_BVC(BVPS[0],BVPS[-1],years_between)

DR_low = .08
DR_hi = .12
DR_range = np.linspace(DR_low*100,DR_hi*100,int(DR_hi*100-DR_low*100+1))/100


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
#DRo = .10
#GRBV = avg_BVC(BVPS[0],BVPS[-1],len(BVPS)-1)
#BB_analyst_1yr_DR = BB_discount_rate(DRo,analyst_1yr_target,BVPS[-1],GRBV,n=n,Div=0)
#%%
# build a spline for each discount rate
BB_cspline_list = []
BB_cspline_dates_nums = dates_nums[1:]+[hist_dates_nums[-1]]
for intrinsic_val_list,DR in zip(BB_intrinsic_val_list,DR_range):
    BB_cspline_val_list = intrinsic_val_list+[intrinsic_val_list[-1]]
    BB_cspline = interp1d(BB_cspline_dates_nums,BB_cspline_val_list,kind='cubic')
    BB_cspline_list.append(BB_cspline)

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

# spline for analyst target value
#BB_analyst_spline_val_list = anaylst_intrinsic_val_list
#BB_analyst_spline_val_list = BB_analyst_spline_val_list+[BB_analyst_spline_val_list[-1]]
#BB_analyst_spline = interp1d(BB_cspline_dates_nums,BB_analyst_spline_val_list,kind='cubic')
#%%
fig4, ax4 = plt.subplots()

fig4.suptitle('BB model',size=60)

# plot historical closing price data
ax4.set_title('n={0} GR LGR={1}'.format(n,LGR),size=40)

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
#ax4.plot(dates_nums[1:],anaylst_intrinsic_val_list,'o',color='g',label=str(DCF_analyst_1yr_DR*100)+'%')   
#ax4.plot(dates_nums[-1],anaylst_intrinsic_val_list[-1],'o',color='orange',label=str(DCF_analyst_1yr_DR*100)+'%')   
#ax4.plot(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):],BB_analyst_spline(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):]),'-',color='orange',label=str(BB_analyst_1yr_DR*100)+'%')   
#ax4.plot(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):],BB_analyst_spline(hist_dates_nums[hist_dates_nums.index(dates_nums[1]):]),'-',color='g',label=str(BB_analyst_1yr_DR*100)+'%')   
#
## annotate analyst spline
#ax4.annotate(str(round(BB_analyst_1yr_DR*100,2))+'%',xy=(dates[-1],analyst_1yr_target),size=20)
    
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
ax5[1,0].set_ylim(min(solvency_ratio)-.20,max(solvency_ratio)+.20)

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
fig11, ax11 = plt.subplots(1,sharex=True,sharey=False)

ax11.set_title('SGR-FCF growth avg',size=20)
ax11.plot(dates[1:],SGR_GRFCF_avg,'o-')
#ax11[0].plot(dates,current_ratio,'-')

tailing_GR_avg = tailing_avg(SGR_GRFCF_avg,period='whole')
tailing_GR_avg3 = tailing_avg(SGR_GRFCF_avg,period=3)
tailing_GR_avg5 = tailing_avg(SGR_GRFCF_avg,period=5)
tailing_GR_avgp = tailing_avg(SGR_GRFCF_avg,period=p)

ax11.plot(dates[len(dates)-len(tailing_GR_avg):],tailing_GR_avg,label='tailing avg')
ax11.plot(dates[len(dates)-len(tailing_GR_avg3):],tailing_GR_avg3,label='3-period tailing avg')
ax11.plot(dates[len(dates)-len(tailing_GR_avg5):],tailing_GR_avg5,label='5-period tailing avg')
ax11.plot(dates[len(dates)-len(tailing_GR_avgp):],tailing_GR_avgp,label='{}-period tailing avg'.format(p))

ax11.legend()
ax11.yaxis.set_tick_params(labelsize=30)
ax11.axhline(0,color='black',zorder=3)
ax11.annotate(str(round(SGR_GRFCF_avg[-1],2)),xy=(dates_nums[-1],SGR_GRFCF_avg[-1]),size=20)

ax11.set_xticks(dates_nums)
ax11.set_xticklabels(dates_labels)
ax11.xaxis.set_tick_params(rotation=45, labelsize=30)

#ax11.annotate(str(round(SGR_GRFCF_avg[-1],2)),xy=(dates_nums[-1],quick_ratio[-1]),size=20)

#%%
fig1.set_size_inches(32, 18) # FCF per share, YoY growth FCF
fig9.set_size_inches(32, 18) # FCF growth based DCF model
fig2.set_size_inches(32, 18) # SGR, IGR
fig3.set_size_inches(32, 18) # SGR based DCF model
fig11.set_size_inches(32, 18) # SGR-FCF growth average
fig10.set_size_inches(32, 18) # SGR-FCF growth average based DCF model
fig4.set_size_inches(32, 18) # BB model
fig5.set_size_inches(32, 18) # solvency analysis
fig6.set_size_inches(32, 18) # liquidity analysis
fig7.set_size_inches(32, 18) # profitability analysis
fig8.set_size_inches(32, 18) # valuation analysis

figure_list = [fig1,fig9,fig2,fig3,fig11,fig10,fig4,fig5,fig6,fig7,fig8]

import matplotlib.backends.backend_pdf
import os
os.chdir(r'C:\Users\Owner\Documents\Analysis\outputs')

pdf = matplotlib.backends.backend_pdf.PdfPages("{}_output.pdf".format(ticker))
for fig in figure_list:
    pdf.savefig(fig)


pdf.close()
os.chdir(r'C:\Users\Owner\Documents\Analysis')

