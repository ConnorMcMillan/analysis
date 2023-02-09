# -*- coding: utf-8 -*-

from get_10K_filings_lines import get_10K_filings_lines
from get_10K_tables_v2 import get_10K_tables_v2
import pandas as pd
import os
import re
#%%
cwd = os.getcwd()#+r'\Documents\Analysis'
CIK = 1326801
company_lines = get_10K_filings_lines(CIK,cwd)
tables_from_10Ks,urls = get_10K_tables_v2(company_lines)

#%%

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
    
    #    # find if data is reported in ones, hundreds, thousands, millions, billions, or  in balance sheet    
    #    # find multiplier keywords if in balance sheet string
    #    if 'in hundreds' in page_string.lower():
    #        BS_multiplier = 100
    #    elif 'in thousands' in page_string.lower():
    #        BS_multiplier = 1000
    #    elif 'in millions' in page_string.lower():
    #        BS_multiplier = 1000000
    #    elif 'in billions' in page_string.lower():
    #        BS_multiplier = 1000000000
    #    else:
    #        BS_multiplier = 1
    #        
    #    BS_multiplier_list.append(BS_multiplier) 
    
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
    
    
        # shares information string comes with different date formats:
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
        
        # seach for date fmt 1
        if re.findall(date_fmt1,shares_out_string.lower()):
            print('Date pattern | fmt1')
            date_fmt1_indices = [x.span() for x in re.finditer(date_fmt1,shares_out_string.lower())]            
            
            # search for shares out fmt1
            if re.findall(shares_out_fmt1,shares_out_string.lower()):
                print('Shares out pattern | fmt1')
                
                shares_out_fmt1_indices = [x.span() for x in re.finditer(shares_out_fmt1,shares_out_string.lower())]            
    
                # go through the sets of numbers in entire string and find the first one listed aka: most recent
                first_num_list = []                
                for indices in shares_out_fmt1_indices:
                    
                    # find substring containing a single set of numbers
                    set_substring = shares_out_string[indices[0]:indices[1]]                    
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
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
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
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
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
                    first_num_raw = re.findall('\d+(?:,\d+)*' ,set_substring)[0]
                    first_num = re.findall('\d+(?:,\d+)*',first_num_raw)[0]
                    first_num = first_num.replace(',','')
                    first_num = float(first_num)*shares_out_multiplier
                    
                    # in fmt3 we only want the first number so break after list of one is formed
                    first_num_list.append(first_num)
                    shares_out = sum(first_num_list)
                    break
        
        # search for date fmt 2
        if re.findall(date_fmt2,shares_out_string.lower()) \
        and not re.findall(date_fmt1,shares_out_string.lower()):
            print('Date pattern | fmt2')
            date_fmt2_indices = [x.span() for x in re.finditer(date_fmt2,shares_out_string.lower())]
        
            # search for shares out fmt1
            if re.findall(shares_out_fmt1,shares_out_string.lower()):
                print('Shares out pattern | fmt1')
                
                shares_out_fmt1_indices = [x.span() for x in re.finditer(shares_out_fmt1,shares_out_string.lower())]            
    
                # go through the sets of numbers in entire string and find the first one listed aka: most recent
                first_num_list = []                
                for indices in shares_out_fmt1_indices:
                    
                    # find substring containing a single set of numbers
                    set_substring = shares_out_string[indices[0]:indices[1]]                    
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
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
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
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
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
                    first_num_raw = re.findall('\d+(?:,\d+)*' ,set_substring)[0]
                    first_num = re.findall('\d+(?:,\d+)*',first_num_raw)[0]
                    first_num = first_num.replace(',','')
                    first_num = float(first_num)*shares_out_multiplier
                   
                    # in fmt3 we only want the first number so break after list of one is formed
                    first_num_list.append(first_num)
                    shares_out = sum(first_num_list)
                    break
                
        # search for date fmt 3
        if not re.findall(date_fmt3,shares_out_string.lower()):
            print('Date pattern | fmt3')            
            # no substring indices for this format 
            
            # search for shares out fmt 1
            if re.findall(r'issued and outstanding:',shares_out_string.lower()):
                print('Shares out pattern | fmt1')
                
                shares_out_fmt1_indices = [x.span() for x in re.finditer(shares_out_fmt1,shares_out_string.lower())]            
    
                # go through the sets of numbers in entire string and find the first one listed aka: most recent
                first_num_list = []                
                for indices in shares_out_fmt1_indices:
                    
                    # find substring containing a single set of numbers
                    set_substring = shares_out_string[indices[0]:indices[1]]                    
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
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
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
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
                    
                    # grab the first number and next word, which is often a multiplier ie thousand, million, billion
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
    return balance_sheet_list, balance_sheet_check, BS_multiplier_list, shares_out_multiplier_list
#%%
# sort through the 10K and find the tables repesenting the financial statments we want
def get_BS(tables_from_10Ks,company_lines):
    balance_Sheet_list = []
    balance_Sheet_check = []
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
                found_statement = 'Found BS Filed',company_lines['date'][company_lines_index]
                print(found_statement)
                            
#            print(found_statement)
                balance_Sheet_check.append(found_statement)

    # format and clean up the balance sheet
#    Balance_Sheet = Balance_Sheet.applymap(str)
    
    # find the 'assets' line and chop out everything above it
#    for index, left_column_string in enumerate(Balance_Sheet[0]):
#        print(left_column_string)
#        if left_column_string.lower() == 'assets':
#            Balance_Sheet = Balance_Sheet[:][index:]
#            print('asset index = ',index)
        Balance_Sheet = Balance_Sheet.applymap(str)
        for index, left_column_string in enumerate(Balance_Sheet[0]):
            if left_column_string.lower() != 'nan':
                nan_ends = index
                break
        Balance_Sheet = Balance_Sheet[:][nan_ends:]
        
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
        
        balance_Sheet_list.append(Balance_Sheet)
    return(balance_Sheet_list,balance_Sheet_check)
    
#%%
def get_IS(tables_from_10Ks,company_lines):
    Income_Statement_list = []
    Income_Statement_check = []
    company_lines_indices = company_lines.index
    for company_lines_index,tables in zip(company_lines_indices,tables_from_10Ks):
        for index, table in enumerate(tables):
    
            left_column = table[0]
            
            # some left columns are only NaN and will throw an error
            if all(left_column.isna()==True):
#                print('NaN series found looking for IS')
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
                found_statement = 'Found IS Filed',company_lines['date'][company_lines_index]
                print(found_statement)
                            
#            print(found_statement)
                Income_Statement_check.append(found_statement)
    
    # find the 'revenue' line and chop out everything above it
#    Income_Statement = Income_Statement.applymap(str)
#    for index, left_column_string in enumerate(Income_Statement[0]):
#        if left_column_string.lower() == 'revenue':
#            Income_Statement = Income_Statement[:][index:]
#            print('revenue index = ',index)
        Income_Statement = Income_Statement.applymap(str)
        for index, left_column_string in enumerate(Income_Statement[0]):
            if left_column_string.lower() != 'nan':
                nan_ends = index
                break
        Income_Statement = Income_Statement[:][nan_ends:]
                
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
        
        Income_Statement_list.append(Income_Statement)
    return(Income_Statement_list,Income_Statement_check)
#%%
def get_SCF(tables_from_10Ks,company_lines):
    company_lines_indices = company_lines.index
    Cash_Flow_list = []
    Cash_Flow_check = []
    for company_lines_index,tables in zip(company_lines_indices,tables_from_10Ks):
#        print('looking for SFC',company_lines['date'][company_lines_index])
        for index, table in enumerate(tables):
        
            left_column = table[0]       
            
            # some left columns are only NaN and will throw an error
            if all(left_column.isna()==True):
    #            print('NaN series found looking for SCF')
                continue
            
            # if true we have found the table representing the statement of cash flows
            if any(left_column.str.contains('net income',case=False,na=False)) and \
                any(left_column.str.contains('end of',case=False,na=False)) \
                and any(left_column.str.contains('cash flow',case=False,na=False)):
                  
                    
                #any(left_column.str.contains('end of period',case=False,na=False)) \
                #^^^ loosened this constraint to 'end of' not 'end of period'
                
                Cash_Flow = table
                found_statement = 'Found SCF Filed',company_lines['date'][company_lines_index]
                print(found_statement)
                            
#            print(found_statement)
                Cash_Flow_check.append(found_statement)
    # find the top line of SCF: the first string not 'nan' and chop out everything above it
        Cash_Flow = Cash_Flow.applymap(str)
        for index, left_column_string in enumerate(Cash_Flow[0]):
            if left_column_string.lower() != 'nan':
                nan_ends = index
                break
        Cash_Flow = Cash_Flow[:][nan_ends:]
                
        # find columns with '$' and all 'nan' and cut them out
        Cash_Flow_cols = Cash_Flow.columns
        good_cols = []
        for col in Cash_Flow_cols:
            if '$' not in Cash_Flow[col].tolist() \
                and not all(Cash_Flow[col]=='nan'):
                good_cols.append(col) 
        
        # continue cleaning up the balance sheet
        Cash_Flow = Cash_Flow[good_cols]
        Cash_Flow = Cash_Flow[Cash_Flow.columns[0:2]]
        
        # replace parenthesis with negative sign
        Cash_Flow[Cash_Flow.columns[-1]] = Cash_Flow[Cash_Flow.columns[-1]].map(lambda x: x.replace('(','-'))
        
        # replace commas with empty spaces
        Cash_Flow[Cash_Flow.columns[-1]] = Cash_Flow[Cash_Flow.columns[-1]].map(lambda x: x.replace(',',''))
        
        # replace "-" dash with 0
        Cash_Flow[Cash_Flow.columns[-1]] = Cash_Flow[Cash_Flow.columns[-1]].map(lambda x: x.replace('—','0'))
        
        # convert to float
        Cash_Flow[Cash_Flow.columns[-1]] = Cash_Flow[Cash_Flow.columns[-1]].astype(float)
        
        Cash_Flow_list.append(Cash_Flow)
    
    return (Cash_Flow_list,Cash_Flow_check)
#%%