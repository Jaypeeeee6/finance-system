#!/usr/bin/env python3
"""One-off migration: add `include_in_balance` column to `current_money_entries` (SQLite).

Usage:
  python scripts/migrate_add_include_in_balance.py
  python scripts/migrate_add_include_in_balance.py --db instance/payment_system.db
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
    p = argparse.ArgumentParser(description='Add include_in_balance column to current_money_entries')
    p.add_argument('--db', default='instance/payment_system.db', help='Path to SQLite DB')
    args = p.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f'ERROR: DB file not found: {db_path}', file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        table = 'current_money_entries'
        col = 'include_in_balance'
        if not column_exists(conn, table, col):
            # SQLite supports ADD COLUMN with a default value
            sql = f"ALTER TABLE {table} ADD COLUMN {col} INTEGER DEFAULT 0"
            conn.execute(sql)
            conn.commit()
            print(f"Added column `{col}` to `{table}` (default 0).")
        else:
            print(f"Column `{col}` already exists on `{table}`. No action taken.")
    finally:
        conn.close()


if __name__ == '__main__':
    main()


