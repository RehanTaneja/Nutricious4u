#!/usr/bin/env python3
"""
Comprehensive test to analyze diet-related issues:
1. Dietician popup issue - "No Activities Found" popup appearing for dieticians
2. Diet refresh issue - Users seeing old diet PDF even after countdown updates
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

def test_1_dietician_popup_analysis():
    """Analyze the dietician popup issue"""
    print("\n🔍 Testing Dietician Popup Issue")
    print("=" * 50)
    
    # Test 1: Check if dietician gets the popup when extracting notifications
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
                log_test("Dietician Notification Extraction", False, "No notifications found - this would trigger the popup")
        else:
            log_test("Dietician Notification Extraction", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Dietician Notification Extraction", False, f"Error: {str(e)}")

def test_2_diet_upload_and_refresh_analysis():
    """Analyze diet upload and refresh functionality"""
    print("\n🔍 Testing Diet Upload and Refresh Analysis")
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
                log_test("PDF URL Update", True, "PDF URL was updated after upload")
            else:
                log_test("PDF URL Update", False, "PDF URL was NOT updated after upload")
                
            # Check if countdown was reset
            if updated_diet.get('daysLeft') == 7:
                log_test("Countdown Reset", True, "Countdown was reset to 7 days")
            else:
                log_test("Countdown Reset", False, f"Countdown was NOT reset properly: {updated_diet.get('daysLeft')} days")
                
        else:
            log_test("Updated Diet Data", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Updated Diet Data", False, f"Error: {str(e)}")

def test_3_pdf_serving_analysis():
    """Analyze PDF serving functionality"""
    print("\n🔍 Testing PDF Serving Analysis")
    print("=" * 50)
    
    try:
        # First get the diet data to see the PDF URL
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet")
        if response.status_code == 200:
            diet_data = response.json()
            pdf_url = diet_data.get('dietPdfUrl')
            
            if pdf_url:
                log_test("Diet PDF URL", True, f"Found PDF URL: {pdf_url}")
                
                # Try to access the PDF
                pdf_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf")
                if pdf_response.status_code == 200:
                    log_test("PDF Serving", True, f"PDF served successfully, size: {len(pdf_response.content)} bytes")
                    
                    # Check if it's actually a PDF
                    if pdf_response.content.startswith(b'%PDF'):
                        log_test("PDF Content Validation", True, "Response is a valid PDF file")
                    else:
                        log_test("PDF Content Validation", False, "Response is NOT a valid PDF file")
                else:
                    log_test("PDF Serving", False, f"HTTP {pdf_response.status_code}: {pdf_response.text}")
            else:
                log_test("Diet PDF URL", False, "No PDF URL found")
        else:
            log_test("Diet Data Retrieval", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        log_test("PDF Serving Analysis", False, f"Error: {str(e)}")

def test_4_cache_analysis():
    """Analyze cache and refresh mechanisms"""
    print("\n🔍 Testing Cache and Refresh Analysis")
    print("=" * 50)
    
    try:
        # Test multiple rapid requests to see if cache is working properly
        responses = []
        for i in range(3):
            response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet")
            if response.status_code == 200:
                data = response.json()
                responses.append({
                    'timestamp': datetime.now().isoformat(),
                    'pdf_url': data.get('dietPdfUrl'),
                    'cache_version': data.get('dietCacheVersion'),
                    'days_left': data.get('daysLeft')
                })
            time.sleep(0.5)
        
        # Check if all responses are consistent
        if len(responses) == 3:
            pdf_urls = [r['pdf_url'] for r in responses]
            cache_versions = [r['cache_version'] for r in responses]
            
            if len(set(pdf_urls)) == 1:
                log_test("PDF URL Consistency", True, "All requests returned same PDF URL")
            else:
                log_test("PDF URL Consistency", False, f"PDF URLs inconsistent: {pdf_urls}")
                
            if len(set(cache_versions)) == 1:
                log_test("Cache Version Consistency", True, "All requests returned same cache version")
            else:
                log_test("Cache Version Consistency", False, f"Cache versions inconsistent: {cache_versions}")
                
        else:
            log_test("Multiple Requests", False, f"Only {len(responses)} successful requests out of 3")
            
    except Exception as e:
        log_test("Cache Analysis", False, f"Error: {str(e)}")

def main():
    """Run all tests"""
    print("🧪 Diet Issues Analysis")
    print("=" * 60)
    
    # Test 1: Dietician popup issue
    test_1_dietician_popup_analysis()
    
    # Test 2: Diet upload and refresh analysis
    test_2_diet_upload_and_refresh_analysis()
    
    # Test 3: PDF serving analysis
    test_3_pdf_serving_analysis()
    
    # Test 4: Cache analysis
    test_4_cache_analysis()
    
    print("\n" + "=" * 60)
    print("📋 Analysis Summary:")
    print("1. Dietician popup issue: Check if dieticians get 'No Activities Found' popup")
    print("2. Diet upload issue: Check if PDF URL updates after upload")
    print("3. PDF serving issue: Check if PDF can be accessed and is valid")
    print("4. Cache issue: Check if multiple requests return consistent data")
    print("\n🔍 Root Cause Analysis:")
    print("- If countdown updates but PDF doesn't: Cache issue in frontend")
    print("- If PDF URL doesn't update: Backend upload issue")
    print("- If PDF serves but shows old content: Storage/URL issue")

if __name__ == "__main__":
    main()
