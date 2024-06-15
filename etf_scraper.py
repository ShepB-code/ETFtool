import os
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import threading
import multiprocessing
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from time import sleep
import pandas as pd

EXCLUSIONS = ['BALT', 'ZALT', 'EALT', 'TJUL']

def is_numeric_and_not_zero(num):
    try:
        fnum = float(num)
        return fnum != 0
    except ValueError:
        return False

def set_chrome_options() -> Options:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}

    download_directory = os.getcwd()
    chrome_prefs["download.default_directory"] = download_directory
    chrome_prefs["download.prompt_for_download"] = False
    chrome_prefs["download.directory_upgrade"] = True
    chrome_prefs["safebrowsing.enabled"] = True
   
    return chrome_options

def first_trust():
    print("Scraping First Trust ETFs...")

    # define needed etf endpoints
    etf_url = "https://www.ftportfolios.com/Retail/etf/targetoutcomefundlist.aspx"
    etf_target_outcomes_url = "https://www.ftportfolios.com/Retail/etf/targetoutcomebasicslist.aspx"
    main_excel_name = "TargetOutcomeFundList.xlsx"
    target_outcomes_excel_name = "TargetOutcomeStartingCapsAndBuffers.xlsx"
    

    driver = webdriver.Chrome(options=set_chrome_options())

    # open up first page
    driver.get(etf_url)

    # open up new tab and switch to it
    driver.execute_script("window.open('', '_blank');")
    driver.switch_to.window(driver.window_handles[1])

    # open up second page
    driver.get(etf_target_outcomes_url)

    # click on element in second tab
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_TargetOutcomeBasicsList_lnkDownloadToExcel"))).click()

    # switch back to first tab
    driver.switch_to.window(driver.window_handles[0])
    
    # click on element in first tab
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_targetoutcomeretail_lnkDownloadToExcel"))).click()
    
    download_directory = os.getcwd()
    # wait for file to download
    while not os.path.exists(f'{download_directory}/{main_excel_name}') or not os.path.exists(f'{download_directory}/{target_outcomes_excel_name}'):
        print("Waiting for file to download...")
        sleep(1)

    driver.quit()

    df = pd.read_excel(main_excel_name, skiprows=2)
    df_target_outcomes = pd.read_excel(target_outcomes_excel_name, skiprows=2)

    # last index has text, not data
    df = df.drop(df.index[-1])
    df_target_outcomes = df_target_outcomes.drop(df_target_outcomes.index[-1])

    # delete excel files
    os.remove(f'{download_directory}/{main_excel_name}')
    os.remove(f'{download_directory}/{target_outcomes_excel_name}')


    # process main data frame 
    all_etf_dict = {}
    skipped_etfs = set()
    for index, row in df.iterrows():
        ticker = row['Ticker'].upper()

        if ticker in EXCLUSIONS:
            print(f'Excluded: {ticker}')
            continue

        # values come as numbers in this excel document
        remaining_cap = row['Remaining Cap Net']
        remaining_buffer = row['Remaining Buffer Net']
        downside_before_buffer = row['Downside Before Buffer Net']
        remaining_outcome_period = row['Remaining Outcome Period (days)']
        #starting_cap = row['Starting Cap'].strip('%')

        if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(remaining_outcome_period):
            all_etf_dict[ticker] = {}
            all_etf_dict[ticker]['remaining_cap'] = remaining_cap
            all_etf_dict[ticker]['remaining_buffer'] = remaining_buffer
            all_etf_dict[ticker]['downside_before_buffer'] = downside_before_buffer
            all_etf_dict[ticker]['remaining_outcome_period'] = int(remaining_outcome_period)
        else:
            skipped_etfs.add(ticker)
    # process target outcomes dataframe
    for index, row in df_target_outcomes.iterrows():
        ticker = row['Ticker'].upper()

        if ticker in EXCLUSIONS:
            print(f'Excluded: {ticker}')
            continue


        starting_cap = row['Starting Cap']

        # print(f'Name: {ticker}\n\tValues: starting_cap_net: {starting_cap}, remaining_cap: {remaining_cap}, remaining_buffer: {remaining_buffer}, downside_before_buffer: {downside_before_buffer}, remaining_period: {remaining_outcome_period}')

        if is_numeric_and_not_zero(starting_cap) and ticker not in skipped_etfs:
            all_etf_dict[ticker]['starting_cap'] = starting_cap

    print("Finished...")
    return all_etf_dict 

def innovator():
    print("Scraping Innovator ETFs...")

    # define url and any downloadable file names
    etf_url = "https://www.innovatoretfs.com/define/etfs/#allproducts"
    csv_name = "DefinedOutcomeProductTable.csv"

    driver = webdriver.Chrome(options=set_chrome_options())
    driver.get(etf_url)

    # find csv element and download csv
    download_button = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "BodyPlaceHolder_DOSGrid1_ExportLinkButton")))
    driver.execute_script("arguments[0].click();", download_button)

    # wait for file to download
    download_directory = os.getcwd()
    while not os.path.exists(f'{download_directory}/{csv_name}'):
        print("Waiting for file to download...")
        sleep(1)

    # quit chrome
    driver.quit()

    # load csv into a pandas dataframe and skip first row (date)
    df = pd.read_csv(csv_name, skiprows=1)
    
    # remove excel files
    os.remove(f'{download_directory}/{csv_name}')

    print(f"Processing: {csv_name}")
    all_etf_dict = {}
    for _, row in df.iterrows():
        ticker = row['Ticker'].upper()
        
        if ticker in EXCLUSIONS:
            print(f'Excluded: {ticker}')
            continue 

        remaining_cap = row['Remaining Cap'].strip('%')
        remaining_buffer = row['Remaining Buffer'].strip('%')
        downside_before_buffer = row['Downside Before Buffer'].strip('%')
        remaining_outcome_period = int(row['Remaining Outcome Period (Days)'])
        starting_cap = row['Starting Cap'].strip('%')

        # print(f'Name: {ticker}\n\tValues: starting_cap_net: {starting_cap}, remaining_cap: {remaining_cap}, remaining_buffer: {remaining_buffer}, downside_before_buffer: {downside_before_buffer}, remaining_period: {remaining_outcome_period}')

        if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(starting_cap) and remaining_outcome_period != 0:
            all_etf_dict[ticker] = {}
            all_etf_dict[ticker]['remaining_cap'] = float(remaining_cap) / 100 # convert to percent
            all_etf_dict[ticker]['remaining_buffer'] = float(remaining_buffer) / 100 
            all_etf_dict[ticker]['downside_before_buffer'] = float(downside_before_buffer) / 100
            all_etf_dict[ticker]['remaining_outcome_period'] = remaining_outcome_period
            all_etf_dict[ticker]['starting_cap'] = float(starting_cap) / 100

    return all_etf_dict 


def allianzim():
    print("Scraping Allianzim ETFs...")

    # define url and any downloadable file names
    etf_url = "https://www.allianzim.com/product-table/"
    csv_name = "Allianz-ETFs.csv"

    driver = webdriver.Chrome(options=set_chrome_options())
    driver.get(etf_url)

    # find csv element and download csv
    csv_download_element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "chart-download")))

    driver.execute_script("arguments[0].scrollIntoView();", csv_download_element)
    driver.execute_script("arguments[0].click();", csv_download_element)

    download_directory = os.getcwd()
    # wait for file to download
    while not os.path.exists(f'{download_directory}/{csv_name}'):
        print("Waiting for file to download...")
        sleep(1)

    # quit chrome
    driver.quit()

    # load csv into a pandas dataframe and skip first row (date)
    df = pd.read_csv(csv_name)
    df = df.dropna(subset=['Starting Cap Net', 'Current Cap Net', 'Starting Buffer Net', 'Current Buffer Net', 'Current Downside Before Buffer Net'])

    # remove excel files
    os.remove(f'{download_directory}/{csv_name}')

    print(f"Processing: {csv_name}")
    all_etf_dict = {}
    for _, row in df.iterrows():
        ticker = row['Ticker_Start Date'].upper().split('_')[0]
        
        if ticker in EXCLUSIONS:
            print(f'Excluded: {ticker}')
            continue 

        remaining_cap = float(row['Starting Cap Net'].strip('%')) - float(row['Current Cap Net'].strip('%'))
        remaining_buffer = float(row['Starting Buffer Net'].strip('%')) - float(row['Current Buffer Net'].strip('%'))
        downside_before_buffer = row['Current Downside Before Buffer Net'].strip('%')
        remaining_outcome_period = int(row['Remaining Outcome Period'].split(" ")[0])
        starting_cap = row['Starting Cap Net'].strip('%')
        
        # print(f'Name: {ticker}\n\tValues: starting_cap_net: {starting_cap}, remaining_cap: {remaining_cap}, remaining_buffer: {remaining_buffer}, downside_before_buffer: {downside_before_buffer}, remaining_period: {remaining_outcome_period}')

        if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(starting_cap) and remaining_outcome_period != 0:
            all_etf_dict[ticker] = {}
            all_etf_dict[ticker]['remaining_cap'] = float(remaining_cap) / 100 # convert to percent
            all_etf_dict[ticker]['remaining_buffer'] = float(remaining_buffer) / 100 
            all_etf_dict[ticker]['downside_before_buffer'] = float(downside_before_buffer) / 100
            all_etf_dict[ticker]['remaining_outcome_period'] = remaining_outcome_period
            all_etf_dict[ticker]['starting_cap'] = float(starting_cap) / 100

    return all_etf_dict 

def thread_scrape_pacer_etf(ticker):
    if ticker in EXCLUSIONS:
        print(f'Excluded: {ticker}')
        return None
    
    print(f'Scraping: {ticker}')

    etf_url = f'https://www.paceretfs.com/products/structured-outcome-strategies/{ticker}'

    driver = webdriver.Chrome(options=set_chrome_options())
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    driver.get(etf_url)

    #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'panel panel-default')))

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # find current value table for specified ETF
    divs = soup.findAll('div', {'class': 'panel panel-default'})
    current_value_div = [div for div in divs if div.find('div', {'class': 'panel-header'}) != None and div.find('div', {'class': 'panel-header'}).find('h2').text == "Current Values"]
    outcome_period_div = [div for div in divs if div.find('div', {'class': 'panel-header'}) != None and div.find('div', {'class': 'panel-header'}).find('h2').text == "Outcome Period Values"]

    # if table found, then grab data and store it
    if len(current_value_div) == 1 and len(outcome_period_div) == 1:
        current_value_table = current_value_div[0].find('table')
        outcome_period_table = outcome_period_div[0].find('table')

        current_value_tds = current_value_table.findAll('td')
        outcome_period_tds = outcome_period_table.findAll('td')


        remaining_cap = current_value_tds[4].text.split('/')[1].strip('%')
        remaining_buffer = current_value_tds[5].text.split('/')[1].strip('%')
        downside_before_buffer = current_value_tds[6].text.split('/')[1].strip('%')
        remaining_outcome_period = int(current_value_tds[7].text.split(' ')[0])
        starting_cap = outcome_period_tds[3].text.strip('%')


        # print(f'Name: {ticker}\n\tValues: starting_cap_net: {starting_cap}, remaining_cap: {remaining_cap}, remaining_buffer: {remaining_buffer}, downside_before_buffer: {downside_before_buffer}, remaining_period: {remaining_outcome_period}')

        # make sure values won't mess up future calculations
        if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(starting_cap) and remaining_outcome_period != 0:
            result = {
                'remaining_cap': float(remaining_cap) / 100,
                'remaining_buffer': float(remaining_buffer) / 100,
                'downside_before_buffer': float(downside_before_buffer) / 100,
                'remaining_outcome_period': remaining_outcome_period,
                'starting_cap': float(starting_cap) / 100
            }
            return ticker, result
    return None

    
def pacer():
    print("Scraping Pacer ETFs")
    etf_url = "https://www.paceretfs.com/products/structured-outcome-strategies"

    # Create a WebDriver instance with headless Chrome

    driver = webdriver.Chrome(options=set_chrome_options())

    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    # Load the page
    driver.get(etf_url)
    sleep(10)
 
    # allow contents to load
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'swan-list')))

    # get the page source after JavaScript has executed
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # find main table and grab each etf ticker from it
    table_body = soup.find('tbody', {'id': 'swan-list'})
    main_page_trs = table_body.findAll('tr')
    etf_tickers = [main_page_row.find('th').text for main_page_row in main_page_trs]

    # scrape each etf page indiviually 
    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        results = list(executor.map(thread_scrape_pacer_etf, etf_tickers))

    # store all results
    all_etf_dict = {}
    for result in results:
        if result is not None:
            ticker, data = result
            all_etf_dict[ticker] = data
    
    print('Finished...')
    return all_etf_dict


def thread_scrape_pgim_etf(ticker, etf_name):
    if etf_name in EXCLUSIONS:
        print(f'Excluded: {etf_name}')
        return None
    
    print(f'Scraping: {etf_name}')

    etf_url = f'https://www.pgim.com/investments/etfs/{etf_name}'

    driver = webdriver.Chrome(options=set_chrome_options())
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    driver.get(etf_url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'tertiary')))

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    
    try: 
        # get overview table to fetch starting cap
        overview_table = soup.findAll('tbody', {'class': 'tertiary'})[0]
        starting_cap_tr = [tr for tr in overview_table.findAll('tr')][7]
        starting_cap_net = starting_cap_tr.findAll('td')[1].text.split('/')[1]

        # get outcome period details table for remaining data
        outcome_table = soup.findAll('table', {'id': 'notStickyHead '})[0]
        outcome_table_trs = [tr for tr in outcome_table.findAll('tr')]
        
        # remaining cap
        remaining_cap = outcome_table_trs[4].findAll('td')[2].text.split('/')[1]
    
        # remaining buffer
        remaining_buffer = outcome_table_trs[5].findAll('td')[2].text.split('/')[1]
        
        # downside before buffer
        downside_before_buffer = outcome_table_trs[6].findAll('td')[2].text.split('/')[1]

        # remaining outcome period
        remaining_outcome_period = outcome_table_trs[7].findAll('td')[2].text

        # print(f'Name: {ticker}\n\tValues: starting_cap_net: {starting_cap_net}, remaining_cap: {remaining_cap}, remaining_buffer: {remaining_buffer}, downside_before_buffer: {downside_before_buffer}, remaining_period: {remaining_outcome_period}')
         # make sure values won't mess up future calculations
        if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(starting_cap_net) and is_numeric_and_not_zero(remaining_outcome_period):
            result = {
                'remaining_cap': float(remaining_cap) / 100,
                'remaining_buffer': float(remaining_buffer) / 100,
                'downside_before_buffer': float(downside_before_buffer) / 100,
                'remaining_outcome_period': remaining_outcome_period,
                'starting_cap': float(starting_cap_net) / 100
            }
            return ticker, result

    except ValueError as e:
        print(f'{etf_name} hit value error: {e}')
   
    return None

def pgim():
    print("Scraping PGIM ETFs")
    etf_url = "https://www.pgim.com/investments/etf-buffer-performance"

    # Create a WebDriver instance with headless Chrome

    driver = webdriver.Chrome(options=set_chrome_options())

    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    # Load the page
    driver.get(etf_url)
    sleep(4)

    # agree and proceed button
    agree_proceed_button = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "attestationSubmitButton")))
    agree_proceed_button.click()
    #driver.execute_script("arguments[0].click();", agree_proceed_button)
    #WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "attestationSubmitButton"))).click()

    # wait for ETF table to load
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'notStickyHead')))

    # get the page source after JavaScript has executed
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # find main table and grab each etf ticker from it
    table_body = soup.find('table', {'id': 'notStickyHead'})
    table_trs = table_body.findAll('tr')
    table_tds = [row.findAll('td') for row in table_trs]
    etf_tickers = [td[0].text for td in table_tds if len(td) > 0]
    etf_names = [td[1].text for td in table_tds if len(td) > 0]
    

    # each ETF page is not represented by the ticker, but the entire name delimeted by '-' 
    formated_etf_names = [name.replace('.', '').replace(' ', '-').replace('---', '-').lower() for name in etf_names]
    
    # scrape each etf page indiviually 
    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        results = list(executor.map(thread_scrape_pgim_etf, etf_tickers, formated_etf_names))

    # store all results
    all_etf_dict = {}
    for result in results:
        if result is not None:
            ticker, data = result
            all_etf_dict[ticker] = data
    
    print('Finished...')
    return all_etf_dict
    

def scraper_main():
    all_etfs_dict = {}
    
    # Define threads for each function
    first_trust_thread = threading.Thread(target=lambda: all_etfs_dict.update({"First Trust": first_trust()}))
    innovator_thread = threading.Thread(target=lambda: all_etfs_dict.update({"Innovator": innovator()}))
    allianzim_thread = threading.Thread(target=lambda: all_etfs_dict.update({"Allianzim": allianzim()}))
    pacer_thread = threading.Thread(target=lambda: all_etfs_dict.update({"Pacer": pacer()}))
    pgim_thread = threading.Thread(target=lambda: all_etfs_dict.update({"Pgim": pgim()}))

    # Start all threads
    first_trust_thread.start()
    innovator_thread.start()
    allianzim_thread.start()
    pacer_thread.start()
    pgim_thread.start()

    # Wait for all threads to finish
    first_trust_thread.join()
    innovator_thread.join()
    allianzim_thread.join()
    pacer_thread.join()
    pgim_thread.join()


    with open("etf_data.json", 'w') as json_file:
        json_file.write(json.dumps(all_etfs_dict, indent=2))

if __name__ == "__main__":
    scraper_main()