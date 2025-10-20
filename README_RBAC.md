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
  - **Approve/Reject**: All departments as Finance Admin approvers, only after manager approval

- **Finance Admin (Abdalaziz)**
  - **View**: Same as Finance Admin
  - **Approve/Reject**: Same as Finance Admin
  - **Additional Responsibility**: Assigned Manager for all Finance department requests (performs manager approval for Finance department before Finance Admin approval stage)

- **Finance (staff)**
  - **View**: All departments, all roles
  - **Approve/Reject**: None

### IT Department
- **IT Department Manager**
  - **View**: All departments, all roles; amounts are censored except for IT department requests
  - **Approve/Reject**: IT department only

- **IT Department Staff**
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