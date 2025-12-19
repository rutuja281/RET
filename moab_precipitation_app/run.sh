#!/bin/bash
# Quick start script for Moab Precipitation Analysis App

echo "Starting Moab Precipitation Analysis Web Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python database.py

# Run the application
echo ""
echo "Starting Flask application..."
echo "Open your browser and navigate to: http://localhost:5000"
echo ""
python app.py

