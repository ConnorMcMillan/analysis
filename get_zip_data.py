# -*- coding: utf-8 -*-
import requests
import requests, zipfile, io
import re
import datetime
import itertools
#%%

#zip_url = 'https://www.sec.gov/files/dera/data/financial-statement-data-sets/2009q2.zip'
zip_urls = [['https://www.sec.gov/files/dera/data/financial-statement-data-sets/'+str(yr)+'q'+str(qtr)+'.zip' for qtr in range(1,5)] for yr in range(2009,datetime.datetime.today().year+1)]
zip_urls = [j for i in zip_urls for j in i] 
for zip_url in zip_urls:
    year_re = re.compile('2\d{3}')
    qtr_re = re.compile('q\d{1}')
    yr = year_re.findall(zip_url)[0]
    qtr = qtr_re.findall(zip_url)[0]
    
    r = requests.get(zip_url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    destination_path = r'C:\Users\Owner\Documents\Analysis_data_needed\{}{}'.format(yr,qtr)
    z.extractall(destination_path)
