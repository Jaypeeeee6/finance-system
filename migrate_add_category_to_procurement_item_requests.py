"""
Migration script to add category column to procurement_item_requests table
Run this script to update the database schema with the category field.
"""

from app import app
from models import db
import sqlite3
import os

def migrate_add_category():
    """Add category column to procurement_item_requests table"""
    
    with app.app_context():
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.name == 'nt':  # Windows
            db_path = db_path.replace('/', '\\')
        
        print(f"Connecting to database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='procurement_item_requests'")
            if not cursor.fetchone():
                print("Table 'procurement_item_requests' does not exist. Creating it...")
                # Create table with all columns
                db.create_all()
                print("✓ Table created with all columns")
                conn.close()
                return
            
            # Get existing columns
            cursor.execute("PRAGMA table_info(procurement_item_requests)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            print(f"Existing columns: {existing_columns}")
            
            # Add category column if it doesn't exist
            if 'category' not in existing_columns:
                try:
                    alter_sql = "ALTER TABLE procurement_item_requests ADD COLUMN category VARCHAR(100)"
                    cursor.execute(alter_sql)
                    conn.commit()
                    print("[OK] Added column: category")
                except sqlite3.OperationalError as e:
                    print(f"[ERROR] Error adding column category: {e}")
                    conn.rollback()
            else:
                print("[SKIP] Column category already exists")
            
            conn.commit()
            print("\n[OK] Migration completed!")
            
        except Exception as e:
            conn.rollback()
            print(f"\n[ERROR] Migration failed: {e}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Add Category Column to Procurement Item Requests Migration")
    print("=" * 60)
    print()
    migrate_add_category()
    print()
    print("Migration script completed!")

