#!/usr/bin/env python3
"""One-off migration: add archive_reason and archive_supporting_files to payment_requests (SQLite).

Usage (from project root):
  python scripts/migrate_add_archive_reason_columns.py
  python scripts/migrate_add_archive_reason_columns.py --db instance/payment_system.db
"""
import sqlite3
import argparse
import os
import sys


def column_exists(conn, table_name, column_name):
    cur = conn.execute(f"PRAGMA table_info('{table_name}')")
    cols = [row[1] for row in cur.fetchall()]
    return column_name in cols


def main():
    p = argparse.ArgumentParser(description='Add archive_reason and archive_supporting_files to payment_requests')
    p.add_argument('--db', default='instance/payment_system.db', help='Path to SQLite DB')
    args = p.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f'ERROR: DB file not found: {db_path}', file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        table = 'payment_requests'
        if not column_exists(conn, table, 'archive_reason'):
            conn.execute("ALTER TABLE payment_requests ADD COLUMN archive_reason TEXT")
            conn.commit()
            print("Added column archive_reason to payment_requests.")
        else:
            print("Column archive_reason already exists on payment_requests. No action taken.")

        if not column_exists(conn, table, 'archive_supporting_files'):
            conn.execute("ALTER TABLE payment_requests ADD COLUMN archive_supporting_files TEXT")
            conn.commit()
            print("Added column archive_supporting_files to payment_requests.")
        else:
            print("Column archive_supporting_files already exists on payment_requests. No action taken.")

        if not column_exists(conn, table, 'different_amounts_per_branch'):
            conn.execute("ALTER TABLE payment_requests ADD COLUMN different_amounts_per_branch INTEGER DEFAULT 0")
            conn.commit()
            print("Added column different_amounts_per_branch to payment_requests.")
        else:
            print("Column different_amounts_per_branch already exists on payment_requests. No action taken.")

        if not column_exists(conn, table, 'branch_amounts'):
            conn.execute("ALTER TABLE payment_requests ADD COLUMN branch_amounts TEXT")
            conn.commit()
            print("Added column branch_amounts to payment_requests.")
        else:
            print("Column branch_amounts already exists on payment_requests. No action taken.")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
