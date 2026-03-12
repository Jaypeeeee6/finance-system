#!/usr/bin/env python3
"""Add branch_type column to branches table if missing ('branch' or 'flat').

Safe to re-run.

Usage:
  python scripts/migrate_branches_add_branch_type.py
  python scripts/migrate_branches_add_branch_type.py --db instance/payment_system.db
"""
import sqlite3
import argparse
import os
import sys

COLUMN_NAME = 'branch_type'
COLUMN_SQL = "branch_type VARCHAR(20)"


def get_existing_columns(conn, table):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]


def main():
    p = argparse.ArgumentParser(description='Add branch_type to branches')
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
        if COLUMN_NAME in existing:
            print("Column branch_type already exists on branches.")
            return

        print(f"Adding column: {COLUMN_NAME}")
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {COLUMN_SQL}")
        conn.execute(f"UPDATE {table} SET branch_type = 'branch' WHERE branch_type IS NULL")
        conn.commit()
        print("Migration complete. Added branch_type (existing rows set to 'branch').")
    except sqlite3.OperationalError as e:
        print("SQLite error:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
