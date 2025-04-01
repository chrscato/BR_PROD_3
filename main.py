import os
import json
import glob
from pathlib import Path
from datetime import datetime

# Import from modules
from config.settings import BASE_PATH, JSON_DIR_PATH, HISTORICAL_EXCEL_PATH
from utils.validators import validate_record
from data.excel_manager import initialize_excel_file, load_historical_duplicates, append_to_excel
from processors.document_processor import generate_document
from processors.eobr_processor import collect_additional_eobr_data
from data.db_manager import check_if_item_paid, update_payment_info

def setup_folder_structure():
    """Create folder structure for current run"""
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = os.path.join(BASE_PATH, current_date)
    
    folder_structure = {
        'root': run_folder,
        'docs': os.path.join(run_folder, 'docs'),
        'pdf': os.path.join(run_folder, 'pdf'),
        'excel': os.path.join(run_folder, 'excel'),
    }
    
    for path in folder_structure.values():
        Path(path).mkdir(parents=True, exist_ok=True)
        
    folder_structure['current_excel'] = os.path.join(folder_structure['excel'], f"EOBR_Data_{current_date}.xlsx")
    return folder_structure

def adapt_record_format(record, filename):
    """Adapt the new JSON format to match what the processors expect"""
    # Create a structure similar to what the processors expect
    adapted_record = {
        "file_info": {
            "file_name": filename
        },
        "data": {
            "patient_info": record.get("order_details", {}),
            "provider_info": record.get("provider_details", {}),
            "date_of_service": next((line.get("date_of_service") for line in record.get("service_lines", [])), None),
            "line_items": []
        },
        "order_id": record.get("Order_ID")
    }
    
    # Convert service_lines to line_items
    for line in record.get("service_lines", []):
        adapted_line = {
            "date_of_service": line.get("date_of_service"),
            "cpt": line.get("cpt_code"),
            "modifier": ",".join(line.get("modifiers", [])) if line.get("modifiers") else None,
            "pos": line.get("place_of_service"),
            "units": line.get("units"),
            "charge": line.get("charge_amount"),
            "validated_rate": line.get("assigned_rate"),
            "payment_id": line.get("payment_id")
        }
        adapted_record["data"]["line_items"].append(adapted_line)
    
    return adapted_record

def process_json_directory(json_dir_path):
    """Process all JSON files in a directory and generate EOBR reports"""
    # Setup
    folders = setup_folder_structure()
    initialize_excel_file(folders['current_excel'])
    initialize_excel_file(HISTORICAL_EXCEL_PATH)
    historical_duplicates, processed_control_numbers = load_historical_duplicates()
    
    # Get all JSON files in the directory
    json_files = glob.glob(os.path.join(json_dir_path, "*.json"))
    print(f"Found {len(json_files)} JSON files to process.")
    
    processed_count = 0
    skipped_count = 0
    
    for json_file_path in json_files:
        filename = os.path.basename(json_file_path)
        try:
            # Load and process JSON data
            with open(json_file_path, "r") as f:
                record = json.load(f)
            
            # Check if this is a valid record (has validation_status = PASS)
            if record.get("validation_status") != "PASS":
                print(f"Skipping file {filename}: Validation status is not PASS.")
                skipped_count += 1
                continue
            
            # Check if any service line has already been paid
            order_id = record.get("Order_ID")
            service_lines = record.get("service_lines", [])
            already_paid = False
            
            for line in service_lines:
                payment_id = line.get("payment_id", {})
                line_item_id = payment_id.get("line_item_id")
                
                if check_if_item_paid(line_item_id, order_id):
                    print(f"Skipping file {filename}: Line item {line_item_id} has already been paid.")
                    already_paid = True
                    break
            
            if already_paid:
                skipped_count += 1
                continue
            
            # Adapt record to expected format if needed
            adapted_record = adapt_record_format(record, filename)
            
            # Validate record
            if not validate_record(adapted_record):
                print(f"Skipping file {filename}: Validations did not pass.")
                skipped_count += 1
                continue
            
            # Process the record
            eobr_data = collect_additional_eobr_data(
                adapted_record, {}, historical_duplicates, processed_control_numbers
            )
            
            # Save to Excel
            append_to_excel(folders['current_excel'], eobr_data)
            append_to_excel(HISTORICAL_EXCEL_PATH, eobr_data)
            
            # Generate documents
            try:
                docx_path, pdf_path = generate_document(adapted_record, eobr_data, folders)
                processed_count += 1
                print(f"Generated EOBR {eobr_data['EOBR Number']}")
                
                # Update database with payment information
                update_database_with_payment(record, eobr_data)
                
            except Exception as e:
                print(f"Error generating documents for {filename}: {e}")
                skipped_count += 1
                
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            skipped_count += 1
    
    print(f"Processing complete. Processed: {processed_count}, Skipped: {skipped_count}")

def update_database_with_payment(record, eobr_data):
    """Update database with payment information for each line item"""
    order_id = record.get("Order_ID")
    eobr_number = eobr_data.get("EOBR Number")
    total_paid = eobr_data.get("Total").replace("$", "").replace(",", "")
    processed_date = datetime.now().strftime("%Y-%m-%d")
    
    for line in record.get("service_lines", []):
        payment_id = line.get("payment_id", {})
        line_item_id = payment_id.get("line_item_id")
        
        if line_item_id and order_id:
            update_payment_info(
                line_item_id=line_item_id,
                order_id=order_id,
                br_paid=str(line.get("assigned_rate", 0)),
                br_rate=float(line.get("assigned_rate", 0)),
                eobr_doc_no=eobr_number,
                hcfa_doc_no=eobr_number,
                br_date_processed=processed_date
            )

if __name__ == "__main__":
    process_json_directory(JSON_DIR_PATH)