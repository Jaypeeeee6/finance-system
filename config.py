import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    # Use absolute path under instance/ to avoid "unable to open database file"
    _BASEDIR = os.path.abspath(os.path.dirname(__file__))
    _INSTANCE_DIR = os.path.join(_BASEDIR, 'instance')
    os.makedirs(_INSTANCE_DIR, exist_ok=True)
    _DB_PATH = os.path.join(_INSTANCE_DIR, 'payment_system.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + _DB_PATH.replace('\\', '/')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'receipts')
    CHEQUE_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'cheque')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max total request size (all files + form data)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max per file
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Session configuration
    # PERMANENT_SESSION_LIFETIME is only used when session.permanent = True
    # We use session.permanent = False, so sessions expire on browser close
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=10)  # Used for idle timeout enforcement only
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Shared cookie with Ticketing: set in .env (e.g. .localhost or .maagroup.om). Leave unset/empty for single-host (e.g. localhost only).
    _session_domain = os.environ.get('SESSION_COOKIE_DOMAIN', '').strip()
    SESSION_COOKIE_DOMAIN = _session_domain or None
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME') or 'session'
    # Ensure session cookie expires when browser closes (no Max-Age or Expires)
    # When session.permanent = False, Flask should create a session cookie without expiration
    # But we explicitly ensure this by not setting SESSION_COOKIE_EXPIRES
    
    # Email configuration (Flask-Mail)
    # IMPORTANT: For Gmail, you MUST use an App Password (not your regular password)
    # Steps: Google Account → Security → 2-Step Verification → App passwords
    # Create an App Password and use it below
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    
    # Email credentials configured
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'noreply.financepin@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'bjgkbjxtzfbzwoqp'  # App Password (spaces removed)
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply.financepin@gmail.com'
    NOTIFICATION_SENDER_NAME = os.environ.get('NOTIFICATION_SENDER_NAME') or 'Payment System - Notifications'
    PIN_SENDER_NAME = os.environ.get('PIN_SENDER_NAME') or 'Payment System - PIN'
    
    
    # PIN configuration
    PIN_EXPIRY_MINUTES = 2  # PIN expires after 2 minutes

    # Ticketing user sync: same email/password in both apps (set in .env; if unset, sync is skipped)
    TICKETING_SYNC_URL = os.environ.get('TICKETING_SYNC_URL') or None  # e.g. http://localhost:9009
    FINANCE_SYNC_SECRET = os.environ.get('FINANCE_SYNC_SECRET') or None  # same as Ticketing's FINANCE_SYNC_SECRET

    # IT Support / Ticketing link (Ask IT Support button). Set in .env: localhost use http://localhost:9009, production use https://ticketing.maagroup.om
    TICKETING_URL = os.environ.get('TICKETING_URL') or 'http://localhost:9009'

