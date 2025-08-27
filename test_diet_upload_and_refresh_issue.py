#!/usr/bin/env python3
"""
Diet Upload and Refresh Issue Test

This script tests the complete diet upload and refresh flow to identify why:
1. New diet is not visible after upload for users with existing diet
2. Notification extraction still uses old diet
3. Cache busting is not working properly
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "https://nutricious4u-production.up.railway.app/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"
TEST_DIETICIAN_ID = "dietician_test_456"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_icon = "✅" if status else "❌"
    print(f"[{timestamp}] {status_icon} {test_name}: {details}")

def test_user_diet_before_upload():
    """Test user's diet data before upload"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet", timeout=10)
        
        if response.status_code == 200:
            diet_data = response.json()
            log_test("User Diet Before Upload", True, f"Current diet: {diet_data.get('dietPdfUrl')}, Days left: {diet_data.get('daysLeft')}")
            return diet_data
        elif response.status_code == 404:
            log_test("User Diet Before Upload", True, "No diet found (expected)")
            return None
        else:
            log_test("User Diet Before Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("User Diet Before Upload", False, f"Error: {str(e)}")
        return None

def test_user_notifications_before_upload():
    """Test user's notifications before upload"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications", timeout=10)
        
        if response.status_code == 200:
            notifications_data = response.json()
            notification_count = len(notifications_data.get("notifications", []))
            log_test("User Notifications Before Upload", True, f"Found {notification_count} notifications")
            return notifications_data
        else:
            log_test("User Notifications Before Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("User Notifications Before Upload", False, f"Error: {str(e)}")
        return None

def test_user_profile_before_upload():
    """Test user's profile before upload"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            diet_pdf_url = profile_data.get("dietPdfUrl")
            cache_version = profile_data.get("dietCacheVersion")
            log_test("User Profile Before Upload", True, f"Diet PDF: {diet_pdf_url}, Cache version: {cache_version}")
            return profile_data
        else:
            log_test("User Profile Before Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("User Profile Before Upload", False, f"Error: {str(e)}")
        return None

def test_diet_upload_simulation():
    """Simulate diet upload process by directly updating Firestore"""
    try:
        # Create a test PDF filename
        test_filename = f"test_diet_{int(time.time())}.pdf"
        
        # Simulate the upload process by creating a test endpoint call
        # Since we can't actually upload a file, we'll test the notification extraction
        # which is the key part that might be failing
        
        log_test("Diet Upload Simulation", True, f"Simulating upload of: {test_filename}")
        return {"filename": test_filename, "timestamp": time.time()}
            
    except Exception as e:
        log_test("Diet Upload Simulation", False, f"Error: {str(e)}")
        return None

def test_user_diet_after_upload():
    """Test user's diet data after upload"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet", timeout=10)
        
        if response.status_code == 200:
            diet_data = response.json()
            log_test("User Diet After Upload", True, f"Current diet: {diet_data.get('dietPdfUrl')}, Days left: {diet_data.get('daysLeft')}")
            return diet_data
        else:
            log_test("User Diet After Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("User Diet After Upload", False, f"Error: {str(e)}")
        return None

def test_user_profile_after_upload():
    """Test user's profile after upload"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            diet_pdf_url = profile_data.get("dietPdfUrl")
            cache_version = profile_data.get("dietCacheVersion")
            log_test("User Profile After Upload", True, f"Diet PDF: {diet_pdf_url}, Cache version: {cache_version}")
            return profile_data
        else:
            log_test("User Profile After Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("User Profile After Upload", False, f"Error: {str(e)}")
        return None

def test_notification_extraction_after_upload():
    """Test notification extraction after upload"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/extract",
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            notification_count = len(result.get("notifications", []))
            log_test("Notification Extraction After Upload", True, f"Extracted {notification_count} notifications")
            return result
        else:
            log_test("Notification Extraction After Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("Notification Extraction After Upload", False, f"Error: {str(e)}")
        return None

def test_user_notifications_after_upload():
    """Test user's notifications after upload"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications", timeout=10)
        
        if response.status_code == 200:
            notifications_data = response.json()
            notification_count = len(notifications_data.get("notifications", []))
            diet_pdf_url = notifications_data.get("diet_pdf_url")
            log_test("User Notifications After Upload", True, f"Found {notification_count} notifications, PDF: {diet_pdf_url}")
            return notifications_data
        else:
            log_test("User Notifications After Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("User Notifications After Upload", False, f"Error: {str(e)}")
        return None

def test_diet_pdf_url_consistency():
    """Test if diet PDF URL is consistent across all endpoints"""
    try:
        # Get diet from diet endpoint
        diet_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet", timeout=10)
        diet_pdf_url_from_diet = None
        if diet_response.status_code == 200:
            diet_data = diet_response.json()
            diet_pdf_url_from_diet = diet_data.get("dietPdfUrl")
        
        # Get diet from profile endpoint
        profile_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", timeout=10)
        diet_pdf_url_from_profile = None
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            diet_pdf_url_from_profile = profile_data.get("dietPdfUrl")
        
        # Get diet from notifications endpoint
        notifications_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications", timeout=10)
        diet_pdf_url_from_notifications = None
        if notifications_response.status_code == 200:
            notifications_data = notifications_response.json()
            diet_pdf_url_from_notifications = notifications_data.get("diet_pdf_url")
        
        # Check consistency
        urls = [diet_pdf_url_from_diet, diet_pdf_url_from_profile, diet_pdf_url_from_notifications]
        urls = [url for url in urls if url is not None]
        
        if len(set(urls)) == 1:
            log_test("Diet PDF URL Consistency", True, f"All endpoints return same URL: {urls[0]}")
            return True
        else:
            log_test("Diet PDF URL Consistency", False, f"URLs inconsistent: Diet={diet_pdf_url_from_diet}, Profile={diet_pdf_url_from_profile}, Notifications={diet_pdf_url_from_notifications}")
            return False
            
    except Exception as e:
        log_test("Diet PDF URL Consistency", False, f"Error: {str(e)}")
        return False

def test_frontend_refresh_simulation():
    """Simulate frontend refresh behavior"""
    try:
        # Simulate what happens when frontend receives new diet notification
        # 1. Get user diet data
        diet_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet", timeout=10)
        
        if diet_response.status_code == 200:
            diet_data = diet_response.json()
            
            # 2. Check if cache version is recent
            profile_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", timeout=10)
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                cache_version = profile_data.get("dietCacheVersion")
                
                if cache_version:
                    # Check if cache version is recent (within last hour)
                    current_time = time.time()
                    if current_time - cache_version < 3600:  # 1 hour
                        log_test("Frontend Refresh Simulation", True, f"Cache version is recent: {cache_version}")
                        return True
                    else:
                        log_test("Frontend Refresh Simulation", False, f"Cache version is old: {cache_version}")
                        return False
                else:
                    log_test("Frontend Refresh Simulation", False, "No cache version found")
                    return False
            else:
                log_test("Frontend Refresh Simulation", False, "Could not get profile data")
                return False
        else:
            log_test("Frontend Refresh Simulation", False, "Could not get diet data")
            return False
            
    except Exception as e:
        log_test("Frontend Refresh Simulation", False, f"Error: {str(e)}")
        return False

def main():
    """Run comprehensive diet upload and refresh tests"""
    print("=" * 80)
    print("DIET UPLOAD AND REFRESH ISSUE TEST")
    print("=" * 80)
    print()
    
    print("🔍 STEP 1: Testing current state before upload")
    print("-" * 50)
    
    # Test current state
    diet_before = test_user_diet_before_upload()
    notifications_before = test_user_notifications_before_upload()
    profile_before = test_user_profile_before_upload()
    
    print()
    print("📤 STEP 2: Simulating diet upload")
    print("-" * 50)
    
    # Simulate upload
    upload_result = test_diet_upload_simulation()
    
    if upload_result:
        print()
        print("🔄 STEP 3: Testing state after upload")
        print("-" * 50)
        
        # Test state after upload
        diet_after = test_user_diet_after_upload()
        profile_after = test_user_profile_after_upload()
        
        print()
        print("📋 STEP 4: Testing notification extraction")
        print("-" * 50)
        
        # Test notification extraction
        extraction_result = test_notification_extraction_after_upload()
        notifications_after = test_user_notifications_after_upload()
        
        print()
        print("🔗 STEP 5: Testing URL consistency")
        print("-" * 50)
        
        # Test URL consistency
        url_consistency = test_diet_pdf_url_consistency()
        
        print()
        print("📱 STEP 6: Testing frontend refresh simulation")
        print("-" * 50)
        
        # Test frontend refresh
        frontend_refresh = test_frontend_refresh_simulation()
        
        print()
        print("=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        # Analyze results
        issues_found = []
        
        if diet_before and diet_after:
            if diet_before.get('dietPdfUrl') == diet_after.get('dietPdfUrl'):
                issues_found.append("❌ Diet PDF URL not updated after upload")
            else:
                print("✅ Diet PDF URL updated correctly")
        
        if profile_before and profile_after:
            cache_version_before = profile_before.get('dietCacheVersion')
            cache_version_after = profile_after.get('dietCacheVersion')
            if not cache_version_after or cache_version_after <= cache_version_before:
                issues_found.append("❌ Cache version not updated after upload")
            else:
                print("✅ Cache version updated correctly")
        
        if extraction_result:
            notification_count = len(extraction_result.get("notifications", []))
            if notification_count == 0:
                issues_found.append("❌ No notifications extracted from new diet")
            else:
                print(f"✅ {notification_count} notifications extracted from new diet")
        
        if notifications_before and notifications_after:
            before_count = len(notifications_before.get("notifications", []))
            after_count = len(notifications_after.get("notifications", []))
            if before_count == after_count and before_count > 0:
                issues_found.append("❌ Notification count not changed after new diet upload")
            else:
                print(f"✅ Notification count updated: {before_count} -> {after_count}")
        
        if not url_consistency:
            issues_found.append("❌ Diet PDF URL inconsistent across endpoints")
        else:
            print("✅ Diet PDF URL consistent across endpoints")
        
        if not frontend_refresh:
            issues_found.append("❌ Frontend refresh mechanism not working")
        else:
            print("✅ Frontend refresh mechanism working")
        
        print()
        if issues_found:
            print("🚨 ISSUES FOUND:")
            for issue in issues_found:
                print(f"  {issue}")
        else:
            print("🎉 No issues found! The system should work correctly.")
        
        print()
        print("RECOMMENDED FIXES:")
        print("1. Ensure diet upload properly updates user profile")
        print("2. Clear old notifications before extracting new ones")
        print("3. Force frontend refresh after diet upload")
        print("4. Add proper cache busting mechanism")
        print("5. Test notification extraction with new PDF")
        print("6. Ensure URL consistency across all endpoints")

if __name__ == "__main__":
    main()
