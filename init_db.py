"""
Database Initialization Script
This script creates the database tables and populates them with initial data.
"""

from app import app
from models import db, User, PaymentRequest, AuditLog, RecurringPaymentSchedule
from datetime import datetime, date

def init_database():
    """Initialize database with tables and sample data"""
    
    with app.app_context():
        print("Creating database tables...")
        
        # Drop all tables (use with caution in production!)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        print("✓ Tables created successfully")
        
        # Create sample users
        print("\nCreating sample users...")
        
        users_data = [
            {
                'username': 'admin',
                'password': 'admin123',
                'department': 'Administration',
                'role': 'Admin',
                'email': 'admin@company.com'
            },
            {
                'username': 'finance',
                'password': 'finance123',
                'department': 'Finance',
                'role': 'Finance Staff',
                'email': 'finance@company.com'
            },
            {
                'username': 'gm',
                'password': 'gm123',
                'department': 'Management',
                'role': 'GM',
                'email': 'gm@company.com'
            },
            {
                'username': 'it',
                'password': 'it123',
                'department': 'IT',
                'role': 'IT Staff',
                'email': 'it@company.com'
            },
            {
                'username': 'hr_user',
                'password': 'hr123',
                'department': 'Human Resources',
                'role': 'HR Staff',
                'email': 'hr@company.com'
            },
            {
                'username': 'marketing_user',
                'password': 'marketing123',
                'department': 'Marketing',
                'role': 'Marketing Staff',
                'email': 'marketing@company.com'
            },
            {
                'username': 'sales_user',
                'password': 'sales123',
                'department': 'Sales',
                'role': 'Sales Staff',
                'email': 'sales@company.com'
            },
            {
                'username': 'operations_user',
                'password': 'operations123',
                'department': 'Operations',
                'role': 'Operation Staff',
                'email': 'operations@company.com'
            }
        ]
        
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                department=user_data['department'],
                role=user_data['role'],
                email=user_data['email']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"  ✓ Created user: {user_data['username']} ({user_data['role']})")
        
        db.session.commit()
        
        # Create sample payment requests
        print("\nCreating sample payment requests...")
        
        # Get user IDs
        hr_user = User.query.filter_by(username='hr_user').first()
        marketing_user = User.query.filter_by(username='marketing_user').first()
        sales_user = User.query.filter_by(username='sales_user').first()
        finance_user = User.query.filter_by(username='finance').first()
        
        requests_data = [
            {
                'request_type': 'Item',
                'requestor_name': 'John Smith',
                'department': 'Human Resources',
                'date': date(2024, 10, 1),
                'purpose': 'Purchase of office supplies for the HR department',
                'account_name': 'HR Operations Account',
                'account_number': '1234567890',
                'amount': 1500.00,
                'status': 'Approved',
                'approver': 'Mahmoud',
                'proof_of_payment': True,
                'user_id': hr_user.user_id
            },
            {
                'request_type': 'Person',
                'requestor_name': 'Sarah Johnson',
                'department': 'Marketing',
                'date': date(2024, 10, 5),
                'purpose': 'Travel reimbursement for client meeting in Dubai',
                'account_name': 'Sarah Johnson Personal',
                'account_number': '9876543210',
                'amount': 3200.50,
                'status': 'Pending',
                'user_id': marketing_user.user_id
            },
            {
                'request_type': 'Item',
                'requestor_name': 'Mike Davis',
                'department': 'Sales',
                'date': date(2024, 10, 7),
                'purpose': 'Purchase of promotional materials for upcoming trade show',
                'account_name': 'Sales Marketing Budget',
                'account_number': '5555666677',
                'amount': 5000.00,
                'status': 'Pending',
                'user_id': sales_user.user_id
            },
            {
                'request_type': 'Supplier/Rental',
                'requestor_name': 'Finance Team',
                'department': 'Finance',
                'date': date(2024, 10, 3),
                'purpose': 'Monthly office rental payment',
                'account_name': 'ABC Properties LLC',
                'account_number': '1111222233',
                'amount': 15000.00,
                'recurring': 'Recurring',
                'recurring_interval': 'Monthly',
                'status': 'Approved',
                'approver': 'Abdulaziz',
                'proof_of_payment': True,
                'user_id': finance_user.user_id
            },
            {
                'request_type': 'Company',
                'requestor_name': 'Emily Brown',
                'department': 'Marketing',
                'date': date(2024, 10, 8),
                'purpose': 'Payment to advertising agency for Q4 campaign',
                'account_name': 'Creative Ads Agency',
                'account_number': '7777888899',
                'amount': 12000.00,
                'status': 'Pending',
                'user_id': marketing_user.user_id
            },
            {
                'request_type': 'Person',
                'requestor_name': 'David Wilson',
                'department': 'Operations',
                'date': date(2024, 9, 28),
                'purpose': 'Reimbursement for equipment purchased for warehouse',
                'account_name': 'David Wilson Personal',
                'account_number': '4444555566',
                'amount': 2500.00,
                'status': 'Approved',
                'approver': 'Mahmoud',
                'proof_of_payment': True,
                'user_id': finance_user.user_id
            }
        ]
        
        for req_data in requests_data:
            request = PaymentRequest(**req_data)
            db.session.add(request)
            print(f"  ✓ Created request: {req_data['request_type']} - ${req_data['amount']:.2f} ({req_data['status']})")
        
        db.session.commit()
        
        # Create audit logs
        print("\nCreating audit logs...")
        
        logs_data = [
            {
                'user_id': hr_user.user_id,
                'action': 'User hr_user logged in'
            },
            {
                'user_id': hr_user.user_id,
                'action': 'Created payment request #1 - Item'
            },
            {
                'user_id': User.query.filter_by(username='admin').first().user_id,
                'action': 'Approved payment request #1'
            },
            {
                'user_id': marketing_user.user_id,
                'action': 'User marketing_user logged in'
            },
            {
                'user_id': marketing_user.user_id,
                'action': 'Created payment request #2 - Person'
            }
        ]
        
        for log_data in logs_data:
            log = AuditLog(**log_data)
            db.session.add(log)
        
        db.session.commit()
        print(f"  ✓ Created {len(logs_data)} audit log entries")
        
        print("\n" + "="*60)
        print("DATABASE INITIALIZATION COMPLETE!")
        print("="*60)
        print("\nSample Login Credentials:")
        print("-" * 60)
        print(f"{'Role':<20} {'Username':<20} {'Password':<20}")
        print("-" * 60)
        for user_data in users_data:
            print(f"{user_data['role']:<20} {user_data['username']:<20} {user_data['password']:<20}")
        print("-" * 60)
        print("\nYou can now start the application with: python app.py")
        print("Then visit: http://127.0.0.1:5000")
        print("\n")


if __name__ == '__main__':
    print("="*60)
    print("PAYMENT REQUEST MANAGEMENT SYSTEM")
    print("Database Initialization")
    print("="*60)
    print("\nWARNING: This will DROP all existing tables and data!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        init_database()
    else:
        print("Database initialization cancelled.")

