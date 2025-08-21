#!/usr/bin/env python3
"""
iOS Crash Debug Test Script
Tests all API endpoints called during login sequence to identify potential crash points
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://nutricious4u-production.up.railway.app"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"  # From the logs

def test_api_endpoint(endpoint, method="GET", data=None, description=""):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "User-Agent": "Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 Testing: {description}")
    print(f"   URL: {url}")
    print(f"   Method: {method}")
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            print(f"   ❌ Unsupported method: {method}")
            return False
            
        duration = (time.time() - start_time) * 1000
        
        print(f"   Status: {response.status_code}")
        print(f"   Duration: {duration:.0f}ms")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"   ✅ Success - Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                return True
            except json.JSONDecodeError:
                print(f"   ⚠️  Success but invalid JSON response")
                return True
        else:
            print(f"   ❌ Failed - Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Error text: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout after 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection error")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_login_sequence():
    """Test the complete login sequence"""
    print("🚀 Testing iOS Login Sequence")
    print("=" * 50)
    
    # Test 1: Profile check
    success1 = test_api_endpoint(
        f"/api/users/{TEST_USER_ID}/profile",
        description="1. Profile Check"
    )
    
    # Add delay to simulate iOS timing
    time.sleep(2)
    
    # Test 2: Subscription status
    success2 = test_api_endpoint(
        f"/api/subscription/status/{TEST_USER_ID}",
        description="2. Subscription Status"
    )
    
    # Add delay to simulate iOS timing
    time.sleep(2)
    
    # Test 3: Lock status
    success3 = test_api_endpoint(
        f"/api/users/{TEST_USER_ID}/lock-status",
        description="3. Lock Status"
    )
    
    # Add delay to simulate iOS timing
    time.sleep(2)
    
    # Test 4: Diet check (the one that was failing)
    success4 = test_api_endpoint(
        f"/api/users/{TEST_USER_ID}/diet",
        description="4. Diet Check (Previously Failed)"
    )
    
    # Add delay to simulate iOS timing
    time.sleep(2)
    
    # Test 5: Log summary (dashboard data)
    success5 = test_api_endpoint(
        f"/api/food/log/summary/{TEST_USER_ID}",
        description="5. Log Summary (Dashboard)"
    )
    
    # Add delay to simulate iOS timing
    time.sleep(2)
    
    # Test 6: Workout log summary
    success6 = test_api_endpoint(
        f"/api/workout/log/summary/{TEST_USER_ID}",
        description="6. Workout Log Summary (Dashboard)"
    )
    
    # Add delay to simulate iOS timing
    time.sleep(2)
    
    # Test 7: Recipes
    success7 = test_api_endpoint(
        "/api/recipes",
        description="7. Recipes (Recipes Tab)"
    )
    
    print("\n" + "=" * 50)
    print("📊 Login Sequence Test Results:")
    print(f"1. Profile Check: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"2. Subscription Status: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"3. Lock Status: {'✅ PASS' if success3 else '❌ FAIL'}")
    print(f"4. Diet Check: {'✅ PASS' if success4 else '❌ FAIL'}")
    print(f"5. Log Summary: {'✅ PASS' if success5 else '❌ FAIL'}")
    print(f"6. Workout Summary: {'✅ PASS' if success6 else '❌ FAIL'}")
    print(f"7. Recipes: {'✅ PASS' if success7 else '❌ FAIL'}")
    
    total_success = sum([success1, success2, success3, success4, success5, success6, success7])
    print(f"\n🎯 Overall: {total_success}/7 endpoints working")
    
    if total_success == 7:
        print("✅ All endpoints working - the issue might be in the frontend logic")
    else:
        print("❌ Some endpoints failing - this could be causing the crash")

def test_concurrent_requests():
    """Test concurrent requests to simulate iOS networking issues"""
    print("\n🔄 Testing Concurrent Requests (iOS Networking Simulation)")
    print("=" * 50)
    
    import threading
    import concurrent.futures
    
    endpoints = [
        f"/api/users/{TEST_USER_ID}/profile",
        f"/api/subscription/status/{TEST_USER_ID}",
        f"/api/users/{TEST_USER_ID}/lock-status",
        f"/api/users/{TEST_USER_ID}/diet",
        f"/api/food/log/summary/{TEST_USER_ID}",
        f"/api/workout/log/summary/{TEST_USER_ID}",
        "/api/recipes"
    ]
    
    def make_request(endpoint):
        url = f"{BASE_URL}{endpoint}"
        headers = {
            "User-Agent": "Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return endpoint, response.status_code, response.elapsed.total_seconds() * 1000
        except Exception as e:
            return endpoint, f"ERROR: {e}", 0
    
    print("Making concurrent requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    print("\n📊 Concurrent Request Results:")
    for endpoint, status, duration in results:
        if isinstance(status, int):
            print(f"   {endpoint}: {status} ({duration:.0f}ms)")
        else:
            print(f"   {endpoint}: {status}")

def test_ios_specific_headers():
    """Test with iOS-specific headers"""
    print("\n📱 Testing iOS-Specific Headers")
    print("=" * 50)
    
    ios_headers = {
        "User-Agent": "Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    url = f"{BASE_URL}/api/users/{TEST_USER_ID}/profile"
    
    try:
        response = requests.get(url, headers=ios_headers, timeout=30)
        print(f"iOS Headers Test: {response.status_code} ({response.elapsed.total_seconds() * 1000:.0f}ms)")
        
        if response.status_code == 200:
            print("✅ iOS headers working correctly")
        else:
            print(f"❌ iOS headers issue: {response.status_code}")
            
    except Exception as e:
        print(f"❌ iOS headers error: {e}")

if __name__ == "__main__":
    print(f"🔧 iOS Crash Debug Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing against: {BASE_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    
    # Run all tests
    test_login_sequence()
    test_concurrent_requests()
    test_ios_specific_headers()
    
    print("\n🎯 Debug Test Complete!")
    print("If all endpoints are working, the issue is likely in the frontend logic.")
    print("If some endpoints are failing, those could be causing the iOS crash.")
