#!/usr/bin/env python3
"""
Test script for diet notifications
Run this to manually test the notification system
"""

import requests
import json
from datetime import datetime

# Backend URL (adjust as needed)
BACKEND_URL = "http://localhost:8000"

def test_diet_reminder_check():
    """Test the diet reminder check endpoint"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/diet/check-reminders")
        if response.status_code == 200:
            result = response.json()
            print("✅ Diet reminder check successful")
            print(f"Users with 1 day remaining: {result['users_with_one_day']}")
            if result['users']:
                print("Users:")
                for user in result['users']:
                    print(f"  - {user['name']} ({user['email']})")
            else:
                print("No users with 1 day remaining")
        else:
            print(f"❌ Diet reminder check failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error testing diet reminder check: {e}")

def test_push_notification():
    """Test sending a push notification to a specific user"""
    # You'll need to replace this with an actual user ID and token
    user_id = "test_user_id"
    token = "ExponentPushToken[your_token_here]"
    
    try:
        # Test the notification endpoint directly
        message = {
            "to": token,
            "sound": "default",
            "title": "Test Notification",
            "body": "This is a test notification from the diet system",
            "data": {"type": "test", "userId": user_id}
        }
        
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            headers={
                "Accept": "application/json",
                "Accept-encoding": "gzip, deflate",
                "Content-Type": "application/json",
            },
            data=json.dumps(message)
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test notification sent successfully")
            print(f"Response: {result}")
        else:
            print(f"❌ Test notification failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error testing push notification: {e}")

if __name__ == "__main__":
    print("🧪 Testing Diet Notification System")
    print("=" * 40)
    
    print("\n1. Testing diet reminder check...")
    test_diet_reminder_check()
    
    print("\n2. Testing push notification...")
    test_push_notification()
    
    print("\n✅ Test completed!") 