from flask import Flask, send_file
from etf_scraper import scraper_main
from etf_excel_writer import excel_writer
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

if __name__ == "__main__":
    app.run(debug=True)
