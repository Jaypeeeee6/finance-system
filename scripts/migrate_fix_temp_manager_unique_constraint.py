#!/usr/bin/env python3
"""
Migration script to fix the unique constraint on department_temporary_managers table.
Changes from unique(department) to unique(department, request_type).
Also ensures include_procurement_approvals column exists.
This requires recreating the table in SQLite.
Safe to run multiple times.
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
    return any(row[1] == column_name for row in res)

def table_exists(conn, table_name):
    res = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")).fetchall()
    return len(res) > 0

def index_exists(conn, index_name):
    res = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")).fetchall()
    return len(res) > 0

def recreate_table_with_composite_constraint():
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            if not table_exists(conn, 'department_temporary_managers'):
                print("Table 'department_temporary_managers' does not exist. Creating it...")
                # Create table with new structure
                conn.execute(text("""
                    CREATE TABLE department_temporary_managers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_type VARCHAR(100) NOT NULL,
                        department VARCHAR(100) NOT NULL,
                        temporary_manager_id INTEGER NOT NULL,
                        set_by_user_id INTEGER,
                        set_at DATETIME,
                        include_procurement_approvals INTEGER DEFAULT 0,
                        FOREIGN KEY (temporary_manager_id) REFERENCES users(user_id),
                        FOREIGN KEY (set_by_user_id) REFERENCES users(user_id),
                        UNIQUE(department, request_type)
                    )
                """))
                trans.commit()
                print("Successfully created table with composite unique constraint.")
                return 0
            
            # Check if request_type column exists
            if not column_exists(conn, 'department_temporary_managers', 'request_type'):
                print("Adding request_type column first...")
                conn.execute(text("ALTER TABLE department_temporary_managers ADD COLUMN request_type VARCHAR(100)"))
                # Set default for existing rows
                existing_rows = conn.execute(text("SELECT COUNT(*) FROM department_temporary_managers")).scalar()
                if existing_rows > 0:
                    print(f"Found {existing_rows} existing rows. Setting default request_type to 'Finance Payment Request'.")
                    conn.execute(text("UPDATE department_temporary_managers SET request_type = 'Finance Payment Request' WHERE request_type IS NULL"))
                trans.commit()
            
            # Check if include_procurement_approvals column exists, add it if not
            if not column_exists(conn, 'department_temporary_managers', 'include_procurement_approvals'):
                print("Adding include_procurement_approvals column...")
                conn.execute(text("ALTER TABLE department_temporary_managers ADD COLUMN include_procurement_approvals INTEGER DEFAULT 0"))
                trans.commit()
            
            # Check if the composite unique constraint already exists
            if index_exists(conn, 'unique_dept_request_type'):
                print("Composite unique constraint 'unique_dept_request_type' already exists. Nothing to do.")
                trans.commit()
                return 0
            
            print("Recreating table with composite unique constraint...")
            
            # Step 1: Create backup table with new structure
            conn.execute(text("""
                CREATE TABLE department_temporary_managers_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_type VARCHAR(100) NOT NULL,
                    department VARCHAR(100) NOT NULL,
                    temporary_manager_id INTEGER NOT NULL,
                    set_by_user_id INTEGER,
                    set_at DATETIME,
                    include_procurement_approvals INTEGER DEFAULT 0,
                    FOREIGN KEY (temporary_manager_id) REFERENCES users(user_id),
                    FOREIGN KEY (set_by_user_id) REFERENCES users(user_id),
                    UNIQUE(department, request_type)
                )
            """))
            
            # Step 2: Copy data from old table to new table
            # First, ensure all rows have request_type set
            conn.execute(text("UPDATE department_temporary_managers SET request_type = 'Finance Payment Request' WHERE request_type IS NULL"))
            
            # Check if include_procurement_approvals exists in old table
            has_include_procurement = column_exists(conn, 'department_temporary_managers', 'include_procurement_approvals')
            
            # Copy data - include include_procurement_approvals if it exists, otherwise use default 0
            if has_include_procurement:
                conn.execute(text("""
                    INSERT INTO department_temporary_managers_new 
                    (id, request_type, department, temporary_manager_id, set_by_user_id, set_at, include_procurement_approvals)
                    SELECT id, request_type, department, temporary_manager_id, set_by_user_id, set_at, COALESCE(include_procurement_approvals, 0)
                    FROM department_temporary_managers
                """))
            else:
                conn.execute(text("""
                    INSERT INTO department_temporary_managers_new 
                    (id, request_type, department, temporary_manager_id, set_by_user_id, set_at, include_procurement_approvals)
                    SELECT id, request_type, department, temporary_manager_id, set_by_user_id, set_at, 0
                    FROM department_temporary_managers
                """))
            
            # Step 3: Drop old table
            conn.execute(text("DROP TABLE department_temporary_managers"))
            
            # Step 4: Rename new table to original name
            conn.execute(text("ALTER TABLE department_temporary_managers_new RENAME TO department_temporary_managers"))
            
            trans.commit()
            print("Successfully recreated table with composite unique constraint (department, request_type).")
            print("You can now assign different temporary managers for different request types in the same department.")
            return 0
            
        except Exception as e:
            trans.rollback()
            print(f"Error recreating table: {e}")
            import traceback
            traceback.print_exc()
            return 2
        finally:
            conn.close()

if __name__ == '__main__':
    raise SystemExit(recreate_table_with_composite_constraint())
