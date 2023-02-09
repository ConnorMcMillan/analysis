# -*- coding: utf-8 -*-

def get_statements(selectcompany,selectreport,selectYR,selectQTR,working_dir):
    r"working_dir = r'C:\Users\Owner\Documents\Analysis' \
    selectcompany = 'Facebook' \
    selectreport = '10-Q' \
    selectYR = '2014' \
    selectQTR = 'QTR2'"
    
    import edgar
    import pandas as pd
    import os
    
    filings_data_dir = working_dir+r'\FilingsData'
    os.chdir(filings_data_dir)
    csv = pd.read_csv(selectYR+'-'+selectQTR+'.tsv',sep='/t',lineterminator='\n',names=None)
    csv.columns.values[0] = 'Item'
    
    
    # filter all filings by company 
    companyreport = csv[(csv['Item'].str.contains(selectcompany))] 
    if len(companyreport)==0:
        raise ValueError('No Data Found for '+selectcompany)
    
    # filter all filings by report type (ie 10Q)
    companyreport = companyreport[(companyreport['Item'].str.contains(selectreport))]
    if len(companyreport)==0:
        raise ValueError('No '+selectreport+' found for this year and quarter')
    
    Filing = companyreport['Item'].str.split('|')
    Filing = Filing.tolist()
    
    
    # get the url for the report we want
    for item in Filing[0]:
        if 'html' in item:
            report = item
    
    url = 'https://www.sec.gov/Archives/'+report    
    
    # read the filing with pandas and take the first table
    df = pd.read_html(url)        
    document_index = df[0]
    document_index = document_index.dropna()
    
    # from first table get the rest of the url we need to get the report
    document_name = document_index[document_index['Description'].str.contains(selectreport)]
    document_name = document_name['Document'].str.split(' ')
    document_name = document_name[0][0]
    document_name
    
    # edit the part of the url we want to change
    report_formatted = report.replace('-','').replace('index.html','')
    report_formatted
    
    # url to the 10Q balance sheet
    url = 'https://www.sec.gov/Archives/'+report_formatted+'/'+document_name
    
    # read blance sheet into pandas
    df = pd.read_html(url)
    
    for index,item in enumerate(df):
        
        # find the balance sheet
        # if first column of table contains either keyword
    #    BS = item[0].str.contains('Retained' or 'Total Assets')
        left_column = item[0]
        # if true we have found the table representing the balance sheet
        if any(left_column.str.contains('retained',case=False,na=False)) and \
            any(left_column.str.contains('total assets',case=False,na=False)) \
            and any(left_column.str.contains('accounts payable',case=False,na=False)):
            
            Balance_Sheet = item
            print(index,'Found Balance Sheet')
    
        # if true we have found the table representing the income statement
        if any(left_column.str.contains('marketing and sales',case=False,na=False)) and \
            any(left_column.str.contains('net income',case=False,na=False)) \
            and any(left_column.str.contains('research and development',case=False,na=False)) \
            and any(left_column.str.contains('cost of revenue',case=False,na=False)) and '%' not in item.to_string():
            
                
            Income_Statement = item
            print(index,'Found Income Statement')
            
        # if true we have found the table representing the statement of cash flows
        if any(left_column.str.contains('net income',case=False,na=False)) and \
            any(left_column.str.contains('end of period',case=False,na=False)) \
            and any(left_column.str.contains('cash flow',case=False,na=False)):
            
            Cash_Flow = item
            print(index,'Found Satement of Cash Flow')
    
        
    
    # cut out the junk rows and columns of the table representing the balance sheet
    Balance_Sheet = Balance_Sheet.iloc[2:,[0,2,6]]
    Balance_Sheet_header = Balance_Sheet.iloc[0]
    Balance_Sheet = Balance_Sheet[1:]
    
    # cut out the junk rows and columns of the table representing the income statement
    Income_Statement = Income_Statement.iloc[4:,[0,2,6]]
    Income_Statement_header = Income_Statement.iloc[0]
    Income_Statement = Income_Statement[1:]
    
    # cut out the junk rows and columns of the table representing the statement of cash flows
    Cash_Flow = Cash_Flow.iloc[3:,[0,2,6]]
    Cash_Flow_header = Cash_Flow.iloc[0]
    Cash_Flow = Cash_Flow[1:]
    
    # continue formatting the balance sheet
    Balance_Sheet.columns = Balance_Sheet_header
    Balance_Sheet.columns.values[0] = 'Item'
    Balance_Sheet = Balance_Sheet[Balance_Sheet['Item'].notna()]
    
    # continue formatting the income statement
    #Income_Statement.columns = Income_Statement_header
    Income_Statement.columns = Balance_Sheet_header
    
    Income_Statement.columns.values[0] = 'Item'
    Income_Statement = Income_Statement[Income_Statement['Item'].notna()]
    
    # continue formatting the statement of cash flows
    #Cash_Flow.columns = Cash_Flow_header
    Cash_Flow.columns = Balance_Sheet_header
    Cash_Flow.columns.values[0] = 'Item'
    Cash_Flow = Cash_Flow[Cash_Flow['Item'].notna()]
    
    
    # convert to string
    #Balance_Sheet.columns = ['Item','March 31, 2014', 'March 31, 2014']
    Balance_Sheet[Balance_Sheet.columns[1:]] = Balance_Sheet[Balance_Sheet.columns[1:]].astype(str)
    
    # replace parenthesis with negative signs
    Balance_Sheet[Balance_Sheet.columns[1]] = Balance_Sheet[Balance_Sheet.columns[1]].map(lambda x: x.replace('(','-'))
    Balance_Sheet[Balance_Sheet.columns[2]] = Balance_Sheet[Balance_Sheet.columns[2]].map(lambda x: x.replace('(','-'))
    
    # replace commas with empty spaces
    Balance_Sheet[Balance_Sheet.columns[1]] = Balance_Sheet[Balance_Sheet.columns[1]].map(lambda x: x.replace(',',''))
    Balance_Sheet[Balance_Sheet.columns[2]] = Balance_Sheet[Balance_Sheet.columns[2]].map(lambda x: x.replace(',',''))
    
    # replace "-" dash with 0
    Balance_Sheet[Balance_Sheet.columns[1]] = Balance_Sheet[Balance_Sheet.columns[1]].map(lambda x: x.replace('—','0'))
    Balance_Sheet[Balance_Sheet.columns[2]] = Balance_Sheet[Balance_Sheet.columns[2]].map(lambda x: x.replace('—','0'))
    
    # convert to float
    Balance_Sheet[Balance_Sheet.columns[1:]] = Balance_Sheet[Balance_Sheet.columns[1:]].astype(float)
    
    # convert to string
    Cash_Flow[Cash_Flow.columns[1:]] = Cash_Flow[Cash_Flow.columns[1:]].astype(str)
    
    # replace parenthesis with negative signs
    Cash_Flow[Cash_Flow.columns[1]] = Cash_Flow[Cash_Flow.columns[1]].map(lambda x: x.replace('(','-'))
    Cash_Flow[Cash_Flow.columns[2]] = Cash_Flow[Cash_Flow.columns[2]].map(lambda x: x.replace('(','-'))
    
    # replace commas with empty spaces
    Cash_Flow[Cash_Flow.columns[1]] = Cash_Flow[Cash_Flow.columns[1]].map(lambda x: x.replace(',',''))
    Cash_Flow[Cash_Flow.columns[2]] = Cash_Flow[Cash_Flow.columns[2]].map(lambda x: x.replace(',',''))
    
    # replace "-" dash with 0
    Cash_Flow[Cash_Flow.columns[1]] = Cash_Flow[Cash_Flow.columns[1]].map(lambda x: x.replace('—','0'))
    Cash_Flow[Cash_Flow.columns[2]] = Cash_Flow[Cash_Flow.columns[2]].map(lambda x: x.replace('—','0'))
    
    # convert to float
    Cash_Flow[Cash_Flow.columns[1:]] = Cash_Flow[Cash_Flow.columns[1:]].astype(float)
    
    # convert to string
    Income_Statement[Income_Statement.columns[1:]] = Income_Statement[Income_Statement.columns[1:]].astype(str)
    
    # replace parenthesis with negative signs
    Income_Statement[Income_Statement.columns[1]] = Income_Statement[Income_Statement.columns[1]].map(lambda x: x.replace('(','-'))
    Income_Statement[Income_Statement.columns[2]] = Income_Statement[Income_Statement.columns[2]].map(lambda x: x.replace('(','-'))
    
    # replace commas with empty spaces
    Income_Statement[Income_Statement.columns[1]] = Income_Statement[Income_Statement.columns[1]].map(lambda x: x.replace(',',''))
    Income_Statement[Income_Statement.columns[2]] = Income_Statement[Income_Statement.columns[2]].map(lambda x: x.replace(',',''))
    
    # replace "-" dash with 0
    Income_Statement[Income_Statement.columns[1]] = Income_Statement[Income_Statement.columns[1]].map(lambda x: x.replace('—','0'))
    Income_Statement[Income_Statement.columns[2]] = Income_Statement[Income_Statement.columns[2]].map(lambda x: x.replace('—','0'))
    
    # convert to float
    Income_Statement[Income_Statement.columns[1:]] = Income_Statement[Income_Statement.columns[1:]].astype(float)

    return (Balance_Sheet,Income_Statement,Cash_Flow)