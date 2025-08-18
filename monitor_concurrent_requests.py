#!/usr/bin/env python3
"""
Concurrent API Request Monitor
Monitors the number of simultaneous API requests during login sequence
"""

import requests
import time
import threading
import concurrent.futures
from datetime import datetime
from collections import defaultdict
import json
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConcurrentRequestMonitor:
    """Monitors concurrent API requests during login sequence"""
    
    def __init__(self, backend_url: str = "https://nutricious4u-production.up.railway.app"):
        self.backend_url = backend_url
        self.api_base = f"{backend_url}/api"
        self.session = requests.Session()
        
        # iOS-specific headers
        self.ios_headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=75, max=1000',
        }
        
        # Monitoring data
        self.request_timeline = []
        self.concurrent_requests = defaultdict(int)
        self.request_details = []
        self.max_concurrent = 0
        self.peak_times = []
        
        # Test user
        self.test_user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
        
    def log_request(self, endpoint: str, start_time: float, end_time: float, status_code: int, success: bool):
        """Log a request for monitoring"""
        duration = end_time - start_time
        
        # Add to timeline
        self.request_timeline.append({
            'endpoint': endpoint,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'status_code': status_code,
            'success': success
        })
        
        # Add to request details
        self.request_details.append({
            'endpoint': endpoint,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'status_code': status_code,
            'success': success
        })
        
        logger.info(f"📡 {endpoint}: {status_code} ({duration:.3f}s)")
    
    def calculate_concurrent_requests(self):
        """Calculate concurrent requests at each point in time"""
        if not self.request_timeline:
            return
        
        # Create time points for all start and end times
        time_points = []
        for req in self.request_timeline:
            time_points.append((req['start_time'], 1, req['endpoint']))  # Request started
            time_points.append((req['end_time'], -1, req['endpoint']))   # Request ended
        
        # Sort by time
        time_points.sort(key=lambda x: x[0])
        
        # Calculate concurrent requests
        current_concurrent = 0
        for timestamp, change, endpoint in time_points:
            current_concurrent += change
            self.concurrent_requests[timestamp] = current_concurrent
            
            if current_concurrent > self.max_concurrent:
                self.max_concurrent = current_concurrent
                self.peak_times.append({
                    'timestamp': timestamp,
                    'concurrent_count': current_concurrent,
                    'endpoint': endpoint
                })
    
    def simulate_login_sequence(self) -> Dict[str, Any]:
        """Simulate the exact iOS login sequence with monitoring"""
        logger.info("🔐 Simulating iOS Login Sequence with Concurrent Request Monitoring")
        logger.info("=" * 80)
        
        # Clear previous data
        self.request_timeline = []
        self.concurrent_requests = defaultdict(int)
        self.request_details = []
        self.max_concurrent = 0
        self.peak_times = []
        
        # Define the login sequence endpoints (in order)
        login_sequence = [
            f"/users/{self.test_user_id}/lock-status",
            f"/users/{self.test_user_id}/diet", 
            f"/food/log/summary/{self.test_user_id}",
            f"/users/{self.test_user_id}/profile",
            f"/subscription/status/{self.test_user_id}",
            f"/user/{self.test_user_id}/reset-daily",
            f"/users/{self.test_user_id}/lock-status"  # Second lock check
        ]
        
        results = {
            'total_requests': len(login_sequence),
            'successful_requests': 0,
            'failed_requests': 0,
            'max_concurrent': 0,
            'peak_times': [],
            'request_timeline': [],
            'concurrent_analysis': {},
            'ios_compatibility': {}
        }
        
        def make_request(endpoint: str, delay: float = 0) -> Dict[str, Any]:
            """Make a single request with monitoring"""
            if delay > 0:
                time.sleep(delay)
            
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{self.api_base}{endpoint}",
                    headers=self.ios_headers,
                    timeout=15
                )
                end_time = time.time()
                
                success = response.status_code == 200
                self.log_request(endpoint, start_time, end_time, response.status_code, success)
                
                return {
                    'endpoint': endpoint,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'status_code': response.status_code,
                    'success': success,
                    'error': None
                }
            except Exception as e:
                end_time = time.time()
                self.log_request(endpoint, start_time, end_time, 'ERROR', False)
                return {
                    'endpoint': endpoint,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'status_code': 'ERROR',
                    'success': False,
                    'error': str(e)
                }
        
        # Simulate sequential login sequence (like the mobile app)
        logger.info("📱 Step 1: Sequential Login Sequence (Mobile App Behavior)")
        logger.info("-" * 60)
        
        sequential_results = []
        for i, endpoint in enumerate(login_sequence):
            # Add delays like in the mobile app
            if i == 0:  # First request
                delay = 0
            elif i == 1:  # After lock status
                delay = 1.0  # 1 second delay
            elif i == 2:  # After diet
                delay = 0.8  # 800ms delay
            elif i == 3:  # After food log
                delay = 0.8  # 800ms delay
            elif i == 4:  # After profile
                delay = 1.0  # 1 second delay
            elif i == 5:  # After subscription
                delay = 0.8  # 800ms delay
            else:
                delay = 0.8  # 800ms delay
            
            result = make_request(endpoint, delay)
            sequential_results.append(result)
            
            if result['success']:
                results['successful_requests'] += 1
            else:
                results['failed_requests'] += 1
        
        # Calculate concurrent requests
        self.calculate_concurrent_requests()
        
        # Analyze results
        results['max_concurrent'] = self.max_concurrent
        results['peak_times'] = self.peak_times
        results['request_timeline'] = self.request_timeline
        
        # Concurrent analysis
        concurrent_counts = list(self.concurrent_requests.values())
        results['concurrent_analysis'] = {
            'max_concurrent': max(concurrent_counts) if concurrent_counts else 0,
            'avg_concurrent': sum(concurrent_counts) / len(concurrent_counts) if concurrent_counts else 0,
            'min_concurrent': min(concurrent_counts) if concurrent_counts else 0,
            'total_time': max(self.concurrent_requests.keys()) - min(self.concurrent_requests.keys()) if self.concurrent_requests else 0
        }
        
        # iOS compatibility assessment
        max_concurrent = results['concurrent_analysis']['max_concurrent']
        results['ios_compatibility'] = {
            'max_concurrent_requests': max_concurrent,
            'is_safe_for_ios': max_concurrent <= 3,  # iOS can handle 3 concurrent requests safely
            'recommendation': self.get_ios_recommendation(max_concurrent),
            'risk_level': self.get_risk_level(max_concurrent)
        }
        
        return results
    
    def simulate_concurrent_login_sequence(self) -> Dict[str, Any]:
        """Simulate concurrent login sequence (worst case scenario)"""
        logger.info("🔄 Simulating Concurrent Login Sequence (Worst Case)")
        logger.info("-" * 60)
        
        # Clear previous data
        self.request_timeline = []
        self.concurrent_requests = defaultdict(int)
        self.request_details = []
        self.max_concurrent = 0
        self.peak_times = []
        
        # Define endpoints that might be called concurrently
        concurrent_endpoints = [
            f"/users/{self.test_user_id}/lock-status",
            f"/users/{self.test_user_id}/diet",
            f"/food/log/summary/{self.test_user_id}",
            f"/users/{self.test_user_id}/profile",
            f"/subscription/status/{self.test_user_id}",
            f"/test-deployment",
            f"/test-firebase"
        ]
        
        results = {
            'total_requests': len(concurrent_endpoints),
            'successful_requests': 0,
            'failed_requests': 0,
            'max_concurrent': 0,
            'peak_times': [],
            'request_timeline': [],
            'concurrent_analysis': {},
            'ios_compatibility': {}
        }
        
        def make_concurrent_request(endpoint: str) -> Dict[str, Any]:
            """Make a request for concurrent testing"""
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{self.api_base}{endpoint}",
                    headers=self.ios_headers,
                    timeout=15
                )
                end_time = time.time()
                
                success = response.status_code == 200
                self.log_request(endpoint, start_time, end_time, response.status_code, success)
                
                return {
                    'endpoint': endpoint,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'status_code': response.status_code,
                    'success': success,
                    'error': None
                }
            except Exception as e:
                end_time = time.time()
                self.log_request(endpoint, start_time, end_time, 'ERROR', False)
                return {
                    'endpoint': endpoint,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'status_code': 'ERROR',
                    'success': False,
                    'error': str(e)
                }
        
        # Make all requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_endpoint = {executor.submit(make_concurrent_request, endpoint): endpoint for endpoint in concurrent_endpoints}
            
            for future in concurrent.futures.as_completed(future_to_endpoint):
                result = future.result()
                if result['success']:
                    results['successful_requests'] += 1
                else:
                    results['failed_requests'] += 1
        
        # Calculate concurrent requests
        self.calculate_concurrent_requests()
        
        # Analyze results
        results['max_concurrent'] = self.max_concurrent
        results['peak_times'] = self.peak_times
        results['request_timeline'] = self.request_timeline
        
        # Concurrent analysis
        concurrent_counts = list(self.concurrent_requests.values())
        results['concurrent_analysis'] = {
            'max_concurrent': max(concurrent_counts) if concurrent_counts else 0,
            'avg_concurrent': sum(concurrent_counts) / len(concurrent_counts) if concurrent_counts else 0,
            'min_concurrent': min(concurrent_counts) if concurrent_counts else 0,
            'total_time': max(self.concurrent_requests.keys()) - min(self.concurrent_requests.keys()) if self.concurrent_requests else 0
        }
        
        # iOS compatibility assessment
        max_concurrent = results['concurrent_analysis']['max_concurrent']
        results['ios_compatibility'] = {
            'max_concurrent_requests': max_concurrent,
            'is_safe_for_ios': max_concurrent <= 3,
            'recommendation': self.get_ios_recommendation(max_concurrent),
            'risk_level': self.get_risk_level(max_concurrent)
        }
        
        return results
    
    def get_ios_recommendation(self, max_concurrent: int) -> str:
        """Get recommendation based on concurrent request count"""
        if max_concurrent <= 2:
            return "✅ Excellent - iOS can handle this easily"
        elif max_concurrent <= 3:
            return "✅ Good - iOS should handle this well"
        elif max_concurrent <= 5:
            return "⚠️  Moderate - May cause occasional issues on iOS"
        elif max_concurrent <= 8:
            return "❌ High - Likely to cause iOS connection issues"
        else:
            return "🚨 Critical - Will definitely cause iOS crashes"
    
    def get_risk_level(self, max_concurrent: int) -> str:
        """Get risk level based on concurrent request count"""
        if max_concurrent <= 2:
            return "LOW"
        elif max_concurrent <= 3:
            return "MEDIUM"
        elif max_concurrent <= 5:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def print_detailed_analysis(self, results: Dict[str, Any], test_name: str):
        """Print detailed analysis of the results"""
        print(f"\n📊 DETAILED ANALYSIS: {test_name}")
        print("=" * 80)
        
        # Request summary
        print(f"📈 Request Summary:")
        print(f"   Total Requests: {results['total_requests']}")
        print(f"   Successful: {results['successful_requests']}")
        print(f"   Failed: {results['failed_requests']}")
        print(f"   Success Rate: {(results['successful_requests'] / results['total_requests'] * 100):.1f}%")
        
        # Concurrent analysis
        concurrent_analysis = results['concurrent_analysis']
        print(f"\n🔄 Concurrent Request Analysis:")
        print(f"   Maximum Concurrent: {concurrent_analysis['max_concurrent']}")
        print(f"   Average Concurrent: {concurrent_analysis['avg_concurrent']:.2f}")
        print(f"   Minimum Concurrent: {concurrent_analysis['min_concurrent']}")
        print(f"   Total Time: {concurrent_analysis['total_time']:.2f}s")
        
        # iOS compatibility
        ios_compat = results['ios_compatibility']
        print(f"\n📱 iOS Compatibility Assessment:")
        print(f"   Max Concurrent Requests: {ios_compat['max_concurrent_requests']}")
        print(f"   Safe for iOS: {'✅ YES' if ios_compat['is_safe_for_ios'] else '❌ NO'}")
        print(f"   Risk Level: {ios_compat['risk_level']}")
        print(f"   Recommendation: {ios_compat['recommendation']}")
        
        # Peak times
        if results['peak_times']:
            print(f"\n⏰ Peak Concurrent Times:")
            for peak in results['peak_times'][:3]:  # Show top 3 peaks
                print(f"   {peak['timestamp']:.2f}s: {peak['concurrent_count']} requests ({peak['endpoint']})")
        
        # Request timeline
        print(f"\n📋 Request Timeline:")
        for req in results['request_timeline']:
            status = "✅" if req['success'] else "❌"
            print(f"   {status} {req['start_time']:.2f}s - {req['end_time']:.2f}s: {req['endpoint']} ({req['duration']:.3f}s)")

def run_concurrent_monitoring():
    """Run the concurrent request monitoring"""
    print("🔍 Concurrent API Request Monitor")
    print(f"📅 Started at: {datetime.now().isoformat()}")
    print("=" * 80)
    
    monitor = ConcurrentRequestMonitor()
    
    # Test 1: Sequential Login Sequence (Mobile App Behavior)
    print("\n🔐 TEST 1: Sequential Login Sequence (Mobile App Behavior)")
    print("-" * 60)
    sequential_results = monitor.simulate_login_sequence()
    monitor.print_detailed_analysis(sequential_results, "Sequential Login")
    
    # Test 2: Concurrent Login Sequence (Worst Case)
    print("\n🔄 TEST 2: Concurrent Login Sequence (Worst Case)")
    print("-" * 60)
    concurrent_results = monitor.simulate_concurrent_login_sequence()
    monitor.print_detailed_analysis(concurrent_results, "Concurrent Login")
    
    # Overall assessment
    print("\n" + "=" * 80)
    print("🎯 OVERALL ASSESSMENT")
    print("=" * 80)
    
    sequential_safe = sequential_results['ios_compatibility']['is_safe_for_ios']
    concurrent_safe = concurrent_results['ios_compatibility']['is_safe_for_ios']
    
    print(f"📱 Sequential Login (Mobile App): {'✅ SAFE' if sequential_safe else '❌ UNSAFE'}")
    print(f"   Max Concurrent: {sequential_results['ios_compatibility']['max_concurrent_requests']}")
    print(f"   Risk Level: {sequential_results['ios_compatibility']['risk_level']}")
    
    print(f"\n🔄 Concurrent Login (Worst Case): {'✅ SAFE' if concurrent_safe else '❌ UNSAFE'}")
    print(f"   Max Concurrent: {concurrent_results['ios_compatibility']['max_concurrent_requests']}")
    print(f"   Risk Level: {concurrent_results['ios_compatibility']['risk_level']}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if sequential_safe and concurrent_safe:
        print("   ✅ Both scenarios are safe for iOS")
        print("   ✅ No additional fixes needed")
        print("   ✅ Ready for iOS deployment")
    elif sequential_safe and not concurrent_safe:
        print("   ✅ Sequential login is safe")
        print("   ⚠️  Concurrent requests may cause issues")
        print("   🔧 Consider implementing request queuing")
    elif not sequential_safe:
        print("   ❌ Sequential login has too many concurrent requests")
        print("   🔧 Need to implement request delays")
        print("   🔧 Consider request deduplication")
        print("   🔧 Implement proper request queuing")
    
    # Specific recommendations based on results
    if sequential_results['ios_compatibility']['max_concurrent_requests'] > 3:
        print(f"\n🔧 SPECIFIC FIXES NEEDED:")
        print(f"   - Increase delays between API calls")
        print(f"   - Implement request deduplication")
        print(f"   - Add request queuing mechanism")
        print(f"   - Consider batching API calls")
    
    return sequential_safe and concurrent_safe

if __name__ == "__main__":
    success = run_concurrent_monitoring()
    exit(0 if success else 1)
