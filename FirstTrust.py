from bs4 import BeautifulSoup
import requests
import json

def main():

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
    data_dict = {}
    header_names = ['ticker', 'strategy', 'series', 'reference_asset', 'fund_value', 'fund_return', 'reference_asset_value', 'reference_asset_return', 'remaining_cap', 'remaining_buffer', 'downside_before_buffer', 'remaining_outcome_period']
    for i, row in enumerate(ticker_table_rows):
        
        td = row.findAll('td')
        if len(td) == 0: continue

        items = []
        for item in td:

            item_spans = item.findAll('span')

            if item_spans:
                for span in item_spans:
                    span = span.text
                    if '%' in span:
                        span = float(span.strip('%')) / 100
                    elif '$' in span:
                        span = float(span.strip('$'))
                    elif span.isnumeric():
                        span = int(span)
                    items.append(span)
            
        if len(items) == len(header_names) and items[-1] != 0 and isinstance(items[8], float):
            ticker_dict = {}
            for i, data in enumerate(items):
                ticker_dict[header_names[i]] = data

            data_dict[items[0]] = ticker_dict
        
    with open("first_trust_outcome_period_values.json", 'w') as json_file:
        json_file.write(json.dumps(data_dict, indent=2))



if __name__ == "__main__":
    main()