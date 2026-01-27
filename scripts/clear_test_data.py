#!/usr/bin/env python3
"""Temporary script to clear test data for Current Money Status testing.

This script will:
1. Delete all ProcurementItemRequest records (all item requests)
2. Delete all PaymentRequest records from Procurement department with request_type='Bank money'
3. Delete all CurrentMoneyEntry records EXCEPT the one with id=1

WARNING: This will permanently delete data from the database!
Run manually from project root:
    python scripts/clear_test_data.py
"""

import os
import sys

# Ensure project root is on sys.path so imports like `from app import app` work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from models import db, PaymentRequest, ProcurementItemRequest, CurrentMoneyEntry


def clear_test_data():
    """Clear test data for Current Money Status testing"""
    
    with app.app_context():
        print("="*60)
        print("CLEARING TEST DATA FOR CURRENT MONEY STATUS")
        print("="*60)
        print()
        
        # 1. Delete all ProcurementItemRequest records
        print("1. Deleting all ProcurementItemRequest records...")
        item_requests_count = ProcurementItemRequest.query.count()
        if item_requests_count > 0:
            ProcurementItemRequest.query.delete()
            print(f"   ✓ Deleted {item_requests_count} item request(s)")
        else:
            print("   ✓ No item requests to delete")
        
        # 2. Delete all PaymentRequest records from Procurement department with request_type='Bank money'
        print()
        print("2. Deleting PaymentRequest records from Procurement department with request_type='Bank money'...")
        
        # Find all Bank money payment requests from Procurement department
        bank_money_requests = PaymentRequest.query.filter(
            PaymentRequest.department == 'Procurement',
            PaymentRequest.request_type == 'Bank money'
        ).all()
        
        bank_money_count = len(bank_money_requests)
        if bank_money_count > 0:
            # Delete them
            for req in bank_money_requests:
                db.session.delete(req)
            print(f"   ✓ Deleted {bank_money_count} Bank money payment request(s) from Procurement department")
        else:
            print("   ✓ No Bank money payment requests to delete")
        
        # 3. Delete all CurrentMoneyEntry records EXCEPT id=1
        print()
        print("3. Deleting CurrentMoneyEntry records (keeping id=1)...")
        money_entries = CurrentMoneyEntry.query.filter(
            CurrentMoneyEntry.id != 1
        ).all()
        
        money_entries_count = len(money_entries)
        if money_entries_count > 0:
            for entry in money_entries:
                db.session.delete(entry)
            print(f"   ✓ Deleted {money_entries_count} CurrentMoneyEntry record(s) (kept id=1)")
        else:
            print("   ✓ No CurrentMoneyEntry records to delete (id=1 already exists or is the only one)")
        
        # Commit all deletions
        print()
        print("Committing changes to database...")
        db.session.commit()
        print("   ✓ Changes committed successfully")
        
        # Verify deletions
        print()
        print("="*60)
        print("VERIFICATION")
        print("="*60)
        remaining_item_requests = ProcurementItemRequest.query.count()
        remaining_bank_money = PaymentRequest.query.filter(
            PaymentRequest.department == 'Procurement',
            PaymentRequest.request_type == 'Bank money'
        ).count()
        remaining_money_entries = CurrentMoneyEntry.query.count()
        entry_id_1 = CurrentMoneyEntry.query.filter_by(id=1).first()
        
        print(f"Remaining item requests: {remaining_item_requests}")
        print(f"Remaining Bank money payment requests: {remaining_bank_money}")
        print(f"Remaining CurrentMoneyEntry records: {remaining_money_entries}")
        if entry_id_1:
            print(f"✓ CurrentMoneyEntry id=1 preserved: {entry_id_1}")
        else:
            print("⚠ CurrentMoneyEntry id=1 does not exist")
        
        print()
        print("="*60)
        print("CLEANUP COMPLETE!")
        print("="*60)


def main():
    """Main function with confirmation prompt"""
    print()
    print("WARNING: This script will permanently delete:")
    print("  - ALL ProcurementItemRequest records")
    print("  - ALL PaymentRequest records from Procurement department with request_type='Bank money'")
    print("  - ALL CurrentMoneyEntry records EXCEPT id=1")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        try:
            clear_test_data()
        except Exception as e:
            print()
            print("="*60)
            print("ERROR OCCURRED!")
            print("="*60)
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            print()
            print("Changes have been rolled back.")
    else:
        print("Cleanup cancelled.")


if __name__ == '__main__':
    main()
