# 📘 Product Requirements Document (PRD)

## 🧩 Project Title
**Payment Request Management System**

---

## 🧠 Overview
The **Payment Request Management System** allows departments to request payments through digital forms while providing Finance, Admin, and General Manager roles with tools for approval, monitoring, and reporting.  

It ensures transparency, accountability, and efficiency across all financial requests.

---

## 🎯 Objectives
- Centralize all payment requests from multiple departments.
- Digitize and standardize approval workflows.
- Provide Finance and GM with access to view financial reports.
- Enable IT and Admin users to manage all system data and approvals.

---

## 👥 User Roles & Permissions

| Role | Description | Access |
|------|--------------|---------|
| **Department Staff** | Can request payments (Item or Person). | Submit 2 forms & view own requests. |
| **Finance** | Can request for items, persons, or suppliers/rentals. | Submit 3 forms & view reports. |
| **Project** | Special role for project-related payments. | Submit Item or Company forms (2 forms). |
| **General Manager** | Oversees all financial activities. | View all reports. |
| **Admin** | Approves or sets requests as pending. | Approve, upload receipts, or mark pending. |
| **IT** | Maintains system and manages data. | Full CRUD access & report visibility. |

---

## 📋 Form Types

### 1. Item Form
- Requestor Name  
- Item Name  
- Department (auto-filled)  
- Date  
- Purpose/Description  
- Account Name  
- Account Number  
- Amount  

### 2. Person Form
- Requestor Name  
- Person/Company  
- Department (auto-filled)  
- Date  
- Purpose/Description  
- Account Name  
- Account Number  
- Amount  

### 3. Supplier/Rental Form
- Requestor Name  
- Company Name  
- Date  
- Account Name  
- Account Number  
- Amount  
- One-time / Recurring (Dropdown)  
- If Recurring → Choose interval (Monthly, Quarterly, Annually)

---

## 🔄 Workflow
1. Department submits request via form.  
2. Admin reviews in dashboard.  
3. Admin either:
   - **Approves** (uploads receipt, selects approver, checks proof box), or  
   - **Marks as Pending** (adds reason).  
4. Finance & GM can view all reports.  
5. IT manages data via CRUD operations.

---

## 📊 Reporting
- **Admin, Finance, GM, IT:** Access all reports.
- **Departments:** Access their own requests.
- Reports filter by: date, department, request type, status.

---

## 🧩 Deliverables
- Secure multi-user system.
- Approval and pending workflows.
- Upload and proof tracking.
- Dashboard and reporting for management.
