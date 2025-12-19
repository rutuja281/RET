#!/bin/bash
# Ensure we're using the right Python and all dependencies

cd "$(dirname "$0")"

echo "Checking Python environment..."
python3 --version

echo ""
echo "Checking dependencies..."
python3 check_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Starting Flask application..."
    echo "Press Ctrl+C to stop"
    echo ""
    python3 app.py
else
    echo ""
    echo "ERROR: Dependencies are missing!"
    echo "Please run: pip3 install -r requirements.txt"
    exit 1
fi

