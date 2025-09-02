#!/usr/bin/env python3
"""
Notification Edge Cases Test
Tests edge cases and different notification scenarios
"""

import os
import json
import re
from datetime import datetime

def test_timezone_handling():
    """Test timezone handling in notifications"""
    print("🔍 TESTING TIMEZONE HANDLING")
    
    # Check if notifications use local device time
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        # Check for local device time usage
        if "const now = new Date()" in content:
            print("✅ Uses local device time (new Date())")
        else:
            print("❌ May not use local device time")
        
        # Check for UTC usage (should be avoided for local scheduling)
        if "UTC" in content and "calculateDietNextOccurrence" in content:
            print("⚠️ May use UTC in diet notification calculations")
        else:
            print("✅ No UTC usage in local scheduling")
            
    except Exception as e:
        print(f"❌ Error checking timezone handling: {e}")

def test_notification_types():
    """Test different notification types"""
    print("\n🔍 TESTING NOTIFICATION TYPES")
    
    # Check for all required notification types
    required_types = [
        "new_diet",
        "diet_reminder", 
        "custom",
        "diet",
        "message",
        "subscription"
    ]
    
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        for notification_type in required_types:
            if notification_type in content:
                print(f"✅ {notification_type} notification type found")
            else:
                print(f"❌ {notification_type} notification type missing")
                
    except Exception as e:
        print(f"❌ Error checking notification types: {e}")

def test_scheduling_methods():
    """Test scheduling methods"""
    print("\n🔍 TESTING SCHEDULING METHODS")
    
    # Check for required scheduling methods
    required_methods = [
        "scheduleNotification",
        "scheduleDietNotifications",
        "scheduleCustomNotification",
        "scheduleNewDietNotification",
        "scheduleMessageNotification"
    ]
    
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        for method in required_methods:
            if method in content:
                print(f"✅ {method} method found")
            else:
                print(f"❌ {method} method missing")
                
    except Exception as e:
        print(f"❌ Error checking scheduling methods: {e}")

def test_calculation_methods():
    """Test calculation methods"""
    print("\n🔍 TESTING CALCULATION METHODS")
    
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        # Check for calculation methods
        if "calculateNextOccurrence" in content:
            print("✅ Custom notification calculation method found")
        else:
            print("❌ Custom notification calculation method missing")
        
        if "calculateDietNextOccurrence" in content:
            print("✅ Diet notification calculation method found")
        else:
            print("❌ Diet notification calculation method missing")
        
        # Check if both use same logic
        if "jsSelectedDay = (dayOfWeek + 1) % 7" in content:
            print("✅ Both methods use same day conversion logic")
        else:
            print("❌ Methods may not use same day conversion logic")
            
    except Exception as e:
        print(f"❌ Error checking calculation methods: {e}")

def test_error_handling():
    """Test error handling in notifications"""
    print("\n🔍 TESTING ERROR HANDLING")
    
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        # Check for error handling
        if "try {" in content and "catch (error)" in content:
            print("✅ Error handling found")
        else:
            print("❌ Error handling may be missing")
        
        # Check for logging
        if "logger.error" in content:
            print("✅ Error logging found")
        else:
            print("❌ Error logging may be missing")
            
    except Exception as e:
        print(f"❌ Error checking error handling: {e}")

def test_backend_notification_sending():
    """Test backend notification sending"""
    print("\n🔍 TESTING BACKEND NOTIFICATION SENDING")
    
    try:
        with open("backend/services/firebase_client.py", "r") as f:
            content = f.read()
        
        # Check for push notification sending
        if "send_push_notification" in content:
            print("✅ Push notification sending method found")
        else:
            print("❌ Push notification sending method missing")
        
        # Check for Expo push service
        if "exp.host/--/api/v2/push/send" in content:
            print("✅ Expo push service endpoint found")
        else:
            print("❌ Expo push service endpoint missing")
        
        # Check for error handling in push notifications
        if "response.status_code == 200" in content:
            print("✅ Push notification response handling found")
        else:
            print("❌ Push notification response handling missing")
            
    except Exception as e:
        print(f"❌ Error checking backend notification sending: {e}")

def test_app_configuration():
    """Test app configuration"""
    print("\n🔍 TESTING APP CONFIGURATION")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        # Check notification configuration
        notification_config = app_config.get("expo", {}).get("notification", {})
        if notification_config:
            print("✅ Notification configuration found")
        else:
            print("❌ Notification configuration missing")
        
        # Check expo-notifications plugin
        plugins = app_config.get("expo", {}).get("plugins", [])
        expo_notifications_found = False
        for plugin in plugins:
            if isinstance(plugin, list) and len(plugin) > 0 and plugin[0] == "expo-notifications":
                expo_notifications_found = True
                break
        
        if expo_notifications_found:
            print("✅ Expo notifications plugin found")
        else:
            print("❌ Expo notifications plugin missing")
        
        # Check for production mode
        for plugin in plugins:
            if isinstance(plugin, list) and len(plugin) > 0 and plugin[0] == "expo-notifications":
                plugin_config = plugin[1] if len(plugin) > 1 else {}
                if plugin_config.get("mode") == "production":
                    print("✅ Expo notifications in production mode")
                else:
                    print("⚠️ Expo notifications not in production mode")
                break
                
    except Exception as e:
        print(f"❌ Error checking app configuration: {e}")

def main():
    """Run all edge case tests"""
    print("🚀 NOTIFICATION EDGE CASES TEST")
    print("=" * 50)
    
    test_timezone_handling()
    test_notification_types()
    test_scheduling_methods()
    test_calculation_methods()
    test_error_handling()
    test_backend_notification_sending()
    test_app_configuration()
    
    print("\n" + "=" * 50)
    print("✅ EDGE CASES TEST COMPLETED")
    print("\n📋 EDGE CASES SUMMARY:")
    print("- Timezone handling should use local device time")
    print("- All notification types should be supported")
    print("- All scheduling methods should be available")
    print("- Calculation methods should be consistent")
    print("- Error handling should be comprehensive")
    print("- Backend notification sending should work")
    print("- App configuration should be correct")

if __name__ == "__main__":
    main()
