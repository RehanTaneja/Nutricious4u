#!/usr/bin/env python3
"""
Comprehensive Test Suite for Subscription Cancellation and Automatic Renewal
Tests the complete flow including diet notification cancellation and automatic renewal
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configuration
BACKEND_URL = "https://nutricious4u-production.up.railway.app"
TEST_USER_ID = "test_user_subscription_cancellation"

def log_test(test_name: str, status: str, details: str = ""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")

def test_backend_connection():
    """Test if backend is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            log_test("Backend Connection", "PASS", "Backend is accessible")
            return True
        else:
            log_test("Backend Connection", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Backend Connection", "FAIL", f"Error: {e}")
        return False

def create_test_user():
    """Create a test user with subscription"""
    try:
        # Create user profile with active subscription
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "isSubscriptionActive": True,
            "subscriptionPlan": "3months",
            "subscriptionStartDate": datetime.now().isoformat(),
            "subscriptionEndDate": (datetime.now() + timedelta(days=90)).isoformat(),
            "currentSubscriptionAmount": 12000.0,
            "totalAmountPaid": 12000.0,
            "autoRenewalEnabled": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/users/{TEST_USER_ID}/profile",
            json=user_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            log_test("Create Test User", "PASS", "Test user created with active subscription")
            return True
        else:
            log_test("Create Test User", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        log_test("Create Test User", "FAIL", f"Error: {e}")
        return False

def test_subscription_status():
    """Test getting subscription status"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/subscription/status/{TEST_USER_ID}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test("Get Subscription Status", "PASS", f"Status: {data.get('isSubscriptionActive')}, Plan: {data.get('subscriptionPlan')}")
            return data
        else:
            log_test("Get Subscription Status", "FAIL", f"Status code: {response.status_code}")
            return None
    except Exception as e:
        log_test("Get Subscription Status", "FAIL", f"Error: {e}")
        return None

def create_test_diet_notifications():
    """Create test diet notifications for the user"""
    try:
        # Create some test notifications
        notifications = [
            {
                "title": "Breakfast Reminder",
                "body": "Time for breakfast!",
                "scheduledTime": (datetime.now() + timedelta(hours=1)).isoformat(),
                "type": "diet"
            },
            {
                "title": "Lunch Reminder", 
                "body": "Time for lunch!",
                "scheduledTime": (datetime.now() + timedelta(hours=5)).isoformat(),
                "type": "diet"
            },
            {
                "title": "Dinner Reminder",
                "body": "Time for dinner!",
                "scheduledTime": (datetime.now() + timedelta(hours=10)).isoformat(),
                "type": "diet"
            }
        ]
        
        response = requests.post(
            f"{BACKEND_URL}/api/users/{TEST_USER_ID}/diet/notifications/schedule",
            json={"notifications": notifications},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test("Create Diet Notifications", "PASS", f"Created {len(notifications)} notifications")
            return True
        else:
            log_test("Create Diet Notifications", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        log_test("Create Diet Notifications", "FAIL", f"Error: {e}")
        return False

def test_subscription_cancellation():
    """Test subscription cancellation with diet notification cancellation"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/subscription/cancel/{TEST_USER_ID}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                cancelled_count = data.get("cancelled_notifications", 0)
                log_test("Cancel Subscription", "PASS", f"Success: {data.get('message')}, Cancelled notifications: {cancelled_count}")
                return data
            else:
                log_test("Cancel Subscription", "FAIL", f"Success: False, Message: {data.get('message')}")
                return None
        else:
            log_test("Cancel Subscription", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_test("Cancel Subscription", "FAIL", f"Error: {e}")
        return None

def verify_subscription_cancelled():
    """Verify that subscription is actually cancelled"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/subscription/status/{TEST_USER_ID}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if not data.get("isSubscriptionActive"):
                log_test("Verify Subscription Cancelled", "PASS", "Subscription is inactive")
                return True
            else:
                log_test("Verify Subscription Cancelled", "FAIL", "Subscription is still active")
                return False
        else:
            log_test("Verify Subscription Cancelled", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Verify Subscription Cancelled", "FAIL", f"Error: {e}")
        return False

def test_automatic_renewal():
    """Test automatic renewal functionality"""
    try:
        # Create a user with expired subscription but auto-renewal enabled
        expired_user_id = "test_user_expired_renewal"
        
        # Create user with expired subscription
        user_data = {
            "name": "Expired User",
            "email": "expired@example.com",
            "isSubscriptionActive": True,
            "subscriptionPlan": "3months",
            "subscriptionStartDate": (datetime.now() - timedelta(days=95)).isoformat(),
            "subscriptionEndDate": (datetime.now() - timedelta(days=5)).isoformat(),  # Expired 5 days ago
            "currentSubscriptionAmount": 12000.0,
            "totalAmountPaid": 12000.0,
            "autoRenewalEnabled": True
        }
        
        # Create the expired user
        response = requests.post(
            f"{BACKEND_URL}/api/users/{expired_user_id}/profile",
            json=user_data,
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            log_test("Create Expired User", "FAIL", f"Status code: {response.status_code}")
            return False
        
        log_test("Create Expired User", "PASS", "Created user with expired subscription")
        
        # Trigger the subscription reminder job (which handles auto-renewal)
        response = requests.post(f"{BACKEND_URL}/api/admin/trigger-subscription-reminder-job", timeout=30)
        
        if response.status_code == 200:
            log_test("Trigger Auto-Renewal", "PASS", "Auto-renewal job triggered successfully")
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Check if subscription was renewed
            response = requests.get(f"{BACKEND_URL}/api/subscription/status/{expired_user_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("isSubscriptionActive"):
                    end_date = data.get("subscriptionEndDate")
                    if end_date:
                        end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        if end_date_obj > datetime.now():
                            log_test("Verify Auto-Renewal", "PASS", f"Subscription renewed, new end date: {end_date}")
                            return True
                        else:
                            log_test("Verify Auto-Renewal", "FAIL", "Subscription not renewed properly")
                            return False
                    else:
                        log_test("Verify Auto-Renewal", "FAIL", "No end date found")
                        return False
                else:
                    log_test("Verify Auto-Renewal", "FAIL", "Subscription is not active")
                    return False
            else:
                log_test("Verify Auto-Renewal", "FAIL", f"Status code: {response.status_code}")
                return False
        else:
            log_test("Trigger Auto-Renewal", "FAIL", f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Test Automatic Renewal", "FAIL", f"Error: {e}")
        return False

def test_push_notifications():
    """Test push notification functionality"""
    try:
        # Test sending a test notification
        response = requests.post(
            f"{BACKEND_URL}/api/users/{TEST_USER_ID}/diet/notifications/test",
            timeout=10
        )
        
        if response.status_code == 200:
            log_test("Test Push Notifications", "PASS", "Test notification sent successfully")
            return True
        else:
            log_test("Test Push Notifications", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Test Push Notifications", "FAIL", f"Error: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    try:
        # Delete test users
        test_users = [TEST_USER_ID, "test_user_expired_renewal"]
        
        for user_id in test_users:
            try:
                response = requests.delete(f"{BACKEND_URL}/api/users/{user_id}/profile", timeout=10)
                if response.status_code in [200, 404]:  # 404 is OK if user doesn't exist
                    log_test(f"Cleanup User {user_id}", "PASS", "User deleted")
                else:
                    log_test(f"Cleanup User {user_id}", "FAIL", f"Status code: {response.status_code}")
            except Exception as e:
                log_test(f"Cleanup User {user_id}", "FAIL", f"Error: {e}")
        
        log_test("Cleanup Test Data", "PASS", "Test data cleanup completed")
        return True
    except Exception as e:
        log_test("Cleanup Test Data", "FAIL", f"Error: {e}")
        return False

def run_comprehensive_test():
    """Run the complete test suite"""
    print("🧪 Starting Comprehensive Subscription Cancellation and Renewal Test")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Backend Connection
    test_results.append(test_backend_connection())
    
    # Test 2: Create Test User
    test_results.append(create_test_user())
    
    # Test 3: Get Subscription Status
    test_results.append(test_subscription_status() is not None)
    
    # Test 4: Create Diet Notifications
    test_results.append(create_test_diet_notifications())
    
    # Test 5: Cancel Subscription (with diet notification cancellation)
    cancellation_result = test_subscription_cancellation()
    test_results.append(cancellation_result is not None)
    
    # Test 6: Verify Subscription Cancelled
    test_results.append(verify_subscription_cancelled())
    
    # Test 7: Test Automatic Renewal
    test_results.append(test_automatic_renewal())
    
    # Test 8: Test Push Notifications
    test_results.append(test_push_notifications())
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Subscription cancellation and renewal system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
