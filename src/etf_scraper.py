import os
import threading
import json
import undetected_chromedriver as uc
from scrapers import allianzim, first_trust, innovator, pacer, pgim
from scrapers.helper_funcs import set_chrome_options


def scraper_main():
    all_etfs_dict = {}

    print("Setting up drivers...")
    first_trust_driver = uc.Chrome(options=set_chrome_options())
    innovator_driver = uc.Chrome(options=set_chrome_options())
    allianzim_driver = uc.Chrome(options=set_chrome_options())
    pacer_driver = uc.Chrome(options=set_chrome_options())
    pgim_driver = uc.Chrome(options=set_chrome_options())

    # Define threads for each function
    print("Setting up threads...")
    first_trust_thread = threading.Thread(target=lambda: all_etfs_dict.update(
        {"First Trust": first_trust.Scrape_First_Trust(first_trust_driver)}))
    innovator_thread = threading.Thread(target=lambda: all_etfs_dict.update(
        {"Innovator": innovator.Scrape_Innovator(innovator_driver)}))
    allianzim_thread = threading.Thread(target=lambda: all_etfs_dict.update(
        {"Allianzim": allianzim.Scrape_Allianzim(allianzim_driver)}))
    pacer_thread = threading.Thread(
        target=lambda: all_etfs_dict.update({"Pacer": pacer.Scrape_Pacer(pacer_driver)}))
    pgim_thread = threading.Thread(
        target=lambda: all_etfs_dict.update({"Pgim": pgim.Scrape_PGIM(pgim_driver)}))

    # Start all threads
    print("Running threads...")
    first_trust_thread.start()
    innovator_thread.start()
    allianzim_thread.start()
    pacer_thread.start()
    pgim_thread.start()

    # # Wait for all threads to finish
    first_trust_thread.join()
    innovator_thread.join()
    allianzim_thread.join()
    pacer_thread.join()
    pgim_thread.join()

    print('Finished...')

    with open("etf_data.json", 'w') as json_file:
        json_file.write(json.dumps(all_etfs_dict, indent=2))


if __name__ == "__main__":
    scraper_main()
