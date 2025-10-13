#!/bin/bash

echo "===================================="
echo "Payment Request Management System"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Install dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "WARNING: Please edit .env file and configure your database settings!"
    echo ""
    read -p "Press enter to continue..."
fi

# Create uploads directory if it doesn't exist
if [ ! -d "uploads/receipts" ]; then
    echo "Creating uploads directory..."
    mkdir -p uploads/receipts
    echo ""
fi

# Ask if user wants to initialize database
read -p "Do you want to initialize the database? (yes/no): " INIT_DB
if [ "$INIT_DB" = "yes" ] || [ "$INIT_DB" = "y" ]; then
    echo ""
    echo "Initializing database..."
    python init_db.py
    echo ""
fi

# Start the application
echo "Starting Flask application..."
echo ""
echo "Application will be available at: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop the server"
echo ""
python app.py

