import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta

from .models import crop_price
from datetime import datetime


count_of_process=0


def fetch_agri_data(driver, commodity):

    initial_url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"
    driver.get(initial_url)

    print(" driver initialized for "+count_of_process+" time")


    # Select Commodity
    dropdown = Select(driver.find_element("id", 'ddlCommodity'))
    dropdown.select_by_visible_text(commodity)
    print(" Commodity Selected : ",commodity)

    # Set Date (3 months data)
    today = datetime.now()
    desired_date = today - timedelta(days=90)
    date_input = driver.find_element(By.ID, "txtDate")
    date_input.clear()
    date_input.send_keys(desired_date.strftime('%d-%b-%Y'))

    # Click Search
    btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "btnGo"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(3)

    # Select Market
    '''dropdown = Select(driver.find_element("id", 'ddlMarket'))
    dropdown.select_by_visible_text(market)

    print(" market selected ")'''

    # Click Search again
    
    '''driver.find_element("id", 'btnGo').click()
    time.sleep(2)'''

    driver.implicitly_wait(10)

    # Wait for table
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, 'cphBody_GridPriceData'))
    )

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    data_list = []

    table_rows = soup.find('table', id='cphBody_GridPriceData').find('tbody').find_all('tr')
    count=0
    for row in table_rows:
        cols = [col.text.strip() for col in row.find_all('td')]
        if len(cols) >= 10:
            d = {
                "s_no": cols[0],
                "city": cols[1],
                "market_name":cols[2],
                "commodity": cols[3],
                "variety":cols[4],
                "grade":cols[5],
                "min_Price": cols[6],
                "max_Price": cols[7],
                "modal_Price": cols[8],
                "date": cols[9]
            }
            data_list.append(d)
        
    count_of_process+=1
    print("driver set " + count_of_process + " completed ")
    return data_list
