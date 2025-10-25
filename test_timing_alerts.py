#!/usr/bin/env python3
"""
Test script for timing alerts functionality
"""

from app import app, db, PaymentRequest, Notification, User
from datetime import datetime, timedelta

def test_timing_alerts():
    """Test the timing alerts system"""
    with app.app_context():
        print("=== Testing Timing Alerts System ===\n")
        
        # 1. Check current pending requests
        print("1. Current Pending Finance Approval Requests:")
        pending_requests = PaymentRequest.query.filter(
            PaymentRequest.status == 'Pending Finance Approval',
            PaymentRequest.finance_approval_start_time.isnot(None),
            PaymentRequest.finance_approval_end_time.is_(None)
        ).all()
        
        current_time = datetime.utcnow()
        for req in pending_requests:
            elapsed = current_time - req.finance_approval_start_time
            print(f"   Request #{req.request_id}: {req.request_type}")
            print(f"   - Urgent: {req.is_urgent}")
            print(f"   - Start Time: {req.finance_approval_start_time}")
            print(f"   - Elapsed: {elapsed.total_seconds()/3600:.2f} hours")
            print()
        
        # 2. Check existing alerts
        print("2. Existing Timing Alerts:")
        for req in pending_requests:
            alerts = Notification.query.filter(
                Notification.request_id == req.request_id,
                Notification.notification_type.in_(['finance_approval_timing_alert', 'finance_approval_timing_recurring'])
            ).order_by(Notification.created_at.desc()).all()
            
            print(f"   Request #{req.request_id}: {len(alerts)} alerts")
            for alert in alerts[:3]:  # Show last 3 alerts
                print(f"     - {alert.title} ({alert.created_at})")
            print()
        
        # 3. Test alert logic manually
        print("3. Testing Alert Logic:")
        for req in pending_requests:
            elapsed = current_time - req.finance_approval_start_time
            
            # Determine thresholds
            if req.is_urgent:
                alert_threshold = timedelta(hours=2)
                recurring_threshold = timedelta(hours=2)
            else:
                alert_threshold = timedelta(hours=24)
                recurring_threshold = timedelta(hours=24)
            
            print(f"   Request #{req.request_id} ({'URGENT' if req.is_urgent else 'NON-URGENT'}):")
            print(f"     - Elapsed: {elapsed.total_seconds()/3600:.2f} hours")
            print(f"     - Threshold: {alert_threshold.total_seconds()/3600} hours")
            print(f"     - Should alert: {elapsed >= alert_threshold}")
            
            if elapsed >= alert_threshold:
                # Check for existing alerts
                existing_alerts = Notification.query.filter(
                    Notification.request_id == req.request_id,
                    Notification.notification_type.in_(['finance_approval_timing_alert', 'finance_approval_timing_recurring'])
                ).order_by(Notification.created_at.desc()).all()
                
                if existing_alerts:
                    last_alert = existing_alerts[0]
                    time_since_last = current_time - last_alert.created_at
                    print(f"     - Last alert: {time_since_last.total_seconds()/3600:.2f} hours ago")
                    print(f"     - Should send recurring: {time_since_last >= recurring_threshold}")
                else:
                    print(f"     - No existing alerts - should send first alert")
            print()
        
        # 4. Test creating a new urgent request for immediate testing
        print("4. Creating Test Request for Immediate Testing:")
        
        # Create a test request that's already overdue
        test_start_time = current_time - timedelta(hours=3)  # 3 hours ago for urgent
        
        # Update request #3 to have a start time 3 hours ago
        test_req = PaymentRequest.query.get(3)
        if test_req:
            original_start_time = test_req.finance_approval_start_time
            test_req.finance_approval_start_time = test_start_time
            test_req.is_urgent = True
            db.session.commit()
            
            print(f"   Updated Request #3 start time to {test_start_time} (3 hours ago)")
            print(f"   Set as urgent for testing")
            
            # Now test the alert function
            print("\n5. Running Alert Check on Modified Request:")
            from app import check_finance_approval_timing_alerts
            check_finance_approval_timing_alerts()
            
            # Check if new alerts were created
            new_alerts = Notification.query.filter(
                Notification.request_id == 3,
                Notification.notification_type.in_(['finance_approval_timing_alert', 'finance_approval_timing_recurring']),
                Notification.created_at >= current_time
            ).all()
            
            print(f"   New alerts created: {len(new_alerts)}")
            for alert in new_alerts:
                print(f"     - {alert.title}")
                print(f"     - Message: {alert.message}")
                print(f"     - Created: {alert.created_at}")
            
            # Restore original start time
            test_req.finance_approval_start_time = original_start_time
            db.session.commit()
            print(f"\n   Restored original start time: {original_start_time}")
        
        print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_timing_alerts()
