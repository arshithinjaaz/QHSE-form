# site_assessment_excel.py

from io import BytesIO
from openpyxl import Workbook
from qhse_form import TEXT_FIELDS # Import the field list for ordering

def generate_assessment_excel(assessment_info):
    """Generates an Excel (XLSX) file from data using openpyxl."""
    
    # 1. Initialize Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "QHSE Data Export"
    
    # 2. Prepare Header and Data rows
    headers = []
    data_row = []
    
    for key in TEXT_FIELDS:
        # Use key names as readable headers
        headers.append(key.replace('_', ' ').title())
        # Ensure data is present, default to empty string
        data_row.append(str(assessment_info.get(key, '')))
    
    # 3. Write Header and Data
    ws.append(headers)
    ws.append(data_row)
    
    # 4. Save to an in-memory stream (BytesIO)
    excel_stream = BytesIO()
    wb.save(excel_stream)
    excel_stream.seek(0)
    
    filename = f"QHSE_Data_{assessment_info.get('project_name', 'Export').replace(' ', '_')}.xlsx"
    
    return excel_stream, filename