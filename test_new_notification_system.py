#!/usr/bin/env python3
"""
Test Script for New Simple Notification System
Tests all notification types and verifies the system works correctly.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_notification_system():
    """Test the new simple notification system"""
    print("=" * 80)
    print("🧪 TESTING NEW SIMPLE NOTIFICATION SYSTEM")
    print("=" * 80)
    
    # Test configuration
    BASE_URL = "http://localhost:8000/api"
    TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"  # Replace with actual user ID
    TEST_DIETICIAN_ID = "mBVlWBBpoaXyOVr8Y4AoHZunq9f1"  # Replace with actual dietician ID
    
    print(f"\n📋 TEST CONFIGURATION:")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Test Dietician ID: {TEST_DIETICIAN_ID}")
    
    # Test results
    results = {
        "test_notification": {"status": "pending", "details": []},
        "new_diet_notification": {"status": "pending", "details": []},
        "message_notification": {"status": "pending", "details": []},
        "appointment_notification": {"status": "pending", "details": []},
        "diet_reminder_notification": {"status": "pending", "details": []}
    }
    
    def log_test(test_name, message, is_success=True):
        """Log test result"""
        status = "✅" if is_success else "❌"
        print(f"{status} {test_name}: {message}")
        results[test_name]["details"].append(f"{status} {message}")
    
    def test_endpoint(endpoint, data=None, method="GET"):
        """Test an API endpoint"""
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=10)
            
            return response.status_code, response.json() if response.content else {}
        except requests.exceptions.ConnectionError:
            return None, {"error": "Connection failed - is the server running?"}
        except Exception as e:
            return None, {"error": str(e)}
    
    # Test 1: Test Notification Endpoint
    print(f"\n🧪 TEST 1: Testing notification endpoint")
    print("-" * 50)
    
    status_code, response = test_endpoint(f"/notifications/test/{TEST_USER_ID}")
    if status_code == 200:
        log_test("test_notification", f"Test notification sent successfully: {response}")
        results["test_notification"]["status"] = "passed"
    else:
        log_test("test_notification", f"Test notification failed: {response}", False)
        results["test_notification"]["status"] = "failed"
    
    # Test 2: New Diet Notification
    print(f"\n🧪 TEST 2: Testing new diet notification")
    print("-" * 50)
    
    new_diet_data = {
        "recipientId": TEST_USER_ID,
        "type": "new_diet",
        "dieticianName": "Dr. Smith"
    }
    
    status_code, response = test_endpoint("/notifications/send", new_diet_data, "POST")
    if status_code == 200 and response.get("success"):
        log_test("new_diet_notification", f"New diet notification sent successfully: {response}")
        results["new_diet_notification"]["status"] = "passed"
    else:
        log_test("new_diet_notification", f"New diet notification failed: {response}", False)
        results["new_diet_notification"]["status"] = "failed"
    
    # Test 3: Message Notification
    print(f"\n🧪 TEST 3: Testing message notification")
    print("-" * 50)
    
    message_data = {
        "recipientId": TEST_USER_ID,
        "type": "message",
        "senderName": "Dr. Smith",
        "message": "Hello! How are you feeling today?",
        "isDietician": True
    }
    
    status_code, response = test_endpoint("/notifications/send", message_data, "POST")
    if status_code == 200 and response.get("success"):
        log_test("message_notification", f"Message notification sent successfully: {response}")
        results["message_notification"]["status"] = "passed"
    else:
        log_test("message_notification", f"Message notification failed: {response}", False)
        results["message_notification"]["status"] = "failed"
    
    # Test 4: Appointment Notification
    print(f"\n🧪 TEST 4: Testing appointment notification")
    print("-" * 50)
    
    appointment_data = {
        "recipientId": TEST_USER_ID,
        "type": "appointment",
        "appointmentType": "scheduled",
        "appointmentDate": "2025-10-10",
        "timeSlot": "10:00 AM"
    }
    
    status_code, response = test_endpoint("/notifications/send", appointment_data, "POST")
    if status_code == 200 and response.get("success"):
        log_test("appointment_notification", f"Appointment notification sent successfully: {response}")
        results["appointment_notification"]["status"] = "passed"
    else:
        log_test("appointment_notification", f"Appointment notification failed: {response}", False)
        results["appointment_notification"]["status"] = "failed"
    
    # Test 5: Diet Reminder Notification
    print(f"\n🧪 TEST 5: Testing diet reminder notification")
    print("-" * 50)
    
    diet_reminder_data = {
        "recipientId": TEST_USER_ID,
        "type": "diet_reminder",
        "userName": "John Doe"
    }
    
    status_code, response = test_endpoint("/notifications/send", diet_reminder_data, "POST")
    if status_code == 200 and response.get("success"):
        log_test("diet_reminder_notification", f"Diet reminder notification sent successfully: {response}")
        results["diet_reminder_notification"]["status"] = "passed"
    else:
        log_test("diet_reminder_notification", f"Diet reminder notification failed: {response}", False)
        results["diet_reminder_notification"]["status"] = "failed"
    
    # Summary
    print(f"\n📊 TEST SUMMARY:")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = result["status"]
        status_icon = "✅" if status == "passed" else "❌"
        print(f"{status_icon} {test_name.replace('_', ' ').title()}: {status.upper()}")
        
        if status == "passed":
            passed_tests += 1
        
        # Show details
        for detail in result["details"]:
            print(f"   {detail}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! The new notification system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the server logs and configuration.")
        return False

if __name__ == "__main__":
    success = test_notification_system()
    sys.exit(0 if success else 1)
