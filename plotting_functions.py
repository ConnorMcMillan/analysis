# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# using SGR only
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import matplotlib.pyplot as plt
from WBA_models import DCF_intrinsic_value
from scipy.interpolate import interp1d
import numpy as np

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



def plotDCF(SGR,FCF,LGR,n,p,plot_title,dates,dates_nums,hist_dates,hist_dates_nums,ticker_hist,dates_labels,xlims = [None,None],ylims = [None,None]):
    DR_low = .08
    DR_hi = .12
    DR_range = np.linspace(DR_low*100,DR_hi*100,int(DR_hi*100-DR_low*100+1))/100
    
    DCF_intrinsic_val_list = []
    for DR in DR_range:
        intrinsic_val_list = []
        SGR_years = []
        for i,(GR,BYFCF) in enumerate(zip(SGR,FCF)):
           
            # take a trailing average of SGR for future GR up to a p year period (normally p=5)
            SGR_years.append(GR)
            if i>=p:
                GR_avg = tailing_avg(SGR_years,period=p)[-1]
            if i<p:            
                GR_avg = tailing_avg(SGR_years,period=i+1)[-1]
            GR_years = np.ones(5)*GR_avg
            print(GR_avg)
            print('GR = {0} | FCF = {1}'.format(GR_avg,BYFCF))
            
            val = DCF_intrinsic_value(DR,BYFCF,GR_years,LGR,n=n)
            intrinsic_val_list.append(val[0])
        DCF_intrinsic_val_list.append(intrinsic_val_list)
    #%%
    
#    # get 1yr avg analyst price target form yahoo 
#    quote_table = si.get_quote_table(ticker, dict_result=False)
#    analyst_1yr_target = quote_table.iloc[0][1]
#    # get corresponding discount rate from anaylst target
#    DRo = .10
#    DCF_analyst_1yr_DR = DCF_discount_rate(DRo,analyst_1yr_target,BYFCF,GR_years,LGR,n=n)
    #%%
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # plotting DCF intrinsic value model
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    # fit spline to intrinsic values
    DCF_cspline_list = []
    DCF_cspline_dates_nums = [hist_dates_nums[0]]+ dates_nums+[hist_dates_nums[-1]]
    for intrinsic_val_list,DR in zip(DCF_intrinsic_val_list,DR_range):
        DCF_cspline_val_list = [intrinsic_val_list[0]]+intrinsic_val_list+[intrinsic_val_list[-1]]
        DCF_cspline = interp1d(DCF_cspline_dates_nums,DCF_cspline_val_list,kind='quadratic')
        DCF_cspline_list.append(DCF_cspline)
    #%%
    # get anaylst intrinsic value list from back-calculated discount rate
#    anaylst_intrinsic_val_list = []
#    for GR,BYFCF in zip(SGR,FCF):
#        GR_years = np.ones(n)*GR
#        val = DCF_intrinsic_value(DCF_analyst_1yr_DR,BYFCF,GR_years,LGR,n=n)
#        anaylst_intrinsic_val_list.append(val[0])
#    
#    # spline for analyst target value
#    DCF_analyst_spline_val_list = anaylst_intrinsic_val_list
#    #DCF_analyst_spline_val_list = [intrinsic_val_list[0]]+DCF_analyst_spline_val_list+[DCF_analyst_spline_val_list[-1]]
#    DCF_analyst_spline_val_list = [DCF_analyst_spline_val_list[0]]+DCF_analyst_spline_val_list+[DCF_analyst_spline_val_list[-1]]
#    
#    DCF_analyst_spline = interp1d(DCF_cspline_dates_nums,DCF_analyst_spline_val_list,kind='cubic')
    
    #%%
    fig3, ax3 = plt.subplots()
    
    fig3.suptitle(plot_title,size=60)
    
    # plot historical closing price data
    ax3.set_title('n={0} LGR={1} p={2}'.format(n,LGR,p),size=40)
    ax3.plot(hist_dates_nums,[ticker_hist[date] for date in hist_dates])
    
    # plot intrinsic value for each discount rate
    for spline,DR,intrinsic_val_list in zip(DCF_cspline_list,DR_range,DCF_intrinsic_val_list):
        ax3.plot(hist_dates_nums,spline(hist_dates_nums),'-',color='g',label=str(DR*100)+'%')
        ax3.plot(dates_nums,intrinsic_val_list,'o',color='g')
    
    # annotate IV splines
    end_intrinsic_vals = [intrinsic_val_list[-1] for intrinsic_val_list in DCF_intrinsic_val_list]
    for DR,end_intrinsic_val in zip(DR_range,end_intrinsic_vals):
        ax3.annotate(str(round(DR*100,2))+'%',xy=(dates[-1],end_intrinsic_val),size=20)
    
    # format axis
    ax3.set_xticks(dates_nums)
    ax3.set_xticklabels(dates_labels)
    ax3.xaxis.set_tick_params(rotation=45, labelsize=30)
    ax3.yaxis.set_tick_params(labelsize=30)
    ax3.axhline(0,color='black')
    xlim_hi = ax3.get_xlim()[1]   
    
    xlim_upper = xlims[1]
    xlim_lower = xlims[0]
    ax3.set_xlim(left = xlim_lower,right = xlim_upper)
    
    ylim_upper = ylims[1]
    ylim_lower = ylims[0]
    ax3.set_ylim(bottom = ylim_lower,top = ylim_upper)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # end SGR based FCF model
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    return fig3,ax3