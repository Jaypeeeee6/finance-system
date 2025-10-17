"""
Delete ONLY users, preserving all other data.

Usage:
  python delete_all_users.py

This will:
  - Set PaymentRequest.user_id = NULL
  - Set Notification.user_id = NULL
  - Delete all rows from users

The default IT bootstrap account will be recreated automatically when you visit /login.
"""

from app import app
from models import db, User, PaymentRequest, Notification


def delete_only_users():
    with app.app_context():
        print("Nulling foreign keys that reference users (but keeping their data)...")
        # Null out references to users to avoid FK issues
        PaymentRequest.query.update({PaymentRequest.user_id: None})
        Notification.query.update({Notification.user_id: None})
        db.session.commit()

        print("Deleting all users...")
        deleted = User.query.delete()
        db.session.commit()
        print(f"Deleted {deleted} users. All other data preserved.")


if __name__ == '__main__':
    delete_only_users()


