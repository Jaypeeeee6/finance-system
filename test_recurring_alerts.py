#!/usr/bin/env python3
"""
Test script for recurring timing alerts functionality
"""

from app import app, db, PaymentRequest, Notification, User
from datetime import datetime, timedelta

def test_recurring_alerts():
    """Test the recurring timing alerts system"""
    with app.app_context():
        print("=== Testing Recurring Timing Alerts System ===\n")
        
        # 1. Create a test scenario where we can trigger recurring alerts
        print("1. Setting up test scenario...")
        
        # Find a pending request to modify
        test_req = PaymentRequest.query.filter(
            PaymentRequest.status == 'Pending Finance Approval',
            PaymentRequest.finance_approval_start_time.isnot(None),
            PaymentRequest.finance_approval_end_time.is_(None)
        ).first()
        
        if not test_req:
            print("   No pending requests found. Creating a test request...")
            # Create a test request
            test_req = PaymentRequest(
                request_type="Test Request",
                requestor_name="Test User",
                branch_name="Test Branch",
                department="Test Department",
                date=datetime.utcnow().date(),
                purpose="Testing timing alerts",
                account_name="Test Account",
                account_number="123456789",
                bank_name="Test Bank",
                amount=100.000,
                status="Pending Finance Approval",
                is_urgent=True,
                finance_approval_start_time=datetime.utcnow() - timedelta(hours=5),  # 5 hours ago
                user_id=1  # Assuming user ID 1 exists
            )
            db.session.add(test_req)
            db.session.commit()
            print(f"   Created test request #{test_req.request_id}")
        else:
            print(f"   Using existing request #{test_req.request_id}")
        
        # 2. Clear existing alerts for this request
        print("\n2. Clearing existing alerts...")
        existing_alerts = Notification.query.filter(
            Notification.request_id == test_req.request_id,
            Notification.notification_type.in_(['finance_approval_timing_alert', 'finance_approval_timing_recurring'])
        ).all()
        
        for alert in existing_alerts:
            db.session.delete(alert)
        db.session.commit()
        print(f"   Deleted {len(existing_alerts)} existing alerts")
        
        # 3. Set up the request for testing
        print("\n3. Setting up request for testing...")
        # Set start time to 5 hours ago for urgent request
        test_req.finance_approval_start_time = datetime.utcnow() - timedelta(hours=5)
        test_req.is_urgent = True
        db.session.commit()
        print(f"   Set request #{test_req.request_id} as urgent with start time 5 hours ago")
        
        # 4. Test first alert
        print("\n4. Testing first alert...")
        from app import check_finance_approval_timing_alerts
        check_finance_approval_timing_alerts()
        
        # Check if first alert was created
        first_alerts = Notification.query.filter(
            Notification.request_id == test_req.request_id,
            Notification.notification_type == 'finance_approval_timing_alert'
        ).all()
        
        print(f"   First alerts created: {len(first_alerts)}")
        for alert in first_alerts:
            print(f"     - {alert.title}")
            print(f"     - Message: {alert.message}")
            print(f"     - Created: {alert.created_at}")
        
        # 5. Simulate time passing for recurring alert
        print("\n5. Simulating time passing for recurring alert...")
        
        # Update the last alert's created_at time to be 3 hours ago
        if first_alerts:
            last_alert = first_alerts[0]
            last_alert.created_at = datetime.utcnow() - timedelta(hours=3)
            db.session.commit()
            print(f"   Updated last alert time to 3 hours ago")
        
        # 6. Test recurring alert
        print("\n6. Testing recurring alert...")
        check_finance_approval_timing_alerts()
        
        # Check if recurring alert was created
        recurring_alerts = Notification.query.filter(
            Notification.request_id == test_req.request_id,
            Notification.notification_type == 'finance_approval_timing_recurring'
        ).all()
        
        print(f"   Recurring alerts created: {len(recurring_alerts)}")
        for alert in recurring_alerts:
            print(f"     - {alert.title}")
            print(f"     - Message: {alert.message}")
            print(f"     - Created: {alert.created_at}")
        
        # 7. Test non-urgent request
        print("\n7. Testing non-urgent request...")
        
        # Create another test request for non-urgent testing
        test_req2 = PaymentRequest(
            request_type="Test Non-Urgent",
            requestor_name="Test User 2",
            branch_name="Test Branch",
            department="Test Department",
            date=datetime.utcnow().date(),
            purpose="Testing non-urgent timing alerts",
            account_name="Test Account",
            account_number="987654321",
            bank_name="Test Bank",
            amount=200.000,
            status="Pending Finance Approval",
            is_urgent=False,
            finance_approval_start_time=datetime.utcnow() - timedelta(hours=25),  # 25 hours ago
            user_id=1
        )
        db.session.add(test_req2)
        db.session.commit()
        print(f"   Created non-urgent test request #{test_req2.request_id} (25 hours ago)")
        
        # Test non-urgent alert
        check_finance_approval_timing_alerts()
        
        # Check non-urgent alerts
        non_urgent_alerts = Notification.query.filter(
            Notification.request_id == test_req2.request_id,
            Notification.notification_type == 'finance_approval_timing_alert'
        ).all()
        
        print(f"   Non-urgent alerts created: {len(non_urgent_alerts)}")
        for alert in non_urgent_alerts:
            print(f"     - {alert.title}")
            print(f"     - Message: {alert.message}")
        
        # 8. Check all notifications for Finance Admin users
        print("\n8. Checking notifications for Finance Admin users...")
        finance_admins = User.query.filter_by(role='Finance Admin').all()
        
        for admin in finance_admins:
            notifications = Notification.query.filter(
                Notification.user_id == admin.user_id,
                Notification.notification_type.in_(['finance_approval_timing_alert', 'finance_approval_timing_recurring'])
            ).order_by(Notification.created_at.desc()).limit(5).all()
            
            print(f"   {admin.name} ({admin.username}): {len(notifications)} timing alerts")
            for notif in notifications:
                print(f"     - {notif.title} ({notif.created_at})")
        
        print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_recurring_alerts()
