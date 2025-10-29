# Notification System Documentation

This document outlines all notifications in the finance system, their recipients, and where they are displayed.

## Display Locations

All notifications appear in **two locations**:
1. **Notification Bell** (`/api/notifications/unread` - dropdown in navbar) - Shows latest 5 notifications
   - Plays a sound notification when a new notification arrives
2. **Notification Page** (`/notifications`) - Shows all notifications filtered by role

---

## Notification Types

### 1. **new_submission**
**Recipients:**
- **GM**: Receives notifications from ALL requests (all roles and departments)
- **Operation Manager**: Receives notifications from ALL requests (all roles and departments)
- **IT Department Manager**: Only when requestor is IT Staff
- **Other Department Managers**: Only when requestor is from their department staff

**When it's sent:** When a new payment request is submitted (before manager approval)

**Notification Content:**
- **Title:** "New Payment Request for Approval"
- **Message:** "New {request_type} request submitted by {requestor_name} from {department} department for OMR {amount} - requires your approval"
  - Example: "New Invoice Payment request submitted by John Doe from IT department for OMR 500.00 - requires your approval"

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 2. **ready_for_finance_review**
**Recipients:**
- **Finance Staff**
- **Finance Admin**

**When it's sent:** 
- When a Finance department request is auto-approved (status = Approved)
- When a manager approves a request and it reaches "Pending Finance Approval" status

**Notification Content:**
- **Title:** "New Payment Request Submitted" (for Finance auto-approved)
- **Message:** "New {request_type} request submitted by {requestor_name} from {department} department for OMR {amount}"
  - Example: "New Invoice Payment request submitted by John Doe from Finance department for OMR 500.00"

- **Title:** "Payment Request Ready for Review" (when manager approves)
- **Message:** "Payment request #{request_id} from {department} department has been approved by manager and is ready for Finance review"
  - Example: "Payment request #123 from IT department has been approved by manager and is ready for Finance review"

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 3. **request_approved**
**Recipients:**
- **Requestor** (the user who created the request)
- **Finance Admin** (also notified)

**When it's sent:** When a manager approves a payment request

**Notification Content:**
- **Title:** "Payment Request Approved"
- **Message:** "Your payment request #{request_id} has been approved by your manager and sent to Finance for final approval."
  - Example: "Your payment request #123 has been approved by your manager and sent to Finance for final approval."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 4. **request_rejected**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** 
- When a manager rejects a request
- When Finance Admin rejects a request

**Notification Content:**
- **Title:** "Payment Request Rejected"
- **Message (from Manager):** "Your payment request #{request_id} has been rejected by your manager. Please review the feedback."
  - Example: "Your payment request #123 has been rejected by your manager. Please review the feedback."

- **Message (from Finance):** "Your payment request #{request_id} has been rejected by Finance. Please review the feedback."
  - Example: "Your payment request #123 has been rejected by Finance. Please review the feedback."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 5. **proof_uploaded**
**Recipients:**
- **Requestor** (the user who created the request)
- **Finance Admin**
- **Finance Staff**

**When it's sent:** When the requestor uploads proof of payment files

**Notification Content:**
- **Title:** "Proof of Payment Uploaded"
- **Message:** "{count} proof file(s) have been uploaded for request #{request_id} by {user_name}"
  - Example: "3 proof file(s) have been uploaded for request #123 by John Doe"

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 6. **proof_required**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When Finance Admin approves a request that requires proof of payment

**Notification Content:**
- **Title:** "Proof of Payment Required"
- **Message:** "Your payment request #{request_id} has been approved. Please upload proof of payment."
  - Example: "Your payment request #123 has been approved. Please upload proof of payment."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 7. **proof_approved**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When Finance Admin approves the uploaded proof of payment

**Notification Content:**
- **Title:** "Recurring Payment Approved" (for recurring payments)
- **Message:** "Your proof for recurring payment request #{request_id} has been approved. Payment schedule is now active."
  - Example: "Your proof for recurring payment request #123 has been approved. Payment schedule is now active."

- **Title:** "Proof Approved" (for one-time payments)
- **Message:** "Your proof for payment request #{request_id} has been approved. Status updated to Payment Pending."
  - Example: "Your proof for payment request #123 has been approved. Status updated to Payment Pending."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 8. **proof_rejected**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When Finance Admin rejects the uploaded proof of payment

**Notification Content:**
- **Title:** "Proof Rejected"
- **Message:** "Your proof for payment request #{request_id} has been rejected. Please review the feedback and resubmit."
  - Example: "Your proof for payment request #123 has been rejected. Please review the feedback and resubmit."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 9. **recurring_due**
**Recipients:**
- **Finance Admin**
- **Finance Staff**
- **Project Staff** (on their own requests only)
- **Department Managers** (for their department's requests)
- **Department Staff** (on their own requests only)

**When it's sent:** 
- Daily automated check for recurring payments due today
- When an installment date is edited to today's date

**Notification Content:**
- **Title:** "Recurring Payment Due"
- **Message (with amount):** "Recurring payment due today for {request_type} - {purpose} (Amount: {amount} OMR)"
  - Example: "Recurring payment due today for Monthly Rent - Office Lease (Amount: 1000.00 OMR)"

- **Message (after date edit):** "Recurring payment due today for {request_type} - {purpose} (Amount: {amount} OMR) - Date was recently edited"
  - Example: "Recurring payment due today for Monthly Rent - Office Lease (Amount: 1000.00 OMR) - Date was recently edited"

- **Message (without amount):** "Recurring payment due today for {request_type} - {purpose}"
  - Example: "Recurring payment due today for Monthly Rent - Office Lease"

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 10. **recurring_approved**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When a recurring payment request is approved by Finance Admin (with or without proof)

**Notification Content:**
- **Title:** "Recurring Payment Approved"
- **Message:** "Your recurring payment request #{request_id} has been approved. Payment schedule will be managed."
  - Example: "Your recurring payment request #123 has been approved. Payment schedule will be managed."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 11. **recurring_completed**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When all installments of a recurring payment have been paid and the request is automatically marked as completed

**Notification Content:**
- **Title:** "Recurring Payment Completed"
- **Message:** "All installments for recurring payment request #{request_id} have been paid. Request marked as completed."
  - Example: "All installments for recurring payment request #123 have been paid. Request marked as completed."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 12. **installment_paid**
**Recipients:**
- **Requestor** (the user who created the request)
- **Finance Admin** (also notified)
- **Finance Staff** (also notified)

**When it's sent:** 
- When the first installment is automatically marked as paid during approval
- When Finance Admin marks an installment as paid

**Notification Content:**
- **Title:** "First Installment Paid" (for first installment auto-paid)
- **Message:** "First installment for {payment_date} has been automatically marked as paid (Amount: {amount} OMR)"
  - Example: "First installment for 2024-01-15 has been automatically marked as paid (Amount: 500.00 OMR)"

- **Title:** "Installment Paid" (for manually marked installments)
- **Message:** "Installment for {payment_date} has been marked as paid (Amount: {amount} OMR)"
  - Example: "Installment for 2024-02-15 has been marked as paid (Amount: 500.00 OMR)"

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 13. **installment_edited**
**Recipients:**
- **Finance Admin**

**When it's sent:** When a requestor edits an installment payment date

**Notification Content:**
- **Title:** "Installment Date Edited"
- **Message:** "Recurring request #{request_id} installment payment date has been edited from {old_date} to {new_date} by {user_name}"
  - Example: "Recurring request #123 installment payment date has been edited from 2024-01-15 to 2024-01-20 by John Doe"

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 14. **request_completed**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** 
- When a one-time payment request is approved and completed (no proof required)
- When Finance Admin closes a request manually

**Notification Content:**
- **Title:** "Request Completed"
- **Message (auto-completed):** "Your payment request #{request_id} has been approved and completed. No proof of payment was required."
  - Example: "Your payment request #123 has been approved and completed. No proof of payment was required."

- **Message (manually closed):** "Your payment request #{request_id} has been completed and closed."
  - Example: "Your payment request #123 has been completed and closed."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 15. **payment_completed**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When Finance Admin marks a Payment Pending request as paid

**Notification Content:**
- **Title:** "Payment Completed"
- **Message:** "Your payment request #{request_id} has been paid."
  - Example: "Your payment request #123 has been paid."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 16. **finance_note_added**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When Finance Admin adds a note to a request in "Pending Finance Approval" status

**Notification Content:**
- **Title:** "Finance Admin Note Added"
- **Message:** "Finance admin has added a note to your payment request #{request_id}. Please check the request details."
  - Example: "Finance admin has added a note to your payment request #123. Please check the request details."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 17. **temporary_manager_assignment**
**Recipients:**
- **GM**
- **Operation Manager**
- **IT Department Manager**
- **Department Managers**

**When it's sent:** When IT Staff assigns a temporary manager to review a request (when original manager is unavailable)

**Notification Content:**
- **Title:** "Temporary Manager Assignment"
- **Message:** "You have been temporarily assigned to review payment request #{request_id} from {department} department. The originally assigned manager is not available."
  - Example: "You have been temporarily assigned to review payment request #123 from IT department. The originally assigned manager is not available."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 18. **manager_reassigned**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When a temporary manager is assigned to their request

**Notification Content:**
- **Title:** "Manager Reassigned for Your Request"
- **Message:** "The manager for your payment request #{request_id} has been temporarily reassigned to {manager_name}. This only affects this specific request."
  - Example: "The manager for your payment request #123 has been temporarily reassigned to Jane Smith. This only affects this specific request."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 19. **temporary_manager_unassigned**
**Recipients:**
- **Previous Temporary Manager** (the user who was previously assigned)

**When it's sent:** When a temporary manager assignment is changed to a different manager

**Notification Content:**
- **Title:** "Temporary Manager Assignment Removed"
- **Message:** "You are no longer the temporary manager for payment request #{request_id}."
  - Example: "You are no longer the temporary manager for payment request #123."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 20. **user_created**
**Recipients:**
- **IT Staff** (all users with IT Staff role)

**When it's sent:** When a new user is created by IT Staff or Department Manager

**Notification Content:**
- **Title:** "New User Created"
- **Message:** "New user {username} ({role}) has been created for {department} department by {creator_name}"
  - Example: "New user johndoe (Project Staff) has been created for IT department by Admin User"

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 21. **user_updated**
**Recipients:**
- **IT Staff** (all users with IT Staff role)

**When it's sent:** When a user's details are updated by IT Staff or Department Manager

**Notification Content:**
- **Title:** "User Updated"
- **Message:** "User {username} has been updated to {new_role} in {new_department} department by {updater_name}"
  - Example: "User johndoe has been updated to Finance Staff in Finance department by Admin User"

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 22. **user_deleted**
**Recipients:**
- **IT Staff** (all users with IT Staff role)

**When it's sent:** When a user is deleted (mentioned in code but not fully implemented yet)

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 23. **account_unlocked**
**Recipients:**
- **User whose account was unlocked**

**When it's sent:** When IT Staff unlocks a locked user account

**Notification Content:**
- **Title:** "Account Unlocked"
- **Message:** "Your account has been unlocked by IT Staff. You can now log in again."
  - Example: "Your account has been unlocked by IT Staff. You can now log in again."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 24. **password_reset**
**Recipients:**
- **User whose password was reset**

**When it's sent:** When IT Staff or Department Manager (IT only) resets a user's password

**Notification Content:**
- **Title:** "Password Reset"
- **Message:** "Your password has been reset by IT Staff. Please log in with your new password and change it immediately."
  - Example: "Your password has been reset by IT Staff. Please log in with your new password and change it immediately."

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

### 25. **status_changed**
**Recipients:**
- **Requestor** (the user who created the request)

**When it's sent:** When the status of a request changes (mentioned in RBAC filters, but not explicitly created in code)

**Display:** ✅ Bell (with sound) | ✅ Notification Page

---

## System-Wide Notifications (Not Currently Implemented)

The following notification types are referenced in the RBAC filters but are not currently created by the system:

- `system_maintenance`
- `system_update`
- `security_alert`
- `system_error`
- `admin_announcement`
- `finance_approval_timing_alert`
- `finance_approval_timing_recurring`

These are likely planned for future implementation.

---

## Notification Filtering by Role

### Project Staff
- Updates on their own requests
- Recurring payment due (on their own requests only)

### Finance Staff
- New submissions (ready_for_finance_review)
- Proof uploaded
- Recurring payment due
- Installment edited
- Updates on their own requests

### Finance Admin
- New submissions (ready_for_finance_review)
- Proof uploaded
- Recurring payment due
- Installment edited

### GM
- New submissions (from Department Managers only)
- Updates on their own requests
- Temporary manager assignments
- System-wide notifications

### Operation Manager
- New submissions (from Operation Staff only)
- Updates on their own requests
- Temporary manager assignments
- System-wide notifications

### IT Department Manager
- New submissions (from IT Staff only)
- Updates on their own requests
- User management notifications
- Temporary manager assignments
- System-wide notifications

### IT Staff
- Updates on their own requests
- User management notifications (user_created, user_updated, user_deleted)
- System-wide notifications

### Department Managers (Non-IT)
- New submissions (from their department staff only)
- Recurring payment due (for their department)
- Updates on their own requests
- Temporary manager assignments

### Department Staff
- Updates on their own requests only
- Recurring payment due (for their own requests only)

---

## Technical Implementation

### Real-time Notifications
All notifications are broadcast via WebSocket (`socketio.emit('new_notification')`) to all connected users, which triggers:
1. A sound notification (bell sound using Web Audio API)
2. Update of the notification badge count
3. Refresh of the notification dropdown if it's open
4. Page refresh on the notifications page (after 2 seconds)

### Notification API Endpoints
- `GET /api/notifications/unread` - Get unread notifications for notification bell (limit 5)
- `GET /notifications` - Get all notifications for notification page (filtered by role)
- `GET /api/notifications/unread_count` - Get unread count for badge

