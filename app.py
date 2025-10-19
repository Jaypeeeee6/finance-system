from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime, date, timedelta
import re
from models import db, User, PaymentRequest, AuditLog, Notification, PaidNotification, RecurringPaymentSchedule, LateInstallment
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Make timedelta available in templates
from datetime import timedelta
app.jinja_env.globals.update(timedelta=timedelta)

def format_recurring_schedule(interval, payment_schedule=None):
    """Format recurring interval into human-readable text"""
    try:
        parts = interval.split(':')
        frequency = parts[0]
        interval_value = int(parts[1])
        
        # Handle the new single date format
        if frequency == 'monthly' and len(parts) > 2 and parts[2] == 'date':
            # Extract the date (format: YYYY-MM-DD)
            date_str = parts[3]
            
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%B %d, %Y')
            except ValueError:
                formatted_date = date_str
            
            # Create the base schedule text
            if interval_value == 1:
                schedule_text = f"Every month starting on {formatted_date}"
            else:
                schedule_text = f"Every {interval_value} months starting on {formatted_date}"
            
            # Check for end date
            end_date_index = parts.index('end') if 'end' in parts else -1
            if end_date_index != -1 and end_date_index + 1 < len(parts):
                end_date = parts[end_date_index + 1]
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                    formatted_end_date = end_date_obj.strftime('%B %d, %Y')
                    schedule_text += f" until {formatted_end_date}"
                except ValueError:
                    schedule_text += f" until {end_date}"
            
            # Add payment schedule information if available
            if payment_schedule:
                try:
                    import json
                    schedule_data = json.loads(payment_schedule)
                    if schedule_data:
                        payment_details = []
                        for payment in schedule_data:
                            date = payment.get('date', '')
                            amount = payment.get('amount', 0)
                            if date and amount > 0:
                                payment_details.append(f"{date}: {amount:.3f} OMR")
                        
                        if payment_details:
                            schedule_text += f"\n\nPayment Schedule:\n" + "\n".join(payment_details)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            return schedule_text
        
        # Handle the old format with specific days (for backward compatibility)
        elif frequency == 'monthly' and len(parts) > 2 and parts[2] == 'days':
            # Extract specific days and dates
            days = parts[3].split(',')
            year = parts[4] if len(parts) > 4 else None
            month = parts[5] if len(parts) > 5 else None
            
            # Format the starting dates using the exact same logic as the preview
            if year and month:
                month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                             'July', 'August', 'September', 'October', 'November', 'December']
                # The stored month is 1-based (1-12), so convert to 0-based for array indexing
                month_int = int(month) - 1  # Convert 1-based to 0-based
                month_name = month_names[month_int] if 0 <= month_int <= 11 else str(month)
                starting_dates = [f"{month_name} {day}, {year}" for day in days]
                starting_text = ", ".join(starting_dates)
            else:
                starting_text = f"days {', '.join(days)}"
            
            # Create the base schedule text using the exact same format as the preview
            if interval_value == 1:
                schedule_text = f"Every month starting on {starting_text}"
            else:
                schedule_text = f"Every {interval_value} months starting on {starting_text}"
            
            # Check for end date
            end_date_index = parts.index('end') if 'end' in parts else -1
            if end_date_index != -1 and end_date_index + 1 < len(parts):
                end_date = parts[end_date_index + 1]
                try:
                    from datetime import datetime
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                    formatted_end_date = end_date_obj.strftime('%B %d, %Y')
                    schedule_text += f" until {formatted_end_date}"
                except ValueError:
                    schedule_text += f" until {end_date}"
            
            # Add payment schedule information if available
            if payment_schedule:
                try:
                    import json
                    schedule_data = json.loads(payment_schedule)
                    if schedule_data:
                        payment_details = []
                        for payment in schedule_data:
                            date = payment.get('date', '')
                            amount = payment.get('amount', 0)
                            if date and amount > 0:
                                payment_details.append(f"{date}: {amount:.3f} OMR")
                        
                        if payment_details:
                            schedule_text += f"\n\nPayment Schedule:\n" + "\n".join(payment_details)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            return schedule_text
        
        # Handle legacy formats
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
        if room == 'finance_admin' and current_user.role in ['Finance', 'Finance Admin']:
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
                        # Create notifications for all admin and project users
                        admin_users = User.query.filter(User.role.in_(['Finance Admin', 'Project'])).all()
                        for user in admin_users:
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
                    admin_users = User.query.filter(User.role.in_(['Finance Admin', 'Project'])).all()
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


def get_notifications_for_user(user):
    """Get appropriate notifications for a user based on their role"""
    if user.role == 'Project':
        # Project users only see recurring due notifications
        return Notification.query.filter_by(
            user_id=user.user_id,
            notification_type='recurring_due'
        ).order_by(Notification.created_at.desc()).limit(5).all()
    else:
        # All other roles see all their notifications
        return Notification.query.filter_by(user_id=user.user_id).order_by(Notification.created_at.desc()).limit(5).all()

def get_unread_count_for_user(user):
    """Get unread notification count for a user based on their role"""
    if user.role == 'Project':
        # Project users only count recurring due notifications
        return Notification.query.filter_by(
            user_id=user.user_id, 
            is_read=False,
            notification_type='recurring_due'
        ).count()
    else:
        # All other roles count all notifications
        return Notification.query.filter_by(user_id=user.user_id, is_read=False).count()

def notify_finance_and_admin(title, message, notification_type, request_id=None):
    """Notify Finance and Admin users about new submissions"""
    # Get all Finance and Admin users
    finance_admin_users = User.query.filter(User.role.in_(['Finance', 'Finance Admin'])).all()
    
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
    # Ensure a default IT user exists if database is empty
    try:
        if User.query.count() == 0:
            default_it = User(
                name='Default IT',
                username='it@system.local',
                department='IT',
                role='IT',
                email='it@system.local'
            )
            default_it.set_password('admin123')
            db.session.add(default_it)
            db.session.commit()
            app.logger.info('Default IT user created: it@system.local / admin123')
    except Exception as _e:
        # If DB not ready or other issue, continue to login page without blocking
        pass
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            log_action(f"User {username} logged in")
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email address or password', 'danger')
    
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
    
    if role == 'Finance Admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'Finance':
        return redirect(url_for('finance_dashboard'))
    elif role == 'GM':
        return redirect(url_for('gm_dashboard'))
    elif role == 'IT':
        return redirect(url_for('it_dashboard'))
    elif role == 'Department Manager':
        # Route IT department managers to the IT dashboard, others to department dashboard
        if current_user.department == 'IT':
            return redirect(url_for('it_dashboard'))
        return redirect(url_for('department_dashboard'))
    elif role == 'Project':
        return redirect(url_for('project_dashboard'))
    elif role == 'Operation Manager':
        return redirect(url_for('operation_dashboard'))
    else:  # Department User
        return redirect(url_for('department_dashboard'))


@app.route('/department/dashboard')
@login_required
@role_required('Department User', 'Department Manager', 'Operation Manager', 'Finance', 'Project')
def department_dashboard():
    """Dashboard for department users, finance, and project users"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # For Department Managers and Operation Managers, show requests from their departments
    if current_user.role in ['Department Manager', 'Operation Manager']:
        # Get requests from their department(s) (including completed/paid ones)
        if current_user.role == 'Operation Manager':
            # Operation Manager can see ALL departments
            query = PaymentRequest.query
        else:
            # Department Manager can see ALL their department's requests
            query = PaymentRequest.query.filter(
                PaymentRequest.department == current_user.department
            )
        
        requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        # For regular users, show their own requests
        requests_pagination = PaymentRequest.query.filter_by(user_id=current_user.user_id).order_by(PaymentRequest.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    # Get notifications for department managers and regular users
    notifications = get_notifications_for_user(current_user)
    unread_count = get_unread_count_for_user(current_user)
    
    return render_template('department_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         user=current_user,
                         notifications=notifications,
                         unread_count=unread_count)


@app.route('/admin/dashboard')
@login_required
@role_required('Finance Admin')
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
    # Finance Admin can see all requests, including pending manager approval
    query = PaymentRequest.query
    if status_filter:
        query = query.filter(PaymentRequest.status == status_filter)
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    notifications = get_notifications_for_user(current_user)
    unread_count = get_unread_count_for_user(current_user)
    
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
    # Finance users can see all requests, including their own pending manager approval requests
    query = PaymentRequest.query
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    notifications = get_notifications_for_user(current_user)
    unread_count = get_unread_count_for_user(current_user)
    
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
    # GM can see ALL requests from ALL departments
    query = PaymentRequest.query
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Calculate statistics (all requests from all departments)
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
    
    # Get notifications for GM (all notifications)
    notifications = get_notifications_for_user(current_user)
    unread_count = get_unread_count_for_user(current_user)
    
    return render_template('gm_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         stats=stats, 
                         user=current_user,
                         notifications=notifications,
                         unread_count=unread_count,
                         department_filter=department_filter)


@app.route('/it/dashboard')
@login_required
@role_required('IT', 'Department Manager')
def it_dashboard():
    """Dashboard for IT - full CRUD access"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    department_filter = request.args.get('department', None)
    
    # Validate per_page to prevent abuse
    if per_page not in [10, 20, 50, 100]:
        per_page = 10
    
    # Restrict Department Managers to IT department only
    if current_user.role == 'Department Manager' and current_user.department != 'IT':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Build query with optional department filter
    if current_user.role == 'IT':
        # IT users see all requests
        query = PaymentRequest.query
    elif current_user.role == 'Department Manager' and current_user.department == 'IT':
        # IT Department Managers see all IT department requests (including pending manager approval)
        query = PaymentRequest.query.filter(PaymentRequest.department == 'IT')
    else:
        # Other users should not see requests that are still pending manager approval
        query = PaymentRequest.query.filter(PaymentRequest.status != 'Pending Manager Approval')
    
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.order_by(PaymentRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get notifications for IT users and IT Department Managers
    notifications = get_notifications_for_user(current_user)
    unread_count = get_unread_count_for_user(current_user)
    
    users = User.query.all()
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
    return render_template('it_dashboard.html', 
                         requests=requests_pagination.items, 
                         pagination=requests_pagination,
                         users=users, 
                         logs=logs, 
                         user=current_user,
                         notifications=notifications,
                         unread_count=unread_count,
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
    notifications = get_notifications_for_user(current_user)
    unread_count = get_unread_count_for_user(current_user)
    
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
    
    # Build query with optional status and department filters - Operation Manager sees ALL departments
    query = PaymentRequest.query
    
    # If no specific status filter, prioritize showing requests that need manager approval
    if not status_filter:
        # Show requests that need manager approval first, then others
        query = query.order_by(
            db.case(
                (PaymentRequest.status == 'Pending Manager Approval', 1),
                else_=2
            ),
            PaymentRequest.created_at.desc()
        )
    else:
        query = query.filter(PaymentRequest.status == status_filter)
    
    if department_filter:
        query = query.filter(PaymentRequest.department == department_filter)
    
    # Get paginated requests
    requests_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get notifications for operation manager (all notifications, same as admin)
    notifications = get_notifications_for_user(current_user)
    unread_count = get_unread_count_for_user(current_user)
    
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
        bank_name = request.form.get('bank_name')
        amount = request.form.get('amount')
        recurring = request.form.get('recurring', 'One-Time')
        recurring_interval = request.form.get('recurring_interval')
        
        # Validate account number length (maximum 16 digits)
        if account_number and len(account_number) > 16:
            flash('Account number cannot exceed 16 digits.', 'error')
            return render_template('new_request.html', user=current_user, today=datetime.utcnow().date().strftime('%Y-%m-%d'))
        
        # Validate account number contains only digits
        if account_number and not account_number.isdigit():
            flash('Account number must contain only numbers.', 'error')
            return render_template('new_request.html', user=current_user, today=datetime.utcnow().date().strftime('%Y-%m-%d'))
        
        # Validate bank name is selected
        if not bank_name:
            flash('Please select a bank name.', 'error')
            return render_template('new_request.html', user=current_user, today=datetime.utcnow().date().strftime('%Y-%m-%d'))
        
        # Handle comma-formatted amount
        if amount:
            # Remove commas from amount for processing
            amount_clean = amount.replace(',', '')
            try:
                amount_float = float(amount_clean)
                if amount_float <= 0:
                    flash('Amount must be greater than 0.', 'error')
                    return render_template('new_request.html', user=current_user, today=datetime.utcnow().date().strftime('%Y-%m-%d'))
            except ValueError:
                flash('Invalid amount format.', 'error')
                return render_template('new_request.html', user=current_user, today=datetime.utcnow().date().strftime('%Y-%m-%d'))
        
        # Handle file upload for receipt
        receipt_path = None
        if 'receipt_file' in request.files:
            receipt_file = request.files['receipt_file']
            if receipt_file and receipt_file.filename:
                # Validate file size (10MB max)
                if len(receipt_file.read()) > 10 * 1024 * 1024:  # 10MB
                    flash('Receipt file is too large. Maximum size is 10MB.', 'error')
                    return render_template('new_request.html', user=current_user, today=datetime.utcnow().date().strftime('%Y-%m-%d'))
                
                # Reset file pointer
                receipt_file.seek(0)
                
                # Validate file extension
                allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
                file_extension = receipt_file.filename.rsplit('.', 1)[1].lower() if '.' in receipt_file.filename else ''
                if file_extension not in allowed_extensions:
                    flash('Invalid file type. Allowed types: PDF, JPG, PNG, DOC, DOCX', 'error')
                    return render_template('new_request.html', user=current_user, today=datetime.utcnow().date().strftime('%Y-%m-%d'))
                
                # Generate unique filename
                import uuid
                filename = f"{uuid.uuid4()}_{receipt_file.filename}"
                
                # Create uploads directory if it doesn't exist
                import os
                upload_folder = os.path.join(app.root_path, 'uploads', 'receipts')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save file
                full_path = os.path.join(upload_folder, filename)
                receipt_file.save(full_path)
                receipt_path = filename  # Store only the filename, not the full path
        
        # Get dynamic fields based on request type
        item_name = request.form.get('item_name')
        person_company = request.form.get('person_company')
        company_name = request.form.get('company_name')
        
        # All departments go to their manager first for approval
        initial_status = 'Pending Manager Approval'
        
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
            bank_name=bank_name,
            amount=amount_clean if amount else amount,  # Use cleaned amount without commas
            recurring=recurring,
            recurring_interval=recurring_interval if recurring == 'Recurring' else None,
            status=initial_status,
            receipt_path=receipt_path,  # Add receipt path if file was uploaded
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
                    create_recurring_payment_schedule(new_req.request_id, amount_clean if amount else amount, payment_schedule_data)
                    log_action(f"Created variable amount payment schedule for request #{new_req.request_id}")
            except Exception as e:
                print(f"Error creating payment schedule: {e}")
                flash('Payment request created but schedule configuration failed. Please contact admin.', 'warning')
        
        log_action(f"Created payment request #{new_req.request_id} - {request_type}")
        
        # Create notifications based on request status
        try:
            if new_req.status == 'Approved':
                # Finance department requests are auto-approved - notify Finance Admin
                notify_finance_and_admin(
                    title="New Payment Request Submitted",
                    message=f"New {request_type} request submitted by {requestor_name} from {current_user.department} department for OMR {amount}",
                    notification_type="new_submission",
                    request_id=new_req.request_id
                )
            else:
                # Other departments - notify only the department manager, not Finance Admin
                if new_req.user and new_req.user.manager_id:
                    create_notification(
                        user_id=new_req.user.manager_id,
                        title="New Payment Request for Approval",
                        message=f"New {request_type} request submitted by {requestor_name} from {current_user.department} department for OMR {amount} - requires your approval",
                        notification_type="manager_approval_required",
                        request_id=new_req.request_id
                    )
        except Exception as e:
            print(f"Error creating notifications: {e}")
            # Don't fail the request creation if notification fails
        
        # Emit real-time event based on request status
        try:
            if new_req.status == 'Approved':
                # Finance department requests - notify Finance Admin
                socketio.emit('new_request', {
                    'request_id': new_req.request_id,
                    'request_type': new_req.request_type,
                    'requestor_name': new_req.requestor_name,
                    'department': new_req.department,
                    'amount': float(new_req.amount),
                    'status': new_req.status,
                    'date': new_req.date.strftime('%Y-%m-%d')
                }, room='finance_admin')
            else:
                # Other departments - notify only the manager
                if new_req.user and new_req.user.manager_id:
                    socketio.emit('new_request', {
                        'request_id': new_req.request_id,
                        'request_type': new_req.request_type,
                        'requestor_name': new_req.requestor_name,
                        'department': new_req.department,
                        'amount': float(new_req.amount),
                        'status': new_req.status,
                        'date': new_req.date.strftime('%Y-%m-%d')
                    }, room=f'user_{new_req.user.manager_id}')
        except Exception as e:
            print(f"Error emitting real-time notification: {e}")
            # Don't fail the request creation if real-time notification fails
        
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
    # Use eager loading to reduce database queries
    req = PaymentRequest.query.options(
        db.joinedload(PaymentRequest.user)
    ).get_or_404(request_id)
    
    # Check permissions
    if current_user.role not in ['Finance Admin', 'Finance', 'GM', 'IT', 'Project']:
        # Department Managers can view requests from their department
        if current_user.role == 'Department Manager':
            if req.department != current_user.department:
                flash('You do not have permission to view this request.', 'danger')
                return redirect(url_for('dashboard'))
        # Operation Managers can view requests from Operation, Maintenance, and Project Department
        elif current_user.role == 'Operation Manager':
            if req.department not in ['Operation', 'Maintenance', 'Project Department']:
                flash('You do not have permission to view this request.', 'danger')
                return redirect(url_for('dashboard'))
        # Regular users can only view their own requests
        elif req.user_id != current_user.user_id:
            flash('You do not have permission to view this request.', 'danger')
            return redirect(url_for('dashboard'))
    
    # Mark notifications related to this request as read for Finance and Admin users
    if current_user.role in ['Finance', 'Finance Admin']:
        # Use a more efficient update query
        db.session.query(Notification).filter_by(
            user_id=current_user.user_id,
            request_id=request_id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
    
    # Get schedule rows for variable payments - show for Admin review, but only allow payments when approved
    schedule_rows = []
    total_paid_amount = 0
    
    # Only process schedule if it's a recurring monthly payment
    if req.recurring_interval and 'monthly' in req.recurring_interval:
        # Get variable payment schedule if exists - use single query with ordering
        schedule = RecurringPaymentSchedule.query.filter_by(
            request_id=request_id
        ).order_by(RecurringPaymentSchedule.payment_order).all()
        
        if schedule:
            # Optimize: Get all paid notifications and late installments in single queries
            # Use list comprehension for better performance
            paid_notifications = PaidNotification.query.filter_by(request_id=request_id).all()
            late_installments = LateInstallment.query.filter_by(request_id=request_id).all()
            
            # Create sets for O(1) lookup instead of O(n) list search
            paid_dates = {paid.paid_date for paid in paid_notifications}
            late_dates = {late.payment_date for late in late_installments}
            
            # Calculate total paid and remaining amounts
            total_paid_amount = 0
            
            # Use list comprehension for better performance
            for entry in schedule:
                # Check if this installment is already paid (optimized lookup)
                is_paid = entry.payment_date in paid_dates
                # Check if this installment is marked late (optimized lookup)
                is_late = entry.payment_date in late_dates
                
                # If this installment is paid, add its amount to total paid
                if is_paid:
                    total_paid_amount += entry.amount
                
                schedule_rows.append({
                    'date': entry.payment_date,
                    'amount': entry.amount,
                    'is_paid': is_paid,
                    'is_late': is_late
                })
    
    # Determine the manager's name for display
    manager_name = None
    # Determine manager name for all statuses (pending and completed)
    if req.user.manager_id:
        # Get the manager's name from the manager_id
        manager = User.query.get(req.user.manager_id)
        if manager:
            manager_name = manager.name
        else:
            # If manager_id exists but user not found, try to find Department Manager
            dept_manager = User.query.filter_by(role='Department Manager', department=req.department).first()
            if dept_manager:
                manager_name = dept_manager.name
    else:
        # If no manager_id is set, find the Department Manager for the requestor's department
        dept_manager = User.query.filter_by(role='Department Manager', department=req.department).first()
        if dept_manager:
            manager_name = dept_manager.name
        elif req.department == 'Operation':
            # For Operation department, try Operation Manager as fallback
            operation_manager = User.query.filter_by(role='Operation Manager').first()
            if operation_manager:
                manager_name = operation_manager.name
        
    
    # Get all proof files for this request
    proof_files = []
    if req.status in ['Proof Sent', 'Proof Rejected', 'Payment Pending', 'Paid', 'Completed']:
        import os
        import glob
        upload_folder = app.config['UPLOAD_FOLDER']
        # Look for all proof files for this request (files starting with proof_{request_id}_)
        proof_pattern = os.path.join(upload_folder, f"proof_{request_id}_*")
        proof_files = [os.path.basename(f) for f in glob.glob(proof_pattern)]
        # Sort by filename (which includes timestamp) to show newest first
        proof_files.sort(reverse=True)
    
    return render_template('view_request.html', request=req, user=current_user, schedule_rows=schedule_rows, total_paid_amount=float(total_paid_amount), manager_name=manager_name, proof_files=proof_files)


@app.route('/request/<int:request_id>/approve', methods=['POST'])
@login_required
@role_required('Finance Admin')
def approve_request(request_id):
    """Approve a payment request (Finance approval)"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if request is in correct status for Finance approval
    if req.status not in ['Pending', 'Pending Finance Approval', 'Payment Pending', 'Proof Sent']:
        flash('This request is not ready for Finance approval.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    # Get form data
    approval_status = request.form.get('approval_status')
    
    if approval_status == 'approve':
        approver = request.form.get('approver')
        proof_required = request.form.get('proof_required') == 'on'
        today = datetime.utcnow().date()
        
        # Require receipt upload for Finance Admin approval
        receipt_file = request.files.get('receipt')
        if not receipt_file or not allowed_file(receipt_file.filename):
            flash('Receipt upload is required for Finance Admin approval.', 'error')
            return redirect(url_for('view_request', request_id=request_id))
        
        # Handle receipt upload
        filename = secure_filename(receipt_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        receipt_file.save(filepath)
        req.receipt_path = filename
        
        req.approver = approver
        req.proof_required = proof_required
        req.updated_at = datetime.utcnow()
        
        if proof_required:
            # Proof is required - set status to Proof Pending
            req.status = 'Proof Pending'
            flash(f'Payment request #{request_id} approved. Waiting for proof of payment from department.', 'info')
            log_action(f"Approved payment request #{request_id} - Proof required")
            
            # Notify the requestor
            create_notification(
                user_id=req.user_id,
                title="Proof of Payment Required",
                message=f"Your payment request #{request_id} has been approved. Please upload proof of payment.",
                notification_type="proof_required",
                request_id=request_id
            )
            
            # Emit real-time update
            socketio.emit('request_updated', {
                'request_id': request_id,
                'status': 'Proof Pending',
                'approver': approver
            })
        else:
            # No proof required - set status to Completed
            req.status = 'Completed'
            req.approval_date = today
            req.completion_date = today
            flash(f'Payment request #{request_id} approved and completed. No proof of payment required.', 'success')
            log_action(f"Approved and completed payment request #{request_id} - No proof required")
            
            # Notify the requestor
            create_notification(
                user_id=req.user_id,
                title="Request Completed",
                message=f"Your payment request #{request_id} has been approved and completed. No proof of payment was required.",
                notification_type="request_completed",
                request_id=request_id
            )
            
            # Emit real-time update
            socketio.emit('request_updated', {
                'request_id': request_id,
                'status': 'Completed',
                'approver': approver,
                'completed': True
            })
    
    
    elif approval_status == 'paid':
        # Mark as paid - requires receipt upload
        receipt_file = request.files.get('receipt')
        if not receipt_file or not allowed_file(receipt_file.filename):
            flash('Receipt upload is required to mark as paid.', 'error')
            return redirect(url_for('view_request', request_id=request_id))
        
        # Handle receipt upload
        filename = secure_filename(receipt_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        receipt_file.save(filepath)
        req.receipt_path = filename
        
        req.status = 'Paid'
        req.approval_date = datetime.utcnow().date()
        req.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(f"Finance admin marked payment request #{request_id} as paid")
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Paid',
            'paid': True
        })
        
        flash(f'Payment request #{request_id} has been marked as paid.', 'success')
    
    elif approval_status == 'proof_sent_approve':
        # Approve proof sent by requestor
        req.status = 'Payment Pending'
        req.approval_date = datetime.utcnow().date()
        req.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(f"Finance admin approved proof for payment request #{request_id}")
        
        # Notify the requestor
        create_notification(
            user_id=req.user_id,
            title="Proof Approved",
            message=f"Your proof for payment request #{request_id} has been approved. Status updated to Payment Pending.",
            notification_type="proof_approved",
            request_id=request_id
        )
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Payment Pending',
            'proof_approved': True
        })
        
        flash(f'Proof for payment request #{request_id} has been approved.', 'success')
    
    elif approval_status == 'proof_sent_reject':
        # Reject proof sent by requestor
        rejection_reason = request.form.get('rejection_reason', '').strip()
        if not rejection_reason:
            flash('Please provide a reason for rejection.', 'error')
            return redirect(url_for('view_request', request_id=request_id))
        
        req.status = 'Proof Rejected'  # Set to Proof Rejected status
        req.rejection_reason = rejection_reason
        req.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(f"Finance admin rejected proof for payment request #{request_id} - Reason: {rejection_reason}")
        
        # Notify the requestor
        create_notification(
            user_id=req.user_id,
            title="Proof Rejected",
            message=f"Your proof for payment request #{request_id} has been rejected. Please review the feedback and resubmit.",
            notification_type="proof_rejected",
            request_id=request_id
        )
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Proof Pending',
            'proof_rejected': True
        })
        
        flash(f'Proof for payment request #{request_id} has been rejected.', 'success')
    
    elif approval_status == 'reject':
        # Finance admin rejects - request is rejected
        rejection_reason = request.form.get('rejection_reason', '').strip()
        if not rejection_reason:
            flash('Please provide a reason for rejection.', 'error')
            return redirect(url_for('view_request', request_id=request_id))
        
        req.status = 'Rejected by Finance'
        req.rejection_reason = rejection_reason
        req.finance_rejection_date = datetime.utcnow().date()
        req.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(f"Finance admin rejected payment request #{request_id} - Reason: {rejection_reason}")
        
        # Notify the requestor
        create_notification(
            user_id=req.user_id,
            title="Payment Request Rejected",
            message=f"Your payment request #{request_id} has been rejected by Finance. Please review the feedback.",
            notification_type="request_rejected",
            request_id=request_id
        )
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Rejected by Finance',
            'finance_rejected': True
        })
        
        flash(f'Payment request #{request_id} has been rejected by Finance.', 'success')
    
    
    else:
        flash('Invalid approval status selected.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    db.session.commit()
    return redirect(url_for('view_request', request_id=request_id))


@app.route('/request/<int:request_id>/upload_additional_files', methods=['POST'])
@login_required
@role_required('Finance Admin')
def upload_additional_files(request_id):
    """Upload additional files to an approved request"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if request is in correct status for additional file upload
    if req.status not in ['Payment Pending', 'Proof Pending', 'Proof Sent', 'Paid']:
        flash('This request is not in a state that allows file uploads.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    # Handle file uploads
    files = request.files.getlist('additional_files')
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to filename to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"additional_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_files.append(filename)
    
    if uploaded_files:
        # Store additional files (you might want to add a new field for this)
        # For now, we'll just log the action
        log_action(f"Finance admin uploaded {len(uploaded_files)} additional files to request #{request_id}")
        flash(f'Successfully uploaded {len(uploaded_files)} additional files.', 'success')
    else:
        flash('No valid files were uploaded.', 'warning')
    
    return redirect(url_for('view_request', request_id=request_id))


@app.route('/request/<int:request_id>/mark_as_paid', methods=['POST'])
@login_required
@role_required('Finance Admin')
def mark_as_paid(request_id):
    """Mark a payment pending request as paid"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if request is in correct status
    if req.status != 'Payment Pending':
        flash('This request is not in Payment Pending status.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    # Mark as paid
    req.status = 'Approved'
    req.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_action(f"Finance admin marked payment request #{request_id} as paid")
    
    # Notify the requestor
    create_notification(
        user_id=req.user_id,
        title="Payment Completed",
        message=f"Your payment request #{request_id} has been paid.",
        notification_type="payment_completed",
        request_id=request_id
    )
    
    # Emit real-time update
    socketio.emit('request_updated', {
        'request_id': request_id,
        'status': 'Approved',
        'paid': True
    })
    
    flash(f'Payment request #{request_id} has been marked as paid.', 'success')
    return redirect(url_for('view_request', request_id=request_id))


@app.route('/request/<int:request_id>/close', methods=['POST'])
@login_required
@role_required('Finance Admin')
def close_request(request_id):
    """Close a request (mark as completed)"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if request is in correct status
    if req.status not in ['Payment Pending', 'Proof Pending', 'Proof Sent', 'Paid']:
        flash('This request cannot be closed in its current status.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    # Close the request
    req.status = 'Completed'
    req.completion_date = datetime.utcnow().date()
    req.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_action(f"Finance admin closed payment request #{request_id}")
    
    # Notify the requestor
    create_notification(
        user_id=req.user_id,
        title="Request Completed",
        message=f"Your payment request #{request_id} has been completed and closed.",
        notification_type="request_completed",
        request_id=request_id
    )
    
    # Emit real-time update
    socketio.emit('request_updated', {
        'request_id': request_id,
        'status': 'Completed',
        'completed': True
    })
    
    flash(f'Payment request #{request_id} has been closed.', 'success')
    return redirect(url_for('view_request', request_id=request_id))


@app.route('/request/<int:request_id>/pending', methods=['POST'])
@login_required
@role_required('Admin')
def mark_pending(request_id):
    """Mark a payment request as pending with reason"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    reason = request.form.get('reason_pending')
    
    if not reason:
        flash('Please provide a reason for marking as pending.', 'warning')
        return redirect(url_for('view_request', request_id=request_id))
    
    req.status = 'Pending'
    req.reason_pending = reason
    req.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_action(f"Marked payment request #{request_id} as pending")
    
    # Emit real-time update for pending status
    socketio.emit('request_updated', {
        'request_id': request_id,
        'status': 'Pending',
        'reason': reason
    })
    
    flash(f'Payment request #{request_id} has been marked as pending.', 'info')
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
    
    # Check if request is in "Proof Pending" or "Proof Rejected" status
    if req.status not in ['Proof Pending', 'Proof Rejected']:
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
        req.status = 'Proof Sent'
        req.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(f"Uploaded proof for payment request #{request_id}")
        
        # Notify Finance Admin
        notify_finance_and_admin(
            title="Proof of Payment Uploaded",
            message=f"Proof of payment has been uploaded for request #{request_id} by {current_user.name}",
            notification_type="proof_uploaded",
            request_id=request_id
        )
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Proof Sent',
            'requestor': current_user.username
        })
        
        flash('Proof of payment uploaded successfully! Finance will review your proof.', 'success')
    else:
        flash('Invalid file type. Please upload an image (jpg, png, gif, etc.).', 'error')
    
    return redirect(url_for('view_request', request_id=request_id))


@app.route('/request/<int:request_id>/final_approve', methods=['POST'])
@login_required
@role_required('Admin')
def final_approve_request(request_id):
    """Admin final approval after receiving proof"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if request is in "Proof Sent" status
    if req.status != 'Proof Sent':
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


@app.route('/request/<int:request_id>/manager_approve', methods=['POST'])
@login_required
def manager_approve_request(request_id):
    """Manager approves a payment request"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if current user is authorized to approve this request
    is_authorized = False
    
    # Check if current user is the manager of the request submitter
    if req.user.manager_id and req.user.manager_id == current_user.user_id:
        is_authorized = True
    # Special case: Operation Manager can approve Operation department requests
    elif (current_user.role == 'Operation Manager' and 
          req.user.department == 'Operation' and 
          req.user.role != 'Operation Manager'):  # Operation Manager can't approve their own requests
        is_authorized = True
    # Special case: Finance Admin can approve Finance department requests
    elif (current_user.role == 'Finance Admin' and 
          req.user.department == 'Finance' and 
          req.user.role != 'Finance Admin'):  # Finance Admin can't approve their own requests
        is_authorized = True
    
    if not is_authorized:
        flash('You are not authorized to approve this request.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if request is in correct status
    if req.status != 'Pending Manager Approval':
        flash('This request is not pending manager approval.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get form data
    approval_status = request.form.get('approval_status')
    
    if approval_status == 'approve':
        # Manager approves - move to Finance for final approval
        req.status = 'Pending Finance Approval'
        req.manager_approval_date = datetime.utcnow().date()
        req.is_urgent = request.form.get('is_urgent') == 'on'
        req.manager_approval_reason = request.form.get('approval_reason', '').strip()
        req.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(f"Manager approved payment request #{request_id}")
        
        # Notify Finance Admin that request is ready for their review
        notify_finance_and_admin(
            title="Payment Request Ready for Review",
            message=f"Payment request #{request_id} from {req.department} department has been approved by manager and is ready for Finance review",
            notification_type="ready_for_finance_review",
            request_id=request_id
        )
        
        # Emit real-time update to Finance Admin
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Pending Finance Approval',
            'manager_approved': True
        }, room='finance_admin')
        
        flash(f'Payment request #{request_id} has been approved by manager. Sent to Finance for final approval.', 'success')
        
        
    elif approval_status == 'reject':
        # Manager rejects - request is rejected
        rejection_reason = request.form.get('rejection_reason', '').strip()
        if not rejection_reason:
            flash('Please provide a reason for rejection.', 'error')
            return redirect(url_for('view_request', request_id=request_id))
        
        req.status = 'Rejected by Manager'
        req.rejection_reason = rejection_reason
        req.manager_rejection_date = datetime.utcnow().date()
        req.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(f"Manager rejected payment request #{request_id} - Reason: {rejection_reason}")
        
        # Notify the requestor
        create_notification(
            user_id=req.user_id,
            title="Payment Request Rejected",
            message=f"Your payment request #{request_id} has been rejected by your manager. Please review the feedback.",
            notification_type="request_rejected",
            request_id=request_id
        )
        
        # Emit real-time update
        socketio.emit('request_updated', {
            'request_id': request_id,
            'status': 'Rejected by Manager',
            'manager_rejected': True
        })
        
        flash(f'Payment request #{request_id} has been rejected by manager.', 'success')
    
    else:
        flash('Invalid approval status selected.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    return redirect(url_for('view_request', request_id=request_id))


@app.route('/request/<int:request_id>/manager_reject', methods=['POST'])
@login_required
def manager_reject_request(request_id):
    """Manager rejects a payment request"""
    req = PaymentRequest.query.get_or_404(request_id)
    
    # Check if current user is authorized to reject this request
    is_authorized = False
    
    # Check if current user is the manager of the request submitter
    if req.user.manager_id and req.user.manager_id == current_user.user_id:
        is_authorized = True
    # Special case: Operation Manager can reject Operation department requests
    elif (current_user.role == 'Operation Manager' and 
          req.user.department == 'Operation' and 
          req.user.role != 'Operation Manager'):  # Operation Manager can't reject their own requests
        is_authorized = True
    # Special case: Finance Admin can reject Finance department requests
    elif (current_user.role == 'Finance Admin' and 
          req.user.department == 'Finance' and 
          req.user.role != 'Finance Admin'):  # Finance Admin can't reject their own requests
        is_authorized = True
    
    if not is_authorized:
        flash('You are not authorized to reject this request.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if request is in correct status
    if req.status != 'Pending Manager Approval':
        flash('This request is not pending manager approval.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get rejection reason
    reason = request.form.get('rejection_reason', '').strip()
    if not reason:
        flash('Please provide a reason for rejection.', 'error')
        return redirect(url_for('view_request', request_id=request_id))
    
    # Manager rejects - request is rejected
    req.status = 'Rejected by Manager'
    req.rejection_reason = reason
    req.manager_rejection_date = datetime.utcnow().date()
    req.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_action(f"Manager rejected payment request #{request_id} - Reason: {reason}")
    
    # Emit real-time update
    socketio.emit('request_updated', {
        'request_id': request_id,
        'status': 'Rejected by Manager',
        'manager_rejected': True
    })
    
    flash(f'Payment request #{request_id} has been rejected by manager.', 'success')
    return redirect(url_for('dashboard'))


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
@role_required('Finance Admin', 'Finance', 'GM', 'IT', 'Operation Manager')
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
        # For all other statuses (Pending, Proof Pending, Proof Sent, or All), use submission date
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
@role_required('Finance Admin', 'Finance', 'GM', 'IT', 'Operation Manager')
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
@role_required('IT', 'Department Manager')
def manage_users():
    """Manage users (IT only)"""
    # Only IT or IT Department Manager
    if current_user.role == 'Department Manager' and current_user.department != 'IT':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template('manage_users.html', users=users, user=current_user)


@app.route('/users/new', methods=['GET', 'POST'])
@login_required
@role_required('IT', 'Department Manager')
def new_user():
    """Create a new user - IT ONLY"""
    if current_user.role == 'Department Manager' and current_user.department != 'IT':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')  # This is now the email
        password = request.form.get('password')
        department = request.form.get('department')
        role = request.form.get('role')
        manager_id = request.form.get('manager_id')
        
        # Check if username (email) already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Email address already exists.', 'danger')
            return redirect(url_for('new_user'))
        
        # Department restriction removed - multiple accounts per department allowed
        
        # Determine manager assignment
        # If the new user IS a Department Manager, they manage their own department and have no manager above them (besides GM)
        if role == 'Department Manager':
            final_manager_id = None
        else:
            # First preference: explicit manager selection from form
            if manager_id:
                final_manager_id = manager_id
            else:
                # Fallback: find the department's manager user
                dept_manager = User.query.filter_by(department=department, role='Department Manager').first()
                if dept_manager:
                    final_manager_id = dept_manager.user_id
                else:
                    # Special rules: Office → GM, Operation → Operation Manager, Finance → specific named manager
                    if department == 'Office':
                        gm_user = User.query.filter_by(role='GM').first()
                        final_manager_id = gm_user.user_id if gm_user else None
                    elif department == 'Operation':
                        op_manager = User.query.filter_by(role='Operation Manager').first()
                        final_manager_id = op_manager.user_id if op_manager else None
                    elif department == 'Finance':
                        named_manager = User.query.filter_by(name='Abdalaziz Hamood Al Brashdi', department='Finance').first()
                        final_manager_id = named_manager.user_id if named_manager else None
                    else:
                        # No fallback: manager assignment depends solely on users with 'Department Manager' role
                        final_manager_id = None
        
        new_user = User(
            name=name,
            username=username,  # Store email as username
            department=department,
            role=role,
            manager_id=final_manager_id,
            email=username  # Store email in both username and email fields
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        log_action(f"Created new user: {username} ({role}) for department: {department}")
        flash(f'User {username} created successfully for {department} department!', 'success')
        return redirect(url_for('manage_users'))
    
    # Get all users for manager selection
    all_users = User.query.all()
    return render_template('new_user.html', user=current_user, all_users=all_users)


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('IT', 'Department Manager')
def edit_user(user_id):
    """Edit user information - IT ONLY"""
    if current_user.role == 'Department Manager' and current_user.department != 'IT':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    user_to_edit = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_password = request.form.get('password')
        new_department = request.form.get('department')
        new_role = request.form.get('role')
        new_manager_id = request.form.get('manager_id')
        
        # Department restriction removed - multiple accounts per department allowed
        
        # Determine manager assignment on edit
        if new_role == 'Department Manager':
            final_manager_id = None
        else:
            if new_manager_id:
                final_manager_id = new_manager_id
            else:
                dept_manager = User.query.filter_by(department=new_department, role='Department Manager').first()
                if dept_manager:
                    final_manager_id = dept_manager.user_id
                else:
                    # Special rules: Office → GM, Operation → Operation Manager, Finance → specific named manager
                    if new_department == 'Office':
                        gm_user = User.query.filter_by(role='GM').first()
                        final_manager_id = gm_user.user_id if gm_user else None
                    elif new_department == 'Operation':
                        op_manager = User.query.filter_by(role='Operation Manager').first()
                        final_manager_id = op_manager.user_id if op_manager else None
                    elif new_department == 'Finance':
                        named_manager = User.query.filter_by(name='Abdalaziz Hamood Al Brashdi', department='Finance').first()
                        final_manager_id = named_manager.user_id if named_manager else None
                    else:
                        # No fallback: manager assignment depends solely on users with 'Department Manager' role
                        final_manager_id = None
        
        # Update user information
        user_to_edit.name = new_name
        user_to_edit.department = new_department
        user_to_edit.role = new_role
        user_to_edit.manager_id = final_manager_id
        # Email is stored in username field, so no need to update email separately
        
        # Only update password if provided
        if new_password:
            user_to_edit.set_password(new_password)
        
        db.session.commit()
        
        log_action(f"Updated user: {user_to_edit.username} ({new_role}) - Department: {new_department}")
        flash(f'User {user_to_edit.username} has been updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    # Get all users for manager selection (excluding the user being edited)
    all_users = User.query.filter(User.user_id != user_id).all()
    return render_template('edit_user.html', user=current_user, user_to_edit=user_to_edit, all_users=all_users)


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('IT', 'Department Manager')
def delete_user(user_id):
    """Delete a user and handle related data"""
    if current_user.role == 'Department Manager' and current_user.department != 'IT':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
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


# ==================== DEBUG ROUTES ====================

@app.route('/debug/requests')
@login_required
@role_required('Finance Admin', 'IT')
def debug_requests():
    """Debug route to see all requests in the database"""
    all_requests = PaymentRequest.query.order_by(PaymentRequest.created_at.desc()).limit(20).all()
    debug_data = []
    for req in all_requests:
        debug_data.append({
            'request_id': req.request_id,
            'requestor_name': req.requestor_name,
            'department': req.department,
            'status': req.status,
            'user_id': req.user_id,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'amount': float(req.amount)
        })
    return jsonify(debug_data)

# ==================== NOTIFICATION ROUTES ====================

@app.route('/notifications')
@login_required
@role_required('Finance Admin', 'Admin', 'Finance', 'Project', 'Operation Manager')
def notifications():
    """View all notifications for Finance Admin, Finance, Admin, and Project users"""
    if current_user.role == 'Project':
        # For project users, only show due date notifications
        notifications = Notification.query.filter_by(
            user_id=current_user.user_id,
            notification_type='recurring_due'
        ).order_by(Notification.created_at.desc()).all()
    else:
        # For Finance Admin, Admin, Finance, and Operation Manager, show all notifications
        notifications = Notification.query.filter_by(user_id=current_user.user_id).order_by(Notification.created_at.desc()).all()
    
    return render_template('notifications.html', notifications=notifications, user=current_user)


@app.route('/notifications/mark_read/<int:notification_id>')
@login_required
@role_required('Finance Admin', 'Admin', 'Finance', 'Project', 'Operation Manager')
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
@role_required('Finance Admin', 'Admin', 'Finance', 'Project', 'Operation Manager')
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    Notification.query.filter_by(user_id=current_user.user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@app.route('/notifications/mark_paid/<int:notification_id>')
@login_required
@role_required('Finance Admin', 'Admin', 'Finance', 'Project', 'Operation Manager')
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
@role_required('Finance Admin', 'Admin', 'Finance', 'Project', 'Operation Manager')
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
@role_required('Finance Admin', 'Admin', 'Finance', 'Project', 'Operation Manager')
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
@role_required('Finance Admin', 'Admin', 'Finance', 'Project', 'Operation Manager')
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



@app.route('/admin/calendar')
@role_required('Admin', 'Project')
def admin_calendar():
    """Calendar view for recurring payments (Admin and Project roles)"""
    return render_template('admin_calendar.html')

@app.route('/api/admin/recurring-events')
@role_required('Admin', 'Project')
def api_admin_recurring_events():
    """API endpoint for calendar events (Admin and Project roles)"""
    try:
        # Build query for approved recurring payment requests
        query = PaymentRequest.query.filter(
            PaymentRequest.recurring_interval.isnot(None),
            PaymentRequest.recurring_interval != '',
            PaymentRequest.status == 'Approved'
        )
        
        # Project users can only see their department's requests
        if current_user.role == 'Project':
            query = query.filter(PaymentRequest.department == current_user.department)
        
        recurring_requests = query.all()
        
        events = []
        today = date.today()
        
        for req in recurring_requests:
            # Check if this is a variable payment with installments
            schedule = RecurringPaymentSchedule.query.filter_by(request_id=req.request_id).all()
            
            if schedule:
                # For variable payments, calculate remaining amount
                total_paid_amount = 0
                paid_notifications = PaidNotification.query.filter_by(request_id=req.request_id).all()
                
                for installment in schedule:
                    # Check if this specific installment is paid
                    is_paid = any(
                        paid_notif.paid_date == installment.payment_date 
                        for paid_notif in paid_notifications
                    )
                    
                    # If this installment is paid, add its amount to total paid
                    if is_paid:
                        total_paid_amount += float(installment.amount)
                
                # Calculate remaining amount
                remaining_amount = float(req.amount) - total_paid_amount
                
                # If remaining amount is 0 or less, skip this request
                if remaining_amount <= 0:
                    continue
            else:
                # For regular recurring payments, check if there are any paid notifications
                paid_notifications_count = PaidNotification.query.filter_by(request_id=req.request_id).count()
                
                # If there are paid notifications, skip this request entirely
                if paid_notifications_count > 0:
                    continue
            
            if schedule:
                # For variable payments, show only the specific installment dates
                for installment in schedule:
                    # Check if this specific installment is paid
                    paid_notification = PaidNotification.query.filter_by(
                        request_id=req.request_id,
                        paid_date=installment.payment_date
                    ).first()
                    
                    # Determine event color (red if marked late)
                    is_late = LateInstallment.query.filter_by(
                        request_id=req.request_id,
                        payment_date=installment.payment_date
                    ).first() is not None
                    event_color = '#2e7d32' if paid_notification else ('#d32f2f' if is_late else '#8e24aa')
                    
                    # Calculate remaining amount
                    total_paid = sum(
                        pn.amount if hasattr(pn, 'amount') else 0 
                        for pn in PaidNotification.query.filter_by(request_id=req.request_id).all()
                    )
                    remaining_amount = req.amount - total_paid
                    
                    events.append({
                        'title': f'OMR {installment.amount:.3f}',
                        'start': installment.payment_date.isoformat(),
                        'color': event_color,
                        'url': f'/request/{req.request_id}',
                        'extendedProps': {
                            'requestId': req.request_id,
                            'requestType': req.request_type,
                            'companyName': req.company_name,
                            'department': req.department,
                            'purpose': req.purpose,
                            'baseAmount': f'OMR {req.amount:.3f}',
                            'remainingAmount': f'OMR {remaining_amount:.3f}'
                        }
                    })
            else:
                # For regular recurring payments, generate future due dates
                start_date = today
                end_date = today + timedelta(days=365)
                
                due_dates = generate_future_due_dates(req, start_date, end_date)
                
                for due_date, amount in due_dates:
                    # Check if this payment is already marked as paid
                    paid_notification = PaidNotification.query.filter_by(
                        request_id=req.request_id,
                        paid_date=due_date
                    ).first()
                    
                    # Determine event color (red if marked late)
                    is_late = LateInstallment.query.filter_by(
                        request_id=req.request_id,
                        payment_date=due_date
                    ).first() is not None
                    event_color = '#2e7d32' if paid_notification else ('#d32f2f' if is_late else '#8e24aa')
                    
                    events.append({
                        'title': f'OMR {amount:.3f}',
                        'start': due_date.isoformat(),
                        'color': event_color,
                        'url': f'/request/{req.request_id}',
                        'extendedProps': {
                            'requestId': req.request_id,
                            'requestType': req.request_type,
                            'companyName': req.company_name,
                            'department': req.department,
                            'purpose': req.purpose,
                            'baseAmount': None,
                            'remainingAmount': None
                        }
                    })
        
        return jsonify(events)
        
    except Exception as e:
        print(f"Error generating calendar events: {e}")
        return jsonify([])

def add_months(source_date, months):
    """Add months to a date, handling month overflow correctly"""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)

def generate_future_due_dates(req, start_date, end_date):
    """Generate future due dates for a recurring request"""
    if not req.recurring_interval:
        return []
    
    try:
        # Parse the recurring interval
        parts = req.recurring_interval.split(':')
        if len(parts) < 2:
            return []
        
        frequency = parts[0]
        interval = int(parts[1])
        
        if frequency == 'monthly':
            due_dates = []
            
            # Check for new :date: format (e.g., monthly:1:date:2025-10-18:end:2026-01-30)
            if len(parts) > 2 and parts[2] == 'date':
                # Parse the start date
                try:
                    base_date_str = parts[3]
                    base_date = datetime.strptime(base_date_str, '%Y-%m-%d').date()
                    
                    # Parse end date if present
                    config_end_date = None
                    if 'end' in parts:
                        end_index = parts.index('end')
                        if end_index + 1 < len(parts):
                            config_end_date = datetime.strptime(parts[end_index + 1], '%Y-%m-%d').date()
                    
                    # Use the earlier of the two end dates
                    effective_end_date = end_date
                    if config_end_date:
                        effective_end_date = min(end_date, config_end_date)
                    
                    # Generate recurring dates starting from base_date
                    current_date = base_date
                    if current_date < start_date:
                        # If base_date is before start_date, advance to the first occurrence after start_date
                        months_diff = (start_date.year - base_date.year) * 12 + (start_date.month - base_date.month)
                        cycles = (months_diff // interval) + 1
                        current_date = add_months(base_date, cycles * interval)
                    
                    # Generate dates
                    while current_date <= effective_end_date:
                        if current_date >= start_date:
                            due_dates.append((current_date, req.amount))
                        # Move to next occurrence
                        current_date = add_months(current_date, interval)
                    
                except (ValueError, IndexError) as e:
                    print(f"Error parsing date format: {e}")
                    return []
            
            # Check if old specific days format is configured
            elif len(parts) > 2 and parts[2] == 'days':
                # Parse specific days from the interval
                days = [int(day) for day in parts[3].split(',')]
                year = int(parts[4]) if len(parts) > 4 else start_date.year
                month = int(parts[5]) if len(parts) > 5 else start_date.month
                
                # Generate dates for the specific days
                current_date = start_date
                month_count = 0
                
                while current_date <= end_date:
                    if month_count % interval == 0:
                        # Generate dates for each specific day in this month
                        for day in days:
                            try:
                                # Create date for this specific day
                                due_date = date(current_date.year, current_date.month, day)
                                if due_date >= start_date and due_date <= end_date:
                                    due_dates.append((due_date, req.amount))
                            except ValueError:
                                # Skip invalid dates (like Feb 30)
                                continue
                    
                    # Move to next month
                    if current_date.month == 12:
                        current_date = date(current_date.year + 1, 1, 1)
                    else:
                        current_date = date(current_date.year, current_date.month + 1, 1)
                    month_count += 1
            else:
                # Fallback to original logic for simple monthly intervals
                current_date = start_date
                month_count = 0
                while current_date <= end_date:
                    if month_count % interval == 0:
                        due_dates.append((current_date, req.amount))
                    current_date = current_date + timedelta(days=1)
                    if current_date.day == 1:  # New month
                        month_count += 1
            
            return due_dates[:12]  # Limit to 12 months
        
        return []
        
    except Exception as e:
        print(f"Error generating due dates: {e}")
        return []


@app.route('/api/requests/mark_paid', methods=['POST'])
@role_required('Admin')
def mark_request_paid():
    """Mark an entire request as paid"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        request_id = data.get('request_id')
        amount = data.get('amount')
        
        if not request_id or not amount:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Get the payment request
        payment_request = PaymentRequest.query.get(request_id)
        if not payment_request:
            return jsonify({'success': False, 'message': 'Request not found'}), 404
        
        # Check if request is approved
        if payment_request.status != 'Approved':
            return jsonify({'success': False, 'message': 'Request must be approved before marking as paid'}), 400
        
        # Check if request is recurring
        if not payment_request.recurring_interval:
            return jsonify({'success': False, 'message': 'This endpoint is only for recurring payments'}), 400
        
        # Check if this request is already paid
        existing_paid = PaidNotification.query.filter_by(request_id=request_id).first()
        
        if existing_paid:
            return jsonify({'success': False, 'message': 'This request is already marked as paid'}), 400
        
        # Create paid notification for the entire request
        paid_notification = PaidNotification(
            request_id=request_id,
            user_id=current_user.user_id,
            paid_date=date.today()
        )
        
        db.session.add(paid_notification)
        db.session.commit()
        
        # Log the action
        audit_log = AuditLog(
            user_id=current_user.user_id,
            action='Mark Request Paid',
            details=f'Marked entire request #{request_id} (OMR {amount}) as paid',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Request marked as paid successfully'})
        
    except Exception as e:
        print(f"Error marking request as paid: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while marking request as paid'}), 500


@app.route('/api/installments/mark_paid', methods=['POST'])
@role_required('Admin', 'Finance')
def mark_installment_paid():
    """Mark a specific installment as paid"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        request_id = data.get('request_id')
        payment_date = data.get('payment_date')
        amount = data.get('amount')
        
        if not request_id or not payment_date or not amount:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Convert payment_date string to date object
        from datetime import datetime
        try:
            payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        # Get the payment request
        payment_request = PaymentRequest.query.get(request_id)
        if not payment_request:
            return jsonify({'success': False, 'message': 'Request not found'}), 404
        
        # Check if request is approved
        if payment_request.status != 'Approved':
            return jsonify({'success': False, 'message': 'Request must be approved before marking as paid'}), 400
        
        # Check if this installment is already paid
        existing_paid = PaidNotification.query.filter_by(
            request_id=request_id,
            paid_date=payment_date_obj
        ).first()
        
        if existing_paid:
            return jsonify({'success': False, 'message': 'This installment is already marked as paid'}), 400
        
        # Create paid notification
        paid_notification = PaidNotification(
            request_id=request_id,
            user_id=current_user.user_id,
            paid_date=payment_date_obj
        )
        
        db.session.add(paid_notification)
        db.session.commit()
        
        # Log the action
        audit_log = AuditLog(
            user_id=current_user.user_id,
            action='Mark Installment Paid',
            details=f'Marked installment of OMR {amount} due on {payment_date} as paid for request #{request_id}',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Installment marked as paid successfully'})
        
    except Exception as e:
        print(f"Error marking installment as paid: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while marking installment as paid'}), 500


@app.route('/api/installments/mark_late', methods=['POST'])
@role_required('Admin')
def mark_installment_late():
    """Mark a specific installment as late (Admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        request_id = data.get('request_id')
        payment_date = data.get('payment_date')
        
        if not request_id or not payment_date:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Convert payment_date string to date object
        from datetime import datetime
        try:
            payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        # Get the payment request
        payment_request = PaymentRequest.query.get(request_id)
        if not payment_request:
            return jsonify({'success': False, 'message': 'Request not found'}), 404
        
        # Check if request is approved
        if payment_request.status != 'Approved':
            return jsonify({'success': False, 'message': 'Request must be approved before marking installments as late'}), 400
        
        # If already paid, cannot be marked late
        existing_paid = PaidNotification.query.filter_by(
            request_id=request_id,
            paid_date=payment_date_obj
        ).first()
        if existing_paid:
            return jsonify({'success': False, 'message': 'This installment is already marked as paid'}), 400
        
        # Check if already marked late
        from models import LateInstallment
        existing_late = LateInstallment.query.filter_by(
            request_id=request_id,
            payment_date=payment_date_obj
        ).first()
        if existing_late:
            return jsonify({'success': True, 'message': 'Installment already marked as late'})
        
        # Create late installment record
        late = LateInstallment(
            request_id=request_id,
            payment_date=payment_date_obj,
            marked_by_user_id=current_user.user_id
        )
        db.session.add(late)
        db.session.commit()
        
        # Log the action
        log_action(f"Marked installment due on {payment_date} as LATE for request #{request_id}")
        
        return jsonify({'success': True, 'message': 'Installment marked as late'})
    except Exception as e:
        print(f"Error marking installment as late: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while marking installment as late'}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5005)

