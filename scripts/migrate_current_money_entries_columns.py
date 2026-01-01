#!/usr/bin/env python3
"""Migration helper: ensure all expected columns exist on current_money_entries.

This script will add any missing columns using ALTER TABLE ... ADD COLUMN.
Safe to re-run.

Usage:
  python scripts/migrate_current_money_entries_columns.py
  python scripts/migrate_current_money_entries_columns.py --db instance/payment_system.db
"""
import sqlite3
import argparse
import os
import sys


EXPECTED_COLUMNS = {
    # column_name: SQL snippet used in ALTER TABLE ... ADD COLUMN <snippet>
    'adjustment_amount': "adjustment_amount NUMERIC DEFAULT 0",
    'affects_reports': "affects_reports INTEGER DEFAULT 0",
    'include_in_balance': "include_in_balance INTEGER DEFAULT 0",
    'source': "source TEXT",
    'source_id': "source_id INTEGER",
    'note': "note TEXT",
    'created_by': "created_by INTEGER",
}


def get_existing_columns(conn, table):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]


def add_column(conn, table, column_sql):
    sql = f"ALTER TABLE {table} ADD COLUMN {column_sql}"
    conn.execute(sql)
    conn.commit()


def main():
    p = argparse.ArgumentParser(description='Ensure current_money_entries has expected columns')
    p.add_argument('--db', default='instance/payment_system.db', help='Path to SQLite DB')
    args = p.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        table = 'current_money_entries'
        existing = get_existing_columns(conn, table)
        missing = [col for col in EXPECTED_COLUMNS.keys() if col not in existing]
        if not missing:
            print("No missing columns detected.")
            return

        for col in missing:
            print(f"Adding column: {col}")
            add_column(conn, table, EXPECTED_COLUMNS[col])
        print("Migration complete. Added columns:", ", ".join(missing))
    except sqlite3.OperationalError as e:
        print("SQLite error:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()


