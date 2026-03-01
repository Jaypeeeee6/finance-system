#!/usr/bin/env python3
"""Add branch_code and region columns to branches table if missing.

Safe to re-run.

Usage:
  python scripts/migrate_branches_add_code_region.py
  python scripts/migrate_branches_add_code_region.py --db instance/payment_system.db
"""
import sqlite3
import argparse
import os
import sys

EXPECTED_COLUMNS = {
    'region': "region VARCHAR(50)",
    'branch_code': "branch_code VARCHAR(20)",
}


def get_existing_columns(conn, table):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]


def add_column(conn, table, column_sql):
    sql = f"ALTER TABLE {table} ADD COLUMN {column_sql}"
    conn.execute(sql)
    conn.commit()


def main():
    p = argparse.ArgumentParser(description='Add branch_code and region to branches')
    p.add_argument('--db', default='instance/payment_system.db', help='Path to SQLite DB')
    args = p.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        table = 'branches'
        existing = get_existing_columns(conn, table)
        missing = [col for col in EXPECTED_COLUMNS.keys() if col not in existing]
        if not missing:
            print("No missing columns on branches. branch_code and region already exist.")
            return

        for col in missing:
            print(f"Adding column: {col}")
            add_column(conn, table, EXPECTED_COLUMNS[col])
        print("Migration complete. Added:", ", ".join(missing))
    except sqlite3.OperationalError as e:
        print("SQLite error:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
