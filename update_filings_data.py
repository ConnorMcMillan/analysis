# -*- coding: utf-8 -*-

import edgar
import os
from datetime import datetime
import re
#%%
# GO THROUGH THIS CAREFULLY AND MAKE SURE YOU KNOW WHAT THE WORKING DIRECTORY IS AT ANY POINT
update_dir = r'C:\Users\Owner\Documents\Analysis\update_master_10K'
analysis_dir = r'C:\Users\Owner\Documents\Analysis'
year = datetime.now().strftime('%Y')
download = edgar.download_index(update_dir,int(year)-1,skip_all_present_except_last=False)
#%%
# update master 10K.tsv
files_list = os.listdir(update_dir)

# read the most current quarterly filing data of this year and get the 10-K lines       
new_lines = open(update_dir+'\\'+files_list[-2],'r')
update_lines = []
for line in new_lines:
    if re.search('10-K',line):
        update_lines.append(line)
new_lines.close()
#%%
new_lines = open(update_dir+'\\'+files_list[-1],'r')
for line in new_lines:
    if re.search('10-K',line):
        update_lines.append(line)
new_lines.close()

#%%
master_10K_old = open(analysis_dir+r'\master_10K.tsv','r')
master_10K_old_no_current_yr = []
for old_line in master_10K_old:
    if not re.findall(year+'-\d\d-\d\d',old_line):
        master_10K_old_no_current_yr.append(old_line)
master_10K_old.close()

master_10K_new = master_10K_old_no_current_yr+update_lines

updated_file = open(analysis_dir+r'\master_10K.tsv','w')
for line in master_10K_new:
    updated_file.write(line)
updated_file.close()
