"""
Migration script to add workflow columns to procurement_item_requests table
Run this script to update the database schema with the new workflow fields.
"""

from app import app
from models import db
import sqlite3
import os

def migrate_procurement_item_requests():
    """Add workflow columns to procurement_item_requests table"""
    
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
            
            # Define columns to add
            columns_to_add = [
                ('manager_approval_date', 'DATE'),
                ('manager_approver', 'VARCHAR(100)'),
                ('manager_approver_user_id', 'INTEGER'),
                ('manager_rejection_date', 'DATE'),
                ('manager_rejector', 'VARCHAR(100)'),
                ('manager_rejector_user_id', 'INTEGER'),
                ('manager_rejection_reason', 'TEXT'),
                ('manager_approval_reason', 'TEXT'),
                ('manager_approval_start_time', 'DATETIME'),
                ('manager_approval_end_time', 'DATETIME'),
                ('procurement_manager_approval_date', 'DATE'),
                ('procurement_manager_approver', 'VARCHAR(100)'),
                ('procurement_manager_approver_user_id', 'INTEGER'),
                ('procurement_manager_rejection_date', 'DATE'),
                ('procurement_manager_rejector', 'VARCHAR(100)'),
                ('procurement_manager_rejector_user_id', 'INTEGER'),
                ('procurement_manager_rejection_reason', 'TEXT'),
                ('procurement_manager_approval_reason', 'TEXT'),
                ('assigned_to_user_id', 'INTEGER'),
                ('assigned_by_user_id', 'INTEGER'),
                ('assignment_date', 'DATETIME'),
                ('completed_by_user_id', 'INTEGER'),
                ('completion_date', 'DATETIME'),
                ('completion_notes', 'TEXT'),
            ]
            
            # Add foreign key constraints separately (SQLite doesn't support adding FKs with ALTER TABLE)
            foreign_keys = [
                ('manager_approver_user_id', 'users', 'user_id'),
                ('manager_rejector_user_id', 'users', 'user_id'),
                ('procurement_manager_approver_user_id', 'users', 'user_id'),
                ('procurement_manager_rejector_user_id', 'users', 'user_id'),
                ('assigned_to_user_id', 'users', 'user_id'),
                ('assigned_by_user_id', 'users', 'user_id'),
                ('completed_by_user_id', 'users', 'user_id'),
            ]
            
            # Add missing columns
            added_count = 0
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        # SQLite doesn't support adding NOT NULL columns to existing tables easily
                        # So we'll add them as nullable
                        alter_sql = f"ALTER TABLE procurement_item_requests ADD COLUMN {column_name} {column_type}"
                        cursor.execute(alter_sql)
                        print(f"[OK] Added column: {column_name}")
                        added_count += 1
                    except sqlite3.OperationalError as e:
                        print(f"[ERROR] Error adding column {column_name}: {e}")
                else:
                    print(f"[SKIP] Column {column_name} already exists")
            
            # Update status column default if needed
            # Check current default value
            cursor.execute("PRAGMA table_info(procurement_item_requests)")
            columns_info = cursor.fetchall()
            status_default = None
            for col_info in columns_info:
                if col_info[1] == 'status':
                    status_default = col_info[4]
                    break
            
            # SQLite doesn't support ALTER COLUMN, so we'll update existing NULL statuses
            if status_default != 'Pending Manager Approval':
                cursor.execute("UPDATE procurement_item_requests SET status = 'Pending Manager Approval' WHERE status IS NULL OR status = ''")
                updated_count = cursor.rowcount
                if updated_count > 0:
                    print(f"[OK] Updated {updated_count} rows with default status")
            
            conn.commit()
            print(f"\n[OK] Migration completed! Added {added_count} new columns.")
            
        except Exception as e:
            conn.rollback()
            print(f"\n[ERROR] Migration failed: {e}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Procurement Item Requests Migration")
    print("=" * 60)
    print()
    migrate_procurement_item_requests()
    print()
    print("Migration script completed!")

