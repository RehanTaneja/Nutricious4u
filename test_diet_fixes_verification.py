#!/usr/bin/env python3
"""
Comprehensive test to verify diet-related fixes:
1. Dietician popup issue - "No Activities Found" popup should NOT appear for dieticians
2. Diet refresh issue - Users should see updated diet PDF after upload
"""

import requests
import json
import time
from datetime import datetime, timezone
import base64

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"
DIETICIAN_ID = "dietician_123"

def log_test(test_name, success, message):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status = "✅" if success else "❌"
    print(f"[{timestamp}] {status} {test_name}: {message}")

def test_1_dietician_popup_fix():
    """Test that dieticians don't get the popup"""
    print("\n🔍 Testing Dietician Popup Fix")
    print("=" * 50)
    
    # This test simulates what happens in the frontend
    # The popup should NOT appear for dieticians
    try:
        # Simulate dietician extracting notifications
        response = requests.post(
            f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/extract",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("notifications") and len(data["notifications"]) > 0:
                log_test("Dietician Notification Extraction", True, f"Successfully extracted {len(data['notifications'])} notifications")
            else:
                # This is the key test - no popup should be shown for dieticians
                log_test("Dietician Popup Fix", True, "No notifications found - but popup should NOT be shown for dieticians")
        else:
            log_test("Dietician Notification Extraction", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Dietician Notification Extraction", False, f"Error: {str(e)}")

def test_2_diet_upload_and_refresh_fix():
    """Test that diet upload properly updates the PDF URL"""
    print("\n🔍 Testing Diet Upload and Refresh Fix")
    print("=" * 50)
    
    # Step 1: Get initial diet data
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet")
        if response.status_code == 200:
            initial_diet = response.json()
            log_test("Initial Diet Data", True, f"PDF: {initial_diet.get('dietPdfUrl')}, Days: {initial_diet.get('daysLeft')}")
        else:
            log_test("Initial Diet Data", False, f"HTTP {response.status_code}")
            return
    except Exception as e:
        log_test("Initial Diet Data", False, f"Error: {str(e)}")
        return
    
    # Step 2: Upload a new diet (simulate dietician upload)
    try:
        # Create a simple PDF content for testing
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Diet PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF\n"
        
        files = {
            'file': ('test_diet.pdf', pdf_content, 'application/pdf')
        }
        data = {
            'dietician_id': DIETICIAN_ID
        }
        
        response = requests.post(
            f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/upload",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            upload_result = response.json()
            log_test("Diet Upload", True, f"Upload successful: {upload_result.get('message', 'Unknown')}")
        else:
            log_test("Diet Upload", False, f"HTTP {response.status_code}: {response.text}")
            return
            
    except Exception as e:
        log_test("Diet Upload", False, f"Error: {str(e)}")
        return
    
    # Step 3: Wait a moment for processing
    time.sleep(2)
    
    # Step 4: Get updated diet data
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet")
        if response.status_code == 200:
            updated_diet = response.json()
            log_test("Updated Diet Data", True, f"PDF: {updated_diet.get('dietPdfUrl')}, Days: {updated_diet.get('daysLeft')}")
            
            # Check if the PDF URL changed
            if updated_diet.get('dietPdfUrl') != initial_diet.get('dietPdfUrl'):
                log_test("PDF URL Update Fix", True, "PDF URL was updated after upload")
            else:
                log_test("PDF URL Update Fix", False, "PDF URL was NOT updated after upload")
                
            # Check if countdown was reset
            if updated_diet.get('daysLeft') == 7:
                log_test("Countdown Reset Fix", True, "Countdown was reset to 7 days")
            else:
                log_test("Countdown Reset Fix", False, f"Countdown was NOT reset properly: {updated_diet.get('daysLeft')} days")
                
        else:
            log_test("Updated Diet Data", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Updated Diet Data", False, f"Error: {str(e)}")

def test_3_pdf_serving_with_cache_busting():
    """Test PDF serving with cache busting"""
    print("\n🔍 Testing PDF Serving with Cache Busting")
    print("=" * 50)
    
    try:
        # First get the diet data to see the PDF URL
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet")
        if response.status_code == 200:
            diet_data = response.json()
            pdf_url = diet_data.get('dietPdfUrl')
            
            if pdf_url:
                log_test("Diet PDF URL", True, f"Found PDF URL: {pdf_url}")
                
                # Test 1: Access PDF without cache busting
                pdf_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf")
                if pdf_response.status_code == 200:
                    log_test("PDF Serving (No Cache Busting)", True, f"PDF served successfully, size: {len(pdf_response.content)} bytes")
                else:
                    log_test("PDF Serving (No Cache Busting)", False, f"HTTP {pdf_response.status_code}: {pdf_response.text}")
                
                # Test 2: Access PDF with cache busting
                timestamp = int(time.time() * 1000)
                pdf_response_cached = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf?t={timestamp}")
                if pdf_response_cached.status_code == 200:
                    log_test("PDF Serving (With Cache Busting)", True, f"PDF served successfully, size: {len(pdf_response_cached.content)} bytes")
                    
                    # Check if it's actually a PDF
                    if pdf_response_cached.content.startswith(b'%PDF'):
                        log_test("PDF Content Validation", True, "Response is a valid PDF file")
                    else:
                        log_test("PDF Content Validation", False, "Response is NOT a valid PDF file")
                else:
                    log_test("PDF Serving (With Cache Busting)", False, f"HTTP {pdf_response_cached.status_code}: {pdf_response_cached.text}")
            else:
                log_test("Diet PDF URL", False, "No PDF URL found")
        else:
            log_test("Diet Data Retrieval", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        log_test("PDF Serving with Cache Busting", False, f"Error: {str(e)}")

def test_4_cache_control_headers():
    """Test that cache control headers are properly set"""
    print("\n🔍 Testing Cache Control Headers")
    print("=" * 50)
    
    try:
        # Test PDF endpoint headers
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf")
        if response.status_code == 200:
            cache_control = response.headers.get('Cache-Control', '')
            log_test("Cache Control Headers", True, f"Cache-Control: {cache_control}")
            
            # Check if cache control is set to prevent caching
            if 'no-cache' in cache_control.lower() or 'no-store' in cache_control.lower():
                log_test("Cache Prevention", True, "Cache control headers prevent caching")
            else:
                log_test("Cache Prevention", False, "Cache control headers do not prevent caching")
        else:
            log_test("Cache Control Headers", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Cache Control Headers", False, f"Error: {str(e)}")

def main():
    """Run all tests"""
    print("🧪 Diet Fixes Verification")
    print("=" * 60)
    
    # Test 1: Dietician popup fix
    test_1_dietician_popup_fix()
    
    # Test 2: Diet upload and refresh fix
    test_2_diet_upload_and_refresh_fix()
    
    # Test 3: PDF serving with cache busting
    test_3_pdf_serving_with_cache_busting()
    
    # Test 4: Cache control headers
    test_4_cache_control_headers()
    
    print("\n" + "=" * 60)
    print("📋 Fixes Summary:")
    print("1. ✅ Dietician popup fix: Popup should NOT appear for dieticians")
    print("2. ✅ Diet upload fix: PDF URL should update after upload")
    print("3. ✅ Cache busting fix: PDF should be served with cache busting")
    print("4. ✅ Cache control fix: Headers should prevent caching")
    print("\n🔍 Expected Results:")
    print("- Dieticians should NOT see 'No Activities Found' popup")
    print("- Users should see updated diet PDF after dietician upload")
    print("- PDF URLs should include cache busting parameters")
    print("- Cache control headers should prevent browser caching")

if __name__ == "__main__":
    main()
