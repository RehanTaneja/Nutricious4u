#!/usr/bin/env python3
"""
Test script to check backend deployment status and identify 500 errors
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "https://nutricious4u-production.up.railway.app/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def test_backend_status():
    """Test basic backend connectivity and status"""
    print_section("Testing Backend Status")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        # Test with iOS headers
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        response = requests.get(f"{API_BASE_URL}/", headers=headers, timeout=10)
        print(f"✅ Root endpoint with iOS headers: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Backend connectivity failed: {e}")
        return False

def test_user_profile_endpoint_detailed():
    """Test user profile endpoint with detailed error analysis"""
    print_section("Testing User Profile Endpoint (Detailed)")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test the exact endpoint from the logs
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text[:500]}...")
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Profile fetch successful")
            print(f"   User: {profile.get('firstName', 'N/A')} {profile.get('lastName', 'N/A')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  User profile not found (expected for test user)")
            return True
        elif response.status_code == 500:
            print(f"❌ Internal server error")
            print(f"   This suggests a backend deployment issue or Firebase connection problem")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Profile fetch timeout")
        return False
    except Exception as e:
        print(f"❌ Profile fetch error: {e}")
        return False

def test_firebase_connection():
    """Test if Firebase connection is working"""
    print_section("Testing Firebase Connection")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test a simple endpoint that doesn't require Firebase
        response = requests.get(f"{API_BASE_URL}/workout/search?query=running", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Workout search successful (Firebase-independent endpoint)")
            return True
        else:
            print(f"❌ Workout search failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Firebase connection test failed: {e}")
        return False

def test_backend_version():
    """Test if backend is running the latest version"""
    print_section("Testing Backend Version")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test if the new middleware is working by checking for custom headers
        response = requests.get(f"{API_BASE_URL}/", headers=headers, timeout=10)
        
        # Check if the new middleware headers are present
        x_platform = response.headers.get('X-Platform')
        x_response_time = response.headers.get('X-Response-Time')
        
        print(f"X-Platform header: {x_platform}")
        print(f"X-Response-Time header: {x_response_time}")
        
        if x_platform and x_response_time:
            print(f"✅ Backend appears to be running latest version with middleware")
            return True
        else:
            print(f"⚠️  Backend may not be running latest version (missing middleware headers)")
            return False
            
    except Exception as e:
        print(f"❌ Backend version test failed: {e}")
        return False

def main():
    """Run all tests"""
    print_header("Backend Deployment Status Check")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Backend Status", test_backend_status),
        ("User Profile Endpoint (Detailed)", test_user_profile_endpoint_detailed),
        ("Firebase Connection", test_firebase_connection),
        ("Backend Version", test_backend_version),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Results Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Backend deployment may need attention.")
        print("\nRecommendations:")
        print("1. Check if backend changes have been deployed to Railway")
        print("2. Verify Firebase credentials and connection")
        print("3. Check Railway logs for deployment errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
