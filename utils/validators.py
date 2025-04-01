def validate_record(record):
    """
    Validate that a record meets all requirements for processing
    
    Checks:
    1. Record has line items with validated rates
    2. Record has required date_of_service
    3. Record has required patient info
    4. Record has required provider info
    """
    # Check for data structure
    if "data" not in record:
        return False
    
    data = record.get("data", {})
    
    # Check for line items with validated rates
    line_items = data.get("line_items", [])
    if not line_items:
        return False
        
    for line in line_items:
        if line.get("validated_rate") is None:
            return False
    
    # Check for date_of_service
    if not data.get("date_of_service"):
        # Try to get from line items
        has_date = any(line.get("date_of_service") for line in line_items)
        if not has_date:
            return False
    
    # Check for patient info
    patient_info = data.get("patient_info", {})
    if not patient_info.get("PatientName"):
        return False
        
    # Check for provider info
    provider_info = data.get("provider_info", {})
    if not provider_info.get("Billing_Name"):
        return False
        
    return True