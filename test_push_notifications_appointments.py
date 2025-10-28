#!/usr/bin/env python3
"""
Test script for push notification system - Appointment Notifications
Tests:
1. User schedules appointment -> Dietician receives notification
2. User cancels appointment -> Dietician receives notification
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Backend URL
BACKEND_URL = "https://nutricious4u-production.up.railway.app"

# Test data
TEST_USER_NAME = "John Doe"
TEST_DATE = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
TEST_TIME_SLOT = "10:00"

def test_appointment_scheduled():
    """Test notification when user schedules appointment"""
    print("\n=== TEST 1: Appointment Scheduled Notification ===")
    
    notification_data = {
        "type": "appointment_scheduled",
        "userName": TEST_USER_NAME,
        "date": TEST_DATE,
        "timeSlot": TEST_TIME_SLOT
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
            print(f"   Notification: '{TEST_USER_NAME} scheduled an appointment for {TEST_DATE} at {TEST_TIME_SLOT}'")
            return True
        else:
            print("❌ TEST 1 FAILED: Notification failed to send")
            return False
            
    except Exception as e:
        print(f"❌ TEST 1 ERROR: {e}")
        return False

def test_appointment_cancelled():
    """Test notification when user cancels appointment"""
    print("\n=== TEST 2: Appointment Cancelled Notification ===")
    
    notification_data = {
        "type": "appointment_cancelled",
        "userName": TEST_USER_NAME,
        "date": TEST_DATE,
        "timeSlot": TEST_TIME_SLOT
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
            print(f"   Notification: '{TEST_USER_NAME} cancelled appointment for {TEST_DATE} at {TEST_TIME_SLOT}'")
            return True
        else:
            print("❌ TEST 2 FAILED: Notification failed to send")
            return False
            
    except Exception as e:
        print(f"❌ TEST 2 ERROR: {e}")
        return False

def main():
    print("=" * 60)
    print("PUSH NOTIFICATION TESTING - APPOINTMENT NOTIFICATIONS")
    print("=" * 60)
    print(f"\nBackend URL: {BACKEND_URL}")
    print(f"Test User Name: {TEST_USER_NAME}")
    print(f"Test Date: {TEST_DATE}")
    print(f"Test Time Slot: {TEST_TIME_SLOT}")
    print("\n⚠️  IMPORTANT: Make sure you have:")
    print("1. Dietician account with push notification token")
    print("2. Dietician mobile device ready to receive notifications")
    print("3. Notifications enabled on dietician device")
    
    input("\nPress Enter to start testing...")
    
    # Run tests
    test1_result = test_appointment_scheduled()
    test2_result = test_appointment_cancelled()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Test 1 (Appointment Scheduled): {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Test 2 (Appointment Cancelled): {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

