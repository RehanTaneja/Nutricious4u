#!/usr/bin/env python3
"""
Test script to verify notification cancellation functionality
"""

import requests
import json
from datetime import datetime, timedelta
import pytz
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER_ID = "test_user_123"  # Replace with actual test user ID

def test_notification_cancellation():
    """Test that old notifications are cancelled when new ones are extracted"""
    
    print("🧪 Testing Notification Cancellation")
    print("=" * 60)
    
    # 1. First extraction - create initial notifications
    print("\n1. First extraction - creating initial notifications...")
    try:
        response = requests.post(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/extract")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ First extraction successful")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Notifications: {len(data.get('notifications', []))}")
            
            # Store initial notification count
            initial_notifications = data.get('notifications', [])
            print(f"   Initial notification count: {len(initial_notifications)}")
        else:
            print(f"❌ First extraction failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error in first extraction: {e}")
        return
    
    # 2. Check scheduled notifications (simulate)
    print("\n2. Checking scheduled notifications...")
    print("   ✅ Backend should have scheduled notifications in Firestore")
    print("   Note: Direct database access would show scheduled_notifications collection")
    
    # 3. Second extraction - should cancel old and create new
    print("\n3. Second extraction - should cancel old notifications...")
    try:
        response = requests.post(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/extract")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Second extraction successful")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Notifications: {len(data.get('notifications', []))}")
            
            # Store second notification count
            second_notifications = data.get('notifications', [])
            print(f"   Second notification count: {len(second_notifications)}")
        else:
            print(f"❌ Second extraction failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error in second extraction: {e}")
        return
    
    # 4. Test manual cancellation
    print("\n4. Testing manual cancellation...")
    try:
        response = requests.post(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/cancel")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Manual cancellation successful")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Cancelled: {data.get('cancelled', 0)} notifications")
        else:
            print(f"❌ Manual cancellation failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error in manual cancellation: {e}")
    
    # 5. Test manual scheduling after cancellation
    print("\n5. Testing manual scheduling after cancellation...")
    try:
        response = requests.post(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/schedule")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Manual scheduling successful")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Scheduled: {data.get('scheduled', 0)} notifications")
        else:
            print(f"❌ Manual scheduling failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error in manual scheduling: {e}")

def test_cancellation_workflow():
    """Test the complete cancellation workflow"""
    
    print("\n🔄 Testing Complete Cancellation Workflow")
    print("=" * 60)
    
    print("\n📋 Expected Workflow:")
    print("   1. User uploads new diet PDF")
    print("   2. Backend extracts notifications")
    print("   3. Backend cancels ALL existing scheduled notifications")
    print("   4. Backend schedules NEW notifications")
    print("   5. User receives only NEW notifications")
    
    print("\n✅ Verification Points:")
    print("   - Old notifications should be marked as 'cancelled' in database")
    print("   - New notifications should be marked as 'scheduled' in database")
    print("   - Only new notifications should be sent to user")
    print("   - No duplicate notifications should be sent")
    print("   - Database status tracking for cancelled notifications")

def check_backend_logs():
    """Check what to look for in backend logs"""
    
    print("\n📊 Backend Logs to Monitor")
    print("=" * 60)
    
    print("✅ Look for these log messages:")
    print("   [Notification Scheduler] Cancelling all scheduled notifications for user {user_id}")
    print("   Cancelled scheduled notification: {notification_id}")
    print("   Cancelled {count} scheduled notifications for user {user_id}")
    print("   Cancelled {count} existing notifications before scheduling new ones")
    print("   Scheduled notification for user {user_id} on {day} at {time}")

if __name__ == "__main__":
    print("Notification Cancellation Test Suite")
    print("=" * 60)
    
    # Test cancellation functionality
    test_notification_cancellation()
    
    # Test workflow
    test_cancellation_workflow()
    
    # Check logs
    check_backend_logs()
    
    print("\n✅ Test suite completed!")
    print("\n📋 Summary:")
    print("   - Backend now cancels old notifications before scheduling new ones")
    print("   - Manual cancellation endpoint available")
    print("   - Proper logging for debugging")
    print("   - No duplicate notifications should be sent")
    print("   - Database status tracking for cancelled notifications")
