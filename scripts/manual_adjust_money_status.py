#!/usr/bin/env python3
"""Temporary script to manually adjust Money Spent and Available Balance in the latest snapshot.

This script allows you to manually set the money_spent and available_balance values
in the most recent CurrentMoneyEntry snapshot. This is useful for testing the new
logic where calculations are based on stored snapshot values plus new transactions.

WARNING: This will permanently modify data in the database!
Run manually from project root:
    python scripts/manual_adjust_money_status.py --money_spent 990.345 --available_balance 4526.648
    OR
    python scripts/manual_adjust_money_status.py  (will prompt for values)
"""

import os
import sys
import argparse
from decimal import Decimal

# Ensure project root is on sys.path so imports like `from app import app` work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from models import db, CurrentMoneyEntry


def adjust_money_status(money_spent_value, available_balance_value):
    """Manually adjust Money Spent and Available Balance in the latest snapshot"""
    
    with app.app_context():
        print("="*60)
        print("MANUALLY ADJUSTING MONEY STATUS")
        print("="*60)
        print()
        
        # Get the most recent snapshot
        latest_snapshot = CurrentMoneyEntry.query.filter(
            CurrentMoneyEntry.department == 'Procurement',
            CurrentMoneyEntry.entry_kind == 'snapshot',
            CurrentMoneyEntry.money_spent.isnot(None),
            CurrentMoneyEntry.available_balance.isnot(None)
        ).order_by(CurrentMoneyEntry.entry_date.desc()).first()
        
        if not latest_snapshot:
            print("⚠ No snapshot found with both money_spent and available_balance set.")
            print("   Creating a new snapshot entry...")
            
            # Create a new snapshot
            new_snapshot = CurrentMoneyEntry(
                department='Procurement',
                entry_kind='snapshot',
                completed_amount=None,
                item_requests_assigned_amount=None,
                completed_item_requests_amount=None,
                money_spent=Decimal(str(money_spent_value)),
                available_balance=Decimal(str(available_balance_value)),
                source='manual_script',
                note=f'Manually adjusted: Money Spent={money_spent_value}, Available Balance={available_balance_value}'
            )
            db.session.add(new_snapshot)
            db.session.commit()
            
            print(f"   ✓ Created new snapshot with ID={new_snapshot.id}")
            print(f"   ✓ Money Spent: {money_spent_value}")
            print(f"   ✓ Available Balance: {available_balance_value}")
            return
        
        # Show current values
        print(f"Current Snapshot (ID: {latest_snapshot.id})")
        print(f"  Entry Date: {latest_snapshot.entry_date}")
        print(f"  Current Money Spent: {latest_snapshot.money_spent}")
        print(f"  Current Available Balance: {latest_snapshot.available_balance}")
        print()
        
        # Update values
        old_money_spent = float(latest_snapshot.money_spent) if latest_snapshot.money_spent else 0.0
        old_available_balance = float(latest_snapshot.available_balance) if latest_snapshot.available_balance else 0.0
        
        latest_snapshot.money_spent = Decimal(str(money_spent_value))
        latest_snapshot.available_balance = Decimal(str(available_balance_value))
        latest_snapshot.note = f'Manually adjusted: Money Spent={old_money_spent}→{money_spent_value}, Available Balance={old_available_balance}→{available_balance_value}'
        
        db.session.commit()
        
        print("="*60)
        print("UPDATED VALUES")
        print("="*60)
        print(f"Money Spent: {old_money_spent} → {money_spent_value}")
        print(f"Available Balance: {old_available_balance} → {available_balance_value}")
        print()
        print("✓ Changes committed successfully")
        print()
        print("="*60)
        print("NOTE")
        print("="*60)
        print("Future calculations will use these values as the base.")
        print("New transactions will be added/subtracted from these base values.")


def main():
    """Main function with argument parsing and confirmation prompt"""
    parser = argparse.ArgumentParser(
        description='Manually adjust Money Spent and Available Balance in the latest snapshot'
    )
    parser.add_argument(
        '--money_spent',
        type=float,
        help='New Money Spent value (e.g., 990.345)'
    )
    parser.add_argument(
        '--available_balance',
        type=float,
        help='New Available Balance value (e.g., 4526.648)'
    )
    
    args = parser.parse_args()
    
    # Get values from arguments or prompt
    if args.money_spent is not None and args.available_balance is not None:
        money_spent = args.money_spent
        available_balance = args.available_balance
    else:
        print()
        print("Manual Money Status Adjustment")
        print("="*60)
        print()
        
        # Get current values to show
        with app.app_context():
            latest_snapshot = CurrentMoneyEntry.query.filter(
                CurrentMoneyEntry.department == 'Procurement',
                CurrentMoneyEntry.entry_kind == 'snapshot',
                CurrentMoneyEntry.money_spent.isnot(None),
                CurrentMoneyEntry.available_balance.isnot(None)
            ).order_by(CurrentMoneyEntry.entry_date.desc()).first()
            
            if latest_snapshot:
                print(f"Current values:")
                print(f"  Money Spent: {latest_snapshot.money_spent}")
                print(f"  Available Balance: {latest_snapshot.available_balance}")
                print()
        
        # Prompt for new values
        money_spent_input = input("Enter new Money Spent value (or press Enter to keep current): ").strip()
        available_balance_input = input("Enter new Available Balance value (or press Enter to keep current): ").strip()
        
        if not money_spent_input and not available_balance_input:
            print("No values provided. Exiting.")
            return
        
        if money_spent_input:
            try:
                money_spent = float(money_spent_input)
            except ValueError:
                print("Invalid Money Spent value. Must be a number.")
                return
        else:
            money_spent = float(latest_snapshot.money_spent) if latest_snapshot else 0.0
        
        if available_balance_input:
            try:
                available_balance = float(available_balance_input)
            except ValueError:
                print("Invalid Available Balance value. Must be a number.")
                return
        else:
            available_balance = float(latest_snapshot.available_balance) if latest_snapshot else 0.0
    
    # Show what will be changed
    print()
    print("="*60)
    print("CONFIRMATION")
    print("="*60)
    print(f"Money Spent will be set to: {money_spent}")
    print(f"Available Balance will be set to: {available_balance}")
    print()
    print("WARNING: This will modify the latest snapshot entry!")
    print("Future calculations will use these values as the base.")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        try:
            adjust_money_status(money_spent, available_balance)
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
        print("Adjustment cancelled.")


if __name__ == '__main__':
    main()
