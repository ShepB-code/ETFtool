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
    ws['E1'] = 'Remaining Cap %'
    ws['F1'] = 'Remaining Buffer %'
    ws['G1'] = 'Downside Before Buffer %'
    ws['H1'] = 'Remaining Outcome Period'
    ws['I1'] = 'Starting Cap %'
    ws['J1'] = 'Cap Used %'
    ws['K1'] = 'Percentage Used %'
    ws['L1'] = 'Remaining Percentage %'
    ws['M1'] = 'One Day Potential Return %'
    ws['N1'] = 'One Month Potential Return %'
    ws['O1'] = 'One Year Potential Return %'
    ws['P1'] = 'Raw Value Sum * Mult'
    ws['Q1'] = 'Raw Value Mult'
    ws['Q2'] = 2
 
    # get json
    with open('etf_data.json', 'r') as json_file: 
        etf_data = json.load(json_file)
        
        current_cell = 2
        for provider, data in etf_data.items():
            for etf, values in data.items():
                ws.cell(current_cell, 2).value = current_cell - 1 # Score Rank
                ws.cell(current_cell, 3).value = provider # Provider
                ws.cell(current_cell, 4).value = etf # Ticker
                ws.cell(current_cell, 5).value = values['remaining_cap'] # Remaining Cap %
                ws.cell(current_cell, 6).value = values['remaining_buffer'] # Remaining Buffer %
                ws.cell(current_cell, 7).value = values['downside_before_buffer'] # Downside Before Buffer %
                ws.cell(current_cell, 8).value = values['remaining_outcome_period'] # Remaining Outcome Period (days)
                ws.cell(current_cell, 9).value = values['starting_cap'] # Starting Cap %
                ws.cell(current_cell, 10).value = f'=I{current_cell} - E{current_cell}' # Cap Used %
                ws.cell(current_cell, 11).value = f'=J{current_cell}/I{current_cell}' # Percentage Used %
                ws.cell(current_cell, 12).value = f'=1-K{current_cell}' # Remaining Percentage %
                ws.cell(current_cell, 13).value = f'=E{current_cell}/H{current_cell}' # One day potential return %
                ws.cell(current_cell, 14).value = f'=M{current_cell}*30.5' # One month Potential Return %
                ws.cell(current_cell, 15).value = f'=M{current_cell}*365' # One Year Potential Return %
                ws.cell(current_cell, 16).value = f'=(E{current_cell}+F{current_cell}+G{current_cell})*$Q$2' # Raw Sum * Mult

                current_cell += 1

    
    # cap_used % = starting cap - remaining cap
    # percentage_used = cap_used/starting_cap
    # remaining_percentage = 100% - %used_up

    # one_day_potential_return = remaining_perecentage / remaining_days


    # write to Calculations Sheet
    ns = wb.create_sheet(title='Calc')

    ns['A1'] = 'Risk/Reward'
    ns['B1'] = 'Period/Time Factor'
    ns['C1'] = 'Rank'
    ns['D1'] = 'Buffer/Downside'
    ns['E1'] = 'Score'

    ns['F1'] = 'Time Factor'
    ns['F2'] = 100

    total_written = current_cell - 2

    for i in range(total_written):
        ns.cell(i + 2, 1).value = f'=ETFs!E{i+2}/ETFs!G{i+2}' # A column
        ns.cell(i + 2, 2).value = f'=$F$2/ETFs!H{i+2}' # B Column
        ns.cell(i + 2, 3).value = f'=A{i+2}*B{i+2}' # C Column
        ns.cell(i + 2, 4).value = f'=ETFs!F{i+2}/ETFs!G{i+2}' # D column
        ns.cell(i + 2, 5).value = f'=C{i+2}+D{i+2}' # E Column


    
    # write score ranking equations in ETF sheet
    for i in range(total_written):
        formula = f'=_xlfn.RANK.EQ(Calc!E{i+2}, Calc!$E$2:Calc!$E${total_written+1})'
        ws.cell(row=i + 2, column=1, value=formula)
    filename = f'ETFReport_{datetime.now().strftime("%m-%d-%Y")}.xlsx'

    # resize all columns in all worksheets and format columns with percentages
    for sheet in wb.sheetnames:
        resize_columns(wb[sheet])
        format_percentages(wb[sheet])

    
    wb.save(filename)
    wb.close()

    return filename


def as_text(value):
    if value is None or (isinstance(value, str) and '=' in value):
        return ""
    return str(value)

def resize_columns(worksheet):
    for column_cells in worksheet.columns:
        length = max(len(as_text(cell.value)) for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = length

def format_percentages(worksheet):
    header_row = worksheet[1]

    for cell in header_row:
        # if this should be represented as a % row, then format
        if '%' in cell.value:
            for cell in worksheet[cell.column_letter][1:]:
                cell.number_format = '0.00%'

if __name__ == "__main__":
    excel_writer()