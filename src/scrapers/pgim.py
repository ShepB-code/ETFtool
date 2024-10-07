from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import json

try:
    # This will work when running individual scrapers
    from global_constants import *
    from helper_funcs import *
except ImportError:
    # This will work when running through etf_scraper.py
    from .global_constants import *
    from .helper_funcs import *

def scrape_pgim_etf(driver, handle, ticker):
    if ticker in EXCLUSIONS:
        print(f'Excluded: {ticker}')
        return None

    print(f'Scraping: {ticker}')

    driver.switch_to.window(handle)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body")))

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'tertiary')))

    soup = BeautifulSoup(driver.page_source, "html.parser")

    try:
        # get overview table to fetch starting cap
        overview_table = soup.findAll('tbody', {'class': 'tertiary'})[0]
        overview_table_trs = [tr for tr in overview_table.findAll('tr')]

        # date from overview table (key facts)
        reference_asset = overview_table_trs[2].findAll('td')[1].text.strip()
        net_expense_ratio = overview_table_trs[4].findAll('td')[1].text
        outcome_period_start = overview_table_trs[5].findAll('td')[
            1].text.replace(" ", "")
        outcome_period_end = overview_table_trs[6].findAll(
            'td')[1].text.replace(" ", "")
        reset_period = calculate_reset_schedule(
            outcome_period_start, outcome_period_end)
        starting_cap_net = overview_table_trs[7].findAll('td')[
            1].text.split('/')[1]

        # get outcome period details table for remaining data
        outcome_table = soup.findAll('table', {'id': 'notStickyHead '})[0]
        outcome_table_trs = [tr for tr in outcome_table.findAll('tr')]

        # remaining cap
        remaining_cap = outcome_table_trs[4].findAll(
            'td')[2].text.split('/')[1]

        # remaining buffer
        remaining_buffer = outcome_table_trs[5].findAll('td')[
            2].text.split('/')[1]

        # downside before buffer
        downside_before_buffer = outcome_table_trs[6].findAll('td')[
            2].text.split('/')[1]

        # remaining outcome period
        remaining_outcome_period = outcome_table_trs[7].findAll('td')[
            2].text

        # make sure values won't mess up future calculations
        if is_numeric_and_not_zero(remaining_cap) and is_numeric_and_not_zero(remaining_buffer) and is_numeric_and_not_zero(downside_before_buffer) and is_numeric_and_not_zero(starting_cap_net) and is_numeric_and_not_zero(remaining_outcome_period) and is_numeric_and_not_zero(net_expense_ratio):
            result = {
                'remaining_cap': float(remaining_cap) / 100,
                'remaining_buffer': float(remaining_buffer) / 100,
                'downside_before_buffer': float(downside_before_buffer) / 100,
                'remaining_outcome_period': int(remaining_outcome_period),
                'starting_cap': float(starting_cap_net) / 100,
                'expense_ratio': float(net_expense_ratio) / 100,
                'reference_asset': reference_asset,
                'reset': reset_period
            }
            return result

    except ValueError as e:
        print(f'{ticker} hit value error: {e}')

    return None


def Scrape_PGIM(driver):
    print("Scraping PGIM ETFs...")
    etf_url = "https://www.pgim.com/investments/etf-buffer-performance"

    # Load the page
    try:
        driver.get(etf_url)
        sleep(4)

        # agree and proceed button
        agree_proceed_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "attestationSubmitButton")))
        agree_proceed_button.click()

        # wait for ETF table to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'notStickyHead')))

        # get the page source after JavaScript has executed
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # find main table and grab each etf ticker from it
        table_body = soup.find('table', {'id': 'notStickyHead'})
        table_trs = table_body.findAll('tr')
        table_tds = [row.findAll('td') for row in table_trs]
        etf_tickers = [td[0].text for td in table_tds if len(td) > 0]
        etf_names = [td[1].text for td in table_tds if len(td) > 0]

        # each ETF page is not represented by the ticker, but the entire name delimeted by '-'
        formated_etf_names = [name.replace('.', '').replace(
            ' ', '-').replace('---', '-').lower() for name in etf_names]

        tab_map = {}
        for etf_name, ticker in zip(formated_etf_names, etf_tickers):
            url = f'https://www.pgim.com/investments/etfs/{etf_name}'

            # open a new tab and visit page
            driver.switch_to.new_window('tab')
            driver.get(url)

            # map page to correct page handle
            tab_map[ticker] = driver.current_window_handle

        # visit all pages and scrape data
        results = []
        for ticker, handle in tab_map.items():
            ticker = ticker.upper()
            data = scrape_pgim_etf(driver, handle, ticker)

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
        print(f'PGIM exited with an error: {e}')
    finally:
        driver.quit()


if __name__ == "__main__":
    driver = uc.Chrome(options=set_chrome_options())

    pgim_res = Scrape_PGIM(driver)

    with open("pgim_scrape.json", 'w') as json_file:
        json_file.write(json.dumps(pgim_res, indent=2))
