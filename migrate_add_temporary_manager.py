"""
Migration script to add temporary_manager_id field to payment_requests table
This script adds the new column for the IT Department manager reassignment feature.
"""

from app import app
from models import db
from sqlalchemy import text

def migrate_database():
    """Add temporary_manager_id column to payment_requests table"""
    
    with app.app_context():
        print("="*60)
        print("Database Migration: Add Temporary Manager Field")
        print("="*60)
        print("\nThis migration adds the 'temporary_manager_id' column to the payment_requests table.")
        print("This enables IT Department staff to temporarily reassign managers for specific requests.")
        print()
        
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('payment_requests')]
            
            if 'temporary_manager_id' in columns:
                print("[OK] Column 'temporary_manager_id' already exists.")
                print("  Migration already applied.")
                return
            
            # Add the new column
            print("Adding 'temporary_manager_id' column to payment_requests table...")
            
            # SQLite specific migration
            with db.engine.connect() as connection:
                connection.execute(text("""
                    ALTER TABLE payment_requests 
                    ADD COLUMN temporary_manager_id INTEGER REFERENCES users(user_id)
                """))
                connection.commit()
            
            print("[OK] Column 'temporary_manager_id' added successfully.")
            print("\n" + "="*60)
            print("MIGRATION COMPLETE!")
            print("="*60)
            print("\nThe temporary manager reassignment feature is now available for IT Department users.")
            print("IT Staff can now temporarily reassign managers for requests with 'Pending Manager Approval' status.")
            print()
            
        except Exception as e:
            print(f"[ERROR] Error during migration: {e}")
            print("\nNote: If the column already exists, this error can be safely ignored.")
            print("Please restart the application.")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        # Auto-confirm if --auto flag is passed
        migrate_database()
    else:
        print("\nWARNING: This will modify your database schema.")
        print("Ensure you have a backup of your database before proceeding.\n")
        response = input("Do you want to continue? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            migrate_database()
        else:
            print("Migration cancelled.")

