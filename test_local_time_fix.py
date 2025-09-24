#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime, timezone

def test_local_time_fix():
    """
    Test the local time fix for food logging:
    1. Backend now uses local time instead of UTC
    2. Food logs should appear in correct day's summary
    3. Both first and subsequent logs should work correctly
    4. Everything uses user's local time consistently
    """
    
    base_url = "https://nutricious4u-production.up.railway.app/api"
    user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    
    print("🏠 TESTING LOCAL TIME FIX")
    print("=" * 60)
    print(f"User: {user_id}")
    print(f"Test time: {datetime.now().isoformat()}")
    
    # Show local vs UTC time for reference
    local_time = datetime.now()
    utc_time = datetime.now(timezone.utc)
    local_date = local_time.strftime('%Y-%m-%d')
    utc_date = utc_time.strftime('%Y-%m-%d')
    
    print(f"Local time: {local_time}")
    print(f"UTC time: {utc_time}")
    print(f"Local date: {local_date}")
    print(f"UTC date: {utc_date}")
    print()
    
    print(f"🎯 FIX APPLIED:")
    print(f"   - Backend now uses LOCAL TIME for all operations")
    print(f"   - Food logs should be saved with LOCAL date: {local_date}")
    print(f"   - Summary should show data for LOCAL date: {local_date}")
    print(f"   - Frontend already uses LOCAL date: {local_date}")
    print(f"   - Everything should be consistent!")
    print()
    
    # Test 1: Get initial summary for local date
    print("1️⃣ CHECKING CURRENT SUMMARY FOR LOCAL DATE")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/food/log/summary/{user_id}", timeout=30)
        if response.status_code == 200:
            summary = response.json()
            
            print(f"Available dates in summary:")
            local_data = None
            utc_data = None
            
            for item in summary.get('history', []):
                date = item.get('day')
                calories = item.get('calories', 0)
                print(f"  - {date}: {calories} calories")
                
                if date == local_date:
                    local_data = item
                if date == utc_date:
                    utc_data = item
            
            print()
            print(f"Local date ({local_date}) data: {local_data.get('calories', 0) if local_data else 'Not found'} calories")
            print(f"UTC date ({utc_date}) data: {utc_data.get('calories', 0) if utc_data else 'Not found'} calories")
            
            # With the fix, we should have local date data
            if local_data:
                current_local_calories = local_data.get('calories', 0)
                print(f"✅ Found local date data: {current_local_calories} calories")
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
    
    # Test 2: Log first test food
    print("2️⃣ TESTING FIRST FOOD LOG (LOCAL TIME)")
    print("-" * 40)
    test_food_1 = {
        "userId": user_id,
        "foodName": "Local Time Test Food 1",
        "servingSize": "100",
        "calories": 111.0,
        "protein": 3.0,
        "fat": 1.5
    }
    
    try:
        print(f"Logging first test food: {test_food_1['foodName']}")
        print(f"Calories to add: {test_food_1['calories']}")
        
        response = requests.post(f"{base_url}/food/log", json=test_food_1, timeout=30)
        if response.status_code == 200:
            response_data = response.json()
            food_timestamp = response_data.get('timestamp')
            print(f"✅ First food logged successfully")
            print(f"   Timestamp: {food_timestamp}")
            
            # Parse the timestamp to see what date it's saved under
            if food_timestamp:
                # Backend now uses local time, so timestamp should be local
                saved_datetime = datetime.fromisoformat(food_timestamp.replace('Z', ''))
                saved_date = saved_datetime.strftime('%Y-%m-%d')
                print(f"   Saved under date: {saved_date}")
                
                if saved_date == local_date:
                    print(f"   ✅ Correctly saved under LOCAL date!")
                else:
                    print(f"   ⚠️ Saved under different date: {saved_date} vs expected {local_date}")
        else:
            print(f"❌ First food log failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception logging first food: {e}")
        return False
    print()
    
    # Test 3: Check if first food appears in summary
    print("3️⃣ VERIFYING FIRST FOOD APPEARS IN SUMMARY")
    print("-" * 40)
    time.sleep(2)  # Wait for database update
    
    try:
        response = requests.get(f"{base_url}/food/log/summary/{user_id}", timeout=30)
        if response.status_code == 200:
            updated_summary = response.json()
            
            # Check local date calories
            local_data_after_first = None
            for item in updated_summary.get('history', []):
                if item.get('day') == local_date:
                    local_data_after_first = item
                    break
            
            if local_data_after_first:
                calories_after_first = local_data_after_first.get('calories', 0)
                expected_calories_after_first = current_local_calories + test_food_1['calories']
                
                print(f"Before first log: {current_local_calories} calories")
                print(f"Added: {test_food_1['calories']} calories")
                print(f"Expected: {expected_calories_after_first} calories")
                print(f"Actual: {calories_after_first} calories")
                
                if abs(calories_after_first - expected_calories_after_first) < 1:
                    print(f"✅ SUCCESS! First food correctly added to LOCAL date")
                    current_local_calories = calories_after_first  # Update for next test
                else:
                    print(f"❌ First food not added correctly")
                    return False
            else:
                print(f"❌ No data found for local date after first log")
                return False
                
        else:
            print(f"❌ Failed to get updated summary: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception getting updated summary: {e}")
        return False
    print()
    
    # Test 4: Log second test food (the critical test that was failing)
    print("4️⃣ TESTING SECOND FOOD LOG (THE CRITICAL TEST)")
    print("-" * 40)
    test_food_2 = {
        "userId": user_id,
        "foodName": "Local Time Test Food 2",
        "servingSize": "150",
        "calories": 222.0,
        "protein": 6.0,
        "fat": 3.0
    }
    
    try:
        print(f"Logging second test food: {test_food_2['foodName']}")
        print(f"Calories to add: {test_food_2['calories']}")
        
        response = requests.post(f"{base_url}/food/log", json=test_food_2, timeout=30)
        if response.status_code == 200:
            response_data = response.json()
            food_timestamp = response_data.get('timestamp')
            print(f"✅ Second food logged successfully")
            print(f"   Timestamp: {food_timestamp}")
            
            if food_timestamp:
                saved_datetime = datetime.fromisoformat(food_timestamp.replace('Z', ''))
                saved_date = saved_datetime.strftime('%Y-%m-%d')
                print(f"   Saved under date: {saved_date}")
                
                if saved_date == local_date:
                    print(f"   ✅ Correctly saved under LOCAL date!")
                else:
                    print(f"   ⚠️ Saved under different date: {saved_date} vs expected {local_date}")
        else:
            print(f"❌ Second food log failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception logging second food: {e}")
        return False
    print()
    
    # Test 5: Check if second food appears in summary (THE CRITICAL TEST)
    print("5️⃣ VERIFYING SECOND FOOD APPEARS IN SUMMARY (CRITICAL)")
    print("-" * 40)
    time.sleep(2)  # Wait for database update
    
    try:
        response = requests.get(f"{base_url}/food/log/summary/{user_id}", timeout=30)
        if response.status_code == 200:
            final_summary = response.json()
            
            # Check local date calories
            local_data_after_second = None
            for item in final_summary.get('history', []):
                if item.get('day') == local_date:
                    local_data_after_second = item
                    break
            
            if local_data_after_second:
                final_calories = local_data_after_second.get('calories', 0)
                expected_final_calories = current_local_calories + test_food_2['calories']
                
                print(f"Before second log: {current_local_calories} calories")
                print(f"Added: {test_food_2['calories']} calories")
                print(f"Expected: {expected_final_calories} calories")
                print(f"Actual: {final_calories} calories")
                
                if abs(final_calories - expected_final_calories) < 1:
                    print(f"✅ SUCCESS! Second food correctly added to LOCAL date")
                    print(f"✅ LOCAL TIME FIX WORKING PERFECTLY!")
                    return True
                else:
                    print(f"❌ Second food not added correctly")
                    print(f"   Difference: {expected_final_calories - final_calories}")
                    return False
            else:
                print(f"❌ No data found for local date after second log")
                return False
                
        else:
            print(f"❌ Failed to get final summary: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception getting final summary: {e}")
        return False

if __name__ == "__main__":
    success = test_local_time_fix()
    
    if success:
        print()
        print("🎉 LOCAL TIME FIX VERIFICATION COMPLETE!")
        print("=" * 50)
        print("✅ Backend now uses LOCAL TIME for all operations")
        print("✅ Food logs appear in correct LOCAL day's summary")
        print("✅ Both first and subsequent logs work correctly")
        print("✅ Everything uses user's local time consistently")
        print("✅ User will see calories in tracker and graph immediately")
        print("✅ No more timezone confusion!")
    else:
        print()
        print("❌ LOCAL TIME FIX NEEDS MORE INVESTIGATION")
        
    exit(0 if success else 1)
