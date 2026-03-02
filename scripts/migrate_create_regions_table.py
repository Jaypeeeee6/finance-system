#!/usr/bin/env python3
"""Create the regions table and optionally seed with initial regions.

Regions are used for branch code generation (first 2 letters of name, skipping "Al ").
No frontend CRUD - manage via SQL. Safe to re-run (skips seed if table has rows).

Usage:
  python scripts/migrate_create_regions_table.py
  python scripts/migrate_create_regions_table.py --db instance/payment_system.db
  python scripts/migrate_create_regions_table.py --no-seed   # create table only, no seed
  python scripts/migrate_create_regions_table.py --replace  # delete existing regions, seed with default list
"""
import sqlite3
import argparse
import os
import sys

SEED_REGIONS = [
    'Muscat',
    'Al Maabilah',
    'Al Dakhilia',
    'Al Batinah',
    'Al Sharqiah',
    'Al Dhahira',
]


def main():
    p = argparse.ArgumentParser(description='Create regions table and optionally seed')
    p.add_argument('--db', default='instance/payment_system.db', help='Path to SQLite DB')
    p.add_argument('--no-seed', action='store_true', help='Do not insert seed regions')
    p.add_argument('--replace', action='store_true', help='Delete existing regions and re-seed with default list')
    args = p.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE
            )
        """)
        conn.commit()
        print("Table 'regions' ensured.")

        if args.no_seed:
            print("Skipping seed (--no-seed).")
            return

        cur = conn.execute("SELECT COUNT(*) FROM regions")
        count = cur.fetchone()[0]
        if count > 0 and not args.replace:
            print("Regions already have data; skipping seed. Use --replace to delete and re-seed.")
            return

        if args.replace and count > 0:
            conn.execute("DELETE FROM regions")
            conn.commit()
            print(f"Deleted {count} existing region(s).")

        for name in SEED_REGIONS:
            conn.execute("INSERT INTO regions (name) VALUES (?)", (name,))
        conn.commit()
        print(f"Seeded {len(SEED_REGIONS)} regions. You can add/edit/delete via SQL.")
    except sqlite3.OperationalError as e:
        print("SQLite error:", e, file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
