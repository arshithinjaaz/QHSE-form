# app.py

import os
import json
from flask import Flask, request, render_template, send_file
from io import BytesIO
# IMPORTANT: You must update these functions to accept the new data structure!
from site_assessment_pdf import generate_assessment_pdf 
from site_assessment_excel import generate_assessment_excel 
# from qhse_form import TEXT_FIELDS # Assuming this still exists

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
    # Note: If 'qhse_form.py' no longer exists or TEXT_FIELDS is unused, you can remove the import and this argument.
    # return render_template('index.html', text_fields=TEXT_FIELDS) 
    return render_template('index.html') 


@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """Receives JSON data and returns the generated PDF file."""
    try:
        data = request.get_json()

        if not data:
            return "Error: No data received for PDF.", 400

        # --- NEW STEP: Extract Defect Items ---
        defect_items = data.pop('defect_items', []) 
        
        # 1. Extract the main photo and signature data
        main_photo_b64 = data.get('inspection_photo_data') 
        
        # 2. Prepare photos_data list for ReportLab's BLOCK 8 (Photos/Site Diagrams)
        # Now this list should also include all the defect photos for a combined photo appendix, 
        # OR you pass the 'defect_items' array to the PDF generator to handle block-by-block.
        
        # For simplicity, we create one large photo list for the generator, 
        # but you might want to adjust 'generate_assessment_pdf' to handle the item photos separately.
        photos_list = [main_photo_b64] if main_photo_b64 else []
        
        # CRITICAL: Append all defect photos to the main photo list (or pass items separately)
        # We extract all defect photos (Base64 strings) and add them to the photo list
        for item in defect_items:
            photos_list.extend(item.get('photos', []))

        # 3. Clean up the main data dictionary and map signatures
        data['tech_signature'] = data.pop('inspector_signature_data', None)
        
        # Remove other temporary base64/mime fields from the main dictionary
        data.pop('inspection_photo_data', None)
        data.pop('inspection_photo_mime', None)
        
        # 4. CRITICAL: Inject the list of defect items back into the main data dictionary
        # This allows generate_assessment_pdf to process the text and photo data block by block
        data['defect_items'] = defect_items
        
        # 5. Call the ReportLab function (REQUIRES UPDATE in site_assessment_pdf.py)
        # Note: You MUST update generate_assessment_pdf to handle the 'data['defect_items']' list.
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
        
        # --- NEW STEP: Extract Defect Items ---
        defect_items = data.get('defect_items', []) 
        
        # 1. Clean up Base64 data from the main dictionary (too large for Excel/CSV)
        data.pop('inspector_signature_data', None)
        data.pop('inspection_photo_data', None)
        data.pop('inspection_photo_mime', None)
        
        # 2. CRITICAL: Inject the list of defect items into the main dictionary
        data['defect_items'] = defect_items
        
        assessment_info = data
        
        # 3. Call the Excel function (REQUIRES UPDATE in site_assessment_excel.py)
        # Note: You MUST update generate_assessment_excel to process the 'data['defect_items']' list.
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