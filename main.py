import os
import json
from pathlib import Path
from datetime import datetime

# Import from modules
from config.settings import BASE_PATH, INPUT_JSON_PATH, HISTORICAL_EXCEL_PATH
from utils.validators import validate_record
from data.excel_manager import initialize_excel_file, load_historical_duplicates, append_to_excel
from processors.document_processor import generate_document
from processors.eobr_processor import collect_additional_eobr_data

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

def process_json_file(json_file_path):
    """Process JSON file and generate EOBR reports"""
    # Setup
    folders = setup_folder_structure()
    initialize_excel_file(folders['current_excel'])
    initialize_excel_file(HISTORICAL_EXCEL_PATH)
    historical_duplicates, processed_control_numbers = load_historical_duplicates()
    
    # Load and process JSON data
    with open(json_file_path, "r") as f:
        json_data = json.load(f)
    
    for record in json_data:
        # Validate record
        if not validate_record(record):
            print(f"Skipping file {record.get('order_id')}: Validations did not pass.")
            continue
        
        # Process the record
        eobr_data = collect_additional_eobr_data(
            record, {}, historical_duplicates, processed_control_numbers
        )
        
        # Save to Excel
        append_to_excel(folders['current_excel'], eobr_data)
        append_to_excel(HISTORICAL_EXCEL_PATH, eobr_data)
        
        # Generate documents
        try:
            docx_path, pdf_path = generate_document(record, eobr_data, folders)
            print(f"Generated EOBR {eobr_data['EOBR Number']}")
        except Exception as e:
            print(f"Error generating documents: {e}")

if __name__ == "__main__":
    process_json_file(INPUT_JSON_PATH)