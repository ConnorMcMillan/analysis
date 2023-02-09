# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 14:02:42 2021

@author: Owner
"""


from get_10K_filings_lines import get_10K_filings_lines
import pandas as pd
from bs4 import BeautifulSoup as bs
from bs4 import Tag
import requests  
#%%
    
def textTillNextPage(t):
    s = ""
    while t != None and not (isinstance(t, Tag) and t.name == 'hr'):
        s += str(t)
        t = t.nextSibling
    return t, s    


#%%   

#company_lines = pd.read_csv('test_df.txt')
def get_10K_tables_v2(company_lines):
    extension_list = []
    url_formatted_list = []
    indices = company_lines.index
    for index in indices:
        html_extension = company_lines['html extension'][index]   
        filing_url = 'https://www.sec.gov/Archives/'+html_extension
        
        url_formatted = filing_url.replace('-','').replace('index.html','')
        url_formatted_list.append(url_formatted)
        files_in_10K_filing = pd.read_html(url_formatted)
        
        # search for 10K. or 10-K. in list of files for a 10K filing. Note the "."
        for file_name in files_in_10K_filing[0]['Name']:
            
            if file_name.lower().find('10K.'.lower())!=-1 or file_name.lower().find('10-K.'.lower())!=-1 :
                print('Found 10K for',company_lines['date'][index])
                extension = file_name
                extension_list.append(extension) 
        
    # add extension to get to the actual 10K file in the filing
    url_10K_list = []
    tables_in_10K_list = []
    for url_extension,url_formatted in zip(extension_list,url_formatted_list):
        url_10K = url_formatted+'/'+url_extension
        url_10K_list.append(url_10K)
        
        r = requests.get(url_10K)
        soup = bs(r.content,'lxml')
          
        # Pull out all the text (with tags) between HR tags, which
        # delineate the pages in the document
        tag = soup.find('hr')
               
        # Loop through the document until the end, and pull out each page
        pages = []
        t = tag.nextSibling
        while not (t == None):
            t, s = textTillNextPage(t)
            pages.append(s)
            if t != None:
                t = t.nextSibling
    
    
        # for each page, get the table and title and multiplier (hundred, thousand, million, etc.)
        tables_list = []
        page_no_table_list = []
        for index, page in enumerate(pages):
            page_soup = bs(page,'lxml')
            
            # remove the table from page to get pre and post table text
            table_on_page_string = str(page_soup.table)
            text_no_table = page.replace(table_on_page_string,'')
            text_no_table = bs(text_no_table).get_text(strip=True)
            page_no_table_list.append(text_no_table)
            
            # get table from each page
            tables = [[[td.get_text(strip=True) for td in tr.find_all('td')] for tr in table.find_all('tr')] for table in page_soup.find_all('table')]
            tables_list.append(tables)
        
        
        # put tables from page into dataframes
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
    
    return tables_in_10K_list,url_10K_list

#%%