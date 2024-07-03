import os
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import pandas as pd
import time
from global_constants import *
from helper_funcs import *
import json


def scrape_first_trust_etf(driver, handle, ticker):
    print(f'Scraping: {ticker}')
    try:
        driver.switch_to.window(handle)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body")))

        soup = BeautifulSoup(driver.page_source, "html.parser")

        fund_overview_table = soup.find(
            'table', {'id': 'FundOverview_FundControlContainer_NameValuePairListing'})

        value_tables = soup.findAll('table', {'class': 'fundGrid'})

        outcome_period_table = [table for table in value_tables if table.find('div', {'class': 'silverBox fundControlSeperatorBar'}) and table.find(
            'div', {'class': 'silverBox fundControlSeperatorBar'}).text.strip() == "Outcome Period Values"]
        current_values_table = [table for table in value_tables if table.find('div', {'class': 'silverBox fundControlSeperatorBar'}) and "Current Values" in table.find(
            'div', {'class': 'silverBox fundControlSeperatorBar'}).text]

        if fund_overview_table and len(outcome_period_table) == 1 and len(current_values_table) == 1:
            outcome_period_table = outcome_period_table[0]
            current_values_table = current_values_table[0]
            secondary_outcome_period_table = value_tables[2]  # this is a hack

            # data from "Fund Overview"
            expense_ratio = fund_overview_table.findAll(
                'tr')[13].findAll('td')[1].text.strip('%')

            # data from "Outcome Period Values"
            outcome_period_trs = outcome_period_table.findAll('tr')

            reference_asset_tr = [tr for tr in outcome_period_trs if tr.findAll(
                'td')[0].text.strip() == "Reference Asset"][0]
            reference_asset = map_reference_asset_to_generic(
                reference_asset_tr.findAll('td')[1].text.strip())

            period_tr = [tr for tr in outcome_period_trs if tr.findAll(
                'td')[0].text.strip() == "Outcome Period"][0]
            outcome_periods = period_tr.findAll(
                'td')[1].text.replace(" ", "").split('-')
            reset_period = calculate_reset_schedule(
                outcome_periods[0], outcome_periods[1])

            fund_cap_tr = [tr for tr in outcome_period_trs if tr.findAll(
                'td')[0].text.strip() == "Fund Cap (Net)"][0]
            starting_cap = fund_cap_tr.findAll(
                'td')[1].text.strip().split(" ")[1][1:-1].strip('%')

            # data from Secondary outcome period values
            secondary_outcome_period_trs = secondary_outcome_period_table.findAll(
                'tr')
            buffer_start_tr = [tr for tr in secondary_outcome_period_trs if tr.findAll(
                'td')[0].text.strip() == "Buffer Start % / Reference Asset Value"][0]
            buffer_start = buffer_start_tr.findAll(
                'td')[1].text.replace(" ", "").split('/')[0].strip('%')
            buffer_end_tr = [tr for tr in secondary_outcome_period_trs if tr.findAll(
                'td')[0].text.strip() == "Buffer End % / Reference Asset Value"][0]
            buffer_end = buffer_end_tr.findAll(
                'td')[1].text.replace(" ", "").split('/')[0].strip('%')

            etf_type = f'{str(abs(int(float(buffer_start))))}/{str(abs(int(float(buffer_end))))}'

            # data from "Current Values" (net values)
            current_values_trs = current_values_table.findAll('tr')
            remaining_outcome_period_tr = [tr for tr in current_values_trs if tr.findAll(
                'td')[0].text.strip() == "Remaining Outcome Period"][0]
            remaining_outcome_period = remaining_outcome_period_tr.findAll('td')[
                1].text.split(" ")[0]

            remaining_cap_tr = [tr for tr in current_values_trs if tr.findAll(
                'td')[0].text.strip() == "Remaining Cap (Net)"][0]
            remaining_cap = remaining_cap_tr.findAll(
                'td')[1].text.strip().split(" ")[1][1:-1].strip('%')

            remaining_buffer_tr = [tr for tr in current_values_trs if tr.findAll(
                'td')[0].text.strip() == "Remaining Buffer (Net)"][0]
            remaining_buffer = remaining_buffer_tr.findAll(
                'td')[1].text.strip().split(" ")[1][1:-1].strip('%')

            downside_before_buffer_tr = [tr for tr in current_values_trs if tr.findAll(
                'td')[0].text.strip() == "Downside Before Buffer (Net)"][0]
            downside_before_buffer = downside_before_buffer_tr.findAll(
                'td')[1].text.strip().split(" ")[1][1:-1].strip('%')

            # make sure values won't mess up future calculations
            if is_numeric_and_not_zero(expense_ratio) and is_numeric_and_not_zero(starting_cap) and is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(remaining_outcome_period):
                result = {
                    'remaining_cap': float(remaining_cap) / 100,
                    'remaining_buffer': float(remaining_buffer) / 100,
                    'downside_before_buffer': float(downside_before_buffer) / 100,
                    'remaining_outcome_period': int(remaining_outcome_period),
                    'starting_cap': float(starting_cap) / 100,
                    'expense_ratio': float(expense_ratio) / 100,
                    'reference_asset': reference_asset,
                    'type': etf_type,
                    'reset': reset_period
                }
                return result
        return None
    except Exception as e:
        print(f'{ticker} threw expection: {e}')
        return None


def Scrape_First_Trust(driver):
    print("Scraping First Trust ETFs...")

    # define needed etf endpoints
    etf_url = "https://www.ftportfolios.com/Retail/etf/targetoutcomefundlist.aspx"

    try:
        driver.get(etf_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "Table1")))

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # grab main table
        etf_table = soup.findAll('table', {'class': 'searchResults small'})
        etf_table_a_tags = etf_table[0].findAll('a')  # skip header row

        # go through rows and get tickers
        tickers = []
        for a_tag in etf_table_a_tags:
            ticker = a_tag.text
            # skip pdf a tags and exclusions
            if ticker != "" and ticker not in EXCLUSIONS:
                tickers.append(ticker)

        # open up etf pages
        tab_map = {}
        for ticker in tickers:
            url = f'https://www.ftportfolios.com/Retail/Etf/EtfSummary.aspx?Ticker={ticker}'
            # open a new tab and visit page
            driver.switch_to.new_window('tab')
            driver.get(url)

            # map page to correct page handle
            tab_map[ticker] = driver.current_window_handle

        # visit all pages and scrape data
        results = []
        for ticker, handle in tab_map.items():
            ticker = ticker.upper()
            data = scrape_first_trust_etf(driver, handle, ticker)

            if data:
                results.append((ticker, data))

        # store all results
        all_etf_dict = {}
        for result in results:
            if result is not None:
                ticker, data = result
                all_etf_dict[ticker] = data

        return all_etf_dict

    except Exception as e:
        print(f'First Trust exited with an error: {e}')
    finally:
        driver.quit()


if __name__ == "__main__":
    driver = uc.Chrome(options=set_chrome_options())

    first_trust_res = Scrape_First_Trust(driver)

    with open("first_trust_scrape.json", 'w') as json_file:
        json_file.write(json.dumps(first_trust_res, indent=2))
