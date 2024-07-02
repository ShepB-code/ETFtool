from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from global_constants import *
from helper_funcs import *


def scrape_pacer_etf(driver, handle, ticker):
    if ticker in EXCLUSIONS:
        print(f'Excluded: {ticker}')
        return None

    print(f"Scraping: {ticker}")

    driver.switch_to.window(handle)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body")))

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # find current value table for specified ETF
    divs = soup.findAll('div', {'class': 'panel panel-default'})
    current_value_div = [div for div in divs if div.find('div', {'class': 'panel-header'}) != None and div.find(
        'div', {'class': 'panel-header'}).find('h2').text == "Current Values"]
    outcome_period_div = [div for div in divs if div.find('div', {'class': 'panel-header'}) != None and div.find(
        'div', {'class': 'panel-header'}).find('h2').text == "Outcome Period Values"]

    # if table found, then grab data and store it
    if len(current_value_div) == 1 and len(outcome_period_div) == 1:
        current_value_table = current_value_div[0].find('table')
        outcome_period_table = outcome_period_div[0].find('table')

        current_value_tds = current_value_table.findAll('td')
        outcome_period_tds = outcome_period_table.findAll('td')

        remaining_cap = current_value_tds[4].text.split('/')[1].strip('%')
        remaining_buffer = current_value_tds[5].text.split('/')[1].strip('%')
        downside_before_buffer = current_value_tds[6].text.split(
            '/')[1].strip('%')
        remaining_outcome_period = int(current_value_tds[7].text.split(' ')[0])
        starting_cap = outcome_period_tds[3].text.strip('%')

        outcome_period = outcome_period_tds[2].text.replace(" ", "").split('-')

        reset_period = calculate_reset_schedule(
            outcome_period[0], outcome_period[1], date_format='%m/%d/%y'
        )

        # make sure values won't mess up future calculations
        if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(starting_cap) and remaining_outcome_period != 0:
            result = {
                'remaining_cap': float(remaining_cap) / 100,
                'remaining_buffer': float(remaining_buffer) / 100,
                'downside_before_buffer': float(downside_before_buffer) / 100,
                'remaining_outcome_period': remaining_outcome_period,
                'starting_cap': float(starting_cap) / 100,
                'reset': reset_period
            }
            return result
    return None


def Scrape_Pacer(driver):
    print("Scraping Pacer ETFs...")
    etf_url = "https://www.paceretfs.com/products/structured-outcome-strategies"

    # Visit the page
    try:
        driver.get(etf_url)

        # allow contents to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'swan-list')))

        # get the page source after JavaScript has executed
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # find main table and grab each etf ticker from it
        table_body = soup.find('tbody', {'id': 'swan-list'})
        main_page_trs = table_body.findAll('tr')
        etf_tickers = [main_page_row.find(
            'th').text for main_page_row in main_page_trs]
        tab_map = {}
        for ticker in etf_tickers:

            ticker = ticker.lower()
            url = f"https://www.paceretfs.com/products/structured-outcome-strategies/{ticker}"

            # open a new tab and visit page
            driver.switch_to.new_window('tab')
            driver.get(url)

            # map page to correct page handle
            tab_map[ticker] = driver.current_window_handle

        # visit all pages and scrape data
        results = []
        for ticker, handle in tab_map.items():
            data = scrape_pacer_etf(driver, handle, ticker)

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
        print(f'Pacer exited with an error: {e}')
    finally:
        driver.quit()


if __name__ == "__main__":
    driver = uc.Chrome(options=set_chrome_options())

    pacer_res = Scrape_Pacer(driver)

    print(pacer_res)
