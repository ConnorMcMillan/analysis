import sqlite3
import pandas as pd
import os
from pathlib import Path
#%%
# search for all filings
SEC_data_path = r'C:\Users\Owner\Documents\SEC_data'
quarter_folders = os.listdir(SEC_data_path)
sub_list = []
num_list = []
for quarter_folder in quarter_folders:
    qtr_data_path = SEC_data_path+'\\'+quarter_folder
    os.listdir(qtr_data_path)
    sub_data_path = SEC_data_path+'\\'+quarter_folder+'\\sub.txt'
    num_data_path = SEC_data_path+'\\'+quarter_folder+'\\num.txt'

    sub = pd.read_csv(sub_data_path,sep='\t')
    num = pd.read_csv(num_data_path,sep='\t')
    sub_list.append(sub)
    num_list.append(num)
#num = pd.read_csv(num_data_path,sep='\t')
#%%
# add new record to table
def add_line(adsh,cik,name,sic,form,period,filed,prevrpt,instance):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()

    database_name = os.path.basename(database_path)    
    c.execute("INSERT INTO {} VALUES (?,?,?,?,?,?,?,?,?)".format(database_name.replace('.db','')) \
              ,(adsh,cik,name,sic,form,period,filed,prevrpt,instance))
    conn.commit()
    conn.close()
#%%
submissions_database_path = r'C:\Users\Owner\Documents\Analysis_database\submissions.db'

# create submissions database
conn = sqlite3.connect(submissions_database_path)
# create cursor
c = conn.cursor()

# create table
c.execute("""CREATE TABLE submissions (
		adsh text,
		cik integer,
		name text,
     sic integer,
     form text,
     period text,
     filed text,
     prevrpt integer,
     instance text)
	""")
conn.commit()
conn.close()
#%%
# create numbers database
numbers_database_path = r'C:\Users\Owner\Documents\Analysis_database\numbers.db'

# create submissions database
conn = sqlite3.connect(numbers_database_path)
# create cursor
c = conn.cursor()

# create table
c.execute("""CREATE TABLE numbers (
		adsh text,
		tag text,
		version text,
     ddate text,
     qtrs integer,
     uom text,
     value real,
     coreg text,
     footnote text)
	""")
conn.commit()
conn.close()
#%%
import re
def get_CIK(ticker):
    with open('ticker-cik.txt','r') as f:
        content = f.readlines()
        for line in content:     
            tick = re.findall('[A-Za-z]*',line)[0]
            cik = int([i for i in re.findall('(\d*)',line) if i!=''][0])
            if tick==ticker.lower():
                break
    
    return cik
cik = get_CIK('FB')
#%%
##build submission db
#conn = sqlite3.connect(submissions_database_path)
#for sub in sub_list:
#    sub[['adsh','cik','name','sic','form','period','filed','prevrpt','instance']].to_sql('submissions',con=conn,if_exists='append',index=False)
#conn.commit()
#conn.close()
#%%
conn = sqlite3.connect(submissions_database_path)
table1 = pd.read_sql("SELECT * FROM submissions WHERE cik={} and form='10-K'".format(cik),conn)
conn.close()

#%%
#build numbers db
conn = sqlite3.connect(numbers_database_path)
for num in num_list:
    num[['adsh','tag','version','ddate','qtrs','uom','value','coreg','footnote']].to_sql('numbers',con=conn,if_exists='append',index=False)
conn.commit()
conn.close()
#%%


adsh = table1['adsh'][0]
period = table1['period'][0]

#adsh = '0001047469-11-001125'
#%%

conn = sqlite3.connect(numbers_database_path)

#table2 = pd.read_sql("SELECT adsh,tag,uom,value,MAX(ddate) FROM numbers WHERE adsh='{}' and ddate={}".format(adsh,period),conn)
table2 = pd.read_sql("""
                     SELECT adsh,tag,uom,value,ddate,coreg 
                     FROM numbers 
                     WHERE adsh='{}' and coreg IS NULL""".format(adsh,period),conn)

conn.close()
#%%
company_lines_db_path = r'C:\Users\Owner\Documents\Analysis_database\company_lines.db'

conn = sqlite3.connect(company_lines_db_path)
# create cursor
c = conn.cursor()

# create table
c.execute("""CREATE TABLE company_lines (
		cik integer,
		name text,
     form text,
	  date text,
     txt_extension text,
     html_extension text)
    	""")
#c.execute("DROP TABLE company_lines")

conn.commit()
conn.close()
#%%
import datetime
import edgar


update_dir = r'C:\Users\Owner\Documents\Analysis\update_master_10K'
analysis_dir = r'C:\Users\Owner\Documents\Analysis'
#year = datetime.now().strftime('%Y')
#download = edgar.download_index(update_dir,int(year)-1,skip_all_present_except_last=False)

#build company_lines db
download = edgar.download_index(update_dir,2009,skip_all_present_except_last=False)

#%%
files = os.listdir(update_dir)
files = [update_dir+'\\'+file for file in files]

company_lines_db_path = r'C:\Users\Owner\Documents\Analysis_database\company_lines.db'
conn = sqlite3.connect(company_lines_db_path)

for file in files:
    qtr = pd.read_csv(file,sep='|')
    qtr.columns = ['cik','name','form','date','txt_extension','html_extension']
    qtr.to_sql('company_lines',con=conn,if_exists='append',index=False)
    
conn.commit()
conn.close()
#%%
# add 'coreg' column to numbers
#numbers_database_path = r'C:\Users\Owner\Documents\Analysis_database\numbers.db'
#
## create submissions database
#conn = sqlite3.connect(numbers_database_path)
## create cursor
#c = conn.cursor()
#
#
#for num in num_list:
#    coreg = num['coreg']
#    
#    if any(list(coreg.astype(str)))!='nan':
#        print('broke')
#        break
#
## add column to numbers table
#c.execute("""ALTER TABLE numbers 
#            ADD COLUMN coreg text
#
#	""")
#conn.commit()
#conn.close()
#
#conn = sqlite3.connect(numbers_database_path)
#conn.commit()
#conn.close()


#%%