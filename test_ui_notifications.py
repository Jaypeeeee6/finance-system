#!/usr/bin/env python3
"""
Test script to verify UI notification display
"""

from app import app, db, User, Notification, PaymentRequest
from datetime import datetime, timedelta

def test_ui_notifications():
    """Test that notifications are properly displayed in UI"""
    with app.app_context():
        print("=== Testing UI Notification Display ===\n")
        
        # 1. Check Finance Admin users
        print("1. Finance Admin Users:")
        finance_admins = User.query.filter_by(role='Finance Admin').all()
        for admin in finance_admins:
            print(f"   - {admin.name} ({admin.username})")
        print()
        
        # 2. Check timing alert notifications
        print("2. Timing Alert Notifications:")
        timing_alerts = Notification.query.filter(
            Notification.notification_type.in_(['finance_approval_timing_alert', 'finance_approval_timing_recurring'])
        ).order_by(Notification.created_at.desc()).all()
        
        print(f"   Total timing alerts: {len(timing_alerts)}")
        for alert in timing_alerts[:5]:  # Show last 5
            user = User.query.get(alert.user_id)
            print(f"   - {alert.title}")
            print(f"     User: {user.name if user else 'Unknown'}")
            print(f"     Request: #{alert.request_id}")
            print(f"     Read: {alert.is_read}")
            print(f"     Created: {alert.created_at}")
            print()
        
        # 3. Test notification filtering for each admin
        print("3. Notification Filtering Test:")
        for admin in finance_admins:
            # This simulates what the UI would show
            notifications = Notification.query.filter(
                Notification.user_id == admin.user_id,
                Notification.notification_type.in_(['ready_for_finance_review', 'proof_uploaded', 'recurring_due', 'installment_edited', 'finance_approval_timing_alert', 'finance_approval_timing_recurring', 'system_maintenance', 'system_update', 'security_alert', 'system_error', 'admin_announcement'])
            ).order_by(Notification.created_at.desc()).limit(5).all()
            
            print(f"   {admin.name}:")
            print(f"     Total notifications: {len(notifications)}")
            timing_count = len([n for n in notifications if n.notification_type in ['finance_approval_timing_alert', 'finance_approval_timing_recurring']])
            print(f"     Timing alerts: {timing_count}")
            print()
        
        # 4. Test unread count
        print("4. Unread Count Test:")
        for admin in finance_admins:
            unread_count = Notification.query.filter(
                Notification.user_id == admin.user_id,
                Notification.is_read == False,
                Notification.notification_type.in_(['ready_for_finance_review', 'proof_uploaded', 'recurring_due', 'installment_edited', 'finance_approval_timing_alert', 'finance_approval_timing_recurring', 'system_maintenance', 'system_update', 'security_alert', 'system_error', 'admin_announcement'])
            ).count()
            
            print(f"   {admin.name}: {unread_count} unread notifications")
        print()
        
        # 5. Test request details
        print("5. Request Details for Notifications:")
        request_ids = list(set([alert.request_id for alert in timing_alerts if alert.request_id]))
        for req_id in request_ids:
            req = PaymentRequest.query.get(req_id)
            if req:
                print(f"   Request #{req_id}:")
                print(f"     Type: {req.request_type}")
                print(f"     Purpose: {req.purpose}")
                print(f"     Urgent: {req.is_urgent}")
                print(f"     Status: {req.status}")
                print(f"     Start Time: {req.finance_approval_start_time}")
                print()
        
        print("=== UI Test Complete ===")
        print("\nTo test in the web UI:")
        print("1. Start the application: python app.py")
        print("2. Login as a Finance Admin user")
        print("3. Check the notifications dropdown/bell icon")
        print("4. Look for timing alert notifications")
        print("5. Click on notifications to view request details")

if __name__ == "__main__":
    test_ui_notifications()
