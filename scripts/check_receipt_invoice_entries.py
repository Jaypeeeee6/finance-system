"""
Simple script to check and display receipt and invoice entries in the database
"""

import sqlite3
import os
import sys

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_entries():
    """Check and display receipt and invoice entries"""
    
    # Get database path from config
    from config import Config
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    if os.name == 'nt':  # Windows
        db_path = db_path.replace('/', '\\')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    print(f"Database: {db_path}\n")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check receipt entries
        cursor.execute("SELECT COUNT(*) FROM procurement_receipt_entries")
        receipt_count = cursor.fetchone()[0]
        print(f"Receipt Entries: {receipt_count}")
        
        if receipt_count > 0:
            cursor.execute("""
                SELECT id, item_request_id, filename, amount, reference_number, created_at
                FROM procurement_receipt_entries
                ORDER BY item_request_id, id
                LIMIT 10
            """)
            print("\nFirst 10 Receipt Entries:")
            print("-" * 100)
            print(f"{'ID':<5} {'Request ID':<12} {'Filename':<40} {'Amount':<12} {'Ref Number':<15} {'Created':<20}")
            print("-" * 100)
            for row in cursor.fetchall():
                print(f"{row[0]:<5} {row[1]:<12} {row[2][:40]:<40} {row[3]:<12} {row[4]:<15} {row[5]:<20}")
            if receipt_count > 10:
                print(f"... and {receipt_count - 10} more receipt entries")
        
        # Check invoice entries
        cursor.execute("SELECT COUNT(*) FROM procurement_invoice_entries")
        invoice_count = cursor.fetchone()[0]
        print(f"\n\nInvoice Entries: {invoice_count}")
        
        if invoice_count > 0:
            cursor.execute("""
                SELECT id, item_request_id, filename, amount, items, created_at
                FROM procurement_invoice_entries
                ORDER BY item_request_id, id
                LIMIT 10
            """)
            print("\nFirst 10 Invoice Entries:")
            print("-" * 100)
            print(f"{'ID':<5} {'Request ID':<12} {'Filename':<40} {'Amount':<12} {'Items':<20} {'Created':<20}")
            print("-" * 100)
            for row in cursor.fetchall():
                items_preview = row[4][:20] if row[4] else ''
                print(f"{row[0]:<5} {row[1]:<12} {row[2][:40]:<40} {row[3]:<12} {items_preview:<20} {row[5]:<20}")
            if invoice_count > 10:
                print(f"... and {invoice_count - 10} more invoice entries")
        
        # Show summary by item request
        print("\n\nSummary by Item Request:")
        print("-" * 60)
        cursor.execute("""
            SELECT 
                item_request_id,
                COUNT(DISTINCT r.id) as receipt_count,
                COUNT(DISTINCT i.id) as invoice_count
            FROM procurement_item_requests p
            LEFT JOIN procurement_receipt_entries r ON p.id = r.item_request_id
            LEFT JOIN procurement_invoice_entries i ON p.id = i.item_request_id
            WHERE r.id IS NOT NULL OR i.id IS NOT NULL
            GROUP BY item_request_id
            ORDER BY item_request_id
            LIMIT 20
        """)
        print(f"{'Request ID':<12} {'Receipts':<10} {'Invoices':<10}")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"{row[0]:<12} {row[1] or 0:<10} {row[2] or 0:<10}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 100)
    print("Receipt and Invoice Entries Check")
    print("=" * 100)
    check_entries()
    print("\n" + "=" * 100)
