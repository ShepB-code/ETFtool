from flask import Flask, send_file
from etf_scraper import scraper_main
from etf_excel_writer import excel_writer
import os

app = Flask(__name__)

@app.route('/etf_data', methods=['GET'])
def get_etf_data():
    try:
        # scrape all etf data
        scraper_main()

        # write it to excel
        excel_file = excel_writer()

        return send_file(excel_file, as_attachment=True)
        
    except Exception as e:
        return str(e), 500

@app.route('/')
def home():
    return 'Ready to go!'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7070))
    app.run(port=port, debug=True, host='0.0.0.0')

