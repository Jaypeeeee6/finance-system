from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    __table_args__ = { 'sqlite_autoincrement': True }
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    pin = db.Column(db.String(255), nullable=True)  # 4-digit PIN (hashed)
    name = db.Column(db.String(100), nullable=False)  # User's full name
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Admin, Finance, GM, IT, Department-specific Staff roles, Project
    manager_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # Manager reference
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Account lockout fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked = db.Column(db.Boolean, default=False)
    locked_at = db.Column(db.DateTime, nullable=True)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    
    def get_id(self):
        return str(self.user_id)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password, password)
    
    def set_pin(self, pin):
        """Hash and set 4-digit PIN"""
        if pin and len(str(pin)) == 4 and str(pin).isdigit():
            self.pin = generate_password_hash(str(pin))
            return True
        return False
    
    def check_pin(self, pin):
        """Verify 4-digit PIN"""
        if not self.pin:
            return False  # No PIN set
        return check_password_hash(self.pin, str(pin))
    
    def has_pin(self):
        """Check if user has a PIN set"""
        return self.pin is not None and self.pin != ''
    
    def is_account_locked(self):
        """Check if account is locked"""
        return self.account_locked
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock account if necessary"""
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        self.last_failed_login = datetime.utcnow()
        
        if self.failed_login_attempts >= 5:
            self.account_locked = True
            self.locked_at = datetime.utcnow()
        
        db.session.commit()
    
    def reset_failed_login(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        db.session.commit()
    
    def unlock_account(self):
        """Unlock account (used by IT Staff)"""
        self.account_locked = False
        self.failed_login_attempts = 0
        self.locked_at = None
        self.last_failed_login = None
        db.session.commit()
    
    def set_temp_login_pin(self, pin, expiry_minutes=5):
        """Set temporary login PIN with expiry"""
        from datetime import timedelta
        self.temp_login_pin = generate_password_hash(str(pin))
        self.temp_pin_created_at = datetime.utcnow()
        self.temp_pin_expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        db.session.commit()
    
    def check_temp_login_pin(self, pin):
        """Verify temporary login PIN and check if it's expired"""
        if not self.temp_login_pin:
            return False, "No PIN generated. Please request a new one."
        
        # Check if PIN is expired
        if self.temp_pin_expires_at and datetime.utcnow() > self.temp_pin_expires_at:
            return False, "PIN has expired. Please request a new one."
        
        # Check if PIN matches
        if check_password_hash(self.temp_login_pin, str(pin)):
            return True, "PIN verified successfully."
        
        return False, "Invalid PIN."
    
    def clear_temp_login_pin(self):
        """Clear temporary login PIN after successful login"""
        self.temp_login_pin = None
        self.temp_pin_created_at = None
        self.temp_pin_expires_at = None
        db.session.commit()
    
    # Relationships
    manager = db.relationship('User', remote_side=[user_id], backref='subordinates')
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class PaymentRequest(db.Model):
    """Payment request model"""
    __tablename__ = 'payment_requests'
    
    request_id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(50), nullable=False)  # Item, Person, Supplier/Rental, Company
    requestor_name = db.Column(db.String(100), nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)  # Branch name for the request
    
    # Dynamic fields based on request type
    item_name = db.Column(db.String(200))  # For Item type
    person_company = db.Column(db.String(200))  # For Person/Company type
    company_name = db.Column(db.String(200))  # For Supplier/Rental type
    
    department = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(20), default='Card')  # Card or Cheque
    account_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), nullable=True)  # Nullable when payment method is Cheque
    bank_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(12, 3), nullable=False)  # OMR supports 3 decimal places
    recurring = db.Column(db.String(20))  # One-Time, Recurring
    recurring_interval = db.Column(db.String(50))  # Monthly, Quarterly, Annually
    status = db.Column(db.String(20), default='Pending')  # Pending, Send Proof, Received Proof, Approved
    reason_pending = db.Column(db.Text)
    receipt_path = db.Column(db.Text)  # DEPRECATED: Use requestor_receipt_path and finance_admin_receipt_path instead
    requestor_receipt_path = db.Column(db.Text)  # JSON string containing multiple file paths uploaded by requestor when submitting
    finance_admin_receipt_path = db.Column(db.Text)  # JSON string containing multiple file paths uploaded by finance admin when approving/completing
    approver = db.Column(db.String(50))  # Mahmoud, Abdulaziz
    proof_required = db.Column(db.Boolean, default=False)  # Whether proof is required
    proof_of_payment = db.Column(db.String(255))  # File path for proof uploaded by department
    approval_date = db.Column(db.Date)  # Date when request was approved
    payment_date = db.Column(db.Date)  # Date when payment is scheduled
    manager_approval_date = db.Column(db.Date)  # Date when manager approved
    manager_approver = db.Column(db.String(100))  # Name of the user who actually approved as manager
    manager_approver_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # ID of the user who actually approved as manager
    manager_rejection_date = db.Column(db.Date)  # Date when manager rejected
    manager_rejector = db.Column(db.String(100))  # Name of the user who actually rejected as manager
    manager_rejector_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # ID of the user who actually rejected as manager
    rejection_reason = db.Column(db.Text)  # Reason for manager rejection
    is_urgent = db.Column(db.Boolean, default=False)  # Whether request is marked as urgent
    manager_approval_reason = db.Column(db.Text)  # Manager's notes when approving
    finance_admin_note = db.Column(db.Text)  # Finance admin's note when reviewing
    finance_admin_note_added_by = db.Column(db.String(100))  # Name of user who added the note
    finance_rejection_date = db.Column(db.Date)  # Date when finance rejected
    completion_date = db.Column(db.Date)  # Date when request was completed
    additional_files = db.Column(db.Text)  # JSON string containing additional file paths uploaded by Finance Admin
    reference_number = db.Column(db.String(100))  # Reference number provided by Finance Admin when approving (alphanumeric)
    
    # Timing fields for approval process
    manager_approval_start_time = db.Column(db.DateTime)  # When manager approval process starts
    manager_approval_end_time = db.Column(db.DateTime)  # When manager approval process ends
    finance_approval_start_time = db.Column(db.DateTime)  # When finance approval process starts
    finance_approval_end_time = db.Column(db.DateTime)  # When finance approval process ends
    manager_approval_duration_minutes = db.Column(db.Integer)  # Duration in minutes
    finance_approval_duration_minutes = db.Column(db.Integer)  # Duration in minutes
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional field for tracking who created the request
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    
    # Temporary manager assignment (used when IT staff reassigns manager for specific request)
    temporary_manager_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # Archive fields for soft delete
    is_archived = db.Column(db.Boolean, default=False)  # Whether request is archived
    archived_at = db.Column(db.DateTime, nullable=True)  # When request was archived
    archived_by = db.Column(db.String(100), nullable=True)  # Name of user who archived the request
    archived_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # ID of user who archived the request
    
    # Relationship to User
    user = db.relationship('User', backref='payment_requests', foreign_keys=[user_id])
    
    # Relationship to temporary manager (if assigned)
    temporary_manager = db.relationship('User', foreign_keys=[temporary_manager_id], backref='temporarily_assigned_requests')
    
    # Relationship to user who archived the request
    archiver = db.relationship('User', foreign_keys=[archived_by_user_id], backref='archived_requests')
    
    def to_dict(self):
        """Convert request to dictionary"""
        return {
            'request_id': self.request_id,
            'request_type': self.request_type,
            'requestor_name': self.requestor_name,
            'department': self.department,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'purpose': self.purpose,
            'account_name': self.account_name,
            'account_number': self.account_number,
            'bank_name': self.bank_name,
            'amount': float(self.amount),
            'recurring': self.recurring,
            'recurring_interval': self.recurring_interval,
            'status': self.status,
            'reason_pending': self.reason_pending,
            'receipt_path': self.receipt_path,  # Legacy field
            'requestor_receipt_path': self.requestor_receipt_path,
            'finance_admin_receipt_path': self.finance_admin_receipt_path,
            'approver': self.approver,
            'proof_of_payment': self.proof_of_payment,
            'finance_admin_note': self.finance_admin_note,
            'finance_admin_note_added_by': self.finance_admin_note_added_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<PaymentRequest {self.request_id} - {self.request_type} - {self.status}>'


class AuditLog(db.Model):
    """Audit log for tracking all actions"""
    __tablename__ = 'audit_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # Allow NULL for deleted users
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    username_snapshot = db.Column(db.String(50))  # Store username for deleted users
    
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.log_id} - {self.action}>'


class Notification(db.Model):
    """Notification model for system notifications"""
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # new_submission, approval, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Related request ID for notifications about specific requests
    request_id = db.Column(db.Integer, db.ForeignKey('payment_requests.request_id'), nullable=True)
    item_request_id = db.Column(db.Integer, db.ForeignKey('procurement_item_requests.id'), nullable=True)
    
    user = db.relationship('User', backref='notifications')
    request = db.relationship('PaymentRequest', backref='notifications')
    item_request = db.relationship('ProcurementItemRequest', backref='notifications')
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'notification_id': self.notification_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'request_id': self.request_id,
            'item_request_id': self.item_request_id
        }
    
    def __repr__(self):
        return f'<Notification {self.notification_id} - {self.title}>'


class PaidNotification(db.Model):
    """Track when recurring payment notifications were marked as paid"""
    __tablename__ = 'paid_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('payment_requests.request_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    paid_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PaidNotification {self.id} - Request {self.request_id} paid on {self.paid_date}>'


class RecurringPaymentSchedule(db.Model):
    """Store variable amounts for recurring payments"""
    __tablename__ = 'recurring_payment_schedules'
    
    schedule_id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('payment_requests.request_id'), nullable=True)
    payment_date = db.Column(db.Date, nullable=False)  # When this specific payment is due
    amount = db.Column(db.Numeric(12, 3), nullable=False)  # Amount for this specific payment
    payment_order = db.Column(db.Integer, nullable=False)  # Order of this payment (1st, 2nd, etc.)
    is_paid = db.Column(db.Boolean, default=False)  # Whether this specific payment has been made
    paid_date = db.Column(db.Date)  # When this payment was actually made
    receipt_path = db.Column(db.String(255))  # Receipt file path for this installment
    invoice_path = db.Column(db.String(255))  # Invoice file path for this installment
    has_been_edited = db.Column(db.Boolean, default=False)  # Whether this installment has been edited
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to the main payment request
    request = db.relationship('PaymentRequest', backref='payment_schedules')
    
    def to_dict(self):
        """Convert schedule to dictionary"""
        return {
            'schedule_id': self.schedule_id,
            'request_id': self.request_id,
            'payment_date': self.payment_date.strftime('%Y-%m-%d') if self.payment_date else None,
            'amount': float(self.amount),
            'payment_order': self.payment_order,
            'is_paid': self.is_paid,
            'paid_date': self.paid_date.strftime('%Y-%m-%d') if self.paid_date else None,
            'receipt_path': self.receipt_path,
            'invoice_path': self.invoice_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<RecurringPaymentSchedule {self.schedule_id} - Request {self.request_id} - Payment {self.payment_order} - {self.amount} OMR>'


class LateInstallment(db.Model):
    """Track installments that were marked as late (by Admin)"""
    __tablename__ = 'late_installments'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('payment_requests.request_id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    marked_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LateInstallment {self.id} - Request {self.request_id} - {self.payment_date}>'


class InstallmentEditHistory(db.Model):
    """Track edit history for recurring payment installments"""
    __tablename__ = 'installment_edit_history'
    
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('recurring_payment_schedules.schedule_id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('payment_requests.request_id'), nullable=False)
    edited_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    old_payment_date = db.Column(db.Date, nullable=False)
    new_payment_date = db.Column(db.Date, nullable=False)
    old_amount = db.Column(db.Numeric(12, 3), nullable=False)
    new_amount = db.Column(db.Numeric(12, 3), nullable=False)
    edit_reason = db.Column(db.Text)  # Optional reason for the edit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    schedule = db.relationship('RecurringPaymentSchedule', backref='edit_history')
    request = db.relationship('PaymentRequest', backref='installment_edit_history')
    edited_by = db.relationship('User', backref='installment_edits')
    
    def to_dict(self):
        """Convert edit history to dictionary"""
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'request_id': self.request_id,
            'edited_by': self.edited_by.name if self.edited_by else 'Unknown',
            'old_payment_date': self.old_payment_date.strftime('%Y-%m-%d') if self.old_payment_date else None,
            'new_payment_date': self.new_payment_date.strftime('%Y-%m-%d') if self.new_payment_date else None,
            'old_amount': float(self.old_amount),
            'new_amount': float(self.new_amount),
            'edit_reason': self.edit_reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<InstallmentEditHistory {self.id} - Schedule {self.schedule_id} - Edited by {self.edited_by.name if self.edited_by else "Unknown"}>'


class ReturnReasonHistory(db.Model):
    """Track history of return reasons when Finance Admin returns requests to manager multiple times"""
    __tablename__ = 'return_reason_history'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('payment_requests.request_id'), nullable=False)
    return_reason = db.Column(db.Text, nullable=False)
    returned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    returned_by_name = db.Column(db.String(100), nullable=False)
    returned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    request = db.relationship('PaymentRequest', backref='return_reason_history')
    returned_by = db.relationship('User', backref='returned_requests')
    
    def to_dict(self):
        """Convert return reason history to dictionary"""
        return {
            'id': self.id,
            'request_id': self.request_id,
            'return_reason': self.return_reason,
            'returned_by': self.returned_by_name,
            'returned_at': self.returned_at.strftime('%Y-%m-%d %H:%M:%S') if self.returned_at else None
        }
    
    def __repr__(self):
        return f'<ReturnReasonHistory {self.id} - Request {self.request_id} - Returned by {self.returned_by_name}>'


class RequestType(db.Model):
    """Request types available for each department"""
    __tablename__ = 'request_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Personal Expenses", "Utilities Expenses"
    department = db.Column(db.String(100), nullable=False)  # Department this type belongs to
    is_active = db.Column(db.Boolean, default=True)  # Whether this type is currently available
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # Relationship to User who created this type
    created_by = db.relationship('User', backref='created_request_types')
    
    def to_dict(self):
        """Convert request type to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'department': self.department,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by.name if self.created_by else 'System'
        }
    
    def __repr__(self):
        return f'<RequestType {self.id} - {self.name} ({self.department})>'


class PersonCompanyOption(db.Model):
    """Person/Company Name options for specific department and request type combinations"""
    __tablename__ = 'person_company_options'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # e.g., "Dr. Scent", "Oman Oil"
    department = db.Column(db.String(100), nullable=False)  # Department this option belongs to
    request_type = db.Column(db.String(100), nullable=False)  # Request type this option belongs to
    is_active = db.Column(db.Boolean, default=True)  # Whether this option is currently available
    account_name = db.Column(db.String(200), nullable=True)  # Account name for payment requests
    account_number = db.Column(db.String(50), nullable=True)  # Account number for payment requests
    bank_name = db.Column(db.String(200), nullable=True)  # Bank name for payment requests
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # Relationship to User who created this option
    created_by = db.relationship('User', backref='created_person_company_options')
    
    def to_dict(self):
        """Convert person/company option to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'department': self.department,
            'request_type': self.request_type,
            'is_active': self.is_active,
            'account_name': self.account_name,
            'account_number': self.account_number,
            'bank_name': self.bank_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by.name if self.created_by else 'System'
        }
    
    def __repr__(self):
        return f'<PersonCompanyOption {self.id} - {self.name} ({self.department}/{self.request_type})>'


class Branch(db.Model):
    """Branch locations for the company"""
    __tablename__ = 'branches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Main Branch", "Muscat Branch"
    restaurant = db.Column(db.String(100), nullable=False)  # Location name for grouping branches
    is_active = db.Column(db.Boolean, default=True)  # Whether this branch is currently active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # Relationship to User who created this branch
    created_by = db.relationship('User', backref='created_branches')
    
    def to_dict(self):
        """Convert branch to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'restaurant': self.restaurant,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by.name if self.created_by else 'System'
        }
    
    def __repr__(self):
        return f'<Branch {self.id} - {self.name}>'


class BranchAlias(db.Model):
    """Alternate names for a Branch (used to match historical request entries)"""
    __tablename__ = 'branch_aliases'
    
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    alias_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship back to Branch; access via branch.aliases
    branch = db.relationship('Branch', backref='aliases')
    
    def __repr__(self):
        return f"<BranchAlias {self.id} - {self.alias_name} (branch_id={self.branch_id})>"


class FinanceAdminNote(db.Model):
    """Model for storing multiple finance admin notes for payment requests"""
    __tablename__ = 'finance_admin_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('payment_requests.request_id'), nullable=False)
    note_content = db.Column(db.Text, nullable=False)
    added_by = db.Column(db.String(100), nullable=False)  # Name of the user who added the note
    added_by_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # ID of the user who added the note
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    request = db.relationship('PaymentRequest', backref='finance_notes')
    user = db.relationship('User', backref='finance_notes_added')
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'note_content': self.note_content,
            'added_by': self.added_by,
            'added_by_id': self.added_by_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<FinanceAdminNote {self.id} - Request {self.request_id} by {self.added_by}>'


class ChequeBook(db.Model):
    """Cheque book model"""
    __tablename__ = 'cheque_books'
    
    id = db.Column(db.Integer, primary_key=True)
    book_no = db.Column(db.Integer, nullable=False, unique=True)
    start_serial_no = db.Column(db.Integer, nullable=False)
    last_serial_no = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # Relationship to User who created this book
    created_by = db.relationship('User', backref='created_cheque_books')
    
    # Relationship to serial numbers
    serials = db.relationship('ChequeSerial', backref='book', cascade='all, delete-orphan', lazy='dynamic')
    
    def __repr__(self):
        return f'<ChequeBook {self.id} - Book No. {self.book_no} ({self.start_serial_no}-{self.last_serial_no})>'


class ChequeSerial(db.Model):
    """Cheque serial number model"""
    __tablename__ = 'cheque_serials'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('cheque_books.id'), nullable=False)
    serial_no = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Available')  # Available, Reserved, Used, Cancelled
    payee_name = db.Column(db.String(200), nullable=True)
    cheque_date = db.Column(db.Date, nullable=True)
    amount = db.Column(db.Numeric(12, 3), nullable=True)
    upload_path = db.Column(db.String(500), nullable=True)  # Path to uploaded file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: same serial number cannot exist in the same book
    __table_args__ = (db.UniqueConstraint('book_id', 'serial_no', name='unique_book_serial'),)
    
    def __repr__(self):
        return f'<ChequeSerial {self.id} - Book {self.book_id} Serial {self.serial_no} ({self.status})>'


class ProcurementItemRequest(db.Model):
    """Procurement item request model"""
    __tablename__ = 'procurement_item_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requestor_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # Category of the item
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.String(100), nullable=True)  # Can be "10 units", "5 boxes", etc.
    purpose = db.Column(db.Text, nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)
    request_date = db.Column(db.Date, nullable=False)
    is_urgent = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Pending Manager Approval')  # Pending Manager Approval, Pending Procurement Manager Approval, Assigned to Procurement, Completed, Rejected by Manager, Rejected by Procurement Manager
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to User who created the request
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    user = db.relationship('User', backref='procurement_item_requests', foreign_keys=[user_id])
    
    # Manager approval fields
    manager_approval_date = db.Column(db.Date, nullable=True)
    manager_approver = db.Column(db.String(100), nullable=True)
    manager_approver_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    manager_rejection_date = db.Column(db.Date, nullable=True)
    manager_rejector = db.Column(db.String(100), nullable=True)
    manager_rejector_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    manager_rejection_reason = db.Column(db.Text, nullable=True)
    manager_approval_reason = db.Column(db.Text, nullable=True)
    manager_approval_start_time = db.Column(db.DateTime, nullable=True)
    manager_approval_end_time = db.Column(db.DateTime, nullable=True)
    manager_on_hold_date = db.Column(db.Date, nullable=True)
    manager_on_hold_by = db.Column(db.String(100), nullable=True)
    manager_on_hold_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    manager_on_hold_reason = db.Column(db.Text, nullable=True)
    
    # Procurement Manager approval fields
    procurement_manager_approval_date = db.Column(db.Date, nullable=True)
    procurement_manager_approver = db.Column(db.String(100), nullable=True)
    procurement_manager_approver_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    procurement_manager_rejection_date = db.Column(db.Date, nullable=True)
    procurement_manager_rejector = db.Column(db.String(100), nullable=True)
    procurement_manager_rejector_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    procurement_manager_rejection_reason = db.Column(db.Text, nullable=True)
    procurement_manager_approval_reason = db.Column(db.Text, nullable=True)
    procurement_manager_on_hold_date = db.Column(db.Date, nullable=True)
    procurement_manager_on_hold_by = db.Column(db.String(100), nullable=True)
    procurement_manager_on_hold_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    procurement_manager_on_hold_reason = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Numeric(10, 3), nullable=True)  # Amount set by Procurement Manager when approving
    payment_date = db.Column(db.Date, nullable=True)  # Date when payment is scheduled
    
    # Assignment fields
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    assignment_date = db.Column(db.DateTime, nullable=True)
    
    # Completion fields
    completed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    completion_date = db.Column(db.DateTime, nullable=True)
    completion_notes = db.Column(db.Text, nullable=True)
    receipt_path = db.Column(db.String(255), nullable=True)  # Receipt file path for completed item requests
    invoice_path = db.Column(db.String(255), nullable=True)  # Invoice file path for completed item requests
    
    # Relationships
    manager_approver_user = db.relationship('User', foreign_keys=[manager_approver_user_id], backref='approved_item_requests_as_manager')
    manager_rejector_user = db.relationship('User', foreign_keys=[manager_rejector_user_id], backref='rejected_item_requests_as_manager')
    procurement_manager_approver_user = db.relationship('User', foreign_keys=[procurement_manager_approver_user_id], backref='approved_item_requests_as_procurement_manager')
    procurement_manager_rejector_user = db.relationship('User', foreign_keys=[procurement_manager_rejector_user_id], backref='rejected_item_requests_as_procurement_manager')
    assigned_to_user = db.relationship('User', foreign_keys=[assigned_to_user_id], backref='assigned_item_requests')
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by_user_id], backref='assigned_item_requests_by_me')
    completed_by_user = db.relationship('User', foreign_keys=[completed_by_user_id], backref='completed_item_requests')
    
    def __repr__(self):
        return f'<ProcurementItemRequest {self.id} - {self.item_name} ({self.status})>'


class ProcurementCategory(db.Model):
    """Procurement category options for specific departments"""
    __tablename__ = 'procurement_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # e.g., "Kitchen Tool", "Dining", "Stationary"
    department = db.Column(db.String(100), nullable=False)  # Department this category belongs to
    is_active = db.Column(db.Boolean, default=True)  # Whether this category is currently available
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # Relationship to User who created this category
    created_by = db.relationship('User', backref='created_procurement_categories')
    
    # Relationship to items in this category
    items = db.relationship('ProcurementItem', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert procurement category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'department': self.department,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by.name if self.created_by else 'System'
        }
    
    def __repr__(self):
        return f'<ProcurementCategory {self.id} - {self.name} ({self.department})>'


class ProcurementItem(db.Model):
    """Procurement item options for specific departments and categories"""
    __tablename__ = 'procurement_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # e.g., "JUICE BLENDER (500ML)", "Pens"
    category_id = db.Column(db.Integer, db.ForeignKey('procurement_categories.id'), nullable=True)  # Category this item belongs to
    department = db.Column(db.String(100), nullable=False)  # Department this item belongs to
    description = db.Column(db.Text, nullable=True)  # Optional description
    is_active = db.Column(db.Boolean, default=True)  # Whether this item is currently available
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # Relationship to User who created this item
    created_by = db.relationship('User', backref='created_procurement_items')
    
    def to_dict(self):
        """Convert procurement item to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'department': self.department,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by.name if self.created_by else 'System'
        }
    
    def __repr__(self):
        return f'<ProcurementItem {self.id} - {self.name} ({self.department})>'