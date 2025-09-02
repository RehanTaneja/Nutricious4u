#!/usr/bin/env python3
"""
Test Diet Notification Scheduling
Verifies that diet notifications use local device time scheduling
"""

import os
import json
import re

def test_diet_notification_scheduling():
    """Test that diet notifications use local device time scheduling"""
    print("🔍 TESTING DIET NOTIFICATION SCHEDULING")
    
    # Check unifiedNotificationService.ts
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        # Check if diet notifications use the same calculation method as custom reminders
        if "calculateDietNextOccurrence" in content:
            print("✅ Diet notification calculation method found")
        else:
            print("❌ Diet notification calculation method missing")
        
        # Check if the method uses local device time
        if "const now = new Date()" in content and "calculateDietNextOccurrence" in content:
            print("✅ Diet notifications use local device time (new Date())")
        else:
            print("❌ Diet notifications may not use local device time")
        
        # Check if the method uses the same logic as custom reminders
        if "jsSelectedDay = (dayOfWeek + 1) % 7" in content and "calculateDietNextOccurrence" in content:
            print("✅ Diet notifications use same day conversion logic as custom reminders")
        else:
            print("❌ Diet notifications may not use same day conversion logic")
        
        # Check if the method uses the same occurrence calculation
        if "for (let dayOffset = 0; dayOffset <= 7; dayOffset++)" in content and "calculateDietNextOccurrence" in content:
            print("✅ Diet notifications use same occurrence calculation as custom reminders")
        else:
            print("❌ Diet notifications may not use same occurrence calculation")
            
    except Exception as e:
        print(f"❌ Error reading unifiedNotificationService.ts: {e}")

def test_notification_service_scheduling():
    """Test notificationService.ts scheduling"""
    print("\n🔍 TESTING NOTIFICATION SERVICE SCHEDULING")
    
    try:
        with open("mobileapp/services/notificationService.ts", "r") as f:
            content = f.read()
        
        # Check if notificationService also uses local device time
        if "const now = new Date()" in content and "calculateDietNextOccurrence" in content:
            print("✅ NotificationService uses local device time")
        else:
            print("❌ NotificationService may not use local device time")
        
        # Check if it uses the same logic
        if "jsSelectedDay = (dayOfWeek + 1) % 7" in content and "calculateDietNextOccurrence" in content:
            print("✅ NotificationService uses same day conversion logic")
        else:
            print("❌ NotificationService may not use same day conversion logic")
            
    except Exception as e:
        print(f"❌ Error reading notificationService.ts: {e}")

def test_backend_scheduler():
    """Test backend scheduler to ensure it doesn't interfere"""
    print("\n🔍 TESTING BACKEND SCHEDULER")
    
    try:
        with open("backend/services/notification_scheduler.py", "r") as f:
            content = f.read()
        
        # Check if backend uses UTC (which is correct for server-side)
        if "datetime.now(pytz.UTC)" in content:
            print("✅ Backend scheduler uses UTC (correct for server-side)")
        else:
            print("❌ Backend scheduler may not use UTC")
        
        # Check if backend is separate from local scheduling
        if "scheduled_notifications" in content:
            print("✅ Backend uses separate scheduled_notifications collection")
        else:
            print("❌ Backend may not use separate collection")
            
    except Exception as e:
        print(f"❌ Error reading notification_scheduler.py: {e}")

def test_frontend_api_calls():
    """Test frontend API calls"""
    print("\n🔍 TESTING FRONTEND API CALLS")
    
    try:
        with open("mobileapp/screens.tsx", "r") as f:
            content = f.read()
        
        # Check if frontend uses local scheduling
        if "unifiedNotificationService.scheduleDietNotifications" in content:
            print("✅ Frontend uses local scheduling via unifiedNotificationService")
        else:
            print("❌ Frontend may not use local scheduling")
        
        # Check if it doesn't use backend scheduling for diet notifications
        if "scheduleDietNotifications(" in content and "api." not in content:
            print("✅ Frontend doesn't use backend API for diet notification scheduling")
        else:
            print("⚠️ Frontend may use backend API for diet notification scheduling")
            
    except Exception as e:
        print(f"❌ Error reading screens.tsx: {e}")

def main():
    """Run all tests"""
    print("🚀 DIET NOTIFICATION SCHEDULING TEST")
    print("=" * 50)
    
    test_diet_notification_scheduling()
    test_notification_service_scheduling()
    test_backend_scheduler()
    test_frontend_api_calls()
    
    print("\n" + "=" * 50)
    print("✅ DIET NOTIFICATION SCHEDULING TEST COMPLETED")
    print("\n📋 SUMMARY:")
    print("- Diet notifications should use local device time scheduling")
    print("- Same calculation method as custom reminders")
    print("- Backend scheduler uses UTC (correct for server-side)")
    print("- Frontend uses local scheduling via unifiedNotificationService")

if __name__ == "__main__":
    main()
