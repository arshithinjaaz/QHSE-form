import io
import base64
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.platypus.flowables import HRFlowable

# --- CONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# IMPORTANT: Verify this LOGO_PATH based on your actual file structure.
# Assuming 'static' folder is a sibling of the directory containing this script:
LOGO_PATH = os.path.join(os.path.dirname(BASE_DIR), 'static', 'INJAAZ.png')


# --- PDF STYLING ---
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='HeaderLeft', fontSize=18, leading=22, alignment=0, spaceAfter=15, textColor=colors.HexColor('#125435')))
styles.add(ParagraphStyle(name='SectionTitle', fontSize=14, leading=18, spaceAfter=8, textColor=colors.darkgreen))
styles.add(ParagraphStyle(name='DataLabel', fontSize=10, leading=12, spaceAfter=2))
styles.add(ParagraphStyle(name='DataValue', fontSize=11, leading=14, spaceAfter=10, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='TableCaption', fontName='Helvetica-Bold', fontSize=12, leading=15, spaceAfter=5, textColor=colors.black, alignment=0))
styles.add(ParagraphStyle(name='DefectDesc', fontSize=10, leading=12, spaceAfter=5))
styles.add(ParagraphStyle(name='SignatureTextLeft', fontName='Helvetica', fontSize=10, leading=12, alignment=0))
# Adjusted DetailHeader to include left padding/indentation
styles.add(ParagraphStyle(name='DetailHeader', fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.black, backColor=colors.HexColor('#F5F5F5'), leftIndent=5))


# --- HELPER FUNCTION ---

def get_base64_image(base64_data_url, width=None, height=None):
    """Decodes a Base64 data URL string into a ReportLab Image object."""
    try:
        if ',' in base64_data_url:
            base64_content = base64_data_url.split(',', 1)[1]
        else:
            base64_content = base64_data_url
            
        image_data = base64.b64decode(base64_content)
        
        img_buffer = io.BytesIO(image_data)
        img = Image(img_buffer, width=width, height=height)
        img.kind = 'bound'
        return img
    except Exception:
        return Paragraph("<b>[Image Load Error]</b>", styles['DataLabel'])

# --- CORE PDF GENERATION FUNCTION ---

def generate_assessment_pdf(data, photos_list):
    """
    Generates the QHSE Inspection Report as a PDF document.
    """
    
    buffer = io.BytesIO()
    margin = 0.75 * inch
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=margin, leftMargin=margin, topMargin=margin, bottomMargin=margin)
    elements = []
    
    doc_width = A4[0] - 2 * margin
    
    project_name = data.get('project_name', 'INSPECTION').replace(' ', '_').upper()
    date_of_visit = data.get('date_of_visit', datetime.now().strftime('%Y%m%d'))
    pdf_filename = f"QHSE_Report_{project_name}_{date_of_visit}.pdf"

    # --- 2. HEADER (Title Left, Logo Right) ---
    report_title = Paragraph("<b>QHSE Inspection Report</b>", styles['HeaderLeft'])
    
    logo_flowable = Paragraph("LOGO", styles['DataLabel'])
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        try:
            logo_flowable = Image(LOGO_PATH, width=1.5*inch, height=0.5*inch)
        except Exception:
            pass

    header_data = [
        [report_title, logo_flowable]
    ]
    
    col_width_title = doc_width * 0.7
    col_width_logo = doc_width * 0.3
    
    header_table = Table(header_data, colWidths=[col_width_title, col_width_logo])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#125435'), spaceBefore=5, spaceAfter=10))
    elements.append(Spacer(1, 12))


    # --- 3. INSPECTION INFO (Tab 1) - Gap Fixed ---
    elements.append(Paragraph("<b>1. Inspection Info</b>", styles['SectionTitle']))
    
    info_data = [
        ["Project Name:", data.get('project_name', 'N/A')],
        ["Assessor Name:", data.get('assessor_name', 'N/A')],
        ["Date of Visit:", data.get('date_of_visit', 'N/A')],
        ["Building Location:", data.get('building_location', 'N/A')]
    ]
    
    info_table_rows = []
    for key_label, value_text in info_data:
        # Note: The DetailHeader style includes the left padding for the label text
        info_table_rows.append([
            Paragraph(f"{key_label}", styles['DetailHeader']), 
            Paragraph(value_text, styles['DefectDesc']) 
        ])
    
    # We will use the full width for the first column's content (label + space)
    # This prevents the content from being crammed against the vertical separator.
    col_width_label_content = 1.5 * inch
    col_width_value_content = doc_width - col_width_label_content
    
    info_table = Table(info_table_rows, colWidths=[col_width_label_content, col_width_value_content])
    info_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # KEY FIX: Set background color for the first column (labels)
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F8F8')), 
        # Add a vertical line right after the first column (0)
        ('LINEAFTER', (0, 0), (0, -1), 0.5, colors.lightgrey), 
        
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.lightgrey), 
        
        # Remove padding from the table structure, the DetailHeader style now handles the label indentation
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5), # Keep some right padding for values
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 24))


    # --- 4. DEFECT REPORT ITEMS (Tab 2) ---
    elements.append(Paragraph("<b>2. Defect Report Items</b>", styles['SectionTitle']))
    defect_items = data.get('defect_items', [])

    if not defect_items:
        elements.append(Paragraph("No defect items were added to the report.", styles['DataValue']))
    else:
        col_width_photos = 2.5 * inch
        col_width_details_section = doc_width - col_width_photos
        
        col_width_detail_label = col_width_details_section * 0.3
        col_width_detail_value = col_width_details_section * 0.7
        
        for i, item in enumerate(defect_items):
            elements.append(Paragraph(f"<b>DEFECT ITEM #{i + 1}</b>", styles['TableCaption']))
            
            # --- Text Details Table (Nested) ---
            detail_rows = [
                (Paragraph(f"Location:", styles['DetailHeader']), Paragraph(item.get('defect_location', 'N/A'), styles['DefectDesc'])),
                (Paragraph(f"Description:", styles['DetailHeader']), Paragraph(item.get('defect_description', 'N/A'), styles['DefectDesc'])),
                (Paragraph(f"Category:", styles['DetailHeader']), Paragraph(item.get('defect_category', 'N/A'), styles['DefectDesc'])),
                (Paragraph(f"Priority:", styles['DetailHeader']), Paragraph(item.get('defect_priority', 'N/A'), styles['DefectDesc'])),
                (Paragraph(f"Recommendation:", styles['DetailHeader']), Paragraph(item.get('defect_recommendation', 'N/A'), styles['DefectDesc'])),
            ]
            
            detail_nested_table = Table(detail_rows, colWidths=[col_width_detail_label, col_width_detail_value])
            detail_nested_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0), # No padding here, handled by style
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.lightgrey), 
                # Background handled by DetailHeader style, but we need to set the cell background too if we want it to fill completely.
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F8F8')), 
                ('LINEAFTER', (0, 0), (0, -1), 0.5, colors.lightgrey), # Vertical separator in nested table
            ]))
            
            # --- Photo Flowables (The content for the second main column) ---
            photos = item.get('photos', [])
            photo_flowables = [Paragraph("<b>Attached Photos:</b>", styles['DataLabel']), Spacer(1, 6)]
            
            img_max_width = col_width_photos * 0.9
            img_max_height = 2.0 * inch

            for photo_b64 in photos:
                photo = get_base64_image(photo_b64, width=img_max_width, height=img_max_height)
                photo_flowables.append(photo)
                photo_flowables.append(Spacer(1, 12))
                
            if not photos:
                photo_flowables.append(Paragraph("No images attached.", styles['DefectDesc']))

            defect_table_data = [
                [detail_nested_table, photo_flowables]
            ]
            
            defect_table = Table(defect_table_data, colWidths=[col_width_details_section, col_width_photos])
            
            defect_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEBEFORE', (1, 0), (1, 0), 1, colors.lightgrey),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            elements.append(defect_table)
            elements.append(Spacer(1, 18))
            
    elements.append(PageBreak())

    # --- 5. SIGNATURE (Tab 3) - ALIGNED LEFT ---
    elements.append(Paragraph("<b>3. Summary & Assessor Signature</b>", styles['SectionTitle']))
    elements.append(Spacer(1, 12))
    
    signature_b64 = data.get('tech_signature')
    assessor_name = data.get('assessor_name', 'N/A')
    
    sig_width = 3.0 * inch
    sig_height = 1.0 * inch

    signature_elements = []
    
    if signature_b64:
        signature_img = get_base64_image(signature_b64, width=sig_width, height=sig_height)
        signature_elements.append(signature_img)
        signature_elements.append(Paragraph(f"<i>Signed by: {assessor_name}</i>", styles['SignatureTextLeft']))
    else:
        signature_elements.append(Spacer(1, sig_height))
        signature_elements.append(Paragraph("<b>Assessor Signature:</b> [Signature not provided]", styles['SignatureTextLeft']))

    signature_table = Table([[signature_elements]], colWidths=[doc_width])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    elements.append(signature_table)
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("This report confirms the site inspection completed by the Assessor on the date of visit.", styles['Normal']))

    # --- BUILD DOCUMENT ---
    doc.build(elements)

    buffer.seek(0)
    return buffer, pdf_filename