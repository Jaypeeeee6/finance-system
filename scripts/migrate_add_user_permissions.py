#!/usr/bin/env python3
"""
Create the user_permissions table (if missing).
Run: python scripts/migrate_add_user_permissions.py
"""
from app import app
from models import db

def run_migration():
    with app.app_context():
        print("Creating missing tables (if any)...")
        db.create_all()
        print("Done. Created any missing tables (including user_permissions).")

if __name__ == '__main__':
    run_migration()

