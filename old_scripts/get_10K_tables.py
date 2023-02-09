# -*- coding: utf-8 -*-

from get_10K_filings_lines import get_10K_filings_lines
import pandas as pd
#%%

def get_10K_tables(company_lines):
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
#            print(file_name)
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
        
        tables = pd.read_html(url_10K)
        tables_in_10K_list.append(tables)
    
    return tables_in_10K_list, url_10K_list

