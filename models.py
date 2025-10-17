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
    name = db.Column(db.String(100), nullable=False)  # User's full name
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Admin, Finance, GM, IT, Department User, Project
    manager_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # Manager reference
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_id(self):
        return str(self.user_id)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password, password)
    
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
    
    # Dynamic fields based on request type
    item_name = db.Column(db.String(200))  # For Item type
    person_company = db.Column(db.String(200))  # For Person/Company type
    company_name = db.Column(db.String(200))  # For Supplier/Rental type
    
    department = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(12, 3), nullable=False)  # OMR supports 3 decimal places
    recurring = db.Column(db.String(20))  # One-Time, Recurring
    recurring_interval = db.Column(db.String(50))  # Monthly, Quarterly, Annually
    status = db.Column(db.String(20), default='Pending')  # Pending, Send Proof, Received Proof, Approved
    reason_pending = db.Column(db.Text)
    receipt_path = db.Column(db.String(255))
    approver = db.Column(db.String(50))  # Mahmoud, Abdulaziz
    proof_required = db.Column(db.Boolean, default=False)  # Whether proof is required
    proof_of_payment = db.Column(db.String(255))  # File path for proof uploaded by department
    approval_date = db.Column(db.Date)  # Date when request was approved
    manager_approval_date = db.Column(db.Date)  # Date when manager approved
    manager_rejection_date = db.Column(db.Date)  # Date when manager rejected
    rejection_reason = db.Column(db.Text)  # Reason for manager rejection
    is_urgent = db.Column(db.Boolean, default=False)  # Whether request is marked as urgent
    manager_approval_reason = db.Column(db.Text)  # Manager's notes when approving
    finance_rejection_date = db.Column(db.Date)  # Date when finance rejected
    completion_date = db.Column(db.Date)  # Date when request was completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional field for tracking who created the request
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    
    # Relationship to User
    user = db.relationship('User', backref='payment_requests')
    
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
            'receipt_path': self.receipt_path,
            'approver': self.approver,
            'proof_of_payment': self.proof_of_payment,
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
    
    user = db.relationship('User', backref='notifications')
    request = db.relationship('PaymentRequest', backref='notifications')
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'notification_id': self.notification_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'request_id': self.request_id
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

