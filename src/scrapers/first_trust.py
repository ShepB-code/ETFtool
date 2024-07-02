import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import pandas as pd
import time
from global_constants import *
from helper_funcs import *


def Scrape_First_Trust(driver):
    print("Scraping First Trust ETFs...")

    # define needed etf endpoints
    etf_url = "https://www.ftportfolios.com/Retail/etf/targetoutcomefundlist.aspx"
    etf_target_outcomes_url = "https://www.ftportfolios.com/Retail/etf/targetoutcomebasicslist.aspx"
    main_excel_name = "TargetOutcomeFundList.xlsx"
    target_outcomes_excel_name = "TargetOutcomeStartingCapsAndBuffers.xlsx"

    try:
        driver.get(etf_url)

        # open up new tab and load new page
        driver.switch_to.new_window('tab')
        driver.get(etf_target_outcomes_url)

        # click on element in second tab
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.ID, "ContentPlaceHolder1_TargetOutcomeBasicsList_lnkDownloadToExcel"))).click()
        driver.close()

        # switch back to first tab
        driver.switch_to.window(driver.window_handles[0])

        # click on element in first tab
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.ID, "ContentPlaceHolder1_targetoutcomeretail_lnkDownloadToExcel"))).click()

        download_directory = os.getcwd()

        # wait for both files to download
        start_time = time.time()
        while not os.path.exists(f'{download_directory}/{main_excel_name}') or not os.path.exists(f'{download_directory}/{target_outcomes_excel_name}'):
            if time.time() - start_time > EXCEL_DOWNLOAD_TIMEOUT:
                raise TimeoutError(
                    "First Trust files did not download properly")
            print("Waiting for file to download...")
            sleep(1)

        df = pd.read_excel(main_excel_name, skiprows=2)
        df_target_outcomes = pd.read_excel(
            target_outcomes_excel_name, skiprows=2)

        # last index has text, not data
        df = df.drop(df.index[-1])
        df_target_outcomes = df_target_outcomes.drop(
            df_target_outcomes.index[-1])

        # delete excel files
        os.remove(f'{download_directory}/{main_excel_name}')
        os.remove(f'{download_directory}/{target_outcomes_excel_name}')

        # process main data frame
        all_etf_dict = {}
        skipped_etfs = set()
        for _, row in df.iterrows():
            ticker = row['Ticker'].upper()

            if ticker in EXCLUSIONS:
                print(f'Excluded: {ticker}')
                continue

            remaining_cap = row['Remaining Cap Net']
            remaining_buffer = row['Remaining Buffer Net']
            downside_before_buffer = row['Downside Before Buffer Net']
            remaining_outcome_period = row['Remaining Outcome Period (days)']

            # calc reset schedule
            start_date = row['Outcome Period Start Date']
            end_date = row['Outcome Period End Date']
            reset_period = calculate_reset_schedule(
                start_date, end_date, date_format='%m/%d/%Y')

            if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(remaining_outcome_period):
                all_etf_dict[ticker] = {}
                all_etf_dict[ticker]['remaining_cap'] = remaining_cap
                all_etf_dict[ticker]['remaining_buffer'] = remaining_buffer
                all_etf_dict[ticker]['downside_before_buffer'] = downside_before_buffer
                all_etf_dict[ticker]['remaining_outcome_period'] = int(
                    remaining_outcome_period)
                all_etf_dict[ticker]['reset'] = reset_period
            else:
                skipped_etfs.add(ticker)

        # process target outcomes dataframe
        for _, row in df_target_outcomes.iterrows():
            ticker = row['Ticker'].upper()

            if ticker in EXCLUSIONS:
                print(f'Excluded: {ticker}')
                continue

            starting_cap = row['Starting Cap']

            if is_numeric_and_not_zero(starting_cap) and ticker not in skipped_etfs:
                all_etf_dict[ticker]['starting_cap'] = starting_cap

        return all_etf_dict

    except Exception as e:
        print(f'First Trust exited with an error: {e}')
    finally:
        driver.quit()


if __name__ == "__main__":
    driver = uc.Chrome(options=set_chrome_options())

    first_trust_res = Scrape_First_Trust(driver)

    print(first_trust_res)
