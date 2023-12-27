import json
import openpyxl as xl
from datetime import datetime

def excel_writer():
    # open workbook
    wb = xl.Workbook()
    ws = wb.active
    ws.title = "ETFs"

    ws['A1'] = 'Score Rank'
    ws['B1'] = 'Index'
    ws['C1'] = 'Provider'
    ws['D1'] = 'Ticker'
    ws['E1'] = 'Remaining Cap'
    ws['F1'] = 'Remaining Buffer'
    ws['G1'] = 'Downside Before Buffer'
    ws['H1'] = 'Remaining Outcome Period'
    ws['I1'] = 'Starting Cap'
    ws['J1'] = 'Cap Used'
    ws['K1'] = 'Percentage Used'
    ws['L1'] = 'Remaining Percentage'
 
    # get json
    with open('etf_data.json', 'r') as json_file: 
        etf_data = json.load(json_file)
        
        current_cell = 2
        for provider, data in etf_data.items():
            for etf, values in data.items():
                ws.cell(current_cell, 2).value = current_cell - 1
                ws.cell(current_cell, 3).value = provider
                ws.cell(current_cell, 4).value = etf
                ws.cell(current_cell, 5).value = values['remaining_cap']
                ws.cell(current_cell, 6).value = values['remaining_buffer']
                ws.cell(current_cell, 7).value = values['downside_before_buffer']
                ws.cell(current_cell, 8).value = values['remaining_outcome_period']
                ws.cell(current_cell, 9).value = values['starting_cap']
                ws.cell(current_cell, 10).value = f'=I{current_cell} - E{current_cell}'
                ws.cell(current_cell, 11).value = f'=J{current_cell}/I{current_cell}'
                ws.cell(current_cell, 12).value = f'=1-K{current_cell}'

                current_cell += 1
    ws.column_dimensions['H'].bestFit = True

    # write to Calculations Sheet
    ns = wb.create_sheet(title='Calc')

    ns['A1'] = 'Risk/Reward'
    ns.column_dimensions['A'].auto_size = True

    ns['B1'] = 'Period/Time Factor'
    ns.column_dimensions['B'].auto_size = True

    ns['C1'] = 'Rank'
    ns.column_dimensions['C'].auto_size = True

    ns['D1'] = 'Downside Before Buffer / Buffer'
    ns.column_dimensions['D'].auto_size = True

    ns['E1'] = 'Score'
    ns.column_dimensions['E'].auto_size = True

    ns['F1'] = 'Time Factor'
    ns['F2'] = 100
    ns.column_dimensions['F'].auto_size = True

    ns['G1'] = "Raw Value Factor"
    ns['G2'] = 2
    ns.column_dimensions['G'].auto_size = True

    total_written = current_cell - 2

    for i in range(total_written):
        ns.cell(i + 2, 1).value = f'=ETFs!E{i+2}/ETFs!G{i+2}' # A column
        ns.cell(i + 2, 2).value = f'=$F$2/ETFs!H{i+2}' # B Column
        ns.cell(i + 2, 3).value = f'=A{i+2}*B{i+2}' # C Column
        ns.cell(i + 2, 4).value = f'=ETFs!G{i+2}/ETFs!F{i+2}' # D column
        ns.cell(i + 2, 5).value = f'=C{i+2}+D{i+2}'

    # cap_used % = starting cap - remaining cap
    # percentage_used = cap_used/starting_cap
    # remaining_percentage = 100% - %used_up

    # one_day_potential_return = remaining_perecentage / remaining_days
    # 
    
    # write score ranking equations in ETF sheet
    for i in range(total_written):
        formula = f'=_xlfn.RANK.EQ(Calc!E{i+2}, Calc!$E$2:Calc!$E${total_written+1})'
        ws.cell(row=i + 2, column=1, value=formula)
    filename = f'ETFReport_{datetime.now().strftime("%m-%d-%Y")}.xlsx'

    wb.save(filename)
    wb.close()

    return filename

if __name__ == "__main__":
    excel_writer()