#!/usr/bin/env python3
"""
Debug script to identify the specific issue with user profile endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "https://nutricious4u-production.up.railway.app/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def test_different_user_ids():
    """Test with different user IDs to see if the issue is specific to one user"""
    print_section("Testing Different User IDs")
    
    headers = {
        'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
        'X-Platform': 'ios',
        'X-App-Version': '1.0.0'
    }
    
    # Test with different user IDs
    test_users = [
        "test_user_123",
        "EMoXb6rFuwN3xKsotq54K0kVArf1",  # Original failing user
        "another_test_user",
        "user_with_special_chars_@#$%",
    ]
    
    for user_id in test_users:
        try:
            print(f"\nTesting user ID: {user_id}")
            response = requests.get(f"{API_BASE_URL}/users/{user_id}/profile", headers=headers, timeout=30)
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 500:
                print(f"  Error: {response.text}")
            elif response.status_code == 404:
                print(f"  Result: User not found (expected)")
            elif response.status_code == 200:
                print(f"  Result: User found")
            else:
                print(f"  Result: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  Error: {e}")

def test_firebase_collections():
    """Test if other Firebase collections are working"""
    print_section("Testing Firebase Collections")
    
    headers = {
        'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
        'X-Platform': 'ios',
        'X-App-Version': '1.0.0'
    }
    
    # Test different endpoints that use Firebase
    endpoints = [
        ("Workout Search", f"{API_BASE_URL}/workout/search?query=running"),
        ("Food Search", f"{API_BASE_URL}/food/search?query=apple"),
        ("Food Log Summary", f"{API_BASE_URL}/food/log/summary/{TEST_USER_ID}"),
        ("Workout Log Summary", f"{API_BASE_URL}/workout/log/summary/{TEST_USER_ID}"),
    ]
    
    for name, url in endpoints:
        try:
            print(f"\nTesting {name}: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            if response.status_code != 200:
                print(f"  Error: {response.text[:100]}...")
            else:
                print(f"  Success: {len(response.text)} characters")
                
        except Exception as e:
            print(f"  Error: {e}")

def test_timeout_handling():
    """Test if the timeout handling is causing issues"""
    print_section("Testing Timeout Handling")
    
    headers = {
        'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
        'X-Platform': 'ios',
        'X-App-Version': '1.0.0'
    }
    
    try:
        # Test with a very short timeout to see if timeout handling works
        print("Testing with 5 second timeout...")
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:100]}...")
        
    except requests.exceptions.Timeout:
        print("✅ Timeout handling works - request timed out as expected")
    except Exception as e:
        print(f"Error: {e}")

def test_middleware_headers():
    """Test if the middleware is working correctly"""
    print_section("Testing Middleware Headers")
    
    headers = {
        'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
        'X-Platform': 'ios',
        'X-App-Version': '1.0.0'
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", headers=headers, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"X-Platform header: {response.headers.get('X-Platform')}")
        print(f"X-Response-Time header: {response.headers.get('X-Response-Time')}")
        print(f"All headers: {dict(response.headers)}")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run all debug tests"""
    print_header("User Profile Endpoint Debug")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Primary Test User ID: {TEST_USER_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Different User IDs", test_different_user_ids),
        ("Firebase Collections", test_firebase_collections),
        ("Timeout Handling", test_timeout_handling),
        ("Middleware Headers", test_middleware_headers),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print_header("Debug Complete")
    print("Check the results above to identify the specific issue.")

if __name__ == "__main__":
    main()
