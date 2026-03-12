#!/usr/bin/env python3
"""Add parent_branch_id column to branches table if missing (for flats linking to a branch).

Safe to re-run.

Usage:
  python scripts/migrate_branches_add_parent_branch_id.py
  python scripts/migrate_branches_add_parent_branch_id.py --db instance/payment_system.db
"""
import sqlite3
import argparse
import os
import sys

COLUMN_NAME = 'parent_branch_id'
COLUMN_SQL = "parent_branch_id INTEGER REFERENCES branches(id)"


def get_existing_columns(conn, table):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]


def main():
    p = argparse.ArgumentParser(description='Add parent_branch_id to branches')
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
            print("Column parent_branch_id already exists on branches.")
            return

        print(f"Adding column: {COLUMN_NAME}")
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {COLUMN_SQL}")
        conn.commit()
        print("Migration complete. Added parent_branch_id.")
    except sqlite3.OperationalError as e:
        print("SQLite error:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
