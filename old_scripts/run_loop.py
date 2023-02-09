# -*- coding: utf-8 -*-
import os
#os.chdir('..')
#os.getcwd()
from get_statements import get_statements

working_dir = r'C:\Users\Owner\Documents\Analysis'  
selectcompany = 'Facebook' 
selectreport = '10-Q' 
selectYR = '2014' 
selectQTR = 'QTR2'

BS, IS, SCF = get_statements(selectcompany,selectreport,selectYR,selectQTR,working_dir)

year_start = 2019
year_end = 2019
years = [str(year_start+i) for i in range(year_end-year_start+1)]
quarters = ['QTR{0}'.format(x) for x in range(1,5)]

BS_list = []
IS_list = []
SCF_list = []
for yr in years:
    for qtr in quarters:

        print('YEAR: ',yr,' ',qtr)
        
        selectYR = yr
        selectQTR = qtr
        
        BS, IS, SCF = get_statements(selectcompany,selectreport,selectYR,selectQTR,working_dir)
        BS_list.append(BS)
        IS_list.append(IS)
        SCF_list.append(SCF)
        print("NEXT LOOP")
        
        
        