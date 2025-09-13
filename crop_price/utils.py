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


def fetch_agri_data(state, commodity, market):
    initial_url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(initial_url)

    # Select Commodity
    dropdown = Select(driver.find_element("id", 'ddlCommodity'))
    dropdown.select_by_visible_text(commodity)

    # Select State
    dropdown = Select(driver.find_element("id", 'ddlState'))
    dropdown.select_by_visible_text(state)

    # Set Date (7 days ago)
    today = datetime.now()
    desired_date = today - timedelta(days=7)
    date_input = driver.find_element(By.ID, "txtDate")
    date_input.clear()
    date_input.send_keys(desired_date.strftime('%d-%b-%Y'))

    # Click Search
    driver.find_element("id", 'btnGo').click()
    time.sleep(3)

    # Select Market
    dropdown = Select(driver.find_element("id", 'ddlMarket'))
    dropdown.select_by_visible_text(market)

    # Click Search again
    driver.find_element("id", 'btnGo').click()
    time.sleep(2)

    # Wait for table
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'cphBody_GridPriceData'))
    )

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    data_list = []

    table_rows = soup.find('table', id='cphBody_GridPriceData').find('tbody').find_all('tr')
    for row in table_rows:
        cols = [col.text.strip() for col in row.find_all('td')]
        if len(cols) >= 10:
            d = {
                "s_no": cols[0],
                "city": cols[1],
                "commodity": cols[3],
                "min_Price": cols[6],
                "max_Price": cols[7],
                "modal_Price": cols[8],
                "date": cols[9]
            }
            data_list.append(d)

    driver.quit()
    return data_list
