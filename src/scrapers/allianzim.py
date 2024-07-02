import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import pandas as pd
import time
from global_constants import *
from helper_funcs import *


def Scrape_Allianzim(driver):
    print("Scraping Allianzim ETFs...")

    # define url and any downloadable file names
    etf_url = "https://www.allianzim.com/product-table/"
    csv_name = "Allianz-ETFs.csv"
    try:
        driver.get(etf_url)

        # find csv element and download csv
        csv_download_element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "chart-download")))

        driver.execute_script(
            "arguments[0].scrollIntoView();", csv_download_element)
        driver.execute_script("arguments[0].click();", csv_download_element)

        download_directory = os.getcwd()

        # wait for file to download
        start_time = time.time()
        while not os.path.exists(f'{download_directory}/{csv_name}'):
            if time.time() - start_time > EXCEL_DOWNLOAD_TIMEOUT:
                raise TimeoutError("Allianzim file did not download properly")
            print("Waiting for file to download...")
            sleep(1)

        # load csv into a pandas dataframe and skip first row (date)
        df = pd.read_csv(csv_name)
        df = df.dropna(subset=['Starting Cap Net', 'Current Cap Net', 'Starting Buffer Net',
                       'Current Buffer Net', 'Current Downside Before Buffer Net'])

        # remove excel files
        os.remove(f'{download_directory}/{csv_name}')

        print(f"Processing: {csv_name}")
        all_etf_dict = {}
        for _, row in df.iterrows():
            ticker = row['Ticker_Start Date'].upper().split('_')[0]

            if ticker in EXCLUSIONS:
                print(f'Excluded: {ticker}')
                continue

            remaining_cap = float(row['Starting Cap Net'].strip(
                '%')) - float(row['Current Cap Net'].strip('%'))
            remaining_buffer = float(row['Starting Buffer Net'].strip(
                '%')) - float(row['Current Buffer Net'].strip('%'))
            downside_before_buffer = row['Current Downside Before Buffer Net'].strip(
                '%')
            remaining_outcome_period = int(
                row['Remaining Outcome Period'].split(" ")[0])
            starting_cap = row['Starting Cap Net'].strip('%')

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
        print(f'Allianzim exited with an error: {e}')
    finally:
        driver.quit()


if __name__ == "__main__":
    driver = uc.Chrome(options=set_chrome_options())

    allianzim_res = Scrape_Allianzim(driver)

    print(allianzim_res)
