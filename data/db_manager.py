import sqlite3
import os
from pathlib import Path
from config.settings import DB_PATH

def initialize_database():
    """Initialize SQLite database if it doesn't exist"""
    if not Path(DB_PATH).exists():
        # Create the directory if it doesn't exist
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database and create tables
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create table for tracking paid items
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS paid_items (
            line_item_id INTEGER,
            order_id TEXT,
            BR_paid TEXT,
            BR_rate REAL,
            EOBR_doc_no TEXT,
            HCFA_doc_no TEXT,
            BR_date_processed TEXT,
            PRIMARY KEY (line_item_id, order_id)
        )
        ''')
        
        conn.commit()
        conn.close()

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
    
    initialize_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if the line item exists and has been paid
    cursor.execute(
        'SELECT BR_paid FROM paid_items WHERE line_item_id = ? AND order_id = ? AND BR_paid IS NOT NULL',
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
    """
    if not line_item_id or not order_id:
        return
    
    initialize_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert or update the payment information
    cursor.execute('''
    INSERT OR REPLACE INTO paid_items (
        line_item_id, order_id, BR_paid, BR_rate, EOBR_doc_no, HCFA_doc_no, BR_date_processed
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (line_item_id, order_id, br_paid, br_rate, eobr_doc_no, hcfa_doc_no, br_date_processed))
    
    conn.commit()
    conn.close() 