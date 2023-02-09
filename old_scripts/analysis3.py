# -*- coding: utf-8 -*-
import pandas as pd
import os

headers = ['CIK','name','type','date','txt extension','html extension']
df = pd.read_csv('master_10K.tsv',sep='|',names=headers)
#%%

df = df.sort_values('name')
#%%
#next(df.iterrows())[1]['date']
testing = []
for index,line in enumerate(df.iterrows()):
#    print(type(line[1]['CIK']))
    if line[1]['CIK']==1326801:
        testing.append([line[1]['date'],line[1]['type']])
        print('found filing')
#    print(line[1]['name'])
#%%

test_extension = df.iloc[109741]['html extension']

#109741 Facebook Inc
#117938 Facebook Inc
#125936 Facebook Inc
#133763 Facebook Inc
#141196 Facebook Inc
#148302 Facebook Inc
#155302 Facebook Inc
#162233 Facebook Inc

test_url = 'https://www.sec.gov/Archives/'+test_extension

url_formatted = test_url.replace('-','').replace('index.html','')

test_10K_files = pd.read_html(url_formatted)

# search for 10K. or 10-K. in list of files for a 10K filing. Note the "."
for file in test_10K_files[0]['Name']:
    print(file)
    if file.lower().find('10K.'.lower())!=-1 or file.lower().find('10-K.'.lower())!=-1 :
        print('found 10K')
        extension = file
#%%

# add extension to get to the actual 10K file in the filing
url_10K = url_formatted+'/'+extension
doc = pd.read_html(url_10K)
#%%

# sort through the 10K and find the tables repesenting the financial statments we want
for index,table in enumerate(doc):

    
    left_column = table[0]
    
    # some left columns are only NaN and will throw an error
    if all(left_column.isna()==True):
        print('NaN series found looking for BS')
        continue
    
    # if true we have found the table representing the balance sheet
    if any(left_column.str.contains('retained',case=False,na=False)) and \
        any(left_column.str.contains('total assets',case=False,na=False)) \
        and any(left_column.str.contains('accounts payable',case=False,na=False)):
        
        Balance_Sheet = table
        print(index,'Found Balance Sheet')
#%%
        
# sort through the 10K and find the tables repesenting the financial statments we want
for index,table in enumerate(doc):
    
    left_column = table[0]
    
    # some left columns are only NaN and will throw an error
    if all(left_column.isna()==True):
        print('NaN series found looking for IS')
        continue   
       
    # if true we have found the table representing the income statement
    if any(left_column.str.contains('marketing and sales',case=False,na=False)) \
        and any(left_column.str.contains('net income',case=False,na=False)) \
        and any(left_column.str.contains('research and development',case=False,na=False)) \
        and any(left_column.str.contains('cost of revenue',case=False,na=False)) \
        and '%' not in table.to_string() \
        and 'three months' not in table.to_string().lower():
        
        # NOTE: still need to cut off this table at net income, rows below net income have duplicate names i.e. research and development
        Income_Statement = table
        print(index,'Found Income Statement')
#%%
        
# sort through the 10K and find the tables repesenting the financial statments we want
for index,table in enumerate(doc):
#    print(table)
    
    left_column = table[0]       
    
    # some left columns are only NaN and will throw an error
    if all(left_column.isna()==True):
        print('NaN series found looking for SCF')
        continue
    
    # if true we have found the table representing the statement of cash flows
    if any(left_column.str.contains('net income',case=False,na=False)) and \
        any(left_column.str.contains('end of period',case=False,na=False)) \
        and any(left_column.str.contains('cash flow',case=False,na=False)):
        
        Cash_Flow = table
        print(index,'Found Satement of Cash Flow')
#%%
for index,name in enumerate(df['name']):
    if 'Facebook' in name:
        print(index,name)
    

#%%
test_data = pd.read_html('https://www.sec.gov/Archives/edgar/data/1326801/000132680117000024/fb-03312017x10q.htm#sBEC13F0E8C235DBC8A091FB2B473B285')        









#%%
import numpy as np
for index,item in enumerate(doc):
    left_column = item[0]
    print(type(left_column))

doc[282]#.str.contains('anything')


series = pd.Series([np.NaN,np.NaN,np.NaN,np.NaN,'not na'])

series.isna()

series.str.contains('string',na=False)


test_list = [np.NaN,np.NaN,np.NaN,np.NaN,np.NaN]

all(series.isna())
#print(left_column.str.contains('101.DEF'))
#%%
import matplotlib.pyplot as plt

for i in range(len(testing)):
    plt.plot(testing[i][0])
    
plt.show()

