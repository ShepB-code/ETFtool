from bs4 import BeautifulSoup
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep


def is_numeric(num):
    try:
        fnum = float(num)
        return True
    except ValueError:
        return False


def first_trust():
    print("Scraping First Trust ETFs...")
    etf_url = "https://www.ftportfolios.com/Retail/etf/targetoutcomefundlist.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    page = requests.get(etf_url, headers=headers)    
    soup = BeautifulSoup(page.content, "html.parser")

    # grab main table
    table1 = soup.find('table', {'id': 'Table1'})

    # grab ticker table within main table
    ticker_table = table1.find('table', {'class': 'searchResults small'})

    # get rows
    ticker_table_rows = ticker_table.findAll('tr')

    # gather data, cleanse it, and put it into a json
    all_etf_dict = {}
    for i, row in enumerate(ticker_table_rows):
        
        td = row.findAll('td')
        if len(td) == 0: continue

        # grab ticker, remaining cap, remaining buffer, downside before buffer, remaining outcome period

        ticker = td[0].find('span').text
        remaining_cap = td[6].find('span').text.strip('%')
        remaining_buffer = td[7].find('span').text.strip('%')
        downside_before_buffer = td[8].find('span').text.strip('%')
        remaining_outcome_period = int(td[9].text.split(' ')[0])

        if is_numeric(remaining_cap) and is_numeric(remaining_buffer) and is_numeric(downside_before_buffer) and remaining_outcome_period != 0:
            all_etf_dict[ticker] = {}
            all_etf_dict[ticker]['remaining_cap'] = float(remaining_cap) / 100 # convert to percent
            all_etf_dict[ticker]['remaining_buffer'] = float(remaining_buffer) / 100 
            all_etf_dict[ticker]['downside_before_buffer'] = float(downside_before_buffer) / 100
            all_etf_dict[ticker]['remaining_outcome_period'] = remaining_outcome_period

    print("Finished...")
    return all_etf_dict 

def innovator():
    print("Scraping Innovator ETFs...")
    etf_url = "https://www.innovatoretfs.com/define/etfs/#allproducts"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    page = requests.get(etf_url, headers=headers)    
    soup = BeautifulSoup(page.content, "html.parser")

    table = soup.find('table', {'class': 'DOGrid'})

    ticker_table_rows = table.findAll('tr')

    all_etf_dict = {}
    for i, row in enumerate(ticker_table_rows):

        td = row.findAll('td')
        
        if len(td) == 0: continue # skip header row
        
        # grab ticker, remaining cap, remaining buffer, downside before buffer, remaining outcome period

        ticker = td[0].find('div').text.upper()
        remaining_cap = td[9].text.strip('%')
        remaining_buffer = td[10].text.strip('%')
        downside_before_buffer = td[11].text.strip('%')
        remaining_outcome_period = int(td[12].text.split(' ')[0])

        if is_numeric(remaining_cap) and is_numeric(remaining_buffer) and is_numeric(downside_before_buffer) and remaining_outcome_period != 0:
            all_etf_dict[ticker] = {}
            all_etf_dict[ticker]['remaining_cap'] = float(remaining_cap) / 100 # convert to percent
            all_etf_dict[ticker]['remaining_buffer'] = float(remaining_buffer) / 100 
            all_etf_dict[ticker]['downside_before_buffer'] = float(downside_before_buffer) / 100
            all_etf_dict[ticker]['remaining_outcome_period'] = remaining_outcome_period
   
    print("Finished...")
    return all_etf_dict


def pacer():
    print("Scraping Pacer ETFs")
    etf_url = "https://www.paceretfs.com/products/structured-outcome-strategies"

    # Set up Chrome options for headless mode
    chrome_options = Options()
    #chrome_options.headless = True

    # Create a WebDriver instance with headless Chrome
    driver = webdriver.Chrome(options=chrome_options)

    # Load the page
    driver.get(etf_url)

    # allow contents to load
    sleep(2)
    
    # Get the page source after JavaScript has executed
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.close()

    table_body = soup.find('tbody', {'id': 'swan-list'})

    main_page_trs = table_body.findAll('tr')

    all_etf_dict = {}
    for i, main_page_row in enumerate(main_page_trs):
        main_page_th = main_page_row.find('th')

        # with ticker iterate through each page (new ETF safe)
        ticker = main_page_th.text
        
        # init a new driver for each ETF page
        driver_two = webdriver.Chrome(options=chrome_options)
        driver_two.get(f'{etf_url}/{ticker.lower()}')
        sleep(2)

        soup_two = BeautifulSoup(driver_two.page_source, "html.parser")
        divs = soup_two.findAll('div', {'class': 'panel panel-default'})
        table_div = [div for div in divs if div.find('div', {'class': 'panel-header'}) != None and div.find('div', {'class': 'panel-header'}).find('h2').text == "Current Values"]

        if len(table_div) == 1:
            current_value_table = table_div[0].find('table')

            etf_page_tds = current_value_table.findAll('td')

            remaining_cap = etf_page_tds[4].text.split('/')[1].strip('%')
            remaining_buffer = etf_page_tds[5].text.split('/')[1].strip('%')
            downside_before_buffer = etf_page_tds[6].text.split('/')[1].strip('%')
            remaining_outcome_period = int(etf_page_tds[7].text.split(' ')[0])
        
            if is_numeric(remaining_cap) and is_numeric(remaining_buffer) and is_numeric(downside_before_buffer) and remaining_outcome_period != 0:
                all_etf_dict[ticker] = {}
                all_etf_dict[ticker]['remaining_cap'] = float(remaining_cap) / 100 # convert to percent
                all_etf_dict[ticker]['remaining_buffer'] = float(remaining_buffer) / 100 
                all_etf_dict[ticker]['downside_before_buffer'] = float(downside_before_buffer) / 100
                all_etf_dict[ticker]['remaining_outcome_period'] = remaining_outcome_period

    driver.quit()
    print("Finished...")
    return all_etf_dict

def main():
    all_etfs_dict = {}

    # first_trust_dict = first_trust()
    # all_etfs_dict["First Trust"] = first_trust_dict

    # innovator_dict = innovator()
    # all_etfs_dict["Innovator"] = innovator_dict

    pacer_dict = pacer()
    all_etfs_dict["Pacer"] = pacer_dict


    with open("etf_data.json", 'w') as json_file:
        json_file.write(json.dumps(all_etfs_dict, indent=2))

    



if __name__ == "__main__":
    main()