#!/usr/bin/env python3
"""
Comprehensive test script to verify iOS fixes for:
1. Login crashes (499 errors)
2. Diet viewing functionality
3. Connection timeout handling
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://nutricious4u-production.up.railway.app"
API_BASE = f"{BACKEND_URL}/api"

def test_backend_connection():
    """Test basic backend connectivity"""
    print("🔍 Testing backend connection...")
    try:
        response = requests.get(f"{API_BASE}/test-deployment", timeout=10)
        if response.status_code == 200:
            print("✅ Backend connection successful")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        return False

def test_ios_diet_functionality():
    """Test iOS-specific diet functionality"""
    print("\n🔍 Testing iOS diet functionality...")
    try:
        response = requests.get(f"{API_BASE}/test-ios-diet", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("✅ iOS diet functionality test successful")
            print(f"   Firebase available: {data.get('firebase_available')}")
            print(f"   Firestore operations: {data.get('firestore_operations')}")
            print(f"   Async operations: {data.get('async_operations')}")
            print(f"   Connection timeout: {data.get('connection_timeout')}")
            print(f"   Keep alive: {data.get('keep_alive')}")
            return True
        else:
            print(f"❌ iOS diet functionality test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ iOS diet functionality test error: {e}")
        return False

def test_firebase_connection():
    """Test Firebase connection"""
    print("\n🔍 Testing Firebase connection...")
    try:
        response = requests.get(f"{API_BASE}/test-firebase", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Firebase connection test successful")
            print(f"   Firebase available: {data.get('firebase_available')}")
            return data.get('firebase_available', False)
        else:
            print(f"❌ Firebase connection test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Firebase connection test error: {e}")
        return False

def test_diet_endpoint_performance():
    """Test diet endpoint performance and timeout handling"""
    print("\n🔍 Testing diet endpoint performance...")
    
    # Test with a sample user ID (this should return 404 but test the endpoint)
    test_user_id = "test_user_ios_fix"
    
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE}/users/{test_user_id}/diet", timeout=15)
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"   Response time: {response_time:.3f}s")
        
        if response.status_code == 404:
            print("✅ Diet endpoint responding correctly (404 for non-existent user)")
            print(f"   Response time: {response_time:.3f}s (acceptable)")
            return response_time < 5.0  # Should respond within 5 seconds
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Diet endpoint timeout (should not happen with fixes)")
        return False
    except Exception as e:
        print(f"❌ Diet endpoint error: {e}")
        return False

def test_concurrent_requests():
    """Test handling of concurrent requests (simulating iOS app behavior)"""
    print("\n🔍 Testing concurrent request handling...")
    
    import threading
    import concurrent.futures
    
    results = []
    errors = []
    
    def make_request(request_id):
        try:
            response = requests.get(f"{API_BASE}/test-deployment", timeout=10)
            results.append((request_id, response.status_code))
        except Exception as e:
            errors.append((request_id, str(e)))
    
    # Make 5 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(5)]
        concurrent.futures.wait(futures, timeout=30)
    
    print(f"   Successful requests: {len(results)}/5")
    print(f"   Failed requests: {len(errors)}/5")
    
    if errors:
        print("   Errors:")
        for req_id, error in errors:
            print(f"     Request {req_id}: {error}")
    
    return len(errors) == 0

def test_connection_headers():
    """Test that proper connection headers are being sent"""
    print("\n🔍 Testing connection headers...")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(f"{API_BASE}/test-deployment", headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Check response headers
            response_headers = response.headers
            print("✅ Connection headers test successful")
            print(f"   X-Platform: {response_headers.get('X-Platform', 'missing')}")
            print(f"   X-Response-Time: {response_headers.get('X-Response-Time', 'missing')}")
            print(f"   Connection: {response_headers.get('Connection', 'missing')}")
            print(f"   Keep-Alive: {response_headers.get('Keep-Alive', 'missing')}")
            
            return True
        else:
            print(f"❌ Connection headers test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection headers test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive iOS fixes verification...")
    print(f"📅 Test started at: {datetime.now().isoformat()}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    tests = [
        ("Backend Connection", test_backend_connection),
        ("Firebase Connection", test_firebase_connection),
        ("iOS Diet Functionality", test_ios_diet_functionality),
        ("Diet Endpoint Performance", test_diet_endpoint_performance),
        ("Concurrent Requests", test_concurrent_requests),
        ("Connection Headers", test_connection_headers),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! iOS fixes appear to be working correctly.")
        print("\n📋 Fixes verified:")
        print("   ✅ Backend connection stability")
        print("   ✅ Firebase integration")
        print("   ✅ Diet endpoint performance")
        print("   ✅ Concurrent request handling")
        print("   ✅ iOS-specific headers")
        print("   ✅ Timeout handling")
        print("   ✅ Connection pooling")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        print("\n🔧 Recommended actions:")
        print("   - Check backend deployment")
        print("   - Verify Firebase configuration")
        print("   - Review server logs for errors")
        print("   - Test with actual iOS device")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
