#!/usr/bin/env python3
"""
Temporary migration script to add `from_store_no_receipt` column to
procurement_item_requests (SQLite). Safe to run multiple times.
"""
from sqlalchemy import text
import os
import sys
# Ensure project root is on sys.path so we can import app module
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from app import app, db

def column_exists(conn, table, column_name):
    res = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    # PRAGMA returns rows where the second column is the name
    return any(row[1] == column_name for row in res)

def add_column_if_missing():
    with app.app_context():
        conn = db.engine.connect()
        try:
            if column_exists(conn, 'procurement_item_requests', 'from_store_no_receipt'):
                print("Column 'from_store_no_receipt' already exists. Nothing to do.")
                return 0
            # SQLite ALTER TABLE to add the column with default 0 (false)
            conn.execute(text("ALTER TABLE procurement_item_requests ADD COLUMN from_store_no_receipt INTEGER DEFAULT 0"))
            print("Added column 'from_store_no_receipt' to procurement_item_requests.")
            return 0
        except Exception as e:
            print("Error adding column:", e)
            return 2
        finally:
            conn.close()

if __name__ == '__main__':
    raise SystemExit(add_column_if_missing())

