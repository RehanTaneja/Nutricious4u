#!/usr/bin/env python3
"""
Test script to verify diet PDF functionality fixes
"""

import requests
import json
import os

# Configuration
API_BASE_URL = "http://172.16.0.28:8000/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"  # From the logs

def test_diet_endpoints():
    """Test the diet-related endpoints"""
    
    print("Testing Diet PDF Functionality...")
    print("=" * 50)
    
    # Test 1: Get user diet info
    print("\n1. Testing GET /users/{user_id}/diet")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 2: Get user diet PDF
    print("\n2. Testing GET /users/{user_id}/diet/pdf")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("PDF endpoint working correctly")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Content-Length: {len(response.content)} bytes")
        elif response.status_code == 302:
            print("Redirect response (expected for Firebase Storage URLs)")
            print(f"Location: {response.headers.get('location', 'unknown')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 3: Get user profile
    print("\n3. Testing GET /users/{user_id}/profile")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"dietPdfUrl: {data.get('dietPdfUrl', 'Not found')}")
            print(f"lastDietUpload: {data.get('lastDietUpload', 'Not found')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_api_connectivity():
    """Test basic API connectivity"""
    print("\nTesting API Connectivity...")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("API server is running")
        else:
            print("API server health check failed")
    except Exception as e:
        print(f"API connectivity failed: {e}")

if __name__ == "__main__":
    test_api_connectivity()
    test_diet_endpoints() 