# Error Messages Documentation

This document provides a comprehensive list of all error messages in the finance system and how they appear in the user interface.

## Error Display Methods

The system uses **4 main methods** to display errors to users:

### 1. **Flash Messages (Server-side)**
- **Location**: Top of the page, below the header
- **Categories**: `error`, `danger`, `warning`, `success`, `info`
- **Display**:
  - **Error category**: Shown as a **centered modal dialog** with backdrop
  - **Other categories** (danger, warning, success, info): Shown as **inline alerts** with close button (×)
- **Styling**: 
  - Error modal: White dialog box with red title, dark backdrop, OK button
  - Inline alerts: Light gray background with colored left border

### 2. **JavaScript Alert() Dialogs**
- **Location**: Browser-native alert popup
- **Usage**: Client-side validation and AJAX error responses
- **Appearance**: Standard browser alert dialog

### 3. **Form Field Validation Errors**
- **Location**: Below the specific form field
- **Styling**: Red text, small font (12px), appears below input field
- **Visual**: Input field gets red border when error is present
- **Class**: `.error-message` with `.has-error` on parent `.form-group`

### 4. **HTTP Error Pages**
- **Location**: Full page replacement
- **Types**: 404 (Not Found), 403 (Forbidden), 500 (Server Error)
- **Appearance**: Centered error page with error code, message, and "Go to Dashboard" button

---

## Complete List of Error Messages

### Authentication & Login Errors

| Error Message | Category | Display Method | UI Appearance |
|--------------|----------|----------------|---------------|
| `Your session has expired. Please log in again.` | warning | Flash (inline alert) | Top of page, yellow border |
| `You were logged out due to inactivity.` | warning | Flash (inline alert) | Top of page, yellow border |
| `Your account has been locked due to too many failed login attempts. Please contact IT Staff to unlock your account.` | danger | Flash (inline alert) | Top of page, dark border |
| `No PIN generated or session expired. Please try logging in again.` | danger | Flash (inline alert) | Top of page, dark border |
| `PIN has expired. Please request a new one by logging in again.` | danger | Flash (inline alert) | Top of page, dark border |
| `Too many failed login attempts. Your account has been locked. Please contact IT Staff to unlock your account.` | danger | Flash (inline alert) | Top of page, dark border |
| `Invalid PIN. You have {X} attempt(s) remaining before your account is locked.` | danger | Flash (inline alert) | Top of page, dark border |
| `Invalid email address or password. You have {X} attempt(s) remaining before your account is locked.` | danger | Flash (inline alert) | Top of page, dark border |
| `Invalid email address or password` | danger | Flash (inline alert) | Top of page, dark border |
| `Failed to send PIN to your email. Please try again or contact IT Staff. Error: {message}` | - | JSON response | JavaScript alert |
| `Please enter your email and password first.` | - | JavaScript | Browser alert |
| `Please enter your email address.` | - | JavaScript | Browser alert |
| `PIN has expired. Please close this modal and try logging in again to get a new PIN.` | - | JavaScript | Browser alert |

### Permission & Access Errors

| Error Message | Category | Display Method | UI Appearance |
|--------------|----------|----------------|---------------|
| `Only IT department can perform this action.` | danger | Flash (inline alert) | Top of page, dark border |
| `You do not have permission to access this page.` | danger | Flash (inline alert) | Top of page, dark border |
| `You do not have permission to access this page. This dashboard is only for Procurement department users.` | danger | Flash (inline alert) | Top of page, dark border |
| `You do not have permission to view this item request.` | danger | Flash (inline alert) | Top of page, dark border |
| `You are not authorized to schedule a payment date for this request.` | error | Flash (modal dialog) | Centered modal with backdrop |
| `You are not authorized to make decisions on this request.` | danger | Flash (inline alert) | Top of page, dark border |
| `You are not authorized to reject this request.` | danger | Flash (inline alert) | Top of page, dark border |
| `Access denied. Only Procurement Department Managers can perform this action.` | danger | Flash (inline alert) | Top of page, dark border |
| `Only procurement staff can complete this request.` | danger | Flash (inline alert) | Top of page, dark border |
| `You do not have permission to complete this request.` | danger | Flash (inline alert) | Top of page, dark border |
| `Only the assigned procurement staff member can complete this request.` | danger | Flash (inline alert) | Top of page, dark border |
| `You do not have permission to update quantities for this request.` | danger | Flash (inline alert) | Top of page, dark border |
| `Only the assigned procurement staff member can update quantities for this request.` | danger | Flash (inline alert) | Top of page, dark border |
| `You do not have permission to update quantities for this request at the manager stage.` | danger | Flash (inline alert) | Top of page, dark border |
| `Only procurement staff can perform this action.` | danger | Flash (inline alert) | Top of page, dark border |
| `Access denied` | - | JSON response | JavaScript alert |
| `Permission denied` | - | JSON response | JavaScript alert |
| `Not authorized` | - | JSON response | JavaScript alert |

### Payment Request Errors

| Error Message | Category | Display Method | UI Appearance |
|--------------|----------|----------------|---------------|
| `Payment date can only be scheduled when status is Pending Manager Approval or Pending Procurement Manager Approval.` | error | Flash (modal dialog) | Centered modal with backdrop |
| `Please select a payment date.` | error | Flash (modal dialog) | Centered modal with backdrop |
| `Invalid payment date format.` | error | Flash (modal dialog) | Centered modal with backdrop |
| `This request is not pending manager approval or on hold.` | danger | Flash (inline alert) | Top of page, dark border |
| `This request is not pending manager approval.` | danger | Flash (inline alert) | Top of page, dark border |
| `This request is not pending procurement manager approval or on hold.` | danger | Flash (inline alert) | Top of page, dark border |
| `This request is not pending procurement manager approval.` | danger | Flash (inline alert) | Top of page, dark border |
| `This request is not assigned to procurement.` | danger | Flash (inline alert) | Top of page, dark border |
| `Invalid approval status.` | danger | Flash (inline alert) | Top of page, dark border |
| `Please provide a reason for rejection.` | danger | Flash (inline alert) | Top of page, dark border |
| `Amount cannot be negative.` | danger | Flash (inline alert) | Top of page, dark border |
| `Invalid amount format.` | danger | Flash (inline alert) | Top of page, dark border |
| `Please enter an amount.` | danger | Flash (inline alert) | Top of page, dark border |
| `Insufficient balance. Available balance is OMR {X}, but the requested amount is OMR {Y}. Please put the request on hold.` | danger | Flash (inline alert) | Top of page, dark border |
| `Please select a payment date.` | - | JavaScript | Browser alert |
| `Failed to schedule payment date.` | - | JavaScript | Browser alert |
| `Please select an approval status` | - | JavaScript | Browser alert |
| `Please provide a reason for rejection` | - | JavaScript | Browser alert |
| `Please provide a reason for editing the payment date.` | - | JavaScript | Browser alert |

### File Upload Errors

| Error Message | Category | Display Method | UI Appearance |
|--------------|----------|----------------|---------------|
| `File upload failed: The uploaded file(s) exceed the maximum allowed size of 100MB total. Please reduce file sizes and try again.` | error | Flash (modal dialog) | Centered modal with backdrop |
| `File validation failed. Please check file sizes and types.` | - | JavaScript | Browser alert |
| `Form submission failed. Please try again.` | - | JavaScript | Browser alert |
| `Form submission failed. Please check your connection and try again.` | - | JavaScript | Browser alert |
| `Invalid file type for receipt "{filename}". Allowed types: PDF, JPG, PNG, DOC, DOCX, XLS, XLSX` | danger | Flash (inline alert) | Top of page, dark border |
| `Receipt file "{filename}" is too large. Maximum size is {X}MB.` | danger | Flash (inline alert) | Top of page, dark border |
| `Invalid file type for invoice "{filename}". Allowed types: PDF, JPG, PNG, DOC, DOCX, XLS, XLSX` | danger | Flash (inline alert) | Top of page, dark border |
| `Invoice file "{filename}" is too large. Maximum size is {X}MB.` | danger | Flash (inline alert) | Top of page, dark border |
| `Upload Receipt file is required.` | danger | Flash (inline alert) | Top of page, dark border |
| `Upload Invoice file is required.` | danger | Flash (inline alert) | Top of page, dark border |
| `File "{filename}" is too large. Maximum size is 50MB.` | - | JavaScript | Browser alert |
| `Invalid file type for "{filename}". Allowed types: PDF, JPG, PNG, DOC, DOCX, XLS, XLSX` | - | JavaScript | Browser alert |
| `Please select a file to upload.` | - | JavaScript | Browser alert |
| `Please select at least one file to upload.` | - | JavaScript | Browser alert |
| `Failed to upload receipt. Please try again.` | - | JavaScript | Browser alert |
| `Failed to upload invoice. Please try again.` | - | JavaScript | Browser alert |
| `Invalid file type. Allowed: JPG, PNG, GIF, PDF` | - | JSON response | JavaScript alert |
| `File too large. Maximum size is {X}MB` | - | JSON response | JavaScript alert |
| `No file provided` | - | JSON response | JavaScript alert |
| `No file selected` | - | JSON response | JavaScript alert |

### Procurement Item Request Errors

| Error Message | Category | Display Method | UI Appearance |
|--------------|----------|----------------|---------------|
| `Receipt amount is required.` | danger | Flash (inline alert) | Top of page, dark border |
| `Please enter a valid positive receipt amount in OMR.` | danger | Flash (inline alert) | Top of page, dark border |
| `Invoice amount is required.` | danger | Flash (inline alert) | Top of page, dark border |
| `Please enter a valid positive invoice amount in OMR.` | danger | Flash (inline alert) | Top of page, dark border |
| `Receipt reference number is required.` | danger | Flash (inline alert) | Top of page, dark border |
| `Receipt reference number must contain only letters and numbers (no spaces or symbols).` | danger | Flash (inline alert) | Top of page, dark border |
| `Quantities can only be updated when the request is assigned to procurement.` | danger | Flash (inline alert) | Top of page, dark border |
| `Quantities can only be updated while the request is pending manager approval or on hold by manager.` | danger | Flash (inline alert) | Top of page, dark border |
| `No item names found for this request.` | danger | Flash (inline alert) | Top of page, dark border |
| `Please select at least one request.` | danger | Flash (inline alert) | Top of page, dark border |
| `Invalid request IDs.` | danger | Flash (inline alert) | Top of page, dark border |
| `No requests selected.` | danger | Flash (inline alert) | Top of page, dark border |
| `You can only bulk upload requests assigned to you.` | - | JavaScript | Browser alert |
| `Rejection reason is required.` | - | JavaScript | Browser alert |
| `No procurement members available for assignment.` | - | JavaScript | Browser alert |
| `Please select at least one receipt file to upload.` | - | JavaScript | Browser alert |
| `Please select at least one invoice file to upload.` | - | JavaScript | Browser alert |
| `Please upload a receipt before marking this installment as paid.` | - | JavaScript | Browser alert |

### Form Validation Errors

| Error Message | Category | Display Method | UI Appearance |
|--------------|----------|----------------|---------------|
| `Please fill in all required fields.` | danger | Flash (inline alert) | Top of page, dark border |
| `Name and department are required.` | danger | Flash (inline alert) | Top of page, dark border |
| `Name, department, and request type are required.` | danger | Flash (inline alert) | Top of page, dark border |
| `Request type "{name}" already exists for {department} department.` | danger | Flash (inline alert) | Top of page, dark border |
| `Person/Company name "{name}" already exists for {department} department and {request_type} request type.` | danger | Flash (inline alert) | Top of page, dark border |
| `Cannot delete request type "{name}" because it is being used by existing payment requests.` | danger | Flash (inline alert) | Top of page, dark border |
| `Please enter a location name.` | - | JavaScript | Browser alert |
| `Please enter a valid priority number (1 or higher).` | - | JavaScript | Browser alert |
| `Please select a location.` | - | JavaScript | Browser alert |
| `Please fill in the branch name.` | - | JavaScript | Browser alert |
| `Branch name must be at least 3 characters long.` | - | JavaScript | Browser alert |
| `Branch name must be less than 100 characters long.` | - | JavaScript | Browser alert |
| `Please fill in all required fields (Name, Department, and Category).` | - | JavaScript | Browser alert |
| `Item name must be at least 2 characters long.` | - | JavaScript | Browser alert |
| `Item name must be less than 200 characters long.` | - | JavaScript | Browser alert |
| `Please enter a note before saving.` | - | JavaScript | Browser alert |

### System & General Errors

| Error Message | Category | Display Method | UI Appearance |
|--------------|----------|----------------|---------------|
| `Error deleting request: {error}` | error | Flash (modal dialog) | Centered modal with backdrop |
| `Error adding request type: {error}` | danger | Flash (inline alert) | Top of page, dark border |
| `Error updating request type: {error}` | danger | Flash (inline alert) | Top of page, dark border |
| `Error deleting request type: {error}` | danger | Flash (inline alert) | Top of page, dark border |
| `Error during bulk deletion: {error}` | danger | Flash (inline alert) | Top of page, dark border |
| `Error adding person/company name option: {error}` | danger | Flash (inline alert) | Top of page, dark border |
| `Error updating person/company name option: {error}` | danger | Flash (inline alert) | Top of page, dark border |
| `An error occurred. Please try again.` | - | JSON response | JavaScript alert |
| `Error checking session` | - | JSON response | JavaScript alert |
| `Error updating installment.` | - | JSON response | JavaScript alert |
| `Error fetching edit history.` | - | JSON response | JavaScript alert |
| `Error saving note. Please try again.` | - | JavaScript | Browser alert |
| `Error updating priorities. Please refresh the page.` | - | JavaScript | Browser alert |
| `Error updating priorities: {error}` | - | JavaScript | Browser alert |
| `Failed to load history` | - | JavaScript | Browser alert |
| `Error updating installment. Please try again.` | - | JavaScript | Browser alert |
| `An error occurred while marking request as paid` | - | JSON response | JavaScript alert |
| `An error occurred while marking installment as paid` | - | JSON response | JavaScript alert |
| `An error occurred while marking installment as late` | - | JSON response | JavaScript alert |
| `Notification not found` | - | JSON response | JavaScript alert |
| `Missing field parameter` | - | JSON response | JavaScript alert |
| `No serial numbers selected` | - | JSON response | JavaScript alert |
| `Some selected serial numbers are not available` | - | JSON response | JavaScript alert |
| `Serial ID not provided` | - | JSON response | JavaScript alert |
| `Cheque serial not found` | - | JSON response | JavaScript alert |

### HTTP Error Pages

| Error Code | Title | Message | UI Appearance |
|-----------|-------|---------|--------------|
| 404 | Page Not Found | `The page you're looking for doesn't exist or has been moved.` | Full page, centered, large error code, "Go to Dashboard" button |
| 403 | Access Denied | `You don't have permission to access this resource.` | Full page, centered, large error code, "Go to Dashboard" button |
| 500 | Server Error | `Something went wrong on our end. Please try again later.` | Full page, centered, large error code, "Go to Dashboard" button |

### Maintenance Mode

| Message | Display Method | UI Appearance |
|---------|----------------|---------------|
| `The system is undergoing maintenance. Please try again later.` (default) | Full page | Centered card with tools icon, custom message |
| Custom maintenance message (set by IT) | Full page | Centered card with tools icon, custom message |

---

## UI Styling Details

### Flash Error Modal (for `error` category)
- **Position**: Fixed, centered on screen
- **Backdrop**: Dark overlay (rgba(0, 0, 0, 0.6))
- **Dialog Box**: 
  - White background
  - Rounded corners (8px)
  - Max width: 480px
  - Padding: 20px 24px
  - Shadow: 0 10px 30px rgba(0, 0, 0, 0.3)
- **Title**: 
  - Red color (#c82333)
  - Font size: 1.2rem
  - Icon: Exclamation circle
- **Body**: 
  - Dark gray text (#333)
  - Font size: 0.95rem
- **OK Button**: 
  - Red background (#c82333)
  - White text
  - Hover: Darker red (#a71d2a)
  - Min width: 80px
- **Body Scroll**: Locked when modal is open

### Flash Inline Alerts (for `danger`, `warning`, `success`, `info`)
- **Position**: Top of page, below header
- **Background**: Light gray (#f5f5f5)
- **Text**: Black (#000000)
- **Border**: 4px solid left border
  - `danger`: Dark color (var(--dark-color))
  - `warning`: Secondary color (var(--secondary-color))
  - `success`: Dark color (var(--dark-color))
  - `info`: Secondary color (var(--secondary-color))
- **Close Button**: × symbol, top right, opacity 0.7 on hover
- **Animation**: Slide in from right (0.3s ease)

### Form Field Validation Errors
- **Text Color**: Red (#dc3545)
- **Font Size**: 12px
- **Position**: Below input field, margin-top: 5px
- **Input Border**: Red (#dc3545) when error present
- **Parent Class**: `.form-group.has-error`

### HTTP Error Pages
- **Layout**: Centered container
- **Error Code**: Large, prominent display
- **Title**: H1 heading
- **Message**: Paragraph text
- **Button**: Primary button style with home icon

---

## Error Message Categories Summary

1. **`error`** → Centered modal dialog (most critical)
2. **`danger`** → Inline alert with dark border (critical but not blocking)
3. **`warning`** → Inline alert with yellow border (warnings)
4. **`success`** → Inline alert with dark border (confirmations)
5. **`info`** → Inline alert with secondary color border (informational)

---

## Notes

- **Error modal** is used for the most critical errors that require user acknowledgment
- **Inline alerts** are dismissible and less intrusive
- **JavaScript alerts** are used for client-side validation and AJAX errors
- **Form validation errors** appear inline with the form field
- **HTTP error pages** replace the entire page content
- All flash messages are stored in Flask's session and displayed on the next page load
- Error modals lock body scrolling until dismissed

