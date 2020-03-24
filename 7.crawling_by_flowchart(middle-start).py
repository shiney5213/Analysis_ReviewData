import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import time
from selenium.webdriver.common.keys import Keys
#from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import numpy as np
import sys
import re

def get_info(html, shop_name, shop_address):
# shop 주소, 총 별점 갖고오기
    search_name, address, total_score, match=get_totalScore(html,shop_name, shop_address)
    
    # shop info가 있는가(addrsss로 확인)
    if address == '':
        review_list = ''
        score_list = ''
        return search_name, address,total_score, review_list, score_list, match 

    # 리뷰가 없는 경우    
    if  total_score == 0:
        review_list = 0
        score_list= 0
        
    # 리뷰가 있는 경우
    else:
        # 리뷰 text(버튼 )클릭
        review_button = driver.find_element_by_xpath('//button[@class="jqnFjrOWMVU__button gm2-caption"]')
        review_button.click()

        time.sleep(SCROLL_PAUSE_TIME)

        # 스크롤 다운
        try:
            element = driver.find_element_by_xpath('//span[@class="section-review-text"]')
            element.click()
        except Exception as err:
            print(err)

        i = 0
        while  True:
            i += 1
            html = driver.find_element_by_tag_name('html')
            time.sleep(SCROLL_PAUSE_TIME)

            text1 = html.text
            html.send_keys(Keys.END)
            time.sleep(SCROLL_PAUSE_TIME)

            html = driver.find_element_by_tag_name('html')
            text2 = html.text

            if text1 == text2:
                break
            else:
                continue
    
        review_html = driver.page_source

        review_list, score_list=get_review(review_html) 
        driver.back()
    return search_name, address, total_score, review_list, score_list, match


def get_review(html):
	soup = BeautifulSoup(html, 'html.parser')
	# 개별 리뷰
	total_review =soup.find_all('span',attrs = {'class': "section-review-text"} )

	review_list=[]
	for i, review in enumerate(total_review):
			review_list.append(review.text)

	#### 개별 별점
	scores =soup.find_all('span',attrs = {'class': "section-review-stars", 'role': 'img'} )

	score_list = []
	for score in scores:
			score_list.append(score.attrs['aria-label'])

	return review_list, score_list


def start_crwarling(k, forpet_hash,shop_name, shop_address):
    print(k, shop_name, shop_address)

	# shop 이름 입력
    try:
        element = driver.find_element_by_xpath('//input[@autofocus="autofocus"]')
        element.clear()
	
    except:
        element = driver.find_element_by_xpath('//input[@class="tactile-searchbox-input"]')
        element.click()

    time.sleep(1)
    search_word = shop_name + ' ' +shop_address[0]
#     search_word = shop_name
    element.send_keys(search_word)
    element.submit()
    time.sleep(1)
    search_button = driver.find_element_by_xpath('//button[@class="searchbox-searchbutton"]')
    search_button.click()
    
    time.sleep(SCROLL_PAUSE_TIME)

    # 키워드 입력 후, dict로 인덱스와 match 여부 받아오기
    select_shop_html = driver.page_source
    shop_select_dict= find_shop_by_name(select_shop_html, shop_name)
    
    # shoh이 여러개인 경우
    if len(shop_select_dict) != 0:
        print(f'shop이 {len(shop_select_dict)}개입니다')
        for index, name in shop_select_dict.items():
            shop_index =  2 * int(index) -1
            
            search_name = name
#             
            time.sleep(3)

            try:
                select_shop = driver.find_element_by_xpath(f'//div[@class = "section-layout section-scrollbox scrollable-y scrollable-show section-layout-flex-vertical"]/div/div[{shop_index}]/div[1]/div[1]')

                select_shop.click()

                time.sleep(SCROLL_PAUSE_TIME)

                html = driver.page_source

                search_name, address, total_score, review_list, score_list, match =get_info(html, shop_name, shop_address)
                print(f'{index}번째 shop:', search_name, address, total_score, match )
            except:
                search_name = shop_name
                address = ''
                total_score = ''
                match = 'not info'
                address = ''
                review_list = ''
                score_list = ''
           
            save_dataframe(forpet_hash, search_name, shop_address, address, total_score, review_list, score_list, match)
        
            time.sleep(SCROLL_PAUSE_TIME)
            driver.back()  
     
    # shop이 1개 인경우
    else:
        print('shop이 1개입니다')
        html = driver.page_source
        search_name, address, total_score, review_list, score_list, match =get_info(html, shop_name, shop_address)
        print(f'shop 1개, {search_name}, {address}, {match} ')
        
        save_dataframe(forpet_hash, search_name, shop_address, address, total_score, review_list, score_list, match)
    # driver.back()  

# 여러개의  shop 목록에서 주소로 찾기
def find_shop_by_name(select_shop_html, shop_name):
    soup = BeautifulSoup(select_shop_html, 'html.parser')
#     print(select_shop_html)
    all_shop_name = soup.find_all('div', attrs = {'class': "section-result-title-container"} )
    
    shop_select_dict = {}
    for i, shop in enumerate(all_shop_name):
        include_word = ['동물', '펫', '애견', 'dot','cat','도그','캣','pet','야옹','멍멍']
        name_include_word = sum([ word in shop.text  for word in include_word]) 
        
        # 이름이 같은 경우
        if shop_name == shop.text :
            shop_select_dict[str(i+1)] = [shop.text, 'same_name']  
        # 이름이 비슷한 경우
        elif name_include_word >= 1:
            shop_select_dict[str(i+1)] = [shop.text,'simiral_name']
        else:
            pass
#     print(shop_select_dict)
    return shop_select_dict

# 주소와 total 별점 가져오기
def get_totalScore(html,shop_name, shop_address):
    
    
    soup = BeautifulSoup(html, 'html.parser')

    time.sleep(SCROLL_PAUSE_TIME)
    infos =soup.find_all('span',attrs = {'class': "section-info-text"} )
    time.sleep(SCROLL_PAUSE_TIME)
    
    # 검색 결과가 있는 경우
    try: 
        search_name = soup.find_all('div', attrs = {'class':'section-hero-header-title-description' })[0].text.replace(' ','')
        if shop_name in search_name:
            search_name = shop_name
        else:
            p = re.compile("[가-힣]")
            search_name = ''.join(p.findall(search_name)).replace('주','')
        
        print('serach_name', search_name, 'shop_name', shop_name)
        
        #  shop이름이 일치하는 경우
        if shop_name in search_name:
            # shop 정보가 없는 경우
            if len(infos)== 0:
                total_score = ''
                match = 'not info'
                address = ''

                return address, total_score
            # shop 정보가 있는 경우    
            else:
                address =infos[0].text

                gu = shop_address[0] in address
                dong = shop_address[1] in address
                bungi = shop_address[2] in address


                if (gu and dong and bungi) or (dong and bungi):
                    match = 'match_all'
                elif (gu and dong) or dong:
                    match = 'match_dong'
                elif gu:
                    match = 'match_gu'
                else:
                    match = 'not_match' 
                    
                    
                    
        #shop이름이 다른 경우
        else:
            address =infos[0].text
            match = 'x'


        total_score = soup.find_all('div',attrs = {'class': "gm2-display-2"} )

        if len(total_score)!=0:
            total_score = total_score[0].text
        else:
            total_score = 0
    
    # 검색 결과가 없는 경우
    except:
        total_score = ''
        match = 'not info'
        address = ''
        search_name = shop_name
    
    return search_name, address, total_score, match

def save_dataframe(forpet_hash, search_name, shop_address, address, total_score, review_list, score_list, match):
    
    # shop 정보가 없는 경우
    if address == '':
        not_info_table_insert(not_info_table, forpet_hash, search_name, match)
    
    # shop 정보가 있는 경우
    else:
        # match 여부에 따라
        if match == 'match_all':
            table_total = match_total_table
            table_review = match_review_table

        elif match == 'x':
            table_total = x_total_table
            table_review = x_review_table

        # shop 이름만 같은 경우, match = match_dong, match_gu, not_match
        else:    
            table_total = not_match_total_table
            table_review = not_match_review_table

        total_table_insert(table_total, forpet_hash, search_name, shop_address, address, total_score, review_list, match)
        review_table_insert(table_review, forpet_hash, search_name, shop_address, address, review_list, score_list, match)   
	

def total_table_insert(total_table, forpet_hash, search_name, shop_address, address, total_score, review_list, match):
    if len(total_table[total_table['address']== address]) == 0:
        # shop 정보가 없고, total_sclre가 없는 경우
        if total_score == '':
            total_table.loc[len(total_table)+1] = [forpet_hash, search_name, shop_address,  address, np.nan, np.nan, match]
        # shop 정보가 있고, total_score가 있는 경우
        elif total_score == 0:
            total_table.loc[len(total_table)+1] = [forpet_hash, search_name, shop_address, address, 0, 0, match]

        #total score이 없는 경우
        else:
            total_table.loc[len(total_table)+1] = [forpet_hash, search_name, shop_address, address,total_score, len(review_list), match]
        print(f'total_table: {search_name}, {address} 등록완료')
    else:
        print(f'total_table: {search_name}, {address} 이미 있음')
    return total_table

def review_table_insert(review_table, forpet_hash, search_name, shop_address, address, review_list, score_list, match):
    if len(review_table[review_table['address']== address]) == 0:
        # shop 정보가 없고, total_sclre가 없는 경우
        if review_list == '':
            review_table.loc[len(review_table)+1] = [forpet_hash, search_name, shop_address, address, 1,  np.nan, np.nan, match]
            print(f'review_table: {search_name}, {address} 등록완료')

        # shop 정보가 있고, total_score가 있는 경우
        elif review_list == 0:
            review_table.loc[len(review_table)+1] = [forpet_hash, search_name, shop_address, address, 1, 0, 0, match]
            print(f'review_table: {search_name}, {address} 등록완료')

        #total score이 없는 경우
        else:
            for i, (review, score, match) in enumerate(zip(review_list, score_list, match)):
                review_table.loc[i+1+len(review_table)] = [forpet_hash, search_name, shop_address, address, i, review, score, match]
            print(f'review_table: {search_name}, {address}, {len(review_list)} 등록완료')
    else:
        print(f'review_table: {search_name}, {address} 이미 있음')

    return review_table


def not_info_table_insert(not_info_table, forpet_hash, shop_name, match):
    not_info_table.loc[1+len(not_info_table)] = [forpet_hash, shop_name, match]
    print(f'not_info_table: {shop_name} 등록완료')
    return not_info_table

	


if __name__=='__main__':
	ordinary_table = pd.read_csv('./data/mysql_forpet_shop.csv', index_col = 0)

    # table
	match_total_table = pd.read_csv('./data/match_total_table.csv', index_col = 0)
	not_match_total_table = pd.read_csv('./data/not_match_total_table.csv', index_col = 0)
	x_total_table = pd.read_csv('./data/x_total_table.csv', index_col = 0)
	not_match_review_table= pd.read_csv('./data/not_match_review_table.csv', index_col = 0)
	match_review_table = pd.read_csv('./data/match_review_table.csv', index_col = 0)
	x_review_table = pd.read_csv('./data/x_review_table.csv', index_col = 0)
	not_info_table = pd.read_csv('./data/not_info_table.csv', index_col = 0)

	SCROLL_PAUSE_TIME = 2

	driver = webdriver.Chrome('chromedriver.exe')
	driver.get("http://www.google.com")
	time.sleep(SCROLL_PAUSE_TIME)
	element = driver.find_element_by_name('q')
	element.clear()
	element.send_keys('google map')
	element.submit()
	time.sleep(SCROLL_PAUSE_TIME)
	element = driver.find_element_by_xpath('//h3[@class="LC20lb DKV0Md"]')
	element.click()

	start_row = 2266
	for k in range(start_row, len(ordinary_table)):
			forpet_hash, address_name, place_name= ordinary_table.loc[k] 
	
			shop_address =address_name.split(' ')[1:]
			shop_name = place_name.replace(' ','')
			start_crwarling(k, forpet_hash, shop_name, shop_address)
			print('\n')
			driver.back()

	if k % 100 == 0:
		match_total_table.to_csv('./data/match_total_table.csv')
		not_match_total_table.to_csv('./data/not_match_total_table.csv')
		match_review_table.to_csv('./data/match_review_table.csv')
		not_match_review_table.to_csv('./data/not_match_review_table.csv')
		x_total_table.to_csv('./data/x_total_table.csv')
		x_review_table.to_csv('./data/x_review_table.csv')
		not_info_table.to_csv('./data/not_info_table.csv')  

    
	