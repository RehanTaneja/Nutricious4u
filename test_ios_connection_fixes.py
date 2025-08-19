#!/usr/bin/env python3
"""
Test script to verify iOS connection fixes
Tests the API endpoints that were causing 499 errors during login
"""

import requests
import time
import json
from datetime import datetime

# Configuration
API_BASE_URL = "https://nutricious4u-production.up.railway.app/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"  # From the logs

# iOS-specific headers to simulate the app
IOS_HEADERS = {
    'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Connection': 'keep-alive',
    'Keep-Alive': 'timeout=120, max=1000',
    'X-Platform': 'ios',
    'X-App-Version': '1.0.0'
}

def test_sequential_requests():
    """Test the exact sequence from the logs with proper delays"""
    print("🧪 Testing iOS Connection Fixes")
    print("=" * 50)
    
    endpoints = [
        f"/users/{TEST_USER_ID}/profile",
        f"/users/{TEST_USER_ID}/lock-status", 
        f"/subscription/status/{TEST_USER_ID}",
        f"/users/{TEST_USER_ID}/profile"  # Duplicate to test 499 prevention
    ]
    
    results = []
    
    for i, endpoint in enumerate(endpoints):
        print(f"\n📱 Request {i+1}: {endpoint}")
        
        try:
            start_time = time.time()
            
            # Add delay between requests to simulate the fix
            if i > 0:
                delay = 1.5 if i == 1 else 1.2  # Match the delays in App.tsx
                print(f"   ⏱️  Waiting {delay}s before request...")
                time.sleep(delay)
            
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=IOS_HEADERS,
                timeout=45  # Increased timeout
            )
            
            duration = time.time() - start_time
            
            result = {
                'endpoint': endpoint,
                'status_code': response.status_code,
                'duration': duration,
                'success': response.status_code < 400
            }
            
            if response.status_code == 200:
                print(f"   ✅ Success: {response.status_code} ({duration:.3f}s)")
                try:
                    data = response.json()
                    if 'firstName' in data:
                        print(f"   📄 Profile: {data.get('firstName', 'N/A')} {data.get('lastName', 'N/A')}")
                    elif 'isAppLocked' in data:
                        print(f"   🔒 Lock Status: {data.get('isAppLocked', False)}")
                    elif 'isSubscriptionActive' in data:
                        print(f"   💳 Subscription: {data.get('isSubscriptionActive', False)}")
                except:
                    pass
            elif response.status_code == 499:
                print(f"   ❌ 499 Error: Client closed connection ({duration:.3f}s)")
                result['success'] = False
            else:
                print(f"   ⚠️  Other Error: {response.status_code} ({duration:.3f}s)")
                result['success'] = False
            
            results.append(result)
            
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout after 45s")
            results.append({
                'endpoint': endpoint,
                'status_code': 'TIMEOUT',
                'duration': 45,
                'success': False
            })
        except requests.exceptions.ConnectionError as e:
            print(f"   🔌 Connection Error: {e}")
            results.append({
                'endpoint': endpoint,
                'status_code': 'CONNECTION_ERROR',
                'duration': 0,
                'success': False
            })
        except Exception as e:
            print(f"   💥 Unexpected Error: {e}")
            results.append({
                'endpoint': endpoint,
                'status_code': 'ERROR',
                'duration': 0,
                'success': False
            })
    
    return results

def test_concurrent_requests():
    """Test concurrent requests to ensure the queue system works"""
    print("\n🔄 Testing Concurrent Request Handling")
    print("=" * 50)
    
    import threading
    import concurrent.futures
    
    def make_request(endpoint, request_id):
        try:
            start_time = time.time()
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=IOS_HEADERS,
                timeout=45
            )
            duration = time.time() - start_time
            
            return {
                'request_id': request_id,
                'endpoint': endpoint,
                'status_code': response.status_code,
                'duration': duration,
                'success': response.status_code < 400
            }
        except Exception as e:
            return {
                'request_id': request_id,
                'endpoint': endpoint,
                'status_code': 'ERROR',
                'duration': 0,
                'success': False,
                'error': str(e)
            }
    
    # Test concurrent requests to the same endpoint
    endpoint = f"/users/{TEST_USER_ID}/profile"
    
    print(f"📱 Making 3 concurrent requests to: {endpoint}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(make_request, endpoint, i+1)
            for i in range(3)
        ]
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            
            if result['success']:
                print(f"   ✅ Request {result['request_id']}: Success ({result['duration']:.3f}s)")
            else:
                print(f"   ❌ Request {result['request_id']}: Failed - {result['status_code']}")
    
    return results

def analyze_results(sequential_results, concurrent_results):
    """Analyze the test results"""
    print("\n📊 Test Results Analysis")
    print("=" * 50)
    
    # Sequential results
    sequential_success = sum(1 for r in sequential_results if r['success'])
    sequential_total = len(sequential_results)
    
    print(f"📈 Sequential Requests: {sequential_success}/{sequential_total} successful")
    
    # Check for 499 errors
    status_codes = [r['status_code'] for r in sequential_results]
    has_499 = 499 in status_codes
    
    if has_499:
        print("   ❌ 499 errors detected - connection issues still present")
    else:
        print("   ✅ No 499 errors - connection fixes working")
    
    # Concurrent results
    concurrent_success = sum(1 for r in concurrent_results if r['success'])
    concurrent_total = len(concurrent_results)
    
    print(f"🔄 Concurrent Requests: {concurrent_success}/{concurrent_total} successful")
    
    # Overall assessment
    if sequential_success == sequential_total and concurrent_success == concurrent_total and not has_499:
        print("\n🎉 All tests passed! iOS connection fixes are working properly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Connection issues may still be present.")
        return False

def main():
    """Run all tests"""
    print(f"🚀 Starting iOS Connection Fix Tests")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    
    try:
        # Test sequential requests (like login sequence)
        sequential_results = test_sequential_requests()
        
        # Test concurrent requests
        concurrent_results = test_concurrent_requests()
        
        # Analyze results
        success = analyze_results(sequential_results, concurrent_results)
        
        # Save detailed results
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'api_base_url': API_BASE_URL,
            'test_user_id': TEST_USER_ID,
            'sequential_results': sequential_results,
            'concurrent_results': concurrent_results,
            'overall_success': success
        }
        
        with open('ios_connection_test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: ios_connection_test_results.json")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
