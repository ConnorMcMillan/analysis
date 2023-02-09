# -*- coding: utf-8 -*-

#from get_10K_filings_lines import get_10K_filings_lines
import pandas as pd
from bs4 import BeautifulSoup as bs
from bs4 import Tag
import requests  
import os
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
#%%
def textTillNextPage(t):
    s = ""
    while t != None and not (isinstance(t, Tag) and t.name == 'hr'):
        s += str(t)
        t = t.nextSibling
    return t, s    
#%%
def get_10K_tables_v3(company_lines):
    url_list = []
    indices = company_lines.index
    for index in indices:
        txt_extension = company_lines['txt extension'][index]   
        filing_url = 'https://www.sec.gov/Archives/'+txt_extension
        url_list.append(filing_url)
        
    # add extension to get to the actual 10K file in the filing
    url_10K_list = []
    tables_in_10K_list = []
    for url in url_list:

        url_10K_list.append(url)
        
        r = requests.get(url)
        parser = 'lxml'
        soup = bs(r.content,parser)
          
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
            text_no_table = bs(text_no_table,'lxml').get_text(strip=True)
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
#        tables_in_10K_list.append([frame_string_list,'bs4 {} parse'.format(parser)])
    return tables_in_10K_list,url_10K_list
#%%
#def get_10K_tables_v3(company_lines):
#    url_list = []
#    indices = company_lines.index
#    for index in indices:
#        txt_extension = company_lines['txt extension'][index]   
#        filing_url = 'https://www.sec.gov/Archives/'+txt_extension
#        url_list.append(filing_url)
#        
#    # add extension to get to the actual 10K file in the filing
#    url_10K_list = []
#    tables_in_10K_list = []
#    for url in url_list:
#
#        url_10K_list.append(url)
#        
#        r = requests.get(url)
#        soup = bs(r.content,'lxml')
#          
#        # Pull out all the text (with tags) between HR tags, which
#        # delineate the pages in the document
#        tag = soup.find('hr')
#               
#        # Loop through the document until the end, and pull out each page
#        pages = []
#        t = tag.nextSibling
#        while not (t == None):
#            t, s = textTillNextPage(t)
#            pages.append(s)
#            if t != None:
#                t = t.nextSibling
#    
#        # for each page, get the table and title and multiplier (hundred, thousand, million, etc.)
#        tables_list = []
#        page_no_table_list = []
#        for index, page in enumerate(pages):
#            page_soup = bs(page,'lxml')
#            
#            # remove the table from page to get pre and post table text
#            table_on_page_string = str(page_soup.table)
#            text_no_table = page.replace(table_on_page_string,'')
#            text_no_table = bs(text_no_table,'lxml').get_text(strip=True)
#            page_no_table_list.append(text_no_table)
#            
#            # get table from each page
#            tables = [[[td.get_text(strip=True) for td in tr.find_all('td')] for tr in table.find_all('tr')] for table in page_soup.find_all('table')]
#            tables_list.append(tables)
#        
#        # put tables from page into dataframes
#        frame_string_list = []
#        table_dataframes = []
#        for table,page_no_table in zip(tables_list,page_no_table_list):
#            if len(table)!=0:
#                df = pd.DataFrame(table[0])
#                table_dataframes.append(df)
#                frame_string_list.append([df,page_no_table])
#            else:
#                table_dataframes.append('placeholder')
#                frame_string_list.append(['placeholder',page_no_table])
#            
#        tables_in_10K_list.append(frame_string_list)
#
#    return tables_in_10K_list,url_10K_list
#%%
if __name__=="__main__":
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup as bs
    from bs4 import Tag
    import urllib
    import re
    import time
    
    def textTillNextPage(t):
        s = ""
        while t != None and not (isinstance(t, Tag) and t.name == 'hr'):
            s += str(t)
            t = t.nextSibling
        return t, s        
    
    def next_element(elem):
        while elem is not None:
            # Find next element, skip NavigableString objects
            elem = elem.next_sibling
            if hasattr(elem, 'name'):
                return elem
    
    company_lines = pd.read_csv('testing_df')
    #company_lines = company_lines[0:1]
    
    
    url_list = []
    indices = company_lines.index
    for index in indices:
        txt_extension = company_lines['txt extension'][index]   
        filing_url = 'https://www.sec.gov/Archives/'+txt_extension
        url_list.append(filing_url)
        
    # add extension to get to the actual 10K file in the filing
    url_10K_list = []
    tables_in_10K_list = []
    
    #url_list = ['https://www.sec.gov/Archives/edgar/data/320193/0001047469-04-035975.txt']
    tot_st = time.time()
    for big_index,url in enumerate(url_list):
        time_st = time.time()
        try:
            url_10K_list.append(url)
            r = requests.get(url)
            parser = 'lxml'
            soup = bs(r.content,parser)
            
            
            hrtags = soup.find_all('hr')
           
            # if no hr tags found, try parsing with re
            if not hrtags:
                raise ValueError()
                
            pages = []
            for hrtag in hrtags:
                page = [str(hrtag)]
                elem = next_element(hrtag)
                while elem and elem.name != 'hr':
                    page.append(str(elem))
                    elem = next_element(elem)
                pages.append('\n'.join(page))
            
        
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
            tables_in_10K_list.append([frame_string_list,'bs4 parse'])
        
        
        # try for plain text docs
        except:
            print('parsing with re')
        
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
            tables_in_10K_list.append([frame_string_list,'text parse'])
            
            
        time_end = time.time()
        print('parsed in {}'.format(time_end-time_st))
        
        if big_index==3:
            break
    tot_end = time.time()
    tot_time = (tot_end-tot_st)
    print('total time',tot_time)