## Role-Based Access Control (RBAC) and Approval Flow

This document describes who can view what, who can approve/reject, and how a payment request moves through the workflow. Keep this as the single reference for permissions and process.

### Statuses Used in the System
- **Pending Manager Approval**: Newly submitted; waiting for the requestor's department manager.
- **Pending Finance Approval**: Approved by department manager; waiting for Finance.
- **Rejected by Manager**: Rejected by the department manager during initial review.
- **Rejected by Finance**: Rejected by Finance during review.
- **Proof Pending**: Approved by Finance and awaiting payment proof upload.
- **Proof Sent**: Proof uploaded/sent; pending any final checks or reconciliation.
- **Proof Rejected**: Proof was rejected by Finance; requestor must resubmit proof.
- **Recurring**: Recurring payment schedule item.
- **Completed**: Fully processed and finalized.

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
   - If the submitted proof is rejected by Finance → status becomes **Proof Rejected**. The requestor must re-submit proof; upon re-submission it moves to **Proof Sent** again, or back to **Proof Pending** if Finance requires a new proof submission. This loop repeats until Finance accepts the proof and advances the request to **Completed**.
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
  - **Approve/Reject (Manager Stage)**: All requests regardless of department and role
  - Note: If a temporary manager is assigned, only the temporary manager can approve/reject.

- **CEO**
  - **View**: All departments, all roles, all statuses (same visibility as GM)
  - **Approve/Reject**: None (view-only everywhere)
  - Note: CEO cannot take approval or rejection actions at any stage.

- **Operation Manager**
  - **View**: All departments, all roles, all statuses
  - **Approve/Reject (Manager Stage)**: All requests regardless of department and role
  - Note: If a temporary manager is assigned, only the temporary manager can approve/reject.

### Finance Roles
- **Finance Admin** (users: Mahmood Al-Mandhari, Abdalaziz Al-Brashdi)
  - **View**: All departments, all roles; finance-related statuses across the board
    - Statuses of interest: Pending Finance Approval, Proof Pending, Proof Sent, Recurring, Completed, Rejected by Finance
    - Additional for Abdalaziz Al-Brashdi: Pending Manager Approval (Finance Dept requests; and for Finance Staff, General Manager, Operation Manager, and CEO requests)
  - **Approve/Reject**: All departments as Finance Admin approvers, only after manager approval

- **Finance Admin (Abdalaziz Al-Brashdi)**
  - **View**: Same as Finance Admin
  - **Approve/Reject**: Same as Finance Admin
  - **Additional Responsibility**: Assigned Manager for Finance Staff, CEO, General Manager, and Operation Manager requests (performs manager approval for these roles before Finance Admin approval stage)

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

### Project Management Structure
- **Project** is managed by the **Operation Manager**
  - **Manager Assignment**: All Project users (Project Staff) are automatically assigned the Operation Manager as their manager
  - **Approval Authority**: Operation Manager approves all Project payment requests
  - **View**: Project Staff can view their own requests only
  - **Approve/Reject**: Project Staff cannot approve/reject requests (Operation Manager handles all approvals)
  - **Edit**: Payment date for their own recurring payment request installments only

### Other Department Managers and Staff
For each listed department below, the rules are analogous:
- Department Manager (PR, Maintenance, Marketing, Logistic, HR, Quality Control, Procurement, Customer Service)
  - **View**: At minimum their domain; primary role is approval within their department
  - **Approve/Reject**: Their own department only

- Department Staff (PR, Maintenance, Marketing, Logistic, HR, Quality Control, Procurement, Customer Service)
  - **View**: Each user will only see their own requests
  - **Approve/Reject**: None
  - **Edit**: Payment date for their own recurring payment request installments only

Departments covered by the above: PR, Maintenance, Marketing, Logistic, HR, Quality Control, Procurement, Customer Service.

---

## Practical Notes
- All roles can create/submit requests.
- "All departments, all roles" visibility means listings and details are accessible, constrained by any role-based field masking (e.g., IT amount censoring).
- Amount censoring for IT roles: IT manager and IT staff see uncensored amounts only for IT department requests; all other departments' request amounts are masked.
- Only the appropriate approver for a given stage can transition the status forward or reject at that stage.

### Manager Assignment Rules
- **Department Managers**: Assigned to General Manager and Operation Manager
- **General Manager**: Assigned to Abdalaziz Al-Brashdi (Finance Admin)
- **CEO**: Assigned to Abdalaziz Al-Brashdi (Finance Admin)
- **Operation Department**: Assigned to Operation Manager
- **Project**: Assigned to Operation Manager (same as Operation Department)
- **Finance Department**: Assigned to Abdalaziz Al-Brashdi (Finance Admin)
- **Office Department**: Assigned to General Manager
- **Other Departments**: Assigned to their respective Department Manager (if exists)

#### Temporary Manager (IT feature)
- IT can assign a `temporary_manager_id` to a specific request while status is `Pending Manager Approval`.
- When a temporary manager is assigned:
  - They have exclusive authority to Approve/Reject that request as manager.
  - They can view the request regardless of their role/department (Finance Admin included).
  - Original/special-case managers cannot approve/reject during the temporary assignment.
  - All approvals/rejections are attributed to the temporary manager in the UI.

#### Multiple Managers for Department Managers (GM + Operation Manager)
- Requests created by users with role `Department Manager` can be approved by either:
  - General Manager (GM), or
  - Operation Manager
- The system records the actual approver (GM or Operation Manager) and displays that person’s name.

---

## RACI at a Glance
- **Responsible**: Requestor (create/submit), Department Manager (mgr approval), Finance Approver (finance approval and payment steps)
- **Accountable**: Department Manager for departmental gatekeeping; Finance Admin (Abdalaziz Al-Brashdi) for Finance approvals
- **Consulted**: Finance Admin (oversight), GM/Operation Manager as needed
- **Informed**: General Manager has full visibility across the process

---

## Notification Permissions by Role

### **Finance Admin (Mahmoud, Abdalaziz Al-Brashdi)**
- **New submissions** when requests reach "Pending Finance Approval"
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **Proof uploaded** notifications
- **Recurring payment due** notifications
- **Installment date edited** notifications (when requestors edit payment dates)
- **System-wide notifications** (all types)
- **Additional for Abdalaziz Al-Brashdi**: 
  - **New submissions** from Finance Staff, CEO, General Manager, and Operation Manager (as their assigned manager)
  - **Updates on Finance Staff, General Manager, and Operation Manager requests** (including rejections)

### **Finance Staff**
- **New submissions** when requests reach "Pending Finance Approval"
- **Updates on their own requests** (status changes, approvals, rejections, etc.)
- **Proof uploaded** notifications
- **Recurring payment due** notifications
- **System-wide notifications** (all types)

### **General Manager (GM)**
- **New submissions** from ALL users (all roles and departments)
- **Updates on ALL requests** (status changes, approvals, rejections, proof uploaded, etc.)
- **Overdue notifications** for ALL requests (finance approval timing alerts)
- **System-wide notifications** (all types)

### **CEO**
- **Updates on their own requests only** (status changes, approvals, rejections, etc., including confirmation when submitting their own requests)
- **System-wide notifications** (all types)
- **Note**: CEO does NOT receive notifications for new requests submitted by other users

### **Operation Manager**
- **New submissions** from ALL users (all roles and departments)
- **Updates on ALL requests** (status changes, approvals, rejections, proof uploaded, etc.)
- **Overdue notifications** for ALL requests (finance approval timing alerts)
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
- **Updates on their department staff's requests** (status changes, approvals, rejections, proof uploaded, etc.)
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
- Rental Expenses
- Coffee Shop Expenses
- Food Supplier
- Vegetable/Fruits Supplier
- Cheese Supplier
- Spices Supplier
- Syrup Supplier
- Oil Supplier
- Soft Drinks Supplier
- Bakery
- Water Supplier
- Freshener Supplier
- Cleaning Supplier
- Plastics Supplier
- Garbage Plastic Supplier
- Furniture Supplier
- Gas Supplier
- Petrol
- Packing/Printing
- Customer Service
- Pest Control
- Maintenance

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

### **HR Department**
- Salary Expenses
- Refund/Reimbursement
- Cash Advance Expenses
- Allowance Expenses

### **Quality Control Department**
- Pest Control Expenses
- Course Expenses
- Refund/Reimbursement

### **Procurement Department**
- Purchasing Expenses

### **IT Department**
- Subscription Expenses
- Course Expenses

### **Customer Service Department**
- Refund/Reimbursement

### **Project**
- New Branch Expenses
- Project Expenses
- Rent Expenses

---

## Calendar Access Permissions

The calendar feature (`/admin/calendar`) provides a visual view of upcoming recurring payment due dates. Access is role-based with different data visibility:

### **Roles with Calendar Access**
- **Finance Admin** - Full calendar access to all departments' recurring payments
- **Finance Staff** - Full calendar access to all departments' recurring payments  
- **General Manager (GM)** - Full calendar access to all departments' recurring payments
- **CEO** - Full calendar access to all departments' recurring payments
- **Operation Manager** - Full calendar access to all departments' recurring payments
- **IT Staff** - Full calendar access to all departments' recurring payments
- **IT Department Manager** - Full calendar access to all departments' recurring payments
- **Project Staff** - Calendar access limited to their own department's recurring payments
- **Admin** - Full calendar access to all departments' recurring payments

### **Calendar Features**
- **Visual Calendar View**: Shows recurring payment due dates in a monthly calendar format
- **Color-coded Events**: 
  - Purple dots indicate upcoming due dates
  - Green dots indicate paid installments
- **Department Filtering**: Project Staff only see their department's payments
- **Real-time Updates**: Calendar reflects current payment status and due dates
- **Interactive Navigation**: Users can navigate between months to view upcoming payments

### **Calendar Data Visibility**
- **Finance Admin/Staff, GM, Operation Manager, IT Staff, IT Department Manager, Admin**: Can view all departments' recurring payment schedules
- **Project Staff**: Can only view their own department's recurring payment schedules
- **Other Roles**: No calendar access

### **Calendar Integration**
The calendar is accessible from:
- General Manager Dashboard
- Operation Manager Dashboard  
- IT Dashboard
- Project Dashboard
- Finance Admin Dashboard (via navigation)

The calendar helps users track upcoming payment obligations and plan financial activities accordingly.

---

## Urgent Payment Request Marking and Visual Indicators

### Urgent Request Functionality
The system includes functionality for managers to mark payment requests as urgent during the approval process. This provides visual indicators to help prioritize urgent requests across all dashboards.

### Who Can Mark Requests as Urgent
- **Department Managers**: Can mark requests as urgent when approving requests from their department
- **General Manager**: Can mark requests as urgent when approving requests from Department Managers
- **Operation Manager**: Can mark requests as urgent when approving requests from Operation and Project departments
- **Finance Admin (Abdalaziz Al-Brashdi)**: Can mark requests as urgent when approving requests from Finance Staff, General Manager, and Operation Manager

### Visual Indicators for Urgent Requests
When a payment request is marked as urgent, the following visual indicators are applied across all dashboards:

#### 1. Red Left Border
- **Style**: `border-left: 4px solid #dc3545;`
- **Color**: Bootstrap danger red (#dc3545)
- **Application**: Applied to the entire table row containing the urgent request

#### 2. URGENT Badge
- **Text**: "URGENT" in white text
- **Background**: Bootstrap danger red (#dc3545)
- **Style**: Small badge with rounded corners
- **Position**: Displayed next to the request ID
- **Font**: Bold, small size (0.7em)

### Implementation Details
- **Database Field**: `is_urgent` (Boolean, default: False)
- **Setting Location**: Manager approval form (`/request/<id>/manager_approve`)
- **Form Control**: Checkbox input with name "is_urgent"
- **Persistence**: Set during manager approval and persists throughout the request lifecycle

### Dashboard Display
Urgent requests are displayed with visual indicators on all dashboards:
- **Admin Dashboard**: Both completed and rejected request tables
- **Finance Dashboard**: All finance-related request tables
- **Department Dashboards**: All department-specific request tables
- **IT Dashboard**: All IT-related request tables
- **Operation Dashboard**: All operation-related request tables
- **Project Dashboard**: All project-related request tables
- **General Manager Dashboard**: All GM-related request tables

### Filtering Capabilities
All dashboards support filtering by urgent status:
- **"Urgent Only"**: Shows only requests marked as urgent
- **"Not Urgent"**: Shows only requests not marked as urgent
- **"All"**: Shows all requests regardless of urgent status

### Business Rules
1. **Manager Authority**: Only the assigned manager for a request can mark it as urgent
2. **Approval Stage**: Urgent marking occurs during manager approval, not during initial submission
3. **Persistence**: Once marked urgent, the status persists throughout the request lifecycle
4. **Visibility**: Urgent indicators are visible to all users who can view the request
5. **No Override**: Once set by a manager, urgent status cannot be changed by other roles

---

## View Request Tab Colors and Status Mapping

**⚠️ CRITICAL: This section defines the EXACT tab color logic for the view request page. This logic MUST NOT be changed under any circumstances. Any modifications to tab colors must be approved by the system administrator and documented here first.**

### Tab Color Meanings
The three-step approval process uses specific colors to indicate the current state of each approval stage:

- 🔴 **Red (rejected)**: This step has been rejected and requires attention
- 🟡 **Yellow (warning)**: This step is in progress or awaiting review/verification
- 🟢 **Green (completed)**: This step has been completed successfully
- ⚫ **Gray (disabled)**: This step is not yet relevant to the current request status

### Submit Request Tab
**Status**: Always **Green (completed)** for all request statuses
- This tab represents the initial submission and is always considered completed once a request exists

### Manager Approval Tab
**Color Logic** (applies to ALL users regardless of role):

| Request Status | Tab Color | Visual State | Meaning |
|----------------|-----------|--------------|---------|
| `Rejected by Manager` | 🔴 Red | `rejected` | Manager has rejected this request |
| `Pending Manager Approval` | 🟡 Yellow | `warning` | Waiting for manager approval |
| `Pending Finance Approval` | 🟢 Green | `completed` | Manager approved, moved to finance |
| `Payment Pending` | 🟢 Green | `completed` | Manager approved, moved to finance |
| `Proof Pending` | 🟢 Green | `completed` | Manager approved, moved to finance |
| `Proof Sent` | 🟢 Green | `completed` | Manager approved, moved to finance |
| `Proof Rejected` | 🟢 Green | `completed` | Manager approved, moved to finance |
| `Paid` | 🟢 Green | `completed` | Manager approved, moved to finance |
| `Completed` | 🟢 Green | `completed` | Manager approved, moved to finance |
| `Recurring` | 🟢 Green | `completed` | Manager approved, moved to finance |
| All other statuses | ⚫ Gray | `disabled` | Not yet relevant |

### Finance Admin Approval Tab
**Color Logic** (applies to ALL users regardless of role):

| Request Status | Tab Color | Visual State | Meaning |
|----------------|-----------|--------------|---------|
| `Rejected by Finance` | 🔴 Red | `rejected` | Finance has rejected this request |
| `Pending Finance Approval` | 🟡 Yellow | `warning` | Waiting for finance approval |
| `Payment Pending` | 🟡 Yellow | `warning` | Finance approved, awaiting payment |
| `Proof Pending` | 🟡 Yellow | `warning` | Finance approved, awaiting proof |
| `Proof Sent` | 🟡 Yellow | `warning` | Proof submitted, awaiting review |
| `Proof Rejected` | 🟡 Yellow | `warning` | Proof rejected, awaiting resubmission |
| `Proof Pending` + `Recurring` | 🟡 Yellow | `warning` | Recurring payment awaiting proof |
| `Proof Sent` + `Recurring` | 🟡 Yellow | `warning` | Recurring payment proof submitted |
| `Paid` | 🟢 Green | `completed` | Payment completed |
| `Completed` | 🟢 Green | `completed` | Request fully completed |
| `Recurring` | 🟢 Green | `completed` | Recurring payment active |
| All other statuses | ⚫ Gray | `disabled` | Not yet relevant |

### Implementation Requirements

#### Server-Side Template Logic (templates/view_request.html)
The server-side template MUST use this exact logic for tab colors:

```html
<!-- Manager Tab -->
<li class="step-tab {% if request.status == 'Rejected by Manager' %}rejected{% elif request.status == 'Pending Manager Approval' %}warning{% elif request.status in ['Pending Finance Approval', 'Payment Pending', 'Proof Pending', 'Proof Sent', 'Proof Rejected', 'Paid', 'Completed', 'Recurring'] %}completed{% else %}disabled{% endif %}" data-step="manager">

<!-- Finance Tab -->
<li class="step-tab {% if request.status == 'Rejected by Finance' %}rejected{% elif request.status in ['Pending Finance Approval', 'Payment Pending', 'Proof Pending', 'Proof Sent', 'Proof Rejected'] %}warning{% elif request.status in ['Paid', 'Completed', 'Recurring'] %}completed{% else %}disabled{% endif %}" data-step="finance">
```

#### Client-Side JavaScript Logic (templates/view_request.html)
The client-side JavaScript MUST use this exact logic for tab colors:

```javascript
// Manager Tab Logic
if (requestStatus === 'Pending Manager Approval') {
    managerTab.classList.add('warning');
} else if (requestStatus === 'Rejected by Manager') {
    managerTab.classList.add('rejected');
} else if (['Pending Finance Approval', 'Payment Pending', 'Proof Pending', 'Proof Sent', 'Proof Rejected', 'Paid', 'Completed', 'Recurring'].includes(requestStatus)) {
    managerTab.classList.add('completed');
} else {
    managerTab.classList.add('disabled');
}

// Finance Tab Logic
if (requestStatus === 'Rejected by Finance') {
    financeTab.classList.add('rejected');
} else if (['Pending Finance Approval', 'Payment Pending', 'Proof Pending', 'Proof Sent', 'Proof Rejected'].includes(requestStatus)) {
    financeTab.classList.add('warning');
} else if (['Paid', 'Completed', 'Recurring'].includes(requestStatus)) {
    financeTab.classList.add('completed');
} else {
    financeTab.classList.add('disabled');
}
```

### Consistency Requirements
1. **Server-side and client-side logic MUST be identical**
2. **Tab colors MUST be consistent across all user roles**
3. **No role-based differences in tab color display**
4. **No brief color flashes due to server/client mismatches**
5. **Proper class cleanup to prevent state conflicts**

### Change Control
- **Any changes to tab color logic require approval from system administrator**
- **All changes must be documented in this section before implementation**
- **Both server-side and client-side logic must be updated simultaneously**
- **Testing must verify consistency across all user roles and request statuses**

**⚠️ WARNING: Modifying tab color logic without following this documentation will result in inconsistent user experience and potential system errors.**