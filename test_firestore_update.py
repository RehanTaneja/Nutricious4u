#!/usr/bin/env python3
"""
Firestore Update Test

This script tests if Firestore updates are working properly
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "https://nutricious4u-production.up.railway.app/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_icon = "✅" if status else "❌"
    print(f"[{timestamp}] {status_icon} {test_name}: {details}")

def test_current_profile():
    """Test current profile state"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            log_test("Current Profile", True, f"Diet: {profile_data.get('dietPdfUrl')}, Cache: {profile_data.get('dietCacheVersion')}")
            return profile_data
        else:
            log_test("Current Profile", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("Current Profile", False, f"Error: {str(e)}")
        return None

def test_direct_profile_update():
    """Test direct profile update"""
    try:
        # Create test data
        test_cache_version = time.time()
        test_data = {
            "dietCacheVersion": test_cache_version,
            "testField": f"test_value_{int(time.time())}"
        }
        
        # Try to update profile directly
        response = requests.patch(
            f"{API_BASE_URL}/users/{TEST_USER_ID}/profile",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            log_test("Direct Profile Update", True, f"Update successful: {result}")
            return test_cache_version
        else:
            log_test("Direct Profile Update", False, f"Status: {response.status_code}, Response: {response.text}")
            return None
            
    except Exception as e:
        log_test("Direct Profile Update", False, f"Error: {str(e)}")
        return None

def test_profile_after_update():
    """Test profile after update"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            log_test("Profile After Update", True, f"Diet: {profile_data.get('dietPdfUrl')}, Cache: {profile_data.get('dietCacheVersion')}, Test: {profile_data.get('testField')}")
            return profile_data
        else:
            log_test("Profile After Update", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("Profile After Update", False, f"Error: {str(e)}")
        return None

def main():
    """Run Firestore update test"""
    print("=" * 80)
    print("FIRESTORE UPDATE TEST")
    print("=" * 80)
    print()
    
    print("🔍 STEP 1: Testing current profile")
    print("-" * 50)
    
    # Test current profile
    current_profile = test_current_profile()
    
    print()
    print("📤 STEP 2: Testing direct profile update")
    print("-" * 50)
    
    # Test direct update
    test_cache_version = test_direct_profile_update()
    
    if test_cache_version:
        print()
        print("🔄 STEP 3: Testing profile after update")
        print("-" * 50)
        
        # Test profile after update
        updated_profile = test_profile_after_update()
        
        print()
        print("=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        if updated_profile:
            cache_version = updated_profile.get("dietCacheVersion")
            test_field = updated_profile.get("testField")
            
            if cache_version == test_cache_version:
                print("✅ Cache version updated correctly")
            else:
                print(f"❌ Cache version not updated. Expected: {test_cache_version}, Got: {cache_version}")
            
            if test_field:
                print("✅ Test field updated correctly")
            else:
                print("❌ Test field not updated")
        else:
            print("❌ Could not get updated profile")
    
    else:
        print("❌ Direct profile update failed")

if __name__ == "__main__":
    main()
