# -*- coding: utf-8 -*-
from scipy.optimize import fsolve
from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
#%%
# discount cash flow intrinsic value model
# free cash flow for year n
def FCFn(n,BYFCF,GR):
    '''
    returns estiamted free cash flow for year n
    n = number of years past base year
    BYFCF = base year free cash flow (current year)
    GR = estimated growth rate of free cash flow
    '''
    GR = GR[n-1]
    FCFn = BYFCF*(1+GR)**n
    return FCFn

# discount factor for year n
def DFn(n,DR):
    '''
    retuns discount factor during year n
    n = number of years
    DR = discount rate
    '''
    DFn = (1+DR)**n
    return DFn

# discounted free cash flow for year n
def DFCFn(n,BYFCF,GR,DR):
    '''
    Discounted free cash flow for year n = FCFn/DFn
    '''
#    GR = GR[n-1]
    FCF = FCFn(n,BYFCF,GR)
    DF = DFn(n,DR)
    DFCFn = FCF/DF
    return DFCFn

# sum of discounted free cash flow to year n
def sum_DFCFn(n,BYFCF,GR,DR):
    '''
    sum of all discounted free cash flows over years n
    '''
    summation = 0
    for n in range(1,n+1):
#        growth_rate = GR[i]
        summation += DFCFn(n,BYFCF,GR,DR)
    return summation
        
# discounted perpetuity free cash flow (beyond ten years to infinity)
def DPFCF(LGR,BYFCF,GR,DR,n):
    '''
    LGR = long term growth rate (beyond 10 years)
    BYFCF = base year free cash flow
    GR = growth rate of free cash flow
    DR = discount rate
    '''
    GR = GR[-1]
    DPFCF = (BYFCF*((1+GR)**(n+1))*(1+LGR))/(DR-LGR)*1/((1+DR)**(n+1))
    return DPFCF

# intrinsic value of company for ten years+into the future
def DCF_intrinsic_value(DR,BYFCF,GR,LGR,n=10):
    '''
    LGR = long term growth rate (beyond 10 years)
    BYFCF = base year free cash flow
    GR = growth rate of free cash flow
    DR = discount rate
    n = 10 by default for this model, summing first 10 years DFCF
    '''
    sum_short_term = sum_DFCFn(n,BYFCF,GR,DR)
    perpituity = DPFCF(LGR,BYFCF,GR,DR,n)
    intrinsic_value = sum_short_term+perpituity
    return intrinsic_value,perpituity
#%%
# solve for corresponding discount rate given intrinsic or market value
def DCF_discount_rate(DRo,intrinsic_val,BYFCF,GR,LGR,n=10):
    
    def solve_DCF_intrinsic_val(DR,BYFCF,GR,LGR,n=n):
        return intrinsic_val - DCF_intrinsic_value(DR,BYFCF,GR,LGR,n=n)[0]
    
    sol = fsolve(solve_DCF_intrinsic_val,DRo,args = (BYFCF,GR,LGR,n))
    
    return sol[0]
#%%
# buffet's books intrinstic value model

# average book value change
def avg_BVC(BVPS_old,BVPS_current,n):
    '''
    calculate the average change in book value over n years
    BVPS_old = old book value per share
    BVPS_current = current book value per share
    n = years between old and current BV
    '''
    i = (BVPS_current/BVPS_old)**(1/n)-1
    return i

def BB_intrinsic_value(DR,BVPS_current,GRBV,n=10,Div=0):
    '''
    DR = discount rate
    BVPS_current = current book value per share
    GBVR = expected growth rate of book value 
    n = number of years into future you estimate cash flows
    Div = yearly dividend payment
    '''
    intrinsic_val = Div*(1-1/((1+DR)**n))/DR+BVPS_current*((1+GRBV)**n)/((1+DR)**n)
    return intrinsic_val


#%%
def BB_discount_rate(DRo,intrinsic_val,BVPS_current,GRBV,n=10,Div=0):
    '''
    solves for discount rate given intrinsic value or market value
    DR_o = discount rate guess
    intrinisc_val = market value or intrinisc value of share 
    BVPS_current = current book value per share
    GBVR = expected growth rate of book value for n years
    n = number of years into future you estimate cash flows
    Div = yearly dividend payment per share
    '''
    def solve_BB_intrinsic_value(DR,intrinsic_val,BVPS_current,GRBV,n=n,Div=Div):
        return intrinsic_val - (Div*(1-1/((1+DR)**n))/DR+BVPS_current*((1+GRBV)**n)/((1+DR)**n))

    sol = fsolve(solve_BB_intrinsic_value,DRo, args = (intrinsic_val,BVPS_current,GRBV,n,Div))
    return sol[0]
#%%
def get_bond_rate(term='10 yr'):
    '''
    get 10 year federal bond interest rate
    term = term of the bond until maturity
    '''
    
    treasury_link = 'https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yield'
    treasury_request = requests.get(treasury_link)
    treasury_soup = bs(treasury_request.content,'lxml')
    
    treasury_tables_body = [[[td.get_text(strip=True) for td in tr.find_all('td')] for tr in table.find_all('tr')] for table in treasury_soup.find_all('table')]
    treasury_tables_headers = [[[th.get_text(strip=True) for th in tr.find_all('th')] for tr in table.find_all('tr')] for table in treasury_soup.find_all('table')]
    treasury_table = pd.DataFrame(treasury_tables_body[1],columns = treasury_tables_headers[1][0])
    note_10Y_rate = treasury_table[term]
    note_10Y_date = treasury_table['Date']
    most_recent_rate = float(note_10Y_rate[note_10Y_rate.index[-1]])
    most_recent_date = note_10Y_date[note_10Y_date.index[-1]]
    return most_recent_rate, most_recent_date
#%%