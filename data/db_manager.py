import sqlite3
import os
from pathlib import Path
from config.settings import DB_PATH

def initialize_database():
    """Initialize SQLite database connection"""
    if not Path(DB_PATH).exists():
        print(f"Error: Database file not found at {DB_PATH}")
        return False
    
    # Just make sure the database is accessible
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the line_items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='line_items'")
        if not cursor.fetchone():
            print("Warning: line_items table not found in database")
            conn.close()
            return False
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

def check_if_item_paid(line_item_id, order_id):
    """
    Check if a line item has already been paid
    
    Args:
        line_item_id (int): The line item ID
        order_id (str): The order ID
        
    Returns:
        bool: True if the item has been paid, False otherwise
    """
    if not line_item_id or not order_id:
        return False
    
    if not initialize_database():
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if the line item exists and has been paid
    cursor.execute(
        'SELECT BR_paid FROM line_items WHERE id = ? AND Order_ID = ? AND BR_paid IS NOT NULL',
        (line_item_id, order_id)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def update_payment_info(line_item_id, order_id, br_paid, br_rate, eobr_doc_no, hcfa_doc_no, br_date_processed):
    """
    Update payment information for a line item
    
    Args:
        line_item_id (int): The line item ID
        order_id (str): The order ID
        br_paid (str): The amount paid
        br_rate (float): The rate applied
        eobr_doc_no (str): The EOBR document number
        hcfa_doc_no (str): The HCFA document number
        br_date_processed (str): The date the payment was processed
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    if not line_item_id or not order_id:
        return False
    
    if not initialize_database():
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Update the line_items table
        cursor.execute('''
        UPDATE line_items SET 
            BR_paid = ?,
            BR_rate = ?,
            EOBR_doc_no = ?,
            HCFA_doc_no = ?,
            BR_date_processed = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND Order_ID = ?
        ''', (br_paid, br_rate, eobr_doc_no, hcfa_doc_no, br_date_processed, line_item_id, order_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        print(f"Updated payment info for line item {line_item_id}, order {order_id}: {rows_affected} row(s) affected")
        return rows_affected > 0
        
    except Exception as e:
        print(f"Error updating payment info: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def list_line_items(order_id=None):
    """List line items in the database, optionally filtered by order_id"""
    if not initialize_database():
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if order_id:
            cursor.execute('SELECT id, Order_ID, CPT, BR_paid, BR_rate, EOBR_doc_no FROM line_items WHERE Order_ID = ?', (order_id,))
        else:
            cursor.execute('SELECT id, Order_ID, CPT, BR_paid, BR_rate, EOBR_doc_no FROM line_items LIMIT 10')
        
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} line items:")
        for row in rows:
            print(f"  ID: {row[0]}, Order: {row[1]}, CPT: {row[2]}, Paid: {row[3]}, Rate: {row[4]}, EOBR: {row[5]}")
            
    except Exception as e:
        print(f"Error listing line items: {e}")
    finally:
        conn.close() 