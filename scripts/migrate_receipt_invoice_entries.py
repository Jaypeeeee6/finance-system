"""
Migration script to move receipt and invoice data from JSON to database tables
for procurement item requests.

Run this script to migrate existing data or verify migration status.
"""

import sqlite3
import json
import os
import sys

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_receipt_invoice_entries():
    """Migrate receipt and invoice entries from JSON to database tables"""
    
    # Get database path from config
    from config import Config
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    if os.name == 'nt':  # Windows
        db_path = db_path.replace('/', '\\')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='procurement_receipt_entries'
        """)
        if not cursor.fetchone():
            print("Creating procurement_receipt_entries table...")
            cursor.execute("""
                CREATE TABLE procurement_receipt_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_request_id INTEGER NOT NULL,
                    filename VARCHAR(500) NOT NULL,
                    amount NUMERIC(10, 3) NOT NULL,
                    reference_number VARCHAR(100) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY (item_request_id) REFERENCES procurement_item_requests(id)
                )
            """)
            conn.commit()
            print("[OK] Created 'procurement_receipt_entries' table")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='procurement_invoice_entries'
        """)
        if not cursor.fetchone():
            print("Creating procurement_invoice_entries table...")
            cursor.execute("""
                CREATE TABLE procurement_invoice_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_request_id INTEGER NOT NULL,
                    filename VARCHAR(500) NOT NULL,
                    amount NUMERIC(10, 3) NOT NULL,
                    items TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY (item_request_id) REFERENCES procurement_item_requests(id)
                )
            """)
            conn.commit()
            print("[OK] Created 'procurement_invoice_entries' table")
        
        # Check current counts
        cursor.execute("SELECT COUNT(*) FROM procurement_receipt_entries")
        receipt_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM procurement_invoice_entries")
        invoice_count = cursor.fetchone()[0]
        
        print(f"\nCurrent database counts:")
        print(f"  Receipt entries: {receipt_count}")
        print(f"  Invoice entries: {invoice_count}")
        
        # Check for data to migrate
        cursor.execute("""
            SELECT id, receipt_path, invoice_path 
            FROM procurement_item_requests 
            WHERE receipt_path IS NOT NULL OR invoice_path IS NOT NULL
        """)
        items_to_migrate = cursor.fetchall()
        
        print(f"\nFound {len(items_to_migrate)} item requests with receipt_path or invoice_path data")
        
        if len(items_to_migrate) == 0:
            print("No existing JSON data found to migrate.")
            print("Tables will populate automatically when new receipts/invoices are uploaded.")
            conn.close()
            return
        
        # Check if migration has already been done
        if receipt_count > 0 or invoice_count > 0:
            print(f"\n[!] Warning: Tables already contain data ({receipt_count} receipts, {invoice_count} invoices)")
            response = input("Do you want to continue and migrate additional data? (y/n): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                conn.close()
                return
        
        migrated_receipts = 0
        migrated_invoices = 0
        errors = []
        
        print("\nStarting migration...")
        for item_id, receipt_path, invoice_path in items_to_migrate:
            # Migrate receipts
            if receipt_path:
                try:
                    receipt_data = json.loads(receipt_path)
                    if isinstance(receipt_data, list):
                        for entry in receipt_data:
                            if isinstance(entry, dict):
                                filename = entry.get('filename') or entry.get('file') or entry.get('name')
                                amount = entry.get('amount') or 0
                                ref_num = entry.get('reference_number') or entry.get('referenceNumber') or ''
                                if filename:
                                    # Check if entry already exists
                                    cursor.execute("""
                                        SELECT COUNT(*) FROM procurement_receipt_entries 
                                        WHERE item_request_id = ? AND filename = ?
                                    """, (item_id, filename))
                                    if cursor.fetchone()[0] == 0:
                                        cursor.execute("""
                                            INSERT INTO procurement_receipt_entries 
                                            (item_request_id, filename, amount, reference_number, created_at, updated_at)
                                            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                                        """, (item_id, filename, amount, ref_num))
                                        migrated_receipts += 1
                            elif isinstance(entry, str):
                                # Check if entry already exists
                                cursor.execute("""
                                    SELECT COUNT(*) FROM procurement_receipt_entries 
                                    WHERE item_request_id = ? AND filename = ?
                                """, (item_id, entry))
                                if cursor.fetchone()[0] == 0:
                                    cursor.execute("""
                                        INSERT INTO procurement_receipt_entries 
                                        (item_request_id, filename, amount, reference_number, created_at, updated_at)
                                        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                                    """, (item_id, entry, 0, ''))
                                    migrated_receipts += 1
                except Exception as e:
                    error_msg = f"Item {item_id} receipts: {str(e)}"
                    errors.append(error_msg)
                    print(f"  [!] {error_msg}")
            
            # Migrate invoices
            if invoice_path:
                try:
                    invoice_data = json.loads(invoice_path)
                    if isinstance(invoice_data, list):
                        for entry in invoice_data:
                            if isinstance(entry, dict):
                                filename = entry.get('filename') or entry.get('file') or entry.get('name')
                                amount = entry.get('amount') or 0
                                items = entry.get('items') or []
                                if filename:
                                    # Check if entry already exists
                                    cursor.execute("""
                                        SELECT COUNT(*) FROM procurement_invoice_entries 
                                        WHERE item_request_id = ? AND filename = ?
                                    """, (item_id, filename))
                                    if cursor.fetchone()[0] == 0:
                                        items_json = json.dumps(items) if isinstance(items, list) else '[]'
                                        cursor.execute("""
                                            INSERT INTO procurement_invoice_entries 
                                            (item_request_id, filename, amount, items, created_at, updated_at)
                                            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                                        """, (item_id, filename, amount, items_json))
                                        migrated_invoices += 1
                            elif isinstance(entry, str):
                                # Check if entry already exists
                                cursor.execute("""
                                    SELECT COUNT(*) FROM procurement_invoice_entries 
                                    WHERE item_request_id = ? AND filename = ?
                                """, (item_id, entry))
                                if cursor.fetchone()[0] == 0:
                                    cursor.execute("""
                                        INSERT INTO procurement_invoice_entries 
                                        (item_request_id, filename, amount, items, created_at, updated_at)
                                        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                                    """, (item_id, entry, 0, '[]'))
                                    migrated_invoices += 1
                except Exception as e:
                    error_msg = f"Item {item_id} invoices: {str(e)}"
                    errors.append(error_msg)
                    print(f"  [!] {error_msg}")
        
        if migrated_receipts > 0 or migrated_invoices > 0:
            conn.commit()
            print(f"\n✓ Migration completed successfully!")
            print(f"  Migrated {migrated_receipts} receipt entries")
            print(f"  Migrated {migrated_invoices} invoice entries")
        else:
            print("\n✓ No new data to migrate (all entries already exist in database)")
        
        if errors:
            print(f"\n[!] {len(errors)} error(s) occurred during migration (see above)")
        
        # Show final counts
        cursor.execute("SELECT COUNT(*) FROM procurement_receipt_entries")
        final_receipt_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM procurement_invoice_entries")
        final_invoice_count = cursor.fetchone()[0]
        
        print(f"\nFinal database counts:")
        print(f"  Receipt entries: {final_receipt_count}")
        print(f"  Invoice entries: {final_invoice_count}")
        
    except Exception as e:
        print(f"\n[X] Error during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Procurement Receipt/Invoice Entries Migration Script")
    print("=" * 60)
    migrate_receipt_invoice_entries()
    print("\n" + "=" * 60)
