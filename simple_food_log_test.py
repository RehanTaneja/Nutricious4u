#!/usr/bin/env python3

import requests
from datetime import datetime

def simple_test():
    base_url = "https://nutricious4u-production.up.railway.app/api"
    user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    
    # Calculate timezone offset like frontend
    timezone_offset = int(-datetime.now().astimezone().utcoffset().total_seconds() / 60)
    local_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"🍎 Simple Food Logging Test")
    print(f"Local date: {local_date}")
    print(f"Timezone offset: {timezone_offset} minutes")
    
    # Test food log
    payload = {
        "userId": user_id,
        "foodName": "Simple Test Apple",
        "servingSize": "100",
        "calories": 80.0,
        "protein": 1.0,
        "fat": 0.5,
        "timezoneOffset": timezone_offset
    }
    
    try:
        response = requests.post(f"{base_url}/food/log", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            timestamp = data.get('timestamp', '')
            saved_date = timestamp.split('T')[0] if timestamp else 'Unknown'
            
            print(f"✅ Food logged successfully")
            print(f"Timestamp: {timestamp}")
            print(f"Saved on date: {saved_date}")
            
            if saved_date == local_date:
                print(f"✅ SUCCESS! Saved on correct local date")
                return True
            else:
                print(f"❌ Wrong date - expected {local_date}, got {saved_date}")
                return False
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = simple_test()
    exit(0 if success else 1)
