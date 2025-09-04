#!/usr/bin/env python3
"""
Test script for notification scheduling system
Tests the automatic scheduling of diet notifications
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.notification_scheduler_simple import get_simple_notification_scheduler
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    """Initialize Firebase for testing"""
    try:
        # Try to get default app
        firebase_admin.get_app()
    except ValueError:
        # Initialize if not already done
        cred = credentials.Certificate("google-services.json")
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

async def test_notification_scheduling():
    """Test the notification scheduling system"""
    print("🧪 Testing Notification Scheduling System...")
    
    try:
        # Initialize Firebase
        db = initialize_firebase()
        print("✅ Firebase initialized")
        
        # Get scheduler
        scheduler = get_simple_notification_scheduler(db)
        print("✅ Scheduler initialized")
        
        # Test user ID (replace with actual user ID for testing)
        test_user_id = "test_user_123"
        
        print(f"🔍 Testing notification scheduling for user: {test_user_id}")
        
        # Test scheduling
        scheduled_count = await scheduler.schedule_user_notifications(test_user_id)
        print(f"📅 Scheduled {scheduled_count} notifications")
        
        # Test sending due notifications
        print("📤 Testing due notification sending...")
        sent_count = await scheduler.send_due_notifications()
        print(f"📨 Sent {sent_count} due notifications")
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Notification Scheduling Tests...")
    asyncio.run(test_notification_scheduling())
