# 💾 Data Requirements Document (DRD)

## 🧩 Project Title
**Payment Request Management System**

---

## 📘 Purpose
To define the structure, storage, and relationships of data used in the Payment Request Management System.

---

## 🧱 Data Entities

### 1. Users Table

| Field | Type | Description |
|--------|------|-------------|
| user_id | INT (PK) | Unique user ID |
| username | VARCHAR | Login name |
| password | VARCHAR | Encrypted password |
| department | VARCHAR | Department name |
| role | ENUM('Admin', 'Finance', 'GM', 'IT', 'Project', '... Staff roles') | Role type |
| email | VARCHAR | Optional user email |

---

### 2. Payment Requests Table

| Field | Type | Description |
|--------|------|-------------|
| request_id | INT (PK) | Unique request ID |
| request_type | ENUM('Item', 'Person', 'Supplier/Rental', 'Company') | Form type |
| requestor_name | VARCHAR | Name of requestor |
| department | VARCHAR | Auto-filled |
| date | DATE | Date of request |
| purpose | TEXT | Purpose/description |
| account_name | VARCHAR | Account name |
| account_number | VARCHAR | Account number |
| amount | DECIMAL | Requested amount |
| recurring | ENUM('One-Time', 'Recurring') | For supplier/rental form |
| recurring_interval | VARCHAR | Interval period if recurring |
| status | ENUM('Pending', 'Approved', 'Declined') | Request status |
| reason_pending | TEXT | Reason for pending |
| receipt_image | VARCHAR | Path to uploaded receipt |
| approver | ENUM('Mahmoud', 'Abdulaziz') | Selected approver |
| proof_of_payment | BOOLEAN | Indicates proof checkbox |
| date_created | TIMESTAMP | When created |
| date_updated | TIMESTAMP | When updated |

---

### 3. Audit Logs Table

| Field | Type | Description |
|--------|------|-------------|
| log_id | INT (PK) | Unique log ID |
| user_id | INT (FK) | Related user |
| action | VARCHAR | Action performed |
| timestamp | TIMESTAMP | When action occurred |

---

## 🔗 Relationships
- **User → Payment Requests:** One-to-Many  
- **Admin → Approvals:** One-to-Many  
- **Requests → Logs:** One-to-Many

---

## 🧮 Data Flow Summary
1. User logs in and submits a payment request.  
2. Request data is stored in the `payment_requests` table.  
3. Admin reviews and updates the record status.  
4. Every action (create/update/approve) is logged in the `audit_logs` table.  
5. Finance and GM can generate reports from stored data.

---

## 📦 Storage
- Database: PostgreSQL / MySQL
- File uploads: Local `/uploads/receipts` or AWS S3
- Backup: Weekly automated database dump

---

## 🧠 Data Validation Rules
- All fields are required except `reason_pending`, `recurring_interval`, and `receipt_image`.
- `amount` must be positive numeric value.
- `account_number` must be numeric only.
- `recurring_interval` required if `recurring = 'Recurring'`.
- `approver` required only for approved requests.
