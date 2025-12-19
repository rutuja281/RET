#!/usr/bin/env python3
"""Check if all dependencies are installed correctly"""

import sys

print("=" * 60)
print("Checking Setup...")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print()

missing = []
required_modules = [
    'flask',
    'flask_sqlalchemy',
    'pandas',
    'numpy',
    'matplotlib',
    'seaborn',
    'werkzeug'
]

for module in required_modules:
    try:
        __import__(module)
        print(f"✓ {module}")
    except ImportError:
        print(f"✗ {module} - MISSING")
        missing.append(module)

print()
if missing:
    print("=" * 60)
    print("MISSING MODULES DETECTED!")
    print("=" * 60)
    print(f"Please install: {', '.join(missing)}")
    print()
    print("Run: pip3 install -r requirements.txt")
    sys.exit(1)
else:
    print("=" * 60)
    print("✓ All dependencies are installed!")
    print("=" * 60)
    
    # Try importing the app
    try:
        from app import app
        print("✓ App can be imported successfully")
        print("✓ Setup is complete!")
    except Exception as e:
        print(f"✗ Error importing app: {e}")
        sys.exit(1)

