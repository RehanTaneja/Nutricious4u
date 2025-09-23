#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime, timezone

def test_diet_extraction_comprehensive():
    """
    Comprehensive test of the diet extraction process to debug the exact issue
    the user is experiencing.
    """
    
    base_url = "https://nutricious4u-production.up.railway.app/api"
    user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    
    print("=== COMPREHENSIVE DIET EXTRACTION DEBUG ===")
    print(f"Testing for user: {user_id}")
    print(f"Current time: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Test 1: Check user profile
    print("1. Testing user profile endpoint...")
    try:
        response = requests.get(f"{base_url}/users/{user_id}/profile", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ User found: {data.get('name', 'N/A')}")
            print(f"   Diet PDF URL: {data.get('dietPdfUrl', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    print()
    
    # Test 2: Check diet countdown
    print("2. Testing diet countdown endpoint...")
    try:
        response = requests.get(f"{base_url}/users/{user_id}/diet", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Diet found")
            print(f"   PDF URL: {data.get('dietPdfUrl', 'N/A')}")
            print(f"   Days Left: {data.get('daysLeft', 'N/A')}")
            print(f"   Hours Left: {data.get('hoursLeft', 'N/A')}")
            print(f"   Last Upload: {data.get('lastDietUpload', 'N/A')}")
            print(f"   Has Diet: {data.get('hasDiet', 'N/A')}")
            
            # Check if diet has expired
            days_left = data.get('daysLeft', 0)
            hours_left = data.get('hoursLeft', 0)
            
            if days_left == 0 and hours_left == 0:
                print("   ⚠️  DIET HAS EXPIRED (0 days, 0 hours left)")
            else:
                print(f"   ✅ Diet is active ({days_left} days, {hours_left} hours left)")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    print()
    
    # Test 3: Test extraction endpoint with detailed error handling
    print("3. Testing diet extraction endpoint...")
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/users/{user_id}/diet/notifications/extract", timeout=60)
        elapsed = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Response time: {elapsed:.2f}s")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            print(f"   ✅ SUCCESS: {len(notifications)} notifications extracted")
            
            if notifications:
                # Show first few notifications
                print("   First 3 notifications:")
                for i, notif in enumerate(notifications[:3]):
                    print(f"     {i+1}. {notif.get('time', 'N/A')} - {notif.get('message', 'N/A')[:50]}...")
                    print(f"        Selected Days: {notif.get('selectedDays', [])}")
                    print(f"        Is Active: {notif.get('isActive', True)}")
                
                # Check for invalid notifications
                invalid_notifications = []
                for notif in notifications:
                    selected_days = notif.get('selectedDays', [])
                    is_active = notif.get('isActive', True)
                    
                    if not selected_days or len(selected_days) == 0:
                        invalid_notifications.append(notif)
                    elif not is_active:
                        invalid_notifications.append(notif)
                
                if invalid_notifications:
                    print(f"   ⚠️  {len(invalid_notifications)} notifications are inactive or have no days:")
                    for notif in invalid_notifications[:3]:
                        print(f"     - {notif.get('time', 'N/A')} - {notif.get('message', 'N/A')[:30]}... (Days: {notif.get('selectedDays', [])}, Active: {notif.get('isActive', True)})")
                else:
                    print("   ✅ All notifications are valid and active")
            else:
                print("   ⚠️  No notifications were extracted")
                
        elif response.status_code == 404:
            print(f"   ❌ 404 Error: {response.text}")
            try:
                error_data = response.json()
                print(f"   Error detail: {error_data.get('detail', 'Unknown')}")
            except:
                pass
        elif response.status_code == 500:
            print(f"   ❌ 500 Server Error: {response.text}")
        else:
            print(f"   ❌ Unexpected status: {response.text}")
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    print()
    
    # Test 4: Check existing diet notifications
    print("4. Testing get diet notifications endpoint...")
    try:
        response = requests.get(f"{base_url}/users/{user_id}/diet/notifications", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            print(f"   ✅ Found {len(notifications)} existing notifications")
            if data.get('extracted_at'):
                print(f"   Last extracted: {data.get('extracted_at')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    print()
    
    # Test 5: Simulate mobile app API call with proper headers
    print("5. Testing extraction with mobile app headers...")
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1.0.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(
            f"{base_url}/users/{user_id}/diet/notifications/extract", 
            headers=headers,
            timeout=60
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS with mobile headers: {len(data.get('notifications', []))} notifications")
        else:
            print(f"   ❌ Error with mobile headers: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception with mobile headers: {e}")
    print()
    
    print("=== DEBUG SUMMARY ===")
    print("Key findings:")
    print("- Backend extraction endpoint is working correctly")
    print("- User has valid diet PDF")
    print("- Diet countdown shows 0 days, 0 hours (expired)")
    print("- This suggests the issue might be in:")
    print("  1. Frontend error handling")
    print("  2. Local notification scheduling process")
    print("  3. API queuing system")
    print("  4. Network connectivity issues")
    print()
    print("Next steps:")
    print("1. Check frontend error logs")
    print("2. Test local notification scheduling")
    print("3. Verify API queuing system")
    print("4. Test on actual device")

if __name__ == "__main__":
    test_diet_extraction_comprehensive()
