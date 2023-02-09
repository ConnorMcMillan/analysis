# -*- coding: utf-8 -*-
#%%
from get_10K_tables_v4 import get_10K_tables_v4,get_10K_filings_lines

from get_fin_statements_v3 import get_BSv3, get_ISv3, get_SCFv3
import re
import numpy as np
from scipy.interpolate import interp1d
from bs4 import BeautifulSoup as bs
from bs4 import Tag
import pandas as pd
import requests
import yfinance as yf
import yahoo_fin.stock_info as si
from datetime import datetime
import matplotlib.pyplot as plt
import math
from WBA_models import get_bond_rate,DCF_intrinsic_value,DCF_discount_rate,avg_BVC,BB_intrinsic_value,BB_discount_rate
import pandas as pd
from bs4 import BeautifulSoup as bs
import os
import urllib
import re
import time
#%%
def get_CIK(ticker):
    with open('ticker-cik.txt','r') as f:
        content = f.readlines()
        for line in content:     
            tick = re.findall('[A-Za-z]*',line)[0]
            cik = int([i for i in re.findall('(\d*)',line) if i!=''][0])
            if tick==ticker.lower():
                break
    
    return cik
#%%
cwd = r'C:\Users\Owner\Documents\Analysis'
#CIK = 1326801 # FB ticker CIK number
#ticker = 'FB'
ticker = 'GE'
CIK = get_CIK(ticker)
print('~'*50)
print('begin analysis for {}'.format(ticker))
print('~'*50)
print(' ')
print('Searching master10K.csv')

company_lines = get_10K_filings_lines(CIK,cwd)

#company_lines = pd.read_csv('testing_df')
#company_lines = company_lines
print(' ')
print('~'*50)
print('begin scraping of SEC database')
print('~'*50)

#tables_from_10Ks,urls,parse_output = get_10K_tables_v4(company_lines)

#from get_10K_filings_lines import get_10K_filings_lines


#%%
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
    
def next_element(elem):
    while elem is not None:
        # Find next element, skip NavigableString objects
        elem = elem.next_sibling
        if hasattr(elem, 'name'):
            return elem

#%%

url_list = []
info_list = []
indices = company_lines.index
for index in indices:
    txt_extension = company_lines['txt extension'][index]   
    filing_url = 'https://www.sec.gov/Archives/'+txt_extension
    url_list.append(filing_url)
    info_list.append([company_lines['date'][index],company_lines['type'][index]])
    
# add extension to get to the actual 10K file in the filing
url_10K_list = []
tables_in_10K_list = []
parse_output = []

#url_list = ['https://www.sec.gov/Archives/edgar/data/1566610/000116552714000122/0001165527-14-000122.txt']
for k,(url,filing_info) in enumerate(zip(url_list,info_list)):
    time_st = time.time()
    try:
        url_10K_list.append(url)
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'}
        r = requests.get(url,headers=headers)

#        r = requests.get(url)

        parser = 'lxml'
#            parser = 'html5lib'

        soup = bs(r.content,parser)
        
        # try for paged delinated by 'hr' tag
        try:
            hrtags = soup.find_all('hr')
    
            # if no hr tags found, try parsing with re
            if not hrtags:
                raise ValueError('no page break tags found')
            
            print('hr tags yo')
            pages = []
            for hrtag in hrtags:
                page = [str(hrtag)]
                elem = next_element(hrtag)
                while elem and elem.name != 'hr':
                    page.append(str(elem))
                    elem = next_element(elem)
                pages.append('\n'.join(page))
                
#            print('hr breaks')
#            all_hrs = soup.find_all('hr')
#            print('all divs len=',len(all_hrs))
#            hr_list = [i for i in all_hrs]
#            
#            print('div list len=',len(hr_list))
#
#            page_list = []
#            for i in range(len(hr_list)-1):
#                div = hr_list[i]
#                print('i=',i)
#                elem_list = []
#                tag_list = []
#                while div!=hr_list[i+1]:
#                    div = div.next_element
#            
#                    if isinstance(div,Tag):
#                        tag = div
#                        print(tag)
#                        tag_list.append(tag)
#                        if not tag.parent in tag_list:
#                            elem_list.append(str(tag).replace('\n',''))
#            #                elem_list.append(tag)
#            
#                page_list.append(elem_list)
#                
#            pages_as_str = [''.join(page_sublist) for page_sublist in page_list]    
#            pages = [bs(page,'lxml') for page in pages_as_str]
#                
        # if not then try for pages delineated by div with page break keywords
        except Exception as err:  
            print('used new func')
            all_divs = soup.find_all('div')
            print('all divs len=',len(all_divs))
            div_list = [i for i in all_divs if 'page-break' or 'pgbrk' in str(i).lower()]
            
            print('div list len=',len(div_list))

            page_list = []
            for i in range(len(div_list)-1):
                div = div_list[i]
                print('i=',i)
                elem_list = []
                tag_list = []
                while div!=div_list[i+1]:
                    div = div.next_element
            
                    if isinstance(div,Tag):
                        tag = div
                        print(tag)
                        tag_list.append(tag)
                        if not tag.parent in tag_list:
                            elem_list.append(str(tag).replace('\n',''))
            #                elem_list.append(tag)
            
                page_list.append(elem_list)
                
            pages_as_str = [''.join(page_sublist) for page_sublist in page_list]    
            pages = [bs(page,'lxml') for page in pages_as_str]
#            print(len(pages))
    
        # for each page, get the table and stuff in the page: title and multiplier (hundred, thousand, million, etc.)
        tables_list = []
        page_no_table_list = []
        for index, page in enumerate(pages):
            page_soup = bs(page,'lxml')
            
            # remove the table from page to get pre and post table text
            table_on_page_string = str(page_soup.table)
            text_no_table = page.replace(table_on_page_string,'')
            text_no_table = bs(text_no_table,'lxml').get_text(strip=True)
            page_no_table_list.append(text_no_table)
            
            # get table from each page
            tables = [[[td.get_text(strip=True) for td in tr.find_all('td')] for tr in table.find_all('tr')] for table in page_soup.find_all('table')]
            tables_list.append(tables)
   
        frame_string_list = []
        table_dataframes = []
        for table,page_no_table in zip(tables_list,page_no_table_list):
            if len(table)!=0:
                df = pd.DataFrame(table[0])
                table_dataframes.append(df)
                frame_string_list.append([df,page_no_table])
            else:
                table_dataframes.append('placeholder')
                frame_string_list.append(['placeholder',page_no_table])
        tables_in_10K_list.append(frame_string_list)
        
        time_end = time.time()

        parse_time = 'in {}s'.format(round(time_end-time_st,3))
        print(filing_info[0],'|',filing_info[1],'|','bs4 {0} parse {1}'.format(parser,'|'),parse_time)

#            print('bs4 {} parse'.format(parser),parse_time)
        
        parse_output.append(['bs4 {} parse'.format(parser),parse_time])

    # try for plain text docs
    except Exception as e:
        data = urllib.request.urlopen(url)
        lines = []
        big_string = ''
        for data_line in data:
            data_line = str(data_line).replace('\\n\'','')
            data_line = data_line.replace('\\n\"','')
            data_line = data_line.replace('b\"','')
            data_line = data_line.replace('b\'','')
            data_line = data_line.replace('\\t','           ')    
            data_line = data_line + ' \\n '
            lines.append(data_line)
            big_string += data_line
            
        pages = re.findall('<PAGE>(.*?)(?=<PAGE>)',big_string)
        tables = [re.findall('<TABLE>(.*?)(?=</TABLE>)',page) for page in pages]
        
        page_no_table_list = []
        for tables_in_page,page in zip(tables,pages):
            for table in tables_in_page:
                page = page.replace(table,'')
            page_no_table_list.append(page) 

        tables_combined = [''.join(table) for table in tables]
        tables_clean = [table.replace('\\n','\n') for table in tables_combined]       
        tables_by_line = [table.split('\n') for table in tables_clean]
       
       # parse through the tables by line to build a dataframe
        tables_list = []
        for table_lines in tables_by_line:
            table_lines_clean = []
            for line in table_lines:
                line = line.replace('$','')
                line = line.replace(',','')
                line = line.strip()
                table_lines_clean.append(line)
    
            good_lines = []
            current_line = ''
            for i in range(len(table_lines_clean)):

               # i.e. current assets:
                if len(table_lines_clean[i])!=0 and table_lines_clean[i][-1] == ':':
                    good_lines.append(current_line+table_lines_clean[i])
                    current_line = ''
                    continue
               
               # get value name, dots, and first number
                if re.findall('.+\.\s+\d+',table_lines_clean[i]):
                    good_lines.append(current_line+' '+re.findall('.+\.\s+\d+',table_lines_clean[i])[0])
                    current_line = ''
                    continue
               
                # add up left column values that take up more than one line
                if re.findall('\w+',table_lines_clean[i]):
                    current_line = current_line+' '+table_lines_clean[i]
               
                columns = [] 
                for good_line in good_lines:             
                    if re.findall('.+\.\s+\d+',good_line):
    
                        num = re.findall('\.\s+\d+',good_line)[0]
                        num = num.replace('.','')
                        num = num.strip()
    
                        text = re.findall('.+\.',good_line)[0]
                        text = text.replace('.','')
                        columns.append([text,num])
                        continue
                   
                    columns.append([good_line,''])
            tables_list.append(columns)

# put tables from page into dataframes
        frame_string_list = []
        table_dataframes = []
        for table,page_no_table in zip(tables_list,page_no_table_list):
            if len(table)!=0:
                df = pd.DataFrame(table)
                table_dataframes.append(df)
                frame_string_list.append([df,page_no_table])
            else:
                table_dataframes.append('placeholder')
                frame_string_list.append(['placeholder',page_no_table])
        tables_in_10K_list.append(frame_string_list)

        time_end = time.time()
        parse_time = 'in {}s'.format(round(time_end-time_st,3))
#            print('regex text parse',parse_time)
        print(filing_info[0],'|',filing_info[1],'|','regex text parse {}'.format('|'),parse_time)

        parse_output.append(['regex text parse',parse_time])
    
    if k==0:
        break
    

#%%
cash_flow_list = []
cash_flow_check = []
SCF_multiplier_list = []
company_lines_indices = company_lines.index
page_string_list = []
for j,(company_lines_index,tables_and_strings) in enumerate(zip(company_lines_indices,tables_from_10Ks)):

    placeholder_indices = []
    for index, table_and_string in enumerate(tables_and_strings):
        table = table_and_string[0]
        page_string = table_and_string[1]
        if type(table)==str:
            placeholder_indices.append(index)
    # delete in reverse order not to throw off the indexing
    for index in sorted(placeholder_indices,reverse=True):
        del tables_and_strings[index]
    
    # go through each table in a 10K and condense each row to two columns    
    tables_formatted = []
    tables_in_10K = [table_and_string[0] for table_and_string in tables_and_strings]
    lhs_ind_list = []
    lhs_col_list = []
    rhs_col_list = []
    common_ind_list = []
    page_strings = []
    for counting,table_and_string in enumerate(tables_and_strings):    
        if counting<9:
            continue
        table_unformatted = table_and_string[0]
        page_string = table_and_string[1]
        iter_lines = []     
        lhs_col = []
        rhs_col = []
        common_ind = []
        # go through each line
        lhs_counter_list = []
        rhs_counter_list = []
        common_counter = 0
        for ind,line in enumerate(table_unformatted.iterrows()):
            line = [line[1][column] for column in table_unformatted.columns]
            iter_lines.append(line)
    
            add_parenthesis = False
            for line_member1 in line:
                if line_member1 is None:
                    continue
                
                # if there is a regex matching regular words i.e. net income
                if re.findall('[a-zA-Z]',line_member1):
                    lhs_counter_list.append(common_counter)                                   
                    lhs_member = line_member1
                    lhs_col.append(line_member1)
                    
                    for line_member2 in line:
                        if line_member2 is None:
                            continue
                        if line_member2 =='(':
                            add_parenthesis = True
                            continue
                        if re.findall('\({0,1}(?:\d+(?:,\d+)*(?:.\d+)*){0,1}',line_member2)[0] and line_member2!=lhs_member:
                            rhs_counter_list.append(common_counter)
                            if add_parenthesis:
                                rhs_member = '('+line_member2  
                                rhs_col.append(rhs_member) 
    
                                break
                            if not add_parenthesis:
                                rhs_member = line_member2    
                                rhs_col.append(rhs_member) 
                                
                                break
                    
                    common_counter+=1
                    break
     
        lhs_col_list.append(lhs_col)
        rhs_col_list.append(rhs_col)
        common_ind_list.append(rhs_counter_list)
    
        rhs_col_placeholders = ['']*len(lhs_col)
        for rhs_index,rhs_columns in zip(rhs_counter_list,rhs_col):
            rhs_col_placeholders[rhs_index] =  rhs_columns
        
        table_formatted = pd.DataFrame([lhs_col,rhs_col_placeholders]).transpose()
        tables_formatted.append(table_formatted)
        page_strings.append(page_string)


    for index, (page_string,table) in enumerate(zip(page_strings,tables_formatted)):

        left_column = table[0]
        left_column_list = list(table[0])
    
        left_column_list_raw = [i for i in left_column_list if i is not None]
        left_column_list = [i.replace(u'\xa0','') for i in left_column_list_raw]

        if  any([re.findall('net\s*income',item.lower()) for item in left_column_list]) \
            and any([re.findall('end\s*of|ending\s*balance',item.lower()) for item in left_column_list]) \
            and any([re.findall('cash\s*flow',item.lower()) for item in left_column_list]) \
            and not any([re.findall('quarter|three\s*months',item.lower()) for item in left_column_list]):
                
            # NOTE: still need to cut off this table at net income, rows below net income have duplicate names i.e. research and development
            cash_flow = table
            found_statement = 'Found SCF Filed',company_lines['date'][company_lines_index],'table index:{0}'.format(index)
            print(found_statement)
            
            page_string_list.append(page_string)
            cash_flow_check.append(found_statement)          
            break
    
    # remove all commas, end parenthesis, and correct negative signs
    cash_flow = cash_flow.applymap(lambda x: str(x))
    cash_flow = cash_flow.applymap(lambda x: x.replace(',',''))
    cash_flow = cash_flow.applymap(lambda x: x.replace(')',''))
    cash_flow = cash_flow.applymap(lambda x: x.replace('(','-'))
    
    cash_flow_indices = cash_flow.index
    cash_flow_columns = cash_flow.columns 
    
    # format IS page string to prepare for searching multiplier
    page_string = r"{}".format(page_string)
    page_string = page_string.replace(u'\xa0',' ')
    page_string = page_string.replace('\n','')
    page_string = page_string.replace('\\n','')
    
    page_string = page_string.lower()
    # look for income statement multiplier in income statement page text
    multipliers = r'(?:hundred|thousand|million|billion)'
    SCF_fmt1 = '(?:statements|statement)\s*of\s*cash\s*(?:flows|flow)\s*\(in\s*(%s)'
    SCF_page_re = re.compile(SCF_fmt1%tuple(([multipliers]*SCF_fmt1.count('%s'))))
    SCF_page_substring = SCF_page_re.findall(page_string)
    if SCF_page_substring:
        SCF_page_substring = SCF_page_substring[0]
    else:
        SCF_page_substring = ''
    
    if 'hundred' in SCF_page_substring:
        SCF_multiplier = 100
    elif 'thousand' in SCF_page_substring:
        SCF_multiplier = 1000
    elif 'million' in SCF_page_substring:
        SCF_multiplier = 1000000
    elif 'billion' in SCF_page_substring:
        SCF_multiplier = 1000000000
    else:
        print('No multiplier found in page text...')
        print('Searching for multiplier in table')
        
        # in the case the multiplier is not in the page text but in the table itself
        modified_multipliers = r'(?:in\s*hundreds|in\s*thousands|in\s*millions|in\s*billions)'
        cash_flow_indices = cash_flow.index
        for df_index in cash_flow_indices:
            row = cash_flow.loc[df_index]
            if any([re.findall(modified_multipliers,item) for item in row]):
                items = [re.findall(modified_multipliers,item) for item in row]
                items = [item[0] for item in items if len(item)!=0]
                item = ''.join(items)
                substring_list = ['in tens','in hundreds','in thousands','in millions','in billions']
                substring_multiplier_list = [10,100,1000,1000000,1000000000]
                for multiplier,substring in zip(substring_multiplier_list,substring_list):
                    if substring in item.lower():
                        SCF_multiplier = multiplier
                        print('multiplier found in table')
                        break
                    
        been_defined = 'SCF_multiplier' in locals() and 'SCF_multiplier' in globals()
        if not been_defined:
            print('No mulitplier found in table | defaulting multiplier to 1')
            SCF_multiplier = 1
                
    SCF_multiplier_list.append(SCF_multiplier)   
    
    #build a new income statement 
    new_row_list = []
    cash_flow_indices = cash_flow.index
    for df_index in cash_flow_indices:
        row = cash_flow.loc[df_index]
        new_row = []
        for index,item in enumerate(row):
            if index==0 and item!='':
                new_row.append(item)
    
            item_no_sign = item.replace('-','')
            item_no_sign_no_decimal = item_no_sign.replace('.','')
            if item_no_sign_no_decimal.isnumeric() and len(new_row)!=0:
                    item_as_float = float(item)*SCF_multiplier
                    new_row.append(item_as_float)    
                    break
        new_row_list.append(new_row)
    
    # delete multiplier as to not mess up later loop iterations
    del SCF_multiplier
    
    cash_flow = pd.DataFrame(new_row_list)
    cash_flow_list.append(cash_flow)
#    if j==0:
#        break
#%%
income_statement_list = []
income_statement_check = []
IS_multiplier_list = []
page_string_list = []

company_lines_indices = company_lines.index
for j,(company_lines_index,tables_and_strings) in enumerate(zip(company_lines_indices,tables_from_10Ks)):
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

    # go through each table in a 10K and condense each row to two columns    
    tables_formatted = []
    tables_in_10K = [table_and_string[0] for table_and_string in tables_and_strings]
    lhs_ind_list = []
    lhs_col_list = []
    rhs_col_list = []
    common_ind_list = []
    page_strings = []
    for counting,table_and_string in enumerate(tables_and_strings):    
        if counting<9:
            continue
        table_unformatted = table_and_string[0]
        page_string = table_and_string[1]
        iter_lines = []     
        lhs_col = []
        rhs_col = []
        common_ind = []
        # go through each line
        lhs_counter_list = []
        rhs_counter_list = []
        common_counter = 0
        for ind,line in enumerate(table_unformatted.iterrows()):
            line = [line[1][column] for column in table_unformatted.columns]
            iter_lines.append(line)
#            print(line)

            add_parenthesis = False
            for line_member1 in line:
                if line_member1 is None:
                    continue
                
                # if there is a regex matching regular words i.e. net income
                if re.findall('[a-zA-Z]',line_member1):
                    lhs_counter_list.append(common_counter)                                   
#                    print(line_member1)
                    lhs_member = line_member1
                    lhs_col.append(line_member1)
                    
                    for line_member2 in line:
                        if line_member2 is None:
                            continue
                        if line_member2 =='(':
                            add_parenthesis = True
                            continue
                        if re.findall('\({0,1}(?:\d+(?:,\d+)*(?:.\d+)*){0,1}',line_member2)[0] and line_member2!=lhs_member:
                            rhs_counter_list.append(common_counter)
                            if add_parenthesis:
                                rhs_member = '('+line_member2  
                                rhs_col.append(rhs_member) 

                                break
                            if not add_parenthesis:
                                rhs_member = line_member2    
                                rhs_col.append(rhs_member) 
                                
                                break
                    
                    common_counter+=1
                    break
     
        lhs_col_list.append(lhs_col)
        rhs_col_list.append(rhs_col)
        common_ind_list.append(rhs_counter_list)

        rhs_col_placeholders = ['']*len(lhs_col)
        for rhs_index,rhs_columns in zip(rhs_counter_list,rhs_col):
            rhs_col_placeholders[rhs_index] =  rhs_columns
        
        table_formatted = pd.DataFrame([lhs_col,rhs_col_placeholders]).transpose()
        tables_formatted.append(table_formatted)
        page_strings.append(page_string)
#        if counting==9:
#            break   
#    if j==0:
#        break
    
        # go through each table in the 10K and find the income statement
    for index, (page_string,table) in enumerate(zip(page_strings,tables_formatted)):
#        table = table_and_string[0]
#        page_string = table_and_string[1]
                
        left_column = table[0]
        left_column_list = list(table[0])
#        if index==9:
#            break
#    for index, (page_string,table) in enumerate(zip(page_strings,tables_formatted)):
#        print('-'*30)
#        print(left_column_list)
#        print('-'*30)
        left_column_list_raw = [i for i in left_column_list if i is not None]
        left_column_list = [i.replace(u'\xa0','') for i in left_column_list_raw]

#        left_column_list = [i for i in left_column_list if i is not None]
        if  any([re.findall('net\s*income',item.lower()) for item in left_column_list]) \
            and any([re.findall('(?:revenue|sales)',item.lower()) for item in left_column_list]) \
            and any([re.findall('cost\s*of\s*(?:revenue|sales)',item.lower()) for item in left_column_list]) \
            and not any([re.findall('quarter|three\s*months',item.lower()) for item in left_column_list]):                
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
    
    # format IS page string to prepare for searching multiplier
    page_string = r"{}".format(page_string)
    page_string = page_string.replace(u'\xa0',' ')
    page_string = page_string.replace('\n','')
    page_string = page_string.replace('\\n','')

    page_string = page_string.lower()
    # look for income statement multiplier in income statement page text
    multipliers = r'(?:hundred|thousand|million|billion)'
    IS_fmt1 = '(?:statements|statement)\s*of\s*(?:operations|operation|income)\s*\(in\s*(%s)'
    IS_page_re = re.compile(IS_fmt1%tuple(([multipliers]*IS_fmt1.count('%s'))))
    IS_page_substring = IS_page_re.findall(page_string)
    if IS_page_substring:
        IS_page_substring = IS_page_substring[0]
    else:
        IS_page_substring = ''

    if 'hundred' in IS_page_substring:
        IS_multiplier = 100
    elif 'thousand' in IS_page_substring:
        IS_multiplier = 1000
    elif 'million' in IS_page_substring:
        IS_multiplier = 1000000
    elif 'billion' in IS_page_substring:
        IS_multiplier = 1000000000
    else:
        print('No multiplier found in page text...')
        print('Searching for multiplier in table')
        
        # in the case the multiplier is not in the page text but in the table itself
        modified_multipliers = r'(?:in\s*hundreds|in\s*thousands|in\s*millions|in\s*billions)'
        income_statement_indices = income_statement.index
        for df_index in income_statement_indices:
            row = income_statement.loc[df_index]
            if any([re.findall(modified_multipliers,item) for item in row]):
                items = [re.findall(modified_multipliers,item) for item in row]
                items = [item[0] for item in items if len(item)!=0]
                item = ''.join(items)
                substring_list = ['in tens','in hundreds','in thousands','in millions','in billions']
                substring_multiplier_list = [10,100,1000,1000000,1000000000]
                for multiplier,substring in zip(substring_multiplier_list,substring_list):
                    if substring in item.lower():
                        IS_multiplier = multiplier
                        print('multiplier found in table')
                        break
                    
        been_defined = 'IS_multiplier' in locals()# or 'IS_multiplier' in globals()
        if not been_defined:
            print('defaulting multiplier to 1')
            IS_multiplier = 1
                
    IS_multiplier_list.append(IS_multiplier)   
    
#     build a new income statement 
    new_row_list = []
    income_statement_indices = income_statement.index
    for df_index in income_statement_indices:
        row = income_statement.loc[df_index]
        new_row = []
        for index,item in enumerate(row):
            if index==0 and item!='':
                new_row.append(item)

            item_no_sign = item.replace('-','')
            item_no_sign_no_decimal = item_no_sign.replace('.','')
            if item_no_sign_no_decimal.isnumeric() and len(new_row)!=0:
#                    print(item)
                    item_as_float = float(item)*IS_multiplier
                    new_row.append(item_as_float)    
                    break
        new_row_list.append(new_row)

    # delete multiplier as to not mess up later loop iterations
    del IS_multiplier

    income_statement = pd.DataFrame(new_row_list)
    income_statement_list.append(income_statement)
#%%
balance_sheet_list = []
balance_sheet_check = []
balance_sheet_string_list = []
#page_string_list = []
BS_multiplier_list = []
shares_out_string_list = []
shares_out_string_list_formatted = []
shares_out_multiplier_list = []
shares_out_page_list = []
shares_out_multiplier_page_list = []
shares_out_list = []
page_strings = []
test_list = []
bs_shares_out_multiplier_list = []
bs_shares_out_list = []
company_lines_indices = company_lines.index
for j,(company_lines_index,tables_and_strings) in enumerate(zip(company_lines_indices,tables_from_10Ks)):  
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

    # go through each table in a 10K and condense each row to two columns    
    tables_formatted = []
    tables_in_10K = [table_and_string[0] for table_and_string in tables_and_strings]
    lhs_ind_list = []
    lhs_col_list = []
    rhs_col_list = []
    common_ind_list = []
    page_strings = []
    for counting,table_and_string in enumerate(tables_and_strings):    
        table_unformatted = table_and_string[0]
        page_string = table_and_string[1]
        test_lines = []     
        lhs_col = []
        rhs_col = []
        common_ind = []
        
        # go through each line
        lhs_counter_list = []
        rhs_counter_list = []
        common_counter = 0
        for ind,line in enumerate(table_unformatted.iterrows()):
            line = [line[1][column] for column in table_unformatted.columns]
            test_lines.append(line)
            

            add_parenthesis = False
            for line_member1 in line:
                if line_member1 is None:
                    continue
                
                # if there is a regex matching regular words i.e. assets
                if re.findall('[a-zA-Z]',line_member1):
                    lhs_counter_list.append(common_counter)                                   
                    
                    lhs_member = line_member1
                    lhs_col.append(line_member1)

                    for line_member2 in line:
                        if line_member2 is None:
                            continue
                        if line_member2 =='(':
                            add_parenthesis = True
                            continue
                            
                        if re.findall('\({0,1}(?:\d+(?:,\d+)*(?:.\d+)*){0,1}',line_member2)[0] and line_member2!=lhs_member:
                            rhs_counter_list.append(common_counter)
                            if add_parenthesis:
                                rhs_member = '('+line_member2  
                                rhs_col.append(rhs_member) 

                                break
                            if not add_parenthesis:
                                rhs_member = line_member2    
                                rhs_col.append(rhs_member) 
                                
                                break
                    
                    common_counter+=1
                    break
        lhs_col_list.append(lhs_col)
        rhs_col_list.append(rhs_col)
        common_ind_list.append(rhs_counter_list)

        rhs_col_placeholders = ['']*len(lhs_col)
        for rhs_index,rhs_columns in zip(rhs_counter_list,rhs_col):
            rhs_col_placeholders[rhs_index] =  rhs_columns
        
        table_formatted = pd.DataFrame([lhs_col,rhs_col_placeholders]).transpose()
        tables_formatted.append(table_formatted)
        page_strings.append(page_string)



    # go through each table in the 10K and find the balance sheet
    for index, (page_string,table) in enumerate(zip(page_strings,tables_formatted)):
        #          
        left_column = table[0]

        # if true we have found the table representing the balance sheet
        if any(left_column.str.contains('retained',case=False,na=False)) and \
            any(left_column.str.contains('total assets',case=False,na=False)) \
            and any(left_column.str.contains('accounts payable',case=False,na=False)) \
            and any(left_column.str.contains('par value',case=False,na=False)):
                                        
            Balance_Sheet = table
            
            found_statement = 'Found BS Filed',company_lines['date'][company_lines_index],'table index:{0}'.format(index)
            print(found_statement)
            
            balance_sheet_string_list.append(page_string)
            balance_sheet_check.append(found_statement)
            break
    
    # find the string containing number of shares oustanding  
    for item in Balance_Sheet[0]:
        if 'common'.lower() \
        and 'stock'.lower() \
        and 'outstanding'.lower() \
        in str(item).lower()\
        and 'preferred'.lower() not in str(item).lower():
            shares_out_string_list.append(item)
            shares_out_string = item
 
    par_st = shares_out_string.find('$')
    par_end = shares_out_string.find('par value')+len('par value')
    par_value = shares_out_string[par_st:par_end]
    par_value = par_value.replace('$','')
    par_value = par_value.replace('par value','')
    par_value = par_value.replace(' ','')
    
    # format shares out string
    shares_out_string = r"{}".format(shares_out_string)
    shares_out_string = shares_out_string.replace(par_value,'')
    shares_out_string = shares_out_string.replace(u'\xa0',' ')
    shares_out_string = shares_out_string.replace('\n','')
    shares_out_string_formatted = shares_out_string.lower()
    shares_out_string_list_formatted.append(shares_out_string_formatted)


    multipliers = r'(?:hundred|thousand|million|billion)'
    so_fmt1 = r'issued\s*and\s*outstanding:\s*\d+(?:,\d+)*\s*%s{0,1}\s*and\s*(\d+(?:,\d+)*\s*%s{0,1})'
    so_fmt2 = r'(\d+(?:,\d+)*\s*%s{0,1})\s*and\s*\d+(?:,\d+)*\s*%s{0,1}\s*shares\s*issued\s*and\s*outstanding,'
    so_fmt3 = r'shares\s*issued\s*and\s*(\d+(?:,\d+)*\s*%s{0,1})\s*shares\s*outstanding'
    so_fmt4 = r'\d+(?:,\d+)*\s*%s{0,1}\s*and\s*(\d+(?:,\d+)*\s*%s{0,1})\s*shares\s*issued\s*and\s*outstanding\s*respectively'    
    
    so_regex_bank = [so_fmt1,so_fmt2,so_fmt3,so_fmt4]
    regex_bank_fmt = ['fmt1','fmt2','fmt3','fmt4']
    
    pattern = ''
    for so_regex,fmt in zip(so_regex_bank,regex_bank_fmt):

        pattern = re.compile(so_regex%(tuple([multipliers]*so_regex.count('%s'))))
        if pattern.findall(shares_out_string_formatted):
            print(fmt)
            shares_out_array = pattern.findall(shares_out_string_formatted)
            print(shares_out_array)
            break
#    if j==0:
#        break
    
    # find the shares outstanding multipliers from balance sheet then remove them
    bs_shares_out_sublist = []
    bs_shares_out_multiplier_array = []
    for shares_out in shares_out_array:
        if 'hundred' in shares_out:
            bs_shares_out_multiplier = 10
            shares_out = shares_out.replace('hundred','')
        elif 'thousand' in shares_out:
            shares_out = shares_out.replace('thousand','')
            bs_shares_out_multiplier = 1000
        elif 'million' in shares_out:
            shares_out = shares_out.replace('million','')
            bs_shares_out_multiplier = 1000000
        elif 'billion' in shares_out:
            shares_out = shares_out.replace('billion','')
            bs_shares_out_multiplier = 1000000000
        else:
            bs_shares_out_multiplier = 1
        bs_shares_out_multiplier_array.append(bs_shares_out_multiplier)
        bs_shares_out_sublist.append(shares_out)
   
    shares_out_sublist = [float(shares_out.replace(',','')) for shares_out,multiplier in zip(bs_shares_out_sublist,bs_shares_out_multiplier_array)]
    shares_out = sum(shares_out_sublist)
    bs_shares_out_multiplier_list.append(bs_shares_out_multiplier_array)
    bs_shares_out_list.append(shares_out)
    
    # format BS page string to prepare
    page_string = r"{}".format(page_string)
    page_string = page_string.replace(par_value,'')
    page_string = page_string.replace(u'\xa0',' ')
    page_string = page_string.replace('\n','')
    page_string = page_string.replace('\\n','')

    page_string = page_string.lower()
    
    # look for shares out multiplier in balance sheet page text
    so_page_fmt1 = 'number\s*of\s*shares.+in\s*(%s)'
    so_page_re = re.compile(so_page_fmt1%(tuple([multipliers]*so_page_fmt1.count('%s'))))
    page_shares_out = so_page_re.findall(page_string)
    test_list.append(page_string)
    if page_shares_out:
        page_shares_out = page_shares_out[0]
    else:
        page_shares_out = ''
    
    shares_out_multiplier_page_list.append(page_shares_out)

    if 'hundred' in page_shares_out:
        page_shares_out_multiplier = 10
        page_shares_out = page_shares_out.replace('hundred','')
    elif 'thousand' in page_shares_out:
        page_shares_out = page_shares_out.replace('thousand','')
        page_shares_out_multiplier = 1000
    elif 'million' in page_shares_out:
        page_shares_out = page_shares_out.replace('million','')
        page_shares_out_multiplier = 1000000
    elif 'billion' in page_shares_out:
        page_shares_out = page_shares_out.replace('billion','')
        page_shares_out_multiplier = 1000000000
    else:
        page_shares_out_multiplier = 1
    
    shares_out_multiplier_page_list.append(page_shares_out_multiplier)

    # compare shares out multiplier found in page text vs found in balance sheet
    shares_out_multiplier = max(bs_shares_out_multiplier,page_shares_out_multiplier)
    shares_out_multiplier_list.append(shares_out_multiplier)
    shares_out_list.append(shares_out_multiplier*int(shares_out))
    
    # look for balance sheet multiplier in balance sheet page text
    bs_fmt1 = 'balance\s*(?:sheets|sheet)\s*\(in\s*(%s)'
    bs_page_re = re.compile(bs_fmt1%tuple(([multipliers]*bs_fmt1.count('%s'))))
    bs_page_substring = bs_page_re.findall(page_string)
    if bs_page_substring:
        bs_page_substring = bs_page_substring[0]
    else:
        bs_page_substring = ''

    if 'hundred' in bs_page_substring:
        BS_multiplier = 100
    elif 'thousand' in bs_page_substring:
        BS_multiplier = 1000
    elif 'million' in bs_page_substring:
        BS_multiplier = 1000000
    elif 'billion' in bs_page_substring:
        BS_multiplier = 1000000000
    else:
        BS_multiplier = 1

        
    BS_multiplier_list.append(BS_multiplier) 
    
    
    # format balance sheet
    Balance_Sheet = Balance_Sheet.applymap(lambda x: str(x))
    Balance_Sheet = Balance_Sheet.applymap(lambda x: x.replace(',',''))
    Balance_Sheet = Balance_Sheet.applymap(lambda x: x.replace(')',''))
    Balance_Sheet = Balance_Sheet.applymap(lambda x: x.replace('(','-'))
    Balance_Sheet = Balance_Sheet.applymap(lambda x: x.replace('\x92',''))
    Balance_Sheet = Balance_Sheet.applymap(lambda x: x.replace('\n',''))

    Balance_Sheet_indices = Balance_Sheet.index
    Balance_Sheet_columns = Balance_Sheet.columns
    
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
            item_no_sign_no_decimal = item_no_sign.replace('.','')
            if item_no_sign_no_decimal.isnumeric() and len(new_row)!=0:
                    item_as_float = float(item)*BS_multiplier
                    new_row.append(item_as_float)    
                    break
                
        new_row_list.append(new_row)
    del BS_multiplier           
    Balance_Sheet = pd.DataFrame(new_row_list)
    balance_sheet_list.append(Balance_Sheet)

#BS_list, shares_out_list, BS_check, BS_multiplier_list, shares_out_multiplier_list = get_BSv3(tables_from_10Ks,company_lines)
#%%
#IS_list, IS_check, IS_multiplier_list = get_ISv3(tables_from_10Ks,company_lines)
#SCF_list, SCF_check, SCF_multiplier_list = get_SCFv3(tables_from_10Ks,company_lines)
