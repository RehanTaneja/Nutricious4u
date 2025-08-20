#!/usr/bin/env python3
"""
iOS Recipe and Login Fixes Test Script
Tests the specific fixes for iOS recipe loading and login sequence issues
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://nutricious4u-production.up.railway.app/api"
USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"

# iOS EAS Build User Agent
EAS_BUILD_HEADERS = {
    "User-Agent": "Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "Content-Type": "application/json",
    "X-Platform": "ios",
    "X-App-Version": "1.0.0",
    "Connection": "keep-alive",
    "Keep-Alive": "timeout=300, max=1000"
}

def test_recipe_endpoint():
    """Test the new recipe endpoint"""
    print("🍳 TESTING RECIPE ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/recipes", headers=EAS_BUILD_HEADERS, timeout=30)
        
        if response.status_code == 200:
            recipes = response.json().get('recipes', [])
            print(f"   ✅ Recipe endpoint: Working ({len(recipes)} recipes found)")
            return True
        else:
            print(f"   ❌ Recipe endpoint: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Recipe endpoint: {e}")
        return False

def test_login_sequence_with_delays():
    """Test the login sequence with proper delays to simulate iOS behavior"""
    print("\n🔐 TESTING LOGIN SEQUENCE WITH DELAYS")
    print("=" * 50)
    
    endpoints = [
        f"/users/{USER_ID}/profile",
        f"/subscription/status/{USER_ID}",
        f"/users/{USER_ID}/diet"
    ]
    
    success_count = 0
    for i, endpoint in enumerate(endpoints, 1):
        try:
            print(f"   📞 API Call {i}: {endpoint}")
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", headers=EAS_BUILD_HEADERS, timeout=45)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print(f"      ✅ SUCCESS: {duration:.2f}s")
                success_count += 1
            elif response.status_code == 499:
                print(f"      ❌ 499 ERROR: Client closed connection ({duration:.2f}s)")
            else:
                print(f"      ❌ FAILED: {response.status_code} ({duration:.2f}s)")
            
            # Add delay between requests to simulate iOS queue behavior
            if i < len(endpoints):
                delay = 2.5  # 2.5 second delay between requests
                print(f"      ⏳ Waiting {delay}s before next request...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"      ❌ ERROR: {e}")
    
    print(f"\n📊 Login Sequence Results: {success_count}/{len(endpoints)} successful")
    return success_count == len(endpoints)

def test_concurrent_recipe_requests():
    """Test concurrent recipe requests to ensure queue system works"""
    print("\n⚡ TESTING CONCURRENT RECIPE REQUESTS")
    print("=" * 50)
    
    import concurrent.futures
    
    def make_recipe_request(request_id):
        try:
            response = requests.get(f"{BASE_URL}/recipes", headers=EAS_BUILD_HEADERS, timeout=30)
            return {
                "request_id": request_id,
                "status": response.status_code,
                "success": response.status_code == 200,
                "recipes_count": len(response.json().get('recipes', [])) if response.status_code == 200 else 0
            }
        except Exception as e:
            return {
                "request_id": request_id,
                "status": "ERROR",
                "success": False,
                "error": str(e)
            }
    
    print("   🔄 Making 3 concurrent recipe requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_recipe_request, i) for i in range(1, 4)]
        results = [future.result() for future in futures]
    
    success_count = sum(1 for r in results if r["success"])
    print(f"   📊 Concurrent Recipe Results: {success_count}/{len(results)} successful")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        if result["success"]:
            print(f"      {status} Request {result['request_id']}: {result['recipes_count']} recipes")
        else:
            print(f"      {status} Request {result['request_id']}: {result['status']}")
    
    return success_count == len(results)

def test_ios_specific_headers():
    """Test iOS-specific headers and configuration"""
    print("\n📱 TESTING iOS-SPECIFIC HEADERS")
    print("=" * 50)
    
    # Test with enhanced iOS headers
    enhanced_headers = {
        **EAS_BUILD_HEADERS,
        "Connection": "keep-alive",
        "Keep-Alive": "timeout=300, max=1000",
        "X-Platform": "ios",
        "X-App-Version": "1.0.0"
    }
    
    try:
        # Test recipe endpoint with enhanced headers
        response = requests.get(f"{BASE_URL}/recipes", headers=enhanced_headers, timeout=30)
        
        if response.status_code == 200:
            print("   ✅ iOS headers with recipes: Working")
            
            # Test profile endpoint with enhanced headers
            response2 = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=enhanced_headers, timeout=30)
            
            if response2.status_code == 200:
                print("   ✅ iOS headers with profile: Working")
                return True
            else:
                print(f"   ❌ iOS headers with profile: {response2.status_code}")
                return False
        else:
            print(f"   ❌ iOS headers with recipes: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ iOS headers: {e}")
        return False

def test_timeout_handling():
    """Test timeout handling for slow requests"""
    print("\n⏱️ TESTING TIMEOUT HANDLING")
    print("=" * 50)
    
    try:
        # Test with a longer timeout (45 seconds for iOS)
        response = requests.get(f"{BASE_URL}/recipes", headers=EAS_BUILD_HEADERS, timeout=45)
        
        if response.status_code == 200:
            print("   ✅ Timeout handling: Working (45s timeout)")
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

def main():
    """Run comprehensive iOS recipe and login fixes test"""
    print("🧪 iOS RECIPE AND LOGIN FIXES TEST")
    print("=" * 60)
    print("Testing fixes for iOS recipe loading and login sequence issues")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Recipe endpoint
    results["recipe_endpoint"] = test_recipe_endpoint()
    
    # Test 2: Login sequence with delays
    results["login_sequence"] = test_login_sequence_with_delays()
    
    # Test 3: Concurrent recipe requests
    results["concurrent_recipes"] = test_concurrent_recipe_requests()
    
    # Test 4: iOS-specific headers
    results["ios_headers"] = test_ios_specific_headers()
    
    # Test 5: Timeout handling
    results["timeout"] = test_timeout_handling()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 iOS RECIPE AND LOGIN FIXES TEST RESULTS")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    overall_success = all(results.values())
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 iOS fixes should work properly!")
        print("✅ Recipe endpoint is working")
        print("✅ Login sequence handles delays properly")
        print("✅ Concurrent requests are managed")
        print("✅ iOS-specific headers are configured")
        print("✅ Timeout handling is robust")
    else:
        print("\n⚠️ Some issues may still exist:")
        if not results["recipe_endpoint"]:
            print("   - Recipe endpoint may not be working")
        if not results["login_sequence"]:
            print("   - Login sequence may still have timing issues")
        if not results["concurrent_recipes"]:
            print("   - Concurrent requests may cause problems")
        if not results["ios_headers"]:
            print("   - iOS-specific headers may not be working")
        if not results["timeout"]:
            print("   - Timeout handling may need improvement")
    
    # Save results
    with open("ios_recipe_login_fixes_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "overall_success": overall_success,
            "test_description": "iOS Recipe and Login Fixes Test"
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: ios_recipe_login_fixes_results.json")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
