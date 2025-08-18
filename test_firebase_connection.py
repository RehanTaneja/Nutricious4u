#!/usr/bin/env python3
"""
Test script to check Firebase connection and identify the specific issue
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

def test_firebase_connection():
    """Test Firebase connection by checking if the service is available"""
    print_section("Testing Firebase Connection")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test a simple endpoint that should work if Firebase is available
        response = requests.get(f"{API_BASE_URL}/workout/search?query=running", headers=headers, timeout=10)
        
        print(f"Workout search status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print(f"✅ Workout search successful - Firebase connection appears to be working")
            return True
        elif response.status_code == 503:
            print(f"❌ Firebase service unavailable (503)")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Firebase connection test failed: {e}")
        return False

def test_user_profile_with_detailed_error():
    """Test user profile endpoint with detailed error analysis"""
    print_section("Testing User Profile Endpoint (Detailed Error Analysis)")
    
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
        print(f"Response Body: {response.text}")
        
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
            print(f"   This suggests a backend code issue or Firebase connection problem")
            return False
        elif response.status_code == 503:
            print(f"❌ Service unavailable - Firebase connection issue")
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

def test_firebase_initialization():
    """Test if Firebase initialization is working"""
    print_section("Testing Firebase Initialization")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test the test-deployment endpoint to see if backend is running
        response = requests.get(f"{API_BASE_URL}/test-deployment", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is running")
            print(f"   Version: {data.get('version', 'N/A')}")
            print(f"   iOS fixes: {data.get('ios_fixes', 'N/A')}")
            return True
        else:
            print(f"❌ Backend test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend initialization test failed: {e}")
        return False

def test_environment_variables():
    """Test if environment variables are properly set"""
    print_section("Testing Environment Variables")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test if we can get any response from the backend
        response = requests.get(f"{API_BASE_URL}/", headers=headers, timeout=10)
        
        print(f"Backend root endpoint: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        # Check if the response contains any Firebase-related errors
        if "Firebase" in response.text or "firebase" in response.text.lower():
            print(f"⚠️  Response contains Firebase-related content")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def main():
    """Run all tests"""
    print_header("Firebase Connection Diagnostic")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Firebase Initialization", test_firebase_initialization),
        ("Environment Variables", test_environment_variables),
        ("Firebase Connection", test_firebase_connection),
        ("User Profile Endpoint (Detailed)", test_user_profile_with_detailed_error),
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
        print("🎉 All tests passed! Firebase connection is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Firebase connection may have issues.")
        print("\nRecommendations:")
        print("1. Check Firebase credentials in Railway environment variables")
        print("2. Verify FIREBASE_PROJECT_ID is set correctly")
        print("3. Check if Firebase service account has proper permissions")
        print("4. Review Railway logs for Firebase initialization errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
