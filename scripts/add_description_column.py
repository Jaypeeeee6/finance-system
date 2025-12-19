#!/usr/bin/env python3
"""Temporary migration: add `description` column to person_company_options (SQLite).
This script is idempotent and will do nothing if the column already exists.
"""
import os
import sqlite3
import sys

# Ensure project root is on sys.path so we can import project modules when running from scripts/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import Config


def get_db_path():
    # Config._DB_PATH is constructed as instance/payment_system.db
    db_path = getattr(Config, "_DB_PATH", None)
    if not db_path:
        # Fallback to SQLALCHEMY_DATABASE_URI if available
        uri = getattr(Config, "SQLALCHEMY_DATABASE_URI", "")
        if uri.startswith("sqlite:///"):
            db_path = uri.replace("sqlite:///", "")
    return db_path


def main():
    db_path = get_db_path()
    if not db_path:
        print("ERROR: Could not determine the SQLite database path from config.", file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at: {db_path}", file=sys.stderr)
        sys.exit(2)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info('person_company_options')")
        cols = [r[1] for r in cur.fetchall()]
        if 'description' in cols:
            print("Column 'description' already exists on person_company_options. Nothing to do.")
            return

        print("Adding 'description' column to person_company_options...")
        cur.execute("ALTER TABLE person_company_options ADD COLUMN description TEXT;")
        conn.commit()
        print("Migration applied successfully.")

    except Exception as exc:
        print(f"ERROR applying migration: {exc}", file=sys.stderr)
        conn.rollback()
        sys.exit(3)
    finally:
        conn.close()


if __name__ == '__main__':
    main()


