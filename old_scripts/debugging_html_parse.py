# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as bs
from bs4 import Tag
import requests
#%%
with open('testing_soup.txt') as f:
#    
    test_soup = bs(f,'lxml')
#    
#test_soup = bs(requests.get('https://www.sec.gov/Archives/edgar/data/1566610/000116552714000122/g7290.htm').content,'lxml')
#%%

def next_element(elem):
    while elem is not None:
        # Find next element, skip NavigableString objects
        elem = elem.next_sibling
        if hasattr(elem, 'name'):
            return elem
        
hrtags = test_soup.find_all('hr')

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


#%%
div_list = test_soup.find_all('hr')
#div_list = [i for i in all_divs if 'page-break' in i.get_text().lower()]
#%%
for i in range(len(div_list)):
    tag = div_list[i]
    next_tag = div_list[i+1]
    
    while tag!=next_tag:
        if not isinstance(tag,Tag):
            continue
        
            tag = tag.next_element
    if i==len(div_list)-2:
        break
#%%
page_list = []
for i in range(len(div_list)-1):
    div = div_list[i]
    print('i=',i)
    elem_list = []
    tag_list = []
    while div!=div_list[i+1]:

        if isinstance(div,Tag):
            tag = div
#            print(tag)
            tag_list.append(tag)
            if not tag.parent in tag_list:
                print(tag)
                elem_list.append(str(tag).replace('\n',''))
#                elem_list.append(tag)
        div = div.next_element

    page_list.append(elem_list)
    
pages_as_str = [''.join(page_sublist) for page_sublist in page_list]    
pages = [bs(page,'lxml') for page in pages_as_str]
#%%
table_tag = div_list[0].next_element.next_element.next_element.next_element.next_element.next_element
children = div_list[0].next_element.next_element.next_element.next_element.next_element.next_element.children
#if div_list[0].next_element.next_element.next_element.next_element.next_element.next_element.children not in table_tag:
#    print('true')
