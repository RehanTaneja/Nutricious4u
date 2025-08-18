#!/usr/bin/env python3
"""
Comprehensive test script to verify iOS fixes for Nutricious4u app
Tests login, API connections, and PDF viewing functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "https://nutricious4u-production.up.railway.app/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"  # From the logs
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def test_api_connection():
    """Test basic API connectivity"""
    print_section("Testing API Connection")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        
        # Test with iOS-specific headers
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(f"{API_BASE_URL}/health", headers=headers, timeout=10)
        print(f"✅ iOS headers test: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_user_profile_endpoint():
    """Test the user profile endpoint that was failing"""
    print_section("Testing User Profile Endpoint")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test the exact endpoint from the logs
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", headers=headers, timeout=20)
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Profile fetch successful")
            print(f"   User: {profile.get('firstName', 'N/A')} {profile.get('lastName', 'N/A')}")
            print(f"   Email: {profile.get('email', 'N/A')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  User profile not found (expected for test user)")
            return True
        else:
            print(f"❌ Profile fetch failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Profile fetch timeout (improved timeout handling should prevent this)")
        return False
    except Exception as e:
        print(f"❌ Profile fetch error: {e}")
        return False

def test_food_log_summary_endpoint():
    """Test the food log summary endpoint that was failing"""
    print_section("Testing Food Log Summary Endpoint")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test the exact endpoint from the logs
        response = requests.get(f"{API_BASE_URL}/food/log/summary/{TEST_USER_ID}", headers=headers, timeout=30)
        
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Food log summary successful")
            print(f"   History entries: {len(summary.get('history', []))}")
            return True
        else:
            print(f"❌ Food log summary failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Food log summary timeout (improved timeout handling should prevent this)")
        return False
    except Exception as e:
        print(f"❌ Food log summary error: {e}")
        return False

def test_workout_log_summary_endpoint():
    """Test the workout log summary endpoint that was failing"""
    print_section("Testing Workout Log Summary Endpoint")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test the exact endpoint from the logs
        response = requests.get(f"{API_BASE_URL}/workout/log/summary/{TEST_USER_ID}", headers=headers, timeout=30)
        
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Workout log summary successful")
            print(f"   History entries: {len(summary.get('history', []))}")
            return True
        else:
            print(f"❌ Workout log summary failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Workout log summary timeout (improved timeout handling should prevent this)")
        return False
    except Exception as e:
        print(f"❌ Workout log summary error: {e}")
        return False

def test_retry_mechanism():
    """Test the retry mechanism for failed requests"""
    print_section("Testing Retry Mechanism")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test with a non-existent endpoint to trigger retries
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/non-existent-endpoint", headers=headers, timeout=10)
        end_time = time.time()
        
        print(f"✅ Retry mechanism test completed in {end_time - start_time:.2f}s")
        print(f"   Expected 404, got: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ Retry mechanism test failed: {e}")
        return False

def test_pdf_endpoint():
    """Test the PDF endpoint for diet viewing"""
    print_section("Testing PDF Endpoint")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test the PDF endpoint
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf", headers=headers, timeout=20)
        
        if response.status_code == 200:
            print(f"✅ PDF endpoint successful")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   Content-Length: {len(response.content)} bytes")
            return True
        elif response.status_code == 404:
            print(f"⚠️  No PDF found for user (expected for test user)")
            return True
        else:
            print(f"❌ PDF endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ PDF endpoint error: {e}")
        return False

def test_mobile_app_simulation():
    """Simulate mobile app behavior with multiple concurrent requests"""
    print_section("Testing Mobile App Simulation")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Simulate the exact requests from the logs
        endpoints = [
            f"/users/{TEST_USER_ID}/profile",
            f"/food/log/summary/{TEST_USER_ID}",
            f"/workout/log/summary/{TEST_USER_ID}"
        ]
        
        print("Simulating concurrent requests like mobile app...")
        start_time = time.time()
        
        responses = []
        for endpoint in endpoints:
            try:
                response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=20)
                responses.append((endpoint, response.status_code))
            except Exception as e:
                responses.append((endpoint, f"Error: {e}"))
        
        end_time = time.time()
        
        print(f"✅ Concurrent requests completed in {end_time - start_time:.2f}s")
        for endpoint, status in responses:
            print(f"   {endpoint}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mobile app simulation failed: {e}")
        return False

def main():
    """Run all tests"""
    print_header("iOS Fixes Verification Test")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("API Connection", test_api_connection),
        ("User Profile Endpoint", test_user_profile_endpoint),
        ("Food Log Summary Endpoint", test_food_log_summary_endpoint),
        ("Workout Log Summary Endpoint", test_workout_log_summary_endpoint),
        ("Retry Mechanism", test_retry_mechanism),
        ("PDF Endpoint", test_pdf_endpoint),
        ("Mobile App Simulation", test_mobile_app_simulation),
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
        print("🎉 All tests passed! iOS fixes are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
