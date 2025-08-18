#!/usr/bin/env python3
"""
iOS Build Behavior Simulation Test
Mimics iOS app behavior to test fixes without EAS builds
"""

import requests
import time
import json
import threading
import concurrent.futures
import random
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IOSSimulator:
    """Simulates iOS app behavior and network conditions"""
    
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
            'X-App-Version': '1.0.0',
            'X-Request-ID': ''
        }
        
        # Simulate iOS network conditions
        self.network_conditions = {
            'slow_network': False,
            'intermittent_connection': False,
            'high_latency': False,
            'packet_loss': False
        }
        
        # Test user data
        self.test_user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"  # From the logs
        
    def simulate_network_conditions(self, condition: str):
        """Simulate different network conditions"""
        if condition == 'slow_network':
            time.sleep(random.uniform(2, 5))
        elif condition == 'high_latency':
            time.sleep(random.uniform(1, 3))
        elif condition == 'intermittent_connection':
            if random.random() < 0.1:  # 10% chance of connection failure
                raise requests.exceptions.ConnectionError("Simulated connection failure")
    
    def simulate_ios_login_sequence(self) -> Dict[str, Any]:
        """Simulate the exact iOS login sequence that was failing"""
        logger.info("🔐 Simulating iOS login sequence...")
        
        results = {
            'lock_status': None,
            'diet': None,
            'food_log_summary': None,
            'profile': None,
            'errors': []
        }
        
        try:
            # Step 1: Check lock status (this was working in logs)
            logger.info("   📱 Step 1: Checking lock status...")
            start_time = time.time()
            response = self.session.get(
                f"{self.api_base}/users/{self.test_user_id}/lock-status",
                headers=self.ios_headers,
                timeout=10
            )
            results['lock_status'] = {
                'status_code': response.status_code,
                'response_time': time.time() - start_time,
                'success': response.status_code == 200
            }
            logger.info(f"   ✅ Lock status: {response.status_code} ({results['lock_status']['response_time']:.3f}s)")
            
            # Simulate iOS app behavior - small delay between requests
            time.sleep(0.5)
            
            # Step 2: Get diet (this was failing with 499)
            logger.info("   📱 Step 2: Getting diet...")
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{self.api_base}/users/{self.test_user_id}/diet",
                    headers=self.ios_headers,
                    timeout=15
                )
                results['diet'] = {
                    'status_code': response.status_code,
                    'response_time': time.time() - start_time,
                    'success': response.status_code == 200,
                    'data': response.json() if response.status_code == 200 else None
                }
                logger.info(f"   ✅ Diet: {response.status_code} ({results['diet']['response_time']:.3f}s)")
            except requests.exceptions.Timeout:
                results['diet'] = {
                    'status_code': 'TIMEOUT',
                    'response_time': time.time() - start_time,
                    'success': False,
                    'error': 'Request timeout'
                }
                results['errors'].append('Diet request timeout')
                logger.error("   ❌ Diet request timed out")
            except Exception as e:
                results['diet'] = {
                    'status_code': 'ERROR',
                    'response_time': time.time() - start_time,
                    'success': False,
                    'error': str(e)
                }
                results['errors'].append(f'Diet request error: {str(e)}')
                logger.error(f"   ❌ Diet request error: {e}")
            
            # Step 3: Get food log summary (this was failing with 499)
            logger.info("   📱 Step 3: Getting food log summary...")
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{self.api_base}/food/log/summary/{self.test_user_id}",
                    headers=self.ios_headers,
                    timeout=15
                )
                results['food_log_summary'] = {
                    'status_code': response.status_code,
                    'response_time': time.time() - start_time,
                    'success': response.status_code == 200,
                    'data': response.json() if response.status_code == 200 else None
                }
                logger.info(f"   ✅ Food log summary: {response.status_code} ({results['food_log_summary']['response_time']:.3f}s)")
            except requests.exceptions.Timeout:
                results['food_log_summary'] = {
                    'status_code': 'TIMEOUT',
                    'response_time': time.time() - start_time,
                    'success': False,
                    'error': 'Request timeout'
                }
                results['errors'].append('Food log summary timeout')
                logger.error("   ❌ Food log summary timed out")
            except Exception as e:
                results['food_log_summary'] = {
                    'status_code': 'ERROR',
                    'response_time': time.time() - start_time,
                    'success': False,
                    'error': str(e)
                }
                results['errors'].append(f'Food log summary error: {str(e)}')
                logger.error(f"   ❌ Food log summary error: {e}")
            
            # Step 4: Get user profile (this was failing with 499)
            logger.info("   📱 Step 4: Getting user profile...")
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{self.api_base}/users/{self.test_user_id}/profile",
                    headers=self.ios_headers,
                    timeout=15
                )
                results['profile'] = {
                    'status_code': response.status_code,
                    'response_time': time.time() - start_time,
                    'success': response.status_code == 200,
                    'data': response.json() if response.status_code == 200 else None
                }
                logger.info(f"   ✅ Profile: {response.status_code} ({results['profile']['response_time']:.3f}s)")
            except requests.exceptions.Timeout:
                results['profile'] = {
                    'status_code': 'TIMEOUT',
                    'response_time': time.time() - start_time,
                    'success': False,
                    'error': 'Request timeout'
                }
                results['errors'].append('Profile request timeout')
                logger.error("   ❌ Profile request timed out")
            except Exception as e:
                results['profile'] = {
                    'status_code': 'ERROR',
                    'response_time': time.time() - start_time,
                    'success': False,
                    'error': str(e)
                }
                results['errors'].append(f'Profile request error: {str(e)}')
                logger.error(f"   ❌ Profile request error: {e}")
                
        except Exception as e:
            logger.error(f"❌ iOS login sequence failed: {e}")
            results['errors'].append(f'Login sequence error: {str(e)}')
        
        return results
    
    def simulate_concurrent_requests(self) -> Dict[str, Any]:
        """Simulate concurrent requests like iOS app startup"""
        logger.info("🔄 Simulating concurrent requests (iOS app startup)...")
        
        endpoints = [
            f"/users/{self.test_user_id}/lock-status",
            f"/users/{self.test_user_id}/diet",
            f"/food/log/summary/{self.test_user_id}",
            f"/users/{self.test_user_id}/profile",
            "/test-deployment",
            "/test-firebase"
        ]
        
        results = {
            'total_requests': len(endpoints),
            'successful_requests': 0,
            'failed_requests': 0,
            'timeout_requests': 0,
            'response_times': [],
            'errors': []
        }
        
        def make_request(endpoint: str) -> Dict[str, Any]:
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{self.api_base}{endpoint}",
                    headers=self.ios_headers,
                    timeout=15
                )
                response_time = time.time() - start_time
                return {
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200,
                    'error': None
                }
            except requests.exceptions.Timeout:
                response_time = time.time() - start_time
                return {
                    'endpoint': endpoint,
                    'status_code': 'TIMEOUT',
                    'response_time': response_time,
                    'success': False,
                    'error': 'Request timeout'
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    'endpoint': endpoint,
                    'status_code': 'ERROR',
                    'response_time': response_time,
                    'success': False,
                    'error': str(e)
                }
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_to_endpoint = {executor.submit(make_request, endpoint): endpoint for endpoint in endpoints}
            
            for future in concurrent.futures.as_completed(future_to_endpoint):
                result = future.result()
                results['response_times'].append(result['response_time'])
                
                if result['success']:
                    results['successful_requests'] += 1
                    logger.info(f"   ✅ {result['endpoint']}: {result['status_code']} ({result['response_time']:.3f}s)")
                else:
                    results['failed_requests'] += 1
                    if result['status_code'] == 'TIMEOUT':
                        results['timeout_requests'] += 1
                    results['errors'].append(f"{result['endpoint']}: {result['error']}")
                    logger.error(f"   ❌ {result['endpoint']}: {result['error']}")
        
        return results
    
    def simulate_diet_viewing_sequence(self) -> Dict[str, Any]:
        """Simulate dietician diet viewing sequence"""
        logger.info("📄 Simulating diet viewing sequence...")
        
        results = {
            'diet_endpoint': None,
            'pdf_endpoint': None,
            'errors': []
        }
        
        try:
            # Step 1: Get diet information
            logger.info("   📱 Step 1: Getting diet information...")
            start_time = time.time()
            response = self.session.get(
                f"{self.api_base}/users/{self.test_user_id}/diet",
                headers=self.ios_headers,
                timeout=15
            )
            
            results['diet_endpoint'] = {
                'status_code': response.status_code,
                'response_time': time.time() - start_time,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
            
            if response.status_code == 200:
                diet_data = response.json()
                logger.info(f"   ✅ Diet info: {response.status_code} ({results['diet_endpoint']['response_time']:.3f}s)")
                logger.info(f"   📊 Diet data: hasDiet={diet_data.get('hasDiet')}, daysLeft={diet_data.get('daysLeft')}")
                
                # Step 2: Try to access PDF if available
                if diet_data.get('hasDiet') and diet_data.get('dietPdfUrl'):
                    logger.info("   📱 Step 2: Testing PDF access...")
                    start_time = time.time()
                    try:
                        pdf_response = self.session.get(
                            f"{self.api_base}/users/{self.test_user_id}/diet/pdf",
                            headers=self.ios_headers,
                            timeout=20
                        )
                        results['pdf_endpoint'] = {
                            'status_code': pdf_response.status_code,
                            'response_time': time.time() - start_time,
                            'success': pdf_response.status_code == 200,
                            'content_type': pdf_response.headers.get('content-type'),
                            'content_length': len(pdf_response.content) if pdf_response.status_code == 200 else 0
                        }
                        logger.info(f"   ✅ PDF access: {pdf_response.status_code} ({results['pdf_endpoint']['response_time']:.3f}s)")
                        if pdf_response.status_code == 200:
                            logger.info(f"   📄 PDF size: {len(pdf_response.content)} bytes")
                    except Exception as e:
                        results['pdf_endpoint'] = {
                            'status_code': 'ERROR',
                            'response_time': time.time() - start_time,
                            'success': False,
                            'error': str(e)
                        }
                        results['errors'].append(f'PDF access error: {str(e)}')
                        logger.error(f"   ❌ PDF access error: {e}")
                else:
                    logger.info("   ℹ️  No diet PDF available for testing")
            else:
                logger.error(f"   ❌ Diet info failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Diet viewing sequence failed: {e}")
            results['errors'].append(f'Diet viewing error: {str(e)}')
        
        return results
    
    def simulate_network_stress_test(self) -> Dict[str, Any]:
        """Simulate network stress conditions"""
        logger.info("🌐 Simulating network stress test...")
        
        results = {
            'total_requests': 20,
            'successful_requests': 0,
            'failed_requests': 0,
            'timeout_requests': 0,
            'response_times': [],
            'errors': []
        }
        
        def stress_request(request_id: int) -> Dict[str, Any]:
            start_time = time.time()
            try:
                # Randomly choose an endpoint
                endpoints = [
                    f"/users/{self.test_user_id}/diet",
                    f"/food/log/summary/{self.test_user_id}",
                    f"/users/{self.test_user_id}/profile",
                    "/test-deployment"
                ]
                endpoint = random.choice(endpoints)
                
                # Simulate network conditions
                if random.random() < 0.1:  # 10% chance of slow network
                    time.sleep(random.uniform(1, 3))
                
                response = self.session.get(
                    f"{self.api_base}{endpoint}",
                    headers=self.ios_headers,
                    timeout=20
                )
                response_time = time.time() - start_time
                return {
                    'request_id': request_id,
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code < 500,
                    'error': None
                }
            except requests.exceptions.Timeout:
                response_time = time.time() - start_time
                return {
                    'request_id': request_id,
                    'endpoint': endpoint,
                    'status_code': 'TIMEOUT',
                    'response_time': response_time,
                    'success': False,
                    'error': 'Request timeout'
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    'request_id': request_id,
                    'endpoint': endpoint,
                    'status_code': 'ERROR',
                    'response_time': response_time,
                    'success': False,
                    'error': str(e)
                }
        
        # Make stress test requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(stress_request, i) for i in range(results['total_requests'])]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results['response_times'].append(result['response_time'])
                
                if result['success']:
                    results['successful_requests'] += 1
                else:
                    results['failed_requests'] += 1
                    if result['status_code'] == 'TIMEOUT':
                        results['timeout_requests'] += 1
                    results['errors'].append(f"Request {result['request_id']}: {result['error']}")
        
        return results

def run_comprehensive_test():
    """Run comprehensive iOS simulation test"""
    print("🚀 Starting iOS Build Behavior Simulation Test")
    print(f"📅 Test started at: {datetime.now().isoformat()}")
    print("=" * 80)
    
    simulator = IOSSimulator()
    
    # Test 1: iOS Login Sequence
    print("\n🔐 TEST 1: iOS Login Sequence Simulation")
    print("-" * 50)
    login_results = simulator.simulate_ios_login_sequence()
    
    # Test 2: Concurrent Requests
    print("\n🔄 TEST 2: Concurrent Requests Simulation")
    print("-" * 50)
    concurrent_results = simulator.simulate_concurrent_requests()
    
    # Test 3: Diet Viewing Sequence
    print("\n📄 TEST 3: Diet Viewing Sequence Simulation")
    print("-" * 50)
    diet_results = simulator.simulate_diet_viewing_sequence()
    
    # Test 4: Network Stress Test
    print("\n🌐 TEST 4: Network Stress Test")
    print("-" * 50)
    stress_results = simulator.simulate_network_stress_test()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    # Login Sequence Summary
    print("\n🔐 Login Sequence Results:")
    login_success = all([
        login_results['lock_status']['success'] if login_results['lock_status'] else False,
        login_results['diet']['success'] if login_results['diet'] else False,
        login_results['food_log_summary']['success'] if login_results['food_log_summary'] else False,
        login_results['profile']['success'] if login_results['profile'] else False
    ])
    print(f"   Overall Success: {'✅ PASS' if login_success else '❌ FAIL'}")
    print(f"   Lock Status: {'✅' if login_results['lock_status'] and login_results['lock_status']['success'] else '❌'}")
    print(f"   Diet: {'✅' if login_results['diet'] and login_results['diet']['success'] else '❌'}")
    print(f"   Food Log: {'✅' if login_results['food_log_summary'] and login_results['food_log_summary']['success'] else '❌'}")
    print(f"   Profile: {'✅' if login_results['profile'] and login_results['profile']['success'] else '❌'}")
    
    # Concurrent Requests Summary
    print(f"\n🔄 Concurrent Requests Results:")
    concurrent_success = concurrent_results['successful_requests'] / concurrent_results['total_requests'] >= 0.8
    print(f"   Overall Success: {'✅ PASS' if concurrent_success else '❌ FAIL'}")
    print(f"   Successful: {concurrent_results['successful_requests']}/{concurrent_results['total_requests']}")
    print(f"   Failed: {concurrent_results['failed_requests']}/{concurrent_results['total_requests']}")
    print(f"   Timeouts: {concurrent_results['timeout_requests']}/{concurrent_results['total_requests']}")
    if concurrent_results['response_times']:
        avg_time = sum(concurrent_results['response_times']) / len(concurrent_results['response_times'])
        print(f"   Average Response Time: {avg_time:.3f}s")
    
    # Diet Viewing Summary
    print(f"\n📄 Diet Viewing Results:")
    diet_success = diet_results['diet_endpoint'] and diet_results['diet_endpoint']['success']
    print(f"   Overall Success: {'✅ PASS' if diet_success else '❌ FAIL'}")
    print(f"   Diet Endpoint: {'✅' if diet_results['diet_endpoint'] and diet_results['diet_endpoint']['success'] else '❌'}")
    if diet_results['pdf_endpoint']:
        print(f"   PDF Endpoint: {'✅' if diet_results['pdf_endpoint']['success'] else '❌'}")
    
    # Stress Test Summary
    print(f"\n🌐 Stress Test Results:")
    stress_success = stress_results['successful_requests'] / stress_results['total_requests'] >= 0.7
    print(f"   Overall Success: {'✅ PASS' if stress_success else '❌ FAIL'}")
    print(f"   Successful: {stress_results['successful_requests']}/{stress_results['total_requests']}")
    print(f"   Failed: {stress_results['failed_requests']}/{stress_results['total_requests']}")
    print(f"   Timeouts: {stress_results['timeout_requests']}/{stress_results['total_requests']}")
    if stress_results['response_times']:
        avg_time = sum(stress_results['response_times']) / len(stress_results['response_times'])
        print(f"   Average Response Time: {avg_time:.3f}s")
    
    # Overall Assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    overall_success = login_success and concurrent_success and diet_success and stress_success
    print(f"   iOS Build Compatibility: {'✅ READY' if overall_success else '❌ NEEDS WORK'}")
    
    if overall_success:
        print("\n🎉 All tests passed! The fixes should work well in iOS builds.")
        print("   ✅ Login sequence stable")
        print("   ✅ Concurrent requests handled")
        print("   ✅ Diet viewing functional")
        print("   ✅ Network stress handled")
    else:
        print("\n⚠️  Some tests failed. Review the issues above before EAS build.")
        print("   🔧 Recommended actions:")
        if not login_success:
            print("   - Check backend timeout settings")
            print("   - Verify connection handling")
        if not concurrent_success:
            print("   - Review concurrent request handling")
            print("   - Check server concurrency limits")
        if not diet_success:
            print("   - Verify diet endpoint functionality")
            print("   - Check PDF serving configuration")
        if not stress_success:
            print("   - Review stress handling")
            print("   - Check server performance under load")
    
    return overall_success

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
