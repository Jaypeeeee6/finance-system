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
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

