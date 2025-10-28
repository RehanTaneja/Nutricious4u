#!/usr/bin/env python3
"""
Test script for push notification system - Diet Countdown Notifications
Tests:
1. Manually trigger diet countdown check
2. Verify dietician receives notifications for users with 1 day left
"""

import requests
import json
import sys
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore

# Backend URL
BACKEND_URL = "https://nutricious4u-production.up.railway.app"

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        cred = credentials.Certificate("backend/services/firebase_service_account.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
        return firestore.client()
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        return None

def create_test_user_with_1_day_left(db):
    """Create or update a test user with 1 day left in diet"""
    print("\n=== Setting up test user with 1 day left ===")
    
    test_user_id = "test_diet_countdown_user"
    
    # Calculate last upload date (6 days ago, so 1 day left in 7-day cycle)
    six_days_ago = datetime.now(timezone.utc) - timedelta(days=6)
    last_upload = six_days_ago.isoformat()
    
    user_data = {
        "firstName": "Test",
        "lastName": "Countdown User",
        "email": "test_countdown@example.com",
        "lastDietUpload": last_upload,
        "isDietician": False
    }
    
    try:
        db.collection("user_profiles").document(test_user_id).set(user_data, merge=True)
        print(f"✅ Test user created/updated: {test_user_id}")
        print(f"   Last upload: {last_upload}")
        print(f"   Days left: ~1 day")
        return test_user_id
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return None

def trigger_diet_countdown_job():
    """Manually trigger the diet countdown scheduled job"""
    print("\n=== TEST: Triggering Diet Countdown Job ===")
    
    # Note: This requires the scheduled job to be running
    # For testing, we'll simulate by calling the backend directly
    
    print("⚠️  This test requires the backend scheduled job to be running")
    print("   The job runs every 6 hours automatically")
    print("   To test immediately, you can:")
    print("   1. Restart the backend server (job runs on startup)")
    print("   2. Wait for the next scheduled run")
    print("   3. Manually check backend logs for '[DIET COUNTDOWN]' entries")
    
    return True

def verify_notification_sent():
    """Verify that notification was sent to dietician"""
    print("\n=== Verification Steps ===")
    print("1. Check dietician mobile device for notification")
    print("2. Notification should say: 'Test Countdown User has 1 day left in their diet plan'")
    print("3. Notification should have title: 'Diet Expiring Soon ⏰'")
    print("\nDid you receive the notification? (y/n): ", end='')
    
    response = input().strip().lower()
    return response == 'y'

def main():
    print("=" * 60)
    print("PUSH NOTIFICATION TESTING - DIET COUNTDOWN")
    print("=" * 60)
    print(f"\nBackend URL: {BACKEND_URL}")
    print("\n⚠️  IMPORTANT: Make sure you have:")
    print("1. Firebase service account JSON file in backend/services/")
    print("2. Dietician account with push notification token")
    print("3. Dietician mobile device ready to receive notifications")
    print("4. Backend server running with scheduled job enabled")
    
    input("\nPress Enter to start testing...")
    
    # Initialize Firebase
    db = init_firebase()
    if not db:
        print("\n❌ Cannot proceed without Firebase connection")
        return 1
    
    # Create test user
    test_user_id = create_test_user_with_1_day_left(db)
    if not test_user_id:
        print("\n❌ Failed to create test user")
        return 1
    
    # Trigger job (manually or wait for scheduled run)
    trigger_diet_countdown_job()
    
    print("\n⏳ Waiting for notification...")
    print("   (This may take a few moments)")
    input("\nPress Enter after you've checked for the notification...")
    
    # Verify
    notification_received = verify_notification_sent()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Test User Created: ✅ {test_user_id}")
    print(f"Notification Received: {'✅ YES' if notification_received else '❌ NO'}")
    
    if notification_received:
        print("\n✅ TEST PASSED!")
        return 0
    else:
        print("\n❌ TEST FAILED")
        print("\nTroubleshooting:")
        print("1. Check backend logs for '[DIET COUNTDOWN]' entries")
        print("2. Verify dietician has push notification token")
        print("3. Ensure scheduled job is running (check server startup logs)")
        return 1

if __name__ == "__main__":
    sys.exit(main())

