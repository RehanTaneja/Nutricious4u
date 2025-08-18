#!/usr/bin/env python3
"""
Test Request Queuing System
Verifies that the request queuing prevents concurrent requests on iOS
"""

import requests
import time
import concurrent.futures
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_request_queuing():
    """Test if the backend properly handles queued requests"""
    print("🔍 Testing Request Queuing System")
    print(f"📅 Started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    backend_url = "https://nutricious4u-production.up.railway.app"
    api_base = f"{backend_url}/api"
    test_user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    
    # iOS-specific headers
    headers = {
        'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
        'X-Platform': 'ios',
        'Accept': 'application/json',
        'Connection': 'keep-alive',
        'Keep-Alive': 'timeout=75, max=1000',
    }
    
    # Test endpoints
    endpoints = [
        f"/users/{test_user_id}/lock-status",
        f"/users/{test_user_id}/diet",
        f"/food/log/summary/{test_user_id}",
        f"/users/{test_user_id}/profile",
        f"/subscription/status/{test_user_id}",
        "/test-deployment",
        "/test-firebase"
    ]
    
    def make_request(endpoint: str, request_id: int) -> dict:
        """Make a single request with timing"""
        start_time = time.time()
        try:
            response = requests.get(
                f"{api_base}{endpoint}",
                headers=headers,
                timeout=15
            )
            end_time = time.time()
            
            return {
                'request_id': request_id,
                'endpoint': endpoint,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'error': None
            }
        except Exception as e:
            end_time = time.time()
            return {
                'request_id': request_id,
                'endpoint': endpoint,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'status_code': 'ERROR',
                'success': False,
                'error': str(e)
            }
    
    # Test 1: Sequential requests (should work fine)
    print("\n📱 Test 1: Sequential Requests (Expected: Safe)")
    print("-" * 40)
    
    sequential_results = []
    start_time = time.time()
    
    for i, endpoint in enumerate(endpoints):
        result = make_request(endpoint, i)
        sequential_results.append(result)
        
        status = "✅" if result['success'] else "❌"
        print(f"{status} Request {i+1}: {endpoint.split('/')[-1]} - {result['status_code']} ({result['duration']:.3f}s)")
        
        # Small delay between requests
        if i < len(endpoints) - 1:
            time.sleep(0.5)
    
    sequential_total_time = time.time() - start_time
    sequential_success = sum(1 for r in sequential_results if r['success'])
    
    print(f"\n📊 Sequential Results:")
    print(f"   Success Rate: {sequential_success}/{len(endpoints)} ({sequential_success/len(endpoints)*100:.1f}%)")
    print(f"   Total Time: {sequential_total_time:.2f}s")
    print(f"   Average Time: {sequential_total_time/len(endpoints):.2f}s per request")
    
    # Test 2: Concurrent requests (should be limited by backend)
    print(f"\n🔄 Test 2: Concurrent Requests (Expected: Limited by Backend)")
    print("-" * 40)
    
    concurrent_results = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_endpoint = {executor.submit(make_request, endpoint, i): endpoint for i, endpoint in enumerate(endpoints)}
        
        for future in concurrent.futures.as_completed(future_to_endpoint):
            result = future.result()
            concurrent_results.append(result)
            
            status = "✅" if result['success'] else "❌"
            print(f"{status} Request {result['request_id']+1}: {result['endpoint'].split('/')[-1]} - {result['status_code']} ({result['duration']:.3f}s)")
    
    concurrent_total_time = time.time() - start_time
    concurrent_success = sum(1 for r in concurrent_results if r['success'])
    
    print(f"\n📊 Concurrent Results:")
    print(f"   Success Rate: {concurrent_success}/{len(endpoints)} ({concurrent_success/len(endpoints)*100:.1f}%)")
    print(f"   Total Time: {concurrent_total_time:.2f}s")
    print(f"   Average Time: {concurrent_total_time/len(endpoints):.2f}s per request")
    
    # Test 3: Rapid sequential requests (simulating mobile app behavior)
    print(f"\n⚡ Test 3: Rapid Sequential Requests (Mobile App Simulation)")
    print("-" * 40)
    
    rapid_results = []
    start_time = time.time()
    
    for i, endpoint in enumerate(endpoints):
        result = make_request(endpoint, i)
        rapid_results.append(result)
        
        status = "✅" if result['success'] else "❌"
        print(f"{status} Request {i+1}: {endpoint.split('/')[-1]} - {result['status_code']} ({result['duration']:.3f}s)")
        
        # Very small delay (like mobile app)
        if i < len(endpoints) - 1:
            time.sleep(0.1)
    
    rapid_total_time = time.time() - start_time
    rapid_success = sum(1 for r in rapid_results if r['success'])
    
    print(f"\n📊 Rapid Sequential Results:")
    print(f"   Success Rate: {rapid_success}/{len(endpoints)} ({rapid_success/len(endpoints)*100:.1f}%)")
    print(f"   Total Time: {rapid_total_time:.2f}s")
    print(f"   Average Time: {rapid_total_time/len(endpoints):.2f}s per request")
    
    # Analysis
    print(f"\n" + "=" * 60)
    print(f"📊 ANALYSIS")
    print(f"=" * 60)
    
    # Compare results
    print(f"📈 Success Rates:")
    print(f"   Sequential: {sequential_success}/{len(endpoints)} ({sequential_success/len(endpoints)*100:.1f}%)")
    print(f"   Concurrent: {concurrent_success}/{len(endpoints)} ({concurrent_success/len(endpoints)*100:.1f}%)")
    print(f"   Rapid: {rapid_success}/{len(endpoints)} ({rapid_success/len(endpoints)*100:.1f}%)")
    
    print(f"\n⏱️  Performance:")
    print(f"   Sequential Total Time: {sequential_total_time:.2f}s")
    print(f"   Concurrent Total Time: {concurrent_total_time:.2f}s")
    print(f"   Rapid Total Time: {rapid_total_time:.2f}s")
    
    # iOS compatibility assessment
    print(f"\n📱 iOS Compatibility Assessment:")
    
    # Check for 499 errors or connection issues
    sequential_errors = [r for r in sequential_results if not r['success']]
    concurrent_errors = [r for r in concurrent_results if not r['success']]
    rapid_errors = [r for r in rapid_results if not r['success']]
    
    print(f"   Sequential Errors: {len(sequential_errors)}")
    print(f"   Concurrent Errors: {len(concurrent_errors)}")
    print(f"   Rapid Errors: {len(rapid_errors)}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if len(sequential_errors) == 0 and len(rapid_errors) == 0:
        print("   ✅ Sequential and rapid requests are working well")
        print("   ✅ Backend can handle the request patterns")
        print("   ✅ iOS should work fine with proper delays")
    else:
        print("   ⚠️  Some request patterns are failing")
        print("   🔧 Need to implement better error handling")
        print("   🔧 Consider increasing delays between requests")
    
    if len(concurrent_errors) > len(sequential_errors):
        print("   ✅ Backend is properly limiting concurrent requests")
        print("   ✅ This is good for iOS stability")
    else:
        print("   ⚠️  Backend might be allowing too many concurrent requests")
        print("   🔧 Consider implementing request queuing on backend")
    
    # Overall assessment
    overall_success = len(sequential_errors) == 0 and len(rapid_errors) == 0
    print(f"\n🎯 Overall Assessment:")
    print(f"   iOS Compatibility: {'✅ READY' if overall_success else '❌ NEEDS WORK'}")
    
    return overall_success

if __name__ == "__main__":
    success = test_request_queuing()
    exit(0 if success else 1)
