"""
One-off migration: copy data from root-level SQLite DB (payment_system.db)
to instance/payment_system.db. Safe to re-run; it overwrites the instance DB.

Run: python migrate_root_to_instance_db.py
"""

import os
import shutil
from app import app
from models import db

ROOT_DB = os.path.join(os.path.dirname(__file__), 'payment_system.db')
INSTANCE_DB_DIR = os.path.join(os.path.dirname(__file__), 'instance')
INSTANCE_DB = os.path.join(INSTANCE_DB_DIR, 'payment_system.db')


def migrate():
    if not os.path.exists(ROOT_DB):
        print('No root DB found; nothing to migrate.')
        return
    os.makedirs(INSTANCE_DB_DIR, exist_ok=True)
    # Close any active connections
    with app.app_context():
        db.session.remove()
    # Copy file byte-for-byte (schema and data)
    shutil.copy2(ROOT_DB, INSTANCE_DB)
    print('Copied root payment_system.db -> instance/payment_system.db')


if __name__ == '__main__':
    migrate()


