#!/usr/bin/env python3
"""
Test script for push notification system - Message Notifications
Tests:
1. User sends message to dietician -> Dietician receives push notification
2. Dietician sends message to user -> User receives push notification
"""

import requests
import json
import sys

# Backend URL
BACKEND_URL = "https://nutricious4u-production.up.railway.app"

# Test user IDs (replace with real IDs from your Firebase)
TEST_USER_ID = "test_user_123"  # Replace with a real user ID
DIETICIAN_ID = "dietician"

def test_user_to_dietician_message():
    """Test notification when user sends message to dietician"""
    print("\n=== TEST 1: User -> Dietician Message Notification ===")
    
    notification_data = {
        "type": "message",
        "recipientId": DIETICIAN_ID,
        "senderName": "Test User",
        "message": "Hello dietician, this is a test message!",
        "isFromDietician": False
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/push-notifications/send",
            json=notification_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get("success"):
            print("✅ TEST 1 PASSED: Notification sent successfully")
            return True
        else:
            print("❌ TEST 1 FAILED: Notification failed to send")
            return False
            
    except Exception as e:
        print(f"❌ TEST 1 ERROR: {e}")
        return False

def test_dietician_to_user_message():
    """Test notification when dietician sends message to user"""
    print("\n=== TEST 2: Dietician -> User Message Notification ===")
    
    notification_data = {
        "type": "message",
        "recipientId": TEST_USER_ID,
        "senderName": "Dietician",
        "message": "Hello, this is your dietician!",
        "isFromDietician": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/push-notifications/send",
            json=notification_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get("success"):
            print("✅ TEST 2 PASSED: Notification sent successfully")
            return True
        else:
            print("❌ TEST 2 FAILED: Notification failed to send")
            return False
            
    except Exception as e:
        print(f"❌ TEST 2 ERROR: {e}")
        return False

def main():
    print("=" * 60)
    print("PUSH NOTIFICATION TESTING - MESSAGE NOTIFICATIONS")
    print("=" * 60)
    print(f"\nBackend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Dietician ID: {DIETICIAN_ID}")
    print("\n⚠️  IMPORTANT: Make sure you have:")
    print("1. Valid user and dietician accounts in Firebase")
    print("2. Push notification tokens registered for both")
    print("3. Mobile devices ready to receive notifications")
    
    input("\nPress Enter to start testing...")
    
    # Run tests
    test1_result = test_user_to_dietician_message()
    test2_result = test_dietician_to_user_message()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Test 1 (User -> Dietician): {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Test 2 (Dietician -> User): {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

