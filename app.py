from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime, date, timedelta
import re
from models import db, User, PaymentRequest, AuditLog, Notification, PaidNotification, RecurringPaymentSchedule
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Make timedelta available in templates
from datetime import timedelta
app.jinja_env.globals.update(timedelta=timedelta)

def format_recurring_schedule(interval):
    """Format recurring interval into human-readable text"""
    try:
        parts = interval.split(':')
        frequency = parts[0]
        interval_value = int(parts[1])
        
        if frequency == 'daily':
            if interval_value == 1:
                return "Daily"
            else:
                return f"Every {interval_value} days"
        elif frequency == 'weekly':
            if interval_value == 1:
                return "Weekly"
            else:
                return f"Every {interval_value} weeks"
        elif frequency == 'monthly':
            if interval_value == 1:
                return "Monthly"
            else:
                return f"Every {interval_value} months"
        elif frequency == 'quarterly':
            if interval_value == 1:
                return "Quarterly"
            else:
                return f"Every {interval_value} quarters"
        elif frequency == 'yearly':
            if interval_value == 1:
                return "Yearly"
            else:
                return f"Every {interval_value} years"
    except (ValueError, IndexError):
        return "Invalid schedule"

# Make the function available in templates
app.jinja_env.globals.update(format_recurring_schedule=format_recurring_schedule)

# Initialize database
db.init_app(app)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_room')
def handle_join_room(data):
    """Handle client joining a room"""
    room = data.get('room')
    if room and current_user.is_authenticated:
        if room == 'finance_admin' and current_user.role in ['Finance', 'Admin']:
            join_room(room)
            print(f'User {current_user.username} joined room: {room}')
        elif room == 'all_users':
            join_room(room)
            print(f'User {current_user.username} joined room: {room}')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))


def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_action(action):
    """Helper function to log user actions"""
    if current_user.is_authenticated:
        log = AuditLog(
            user_id=current_user.user_id, 
            action=action,
            username_snapshot=current_user.username
        )
        db.session.add(log)
        db.session.commit()


def create_notification(user_id, title, message, notification_type, request_id=None):
    """Helper function to create notifications"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        request_id=request_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def create_recurring_payment_schedule(request_id, total_amount, payment_schedule_data):
    """Create a recurring payment schedule with variable amounts"""
    try:
        # Clear any existing schedule for this request
        RecurringPaymentSchedule.query.filter_by(request_id=request_id).delete()
        
        # Create new schedule entries
        for i, payment_data in enumerate(payment_schedule_data, 1):
            schedule_entry = RecurringPaymentSchedule(
                request_id=request_id,
                payment_date=datetime.strptime(payment_data['date'], '%Y-%m-%d').date(),
                amount=payment_data['amount'],
                payment_order=i
            )
            db.session.add(schedule_entry)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error creating payment schedule: {e}")
        return False

def get_payment_schedule(request_id):
    """Get the payment schedule for a specific request"""
    schedules = RecurringPaymentSchedule.query.filter_by(request_id=request_id).order_by(RecurringPaymentSchedule.payment_order).all()
    return [schedule.to_dict() for schedule in schedules]

def check_recurring_payments_due():
    """Check for recurring payments due today and create notifications"""
    today = date.today()
    
    # Get all approved recurring payment requests
    recurring_requests = PaymentRequest.query.filter_by(
        recurring='Recurring',
        status='Approved'
    ).all()
    
    for request in recurring_requests:
        # Check if this request has a custom payment schedule
        payment_schedules = RecurringPaymentSchedule.query.filter_by(
            request_id=request.request_id,
            is_paid=False
        ).order_by(RecurringPaymentSchedule.payment_order).all()
        
        if payment_schedules:
            # Handle variable amount recurring payments
            for schedule in payment_schedules:
                if schedule.payment_date == today:
                    # Check if payment was already marked as paid today
                    paid_today = PaidNotification.query.filter_by(
                        request_id=request.request_id,
                        paid_date=today
                    ).first()
                    
                    if paid_today:
                        continue  # Skip this payment - already marked as paid today
                    
                    # Check if notification already exists for today
                    start_of_day = datetime.combine(today, datetime.min.time())
                    end_of_day = datetime.combine(today, datetime.max.time())
                    
                    existing_notification = Notification.query.filter_by(
                        request_id=request.request_id,
                        notification_type='recurring_due'
                    ).filter(
                        Notification.created_at >= start_of_day,
                        Notification.created_at <= end_of_day
                    ).first()
                    
                    if not existing_notification:
                        # Create notifications for all users in the department
                        department_users = User.query.filter_by(department=request.department).all()
                        for user in department_users:
                            create_notification(
                                user_id=user.user_id,
                                title="Recurring Payment Due",
                                message=f'Recurring payment due today for {request.request_type} - {request.purpose} (Amount: {schedule.amount} OMR)',
                                notification_type='recurring_due',
                                request_id=request.request_id
                            )
                        
                        # Log the action
                        log_action(f"Recurring payment due notification created for request #{request.request_id} - Payment {schedule.payment_order}")
        else:
            # Handle traditional recurring payments (single amount)
            if is_payment_due_today(request, today):
                # Check if payment was already marked as paid today
                paid_today = PaidNotification.query.filter_by(
                    request_id=request.request_id,
                    paid_date=today
                ).first()
                
                if paid_today:
                    continue  # Skip this payment - already marked as paid today
                
                # Check if notification already exists for today (more robust check)
                start_of_day = datetime.combine(today, datetime.min.time())
                end_of_day = datetime.combine(today, datetime.max.time())
                
                existing_notification = Notification.query.filter_by(
                    request_id=request.request_id,
                    notification_type='recurring_due'
                ).filter(
                    Notification.created_at >= start_of_day,
                    Notification.created_at <= end_of_day
                ).first()
                
                if not existing_notification:
                    # Create notification for all admin and project users
                    admin_users = User.query.filter(User.role.in_(['Admin', 'Project'])).all()
                    for user in admin_users:
                        create_notification(
                            user_id=user.user_id,
                            title="Recurring Payment Due",
                            message=f'Recurring payment due today for {request.request_type} - {request.purpose}',
                            notification_type='recurring_due',
                            request_id=request.request_id
                        )
                    
                    # Log the action
                    log_action(f"Recurring payment due notification created for request #{request.request_id}")

def is_payment_due_today(request, today):
    """Check if a recurring payment is due today based on its configuration"""
    if not request.recurring_interval:
        return False
    
    try:
        # Parse the recurring interval configuration
        parts = request.recurring_interval.split(':')
        frequency = parts[0]
        interval = int(parts[1])
        
        if frequency == 'daily':
            # Daily payments - check if it's been the right number of days AND time has passed
            days_since_created = (today - request.date).days
            
            # Parse the time from the recurring interval
            time_parts = request.recurring_interval.split(':')
            if len(time_parts) >= 5 and time_parts[2] == 'time':
                try:
                    scheduled_hour = int(time_parts[3])
                    scheduled_minute = int(time_parts[4])
                    
                    # Use local time instead of UTC
                    from datetime import datetime
                    current_time = datetime.now()
                    scheduled_time = datetime.combine(today, datetime.min.time().replace(hour=scheduled_hour, minute=scheduled_minute))
                    
                    
                    # Check if it's the right day and time has passed
                    if interval == 1:
                        # Every day - due if it's the same day or later AND time has passed
                        if days_since_created >= 0:
                            return current_time >= scheduled_time
                    else:
                        # Every X days - due if it's been X days since creation AND time has passed
                        if days_since_created > 0 and days_since_created % interval == 0:
                            return current_time >= scheduled_time
                except (ValueError, IndexError):
                    # If time parsing fails, fall back to day-only logic
                    pass
            
            # Fallback to day-only logic if time parsing fails
            if interval == 1:
                return days_since_created >= 0
            else:
                return days_since_created > 0 and days_since_created % interval == 0
            
        elif frequency == 'weekly':
            # Weekly payments - check if it's the right day of week
            if len(parts) > 2 and parts[2] == 'days':
                selected_days = parts[3].split(',')
                weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                today_weekday = weekday_names[today.weekday()]
                return today_weekday in selected_days
            else:
                # Default to same day of week as created
                return today.weekday() == request.date.weekday()
                
        elif frequency == 'monthly':
            # Monthly payments - check if it's the right day of month and enough months have passed
            if len(parts) > 2 and parts[2] == 'days':
                selected_days = [int(d) for d in parts[3].split(',')]
                if today.day in selected_days:
                    # Check if enough months have passed since creation
                    months_since_created = (today.year - request.date.year) * 12 + (today.month - request.date.month)
                    # Always require at least 1 month to pass (never due on creation day)
                    return months_since_created > 0 and months_since_created % interval == 0
            else:
                # Default to same day of month as created
                if today.day == request.date.day:
                    months_since_created = (today.year - request.date.year) * 12 + (today.month - request.date.month)
                    # Always require at least 1 month to pass (never due on creation day)
                    return months_since_created > 0 and months_since_created % interval == 0
            return False
                
        elif frequency == 'quarterly':
            # Quarterly payments - check if it's the right month and day
            if len(parts) > 2 and parts[2] == 'months':
                # Convert month names to numbers
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                             'July', 'August', 'September', 'October', 'November', 'December']
                selected_month_names = [m.strip() for m in parts[3].split(',')]
                selected_months = [month_names.index(m) + 1 for m in selected_month_names if m in month_names]
                
                if today.month in selected_months:
                    if len(parts) > 4 and parts[4] == 'days':
                        selected_days = [int(d) for d in parts[5].split(',')]
                        if today.day in selected_days:
                            # Check if enough quarters have passed
                            months_since_created = (today.year - request.date.year) * 12 + (today.month - request.date.month)
                            return months_since_created > 0 and months_since_created % (interval * 3) == 0
                    else:
                        if today.day == request.date.day:
                            months_since_created = (today.year - request.date.year) * 12 + (today.month - request.date.month)
                            return months_since_created > 0 and months_since_created % (interval * 3) == 0
            return False
            
        elif frequency == 'yearly':
            # Yearly payments - check if it's the right month and day
            if len(parts) > 2 and parts[2] == 'months':
                # Convert month names to numbers
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                             'July', 'August', 'September', 'October', 'November', 'December']
                selected_month_names = [m.strip() for m in parts[3].split(',')]
                selected_months = [month_names.index(m) + 1 for m in selected_month_names if m in month_names]
                
                if today.month in selected_months:
                    if len(parts) > 4 and parts[4] == 'days':
                        selected_days = [int(d) for d in parts[5].split(',')]
                        if today.day in selected_days:
                            # Check if enough years have passed
                            years_since_created = today.year - request.date.year
                            return years_since_created > 0 and years_since_created % interval == 0
                    else:
                        if today.day == request.date.day:
                            years_since_created = today.year - request.date.year
                            return years_since_created > 0 and years_since_created % interval == 0
            return False
            
    except (ValueError, IndexError, AttributeError):
        # If parsing fails, don't create notification
        return False
    
    return False


def notify_finance_and_admin(title, message, notification_type, request_id=None):
    """Notify Finance and Admin users about new submissions"""
    # Get all Finance and Admin users
    finance_admin_users = User.query.filter(User.role.in_(['Finance', 'Admin'])).all()
    
    for user in finance_admin_users:
        create_notification(
            user_id=user.user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            request_id=request_id
        )
    
    # Emit real-time notification to Finance and Admin users
    socketio.emit('new_notification', {
        'title': title,
        'message': message,
        'type': notification_type,
        'request_id': request_id
    }, room='finance_admin')


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    """Redirect to login or dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            log_action(f"User {username} logged in")
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout current user"""
    log_action(f"User {current_user.username} logged out")
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - routes to appropriate dashboard based on role"""
    role = current_user.role
    
    if role == 'Admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'Finance':
        return redirect(url_for('finance_dashboard'))
    elif role == 'GM':
        return redirect(url_for('gm_dashboard'))
    elif role == 'IT':
        return redirect(url_for('it_dashboard'))
    elif role == 'Project':
        return redirect(url_for('project_dashboard'))
    elif role == 'Operation Manager':
        return redirect(url_for('operation_dashboard'))
    else:  # Department User
        return redirect(url_for('department_dashboard'))


@app.route('/department/dashboard')
@login_required
@role_required('Department User', 'Finance', 'Project')
def department_dashboard():
    """Dashboard for department users, finance, and project users"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # Get paginated requests for current user
    requests_pagination = PaymentRequest.query.filter_by(user_id=current_user.user_id).order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('department_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         user=current_user)


@app.route('/admin/dashboard')
@login_required
@role_required('Admin')
def admin_dashboard():
    """Dashboard for admin - shows all requests with optional status filtering"""
    # Check for recurring payments due today
    check_recurring_payments_due()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status_filter = request.args.get('status', None)
    department_filter = request.args.get('department', None)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # Build query with optional status and department filters
    query = PaymentRequest.query
    if status_filter:
        query = query.filter(PaymentRequest.status == status_filter)
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    notifications = Notification.query.filter_by(user_id=current_user.user_id).order_by(Notification.created_at.desc()).limit(5).all()
    unread_count = Notification.query.filter_by(user_id=current_user.user_id, is_read=False).count()
    
    return render_template('admin_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         user=current_user, 
                         notifications=notifications, 
                         unread_count=unread_count,
                         status_filter=status_filter,
                         department_filter=department_filter)


@app.route('/finance/dashboard')
@login_required
@role_required('Finance')
def finance_dashboard():
    """Dashboard for finance - can view all reports and submit requests"""
    # Check for recurring payments due today
    check_recurring_payments_due()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    department_filter = request.args.get('department', None)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # Build query with optional department filter
    query = PaymentRequest.query
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    notifications = Notification.query.filter_by(user_id=current_user.user_id).order_by(Notification.created_at.desc()).limit(5).all()
    unread_count = Notification.query.filter_by(user_id=current_user.user_id, is_read=False).count()
    
    return render_template('finance_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         user=current_user, 
                         notifications=notifications, 
                         unread_count=unread_count,
                         department_filter=department_filter)


@app.route('/gm/dashboard')
@login_required
@role_required('GM')
def gm_dashboard():
    """Dashboard for General Manager - view all reports (Approved/Pending only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    department_filter = request.args.get('department', None)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # Build query with optional department filter
    query = PaymentRequest.query
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Calculate statistics (only Approved and Pending)
    all_requests = PaymentRequest.query.all()
    total_requests = len(all_requests)
    approved = len([r for r in all_requests if r.status == 'Approved'])
    pending = len([r for r in all_requests if r.status == 'Pending'])
    total_amount = sum([float(r.amount) for r in all_requests if r.status == 'Approved'])
    
    stats = {
        'total_requests': total_requests,
        'approved': approved,
        'pending': pending,
        'total_amount': total_amount
    }
    
    return render_template('gm_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         stats=stats, 
                         user=current_user,
                         department_filter=department_filter)


@app.route('/it/dashboard')
@login_required
@role_required('IT')
def it_dashboard():
    """Dashboard for IT - full CRUD access"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    department_filter = request.args.get('department', None)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # Build query with optional department filter
    query = PaymentRequest.query
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users = User.query.all()
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
    return render_template('it_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         users=users, 
                         logs=logs, 
                         user=current_user,
                         department_filter=department_filter)


@app.route('/project/dashboard')
@login_required
@role_required('Project')
def project_dashboard():
    """Dashboard for project users - can request payments and view due dates"""
    # Check for recurring payments due today
    check_recurring_payments_due()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status_filter = request.args.get('status', None)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # Build query with optional status filter
    query = PaymentRequest.query.filter_by(user_id=current_user.user_id)
    if status_filter:
        query = query.filter(PaymentRequest.status == status_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get notifications for project users (only due date notifications)
    notifications = Notification.query.filter_by(
        user_id=current_user.user_id,
        notification_type='recurring_due'
    ).order_by(Notification.created_at.desc()).limit(5).all()
    unread_count = Notification.query.filter_by(
        user_id=current_user.user_id, 
        is_read=False,
        notification_type='recurring_due'
    ).count()
    
    return render_template('project_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         user=current_user,
                         notifications=notifications,
                         unread_count=unread_count,
                         status_filter=status_filter)


@app.route('/operation/dashboard')
@login_required
@role_required('Operation Manager')
def operation_dashboard():
    """Dashboard for operation manager - can view all requests but only in dashboard"""
    # Check for recurring payments due today
    check_recurring_payments_due()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status_filter = request.args.get('status', None)
    department_filter = request.args.get('department', None)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # Build query with optional status and department filters - Operation Manager sees only Maintenance, Operation, and Project Department
    query = PaymentRequest.query.filter(PaymentRequest.department.in_(['Maintenance', 'Operation', 'Project Department']))
    if status_filter:
        query = query.filter(PaymentRequest.status == status_filter)
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get notifications for operation manager (all notifications, same as admin)
    notifications = Notification.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).limit(5).all()
    unread_count = Notification.query.filter_by(
        user_id=current_user.user_id, 
        is_read=False
    ).count()
    
    return render_template('operation_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         user=current_user,
                         notifications=notifications,
                         unread_count=unread_count,
                         status_filter=status_filter,
                         department_filter=department_filter)


# ==================== PAYMENT REQUEST ROUTES ====================

@app.route('/request/new', methods=['GET', 'POST'])
@login_required
def new_request():
    """Create a new payment request"""
    if request.method == 'POST':
        request_type = request.form.get('request_type')
        requestor_name = request.form.get('requestor_name')
        date = datetime.utcnow().date()  # Automatically use today's date
        purpose = request.form.get('purpose')
        account_name = request.form.get('account_name')
        account_number = request.form.get('account_number')
        amount = request.form.get('amount')
        recurring = request.form.get('recurring', 'One-Time')
        recurring_interval = request.form.get('recurring_interval')
        
        # Get dynamic fields based on request type
        item_name = request.form.get('item_name')
        person_company = request.form.get('person_company')
        company_name = request.form.get('company_name')
        
        # Create new request
        new_req = PaymentRequest(
            request_type=request_type,
            requestor_name=requestor_name,
            item_name=item_name if request_type == 'Item' else None,
            person_company=person_company if request_type in ['Person', 'Company'] else None,
            company_name=company_name if request_type == 'Supplier/Rental' else None,
            department=current_user.department,
            date=date,
            purpose=purpose,
            account_name=account_name,
            account_number=account_number,
            amount=amount,
            recurring=recurring,
            recurring_interval=recurring_interval if recurring == 'Recurring' else None,
            status='Pending',
            user_id=current_user.user_id
        )
        
        db.session.add(new_req)
        db.session.commit()
        
        # Handle variable amount recurring payments
        if recurring == 'Recurring' and request.form.get('variable_amounts') == 'true':
            try:
                # Get the payment schedule data from the form
                payment_schedule_data = []
                schedule_data = request.form.get('payment_schedule', '[]')
                import json
                schedule_list = json.loads(schedule_data)
                
                for payment in schedule_list:
                    payment_schedule_data.append({
                        'date': payment['date'],
                        'amount': payment['amount']
                    })
                
                # Create the payment schedule
                if payment_schedule_data:
                    create_recurring_payment_schedule(new_req.request_id, amount, payment_schedule_data)
                    log_action(f"Created variable amount payment schedule for request #{new_req.request_id}")
            except Exception as e:
                print(f"Error creating payment schedule: {e}")
                flash('Payment request created but schedule configuration failed. Please contact admin.', 'warning')
        
        log_action(f"Created payment request #{new_req.request_id} - {request_type}")
        
        # Create notifications for Finance and Admin users
        notify_finance_and_admin(
            title="New Payment Request Submitted",
            message=f"New {request_type} request submitted by {requestor_name} from {current_user.department} department for OMR {amount}",
            notification_type="new_submission",
            request_id=new_req.request_id
        )
        
        # Emit real-time event to all connected clients
        socketio.emit('new_request', {
            'request_id': new_req.request_id,
            'request_type': new_req.request_type,
            'requestor_name': new_req.requestor_name,
            'department': new_req.department,
            'amount': float(new_req.amount),
            'status': new_req.status,
            'date': new_req.date.strftime('%Y-%m-%d')
        })
        
        flash('Payment request submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Pass today's date to template for display
    today = datetime.utcnow().date().strftime('%Y-%m-%d')
    return render_template('new_request.html', user=current_user, today=today)


@app.route('/api/payment-schedule/<int:request_id>')
@login_required
def get_payment_schedule_api(request_id):
    """API endpoint to get payment schedule for a request"""
    try:
        schedule = get_payment_schedule(request_id)
        return jsonify({'success': True, 'schedule': schedule})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors"""
    return '', 204  # No content response


@app.route('/write-cheque', methods=['GET', 'POST'])
@login_required
@role_required('GM', 'Operation Manager')
def write_cheque():
    """Write a cheque for approved payment requests"""
    if request.method == 'POST':
        # Handle cheque writing logic here
        flash('Cheque written successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get approved payment requests that need cheques
    approved_requests = PaymentRequest.query.filter_by(status='Approved').all()
    
    return render_template('write_cheque.html', 
                         user=current_user, 
                         approved_requests=approved_requests)


@app.route('/request/<int:request_id>')
@login_required
def view_request(request_id):
    """View a specific payment request"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check permissions
    if current_user.role not in ['Admin', 'Finance', 'GM', 'IT', 'Project']:
        if req.user_id != current_user.user_id:
            flash('You do not have permission to view this request.', 'danger')
            return redirect(url_for('dashboard'))
    
    # Mark notifications related to this request as read for Finance and Admin users
    if current_user.role in ['Finance', 'Admin']:
        Notification.query.filter_by(
            user_id=current_user.user_id,
            request_id=request_id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
    
    return render_template('view_request.html', request=req, user=current_user)


@app.route('/request/<int:request_id>/approve', methods=['POST'])
@login_required
@role_required('Admin')
def approve_request(request_id):
    """Approve a payment request"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    approver = request.form.get('approver')
    proof_required = request.form.get('proof_required') == 'on'
    
    # Handle receipt upload
    receipt_file = request.files.get('receipt')
    if receipt_file and allowed_file(receipt_file.filename):
        filename = secure_filename(receipt_file.filename)
        # Add timestamp to filename to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        receipt_file.save(filepath)
        req.receipt_path = filename
    
    req.approver = approver
    req.proof_required = proof_required
    req.updated_at = datetime.utcnow()
    
    if proof_required:
        # Proof is required - set status to Send Proof
        req.status = 'Send Proof'
        flash(f'Payment request #{request_id} approved. Waiting for proof of payment from department.', 'info')
        log_action(f"Approved payment request #{request_id} - Proof required")
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Send Proof',
            'approver': approver
        })
    else:
        # No proof required - directly approved
        req.status = 'Approved'
        req.approval_date = datetime.utcnow().date()  # Set approval date
        flash(f'Payment request #{request_id} has been approved.', 'success')
        log_action(f"Approved payment request #{request_id} - No proof required")
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Approved',
            'approver': approver
        })
    
    db.session.commit()
    
    return redirect(url_for('admin_dashboard'))


@app.route('/request/<int:request_id>/pending', methods=['POST'])
@login_required
@role_required('Admin')
def mark_pending(request_id):
    """Mark a payment request as pending with reason"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    reason = request.form.get('reason_pending')
    
    if not reason:
        flash('Please provide a reason for marking as Action Required.', 'warning')
        return redirect(url_for('view_request', request_id=request_id))
    
    req.status = 'Action Required'
    req.reason_pending = reason
    req.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_action(f"Marked payment request #{request_id} as Action Required")
    
    # Emit real-time update for Action Required status
    socketio.emit('request_updated', {
        'request_id': request_id,
        'status': 'Action Required',
        'reason': reason
    })
    
    flash(f'Payment request #{request_id} has been marked as Action Required.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/request/<int:request_id>/upload_proof', methods=['POST'])
@login_required
def upload_proof(request_id):
    """Department user uploads proof of payment"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if user owns this request
    if req.user_id != current_user.user_id:
        flash('You can only upload proof for your own requests.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if request is in "Send Proof" status
    if req.status != 'Send Proof':
        flash('This request does not require proof upload.', 'error')
        return redirect(url_for('dashboard'))
    
    # Handle file upload
    if 'proof_file' not in request.files:
        flash('No file uploaded.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    file = request.files['proof_file']
    
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"proof_{request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Update request
        req.proof_of_payment = filename
        req.status = 'Received Proof'
        req.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(f"Uploaded proof for payment request #{request_id}")
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Received Proof',
            'requestor': current_user.username
        })
        
        flash('Proof of payment uploaded successfully! Waiting for final approval.', 'success')
    else:
        flash('Invalid file type. Please upload an image (jpg, png, gif, etc.).', 'error')
    
    return redirect(url_for('view_request', request_id=request_id))


@app.route('/request/<int:request_id>/final_approve', methods=['POST'])
@login_required
@role_required('Admin')
def final_approve_request(request_id):
    """Admin final approval after receiving proof"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if request is in "Received Proof" status
    if req.status != 'Received Proof':
        flash('This request is not ready for final approval.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Final approval
    req.status = 'Approved'
    req.approval_date = datetime.utcnow().date()  # Set approval date
    req.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_action(f"Final approved payment request #{request_id}")
    
    # Emit real-time update
    socketio.emit('request_updated', {
        'request_id': request_id,
        'status': 'Approved',
        'final_approval': True
    })
    
    flash(f'Payment request #{request_id} has been finally approved.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/request/<int:request_id>/delete', methods=['POST'])
@login_required
@role_required('IT')
def delete_request(request_id):
    """Delete a payment request (IT only)"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Delete associated receipt file if exists
    if req.receipt_path:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], req.receipt_path)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.delete(req)
    db.session.commit()
    
    log_action(f"Deleted payment request #{request_id}")
    flash(f'Payment request #{request_id} has been deleted.', 'success')
    return redirect(url_for('it_dashboard'))


# ==================== REPORTS ROUTES ====================

@app.route('/reports')
@login_required
@role_required('Admin', 'Finance', 'GM', 'IT', 'Operation Manager')
def reports():
    """View reports page"""
    # Get filter parameters
    department_filter = request.args.get('department', '')
    status_filter = request.args.get('status', '')
    request_type_filter = request.args.get('request_type', '')
    company_filter = request.args.get('company', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Build query
    query = PaymentRequest.query
    
    # Role-based department filtering
    if current_user.role == 'Operation Manager':
        # Operation Manager can only see Maintenance, Operation, and Project Department
        query = query.filter(PaymentRequest.department.in_(['Maintenance', 'Operation', 'Project Department']))
    
    if department_filter:
        query = query.filter_by(department=department_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if request_type_filter:
        query = query.filter_by(request_type=request_type_filter)
    if company_filter:
        # Only filter by company name for approved requests with company_name
        query = query.filter(PaymentRequest.company_name.ilike(f'%{company_filter}%'))
    
    # Date filtering and sorting based on status
    if status_filter == 'Approved':
        # For approved requests, filter and sort by approval_date
        if date_from:
            query = query.filter(PaymentRequest.approval_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(PaymentRequest.approval_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        requests = query.order_by(PaymentRequest.approval_date.desc()).all()
    else:
        # For all other statuses (Pending, Send Proof, Received Proof, or All), use submission date
        if date_from:
            query = query.filter(PaymentRequest.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(PaymentRequest.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        requests = query.order_by(PaymentRequest.date.desc()).all()
    
    # Get unique departments for filter
    if current_user.role == 'Operation Manager':
        # Operation Manager can only see specific departments
        departments = ['Maintenance', 'Operation', 'Project Department']
    else:
        # Other roles can see all departments
        departments = db.session.query(PaymentRequest.department).distinct().all()
        departments = [d[0] for d in departments]
    
    # Get unique companies for filter (only for approved requests with company_name)
    companies = db.session.query(PaymentRequest.company_name).filter(
        PaymentRequest.status == 'Approved',
        PaymentRequest.company_name.isnot(None),
        PaymentRequest.company_name != ''
    ).distinct().all()
    companies = [c[0] for c in companies if c[0]]
    
    return render_template('reports.html', 
                         requests=requests, 
                         departments=departments,
                         companies=companies,
                         company_filter=company_filter,
                         user=current_user)



@app.route('/reports/export/pdf')
@login_required
@role_required('Admin', 'Finance', 'GM', 'IT', 'Operation Manager')
def export_reports_pdf():
    """Export filtered reports to a PDF including total amount and full list"""
    # Lazy imports to avoid hard dependency during app startup
    import io
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
    except ImportError:
        flash('PDF export requires reportlab. Install with: pip install reportlab', 'warning')
        return redirect(url_for('reports', **request.args))
    except Exception as e:
        flash(f'Error importing PDF library: {str(e)}', 'error')
        return redirect(url_for('reports', **request.args))

    # Reuse the same filters as the reports() view
    department_filter = request.args.get('department', '')
    status_filter = request.args.get('status', '')
    request_type_filter = request.args.get('request_type', '')
    company_filter = request.args.get('company', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = PaymentRequest.query
    
    # Role-based department filtering
    if current_user.role == 'Operation Manager':
        # Operation Manager can only see Maintenance, Operation, and Project Department
        query = query.filter(PaymentRequest.department.in_(['Maintenance', 'Operation', 'Project Department']))
    
    if department_filter:
        query = query.filter_by(department=department_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if request_type_filter:
        query = query.filter_by(request_type=request_type_filter)
    if company_filter:
        # Only filter by company name for approved requests with company_name
        query = query.filter(PaymentRequest.company_name.ilike(f'%{company_filter}%'))

    if status_filter == 'Approved':
        if date_from:
            query = query.filter(PaymentRequest.approval_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(PaymentRequest.approval_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        result_requests = query.order_by(PaymentRequest.approval_date.desc()).all()
    else:
        if date_from:
            query = query.filter(PaymentRequest.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(PaymentRequest.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        result_requests = query.order_by(PaymentRequest.date.desc()).all()

    # Compute total amount (masking not applied for exports by design)
    def to_float(value):
        try:
            return float(value)
        except Exception:
            return 0.0

    total_amount = sum(to_float(r.amount) for r in result_requests)

    try:
        # Build PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Margins
        left = 15 * mm
        right = width - 15 * mm
        top = height - 15 * mm
        y = top

        # Header
        c.setFont('Helvetica-Bold', 14)
        c.drawString(left, y, 'Payment Reports')
        c.setFont('Helvetica', 10)
        y -= 14
        filters_line = f"Dept: {department_filter or 'All'} | Status: {status_filter or 'All'} | Type: {request_type_filter or 'All'}"
        c.drawString(left, y, filters_line)
        y -= 12
        if date_from or date_to:
            c.drawString(left, y, f"Date: {date_from or '...'} to {date_to or '...'}")
            y -= 12

        # Total amount
        c.setFont('Helvetica-Bold', 11)
        c.drawString(left, y, f"Total Amount: OMR {total_amount:.3f}")
        y -= 18

        # Table header
        c.setFont('Helvetica-Bold', 9)
        headers = ['ID', 'Type', 'Requestor', 'Dept', 'Submitted', 'Approved', 'Amount', 'Status', 'Approver']
        col_x = [left, left+18*mm, left+42*mm, left+80*mm, left+105*mm, left+135*mm, left+165*mm, left+195*mm, left+225*mm]
        for hx, text in zip(col_x, headers):
            c.drawString(hx, y, text)
        y -= 10
        c.line(left, y, right, y)
        y -= 8

        # Rows
        c.setFont('Helvetica', 9)
        row_height = 10
        for r in result_requests:
            if y < 20 * mm:
                c.showPage()
                y = top
                c.setFont('Helvetica-Bold', 9)
                for hx, text in zip(col_x, headers):
                    c.drawString(hx, y, text)
                y -= 10
                c.line(left, y, right, y)
                y -= 8
                c.setFont('Helvetica', 9)

            c.drawString(col_x[0], y, f"#{r.request_id}")
            c.drawString(col_x[1], y, str(r.request_type or ''))
            c.drawString(col_x[2], y, (r.requestor_name or '')[:20])
            c.drawString(col_x[3], y, (r.department or '')[:12])
            c.drawString(col_x[4], y, r.date.strftime('%Y-%m-%d') if getattr(r, 'date', None) else '')
            c.drawString(col_x[5], y, r.approval_date.strftime('%Y-%m-%d') if getattr(r, 'approval_date', None) else '')
            c.drawRightString(col_x[6]+18*mm, y, f"OMR {to_float(r.amount):.3f}")
            c.drawString(col_x[7], y, str(r.status or '')[:18])
            c.drawString(col_x[8], y, (r.approver or '')[:12])
            y -= row_height

        c.showPage()
        c.save()
        pdf_value = buffer.getvalue()
        buffer.close()

        from flask import make_response
        response = make_response(pdf_value)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=reports.pdf'
        response.headers['Content-Length'] = str(len(pdf_value))
        return response
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('reports', **request.args))


# ==================== USER MANAGEMENT ROUTES (IT ONLY) ====================

@app.route('/users')
@login_required
@role_required('IT')
def manage_users():
    """Manage users (IT only)"""
    users = User.query.all()
    return render_template('manage_users.html', users=users, user=current_user)


@app.route('/users/new', methods=['GET', 'POST'])
@login_required
@role_required('IT')
def new_user():
    """Create a new user - IT ONLY"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        department = request.form.get('department')
        role = request.form.get('role')
        email = request.form.get('email')
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('new_user'))
        
        # Department restriction removed - multiple accounts per department allowed
        
        new_user = User(
            username=username,
            department=department,
            role=role,
            email=email
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        log_action(f"Created new user: {username} ({role}) for department: {department}")
        flash(f'User {username} created successfully for {department} department!', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('new_user.html', user=current_user)


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('IT')
def edit_user(user_id):
    """Edit user information - IT ONLY"""
    user_to_edit = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        new_department = request.form.get('department')
        new_role = request.form.get('role')
        new_email = request.form.get('email')
        
        # Department restriction removed - multiple accounts per department allowed
        
        # Update user information
        user_to_edit.department = new_department
        user_to_edit.role = new_role
        user_to_edit.email = new_email
        
        # Only update password if provided
        if new_password:
            user_to_edit.set_password(new_password)
        
        db.session.commit()
        
        log_action(f"Updated user: {user_to_edit.username} ({new_role}) - Department: {new_department}")
        flash(f'User {user_to_edit.username} has been updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('edit_user.html', user=current_user, user_to_edit=user_to_edit)


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('IT')
def delete_user(user_id):
    """Delete a user and handle related data"""
    user_to_delete = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user_to_delete.user_id == current_user.user_id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('manage_users'))
    
    username = user_to_delete.username
    
    # Handle payment requests created by this user
    payment_requests = PaymentRequest.query.filter_by(user_id=user_id).all()
    if payment_requests:
        # Delete all payment requests by this user
        for req in payment_requests:
            # Delete associated files if they exist
            if req.receipt_path:
                receipt_file = os.path.join(app.config['UPLOAD_FOLDER'], req.receipt_path)
                if os.path.exists(receipt_file):
                    os.remove(receipt_file)
            if req.proof_of_payment:
                proof_file = os.path.join(app.config['UPLOAD_FOLDER'], req.proof_of_payment)
                if os.path.exists(proof_file):
                    os.remove(proof_file)
            db.session.delete(req)
    
    # Update audit logs to preserve history (user_id will be NULL, but username_snapshot kept)
    # No need to explicitly update - the nullable foreign key will handle this
    
    # Delete the user
    db.session.delete(user_to_delete)
    db.session.commit()
    
    log_action(f"Deleted user: {username} (and {len(payment_requests)} associated requests)")
    flash(f'User {username} has been deleted successfully.', 'success')
    return redirect(url_for('manage_users'))


# ==================== NOTIFICATION ROUTES ====================

@app.route('/notifications')
@login_required
@role_required('Admin', 'Finance', 'Project', 'Operation Manager')
def notifications():
    """View all notifications for Finance, Admin, and Project users"""
    if current_user.role == 'Project':
        # For project users, only show due date notifications
        notifications = Notification.query.filter_by(
            user_id=current_user.user_id,
            notification_type='recurring_due'
        ).order_by(Notification.created_at.desc()).all()
    else:
        # For Admin, Finance, and Operation Manager, show all notifications
        notifications = Notification.query.filter_by(user_id=current_user.user_id).order_by(Notification.created_at.desc()).all()
    
    return render_template('notifications.html', notifications=notifications, user=current_user)


@app.route('/notifications/mark_read/<int:notification_id>')
@login_required
@role_required('Admin', 'Finance', 'Project', 'Operation Manager')
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(notification_id=notification_id, user_id=current_user.user_id).first()
    if notification:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


@app.route('/notifications/mark_all_read')
@login_required
@role_required('Admin', 'Finance', 'Project', 'Operation Manager')
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    Notification.query.filter_by(user_id=current_user.user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@app.route('/notifications/mark_paid/<int:notification_id>')
@login_required
@role_required('Admin', 'Finance', 'Project', 'Operation Manager')
def mark_notification_paid(notification_id):
    """Mark a recurring payment notification as paid and delete it"""
    notification = Notification.query.filter_by(
        notification_id=notification_id, 
        user_id=current_user.user_id
    ).first()
    
    if not notification:
        return jsonify({'success': False, 'message': 'Notification not found'}), 404
    
    # Only allow marking recurring due notifications as paid
    if notification.notification_type != 'recurring_due':
        return jsonify({'success': False, 'message': 'This notification cannot be marked as paid'}), 400
    
    # Record that this payment was marked as paid today
    paid_notification = PaidNotification(
        request_id=notification.request_id,
        user_id=current_user.user_id,
        paid_date=date.today()
    )
    db.session.add(paid_notification)
    
    # Delete the notification
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Payment marked as paid. Notification will reappear on the next due date.'})


@app.route('/notifications/delete/<int:notification_id>')
@login_required
@role_required('Admin', 'Finance', 'Project', 'Operation Manager')
def delete_notification(notification_id):
    """Delete a specific notification"""
    notification = Notification.query.filter_by(notification_id=notification_id, user_id=current_user.user_id).first()
    if notification:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Notification not found'}), 404


@app.route('/api/notifications/unread_count')
@login_required
@role_required('Admin', 'Finance', 'Project', 'Operation Manager')
def unread_notifications_count():
    """Get count of unread notifications"""
    if current_user.role == 'Project':
        # For project users, only count due date notifications
        count = Notification.query.filter_by(
            user_id=current_user.user_id, 
            is_read=False,
            notification_type='recurring_due'
        ).count()
    else:
        # For Admin, Finance, and Operation Manager, count all notifications
        count = Notification.query.filter_by(user_id=current_user.user_id, is_read=False).count()
    return jsonify({'count': count})


@app.route('/api/notifications/recent')
@login_required
@role_required('Admin', 'Finance', 'Project', 'Operation Manager')
def recent_notifications():
    """Get recent notifications for the user"""
    if current_user.role == 'Project':
        # For project users, only show due date notifications
        notifications = Notification.query.filter_by(
            user_id=current_user.user_id,
            notification_type='recurring_due'
        ).order_by(Notification.created_at.desc()).limit(5).all()
    else:
        # For Admin, Finance, and Operation Manager, show all notifications
        notifications = Notification.query.filter_by(user_id=current_user.user_id).order_by(Notification.created_at.desc()).limit(5).all()
    return jsonify([n.to_dict() for n in notifications])






# ==================== FILE UPLOAD ROUTES ====================

@app.route('/uploads/receipts/<filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded receipt files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500



# ==================== MAIN ====================



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5005)

