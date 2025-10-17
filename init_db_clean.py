"""
Utility script to purge all users and related data.

Run non-interactively:
  python init_db_clean.py

After purge, visiting the login page will auto-create the default IT user
(it@system.local / admin123) as implemented in app.py.
"""

from app import app
from models import db, User, PaymentRequest, AuditLog, Notification, RecurringPaymentSchedule, PaidNotification, LateInstallment


def purge_users_and_related_data():
    with app.app_context():
        print("Purging all user-related data...")

        # Delete dependent records first to satisfy foreign keys
        deleted_counts = {}
        for model in [RecurringPaymentSchedule, PaidNotification, LateInstallment, Notification, PaymentRequest, AuditLog]:
            count = model.query.delete()
            deleted_counts[model.__tablename__] = count

        # Delete all users last
        users_deleted = User.query.delete()
        deleted_counts['users'] = users_deleted

        db.session.commit()

        print("Deletion summary:")
        for table, count in deleted_counts.items():
            print(f"  - {table}: {count}")
        print("\nAll users and related data have been purged.")


if __name__ == '__main__':
    purge_users_and_related_data()


