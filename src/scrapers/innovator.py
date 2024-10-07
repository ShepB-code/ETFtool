import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import pandas as pd
import time

try:
    # This will work when running individual scrapers
    from global_constants import *
    from helper_funcs import *
except ImportError:
    # This will work when running through etf_scraper.py
    from .global_constants import *
    from .helper_funcs import *

def Scrape_Innovator(driver):
    print("Scraping Innovator ETFs...")

    # define url and any downloadable file names
    etf_url = "https://www.innovatoretfs.com/define/etfs/#allproducts"
    csv_name = "DefinedOutcomeProductTable.csv"

    try:
        driver.get(etf_url)

        # find csv element and download csv
        download_button = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.ID, "BodyPlaceHolder_DOSGrid1_ExportLinkButton")))
        driver.execute_script("arguments[0].click();", download_button)

        # wait for file to download
        download_directory = os.getcwd()
        start_time = time.time()
        while not os.path.exists(f'{download_directory}/{csv_name}'):
            if time.time() - start_time > EXCEL_DOWNLOAD_TIMEOUT:
                raise TimeoutError("Innovator file did not download properly")
            print("Waiting for file to download...")
            sleep(1)

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
            remaining_outcome_period = int(
                row['Remaining Outcome Period (Days)'])
            starting_cap = row['Starting Cap'].strip('%')

            if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(starting_cap) and remaining_outcome_period != 0:
                all_etf_dict[ticker] = {}
                all_etf_dict[ticker]['remaining_cap'] = float(
                    remaining_cap) / 100  # convert to percent
                all_etf_dict[ticker]['remaining_buffer'] = float(
                    remaining_buffer) / 100
                all_etf_dict[ticker]['downside_before_buffer'] = float(
                    downside_before_buffer) / 100
                all_etf_dict[ticker]['remaining_outcome_period'] = remaining_outcome_period
                all_etf_dict[ticker]['starting_cap'] = float(
                    starting_cap) / 100

        return all_etf_dict
    except Exception as e:
        print(f'Innovator exited with an error: {e}')
    finally:
        driver.quit()
