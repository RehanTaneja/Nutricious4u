#!/usr/bin/env python3
"""
Quick iOS Test - Fast validation of iOS fixes
Run this frequently during development to catch issues early
"""

import requests
import time
from datetime import datetime

def quick_ios_test():
    """Quick test of iOS-critical endpoints"""
    print("⚡ Quick iOS Test")
    print(f"📅 {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 40)
    
    backend_url = "https://nutricious4u-production.up.railway.app"
    api_base = f"{backend_url}/api"
    test_user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    
    # iOS headers
    headers = {
        'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
        'X-Platform': 'ios',
        'Accept': 'application/json',
        'Connection': 'keep-alive'
    }
    
    # Test endpoints that were failing with 499
    endpoints = [
        f"/users/{test_user_id}/diet",
        f"/food/log/summary/{test_user_id}",
        f"/users/{test_user_id}/profile"
    ]
    
    session = requests.Session()
    results = []
    
    for endpoint in endpoints:
        try:
            start_time = time.time()
            response = session.get(f"{api_base}{endpoint}", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint.split('/')[-1]}: {response.status_code} ({response_time:.2f}s)")
            
            results.append({
                'endpoint': endpoint.split('/')[-1],
                'success': response.status_code == 200,
                'time': response_time
            })
            
        except requests.exceptions.Timeout:
            print(f"❌ {endpoint.split('/')[-1]}: TIMEOUT")
            results.append({
                'endpoint': endpoint.split('/')[-1],
                'success': False,
                'time': 10.0
            })
        except Exception as e:
            print(f"❌ {endpoint.split('/')[-1]}: ERROR - {str(e)[:30]}")
            results.append({
                'endpoint': endpoint.split('/')[-1],
                'success': False,
                'time': 0.0
            })
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    avg_time = sum(r['time'] for r in results) / len(results) if results else 0
    
    print("-" * 40)
    print(f"📊 {successful}/{total} endpoints working")
    print(f"⏱️  Avg response time: {avg_time:.2f}s")
    
    if successful == total:
        print("🎉 All good! Ready for iOS build.")
    else:
        print("⚠️  Issues detected. Check before building.")
    
    return successful == total

if __name__ == "__main__":
    quick_ios_test()
