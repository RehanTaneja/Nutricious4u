#!/usr/bin/env python3
"""
Test script to verify PDF viewing functionality
"""

import requests
import json

# Configuration
API_BASE_URL = "http://172.16.0.28:8000/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"

def test_pdf_viewing():
    """Test the PDF viewing functionality"""
    
    print("Testing PDF Viewing Functionality...")
    print("=" * 50)
    
    # Test 1: Get user profile to check diet info
    print("\n1. Testing GET /users/{user_id}/profile")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ User profile retrieved successfully")
            print(f"  dietPdfUrl: {data.get('dietPdfUrl', 'Not found')}")
            print(f"  lastDietUpload: {data.get('lastDietUpload', 'Not found')}")
            print(f"  hasDiet: {data.get('dietPdfUrl') is not None}")
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 2: Get diet PDF directly
    print("\n2. Testing GET /users/{user_id}/diet/pdf")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ PDF endpoint working correctly")
            print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"  Content-Length: {len(response.content)} bytes")
            print(f"  PDF data received successfully")
        elif response.status_code == 302:
            print(f"✓ Redirect response (expected for Firebase Storage URLs)")
            print(f"  Location: {response.headers.get('location', 'unknown')}")
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 3: Test PDF URL construction for mobile app
    print("\n3. Testing PDF URL construction for mobile app")
    try:
        # Simulate what the mobile app would do
        pdf_url = f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf"
        print(f"  Mobile app would use URL: {pdf_url}")
        
        # Test if this URL works
        response = requests.get(pdf_url)
        if response.status_code in [200, 302]:
            print(f"✓ URL is accessible from mobile app")
        else:
            print(f"✗ URL not accessible: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")

def test_api_connectivity():
    """Test basic API connectivity"""
    print("\nTesting API Connectivity...")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✓ API server is running")
        else:
            print("✗ API server health check failed")
    except Exception as e:
        print(f"✗ API connectivity failed: {e}")

if __name__ == "__main__":
    test_api_connectivity()
    test_pdf_viewing() 