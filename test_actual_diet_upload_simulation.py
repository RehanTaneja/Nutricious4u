#!/usr/bin/env python3
"""
Actual Diet Upload Simulation Test

This script simulates an actual diet upload to identify why the diet PDF URL is not being updated
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

def test_current_diet_state():
    """Test current diet state before upload"""
    try:
        # Get current diet data
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet", timeout=10)
        
        if response.status_code == 200:
            diet_data = response.json()
            current_diet = diet_data.get("dietPdfUrl")
            days_left = diet_data.get("daysLeft")
            log_test("Current Diet State", True, f"Current diet: {current_diet}, Days left: {days_left}")
            return current_diet
        else:
            log_test("Current Diet State", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("Current Diet State", False, f"Error: {str(e)}")
        return None

def test_current_profile_state():
    """Test current profile state before upload"""
    try:
        # Get current profile data
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            current_diet = profile_data.get("dietPdfUrl")
            cache_version = profile_data.get("dietCacheVersion")
            last_upload = profile_data.get("lastDietUpload")
            log_test("Current Profile State", True, f"Diet: {current_diet}, Cache: {cache_version}, Last upload: {last_upload}")
            return {"diet": current_diet, "cache": cache_version, "last_upload": last_upload}
        else:
            log_test("Current Profile State", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("Current Profile State", False, f"Error: {str(e)}")
        return None

def test_diet_upload_endpoint():
    """Test the actual diet upload endpoint"""
    try:
        # Create a simple test PDF content
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Diet PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
        
        # Create test filename
        test_filename = f"test_diet_upload_{int(time.time())}.pdf"
        
        # Prepare the upload data
        files = {
            'file': (test_filename, test_pdf_content, 'application/pdf')
        }
        data = {
            'dietician_id': TEST_DIETICIAN_ID
        }
        
        # Make the upload request
        response = requests.post(
            f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/upload",
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            log_test("Diet Upload Endpoint", True, f"Upload successful: {result.get('message', 'Success')}")
            return test_filename
        else:
            log_test("Diet Upload Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
            return None
            
    except Exception as e:
        log_test("Diet Upload Endpoint", False, f"Error: {str(e)}")
        return None

def test_diet_after_upload():
    """Test diet data after upload"""
    try:
        # Wait a moment for the upload to process
        time.sleep(2)
        
        # Get diet data after upload
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet", timeout=10)
        
        if response.status_code == 200:
            diet_data = response.json()
            new_diet = diet_data.get("dietPdfUrl")
            days_left = diet_data.get("daysLeft")
            log_test("Diet After Upload", True, f"New diet: {new_diet}, Days left: {days_left}")
            return new_diet
        else:
            log_test("Diet After Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("Diet After Upload", False, f"Error: {str(e)}")
        return None

def test_profile_after_upload():
    """Test profile data after upload"""
    try:
        # Get profile data after upload
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            new_diet = profile_data.get("dietPdfUrl")
            cache_version = profile_data.get("dietCacheVersion")
            last_upload = profile_data.get("lastDietUpload")
            log_test("Profile After Upload", True, f"Diet: {new_diet}, Cache: {cache_version}, Last upload: {last_upload}")
            return {"diet": new_diet, "cache": cache_version, "last_upload": last_upload}
        else:
            log_test("Profile After Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("Profile After Upload", False, f"Error: {str(e)}")
        return None

def test_notifications_after_upload():
    """Test notifications after upload"""
    try:
        # Get notifications after upload
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications", timeout=10)
        
        if response.status_code == 200:
            notifications_data = response.json()
            notification_count = len(notifications_data.get("notifications", []))
            diet_pdf_url = notifications_data.get("diet_pdf_url")
            extracted_at = notifications_data.get("extracted_at")
            log_test("Notifications After Upload", True, f"Count: {notification_count}, PDF: {diet_pdf_url}, Extracted: {extracted_at}")
            return {"count": notification_count, "pdf": diet_pdf_url, "extracted": extracted_at}
        else:
            log_test("Notifications After Upload", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        log_test("Notifications After Upload", False, f"Error: {str(e)}")
        return None

def main():
    """Run actual diet upload simulation test"""
    print("=" * 80)
    print("ACTUAL DIET UPLOAD SIMULATION TEST")
    print("=" * 80)
    print()
    
    print("🔍 STEP 1: Testing current state before upload")
    print("-" * 50)
    
    # Test current state
    current_diet = test_current_diet_state()
    current_profile = test_current_profile_state()
    
    print()
    print("📤 STEP 2: Simulating actual diet upload")
    print("-" * 50)
    
    # Test actual upload
    uploaded_filename = test_diet_upload_endpoint()
    
    if uploaded_filename:
        print()
        print("🔄 STEP 3: Testing state after upload")
        print("-" * 50)
        
        # Test state after upload
        new_diet = test_diet_after_upload()
        new_profile = test_profile_after_upload()
        new_notifications = test_notifications_after_upload()
        
        print()
        print("=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        # Analyze results
        issues_found = []
        
        if current_diet and new_diet:
            if current_diet == new_diet:
                issues_found.append("❌ Diet PDF URL not updated after upload")
            else:
                print("✅ Diet PDF URL updated correctly")
        
        if current_profile and new_profile:
            current_cache = current_profile.get("cache")
            new_cache = new_profile.get("cache")
            if not new_cache or new_cache == current_cache:
                issues_found.append("❌ Cache version not updated after upload")
            else:
                print("✅ Cache version updated correctly")
        
        if new_notifications:
            notification_count = new_notifications.get("count", 0)
            if notification_count == 0:
                issues_found.append("❌ No notifications extracted from new diet")
            else:
                print(f"✅ {notification_count} notifications extracted from new diet")
        
        print()
        if issues_found:
            print("🚨 ISSUES FOUND:")
            for issue in issues_found:
                print(f"  {issue}")
            
            print()
            print("🔧 ROOT CAUSE ANALYSIS:")
            print("The issue is that the diet upload endpoint is not properly updating the user profile.")
            print("This could be due to:")
            print("1. Firestore update failing silently")
            print("2. User profile document not existing")
            print("3. Permission issues with Firestore")
            print("4. Async operation not completing properly")
            
            print()
            print("🛠️ RECOMMENDED FIXES:")
            print("1. Add better error handling in diet upload endpoint")
            print("2. Ensure user profile exists before upload")
            print("3. Add retry mechanism for Firestore updates")
            print("4. Add verification step after upload")
            print("5. Force frontend refresh after successful upload")
        else:
            print("🎉 No issues found! The diet upload should work correctly.")
    
    else:
        print("❌ Diet upload failed - cannot proceed with analysis")

if __name__ == "__main__":
    main()
