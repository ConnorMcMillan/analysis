# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from yahoofinancials import YahooFinancials
from datetime import datetime
#%%
start_date = '2019-01-01'
end_date = datetime.today().strftime('%Y-%m-%d')
time_interval = 'daily' # weekly, monthly

MSFT_financials = YahooFinancials('MSFT') #MSFT JSON
MSFT = MSFT_financials.get_historical_price_data(start_date=start_date,end_date=end_date,time_interval=time_interval)

#%%
MSFT_price_df = pd.DataFrame(MSFT['MSFT']['prices'])
MSFT_price_df = MSFT_price_df.drop('date', axis=1).set_index('formatted_date')

MSFT_earnings = MSFT_financials.get_stock_earnings_data()
MSFT_earnings_df = pd.DataFrame(MSFT_earnings['MSFT']['earningsData']['quarterly'])
#%%
from pyfmpcloud import settings
from pyfmpcloud import company_valuation as cv

settings.set_apikey('e2e50da7484b51af6230a7d39e6f5fb9')



aapls = cv.balance_sheet('AAPL', period = 'annual', ftype = 'full')
#%%
import requests
from bs4 import BeautifulSoup


# def base URL
base_url = r'https://sec.gov/Archives/edgar/data'

# define a CIK number to do company search, GOLDMAN SACHS
cik_num = '/886982/'

# create filings URL for a company. we want json not html
filings_url = base_url+cik_num+'index.json'

# request the url
content = requests.get(filings_url)
decoded_content = content.json()

# go and grab a single filing number
filing_number = decoded_content['directory']['item'][0]['name']

#define our filing number url
filing_url = base_url+cik_num+filing_number+'/index.json'

# request the url for a single filing
content = requests.get(filing_url)
document_content = content.json()

# get the document names
for document in document_content['directory']['item']:
    if document['type'] != 'image2.gif':
        doc_name = document['name']
        document_url = base_url+cik_num+filing_number+'/'+doc_name
        print(document_url)
#%%

# def base URL
base_url = r'https://sec.gov/Archives/edgar/data'

# define a CIK number to do company search, GOLDMAN SACHS
cik_num = '/886982/'

# create filings URL for a company. we want json not html
filings_url = base_url+cik_num+'index.json'

# request the url
content = requests.get(filings_url)
decoded_content = content.json()


# go and grab a multiple filings
for filing in decoded_content['directory']['item']:
    
    # define each filing number
    filing_num = filing['name']
     
    # define our filing number url
    filing_url = base_url+cik_num+filing_num+'/index.json'
    
    # request the url for multiple filings
    content = requests.get(filing_url)
    document_content = content.json()
    
    # get the document names
    for document in document_content['directory']['item']:
        if document['type'] != 'image2.gif':
            doc_name = document['name']
            document_url = base_url+cik_num+filing_num+'/'+doc_name
            #print(document_url)

#%%
import urllib

# function that will make building a url easy
def make_url(base_url,comp):
    
    url = base_url
    
    #add each component to the base url
    
    for r in comp:  
        url = '{}/{}'.format(url,r)

    return url

base_url = r'https://sec.gov/Archives/edgar/data'

components = ['886982','000156459019011378','0001564590-19-011378-index-headers.html']

make_url(base_url,components)
#%%

# base url for the daily index files
base_url = r'https://sec.gov/Archives/edgar/daily-index'


# create the daily index url for 2019
year_url = make_url(base_url,['2019','index.json'])


# request the 2019 url
content = requests.get(year_url)
decoded_content = content.json()    

# loop through the dictionary
for item in decoded_content['directory']['item']:
    
    # get the name of folder
    print('-'*100)
    print('Pulling url for quarter {}'.format(item['name']))
    
    # create the qtr url
    qtr_url = make_url(base_url,['2019',item['name'],'index.json'])
    print(qtr_url)
    
    # request url and decode it
    file_content = requests.get(qtr_url)
    decoded_content = file_content.json()

    print('-'*100)
    print('Pulling files')
    
    for file in decoded_content['directory']['item']:
        
        file_url = make_url(base_url,['2019',item['name'],file['name']])
        print(file_url)

#%%
    
# define a master file url
        
file_url = r'https://sec.gov/Archives/edgar/daily-index/2019/QTR2/master.20190401.idx'

# make a request for that file
content = requests.get(file_url).content


# lets write the content to a text file
with open('master.20190401.txt','wb') as f:
    f.write(content)
#%%

# lets read the content
with open('master.20190401.txt','rb') as f:
    byte_data = f.read()


# decode the byte data
data = byte_data.decode('utf-8').split('  ')

# finding the starting index
for index, item in enumerate(data):
    
    if 'ftp://ftp.sec.gov/edgar/' in item:
        start_ind = index
    
# create a new list that removes the junk
data_format = data[start_ind+1:]
print('-'*5000)

master_data = []

# loop through the data list
for index, item  in enumerate(data_format):
    
    if index == 0:
        clean_item_data = item.replace('\n', '|').split('|')
        clean_item_data = clean_item_data[8:]
    else:
         clean_item_data = item.replace('\n', '|').split('|')

   # print(clean_item_data)

    for index, row in enumerate(clean_item_data):
        
        # when you find the txt file
        if '.txt' in row:
            
            mini_list = clean_item_data[(index-4): index+1]
            #print(mini_list)

            if len(mini_list) != 0:
                
                mini_list[4] = "https://sec.gov/Archives/"+mini_list[4]

                master_data.append(mini_list)
            
master_data[:3]
#%%
# loop through master data set

for index, document in enumerate(master_data):
    
    # create a dictionary
    document_dict = {}
    document_dict['cik_number'] = document[0]
    document_dict['company_name'] = document[1]
    document_dict['form_id'] = document[2]
    document_dict['date'] = document[3]
    document_dict['file_url'] = document[4]
    
    master_data[index] = document_dict

#%%

for document_dict in master_data:
    if document_dict['form_id']=='10-K':
        print(document_dict['company_name'])
        print(document_dict['file_url'])

for member in master_data:
    #print(member['form_id'])
    if member['form_id'] == '10-K':
        print (member['form_id'])
        print(member['file_url'])

#%%
# import libraries
import requests
import pandas as pd
from bs4 import BeautifulSoup

base_url = r'https://www.sec.gov'

# 10K url from master list
# base_url = https://www.sec.gov/Archives/edgar/data/949961/0001387131-19-002363.txt

# 10K url in more friendly format, no dashes+/index.json
documents_url = r'https://www.sec.gov/Archives/edgar/data/949961/000138713119002363/index.json'

#request the url and decode it
content = requests.get(documents_url).json()

for file in content['directory']['item']:
    
    #grab the filing summary and create a new url leading to the file so we can download it
    if file['name'] == 'FilingSummary.xml':
        xml_summary = base_url+content['directory']['name']+'/'+file['name']
        
        print('-'*100)
        print('File Name: '+file['name'])
        print('File Path: '+xml_summary)
        
#%%
        
# define a new base url the represents the filing folder. This will come in handy when we need to download the reports

base_url = xml_summary.replace('FilingSummary.xml','')

#request and parse the content
content = requests.get(xml_summary).content
soup = BeautifulSoup(content,'lxml')

# find the "myreports" tag because this contains all the individual reports submitted
reports = soup.find('myreports')
reports

# I want a list of reports to store all the individual components of the report, so create the master list
master_reports = []

# loop through each report in the "myreports" tag but avoid the last one as this will cause an error
for report in reports.find_all('report')[:-1]:
    
    # lets create a dictionary to store all the different parts we need
    report_dict = {}
    report_dict['name_short'] = report.shortname.text
    report_dict['name_long'] = report.longname.text
    report_dict['position'] = report.position.text
    report_dict['category'] = report.menucategory.text
    report_dict['url'] = base_url+report.htmlfilename.text
    
    # append the dictionary to the master list of reports
    master_reports.append(report_dict)
    
    # print the info to the user
    print('-'*100)
    print(base_url+report.htmlfilename.text)
    print(report.longname.text)
    print(report.shortname.text)
    print(report.menucategory.text)
    print(report.position.text)
#%%

# create the list to hold the statment urls
statements_url = []

for report_dict in master_reports:
    
    # define the staements we want to look for
    item1 = r"Consolidated Balance Sheets"
#    item1 = r"CONSOLIDATED BALANCE SHEETS"
    item2 = r"Consolidated Statements of Operations and Comprehensive Income (Loss)"
#    item2 = r"CONSOLIDATED STATEMENTS OF OPERATIONS AND COMPREHENSIVE INCOME (LOSS)"
    item3 = r"Consolidated Statements of Cash Flows"
    item4 = r"Consolidated Statements of Stockholder's (Deficit Equity)"
    
    # store them in a list
    report_list = [item1,item2,item3,item4]
    
    # if the short name can be found in the report list
    if report_dict['name_short'] in report_list:
        
        # print some info and share it in the statements url
        print('-'*100)
        print(report_dict['name_short'])
        print(report_dict['url'])
        
        statements_url.append(report_dict['url'])
#    else:
#        print("NOT FOUND")
#%%
# define the endpoint to do filing searches.
search_form_type = r"https://www.sec.gov/cgi-bin/srch-edgar"

# define the arguments of the request
search_form_params = {'text':'form-type=(10-K)',
                     'start':start,
                     'count':100,
                     'output':'atom',
                     'first':2012,
                     'last':2014}

# make the request
form_type_response = requests.get(url = search_form_type, params =search_form_params)
#%%

