# -*- coding: utf-8 -*-
import sys
import os
import pandas as pd
os.getcwd()

Filings_data_path = os.getcwd()#+'\\FilingsData'

os.chdir(Filings_data_path)

FilingsData_list = os.listdir()

#%%
_10Q_list = []
_10K_list = []

for index,FilingsData in enumerate(FilingsData_list):
    _10Q_list = []
    _10K_list = []
    
#    data = pd.read_csv(Filings_data_path+'\\'+FilingsData_list[0])
    data = open(Filings_data_path+'\\'+FilingsData)
#    strings = data[data.columns[0]].tolist()
    
    for string in data:
        if '|10-Q|' in string:
            _10Q_list.append(string)
        
        if '|10-K|' in string:
            _10K_list.append(string)
    
    
    list_10K = _10K_list
    list_10Q = _10Q_list
#    
#    file_10K = open('master_10K.tsv','w+')
#    file_10Q = open('master_10Q.tsv','w+')
    if index==0:
        file_10K = open('master_10K.tsv','w+')
        file_10Q = open('master_10Q.tsv','w+')

        for line in list_10K:
            file_10K.write(line+'\n')
        file_10K.close()
    
        for line in list_10Q:
            file_10Q.write(line+'\n')
        file_10Q.close()
        
        data.close()
     
    if index!=0:
        file_10K = open('master_10K.tsv','a')
        file_10Q = open('master_10Q.tsv','a')

        for line in list_10K:
            file_10K.write(line+'\n')
        file_10K.close()

        for line in list_10Q:
            file_10Q.write(line+'\n')
        file_10Q.close()
        
        data.close()
        
             