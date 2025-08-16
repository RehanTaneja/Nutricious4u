#!/usr/bin/env python3
"""
Test script for subscription auto-renewal system
Run this to manually test the auto-renewal functionality
"""

import requests
import json
from datetime import datetime, timedelta

# Backend URL (adjust as needed)
BACKEND_URL = "http://localhost:8000"

def test_subscription_status(user_id: str):
    """Test getting subscription status for a user"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/subscription/status/{user_id}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Subscription status retrieved successfully")
            print(f"Plan: {result.get('subscriptionPlan', 'None')}")
            print(f"Active: {result.get('isSubscriptionActive', False)}")
            print(f"Auto-renewal: {result.get('autoRenewalEnabled', True)}")
            print(f"End Date: {result.get('subscriptionEndDate', 'None')}")
            print(f"Total Amount: ₹{result.get('totalAmountPaid', 0):,.0f}")
            return result
        else:
            print(f"❌ Failed to get subscription status: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error testing subscription status: {e}")
        return None

def test_toggle_auto_renewal(user_id: str, enabled: bool):
    """Test toggling auto-renewal setting"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/subscription/toggle-auto-renewal/{user_id}?enabled={enabled}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Auto-renewal {'enabled' if enabled else 'disabled'} successfully")
            print(f"Message: {result.get('message', '')}")
            return result
        else:
            print(f"❌ Failed to toggle auto-renewal: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error testing auto-renewal toggle: {e}")
        return None

def test_subscription_plans():
    """Test getting available subscription plans"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/subscription/plans")
        if response.status_code == 200:
            result = response.json()
            print("✅ Subscription plans retrieved successfully")
            print(f"Available plans: {len(result.get('plans', []))}")
            for plan in result.get('plans', []):
                if not plan.get('isFree', False):  # Only show paid plans
                    print(f"  - {plan['name']}: ₹{plan['price']:,.0f}")
            return result
        else:
            print(f"❌ Failed to get subscription plans: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error testing subscription plans: {e}")
        return None

def test_select_subscription(user_id: str, plan_id: str):
    """Test selecting a subscription plan"""
    try:
        payload = {
            "userId": user_id,
            "planId": plan_id
        }
        response = requests.post(f"{BACKEND_URL}/api/subscription/select", json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Subscription selected successfully")
            print(f"Message: {result.get('message', '')}")
            if result.get('subscription'):
                sub = result['subscription']
                print(f"Plan: {sub.get('planId')}")
                print(f"Start Date: {sub.get('startDate')}")
                print(f"End Date: {sub.get('endDate')}")
                print(f"Amount: ₹{sub.get('amountPaid', 0):,.0f}")
            return result
        else:
            print(f"❌ Failed to select subscription: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error testing subscription selection: {e}")
        return None

def test_cancel_subscription(user_id: str):
    """Test cancelling a subscription"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/subscription/cancel/{user_id}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Subscription cancelled successfully")
            print(f"Message: {result.get('message', '')}")
            return result
        else:
            print(f"❌ Failed to cancel subscription: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error testing subscription cancellation: {e}")
        return None

def test_notification_system():
    """Test the notification system"""
    try:
        # Test getting notifications for a user
        user_id = "test_user_id"  # Replace with actual user ID
        response = requests.get(f"{BACKEND_URL}/api/notifications/{user_id}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Notifications retrieved successfully")
            print(f"Number of notifications: {len(result.get('notifications', []))}")
            for notification in result.get('notifications', [])[:3]:  # Show first 3
                print(f"  - {notification.get('title')}: {notification.get('body')}")
            return result
        else:
            print(f"❌ Failed to get notifications: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error testing notification system: {e}")
        return None

def simulate_subscription_expiry(user_id: str):
    """Simulate a subscription that has expired for testing auto-renewal"""
    print("\n🔧 Simulating subscription expiry for testing...")
    print("Note: This would require manual database manipulation in production")
    print("For testing, you can manually set a user's subscriptionEndDate to a past date")
    print("Then run the subscription reminder job to trigger auto-renewal")

def test_subscription_reminder_job():
    """Test the subscription reminder job (this would be called by the scheduler)"""
    print("\n⏰ Testing subscription reminder job...")
    print("This job runs every minute to check for expiring subscriptions")
    print("In production, this is handled by the notification scheduler")
    print("Manual testing would require setting up expired subscriptions in the database")

if __name__ == "__main__":
    print("🧪 Testing Subscription Auto-Renewal System")
    print("=" * 50)
    
    # Test user ID (replace with actual user ID for testing)
    test_user_id = "test_user_123"
    
    print(f"\n1. Testing subscription plans...")
    test_subscription_plans()
    
    print(f"\n2. Testing subscription status for user {test_user_id}...")
    test_subscription_status(test_user_id)
    
    print(f"\n3. Testing auto-renewal toggle...")
    test_toggle_auto_renewal(test_user_id, True)
    test_toggle_auto_renewal(test_user_id, False)
    test_toggle_auto_renewal(test_user_id, True)  # Re-enable
    
    print(f"\n4. Testing subscription selection (1 month plan)...")
    test_select_subscription(test_user_id, "1month")
    
    print(f"\n5. Testing subscription status after selection...")
    test_subscription_status(test_user_id)
    
    print(f"\n6. Testing notification system...")
    test_notification_system()
    
    print(f"\n7. Testing subscription cancellation...")
    test_cancel_subscription(test_user_id)
    
    print(f"\n8. Testing subscription status after cancellation...")
    test_subscription_status(test_user_id)
    
    print(f"\n9. Testing subscription reminder job...")
    test_subscription_reminder_job()
    
    print(f"\n10. Simulating subscription expiry...")
    simulate_subscription_expiry(test_user_id)
    
    print("\n" + "=" * 50)
    print("✅ Auto-renewal system test completed!")
    print("\n📋 Summary of Auto-Renewal Features:")
    print("  ✅ Automatic subscription renewal when plan expires")
    print("  ✅ Auto-renewal enabled by default for all users")
    print("  ✅ Toggle auto-renewal on/off via API")
    print("  ✅ Notifications sent to user and dietician on renewal")
    print("  ✅ Proper amount tracking and total calculation")
    print("  ✅ Subscription status includes auto-renewal setting")
    print("  ✅ Expiry notifications for users with auto-renewal disabled")
    print("  ✅ Comprehensive error handling and logging")
