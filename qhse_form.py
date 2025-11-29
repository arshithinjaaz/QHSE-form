# qhse_form.py

# List of expected text/data fields for validation/export headers
TEXT_FIELDS = [
    # Project & Client Details
    'client_name', 
    'project_name', 
    'site_address',
    'date_of_visit', 
    'key_person_name',
    'contact_number',
    
    # Site Count & Current Operations
    'room_count',
    'lift_count_total',
    'current_team_desc',
    'current_team_size',
    'facility_ground_parking',
    'facility_washroom_male',
    'facility_basement',
    'facility_washroom_female',
    'facility_podium',
    'facility_changing_room',
    'facility_gym_room',
    'facility_play_kids_place',
    'facility_swimming_pool',
    'facility_garbage_room',
    'facility_floor_chute_room',
    'facility_staircase',
    'facility_floor_service_room',
    'facility_cleaner_count',
    
    # Cleaning Requirements & Scope (Includes checkboxes/radios)
    # These fields must be handled explicitly in your ReportLab code's `get_checkbox_list`
    # Example: 'scope_toilets', 'freq_daily', 'deep_cleaning_required', etc.
    'deep_clean_areas',
    'waste_general',
    'waste_recycling',
    'waste_hazardous',
    'waste_hazardous_details',
    
    # Special Considerations
    'restricted_access',
    'pest_control',
    
    # Health & Safety
    'ppe_requirements',
    'risk_assessment_required',
    'fire_exits_reviewed',
    
    # Staffing Requirements
    'staff_needed',
    'shift_times',
    'weekend_work',
    
    # Notes
    'notes_and_observations',
    
    # Signatures (Note: front-end signature is mapped to 'tech_signature' in app.py)
    'assessor_name',
    'contact_name', # Matches contact_signature logic in ReportLab code
]