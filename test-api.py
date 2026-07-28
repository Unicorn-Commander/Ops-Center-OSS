#!/usr/bin/env python3

import sys
sys.path.append('.')

# Activate venv
activate_this = 'venv/bin/activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

import requests

# Test the API
try:
    response = requests.get('http://localhost:8085/api/v1/system/status')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")