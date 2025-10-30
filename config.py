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
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=10)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
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
    
    # PIN configuration
    PIN_EXPIRY_MINUTES = 2  # PIN expires after 2 minutes
    

