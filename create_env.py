"""
Script to create .env file for the application
"""

env_content = """# Flask Configuration
SECRET_KEY=dev-secret-key-change-in-production-12345
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration - Using SQLite for easy setup
DATABASE_URL=sqlite:///payment_system.db

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads/receipts

# Session Configuration
PERMANENT_SESSION_LIFETIME=28800
"""

try:
    with open('.env', 'w') as f:
        f.write(env_content)
    print("[OK] .env file created successfully!")
    print("\nYou can now run:")
    print("  python init_db.py")
    print("  python app.py")
except Exception as e:
    print(f"Error creating .env file: {e}")



