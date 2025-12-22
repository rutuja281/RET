#!/usr/bin/env python3
"""Test script to verify the /process endpoint returns valid JSON"""

import requests
import json

# Test data
test_data = {
    'file_id': 999,  # Non-existent file to trigger error
    'months': [],
    'seasons': [],
    'plot_types': [],
    'generate_all': False,
    'enable_comparison': False
}

try:
    response = requests.post('http://localhost:5000/process', 
                           json=test_data,
                           timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
    print(f"Response Length: {len(response.text)}")
    
    try:
        data = response.json()
        print(f"✓ Valid JSON received:")
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError as e:
        print(f"✗ JSON Parse Error: {e}")
        print(f"Response text (first 500 chars): {response.text[:500]}")
        
except requests.exceptions.ConnectionError:
    print("✗ Could not connect to server. Is Flask running on localhost:5000?")
except Exception as e:
    print(f"✗ Error: {e}")

