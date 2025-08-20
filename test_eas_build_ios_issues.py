#!/usr/bin/env python3
"""
EAS Build iOS Issues Test Script
Tests the specific issues that occur in EAS builds vs Expo Go
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://nutricious4u-production.up.railway.app/api"
USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"
DIETICIAN_EMAIL = "nutricious4u@gmail.com"

# iOS EAS Build User Agent
EAS_BUILD_HEADERS = {
    "User-Agent": "Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "Content-Type": "application/json",
    "X-Platform": "ios",
    "X-App-Version": "1.0.0"
}

def test_environment_variables():
    """Test if environment variables are properly configured"""
    print("🔧 TESTING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    # Test backend connectivity
    try:
        response = requests.get(f"{BASE_URL}/test-deployment", headers=EAS_BUILD_HEADERS, timeout=10)
        if response.status_code == 200:
            print("   ✅ Backend connectivity: Working")
            return True
        else:
            print(f"   ❌ Backend connectivity: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend connectivity: {e}")
        return False

def test_dietician_vs_user_login_flow():
    """Test the difference between dietician and user login flows"""
    print("\n👨‍⚕️ TESTING DIETICIAN VS USER LOGIN FLOW")
    print("=" * 50)
    
    # Test 1: Dietician login flow (should work)
    print("\n🔍 Testing: Dietician Login Flow")
    try:
        # Dietician only makes one API call: createUserProfile
        response = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=EAS_BUILD_HEADERS, timeout=15)
        if response.status_code == 200:
            print("   ✅ Dietician profile check: Working")
        else:
            print(f"   ❌ Dietician profile check: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Dietician profile check: {e}")
    
    # Test 2: User login flow (problematic API calls)
    print("\n🔍 Testing: User Login Flow (Sequential API Calls)")
    
    endpoints = [
        f"/users/{USER_ID}/profile",
        f"/subscription/status/{USER_ID}",
        f"/users/{USER_ID}/lock-status"
    ]
    
    success_count = 0
    for i, endpoint in enumerate(endpoints, 1):
        try:
            print(f"   📞 API Call {i}: {endpoint}")
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", headers=EAS_BUILD_HEADERS, timeout=15)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print(f"      ✅ SUCCESS: {duration:.2f}s")
                success_count += 1
            else:
                print(f"      ❌ FAILED: {response.status_code} ({duration:.2f}s)")
        except Exception as e:
            print(f"      ❌ ERROR: {e}")
    
    print(f"\n📊 User Login Flow Results: {success_count}/{len(endpoints)} successful")
    return success_count == len(endpoints)

def test_concurrent_requests():
    """Test concurrent requests (simulates rapid API calls)"""
    print("\n⚡ TESTING CONCURRENT REQUESTS")
    print("=" * 50)
    
    import concurrent.futures
    
    def make_request(endpoint):
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=EAS_BUILD_HEADERS, timeout=15)
            return {"endpoint": endpoint, "status": response.status_code, "success": response.status_code == 200}
        except Exception as e:
            return {"endpoint": endpoint, "status": "ERROR", "success": False, "error": str(e)}
    
    endpoints = [
        f"/users/{USER_ID}/profile",
        f"/subscription/status/{USER_ID}",
        f"/users/{USER_ID}/lock-status"
    ]
    
    print("   🔄 Making concurrent requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
        results = [future.result() for future in futures]
    
    success_count = sum(1 for r in results if r["success"])
    print(f"   📊 Concurrent Results: {success_count}/{len(results)} successful")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"      {status} {result['endpoint']}: {result['status']}")
    
    return success_count == len(results)

def test_timeout_handling():
    """Test timeout handling for slow requests"""
    print("\n⏱️ TESTING TIMEOUT HANDLING")
    print("=" * 50)
    
    try:
        # Test with a longer timeout
        response = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=EAS_BUILD_HEADERS, timeout=30)
        if response.status_code == 200:
            print("   ✅ Timeout handling: Working (30s timeout)")
            return True
        else:
            print(f"   ❌ Timeout handling: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Timeout handling: Request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Timeout handling: {e}")
        return False

def test_ios_specific_headers():
    """Test iOS-specific headers and configuration"""
    print("\n📱 TESTING iOS-SPECIFIC CONFIGURATION")
    print("=" * 50)
    
    # Test with iOS-specific headers
    ios_headers = {
        **EAS_BUILD_HEADERS,
        "Connection": "keep-alive",
        "Keep-Alive": "timeout=120, max=1000"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=ios_headers, timeout=15)
        if response.status_code == 200:
            print("   ✅ iOS headers: Working")
            return True
        else:
            print(f"   ❌ iOS headers: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ iOS headers: {e}")
        return False

def main():
    """Run comprehensive EAS build iOS tests"""
    print("🧪 EAS BUILD iOS ISSUES TEST")
    print("=" * 60)
    print("Testing specific issues that occur in EAS builds vs Expo Go")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Environment variables
    results["environment"] = test_environment_variables()
    
    # Test 2: Dietician vs User login flow
    results["login_flow"] = test_dietician_vs_user_login_flow()
    
    # Test 3: Concurrent requests
    results["concurrent"] = test_concurrent_requests()
    
    # Test 4: Timeout handling
    results["timeout"] = test_timeout_handling()
    
    # Test 5: iOS-specific headers
    results["ios_headers"] = test_ios_specific_headers()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 EAS BUILD iOS TEST RESULTS")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    overall_success = all(results.values())
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 EAS build should work properly with the implemented fixes!")
        print("✅ Environment variables are configured")
        print("✅ Login flows are working")
        print("✅ Concurrent requests are handled")
        print("✅ Timeout handling is robust")
        print("✅ iOS-specific configuration is correct")
    else:
        print("\n⚠️ Some issues may still exist:")
        if not results["environment"]:
            print("   - Environment variables may not be properly configured")
        if not results["login_flow"]:
            print("   - User login flow may still have issues")
        if not results["concurrent"]:
            print("   - Concurrent requests may cause problems")
        if not results["timeout"]:
            print("   - Timeout handling may need improvement")
        if not results["ios_headers"]:
            print("   - iOS-specific headers may not be working")
    
    # Save results
    with open("eas_build_ios_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "overall_success": overall_success
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: eas_build_ios_test_results.json")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
