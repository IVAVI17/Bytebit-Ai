import gspread
from google.oauth2.service_account import Credentials
import json
import os
import sqlite3
import tempfile

# ========= GOOGLE SHEETS CONFIG =========
SPREADSHEET_ID = "1LWhTGN3mNYqe7gtuRNAKBx8W87HtO5QmLPxv-8zWCc8"
SHEET_ANALYTICS = "analytics"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

def get_credentials():
    """Load Google credentials from config"""
    from config import GOOGLE_CREDENTIALS
    creds = Credentials.from_service_account_info(
        GOOGLE_CREDENTIALS, scopes=SCOPES
    )
    return creds

client = gspread.authorize(get_credentials())
ss = client.open_by_key(SPREADSHEET_ID)

def get_sheet(name):
    return ss.worksheet(name)

def init_analytics_sheet():
    """Create analytics sheet if it doesn't exist"""
    try:
        ss.worksheet(SHEET_ANALYTICS)
    except:
        ss.add_worksheet(SHEET_ANALYTICS, rows="1000", cols="15")
        sh = get_sheet(SHEET_ANALYTICS)
        sh.append_row([
            "patient_id",
            "patient_name",
            "age",
            "gender",
            "doctor_id",
            "doctor_name",
            "diagnosis",
            "visit_date",
            "medication",
            "medication_duration",
            "symptoms",
            "cure",
            "patient_notes",
            "doctor_notes"
        ])

def run_read_query(query: str):
    """
    Execute SQL queries against Google Sheets data using temporary SQLite database.
    Supports: Full SQL syntax (SELECT, WHERE, JOIN, GROUP BY, ORDER BY, aggregate functions, etc.)
    """
    # Safety: allow only SELECT queries
    if not query.lower().strip().startswith("select"):
        raise Exception("Only SELECT queries are allowed")
    
    init_analytics_sheet()
    
    sheet = get_sheet(SHEET_ANALYTICS)
    all_records = sheet.get_all_records()
    
    # Create temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table and populate with data
        if all_records:
            columns = list(all_records[0].keys())
            # Create table with all columns as TEXT to accommodate any data
            create_table_sql = f"CREATE TABLE analytics ({', '.join([f'{col} TEXT' for col in columns])})"
            cursor.execute(create_table_sql)
            
            # Insert data
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO analytics VALUES ({placeholders})"
            for record in all_records:
                values = [str(record.get(col, '')) for col in columns]
                cursor.execute(insert_sql, values)
            
            conn.commit()
        
        # Execute the user's query
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Get column names from cursor description
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            result_dicts = [dict(zip(columns, row)) for row in rows]
        else:
            result_dicts = []
        
        conn.close()
    finally:
        # Clean up temporary database file
        if os.path.exists(db_path):
            os.remove(db_path)
    
    return result_dicts



def add_record(record_dict):
    """Add a new record to analytics sheet"""
    init_analytics_sheet()
    sheet = get_sheet(SHEET_ANALYTICS)
    headers = sheet.row_values(1)
    
    row = [record_dict.get(header, "") for header in headers]
    sheet.append_row(row)

def update_record(record_id, updates):
    """Update a record by patient_id"""
    init_analytics_sheet()
    sheet = get_sheet(SHEET_ANALYTICS)
    all_records = sheet.get_all_records()
    
    for idx, record in enumerate(all_records, start=2):
        if record.get("patient_id") == record_id:
            headers = sheet.row_values(1)
            for col_idx, header in enumerate(headers, start=1):
                if header in updates:
                    sheet.update_cell(idx, col_idx, updates[header])
            break