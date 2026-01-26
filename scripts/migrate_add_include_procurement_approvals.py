#!/usr/bin/env python3
"""
Migration script to add include_procurement_approvals column to department_temporary_managers table.
This column allows temporary managers for Procurement department to also handle Procurement Manager Approval
and Final Approval steps for item requests from ALL departments.
"""

import sqlite3
import os
import sys

def migrate():
    # Get database path from environment or use default
    db_path = os.environ.get('DATABASE_PATH', 'instance/payment_system.db')
    
    # Handle Windows paths
    if os.name == 'nt':
        db_path = db_path.replace('/', '\\')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(department_temporary_managers)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'include_procurement_approvals' in columns:
            print("✓ Column 'include_procurement_approvals' already exists. Migration not needed.")
            conn.close()
            return
        
        # Add the new column
        print("Adding 'include_procurement_approvals' column to department_temporary_managers table...")
        cursor.execute("""
            ALTER TABLE department_temporary_managers 
            ADD COLUMN include_procurement_approvals INTEGER DEFAULT 0
        """)
        
        conn.commit()
        print("✓ Successfully added 'include_procurement_approvals' column")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(department_temporary_managers)")
        columns_after = [row[1] for row in cursor.fetchall()]
        if 'include_procurement_approvals' in columns_after:
            print("✓ Verification: Column exists in table")
        else:
            print("✗ Warning: Column was not found after creation")
        
        conn.close()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if conn:
            conn.rollback()
            conn.close()
        sys.exit(1)

if __name__ == '__main__':
    migrate()
