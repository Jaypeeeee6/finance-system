#!/usr/bin/env python3
"""Temporary script to insert a manual adjustment into current_money_entries.

Run manually from project root:
    python scripts/add_manual_adjustment.py --amount 100.5 --note "Add card topup" --user_id 1

The script inserts a row with entry_kind='manual_adjustment' and, by default,
sets affects_reports=True so the amount is included in the frontend Available Balance.
"""
import os
import sys
from decimal import Decimal
import argparse
from datetime import datetime

# Ensure project root is on sys.path so imports like `from app import app` work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from models import db, CurrentMoneyEntry, PaymentRequest, ProcurementItemRequest
from sqlalchemy import func


def parse_args():
    p = argparse.ArgumentParser(description='Insert manual adjustment into current_money_entries')
    p.add_argument('--amount', required=True, help='Adjustment amount (positive or negative). Example: 100.500')
    p.add_argument('--note', default=None, help='Optional note for this adjustment')
    p.add_argument('--user_id', type=int, default=None, help='User id to store in created_by (optional)')
    p.add_argument('--department', default='Procurement', help='Department this adjustment applies to (default: Procurement)')
    p.add_argument('--affects_reports', action='store_true', help='If set, the adjustment will be included in available_balance calculations')
    p.add_argument('--include_in_balance', action='store_true', help='If set, the adjustment will be included in runtime available_balance calculation (separate from reports)')
    return p.parse_args()


def insert_adjustment(amount_decimal: Decimal, department: str, note: str, user_id: int, affects_reports: bool, include_in_balance: bool):
    with app.app_context():
        entry = CurrentMoneyEntry(
            department=department,
            entry_kind='manual_adjustment',
            completed_amount=None,
            item_requests_assigned_amount=None,
            completed_item_requests_amount=None,
            money_spent=None,
            available_balance=None,
            adjustment_amount=amount_decimal,
            affects_reports=bool(affects_reports),
            include_in_balance=bool(include_in_balance),
            source='manual_script',
            note=note,
            created_by=user_id
        )
        db.session.add(entry)
        db.session.commit()
        print(f'Inserted CurrentMoneyEntry id={entry.id} adjustment_amount={entry.adjustment_amount} affects_reports={entry.affects_reports} include_in_balance={entry.include_in_balance}')

        # Print the newly computed available balance (mirrors app logic)
        bank_money_requests = PaymentRequest.query.filter(
            PaymentRequest.department == department,
            PaymentRequest.request_type == 'Bank money',
            PaymentRequest.is_archived == False
        ).all()
        completed_requests_bm = [r for r in bank_money_requests if r.status == 'Completed']
        completed_amount_bm = sum(float(r.amount) for r in completed_requests_bm)

        completed_item_requests = ProcurementItemRequest.query.filter_by(status='Completed').all()
        completed_item_requests_amount = sum(float(r.invoice_amount) for r in completed_item_requests if r.invoice_amount is not None)

        adjustments_sum = db.session.query(func.coalesce(func.sum(CurrentMoneyEntry.adjustment_amount), 0)).filter(
            CurrentMoneyEntry.department == department,
            CurrentMoneyEntry.entry_kind == 'manual_adjustment',
            CurrentMoneyEntry.include_in_balance == True
        ).scalar() or 0
        adjustments_sum = float(adjustments_sum)

        available_balance = completed_amount_bm - completed_item_requests_amount + adjustments_sum
        print(f'New computed available_balance for {department}: {available_balance:.3f}')


def main():
    args = parse_args()
    try:
        amt = Decimal(args.amount)
    except Exception as exc:
        print('Invalid amount. Use a numeric value with up to 3 decimal places, e.g. 100.500')
        raise

    insert_adjustment(amount_decimal=amt, department=args.department, note=args.note, user_id=args.user_id, affects_reports=args.affects_reports, include_in_balance=args.include_in_balance)


if __name__ == '__main__':
    main()


