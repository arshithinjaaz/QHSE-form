# site_assessment_pdf.py

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import base64
import logging

# --- Logging Configuration ---
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# NOTE: Ensure this path is correct for your logo file
LOGO_PATH = os.path.join(BASE_DIR, 'static', 'INJAAZ.png')
CHECKBOX_CHAR = u'\u2610' # Unicode for empty checkbox
CHECKED_CHAR = u'\u2611' # Unicode for checked box (Used for output)

# Initialize styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='SmallText', fontName='Helvetica', fontSize=8, leading=10))
# BoldTitle is used for section headings like "1. Project & Client Details"
styles.add(ParagraphStyle(name='BoldTitle', fontName='Helvetica-Bold', fontSize=14, leading=16, textColor=colors.HexColor('#125435')))
styles.add(ParagraphStyle(name='Question', fontName='Helvetica-Bold', fontSize=10, leading=12))
styles.add(ParagraphStyle(name='Answer', fontName='Helvetica', fontSize=10, leading=12))

# --- HELPER FUNCTION for Checklists ---

def get_checkbox_list(assessment_info, prefix, multi_word_map=None):
    """
    Filters the data for a given prefix and returns a formatted list of checked items.
    """
    items = []
    
    if multi_word_map is None:
        multi_word_map = {}
        
    for key, value in assessment_info.items():
        # Handle various representations of 'checked'
        if key.startswith(prefix) and value in ['True', 'true', 'Yes', 'yes', CHECKED_CHAR, CHECKED_CHAR]:
            base_key = key[len(prefix):]
            display_name = multi_word_map.get(base_key, base_key.replace('_', ' ').title())
            items.append(display_name)
    
    return ", ".join(items) if items else "None Specified"

# --- CORE HELPER FUNCTIONS ---

def get_sig_image(assessment_info, key, name):
    """Decodes base64 signature data into a ReportLab Image object."""
    from reportlab.lib.utils import ImageReader # Needed for ReportLab to handle in-memory image
    
    base64_sig = assessment_info.get(key)
    if base64_sig:
        try:
            if ',' in base64_sig:
                base64_data = base64_sig.split(',')[1]
            else:
                base64_data = base64_sig
            
            image_data = base64.b64decode(base64_data)
            img_stream = BytesIO(image_data)
            
            sig_img = Image(img_stream)
            sig_img.drawHeight = 0.7 * inch
            sig_img.drawWidth = 2.5 * inch
            sig_img.hAlign = 'LEFT' 
            return sig_img
        except Exception as e:
            logger.error(f"Failed to decode signature image for {name}: {e}")
            return Paragraph(f'Signature Failed: {name}', styles['Normal'])
        
    return Paragraph(f'Unsigned: {name}', styles['Normal']) 

def create_signature_table(assessment_info):
    """Creates the signature block (Block 9)."""
    sig_story = []
    
    sig_story.append(Spacer(1, 0.3*inch))
    sig_story.append(Paragraph('9. Signatures', styles['BoldTitle'])) 
    sig_story.append(Spacer(1, 0.1*inch)) 

    # 'tech_signature' is mapped from the front-end signature in app.py
    tech_sig = get_sig_image(assessment_info, 'tech_signature', 'Assessor')
    contact_sig = get_sig_image(assessment_info, 'contact_signature', 'Key Contact')

    signature_data = [
        [tech_sig, contact_sig],
        [Paragraph('<font size="10">_________________________</font>', styles['Normal']), 
         Paragraph('<font size="10">_________________________</font>', styles['Normal'])],
        [Paragraph(f"<font size='10'><b>Assessor:</b> {assessment_info.get('assessor_name', 'N/A')}</font>", styles['Normal']), 
         Paragraph(f"<font size='10'><b>Key Contact:</b> {assessment_info.get('contact_name', assessment_info.get('key_person_name', 'N/A'))}</font>", styles['Normal'])]
    ]
    
    signature_table = Table(signature_data, colWidths=[3.75*inch, 3.75*inch], rowHeights=[0.8*inch, 0.1*inch, 0.2*inch]) 
    
    TEXT_SHIFT_PADDING = 15 

    signature_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'), 
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0, 1), (-1,-1), TEXT_SHIFT_PADDING), 
    ]))
    
    sig_story.append(signature_table)
    return sig_story

def get_inline_image(base64_img, width, height, placeholder_text="No Photo"):
    """Decodes base64 image data into a ReportLab Image object."""
    from reportlab.lib.utils import ImageReader
    if not base64_img:
        return Paragraph(f'<font size="8">{placeholder_text}</font>', styles['SmallText'])
    try:
        if ',' in base64_img:
            base64_data = base64_img.split(',')[1]
        else:
            base64_data = base64_img
            
        image_data = base64.b64decode(base64_data)
        img_stream = BytesIO(image_data)
        img = Image(img_stream)
        img.drawWidth = width
        img.drawHeight = height
        img.hAlign = 'CENTER' 
        return img
    except Exception as e:
        logger.error(f"Image load error: {e}")
        return Paragraph(f'<font size="8">Image Load Error</font>', styles['SmallText'])

# --- TEMPLATE HANDLER FOR FOOTER (Fixed for better spacing) ---

FOOTER_TEXT = "PO BOX, 3456 Ajman, UAE | Tel +971 6 7489813 | Fax +971 6 711 6701 | www.injaaz.ae | Member of Ajman Holding group"

def page_layout_template(canvas, doc):
    """Function to draw the custom footer on every page."""
    canvas.saveState()
    
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#666666'))
    
    # Calculate the footer position to be *above* the new bottom margin (0.75 inch)
    footer_y = doc.bottomMargin - 0.25 * inch 
    canvas.drawCentredString(letter[0] / 2, footer_y, FOOTER_TEXT)
    
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.5)
    # Draw the line slightly above the footer text
    canvas.line(doc.leftMargin, footer_y + 0.15 * inch, letter[0] - doc.rightMargin, footer_y + 0.15 * inch)
    
    # Draw page number next to the footer text
    canvas.drawRightString(letter[0] - doc.rightMargin, footer_y, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()

# --- MAIN GENERATOR FUNCTION ---

def generate_assessment_pdf(assessment_info, photos_data):
    """Generates the full ReportLab PDF document."""
    
    project_name = assessment_info.get('project_name', 'Unknown').replace(' ', '_')
    ts = datetime.now().strftime('%Y%m%d_%H%M%S') 
    filename = f"Site_Assessment_{project_name}_{ts}.pdf"
    
    buffer = BytesIO() 

    # INCREASED bottomMargin to 0.75 inch to prevent content/footer overlap
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=inch/4, leftMargin=inch/4,
                              topMargin=inch/4, bottomMargin=0.75*inch)
                              
    doc.build(
        build_assessment_story(assessment_info, photos_data), 
        onFirstPage=page_layout_template, 
        onLaterPages=page_layout_template
    )
    
    buffer.seek(0)
    return buffer, filename


def build_assessment_story(assessment_info, photos_data):
    story = []
    
    # Define mapping for complex field names for readability
    scope_map = {
        'toilets': 'Toilets/Washrooms',
        'kitchens': 'Kitchens/Break rooms',
        'hallways': 'Hallways/Common Areas',
        'lobbies': 'Entrances/Lobbies',
        'windows': 'Windows (Interior/Exterior)',
        'carpet': 'Carpet Cleaning',
        'hardfloor': 'Hard Floor Maintenance (sweeping, mopping, polishing)',
    }

    # --- Data Processing for Cleaning Sections ---
    routine_scope = get_checkbox_list(assessment_info, 'scope_', scope_map)
    frequency = get_checkbox_list(assessment_info, 'freq_')

    # --- BLOCK 3: Deep Cleaning Required (MODIFIED OUTPUT - ONLY SHOWS SELECTED CHOICE) ---
    deep_cleaning_input = assessment_info.get('deep_cleaning_required', '').strip()
    # Check if 'deep_cleaning_required' is NOT set to 'no', 'false', or the unchecked character.
    deep_clean_required = deep_cleaning_input.lower() not in ['no', 'false', CHECKBOX_CHAR.lower()]
    deep_clean_areas = assessment_info.get('deep_clean_areas', '')
    
    if deep_clean_required:
        # Output: [x] Yes (Areas: ...)
        deep_clean_details = f"{CHECKED_CHAR} Yes (Areas: {deep_clean_areas or 'Not specified'})"
    else:
        # Output: [x] No
        if deep_clean_areas:
             # If the user selected 'No' but still filled areas
             deep_clean_details = f"{CHECKED_CHAR} No (Areas: {deep_clean_areas})" 
        else:
             deep_clean_details = f"{CHECKED_CHAR} No"

    waste_list = []
    if assessment_info.get('waste_general') == 'True': waste_list.append("General Waste")
    if assessment_info.get('waste_recycling') == 'True': waste_list.append("Recycling")
    if assessment_info.get('waste_hazardous') == 'True': 
        hazardous_details = assessment_info.get('waste_hazardous_details', 'Not specified')
        waste_list.append(f"Hazardous Waste (Specify: {hazardous_details})")
    
    waste_disposal = "; ".join(waste_list) if waste_list else "None Specified"
    
    
    # 2. Header and Title with Logo
    title_text = f"Site Assessment Form - {assessment_info.get('project_name', 'N/A')} ({datetime.now().strftime('%Y-%m-%d')})"
    title_paragraph = Paragraph(title_text, styles['BoldTitle'])

    logo = Paragraph('', styles['Normal'])
    try:
        # Check if the logo file exists to prevent errors
        if os.path.exists(LOGO_PATH):
            logo = Image(LOGO_PATH)
            logo.drawWidth = 0.8 * inch 
            logo.drawHeight = 0.7 * inch 
            logo.hAlign = 'RIGHT' 
    except Exception as e:
        logger.warning(f"Logo not found or failed to load at {LOGO_PATH}: {e}")

    header_data = [[title_paragraph, logo]]
    header_table = Table(header_data, colWidths=[6.5 * inch, 1.5 * inch]) 
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))


    # --- BLOCK 1: Project & Client Details ---
    story.append(Paragraph('1. Project & Client Details', styles['BoldTitle']))
    story.append(Spacer(1, 0.1*inch))
    
    details_data = [
        ['Client Name:', assessment_info.get('client_name', 'N/A'), 'Project Name:', assessment_info.get('project_name', 'N/A')],
        ['Site Address:', assessment_info.get('site_address', 'N/A'), 'Date of Visit:', assessment_info.get('date_of_visit', 'N/A')],
        ['Key Person:', assessment_info.get('key_person_name', 'N/A'), 'Contact Number:', assessment_info.get('contact_number', 'N/A')]
    ]

    details_table = Table(details_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F2F2F2')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#F2F2F2')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.2*inch))


    # --- BLOCK 2: Site Count & Current Operations ---
    story.append(Paragraph('2. Site Count & Current Operations', styles['BoldTitle']))
    story.append(Spacer(1, 0.1*inch))
    
    # 2A. General Counts and Team Info
    count_data = [
        [Paragraph('<b>Room Count (General):</b>', styles['Question']), assessment_info.get('room_count', 'N/A'), Paragraph('<b>Current Team:</b>', styles['Question']), Paragraph(assessment_info.get('current_team_desc', 'N/A'), styles['Answer'])],
        [Paragraph('<b>Lift Count (Total):</b>', styles['Question']), assessment_info.get('lift_count_total', 'N/A'), Paragraph('<b>Current Team Size:</b>', styles['Question']), assessment_info.get('current_team_size', 'N/A')],
    ]

    count_table = Table(count_data, colWidths=[1.5*inch, 2.5*inch, 1.7*inch, 2.3*inch])
    count_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#D3E5D3')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(count_table)
    story.append(Spacer(1, 0.2*inch))

    # 2B. Detailed Facility Area Counts
    story.append(Paragraph('<b>2B. Detailed Facility Area Counts</b>', styles['Question']))
    story.append(Spacer(1, 0.1*inch))
    
    facility_data = [
        # Row 1
        [Paragraph('<b>Ground Parking:</b>', styles['Answer']), assessment_info.get('facility_ground_parking', '0'), 
         Paragraph('<b>Male Washroom:</b>', styles['Answer']), assessment_info.get('facility_washroom_male', '0')],
        # Row 2
        [Paragraph('<b>Basement:</b>', styles['Answer']), assessment_info.get('facility_basement', '0'), 
         Paragraph('<b>Female Washroom:</b>', styles['Answer']), assessment_info.get('facility_washroom_female', '0')],
        # Row 3
        [Paragraph('<b>Podium:</b>', styles['Answer']), assessment_info.get('facility_podium', '0'), 
         Paragraph('<b>Changing Room:</b>', styles['Answer']), assessment_info.get('facility_changing_room', '0')],
        # Row 4
        [Paragraph('<b>Gym Room:</b>', styles['Answer']), assessment_info.get('facility_gym_room', '0'), 
         Paragraph('<b>Kids Place:</b>', styles['Answer']), assessment_info.get('facility_play_kids_place', '0')],
        # Row 5
        [Paragraph('<b>Swimming Pool:</b>', styles['Answer']), assessment_info.get('facility_swimming_pool', '0'), 
         Paragraph('<b>Garbage Room:</b>', styles['Answer']), assessment_info.get('facility_garbage_room', '0')],
        # Row 6
        [Paragraph('<b>Floor Chute Room:</b>', styles['Answer']), assessment_info.get('facility_floor_chute_room', '0'), 
         Paragraph('<b>Staircase:</b>', styles['Answer']), assessment_info.get('facility_staircase', '0')],
        # Row 7 (Final row with remaining counts)
        [Paragraph('<b>Floor Service Room:</b>', styles['Answer']), assessment_info.get('facility_floor_service_room', '0'), 
         Paragraph('<b>Cleaner Total:</b>', styles['Answer']), assessment_info.get('facility_cleaner_count', '0')],
    ]

    facility_table = Table(facility_data, colWidths=[1.7*inch, 2.3*inch, 2.0*inch, 2.0*inch])
    facility_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F2F2F2')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), # Bold first column
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'), # Bold third column
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(facility_table)
    story.append(Spacer(1, 0.2*inch))


    # --- BLOCK 3: Cleaning Requirements (MODIFIED OUTPUT - ONLY SHOWS SELECTED CHOICE) ---
    story.append(Paragraph('3. Cleaning Requirements & Scope', styles['BoldTitle']))
    story.append(Spacer(1, 0.1*inch))
    
    cleaning_table_data = [
        [Paragraph('<b>Routine Scope (Areas):</b>', styles['Question']), Paragraph(routine_scope, styles['Answer'])],
        [Paragraph('<b>Frequency:</b>', styles['Question']), Paragraph(frequency, styles['Answer'])],
        [Paragraph('<b>Deep Cleaning Required:</b>', styles['Question']), Paragraph(deep_clean_details, styles['Answer'])],
        [Paragraph('<b>Waste Disposal:</b>', styles['Question']), Paragraph(waste_disposal, styles['Answer'])],
    ]

    cleaning_table = Table(cleaning_table_data, colWidths=[2.0*inch, 6.0*inch])
    cleaning_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F9F9F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(cleaning_table)
    story.append(Spacer(1, 0.2*inch))


    # --- BLOCK 4: Special Consideration ---
    story.append(Paragraph('4. Special Considerations', styles['BoldTitle']))
    story.append(Spacer(1, 0.1*inch))
    
    restricted_access_text = assessment_info.get('restricted_access') or 'N/A'
    pest_control_text = assessment_info.get('pest_control') or 'N/A'

    consideration_data = [
        [Paragraph('Are there any areas with restricted access? (Describe area and access requirements)', styles['Question']), 
         Paragraph(restricted_access_text, styles['Answer'])],
        [Paragraph('Pest control needed? (Specify type and location)', styles['Question']), 
         Paragraph(pest_control_text, styles['Answer'])],
    ]

    consideration_table = Table(consideration_data, colWidths=[4.5*inch, 3.5*inch])
    consideration_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(consideration_table)
    story.append(Spacer(1, 0.2*inch))


    # --- BLOCK 5: Health & Safety (MODIFIED OUTPUT - ONLY SHOWS SELECTED CHOICE) ---
    story.append(Paragraph('5. Health & Safety', styles['BoldTitle']))
    story.append(Spacer(1, 0.1*inch))
    
    # 5. Risk Assessment Logic
    risk_input = assessment_info.get('risk_assessment_required', '').strip()
    risk_required = risk_input.lower() not in ['no', 'false', CHECKBOX_CHAR.lower()]
    risk_choice = f"{CHECKED_CHAR} Yes" if risk_required else f"{CHECKED_CHAR} No"

    # 5. Fire Exits Logic
    fire_input = assessment_info.get('fire_exits_reviewed', '').strip()
    fire_reviewed = fire_input.lower() not in ['no', 'false', CHECKBOX_CHAR.lower()]
    fire_choice = f"{CHECKED_CHAR} Yes" if fire_reviewed else f"{CHECKED_CHAR} No"

    safety_data = [
        [Paragraph('PPE requirements:', styles['Question']), 
         Paragraph(assessment_info.get('ppe_requirements', '___________________________'), styles['Answer'])],
        [Paragraph('Risk assessments required:', styles['Question']), 
         Paragraph(risk_choice, styles['Answer'])],
        [Paragraph('Fire exits and evacuation points reviewed?', styles['Question']), 
         Paragraph(fire_choice, styles['Answer'])],
    ]

    safety_table = Table(safety_data, colWidths=[4.5*inch, 3.5*inch])
    safety_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(safety_table)
    story.append(Spacer(1, 0.2*inch))


    # --- BLOCK 6: Staffing Requirements (MODIFIED OUTPUT - ONLY SHOWS SELECTED CHOICE) ---
    story.append(Paragraph('6. Staffing Requirements', styles['BoldTitle']))
    story.append(Spacer(1, 0.1*inch))
    
    # 6. Weekend Work Logic
    weekend_input = assessment_info.get('weekend_work', '').strip()
    weekend_work = weekend_input.lower() in ['true', 'yes', CHECKED_CHAR.lower()]
    # This line displays ONLY the selected option with the checked box.
    weekend_choice = f"{CHECKED_CHAR} Yes" if weekend_work else f"{CHECKED_CHAR} No"

    staffing_data = [
        [Paragraph('Number of staff needed per shift:', styles['Question']), 
         Paragraph(assessment_info.get('staff_needed', '_______'), styles['Answer'])],
        [Paragraph('Shift times:', styles['Question']), 
         Paragraph(assessment_info.get('shift_times', '___________________________'), styles['Answer'])],
        [Paragraph('Weekend or out-of-hours’ work?', styles['Question']), 
         Paragraph(weekend_choice, styles['Answer'])],
    ]

    staffing_table = Table(staffing_data, colWidths=[4.5*inch, 3.5*inch])
    staffing_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(staffing_table)
    story.append(Spacer(1, 0.2*inch))


    # --- BLOCK 7: Notes and Observation ---
    story.append(Paragraph('7. Notes and Observation', styles['BoldTitle']))
    story.append(Spacer(1, 0.1*inch))

    notes_text = assessment_info.get('notes_and_observations', '')
    notes_data = [[Paragraph(notes_text, styles['Answer'])]]
    notes_table = Table(notes_data, colWidths=[8.0*inch], rowHeights=[1.5*inch])
    notes_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(notes_table)
    story.append(Spacer(1, 0.2*inch))
    
    # --- BLOCK 9: Signatures ---
    story.extend(create_signature_table(assessment_info))
    story.append(Spacer(1, 0.2*inch))
    
    # --- Start Photos on a new page ---
    story.append(PageBreak())

    # --- BLOCK 8: Photos/Site Diagrams (Single-table logic) ---
    story.append(Paragraph('8. Site Photos & Diagrams', styles['BoldTitle']))
    story.append(Spacer(1, 0.1*inch))
    
    all_photos_data = [] 
    
    if photos_data:
        
        heading_paragraph = Paragraph('<font color="#333333"><b>Visual Evidence</b></font>', styles['Normal'])
        all_photos_data.append([heading_paragraph, ''])
        
        # Group photos into rows of two
        for i in range(0, len(photos_data), 2):
            row = []
            for j in range(2):
                photo_idx = i + j
                if photo_idx < len(photos_data):
                    try:
                        photo_b64 = photos_data[photo_idx]
                        img = get_inline_image(photo_b64, 3.5 * inch, 2.5 * inch, placeholder_text=f'Photo {photo_idx + 1} N/A')
                        row.append(img)
                    except Exception:
                        row.append(Paragraph(f'Image {photo_idx + 1} Failed to Load', styles['Normal']))
                else:
                    row.append('') # Empty cell for padding
            all_photos_data.append(row)
        
        # Add a transparent spacer row at the end (for bottom padding)
        all_photos_data.append([Spacer(1, 0.1*inch), Spacer(1, 0.1*inch)])
        
        photo_table = Table(all_photos_data, colWidths=[3.75*inch, 3.75*inch])
        
        style_list = [
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
            
            # Style for the "Visual Evidence" heading row (first row)
            ('SPAN', (0, 0), (1, 0)),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#EFEFEF')),
            ('TOPPADDING', (0, 0), (1, 0), 5),
            ('BOTTOMPADDING', (0, 0), (1, 0), 5),
        ]
        
        photo_table.setStyle(TableStyle(style_list))
        story.append(photo_table)
    else:
        story.append(Paragraph("No photos or site diagrams were provided for this assessment.", styles['Normal']))


    return story