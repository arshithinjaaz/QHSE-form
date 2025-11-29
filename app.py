# app.py

import os
import json
from flask import Flask, request, render_template, send_file
from io import BytesIO
from site_assessment_pdf import generate_assessment_pdf 
from site_assessment_excel import generate_assessment_excel 
from qhse_form import TEXT_FIELDS

# --- Configuration ---
app = Flask(__name__)

# Define the base directory (where app.py is located)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Set up the static and template paths relative to BASE_DIR
app.template_folder = os.path.join(BASE_DIR, 'templates')
app.static_folder = os.path.join(BASE_DIR, 'static')

GENERATED_DIR = os.path.join(BASE_DIR, 'generated')
os.makedirs(GENERATED_DIR, exist_ok=True)

# --- Routes ---

@app.route('/')
def index():
    """Serves the main Site Assessment Form page."""
    return render_template('index.html', text_fields=TEXT_FIELDS)

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """Receives JSON data and returns the generated PDF file."""
    try:
        data = request.get_json()

        if not data:
            return "Error: No data received for PDF.", 400

        # The ReportLab function expects two args: assessment_info and photos_data (list of B64 strings)
        # 1. Extract the main photo and signature data (they will be referenced directly in the PDF script)
        main_photo_b64 = data.get('inspection_photo_data') 
        
        # 2. Prepare photos_data list for ReportLab's BLOCK 8 (Photos/Site Diagrams)
        # We pass the single inspection photo as the first item in the list.
        photos_list = [main_photo_b64] if main_photo_b64 else []

        # 3. Clean up the main data dictionary before passing to ReportLab (optional, but cleaner)
        # The ReportLab code looks for 'tech_signature' and 'contact_signature',
        # so we map the front-end 'inspector_signature_data' to 'tech_signature'
        data['tech_signature'] = data.pop('inspector_signature_data', None)
        
        # Remove other temporary base64/mime fields from the main dictionary
        data.pop('inspection_photo_data', None)
        data.pop('inspection_photo_mime', None)
        
        # 4. Call the ReportLab function
        pdf_stream, pdf_filename = generate_assessment_pdf(data, photos_list)
        
        response = send_file(
            pdf_stream,
            mimetype='application/pdf', 
            as_attachment=True,
            download_name=pdf_filename, 
            max_age=0 
        )
        
        return response

    except Exception as e:
        print(f"Error during PDF generation: {e}")
        return f"Internal Server Error: Could not generate PDF. Details: {e}", 500

@app.route('/download-excel', methods=['POST'])
def download_excel():
    """Receives JSON data and returns the generated Excel file."""
    try:
        data = request.get_json()

        if not data:
            return "Error: No data received for Excel.", 400

        # Clean up Base64 data which is too large for Excel/CSV
        data.pop('inspector_signature_data', None)
        data.pop('inspection_photo_data', None)
        data.pop('inspection_photo_mime', None)

        assessment_info = data
        
        excel_stream, excel_filename = generate_assessment_excel(assessment_info) 
        
        response = send_file(
            excel_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
            as_attachment=True,
            download_name=excel_filename, 
            max_age=0 
        )
        
        return response

    except Exception as e:
        print(f"Error during Excel generation: {e}")
        return f"Internal Server Error: Could not generate Excel. Details: {e}", 500


# --- Run Application ---
if __name__ == '__main__':
    NEW_PORT = 5001 
    
    print(f"Flask running. Access form at: http://127.0.0.1:{NEW_PORT}/")
    
    app.run(debug=True, port=NEW_PORT)