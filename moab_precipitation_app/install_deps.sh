#!/bin/bash
# Install dependencies compatible with Python 3.13

echo "Installing Flask and core dependencies..."
pip install Flask Flask-SQLAlchemy Werkzeug SQLAlchemy

echo "Installing numpy..."
pip install numpy

echo "Installing matplotlib and seaborn..."
pip install matplotlib seaborn

echo "Installing pandas (will get Python 3.13 compatible version)..."
pip install "pandas>=2.2.0"

echo ""
echo "✓ Installation complete!"
echo "Run: python check_setup.py to verify"

