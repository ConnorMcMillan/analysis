# -*- coding: utf-8 -*-

import pandas as pd
import os

#CIK = 1326801
def get_10K_filings_lines(CIK,master_10K_dir):
    
    os.chdir(master_10K_dir)
    headers = ['CIK','name','type','date','txt extension','html extension']
    df = pd.read_csv('master_10K.tsv',sep='|',names=headers)
    
    # go through list of filings and find dates 10K's were filed
    filings_list = []
    for index,line in enumerate(df.iterrows()):
        if line[1]['CIK']==CIK:
            filings_list.append(line[1])
            
    filings_df = pd.DataFrame(filings_list).sort_values('date')
    
    for line in filings_df.iterrows():
        print(line[1]['name'],' | ',line[1]['date'],' | ',line[1]['type'])
    
    return(pd.DataFrame(filings_list))
