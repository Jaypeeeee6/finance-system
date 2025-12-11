# Finance System Flowcharts

This document contains comprehensive flowcharts for the Payment Request Management System, covering all major workflows and processes.

---

## 1. System Overview & Architecture

```mermaid
graph TB
    Start([User Access]) --> Login[Login Page]
    Login --> Auth{Authentication}
    Auth -->|Invalid| Login
    Auth -->|Valid| CheckRole{Check User Role}
    
    CheckRole -->|Finance Admin| FinanceAdminDash[Finance Admin Dashboard]
    CheckRole -->|Finance Staff| FinanceStaffDash[Finance Staff Dashboard]
    CheckRole -->|GM| GMDash[General Manager Dashboard]
    CheckRole -->|CEO| CEODash[CEO Dashboard]
    CheckRole -->|IT Staff/Manager| ITDash[IT Dashboard]
    CheckRole -->|Department Manager| DeptMgrDash[Department Manager Dashboard]
    CheckRole -->|Department Staff| DeptStaffDash[Department Staff Dashboard]
    CheckRole -->|Project Staff| ProjectDash[Project Dashboard]
    CheckRole -->|Operation Manager| OpMgrDash[Operation Manager Dashboard]
    CheckRole -->|Procurement Staff| ProcDash[Procurement Dashboard]
    
    FinanceAdminDash --> AdminActions[Admin Actions]
    FinanceStaffDash --> ViewReports[View Reports]
    GMDash --> ViewAll[View All Requests]
    CEODash --> ViewAll
    ITDash --> SystemMgmt[System Management]
    DeptMgrDash --> ApproveRequests[Approve/Reject Requests]
    DeptStaffDash --> CreateRequest[Create Payment Request]
    ProjectDash --> CreateRequest
    ProcDash --> ProcActions[Procurement Actions]
    
    AdminActions --> PaymentFlow[Payment Workflow]
    ApproveRequests --> PaymentFlow
    CreateRequest --> PaymentFlow
    ViewAll --> PaymentFlow
    SystemMgmt --> PaymentFlow
    ProcActions --> PaymentFlow
    
    PaymentFlow --> End([System Operations])
```

---

## 2. User Authentication & Role Routing Flow

```mermaid
flowchart TD
    Start([User Visits System]) --> CheckMaintenance{Maintenance Mode?}
    CheckMaintenance -->|Yes| ShowMaintenance[Show Maintenance Page]
    CheckMaintenance -->|No| LoginPage[Login Page]
    
    LoginPage --> EnterCreds[Enter Username/Password]
    EnterCreds --> ValidateCreds{Validate Credentials}
    
    ValidateCreds -->|Invalid| IncrementFail[Increment Failed Attempts]
    IncrementFail --> CheckLock{Account Locked?}
    CheckLock -->|Yes| ShowLocked[Show Account Locked Message]
    CheckLock -->|No| MaxAttempts{5 Failed Attempts?}
    MaxAttempts -->|Yes| LockAccount[Lock Account]
    MaxAttempts -->|No| LoginPage
    
    ValidateCreds -->|Valid| CheckPIN{Has PIN?}
    CheckPIN -->|Yes| EnterPIN[Enter PIN]
    CheckPIN -->|No| ResetFailures[Reset Failed Attempts]
    
    EnterPIN --> ValidatePIN{Valid PIN?}
    ValidatePIN -->|Invalid| LoginPage
    ValidatePIN -->|Valid| ResetFailures
    
    ResetFailures --> CheckIdleTimeout{Idle Timeout Check}
    CheckIdleTimeout --> SetSession[Set Session]
    SetSession --> RouteRole{Route by Role}
    
    RouteRole -->|Finance Admin| FinanceAdmin[Finance Admin Dashboard]
    RouteRole -->|Finance Staff| FinanceStaff[Finance Staff Dashboard]
    RouteRole -->|GM| GM[GM Dashboard]
    RouteRole -->|CEO| CEO[CEO Dashboard]
    RouteRole -->|IT Staff| IT[IT Dashboard]
    RouteRole -->|IT Manager| IT
    RouteRole -->|Department Manager| DeptMgr[Department Manager Dashboard]
    RouteRole -->|Department Staff| DeptStaff[Department Staff Dashboard]
    RouteRole -->|Project Staff| Project[Project Dashboard]
    RouteRole -->|Operation Manager| OpMgr[Operation Manager Dashboard]
    RouteRole -->|Procurement Staff| Procurement[Procurement Dashboard]
    
    FinanceAdmin --> End([Dashboard Loaded])
    FinanceStaff --> End
    GM --> End
    CEO --> End
    IT --> End
    DeptMgr --> End
    DeptStaff --> End
    Project --> End
    OpMgr --> End
    Procurement --> End
```

---

## 3. Payment Request Submission Flow

```mermaid
flowchart TD
    Start([User Creates New Request]) --> SelectType{Select Request Type}
    
    SelectType -->|Item| ItemForm[Item Form]
    SelectType -->|Person/Company| PersonForm[Person Form]
    SelectType -->|Supplier/Rental| SupplierForm[Supplier/Rental Form]
    SelectType -->|Company| CompanyForm[Company Form]
    
    ItemForm --> FillItemFields[Fill Fields:<br/>- Requestor Name<br/>- Item Name<br/>- Department<br/>- Date<br/>- Purpose<br/>- Payment Method<br/>- Account Details<br/>- Amount]
    
    PersonForm --> FillPersonFields[Fill Fields:<br/>- Requestor Name<br/>- Person/Company<br/>- Department<br/>- Date<br/>- Purpose<br/>- Payment Method<br/>- Account Details<br/>- Amount]
    
    SupplierForm --> FillSupplierFields[Fill Fields:<br/>- Requestor Name<br/>- Company Name<br/>- Date<br/>- Payment Method<br/>- Account Details<br/>- Amount<br/>- Recurring?]
    
    CompanyForm --> FillCompanyFields[Fill Fields:<br/>- Requestor Name<br/>- Company Name<br/>- Date<br/>- Payment Method<br/>- Account Details<br/>- Amount<br/>- Recurring?]
    
    FillItemFields --> CheckRecurring{Recurring?}
    FillPersonFields --> CheckRecurring
    FillSupplierFields --> CheckRecurring
    FillCompanyFields --> CheckRecurring
    
    CheckRecurring -->|Yes| SetRecurring[Set Recurring Interval:<br/>- Monthly<br/>- Quarterly<br/>- Annually<br/>- Custom Schedule]
    CheckRecurring -->|No| UploadReceipts[Upload Receipt Files]
    
    SetRecurring --> UploadReceipts
    
    UploadReceipts --> ValidateForm{Validate Form Data}
    ValidateForm -->|Invalid| ShowErrors[Show Validation Errors]
    ShowErrors --> FillItemFields
    ShowErrors --> FillPersonFields
    ShowErrors --> FillSupplierFields
    ShowErrors --> FillCompanyFields
    
    ValidateForm -->|Valid| SaveRequest[Save Payment Request]
    SaveRequest --> SetStatus[Set Status: Pending Manager Approval]
    SetStatus --> AssignManager{Assign Manager}
    
    AssignManager -->|Department Manager| DeptMgr[Department Manager]
    AssignManager -->|GM/Operation Manager| ExecMgr[GM/Operation Manager]
    AssignManager -->|Finance Admin| FinanceMgr[Finance Admin<br/>Abdalaziz Al-Brashdi]
    AssignManager -->|Temporary Manager| TempMgr[Temporary Manager<br/>Assigned by IT]
    
    DeptMgr --> CreateNotification[Create Notification]
    ExecMgr --> CreateNotification
    FinanceMgr --> CreateNotification
    TempMgr --> CreateNotification
    
    CreateNotification --> NotifyManager[Notify Manager]
    CreateNotification --> NotifyGM[Notify GM/Operation Manager]
    CreateNotification --> NotifyRequestor[Notify Requestor]
    
    NotifyManager --> LogAction[Log Action in Audit Log]
    NotifyGM --> LogAction
    NotifyRequestor --> LogAction
    
    LogAction --> End([Request Submitted Successfully])
```

---

## 4. Approval Workflow - Manager Stage

```mermaid
flowchart TD
    Start([Request: Pending Manager Approval]) --> ManagerViews[Manager Views Request]
    
    ManagerViews --> CheckAuthority{Has Approval Authority?}
    CheckAuthority -->|No| ViewOnly[View Only - No Actions]
    CheckAuthority -->|Yes| ManagerActions{Manager Decision}
    
    ManagerActions -->|Approve| StartTimer[Start Manager Approval Timer]
    ManagerActions -->|Reject| RejectReason[Enter Rejection Reason]
    ManagerActions -->|On Hold| HoldReason[Enter Hold Reason]
    
    StartTimer --> SetUrgent{Mark as Urgent?}
    SetUrgent -->|Yes| SetUrgentFlag[Set Urgent Flag]
    SetUrgent -->|No| ApprovalReason[Enter Approval Reason]
    
    SetUrgentFlag --> ApprovalReason
    ApprovalReason --> EndTimer[End Manager Approval Timer]
    EndTimer --> CalculateDuration[Calculate Approval Duration]
    CalculateDuration --> UpdateStatus[Update Status:<br/>Pending Finance Approval]
    UpdateStatus --> StartFinanceTimer[Start Finance Approval Timer]
    
    RejectReason --> UpdateStatusReject[Update Status:<br/>Rejected by Manager]
    UpdateStatusReject --> NotifyRequestorReject[Notify Requestor]
    
    HoldReason --> UpdateStatusHold[Update Status:<br/>On Hold]
    UpdateStatusHold --> SetHoldDate[Set Hold Date & Reason]
    SetHoldDate --> NotifyRequestorHold[Notify Requestor]
    
    StartFinanceTimer --> NotifyFinance[Notify Finance Admin]
    NotifyFinance --> NotifyGM[Notify GM/Operation Manager]
    NotifyFinance --> NotifyRequestor[Notify Requestor]
    
    NotifyRequestorReject --> LogActionReject[Log Action]
    NotifyRequestorHold --> LogActionHold[Log Action]
    NotifyRequestor --> LogActionApprove[Log Action]
    
    LogActionReject --> EndReject([Request Rejected])
    LogActionHold --> EndHold([Request On Hold])
    LogActionApprove --> EndApprove([Request Approved - Sent to Finance])
```

---

## 5. Approval Workflow - Finance Stage

```mermaid
flowchart TD
    Start([Request: Pending Finance Approval]) --> FinanceViews[Finance Admin Views Request]
    
    FinanceViews --> CheckFinanceAuth{Finance Admin?}
    CheckFinanceAuth -->|No| ViewOnly[View Only - No Actions]
    CheckFinanceAuth -->|Yes| FinanceDecision{Finance Decision}
    
    FinanceDecision -->|Approve| CheckProof{Proof Required?}
    FinanceDecision -->|Reject| RejectReason[Enter Rejection Reason]
    
    CheckProof -->|Yes| SetProofPending[Set Status:<br/>Proof Pending]
    CheckProof -->|No| CheckRecurring{Recurring Payment?}
    
    CheckRecurring -->|Yes| CreateSchedule[Create Recurring Schedule]
    CheckRecurring -->|No| SetCompleted[Set Status:<br/>Completed]
    
    CreateSchedule --> SetRecurringStatus[Set Status:<br/>Recurring]
    SetRecurringStatus --> CreateInstallments[Create Installments]
    CreateInstallments --> SetPaymentDates[Set Payment Dates]
    
    SetProofPending --> UploadFinanceReceipts[Upload Finance Receipts]
    UploadFinanceReceipts --> SetReference[Set Reference Number]
    SetReference --> AddFinanceNote[Add Finance Admin Note]
    AddFinanceNote --> NotifyRequestorProof[Notify Requestor:<br/>Proof Required]
    
    SetCompleted --> SetApprovalDate[Set Approval Date]
    SetApprovalDate --> SetCompletionDate[Set Completion Date]
    SetCompletionDate --> EndFinanceTimer[End Finance Approval Timer]
    EndFinanceTimer --> CalculateFinanceDuration[Calculate Finance Duration]
    CalculateFinanceDuration --> NotifyRequestorComplete[Notify Requestor:<br/>Completed]
    NotifyRequestorComplete --> NotifyAuditing[Notify Auditing Staff]
    
    RejectReason --> SetRejectStatus[Set Status:<br/>Rejected by Finance]
    SetRejectStatus --> SetRejectDate[Set Rejection Date]
    SetRejectDate --> NotifyRequestorReject[Notify Requestor:<br/>Rejected]
    
    NotifyRequestorProof --> LogProofPending[Log Action]
    NotifyRequestorComplete --> LogComplete[Log Action]
    NotifyRequestorReject --> LogReject[Log Action]
    NotifyAuditing --> LogComplete
    
    LogProofPending --> EndProofPending([Awaiting Proof])
    LogComplete --> EndComplete([Request Completed])
    LogReject --> EndReject([Request Rejected])
```

---

## 6. Proof of Payment Workflow

```mermaid
flowchart TD
    Start([Request: Proof Pending]) --> RequestorViews[Requestor Views Request]
    
    RequestorViews --> UploadProof[Upload Proof of Payment]
    UploadProof --> ValidateProof{Validate Proof File}
    
    ValidateProof -->|Invalid| ShowError[Show Error Message]
    ShowError --> UploadProof
    
    ValidateProof -->|Valid| SaveProof[Save Proof File]
    SaveProof --> UpdateStatus[Update Status:<br/>Proof Sent]
    
    UpdateStatus --> NotifyFinance[Notify Finance Admin]
    NotifyFinance --> FinanceReviews[Finance Admin Reviews Proof]
    
    FinanceReviews --> FinanceDecision{Finance Decision}
    
    FinanceDecision -->|Accept| MarkAsPaid[Mark as Paid]
    FinanceDecision -->|Reject| RejectProof[Reject Proof]
    
    MarkAsPaid --> SetCompleted[Set Status:<br/>Completed]
    SetCompleted --> SetCompletionDate[Set Completion Date]
    SetCompletionDate --> NotifyRequestorPaid[Notify Requestor:<br/>Payment Completed]
    NotifyRequestorPaid --> NotifyAuditing[Notify Auditing Staff]
    
    RejectProof --> SetProofRejected[Set Status:<br/>Proof Rejected]
    SetProofRejected --> RejectionReason[Add Rejection Reason]
    RejectionReason --> NotifyRequestorReject[Notify Requestor:<br/>Proof Rejected - Resubmit]
    
    NotifyRequestorReject --> RequestorResubmit{Requestor Resubmits?}
    RequestorResubmit -->|Yes| UploadProof
    RequestorResubmit -->|No| WaitResubmit[Wait for Resubmission]
    
    NotifyRequestorPaid --> LogPaid[Log Action]
    NotifyAuditing --> LogPaid
    NotifyRequestorReject --> LogReject[Log Action]
    
    LogPaid --> EndPaid([Payment Completed])
    LogReject --> EndReject([Proof Rejected])
    WaitResubmit --> EndWait([Awaiting Resubmission])
```

---

## 7. Recurring Payment Flow

```mermaid
flowchart TD
    Start([Recurring Payment Approved]) --> CreateSchedule[Create Recurring Schedule]
    
    CreateSchedule --> ParseInterval[Parse Recurring Interval]
    ParseInterval --> GenerateInstallments[Generate Installments]
    
    GenerateInstallments --> SetInstallmentDates[Set Payment Dates]
    SetInstallmentDates --> SetInstallmentAmounts[Set Amounts]
    
    SetInstallmentAmounts --> SaveInstallments[Save Installments to DB]
    SaveInstallments --> SetRecurringStatus[Set Status: Recurring]
    
    SetRecurringStatus --> ScheduleNotifications[Schedule Payment Due Notifications]
    
    ScheduleNotifications --> WaitPaymentDate{Payment Date Arrives}
    
    WaitPaymentDate -->|Yes| CheckPaid{Installment Paid?}
    WaitPaymentDate -->|No| WaitPaymentDate
    
    CheckPaid -->|No| SendDueNotification[Send Payment Due Notification<br/>to Finance Admin]
    CheckPaid -->|Yes| MarkInstallmentPaid[Mark Installment as Paid]
    
    SendDueNotification --> CheckOverdue{Overdue?}
    CheckOverdue -->|Yes| SendOverdueNotification[Send Overdue Notification<br/>to GM/Operation Manager]
    CheckOverdue -->|No| WaitPayment
    
    SendOverdueNotification --> WaitPayment[Wait for Payment]
    WaitPayment --> CheckPaid
    
    MarkInstallmentPaid --> CheckAllPaid{All Installments Paid?}
    
    CheckAllPaid -->|No| WaitNextInstallment[Wait for Next Installment]
    CheckAllPaid -->|Yes| SetCompleted[Set Status: Completed]
    
    WaitNextInstallment --> WaitPaymentDate
    
    SetCompleted --> NotifyRequestor[Notify Requestor]
    NotifyRequestor --> LogCompletion[Log Completion]
    
    LogCompletion --> End([Recurring Payment Completed])
    
    RequestorEditsDate[Requestor Edits Payment Date] --> ValidateNewDate{Valid Date?}
    ValidateNewDate -->|No| ShowError[Show Error]
    ValidateNewDate -->|Yes| UpdateInstallmentDate[Update Installment Date]
    UpdateInstallmentDate --> CancelOldNotifications[Cancel Old Notifications]
    CancelOldNotifications --> CreateNewNotifications[Create New Notifications]
    CreateNewNotifications --> NotifyFinanceEdit[Notify Finance Admin:<br/>Date Edited]
    NotifyFinanceEdit --> WaitPaymentDate
```

---

## 8. Cheque Management Flow

```mermaid
flowchart TD
    Start([Cheque Management]) --> CheckRole{User Role?}
    
    CheckRole -->|GM/CEO/Operation Manager| ChequeActions[Cheque Actions]
    CheckRole -->|IT Staff| ChequeBookMgmt[Cheque Book Management]
    CheckRole -->|Other| NoAccess[No Access]
    
    ChequeBookMgmt --> CreateBook[Create Cheque Book]
    CreateBook --> EnterBookDetails[Enter Details:<br/>- Book Number<br/>- Start Serial<br/>- End Serial]
    EnterBookDetails --> ValidateBook{Valid Range?}
    ValidateBook -->|No| ShowError[Show Error]
    ValidateBook -->|Yes| GenerateSerials[Generate Serial Numbers]
    GenerateSerials --> SaveBook[Save Cheque Book]
    
    ChequeActions --> ViewApproved[View Approved Requests]
    ViewApproved --> SelectRequest[Select Request for Cheque]
    SelectRequest --> ReserveCheque[Reserve Cheque Serial]
    
    ReserveCheque --> SelectBook[Select Cheque Book]
    SelectBook --> SelectSerial[Select Available Serial]
    SelectSerial --> ReserveSerial[Reserve Serial Number]
    
    ReserveSerial --> WriteCheque[Write Cheque Form]
    WriteCheque --> FillChequeDetails[Fill Details:<br/>- Payee Name<br/>- Amount<br/>- Date<br/>- Bank<br/>- Crossing Type]
    
    FillChequeDetails --> PreviewCheque[Preview Cheque]
    PreviewCheque --> GeneratePDF[Generate PDF]
    
    GeneratePDF --> UploadCheque[Upload Cheque Image]
    UploadCheque --> UpdateSerial[Update Serial Status: Used]
    UpdateSerial --> LinkToRequest[Link to Payment Request]
    
    LinkToRequest --> LogChequeAction[Log Cheque Action]
    LogChequeAction --> End([Cheque Generated])
    
    ViewChequeRegister[View Cheque Register] --> FilterCheques[Filter by:<br/>- Book Number<br/>- Serial Number<br/>- Status<br/>- Date Range]
    FilterCheques --> DisplayCheques[Display Cheques]
    DisplayCheques --> ViewDetails[View Cheque Details]
```

---

## 9. Procurement Item Request Flow

```mermaid
flowchart TD
    Start([Procurement Staff]) --> SelectCategory[Select Procurement Category]
    
    SelectCategory --> SelectItem[Select Procurement Item]
    SelectItem --> EnterQuantity[Enter Quantity]
    
    EnterQuantity --> FillRequestDetails[Fill Request Details:<br/>- Purpose<br/>- Urgency<br/>- Notes]
    
    FillRequestDetails --> SubmitRequest[Submit Item Request]
    SubmitRequest --> SetStatus[Set Status: Pending]
    
    SetStatus --> NotifyProcurementMgr[Notify Procurement Manager]
    NotifyProcurementMgr --> ManagerReviews[Manager Reviews Request]
    
    ManagerReviews --> ManagerDecision{Manager Decision}
    
    ManagerDecision -->|Approve| ApproveItemRequest[Approve Item Request]
    ManagerDecision -->|Reject| RejectItemRequest[Reject Item Request]
    
    ApproveItemRequest --> CreatePaymentRequest[Create Payment Request]
    CreatePaymentRequest --> LinkToItemRequest[Link to Item Request]
    LinkToItemRequest --> SetPaymentStatus[Set Payment Status:<br/>Pending Manager Approval]
    
    RejectItemRequest --> NotifyStaff[Notify Procurement Staff]
    
    SetPaymentStatus --> PaymentWorkflow[Follow Payment Workflow]
    PaymentWorkflow --> PaymentCompleted{Payment Completed?}
    
    PaymentCompleted -->|Yes| UpdateItemRequest[Update Item Request Status]
    PaymentCompleted -->|No| PaymentWorkflow
    
    UpdateItemRequest --> MarkFulfilled[Mark Item Request as Fulfilled]
    MarkFulfilled --> End([Item Request Completed])
```

---

## 10. Notification System Flow

```mermaid
flowchart TD
    Start([System Event Occurs]) --> DetermineEvent{Event Type?}
    
    DetermineEvent -->|Request Submitted| NewRequestEvent[New Request Event]
    DetermineEvent -->|Status Changed| StatusChangeEvent[Status Change Event]
    DetermineEvent -->|Proof Uploaded| ProofEvent[Proof Uploaded Event]
    DetermineEvent -->|Payment Due| PaymentDueEvent[Payment Due Event]
    DetermineEvent -->|Overdue| OverdueEvent[Overdue Event]
    DetermineEvent -->|System Wide| SystemEvent[System Event]
    
    NewRequestEvent --> GetRecipientsNew[Get Recipients:<br/>- Manager<br/>- GM/Operation Manager<br/>- Finance Admin]
    
    StatusChangeEvent --> GetRecipientsStatus[Get Recipients:<br/>- Requestor<br/>- Manager<br/>- GM/Operation Manager<br/>- Finance Admin]
    
    ProofEvent --> GetRecipientsProof[Get Recipients:<br/>- Finance Admin<br/>- Finance Staff]
    
    PaymentDueEvent --> GetRecipientsDue[Get Recipients:<br/>- Finance Admin<br/>- Finance Staff]
    
    OverdueEvent --> GetRecipientsOverdue[Get Recipients:<br/>- GM<br/>- Operation Manager]
    
    SystemEvent --> GetRecipientsSystem[Get Recipients:<br/>- All Users]
    
    GetRecipientsNew --> CreateNotifications[Create Notifications]
    GetRecipientsStatus --> CreateNotifications
    GetRecipientsProof --> CreateNotifications
    GetRecipientsDue --> CreateNotifications
    GetRecipientsOverdue --> CreateNotifications
    GetRecipientsSystem --> CreateNotifications
    
    CreateNotifications --> SaveToDB[Save to Database]
    SaveToDB --> EmitRealtime[Emit Real-time Update<br/>via Socket.IO]
    
    EmitRealtime --> CheckOnline{User Online?}
    CheckOnline -->|Yes| PushNotification[Push Notification]
    CheckOnline -->|No| StoreNotification[Store for Later]
    
    PushNotification --> UpdateBadge[Update Notification Badge]
    UpdateBadge --> UserViews[User Views Notification]
    
    StoreNotification --> UserLogsIn[User Logs In]
    UserLogsIn --> LoadNotifications[Load Pending Notifications]
    LoadNotifications --> UpdateBadge
    
    UserViews --> MarkRead[Mark as Read]
    MarkRead --> End([Notification Processed])
```

---

## 11. System Maintenance Flow

```mermaid
flowchart TD
    Start([IT Staff]) --> CheckITRole{IT Department?}
    
    CheckITRole -->|No| AccessDenied[Access Denied]
    CheckITRole -->|Yes| MaintenanceMenu[Maintenance Menu]
    
    MaintenanceMenu --> MaintenanceActions{Maintenance Actions}
    
    MaintenanceActions -->|Enable Maintenance| EnableMaintenance[Enable Maintenance Mode]
    MaintenanceActions -->|Disable Maintenance| DisableMaintenance[Disable Maintenance Mode]
    MaintenanceActions -->|View Status| ViewStatus[View Maintenance Status]
    MaintenanceActions -->|Feature Flags| FeatureFlags[Manage Feature Flags]
    
    EnableMaintenance --> EnterMessage[Enter Maintenance Message]
    EnterMessage --> SaveMaintenanceState[Save to maintenance.json]
    SaveMaintenanceState --> ActivateGate[Activate Maintenance Gate]
    
    ActivateGate --> BlockRequests[Block All Requests<br/>Except IT/Login]
    BlockRequests --> ShowMaintenancePage[Show Maintenance Page<br/>to All Users]
    
    DisableMaintenance --> UpdateMaintenanceState[Update maintenance.json]
    UpdateMaintenanceState --> DeactivateGate[Deactivate Maintenance Gate]
    DeactivateGate --> AllowAccess[Allow Normal Access]
    
    FeatureFlags --> ViewFlags[View Feature Flags]
    ViewFlags --> ToggleFlags[Toggle Feature Flags:<br/>- show_item_requests<br/>- show_test_login]
    ToggleFlags --> SaveFlags[Save to feature_flags.json]
    SaveFlags --> ApplyFlags[Apply Feature Flags]
    
    ViewStatus --> DisplayStatus[Display Current Status]
    
    ShowMaintenancePage --> EndMaintenance([Maintenance Active])
    AllowAccess --> EndNormal([Normal Operation])
    ApplyFlags --> EndFlags([Flags Applied])
    DisplayStatus --> EndStatus([Status Displayed])
```

---

## 12. Audit Logging Flow

```mermaid
flowchart TD
    Start([User Action Performed]) --> CaptureAction[Capture Action Details]
    
    CaptureAction --> ExtractDetails[Extract:<br/>- User ID<br/>- Action Type<br/>- Timestamp<br/>- Request ID<br/>- Details]
    
    ExtractDetails --> ValidateAction{Valid Action?}
    
    ValidateAction -->|No| SkipLog[Skip Logging]
    ValidateAction -->|Yes| CreateLogEntry[Create Audit Log Entry]
    
    CreateLogEntry --> SetTimestamp[Set Timestamp]
    SetTimestamp --> SetUserInfo[Set User Information]
    SetUserInfo --> SetActionDetails[Set Action Details]
    
    SetActionDetails --> SaveToDB[Save to audit_logs Table]
    SaveToDB --> LogSuccess{Log Saved?}
    
    LogSuccess -->|No| RetryLog[Retry Logging]
    RetryLog --> SaveToDB
    LogSuccess -->|Yes| End([Action Logged])
    
    SkipLog --> End
    
    ViewAuditLogs[View Audit Logs] --> FilterLogs[Filter by:<br/>- User<br/>- Date Range<br/>- Action Type<br/>- Request ID]
    FilterLogs --> DisplayLogs[Display Logs]
    DisplayLogs --> ExportLogs[Export Logs]
    ExportLogs --> EndView([Logs Exported])
```

---

## Legend

### Shapes Used:
- **Rectangle**: Process/Action
- **Diamond**: Decision Point
- **Rounded Rectangle**: Start/End Point
- **Parallelogram**: Input/Output

### Status Flow:
1. **Pending Manager Approval** → Manager reviews
2. **Pending Finance Approval** → Finance reviews
3. **Proof Pending** → Awaiting proof upload
4. **Proof Sent** → Proof uploaded, awaiting review
5. **Recurring** → Recurring payment active
6. **Completed** → Request fully processed
7. **Rejected by Manager** → Manager rejected
8. **Rejected by Finance** → Finance rejected
9. **Proof Rejected** → Proof rejected, resubmit required

### Key Roles:
- **Finance Admin**: Mahmoud Al-Mandhari, Abdalaziz Al-Brashdi
- **General Manager**: Oversees all operations
- **Operation Manager**: Manages operations and projects
- **Department Managers**: Approve department requests
- **IT Staff**: System maintenance and management

---

## Notes

- All workflows include notification systems
- Audit logging is performed for all critical actions
- Real-time updates via Socket.IO for status changes
- Role-based access control enforced at every step
- Maintenance mode can be enabled by IT staff
- Feature flags allow IT to toggle features temporarily

---

## 13. Recurring Cheque Payment Day Calculation Logic

### Overview
For **Cheque + Recurring** payment requests, the system calculates and displays the number of days for each payment date. This helps track how many days each cheque covers within its respective month.

### Calculation Rules

#### **Rule 1: First Payment Date (First Installment)**
For the **first payment date** in the recurring schedule:
- **Calculate**: Days from the payment date to the **end of that month** (excluding the payment date itself)
- **Formula**: `Days = Last Day of Month - Payment Day`
- **Purpose**: Shows how many days the first cheque covers in its initial month

**Example:**
- Payment Date: **December 11, 2025**
- December has **31 days**
- Calculation: 31 - 11 = **20 days**
- Meaning: The cheque covers 20 days from Dec 11 to Dec 31 (excluding Dec 11 itself)

#### **Rule 2: Subsequent Payment Dates (All Other Installments)**
For **all payment dates after the first one**:
- **Calculate**: Days from the **first day of the month** to the payment date (excluding the payment date itself)
- **Formula**: `Days = Payment Day - 1`
- **Purpose**: Shows how many days the cheque covers from the start of its month

**Examples:**

1. **December 21, 2025** (2nd installment)
   - Calculation: 21 - 1 = **20 days**
   - Meaning: The cheque covers 20 days from Dec 1 to Dec 21 (excluding Dec 21 itself)

2. **December 31, 2025** (3rd installment)
   - Calculation: 31 - 1 = **30 days**
   - Meaning: The cheque covers 30 days from Dec 1 to Dec 31 (excluding Dec 31 itself)

3. **May 1, 2026** (4th installment)
   - Calculation: 1 - 1 = **0 days**
   - Meaning: The cheque is due on the first day of the month, so it covers 0 days from the start

4. **May 15, 2026** (5th installment)
   - Calculation: 15 - 1 = **14 days**
   - Meaning: The cheque covers 14 days from May 1 to May 15 (excluding May 15 itself)

5. **May 30, 2026** (6th installment)
   - Calculation: 30 - 1 = **29 days**
   - Meaning: The cheque covers 29 days from May 1 to May 30 (excluding May 30 itself)

### Visual Example

```
Payment Schedule for Recurring Cheque:

2025-12-11 (20 days)  ← First payment: 20 days remaining in December
2025-12-21 (20 days)  ← Subsequent: 20 days from start of December
2025-12-31 (30 days)  ← Subsequent: 30 days from start of December
2026-05-01 (0 days)   ← Subsequent: 0 days (due on 1st of month)
2026-05-15 (14 days)  ← Subsequent: 14 days from start of May
2026-05-30 (29 days)  ← Subsequent: 29 days from start of May
```

### Why This Logic?

1. **First Payment**: Represents the **remaining days** in the first month from when the payment starts
2. **Subsequent Payments**: Represents the **coverage period** from the beginning of each month to the payment date
3. **Business Purpose**: Helps finance track:
   - How many days each cheque payment period covers
   - The billing cycle for each installment
   - Cash flow planning and reconciliation

### Important Notes

- This calculation **only applies** to requests where:
  - `payment_method = 'Cheque'` **AND**
  - `recurring = 'Recurring'`
- For other payment methods (Card) or one-time payments, dates are shown **without day calculations**
- The calculation is **automatic** and displayed in reports and request views
- Days are calculated **exclusively** (the payment date itself is not counted)

