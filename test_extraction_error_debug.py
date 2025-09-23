#!/usr/bin/env python3
"""
Test script to debug the diet extraction error that occurs in mobile app.
This simulates the exact API calls made by the mobile app.
"""

import requests
import json
import time
import sys

# Test user ID from logs
USER_ID = 'EMoXb6rFuwN3xKsotq54K0kVArf1'
API_BASE = 'https://nutricious4u-production.up.railway.app/api'

def test_extraction_workflow():
    """Test the complete extraction workflow as mobile app does"""
    
    print("=== TESTING DIET EXTRACTION WORKFLOW ===")
    print(f"User ID: {USER_ID}")
    print(f"API Base: {API_BASE}")
    print()
    
    # Step 1: Check if user has diet PDF
    print("1. Checking user diet...")
    try:
        response = requests.get(f'{API_BASE}/users/{USER_ID}/diet', timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            diet_data = response.json()
            print(f"   Diet PDF URL: {diet_data.get('dietPdfUrl', 'None')}")
            print(f"   Days left: {diet_data.get('daysLeft', 'None')}")
            print(f"   Hours left: {diet_data.get('hoursLeft', 'None')}")
            
            # Check if countdown is 0 - this might be the trigger condition
            if diet_data.get('daysLeft') == 0 and diet_data.get('hoursLeft') == 0:
                print("   ⚠️  WARNING: Diet countdown is at 0 days, 0 hours")
                print("   ⚠️  This might be causing the extraction error")
            
        else:
            print(f"   ERROR: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Step 2: Get existing notifications 
    print("\n2. Checking existing notifications...")
    try:
        response = requests.get(f'{API_BASE}/users/{USER_ID}/diet/notifications', timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Existing notifications: {len(data.get('notifications', []))}")
        else:
            print(f"   ERROR: {response.text}")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Step 3: Test extraction endpoint (this is what's failing in mobile app)
    print("\n3. Testing extraction endpoint...")
    try:
        # Simulate mobile app headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=300, max=1000',
        }
        
        start_time = time.time()
        response = requests.post(
            f'{API_BASE}/users/{USER_ID}/diet/notifications/extract',
            headers=headers,
            timeout=60
        )
        end_time = time.time()
        
        print(f"   Status: {response.status_code}")
        print(f"   Duration: {end_time - start_time:.2f}s")
        print(f"   Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS: Extracted {len(data.get('notifications', []))} notifications")
            print(f"   Message: {data.get('message', 'No message')}")
            
            # Check if any notifications have scheduling issues
            notifications = data.get('notifications', [])
            if notifications:
                scheduled_count = sum(1 for n in notifications if n.get('scheduledId'))
                print(f"   Scheduled: {scheduled_count}/{len(notifications)}")
                
                # Check for any problems in notification structure
                for i, notif in enumerate(notifications[:3]):  # Check first 3
                    print(f"   Sample {i+1}: {notif.get('time')} - {notif.get('message')[:50]}...")
            
            return True
            
        else:
            print(f"   ❌ ERROR: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"   Error details: {json.dumps(error_data, indent=4)}")
            except:
                pass
                
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ ERROR: Request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ ERROR: Connection error - {e}")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_mobile_api_simulation():
    """Simulate the exact request pattern that mobile app uses"""
    
    print("\n=== MOBILE APP API SIMULATION ===")
    
    # Test with iOS-specific settings that mobile app uses
    session = requests.Session()
    
    # iOS-specific headers from the mobile app
    session.headers.update({
        'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive',
        'Keep-Alive': 'timeout=300, max=1000'
    })
    
    # Use the same timeout settings as mobile app (45 seconds for iOS)
    timeout = 45
    
    try:
        print(f"Making request with {timeout}s timeout...")
        response = session.post(
            f'{API_BASE}/users/{USER_ID}/diet/notifications/extract',
            timeout=timeout
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: {len(data.get('notifications', []))} notifications")
        else:
            print(f"❌ FAILED: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_concurrent_requests():
    """Test if concurrent requests might be causing issues"""
    
    print("\n=== TESTING CONCURRENT REQUEST HANDLING ===")
    
    import concurrent.futures
    import threading
    
    def make_request(request_id):
        try:
            response = requests.post(
                f'{API_BASE}/users/{USER_ID}/diet/notifications/extract',
                timeout=30
            )
            return f"Request {request_id}: {response.status_code}"
        except Exception as e:
            return f"Request {request_id}: ERROR - {e}"
    
    # Test 3 concurrent requests (like mobile app might do)
    print("Making 3 concurrent requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request, i+1) for i in range(3)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    for result in results:
        print(f"   {result}")

if __name__ == "__main__":
    # Run all tests
    success = test_extraction_workflow()
    test_mobile_api_simulation()
    test_concurrent_requests()
    
    if success:
        print("\n✅ EXTRACTION ENDPOINT IS WORKING CORRECTLY")
        print("The issue is likely in the mobile app's error handling or API call pattern")
    else:
        print("\n❌ EXTRACTION ENDPOINT HAS ISSUES")
        print("The problem is on the backend side")
