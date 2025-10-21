## Role-Based Access Control (RBAC) and Approval Flow

This document describes who can view what, who can approve/reject, and how a payment request moves through the workflow. Keep this as the single reference for permissions and process.

### Statuses Used in the System
- **Pending Manager Approval**: Newly submitted; waiting for the requestor’s department manager.
- **Pending Finance Approval**: Approved by department manager; waiting for Finance.
- **Rejected by Manager**: Rejected by the department manager during initial review.
- **Proof Pending**: Approved by Finance and awaiting payment proof upload.
- **Proof Sent**: Proof uploaded/sent; pending any final checks or reconciliation.
- **Recurring**: Recurring payment schedule item.
- **Completed**: Fully processed and finalized.
- **Rejected by Finance**: Finance rejected after manager approval.

### High-Level Approval Flow
1. Requestor submits a request → status becomes **Pending Manager Approval**.
2. Department Manager reviews:
   - If approved → status becomes **Pending Finance Approval**.
   - If rejected → status becomes **Rejected by Manager**.
3. Finance reviews:
   - If approved and proof of payment is required → status becomes **Proof Pending** (awaiting payment execution/proof).
   - If approved and proof of payment is not required → status becomes **Completed**.
   - If rejected → status becomes **Rejected by Finance**.
4. Proof is provided (e.g., receipt/transfer slip):
   - Status progresses to **Proof Sent**, then to **Completed** after verification.
   - If the submitted proof is rejected by Finance → status returns to **Proof Pending**. The requestor must re-submit proof; upon re-submission it moves to **Proof Sent** again. This loop repeats until Finance accepts the proof and advances the request to **Completed**.
5. Recurring requests cycle as **Recurring** according to schedule; when all installments are marked as paid, the request status becomes **Completed**.

### Who Can Change Status
- **Department Managers (by department)**: Can approve/reject requests from their own department (move to Pending Finance Approval or reject).
- **Finance Approvers** (see roles below): Can approve/reject only after manager approval, i.e., while in Pending Finance Approval (move to Proof Pending or Rejected by Finance) and advance through proof-related states.
- Other roles with view-only rights cannot change status.

---

## Viewing and Approval Permissions by Role

### Global/Executive Roles
- **General Manager**
  - **View**: All departments, all roles, all statuses
  - **Approve/Reject**: All departments (acts as assigned manager for department managers only)

- **Operation Manager**
  - **View**: All departments, all roles, all statuses
  - **Approve/Reject**: Operation department only

### Finance Roles
- **Finance Admin** (users: Mahmoud, Abdalaziz)
  - **View**: All departments, all roles; finance-related statuses across the board
    - Statuses of interest: Pending Finance Approval, Proof Pending, Proof Sent, Recurring, Completed, Rejected by Finance
    - Additional for Abdalaziz: Pending Manager Approval (only for Finance Staff, General Manager, and Operation Manager requests)
    - Additional for Abdalaziz: Rejected by Manager (only for Finance Staff, General Manager, and Operation Manager requests)
  - **Approve/Reject**: All departments as Finance Admin approvers, only after manager approval

- **Finance Admin (Abdalaziz)**
  - **View**: Same as Finance Admin
  - **Approve/Reject**: Same as Finance Admin
  - **Additional Responsibility**: Assigned Manager for Finance Staff, General Manager, and Operation Manager requests (performs manager approval for these roles before Finance Admin approval stage)

- **Finance Staff**
  - **View**: All departments, all roles; finance-related statuses across the board
    - Statuses of interest: Pending Finance Approval, Proof Pending, Proof Sent, Recurring, Completed, Rejected by Finance
    - **Additional**: Pending Manager Approval (only for their own requests)
    - **Additional**: Rejected by Manager (only for their own requests)
  - **Approve/Reject**: None
  - **Edit**: Payment date for their own recurring payment request installments only

### IT Department
- **IT Department Manager**
  - **View**: All departments, all roles; amounts are censored except for IT department requests
  - **Approve/Reject**: IT department only

- **IT Staff**
  - **View**: All departments, all roles; amounts are censored except for IT department requests
  - **Approve/Reject**: None

### Other Department Managers and Staff
For each listed department below, the rules are analogous:
- Department Manager (PR, Maintenance, Marketing, Logistic, HR, Quality Control, Procurement, Customer Service, Project)
  - **View**: At minimum their domain; primary role is approval within their department
  - **Approve/Reject**: Their own department only

- Department Staff (PR, Maintenance, Marketing, Logistic, HR, Quality Control, Procurement, Customer Service, Project)
  - **View**: Each user will only see their own requests
  - **Approve/Reject**: None
  - **Edit**: Payment date for their own recurring payment request installments only

Departments covered by the above: PR, Maintenance, Marketing, Logistic, HR, Quality Control, Procurement, Customer Service, Project.

---

## Practical Notes
- All roles can create/submit requests.
- “All departments, all roles” visibility means listings and details are accessible, constrained by any role-based field masking (e.g., IT amount censoring).
- Amount censoring for IT roles: IT manager and IT staff see uncensored amounts only for IT department requests; all other departments’ request amounts are masked.
- Only the appropriate approver for a given stage can transition the status forward or reject at that stage.

---

## RACI at a Glance
- **Responsible**: Requestor (create/submit), Department Manager (mgr approval), Finance Approver (finance approval and payment steps)
- **Accountable**: Department Manager for departmental gatekeeping; Finance Admin (Abdalaziz) for Finance approvals
- **Consulted**: Finance Admin (oversight), GM/Operation Manager as needed
- **Informed**: General Manager has full visibility across the process

---

## Notification Permissions by Role

### **Finance Admin (Mahmoud, Abdalaziz)**
- **New submissions** when requests reach "Pending Finance Approval"
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **Proof uploaded** notifications
- **Recurring payment due** notifications
- **Installment date edited** notifications (when requestors edit payment dates)
- **System-wide notifications** (all types)
- **Additional for Abdalaziz**: Updates on Finance Staff, General Manager, and Operation Manager requests (including rejections)

### **Finance Staff**
- **New submissions** when requests reach "Pending Finance Approval"
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **Proof uploaded** notifications
- **Recurring payment due** notifications
- **System-wide notifications** (all types)

### **General Manager (GM)**
- **New submissions** from users with role "Department Manager" only
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **System-wide notifications** (all types)

### **Operation Manager**
- **New submissions** from users with role "Operation Staff" only
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **System-wide notifications** (all types)

### **IT Department Manager**
- **New submissions** from users with role "IT Staff" only
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **System-wide notifications** (all types)
- **User management** notifications (user creation, role changes)

### **IT Staff**
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **System-wide notifications** (all types)
- **User management** notifications (user creation, role changes)

### **Project Staff**
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **Recurring payment due** notifications on their own requests only
- **Project-related** notifications (if any)

### **Department Managers (Non-IT)**
- **New submissions** from their own department staff only
- **Recurring payment due** notifications for their department

### **Department Staff (All departments)**
- **Updates on their own requests** only (status changes, approvals, rejections, etc.)
- **Recurring payment due** notifications for their own requests
- **Edit payment date** for their own recurring payment request installments only

### **Installment Edit Notifications**
When requestors edit payment dates for recurring payment installments:

- **Finance Admin receives**: "Installment Date Edited" notification with details of the change
- **Notification includes**: Original date, new date, requestor name, and request ID
- **Automatic cleanup**: Old payment due notifications for the original date are automatically removed
- **Smart payment due**: If the new date is today, immediate payment due notifications are sent to Finance Admin and Finance Staff
- **Prevents duplicates**: System ensures no notifications are sent on the old (pre-edited) date

### **Payment Due Notification Behavior**
- **Uses edited dates**: Payment due notifications are based on the current (edited) date, not the original date
- **Acknowledges edits**: Messages include "Date was recently edited" when applicable
- **Clean notifications**: Old date notifications are automatically cleaned up when dates are edited
- **Immediate alerts**: Same-day edits trigger immediate payment due notifications

### **System-Wide Notifications**
These are notifications that affect the entire system or multiple users:
- **System Maintenance/Updates**: "System will be down for maintenance on [date]"
- **Policy Changes**: "New approval policies have been implemented"
- **Security Alerts**: "Multiple failed login attempts detected"
- **System Errors/Issues**: "Payment processing is temporarily unavailable"
- **Administrative Announcements**: "New user roles have been added"
- **IT-Specific System Notifications**: "Server performance issues detected"

---

## Request Types by Department and Role

When creating a new payment request, users can only select from request types that are available for their department or role. The following request types are available:

### **General Manager (Role-based)**
- Personal Expenses

### **Finance Department**
- Utilities Expenses
- Coffee Shop Expenses
- Supplier Expenses

### **Operation Department**
- Refund/Reimbursement

### **PR Department**
- Permission Bills
- Flight Tickets
- Petty Cash
- Contract Expenses
- Refund/Reimbursement

### **Maintenance Department**
- Purchase Items
- AC Installment
- Repair Expenses
- Sewage Service Expenses

### **Marketing Department**
- Advertisement Expenses
- Photoshoot Expenses
- Subscription Expenses

### **Logistic Department**
- ROP Expenses
- Truck Maintenance
- Rent Expenses (Jawad)

### **HR Department**
- Salary Expenses
- Refund/Reimbursement
- Cash Advance Expenses
- Allowance Expenses

### **Quality Control Department**
- Pest Control Expenses
- Courses Expenses
- Refund/Reimbursement

### **Procurement Department**
- Purchasing Expenses

### **IT Department**
- Subscription Expenses
- Course Expenses

### **Customer Service Department**
- Refund/Reimbursement

### **Project Department**
- New Branch Expenses
- Project Expenses