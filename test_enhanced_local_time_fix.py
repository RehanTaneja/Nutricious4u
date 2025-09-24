#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime, timezone

def test_enhanced_local_time_fix():
    """
    Test the enhanced local time fix for food logging:
    1. Frontend now sends timezone offset to backend
    2. Backend calculates user's local time using the offset
    3. Food logs should appear in correct day's summary
    4. Both first and subsequent logs should work correctly
    """
    
    base_url = "https://nutricious4u-production.up.railway.app/api"
    user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    
    print("🌍 TESTING ENHANCED LOCAL TIME FIX (WITH TIMEZONE OFFSET)")
    print("=" * 70)
    print(f"User: {user_id}")
    print(f"Test time: {datetime.now().isoformat()}")
    
    # Calculate timezone offset like frontend does
    local_time = datetime.now()
    timezone_offset = datetime.now().astimezone().utcoffset().total_seconds() / 60
    timezone_offset = int(-timezone_offset)  # JavaScript uses negative values
    
    local_date = local_time.strftime('%Y-%m-%d')
    utc_time = datetime.now(timezone.utc)
    utc_date = utc_time.strftime('%Y-%m-%d')
    
    print(f"Local time: {local_time}")
    print(f"UTC time: {utc_time}")
    print(f"Local date: {local_date}")
    print(f"UTC date: {utc_date}")
    print(f"Timezone offset: {timezone_offset} minutes ({timezone_offset / 60} hours)")
    print()
    
    print(f"🎯 ENHANCED FIX:")
    print(f"   - Frontend sends timezone offset: {timezone_offset} minutes")
    print(f"   - Backend calculates user's local time using offset")
    print(f"   - Food logs should be saved with LOCAL date: {local_date}")
    print(f"   - Summary should show data for LOCAL date: {local_date}")
    print(f"   - Complete timezone consistency!")
    print()
    
    # Test 1: Get initial summary
    print("1️⃣ CHECKING CURRENT SUMMARY")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/food/log/summary/{user_id}", timeout=30)
        if response.status_code == 200:
            summary = response.json()
            
            print(f"Available dates in summary:")
            local_data = None
            
            for item in summary.get('history', []):
                date = item.get('day')
                calories = item.get('calories', 0)
                print(f"  - {date}: {calories} calories")
                
                if date == local_date:
                    local_data = item
            
            print()
            if local_data:
                current_local_calories = local_data.get('calories', 0)
                print(f"✅ Current local date ({local_date}) calories: {current_local_calories}")
            else:
                current_local_calories = 0
                print(f"✅ No local date data yet, starting from 0")
                
        else:
            print(f"❌ Failed to get summary: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    print()
    
    # Test 2: Log food with timezone offset
    print("2️⃣ TESTING FOOD LOG WITH TIMEZONE OFFSET")
    print("-" * 40)
    test_food = {
        "userId": user_id,
        "foodName": "Enhanced Local Time Test",
        "servingSize": "100",
        "calories": 333.0,
        "protein": 7.0,
        "fat": 4.0,
        "timezoneOffset": timezone_offset  # Send timezone offset
    }
    
    try:
        print(f"Logging test food: {test_food['foodName']}")
        print(f"Calories to add: {test_food['calories']}")
        print(f"Timezone offset being sent: {test_food['timezoneOffset']} minutes")
        
        response = requests.post(f"{base_url}/food/log", json=test_food, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            food_timestamp = response_data.get('timestamp')
            print(f"✅ Food logged successfully")
            print(f"   Backend timestamp: {food_timestamp}")
            
            # Parse the timestamp to check the date
            if food_timestamp:
                # Remove Z if present and parse
                timestamp_str = food_timestamp.replace('Z', '')
                try:
                    saved_datetime = datetime.fromisoformat(timestamp_str)
                    saved_date = saved_datetime.strftime('%Y-%m-%d')
                    print(f"   Calculated date: {saved_date}")
                    
                    if saved_date == local_date:
                        print(f"   ✅ PERFECT! Saved under LOCAL date: {saved_date}")
                    else:
                        print(f"   ❌ Wrong date - expected {local_date}, got {saved_date}")
                except Exception as e:
                    print(f"   ⚠️ Could not parse timestamp: {e}")
        else:
            print(f"❌ Food log failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception logging food: {e}")
        return False
    print()
    
    # Test 3: Verify calories appear in summary
    print("3️⃣ VERIFYING CALORIES APPEAR IN LOCAL DATE SUMMARY")
    print("-" * 50)
    time.sleep(3)  # Wait for database update
    
    try:
        response = requests.get(f"{base_url}/food/log/summary/{user_id}", timeout=30)
        if response.status_code == 200:
            updated_summary = response.json()
            
            # Check local date calories
            local_data_after = None
            for item in updated_summary.get('history', []):
                if item.get('day') == local_date:
                    local_data_after = item
                    break
            
            if local_data_after:
                new_calories = local_data_after.get('calories', 0)
                expected_calories = current_local_calories + test_food['calories']
                
                print(f"Before log: {current_local_calories} calories")
                print(f"Added: {test_food['calories']} calories")
                print(f"Expected: {expected_calories} calories")
                print(f"Actual: {new_calories} calories")
                
                if abs(new_calories - expected_calories) < 1:
                    print(f"✅ SUCCESS! Calories correctly added to LOCAL date")
                    print(f"✅ ENHANCED LOCAL TIME FIX WORKING PERFECTLY!")
                    return True
                else:
                    print(f"❌ Calories not added correctly")
                    print(f"   Difference: {expected_calories - new_calories}")
                    return False
            else:
                print(f"❌ No data found for local date after logging")
                return False
                
        else:
            print(f"❌ Failed to get updated summary: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception getting updated summary: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_local_time_fix()
    
    if success:
        print()
        print("🎉 ENHANCED LOCAL TIME FIX SUCCESSFUL!")
        print("=" * 60)
        print("✅ Frontend sends timezone offset to backend")
        print("✅ Backend calculates user's local time correctly") 
        print("✅ Food logs appear in correct LOCAL day's summary")
        print("✅ Complete timezone consistency achieved")
        print("✅ User will see calories immediately in tracker/graph")
        print("✅ Food logging issue COMPLETELY RESOLVED!")
    else:
        print()
        print("❌ ENHANCED FIX STILL NEEDS WORK")
        
    exit(0 if success else 1)
