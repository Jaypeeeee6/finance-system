#!/usr/bin/env python3
"""Add floor_number, flat_number, villa_number columns to branches table if missing.

Safe to re-run.

Usage:
  python scripts/migrate_branches_add_floor_flat_villa_number.py
  python scripts/migrate_branches_add_floor_flat_villa_number.py --db instance/payment_system.db
"""
import sqlite3
import argparse
import os
import sys

COLUMNS = {
    'floor_number': 'floor_number VARCHAR(20)',
    'flat_number': 'flat_number VARCHAR(20)',
    'villa_number': 'villa_number VARCHAR(20)',
}


def get_existing_columns(conn, table):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]


def main():
    p = argparse.ArgumentParser(description='Add floor_number, flat_number, villa_number to branches')
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
        added = []
        for col, col_sql in COLUMNS.items():
            if col in existing:
                continue
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_sql}")
            added.append(col)
        conn.commit()
        if added:
            print("Migration complete. Added:", ", ".join(added))
        else:
            print("All columns already exist on branches.")
    except sqlite3.OperationalError as e:
        print("SQLite error:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
