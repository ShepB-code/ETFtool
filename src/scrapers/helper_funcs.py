import os
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from datetime import datetime


def parse_date(date_str):
    try:
        # Try parsing with '%m/%d/%y' format (2-digit year)
        return datetime.strptime(date_str, '%m/%d/%y')
    except ValueError:
        try:
            # If that fails, try '%m/%d/%Y' format (4-digit year)
            return datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError:
            # If both fail, raise an error
            raise ValueError(f"Unable to parse date string: {date_str}")


def calculate_reset_schedule(date_str1, date_str2, date_format='%m/%d/%Y'):
    date1 = parse_date(date_str1)
    date2 = parse_date(date_str2)

    # Calculate the days in between
    num_days = (date2 - date1).days

    if num_days <= 95:
        return 'Quarterly'
    elif num_days <= 196:
        return 'Semi-Annual'
    else:
        return 'Annual'


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
    chrome_options = uc.ChromeOptions()

    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-css')
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'--user-agent={ua}')

    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}

    download_directory = os.getcwd()
    chrome_prefs["download.default_directory"] = download_directory
    chrome_prefs["download.prompt_for_download"] = False
    chrome_prefs["download.directory_upgrade"] = True
    chrome_prefs["safebrowsing.enabled"] = True

    return chrome_options
