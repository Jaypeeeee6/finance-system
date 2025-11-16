#!/usr/bin/env python3
"""
Script to populate initial request types based on RBAC documentation.
This script should be run after the database migration to add the RequestType table.
"""

from app import app, db
from models import RequestType, User
from datetime import datetime

def populate_request_types():
    """Populate the database with initial request types based on RBAC documentation."""
    
    # Request types by department as defined in README_RBAC.md
    request_types_data = [
        # General Manager (Role-based)
        ('General Manager', 'Personal Expenses'),
        ('General Manager', 'Others'),
        
        # Finance Department
        ('Finance', 'Utilities Expenses'),
        ('Finance', 'Coffee Shop Expenses'),
        ('Finance', 'Supplier Expenses'),
        ('Finance', 'Others'),
        
        # Operation Department
        ('Operation', 'Refund/Reimbursement'),
        ('Operation', 'Others'),
        
        # PR Department
        ('PR', 'Permission Bills'),
        ('PR', 'Flight Tickets'),
        ('PR', 'Petty Cash'),
        ('PR', 'Contract Expenses'),
        ('PR', 'Refund/Reimbursement'),
        ('PR', 'Others'),
        
        # Maintenance Department
        ('Maintenance', 'Purchase Items'),
        ('Maintenance', 'AC Installment'),
        ('Maintenance', 'Repair Expenses'),
        ('Maintenance', 'Sewage Service Expenses'),
        ('Maintenance', 'Others'),
        
        # Marketing Department
        ('Marketing', 'Advertisement Expenses'),
        ('Marketing', 'Photoshoot Expenses'),
        ('Marketing', 'Subscription Expenses'),
        ('Marketing', 'Others'),
        
        # Logistic Department
        ('Logistic', 'ROP Expenses'),
        ('Logistic', 'Truck Maintenance'),
        ('Logistic', 'Others'),
        
        # HR Department
        ('HR', 'Salary Expenses'),
        ('HR', 'Refund/Reimbursement'),
        ('HR', 'Cash Advance Expenses'),
        ('HR', 'Allowance Expenses'),
        ('HR', 'Others'),
        
        # Quality Control Department
        ('Quality Control', 'Pest Control Expenses'),
        ('Quality Control', 'Course Expenses'),
        ('Quality Control', 'Refund/Reimbursement'),
        ('Quality Control', 'Others'),
        
        # Procurement Department
        ('Procurement', 'Purchasing Expenses'),
        ('Procurement', 'Bank money'),
        ('Procurement', 'Others'),
        
        # IT Department
        ('IT', 'Subscription Expenses'),
        ('IT', 'Course Expenses'),
        ('IT', 'Others'),
        
        # Customer Service Department
        ('Customer Service', 'Refund/Reimbursement'),
        ('Customer Service', 'Others'),
        
        # Project
        ('Project', 'New Branch Expenses'),
        ('Project', 'Project Expenses'),
        ('Project', 'Rent Expenses'),
        ('Project', 'Others'),
    ]
    
    print("🚀 Starting to populate request types...")
    
    # Get or create a system user for created_by_user_id
    system_user = User.query.filter_by(username='system').first()
    if not system_user:
        print("⚠️  No system user found. Creating one...")
        system_user = User(
            username='system',
            name='System',
            department='IT',
            role='IT Staff',
            email='system@company.com'
        )
        system_user.set_password('system_password')
        db.session.add(system_user)
        db.session.commit()
        print("✅ System user created.")
    
    created_count = 0
    skipped_count = 0
    
    for department, request_type_name in request_types_data:
        # Check if this request type already exists
        existing = RequestType.query.filter_by(
            name=request_type_name, 
            department=department
        ).first()
        
        if existing:
            print(f"⏭️  Skipping {request_type_name} for {department} (already exists)")
            skipped_count += 1
            continue
        
        # Create new request type
        request_type = RequestType(
            name=request_type_name,
            department=department,
            is_active=True,
            created_by_user_id=system_user.user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(request_type)
        created_count += 1
        print(f"✅ Created: {request_type_name} for {department}")
    
    try:
        db.session.commit()
        print(f"\n🎉 Successfully populated request types!")
        print(f"   - Created: {created_count} new request types")
        print(f"   - Skipped: {skipped_count} existing request types")
        print(f"   - Total departments: {len(set(dept for dept, _ in request_types_data))}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error populating request types: {e}")
        raise

def verify_population():
    """Verify that request types were populated correctly."""
    print("\n🔍 Verifying population...")
    
    # Count request types by department
    departments = db.session.query(RequestType.department).distinct().all()
    
    for dept in departments:
        dept_name = dept[0]
        count = RequestType.query.filter_by(department=dept_name).count()
        print(f"   - {dept_name}: {count} request types")
    
    total_count = RequestType.query.count()
    print(f"\n📊 Total request types in database: {total_count}")

if __name__ == '__main__':
    with app.app_context():
        print("=" * 60)
        print("📋 REQUEST TYPES POPULATION SCRIPT")
        print("=" * 60)
        
        try:
            populate_request_types()
            verify_population()
            print("\n✅ Script completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Script failed: {e}")
            exit(1)
