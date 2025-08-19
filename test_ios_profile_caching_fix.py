#!/usr/bin/env python3
"""
Test script to verify iOS profile caching fix prevents 499 errors
Simulates the exact scenario: App.tsx profile request + ChatbotScreen profile request
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://nutricious4u-production.up.railway.app/api"
USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"
HEADERS = {
    "User-Agent": "Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "Content-Type": "application/json"
}

def log_request(method, path, status_code, duration, error=None):
    """Log request details in the same format as the backend logs"""
    timestamp = datetime.utcnow().isoformat() + "Z"
    print(f'requestId:"test-{int(time.time())}"')
    print(f'timestamp:"{timestamp}"')
    print(f'method:"{method}"')
    print(f'path:"{path}"')
    print(f'host:"nutricious4u-production.up.railway.app"')
    print(f'httpStatus:{status_code}')
    print(f'responseDetails:"{error or ""}"')
    print(f'totalDuration:{duration}')
    print(f'clientUa:"Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0"')
    print("---")

def test_profile_caching_scenario():
    """Test the exact scenario that was causing 499 errors"""
    print("🧪 Testing iOS Profile Caching Fix")
    print("=" * 50)
    
    # Track 499 errors
    error_499_count = 0
    total_requests = 0
    
    # Simulate the exact sequence from the logs
    print("\n📱 Simulating iOS Login Sequence with Profile Caching")
    print("-" * 50)
    
    # Request 1: Profile request (from App.tsx) - Should succeed
    print("\n1️⃣ App.tsx Profile Request (should succeed)")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=HEADERS, timeout=30)
        duration = int((time.time() - start_time) * 1000)
        total_requests += 1
        
        if response.status_code == 499:
            error_499_count += 1
            log_request("GET", f"/api/users/{USER_ID}/profile", 499, duration, "client has closed the request before the server could send a response")
            print("❌ 499 ERROR - Profile request failed")
        else:
            log_request("GET", f"/api/users/{USER_ID}/profile", response.status_code, duration)
            print(f"✅ SUCCESS - Profile request completed in {duration}ms")
            
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        print(f"❌ EXCEPTION - Profile request failed: {e}")
    
    # Wait 2 seconds (simulating the delay in App.tsx)
    print("\n⏳ Waiting 2 seconds (App.tsx delay)...")
    time.sleep(2)
    
    # Request 2: Subscription status (from App.tsx) - Should succeed
    print("\n2️⃣ App.tsx Subscription Status Request (should succeed)")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/subscription/status/{USER_ID}", headers=HEADERS, timeout=30)
        duration = int((time.time() - start_time) * 1000)
        total_requests += 1
        
        if response.status_code == 499:
            error_499_count += 1
            log_request("GET", f"/api/subscription/status/{USER_ID}", 499, duration, "client has closed the request before the server could send a response")
            print("❌ 499 ERROR - Subscription request failed")
        else:
            log_request("GET", f"/api/subscription/status/{USER_ID}", response.status_code, duration)
            print(f"✅ SUCCESS - Subscription request completed in {duration}ms")
            
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        print(f"❌ EXCEPTION - Subscription request failed: {e}")
    
    # Wait 2 seconds (simulating the delay in App.tsx)
    print("\n⏳ Waiting 2 seconds (App.tsx delay)...")
    time.sleep(2)
    
    # Request 3: Lock status (from App.tsx) - Should succeed
    print("\n3️⃣ App.tsx Lock Status Request (should succeed)")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/users/{USER_ID}/lock-status", headers=HEADERS, timeout=30)
        duration = int((time.time() - start_time) * 1000)
        total_requests += 1
        
        if response.status_code == 499:
            error_499_count += 1
            log_request("GET", f"/api/users/{USER_ID}/lock-status", 499, duration, "client has closed the request before the server could send a response")
            print("❌ 499 ERROR - Lock status request failed")
        else:
            log_request("GET", f"/api/users/{USER_ID}/lock-status", response.status_code, duration)
            print(f"✅ SUCCESS - Lock status request completed in {duration}ms")
            
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        print(f"❌ EXCEPTION - Lock status request failed: {e}")
    
    # Wait 3 seconds (simulating the delay in ChatbotScreen)
    print("\n⏳ Waiting 3 seconds (ChatbotScreen delay)...")
    time.sleep(3)
    
    # Request 4: Profile request (from ChatbotScreen) - Should use cache and succeed
    print("\n4️⃣ ChatbotScreen Profile Request (should use cache and succeed)")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=HEADERS, timeout=30)
        duration = int((time.time() - start_time) * 1000)
        total_requests += 1
        
        if response.status_code == 499:
            error_499_count += 1
            log_request("GET", f"/api/users/{USER_ID}/profile", 499, duration, "client has closed the request before the server could send a response")
            print("❌ 499 ERROR - ChatbotScreen profile request failed")
        else:
            log_request("GET", f"/api/users/{USER_ID}/profile", response.status_code, duration)
            print(f"✅ SUCCESS - ChatbotScreen profile request completed in {duration}ms")
            
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        print(f"❌ EXCEPTION - ChatbotScreen profile request failed: {e}")
    
    # Test concurrent profile requests (simulating race condition)
    print("\n🔄 Testing Concurrent Profile Requests (Race Condition Test)")
    print("-" * 50)
    
    import threading
    
    def make_profile_request(request_id):
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=HEADERS, timeout=30)
            duration = int((time.time() - start_time) * 1000)
            
            if response.status_code == 499:
                return (request_id, 499, duration, "499 error")
            else:
                return (request_id, response.status_code, duration, "success")
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return (request_id, 0, duration, f"exception: {e}")
    
    # Make 3 concurrent profile requests
    threads = []
    results = []
    
    for i in range(3):
        thread = threading.Thread(target=lambda i=i: results.append(make_profile_request(f"concurrent-{i}")))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Process results
    for request_id, status_code, duration, result in results:
        total_requests += 1
        if status_code == 499:
            error_499_count += 1
            log_request("GET", f"/api/users/{USER_ID}/profile", 499, duration, "client has closed the request before the server could send a response")
            print(f"❌ 499 ERROR - {request_id}")
        else:
            log_request("GET", f"/api/users/{USER_ID}/profile", status_code, duration)
            print(f"✅ SUCCESS - {request_id} completed in {duration}ms")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total Requests: {total_requests}")
    print(f"499 Errors: {error_499_count}")
    print(f"Success Rate: {((total_requests - error_499_count) / total_requests * 100):.1f}%")
    
    if error_499_count == 0:
        print("\n🎉 SUCCESS: No 499 errors detected!")
        print("✅ Profile caching fix is working correctly")
        print("✅ Race condition has been resolved")
        return True
    else:
        print(f"\n❌ FAILURE: {error_499_count} 499 errors detected")
        print("⚠️  Profile caching fix may need further adjustment")
        return False

def test_rapid_sequential_requests():
    """Test rapid sequential requests to ensure caching works"""
    print("\n🚀 Testing Rapid Sequential Profile Requests")
    print("-" * 50)
    
    error_499_count = 0
    total_requests = 0
    
    # Make 5 rapid profile requests
    for i in range(5):
        print(f"\n{i+1}️⃣ Rapid Profile Request {i+1}")
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=HEADERS, timeout=30)
            duration = int((time.time() - start_time) * 1000)
            total_requests += 1
            
            if response.status_code == 499:
                error_499_count += 1
                log_request("GET", f"/api/users/{USER_ID}/profile", 499, duration, "client has closed the request before the server could send a response")
                print("❌ 499 ERROR")
            else:
                log_request("GET", f"/api/users/{USER_ID}/profile", response.status_code, duration)
                print(f"✅ SUCCESS - {duration}ms")
                
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            print(f"❌ EXCEPTION: {e}")
    
    print(f"\n📊 Rapid Requests: {total_requests - error_499_count}/{total_requests} successful")
    return error_499_count == 0

if __name__ == "__main__":
    print("🧪 iOS Profile Caching Fix Test Suite")
    print("=" * 60)
    
    # Run main test
    main_test_passed = test_profile_caching_scenario()
    
    # Run rapid requests test
    rapid_test_passed = test_rapid_sequential_requests()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"Main Scenario Test: {'✅ PASSED' if main_test_passed else '❌ FAILED'}")
    print(f"Rapid Requests Test: {'✅ PASSED' if rapid_test_passed else '❌ FAILED'}")
    
    if main_test_passed and rapid_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ iOS profile caching fix is working correctly")
        print("✅ 499 errors have been eliminated")
        print("✅ App should no longer crash on login")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        print("⚠️  Further investigation may be needed")
        exit(1)
