# ⚙️ Technical Requirements Document (TRD)

## 💻 System Title
**Payment Request Management System**

---

## 🏗️ System Architecture

### 🔹 Type:
Client–Server (Web-based Application)

### 🔹 Tech Stack:
- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Python (Flask Framework)  
- **Database:** PostgreSQL  
- **Authentication:** Flask-Login (simple, secure, and session-based)  
- **File Storage:** Local file system (`/uploads/receipts`)  
- **Server Hosting (optional):** Gunicorn + Nginx for deployment  

---

## 🧩 System Modules

### 1. **Authentication Module**
- Login/Logout functionality for each department.
- Role-based session control using **Flask-Login**.
- Passwords hashed using **Werkzeug’s `generate_password_hash()`**.
- Session expiration handled through Flask sessions.

**Roles:**
- Department-specific Staff roles (e.g., HR Staff, Finance Staff, IT Staff, ...)
- Finance
- General Manager
- Admin
- IT
- Project

---

### 2. **Payment Request Module**
- Each department can submit payment requests.
- **Department Staff** can choose between **Item** or **Person** forms (2 forms).
- **Finance role** can use **Item**, **Person**, or **Supplier/Rental** forms (3 forms).
- **Project role** can use **Item** or **Company** forms (2 forms).
- Department field auto-fills based on logged-in user's account.

---

### 3. **Admin Dashboard Module**
- Displays all submitted requests.
- Admin can view each request’s full details.
- **Approve action:**
  - Upload a receipt image (stored locally in `/uploads/receipts`).
  - Select approver (`Mahmoud` or `Abdulaziz`).
  - Optional checkbox for “Proof of Payment”.
- **Pending action:**
  - Requires a reason for pending.
- Request status automatically updates to “Approved” or “Pending”.

---

### 4. **Finance & GM Dashboard**
- Read-only dashboard.
- Can view all requests (Approved, Pending, Declined).
- Can export reports by department, date, or status.

---

### 5. **IT Dashboard**
- Full CRUD access to all data.
- Can manage users, update requests, and perform maintenance.

---

## 🧱 Database Design

### **Database:** PostgreSQL

#### 1. Table: `users`
| Column | Type | Description |
|---------|------|-------------|
| user_id | SERIAL PRIMARY KEY | Unique ID |
| username | VARCHAR(50) | Login name |
| password | VARCHAR(255) | Hashed password |
| department | VARCHAR(100) | Department name |
| role | VARCHAR(50) | Role (Admin, Finance, GM, IT, Department Staff) |
| email | VARCHAR(100) | Optional email address |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Creation date |

---

#### 2. Table: `payment_requests`
| Column | Type | Description |
|---------|------|-------------|
| request_id | SERIAL PRIMARY KEY | Unique request ID |
| request_type | VARCHAR(50) | Type (Item, Person, Supplier/Rental, Company) |
| requestor_name | VARCHAR(100) | Requesting person’s name |
| department | VARCHAR(100) | Auto-filled department |
| date | DATE | Date of request |
| purpose | TEXT | Purpose/description |
| account_name | VARCHAR(100) | Account name |
| account_number | VARCHAR(50) | Account number |
| amount | DECIMAL(12,2) | Requested amount |
| recurring | VARCHAR(20) | (‘One-Time’, ‘Recurring’) |
| recurring_interval | VARCHAR(50) | e.g., Monthly, Quarterly, Annually |
| status | VARCHAR(20) | (‘Pending’, ‘Approved’, ‘Declined’) |
| reason_pending | TEXT | Reason for pending |
| receipt_path | VARCHAR(255) | Path to uploaded receipt |
| approver | VARCHAR(50) | (‘Mahmoud’, ‘Abdulaziz’) |
| proof_of_payment | BOOLEAN DEFAULT FALSE | Checkbox status |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Creation date |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Last update time |

---

#### 3. Table: `audit_logs`
| Column | Type | Description |
|---------|------|-------------|
| log_id | SERIAL PRIMARY KEY | Unique ID |
| user_id | INT REFERENCES users(user_id) | User who performed the action |
| action | VARCHAR(255) | Description of the action |
| timestamp | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | When it occurred |

---

## 🌐 API Endpoints (Flask)

| Method | Endpoint | Description |
|---------|-----------|-------------|
| `POST` | `/login` | Authenticate user via Flask-Login |
| `POST` | `/logout` | End session |
| `POST` | `/requests` | Submit a new payment request |
| `GET` | `/requests` | Get all requests (role-filtered) |
| `GET` | `/requests/<id>` | Get specific request details |
| `PUT` | `/requests/<id>/approve` | Approve a request |
| `PUT` | `/requests/<id>/pending` | Mark request as pending |
| `DELETE` | `/requests/<id>` | Delete request (IT role only) |
| `GET` | `/reports` | Generate department-based reports |

---

## 🔐 Security & Authentication

- **Flask-Login:** Handles user sessions.
- **Werkzeug:** For password hashing & verification.
- **Role-based Access Control:** Protects routes with decorators:
  ```python
  @login_required
  @role_required('admin')
