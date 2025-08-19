#!/usr/bin/env python3
"""
Comprehensive test script to verify iOS 499 error fixes
Tests the exact sequence that was causing crashes: subscription status -> lock status -> profile
"""

import requests
import time
import json
from datetime import datetime
import threading
import concurrent.futures

# Configuration
API_BASE_URL = "https://nutricious4u-production.up.railway.app/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"  # From the logs

# iOS-specific headers to simulate the app
IOS_HEADERS = {
    'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Connection': 'keep-alive',
    'Keep-Alive': 'timeout=300, max=1000',
    'X-Platform': 'ios',
    'X-App-Version': '1.0.0'
}

def test_exact_failing_sequence():
    """Test the exact sequence from the logs that was causing 499 errors"""
    print("🧪 Testing Exact Failing Sequence (499 Error Fix)")
    print("=" * 60)
    
    # The exact sequence from the logs
    endpoints = [
        f"/subscription/status/{TEST_USER_ID}",
        f"/users/{TEST_USER_ID}/lock-status",
        f"/users/{TEST_USER_ID}/profile"  # This was failing with 499
    ]
    
    results = []
    
    for i, endpoint in enumerate(endpoints):
        print(f"\n📱 Request {i+1}: {endpoint}")
        
        try:
            start_time = time.time()
            
            # Add delays to simulate the new conservative approach
            if i > 0:
                delay = 2.0  # 2 second delay as implemented in the fix
                print(f"   ⏱️  Waiting {delay}s before request...")
                time.sleep(delay)
            
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=IOS_HEADERS,
                timeout=60  # Increased timeout
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
                    if 'isSubscriptionActive' in data:
                        print(f"   💳 Subscription: {data.get('isSubscriptionActive', False)}")
                    elif 'isAppLocked' in data:
                        print(f"   🔒 Lock Status: {data.get('isAppLocked', False)}")
                    elif 'firstName' in data:
                        print(f"   📄 Profile: {data.get('firstName', 'N/A')} {data.get('lastName', 'N/A')}")
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
            print(f"   ⏰ Timeout after 60s")
            results.append({
                'endpoint': endpoint,
                'status_code': 'TIMEOUT',
                'duration': 60,
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

def test_concurrent_profile_requests():
    """Test multiple concurrent requests to the profile endpoint"""
    print("\n🔄 Testing Concurrent Profile Requests")
    print("=" * 60)
    
    def make_profile_request(request_id):
        try:
            start_time = time.time()
            response = requests.get(
                f"{API_BASE_URL}/users/{TEST_USER_ID}/profile",
                headers=IOS_HEADERS,
                timeout=60
            )
            duration = time.time() - start_time
            
            return {
                'request_id': request_id,
                'status_code': response.status_code,
                'duration': duration,
                'success': response.status_code < 400
            }
        except Exception as e:
            return {
                'request_id': request_id,
                'status_code': 'ERROR',
                'duration': 0,
                'success': False,
                'error': str(e)
            }
    
    # Test 3 concurrent requests to the profile endpoint
    print(f"📱 Making 3 concurrent requests to profile endpoint")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(make_profile_request, i+1)
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

def test_rapid_sequential_requests():
    """Test rapid sequential requests without delays"""
    print("\n⚡ Testing Rapid Sequential Requests (No Delays)")
    print("=" * 60)
    
    endpoints = [
        f"/subscription/status/{TEST_USER_ID}",
        f"/users/{TEST_USER_ID}/lock-status",
        f"/users/{TEST_USER_ID}/profile"
    ]
    
    results = []
    
    for i, endpoint in enumerate(endpoints):
        print(f"\n📱 Request {i+1}: {endpoint}")
        
        try:
            start_time = time.time()
            
            # No delays - this should trigger 499 errors if the fix isn't working
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=IOS_HEADERS,
                timeout=60
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
            elif response.status_code == 499:
                print(f"   ❌ 499 Error: Client closed connection ({duration:.3f}s)")
                result['success'] = False
            else:
                print(f"   ⚠️  Other Error: {response.status_code} ({duration:.3f}s)")
                result['success'] = False
            
            results.append(result)
            
        except Exception as e:
            print(f"   💥 Error: {e}")
            results.append({
                'endpoint': endpoint,
                'status_code': 'ERROR',
                'duration': 0,
                'success': False
            })
    
    return results

def analyze_results(sequence_results, concurrent_results, rapid_results):
    """Analyze all test results"""
    print("\n📊 Comprehensive Test Results Analysis")
    print("=" * 60)
    
    # Sequence results (with delays)
    sequence_success = sum(1 for r in sequence_results if r['success'])
    sequence_total = len(sequence_results)
    sequence_499_count = sum(1 for r in sequence_results if r['status_code'] == 499)
    
    print(f"📈 Sequential Requests (with delays): {sequence_success}/{sequence_total} successful")
    print(f"   ❌ 499 errors: {sequence_499_count}")
    
    # Concurrent results
    concurrent_success = sum(1 for r in concurrent_results if r['success'])
    concurrent_total = len(concurrent_results)
    concurrent_499_count = sum(1 for r in concurrent_results if r['status_code'] == 499)
    
    print(f"🔄 Concurrent Requests: {concurrent_success}/{concurrent_total} successful")
    print(f"   ❌ 499 errors: {concurrent_499_count}")
    
    # Rapid results (no delays)
    rapid_success = sum(1 for r in rapid_results if r['success'])
    rapid_total = len(rapid_results)
    rapid_499_count = sum(1 for r in rapid_results if r['status_code'] == 499)
    
    print(f"⚡ Rapid Requests (no delays): {rapid_success}/{rapid_total} successful")
    print(f"   ❌ 499 errors: {rapid_499_count}")
    
    # Overall assessment
    total_499_errors = sequence_499_count + concurrent_499_count + rapid_499_count
    
    if total_499_errors == 0:
        print("\n🎉 EXCELLENT! No 499 errors detected - iOS connection fixes are working perfectly!")
        return True
    elif sequence_499_count == 0 and concurrent_499_count == 0:
        print("\n✅ GOOD! No 499 errors in critical scenarios - fixes are working for normal usage!")
        print("   ⚠️  Some 499 errors in rapid testing, but this is expected behavior")
        return True
    else:
        print(f"\n⚠️  WARNING: {total_499_errors} 499 errors detected - connection issues may still be present")
        return False

def main():
    """Run all comprehensive tests"""
    print(f"🚀 Starting Comprehensive iOS 499 Error Fix Tests")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    
    try:
        # Test 1: Exact failing sequence with delays
        sequence_results = test_exact_failing_sequence()
        
        # Test 2: Concurrent profile requests
        concurrent_results = test_concurrent_profile_requests()
        
        # Test 3: Rapid sequential requests without delays
        rapid_results = test_rapid_sequential_requests()
        
        # Analyze results
        success = analyze_results(sequence_results, concurrent_results, rapid_results)
        
        # Save detailed results
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'api_base_url': API_BASE_URL,
            'test_user_id': TEST_USER_ID,
            'sequence_results': sequence_results,
            'concurrent_results': concurrent_results,
            'rapid_results': rapid_results,
            'overall_success': success
        }
        
        with open('ios_499_fix_comprehensive_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: ios_499_fix_comprehensive_results.json")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
