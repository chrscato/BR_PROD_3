import sqlite3
from pathlib import Path
from config.settings import DB_PATH

def reset_payment_fields(line_item_ids):
    """
    Reset payment fields to NULL for specified line items
    
    Args:
        line_item_ids (list): List of line item IDs to reset
    """
    if not Path(DB_PATH).exists():
        print(f"Error: Database file not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Update the line_items table
        cursor.execute('''
        UPDATE line_items SET 
            BR_paid = NULL,
            BR_rate = NULL,
            EOBR_doc_no = NULL,
            HCFA_doc_no = NULL,
            BR_date_processed = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id IN ({})
        '''.format(','.join('?' * len(line_item_ids))), line_item_ids)
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        print(f"Reset payment info for {rows_affected} line items")
        
        # Verify the changes
        cursor.execute('''
        SELECT id, Order_ID, CPT, BR_paid, BR_rate, EOBR_doc_no 
        FROM line_items 
        WHERE id IN ({})
        '''.format(','.join('?' * len(line_item_ids))), line_item_ids)
        
        rows = cursor.fetchall()
        print("\nUpdated records:")
        for row in rows:
            print(f"  ID: {row[0]}, Order: {row[1]}, CPT: {row[2]}, Paid: {row[3]}, Rate: {row[4]}, EOBR: {row[5]}")
            
    except Exception as e:
        print(f"Error resetting payment info: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # List of line item IDs to reset
    line_item_ids = [
        # Add your line item IDs here
        # Example:
         21718,
         21717,
    ]
    
    if not line_item_ids:
        print("Please add line item IDs to the list in the script")
    else:
        print(f"Resetting payment fields for {len(line_item_ids)} line items...")
        reset_payment_fields(line_item_ids) 