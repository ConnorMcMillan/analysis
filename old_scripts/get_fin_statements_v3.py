# -*- coding: utf-8 -*-

#from get_10K_filings_lines import get_10K_filings_lines
from get_10K_tables_v3 import get_10K_tables_v3,get_10K_filings_lines
import pandas as pd
import os
import re
#%%
#if __name__=='__main__':
#    cwd = os.getcwd()#+r'\Documents\Analysis'
#    CIK = 1326801
#    company_lines = get_10K_filings_lines(CIK,cwd)
#    tables_from_10Ks,urls = get_10K_tables_v3(company_lines)

#%%
def get_BSv3(tables_from_10Ks,company_lines):
    balance_sheet_list = []
    balance_sheet_check = []
    page_string_list = []
    BS_multiplier_list = []
    shares_out_string_list = []
    shares_out_multiplier_list = []
    shares_out_list = []
    
    company_lines_indices = company_lines.index
    for company_lines_index,tables_and_strings in zip(company_lines_indices,tables_from_10Ks):  
        
        # go through the tables and toss out the placeholders
        placeholder_indices = []
        for index, table_and_string in enumerate(tables_and_strings):
            table = table_and_string[0]
            page_string = table_and_string[1]
            if type(table)==str:
                placeholder_indices.append(index)
        # delete in reverse order not to throw off the indexing
        for index in sorted(placeholder_indices,reverse=True):
            del tables_and_strings[index]
                
        # go through each table in the 10K and find the balance sheet
        for index, table_and_string in enumerate(tables_and_strings):
            table = table_and_string[0]
            page_string = table_and_string[1]
            
            
            left_column = table[0]
    
            # if true we have found the table representing the balance sheet
            if any(left_column.str.contains('retained',case=False,na=False)) and \
                any(left_column.str.contains('total assets',case=False,na=False)) \
                and any(left_column.str.contains('accounts payable',case=False,na=False)) \
                and any(left_column.str.contains('par value',case=False,na=False)):
                            
                Balance_Sheet = table
                found_statement = 'Found BS Filed',company_lines['date'][company_lines_index],'table index:{0}'.format(index)
                print(found_statement)
                
                page_string_list.append(page_string)
                balance_sheet_check.append(found_statement)
                break
    
        # find the string containing number of shares oustanding  
        for line in Balance_Sheet[0]:
            if 'common'.lower() \
            and 'stock'.lower() \
            and 'outstanding'.lower() \
            in str(line).lower()\
            and 'preferred'.lower() not in str(line).lower():
                print('FOUND SHARES OUT STRING FROM BALANCE SHEET','-'*100)
                shares_out_string_list.append(line)
                shares_out_string = line
     
        par_st = shares_out_string.find('$')
        par_end = shares_out_string.find('par value')+len('par value')
        par_value = shares_out_string[par_st:par_end]
        par_value = par_value.replace('$','')
        par_value = par_value.replace('par value','')
        par_value = par_value.replace(' ','')
        
        shares_out_string = shares_out_string.replace(par_value,'')
        shares_out_string = shares_out_string.replace(u'\xa0',' ')
        shares_out_string = shares_out_string.lower()
        
        # find the shares outstanding multipliers and remove them
        if 'hundred' in shares_out_string:
            shares_out_multiplier = 10
            shares_out_string = shares_out_string.replace('hundred ','')
        elif 'thousand' in shares_out_string:
            shares_out_string = shares_out_string.replace('thousand ','')
            shares_out_multiplier = 1000
        elif 'million' in shares_out_string:
            shares_out_string = shares_out_string.replace('million ','')
            shares_out_multiplier = 1000000
        elif 'billion' in shares_out_string:
            shares_out_string = shares_out_string.replace('billion ','')
            shares_out_multiplier = 1000000000
        else:
            shares_out_multiplier = 1
        
        shares_out_multiplier_list.append(shares_out_multiplier)
    
    
        # shares information string comes with different date formats and shares outstanding formats:
        # date fmt1: 'December 31, 20XX, and 20X(X-1)' or 'December 31, 20XX, and December 31, 20X(X-1)'
        # date fmt2: 'at December 31, 20XX' and not date fmt 1
        # date fmt3: no date included in information string aka: not 'december 31, 20XX' anywhere
            # then search for 'shares outstanding format'
            # shares out fmt1: 'issued and outstanding: ### and ###'
            # shares out fmt2: '### and ### shares issued and outstanding,'
            # shares out fmt3: 'at december 20##'
            
        # bank of regular expressions:
        date_fmt1 = r'december 31, 20[0-9][0-9] and (?:december 31, )?20[0-9][0-9]'
        date_fmt2 = r'(?:at )?december 31, 20[0-9][0-9]' # and not date fmt1
        date_fmt3 = r'december 31, 20[0-9][0-9]' # if not this regex
        
        shares_out_fmt1 = r'issued and outstanding: \d+(?:,\d+)* and \d+(?:,\d+)*'
        shares_out_fmt2 = r'\d+(?:,\d+)* and \d+(?:,\d+)* shares issued and outstanding,'
        shares_out_fmt3 = r'shares issued and \d+(?:,\d+)* shares outstanding'
        
            
        # search for shares out fmt1
        if re.findall(shares_out_fmt1,shares_out_string.lower()):
            print('Shares out pattern | fmt1')
            
            shares_out_fmt1_indices = [x.span() for x in re.finditer(shares_out_fmt1,shares_out_string.lower())]            
    
            # go through the sets of numbers in entire string and find the first one listed aka: most recent
            first_num_list = []                
            for indices in shares_out_fmt1_indices:
                
                # find substring containing a single set of numbers
                set_substring = shares_out_string[indices[0]:indices[1]]                    
                
                # grab the first number 
                first_num_raw = re.findall('\d+(?:,\d+)*' ,set_substring)[0]                       
                first_num = re.findall('\d+(?:,\d+)*',first_num_raw)[0]
            first_num = first_num.replace(',','')
            first_num = float(first_num)*shares_out_multiplier
            
            first_num_list.append(first_num)
            shares_out = sum(first_num_list)
                    
        # search for shares out fmt2
        if re.findall(shares_out_fmt2,shares_out_string.lower()):
            print('Shares out pattern | fmt2')
            shares_out_fmt2_indices = [x.span() for x in re.finditer(shares_out_fmt2,shares_out_string.lower())]            
                       
            # go through the sets of numbers in entire string and find the first one listed aka: most recent
            first_num_list = []                
            for indices in shares_out_fmt2_indices:
                
                # find substring containing a single set of numbers
                set_substring = shares_out_string[indices[0]:indices[1]]                    
                
                # grab the first number 
                first_num_raw = re.findall('\d+(?:,\d+)*' ,set_substring)[0]
                first_num = re.findall('\d+(?:,\d+)*',first_num_raw)[0]
                first_num = first_num.replace(',','')
                first_num = float(first_num)*shares_out_multiplier
                
                first_num_list.append(first_num)
                shares_out = sum(first_num_list)
        
        # search for shares out fmt3
        if re.findall(shares_out_fmt3,shares_out_string.lower()):
            print('Shares out pattern | fmt3')
            shares_out_fmt3_indices = [x.span() for x in re.finditer(shares_out_fmt3,shares_out_string.lower())]            
            
            # go through the sets of numbers in entire string and find the first one listed aka: most recent
            first_num_list = []                
            for indices in shares_out_fmt3_indices:
                
                # find substring containing a single set of numbers
                set_substring = shares_out_string[indices[0]:indices[1]]                    
                
                # grab the first number 
                first_num_raw = re.findall('\d+(?:,\d+)*' ,set_substring)[0]
                first_num = re.findall('\d+(?:,\d+)*',first_num_raw)[0]
                first_num = first_num.replace(',','')
                first_num = float(first_num)*shares_out_multiplier
                
                # in fmt3 we only want the first number so break after list of one is formed
                first_num_list.append(first_num)
                shares_out = sum(first_num_list)
                break
        
        shares_out_list.append(shares_out)
    
        # remove all commas
        Balance_Sheet = Balance_Sheet.applymap(lambda x: str(x))
        Balance_Sheet = Balance_Sheet.applymap(lambda x: x.replace(',',''))
        Balance_Sheet = Balance_Sheet.applymap(lambda x: x.replace(')',''))
        Balance_Sheet = Balance_Sheet.applymap(lambda x: x.replace('(','-'))
    
        Balance_Sheet_indices = Balance_Sheet.index
        Balance_Sheet_columns = Balance_Sheet.columns
        
        # find if data is reported in ones, hundreds, thousands, millions, billions, or  in balance sheet    
        # find multiplier keywords if in balance sheet string
        if 'in hundreds' in page_string.lower():
            BS_multiplier = 100
        elif 'in thousands' in page_string.lower():
            BS_multiplier = 1000
        elif 'in millions' in page_string.lower():
            BS_multiplier = 1000000
        elif 'in billions' in page_string.lower():
            BS_multiplier = 1000000000
        else:
            BS_multiplier = 1
            
        BS_multiplier_list.append(BS_multiplier) 
        
        # build a new balance sheet 
        new_row_list = []
        Balance_Sheet_indices = Balance_Sheet.index
        for df_index in Balance_Sheet_indices:
            row = Balance_Sheet.loc[df_index]
            new_row = []
            for index,item in enumerate(row):
                if index==0 and item!='':
                    new_row.append(item)
    
                item_no_sign = item.replace('-','')
                if item_no_sign.isnumeric() and len(new_row)!=0:
                        item_as_float = float(item)*BS_multiplier
                        new_row.append(item_as_float)    
                        break
                    
            new_row_list.append(new_row)
                    
        Balance_Sheet = pd.DataFrame(new_row_list)
        balance_sheet_list.append(Balance_Sheet)
    return balance_sheet_list, shares_out_list, balance_sheet_check, BS_multiplier_list, shares_out_multiplier_list
#%%
def get_ISv3(tables_from_10Ks,company_lines):
    income_statement_list = []
    income_statement_check = []
    IS_multiplier_list = []
    page_string_list = []
    
    company_lines_indices = company_lines.index
    for company_lines_index,tables_and_strings in zip(company_lines_indices,tables_from_10Ks):
        
            # go through the tables and toss out the placeholders
        placeholder_indices = []
        for index, table_and_string in enumerate(tables_and_strings):
            table = table_and_string[0]
            page_string = table_and_string[1]
            if type(table)==str:
                placeholder_indices.append(index)
        # delete in reverse order not to throw off the indexing
        for index in sorted(placeholder_indices,reverse=True):
            del tables_and_strings[index]
                
        # go through each table in the 10K and find the income statement
        for index, table_and_string in enumerate(tables_and_strings):
            table = table_and_string[0]
            page_string = table_and_string[1]
                    
            left_column = table[0]
                
            if any(left_column.str.contains('marketing and sales',case=False,na=False)) \
                and any(left_column.str.contains('net income',case=False,na=False)) \
                and any(left_column.str.contains('research and development',case=False,na=False)) \
                and any(left_column.str.contains('cost of revenue',case=False,na=False)) \
                and '%' not in table.to_string() \
                and 'three months' not in table.to_string().lower() \
                and 'share' not in table.to_string().lower():
                    
                # NOTE: still need to cut off this table at net income, rows below net income have duplicate names i.e. research and development
                income_statement = table
                found_statement = 'Found IS Filed',company_lines['date'][company_lines_index],'table index:{0}'.format(index)
                print(found_statement)
                            
                page_string_list.append(page_string)
                income_statement_check.append(found_statement)          
                break
    
        # remove all commas, end parenthesis, and correct negative signs
        income_statement = income_statement.applymap(lambda x: str(x))
        income_statement = income_statement.applymap(lambda x: x.replace(',',''))
        income_statement = income_statement.applymap(lambda x: x.replace(')',''))
        income_statement = income_statement.applymap(lambda x: x.replace('(','-'))

    
        income_statement_indices = income_statement.index
        income_statement_columns = income_statement.columns
        
        # find if data is reported in ones, hundreds, thousands, millions, billions, or  in balance sheet    
        # find multiplier keywords if in page text on income statement page
        substring_list = ['in tens','in hundreds','in thousands','in millions','in billions']
        substring_multiplier_list = [10,100,1000,1000000,1000000000]
        if any(map(page_string.lower().__contains__, substring_list)):
            for multiplier,substring in zip(substring_multiplier_list,substring_list):
                if substring in page_string.lower():
                    IS_multiplier = multiplier
                    print('Found multiplier in page text')
                    break
        else:
            print('No multiplier found in page text...')
            print('Searching for multiplier in table')
    
            # in the case the multiplier is not in the page text but in the table itself
            income_statement_indices = income_statement.index
            for df_index in income_statement_indices:
                row = income_statement.loc[df_index]
                new_row = []
                for item in row:
                    if any(map(item.lower().__contains__, substring_list)):
                        for multiplier,substring in zip(substring_multiplier_list,substring_list):
                            if substring in item.lower():
                                IS_multiplier = multiplier
                                break
        
        # if IS_multipler has not yet been defined by looking in page and table, set to default of 1
        try:
            print('IS multiplier =',IS_multiplier)
        except:
            IS_multiplier = 1
            print('No multiplier found: defaulting to 1')
        IS_multiplier_list.append(IS_multiplier)   
        
        # build a new income statement 
        new_row_list = []
        income_statement_indices = income_statement.index
        for df_index in income_statement_indices:
            row = income_statement.loc[df_index]
            new_row = []
            for index,item in enumerate(row):
                if index==0 and item!='':
                    new_row.append(item)
    
                item_no_sign = item.replace('-','')
                if item_no_sign.isnumeric() and len(new_row)!=0:
                        item_as_float = float(item)*IS_multiplier
                        new_row.append(item_as_float)    
                        break
            new_row_list.append(new_row)
        
        # delete multiplier as to not mess up later loop iterations
        del IS_multiplier
    
        income_statement = pd.DataFrame(new_row_list)
        income_statement_list.append(income_statement)
        
    return income_statement_list, income_statement_check, IS_multiplier_list
#%%
def get_SCFv3(tables_from_10Ks,company_lines):
    cash_flow_list = []
    cash_flow_check = []
    SCF_multiplier_list = []
    company_lines_indices = company_lines.index
    page_string_list = []
    for company_lines_index,tables_and_strings in zip(company_lines_indices,tables_from_10Ks):
        
        # go through the tables and toss out the placeholders
        placeholder_indices = []
        for index, table_and_string in enumerate(tables_and_strings):
            table = table_and_string[0]
            page_string = table_and_string[1]
            if type(table)==str:
                placeholder_indices.append(index)
        # delete in reverse order not to throw off the indexing
        for index in sorted(placeholder_indices,reverse=True):
            del tables_and_strings[index]
                
        # go through each table in the 10K and find the income statement
        for index, table_and_string in enumerate(tables_and_strings):
            table = table_and_string[0]
            page_string = table_and_string[1]
                    
            left_column = table[0]
            
            if any(left_column.str.contains('net income',case=False,na=False)) \
                and any(left_column.str.contains('end of',case=False,na=False)) \
                and any(left_column.str.contains('cash flow',case=False,na=False)):
                  
                cash_flow = table
                found_statement = 'Found SCF Filed',company_lines['date'][company_lines_index],'table index:{0}'.format(index)
                print(found_statement)
                            
                cash_flow_check.append(found_statement)
                page_string_list.append(page_string)
                break
                
        # remove all commas, end parenthesis, and correct negative signs
        cash_flow = cash_flow.applymap(lambda x: str(x))
        cash_flow = cash_flow.applymap(lambda x: x.replace(',',''))
        cash_flow = cash_flow.applymap(lambda x: x.replace(')',''))
        cash_flow = cash_flow.applymap(lambda x: x.replace('(','-'))

    
        cash_flow_indices = cash_flow.index
        cash_flow_columns = cash_flow.columns
        
        # find if data is reported in ones, hundreds, thousands, millions, billions, or  in balance sheet    
        # find multiplier keywords if in page text on income statement page
        substring_list = ['in tens','in hundreds','in thousands','in millions','in billions']
        substring_multiplier_list = [10,100,1000,1000000,1000000000]
        if any(map(page_string.lower().__contains__, substring_list)):
            for multiplier,substring in zip(substring_multiplier_list,substring_list):
                if substring in page_string.lower():
                    SCF_multiplier = multiplier
                    print('Found multiplier in page text')
                    break
        else:
            print('No multiplier found in page text...')
            print('Searching for multiplier in table')
    
            # in the case the multiplier is not in the page text but in the table itself
            cash_flow_indices = cash_flow.index
            for df_index in cash_flow_indices:
                row = cash_flow.loc[df_index]
                new_row = []
                for item in row:
                    if any(map(item.lower().__contains__, substring_list)):
                        for multiplier,substring in zip(substring_multiplier_list,substring_list):
                            if substring in item.lower():
                                SCF_multiplier = multiplier
                                break
        
        # if IS_multipler has not yet been defined by looking in page and table, set to default of 1
        try:
            print('SCF multiplier =',SCF_multiplier)
        except:
            SCF_multiplier = 1
            print('No multiplier found: defaulting to 1')
        SCF_multiplier_list.append(SCF_multiplier)   
        
        # build a new statement of cash flow 
        new_row_list = []
        cash_flow_indices = cash_flow.index
        for df_index in cash_flow_indices:
            row = cash_flow.loc[df_index]
            new_row = []
            for index,item in enumerate(row):
                if index==0 and item!='':
                    new_row.append(item)
    
                item_no_sign = item.replace('-','')
                if item_no_sign.isnumeric() and len(new_row)!=0:
                        item_as_float = float(item)*SCF_multiplier
                        new_row.append(item_as_float)    
                        break
            new_row_list.append(new_row)
        
        # delete multiplier as to not mess up later loop iterations
        del SCF_multiplier
    
        cash_flow = pd.DataFrame(new_row_list)
        cash_flow_list.append(cash_flow)
    
    return cash_flow_list, cash_flow_check, SCF_multiplier_list
#%%
