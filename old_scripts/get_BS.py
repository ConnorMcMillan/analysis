# -*- coding: utf-8 -*-

from get_10K_filings_lines import get_10K_filings_lines
from get_10K_tables import get_10K_tables
import pandas as pd
import os
import numpy as np
#%%
cwd = os.getcwd()#+r'\Documents\Analysis'
CIK = 1326801
company_lines = get_10K_filings_lines(CIK,cwd)
tables_from_10Ks,urls = get_10K_tables(company_lines)

#%%

# sort through the 10K and find the tables repesenting the financial statments we want
def get_BS(tables_from_10Ks,company_lines_indices):
    company_lines_indices = company_lines.index
    for company_lines_index,tables in zip(company_lines_indices,tables_from_10Ks):
        for index, table in enumerate(tables):
        
            left_column = table[0]
            
            # some left columns are only NaN and will throw an error
            if all(left_column.isna()==True):
                continue
            
            # if true we have found the table representing the balance sheet
            if any(left_column.str.contains('retained',case=False,na=False)) and \
                any(left_column.str.contains('total assets',case=False,na=False)) \
                and any(left_column.str.contains('accounts payable',case=False,na=False)):
                            
                Balance_Sheet = table
                print('Found BS Filed',company_lines['date'][company_lines_index])


    # format and clean up the balance sheet
    Balance_Sheet = Balance_Sheet.applymap(str)
    # find the 'assets' line and chop out everything above it
    for index, left_column_string in enumerate(Balance_Sheet[0]):
        print(left_column_string)
        if left_column_string.lower() == 'assets':
            Balance_Sheet = Balance_Sheet[:][index:]
            print('asset index = ',index)
    
    # find columns with '$' and all 'nan' and cut them out
    Balance_Sheet_cols = Balance_Sheet.columns
    good_cols = []
    for col in Balance_Sheet_cols:
        if '$' not in Balance_Sheet[col].tolist() \
            and not all(Balance_Sheet[col]=='nan'):
                good_cols.append(col) 
    
    # continue cleaning up the balance sheet
    Balance_Sheet = Balance_Sheet[good_cols]
    Balance_Sheet = Balance_Sheet[Balance_Sheet.columns[0:2]]
    
    # replace parenthesis with negative sign
    Balance_Sheet[Balance_Sheet.columns[-1]] = Balance_Sheet[Balance_Sheet.columns[-1]].map(lambda x: x.replace('(','-'))
    
    # replace commas with empty spaces
    Balance_Sheet[Balance_Sheet.columns[-1]] = Balance_Sheet[Balance_Sheet.columns[-1]].map(lambda x: x.replace(',',''))
    
    # replace "-" dash with 0
    Balance_Sheet[Balance_Sheet.columns[-1]] = Balance_Sheet[Balance_Sheet.columns[-1]].map(lambda x: x.replace('—','0'))
    
    # convert to float
    Balance_Sheet[Balance_Sheet.columns[-1]] = Balance_Sheet[Balance_Sheet.columns[-1]].astype(float)

    return(Balance_Sheet)
    
#%%
def get_IS(tables_from_10Ks,company_lines_indices):
    company_lines_indices = company_lines.index
    for company_lines_index,tables in zip(company_lines_indices,tables_from_10Ks):
        for index, table in enumerate(tables):
    
            left_column = table[0]
            
            # some left columns are only NaN and will throw an error
            if all(left_column.isna()==True):
                print('NaN series found looking for IS')
                continue   
    
                
            if any(left_column.str.contains('marketing and sales',case=False,na=False)) \
                and any(left_column.str.contains('net income',case=False,na=False)) \
                and any(left_column.str.contains('research and development',case=False,na=False)) \
                and any(left_column.str.contains('cost of revenue',case=False,na=False)) \
                and '%' not in table.to_string() \
                and 'three months' not in table.to_string().lower() \
                and 'share' not in table.to_string().lower():
            
            # NOTE: still need to cut off this table at net income, rows below net income have duplicate names i.e. research and development
                Income_Statement = table
                print('Found IS Filed',company_lines['date'][company_lines_index])
    
    
    # find the 'revenue' line and chop out everything above it
    Income_Statement = Income_Statement.applymap(str)
    for index, left_column_string in enumerate(Income_Statement[0]):
        if left_column_string.lower() == 'revenue':
            Income_Statement = Income_Statement[:][index:]
            print('revenue index = ',index)
            
    # find columns with '$' and all 'nan' and cut them out
    Income_Statement_cols = Income_Statement.columns
    good_cols = []
    for col in Income_Statement_cols:
        if '$' not in Income_Statement[col].tolist() \
            and not all(Income_Statement[col]=='nan'):
                good_cols.append(col) 
    
    # continue cleaning up the balance sheet
    Income_Statement = Income_Statement[good_cols]
    Income_Statement = Income_Statement[Income_Statement.columns[0:2]]
    
    # replace parenthesis with negative sign
    Income_Statement[Income_Statement.columns[-1]] = Income_Statement[Income_Statement.columns[-1]].map(lambda x: x.replace('(','-'))
    
    # replace commas with empty spaces
    Income_Statement[Income_Statement.columns[-1]] = Income_Statement[Income_Statement.columns[-1]].map(lambda x: x.replace(',',''))
    
    # replace "-" dash with 0
    Income_Statement[Income_Statement.columns[-1]] = Income_Statement[Income_Statement.columns[-1]].map(lambda x: x.replace('—','0'))
    
    # convert to float
    Income_Statement[Income_Statement.columns[-1]] = Income_Statement[Income_Statement.columns[-1]].astype(float)

    return(Income_Statement)