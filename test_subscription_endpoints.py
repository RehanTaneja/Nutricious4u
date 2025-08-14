#!/usr/bin/env python3

import requests
import json

# Test the subscription endpoints
BASE_URL = "https://nutricious4u-production.up.railway.app"

def test_subscription_endpoints():
    print("Testing subscription endpoints...")
    
    # Test 1: Get subscription plans
    print("\n1. Testing GET /api/subscription/plans")
    try:
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Get subscription status
    print("\n2. Testing GET /api/subscription/status/{userId}")
    try:
        response = requests.get(f"{BASE_URL}/api/subscription/status/test-user-id")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Health check
    print("\n3. Testing GET /health")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_subscription_endpoints()
