#!/usr/bin/env python3
"""
Start the Flask server
"""
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("Moab Precipitation Analysis Web Application")
    print("=" * 60)
    print("\nStarting server...")
    print("Open your browser and navigate to:")
    print("  http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    app.run(debug=True, host='127.0.0.1', port=5000)

