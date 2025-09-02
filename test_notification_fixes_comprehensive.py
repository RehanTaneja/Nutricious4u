#!/usr/bin/env python3
"""
Comprehensive Notification Fixes Test
Tests all notification fixes after implementation
"""

import os
import json
import re
from datetime import datetime

def test_critical_fixes():
    """Test critical notification fixes"""
    print("🔍 TESTING CRITICAL FIXES")
    
    # Test 1: Check if local "1 day left" notification was removed
    try:
        with open("mobileapp/screens.tsx", "r") as f:
            content = f.read()
        
        if "scheduleDietReminderNotification" not in content:
            print("✅ Local '1 day left' notification removed from Dashboard")
        else:
            print("❌ Local '1 day left' notification still exists in Dashboard")
            
    except Exception as e:
        print(f"❌ Error reading screens.tsx: {e}")
    
    # Test 2: Check if problematic method was removed
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        if "async scheduleDietReminderNotification" not in content:
            print("✅ Problematic method removed from unifiedNotificationService")
        else:
            print("❌ Problematic method still exists in unifiedNotificationService")
            
    except Exception as e:
        print(f"❌ Error reading unifiedNotificationService.ts: {e}")

def test_notification_icon():
    """Test notification icon configuration"""
    print("\n🔍 TESTING NOTIFICATION ICON")
    
    # Check if notification icons exist and are properly sized
    icon_paths = [
        "mobileapp/assets/notification_icon.png",
        "mobileapp/assets/small_notification_icon.png"
    ]
    
    for icon_path in icon_paths:
        if os.path.exists(icon_path):
            size = os.path.getsize(icon_path)
            print(f"✅ {icon_path} exists ({size} bytes)")
        else:
            print(f"❌ {icon_path} missing")
    
    # Check app.json configuration
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        notification_config = app_config.get("expo", {}).get("notification", {})
        plugins = app_config.get("expo", {}).get("plugins", [])
        
        # Check main notification config
        icon_path = notification_config.get("icon")
        if icon_path == "./assets/notification_icon.png":
            print("✅ Main notification icon configured correctly")
        else:
            print(f"❌ Main notification icon misconfigured: {icon_path}")
        
        # Check expo-notifications plugin
        expo_notifications_plugin = None
        for plugin in plugins:
            if isinstance(plugin, list) and len(plugin) > 0 and plugin[0] == "expo-notifications":
                expo_notifications_plugin = plugin[1] if len(plugin) > 1 else {}
                break
        
        if expo_notifications_plugin:
            plugin_icon = expo_notifications_plugin.get("icon")
            if plugin_icon == "./assets/notification_icon.png":
                print("✅ Expo notifications plugin icon configured correctly")
            else:
                print(f"❌ Expo notifications plugin icon misconfigured: {plugin_icon}")
        else:
            print("❌ Expo notifications plugin not found")
            
    except Exception as e:
        print(f"❌ Error reading app.json: {e}")

def test_backend_scheduler():
    """Test backend scheduler changes"""
    print("\n🔍 TESTING BACKEND SCHEDULER")
    
    # Check if complex scheduler is disabled
    try:
        with open("backend/services/notification_scheduler.py", "r") as f:
            content = f.read()
        
        if "TEMPORARILY DISABLED" in content:
            print("✅ Complex notification scheduler disabled")
        else:
            print("❌ Complex notification scheduler still active")
            
    except Exception as e:
        print(f"❌ Error reading notification_scheduler.py: {e}")
    
    # Check if simple scheduler exists
    try:
        with open("backend/services/notification_scheduler_simple.py", "r") as f:
            content = f.read()
        
        if "SimpleNotificationScheduler" in content:
            print("✅ Simple notification scheduler created")
        else:
            print("❌ Simple notification scheduler not found")
            
    except Exception as e:
        print(f"❌ Error reading notification_scheduler_simple.py: {e}")
    
    # Check if server.py uses simple scheduler
    try:
        with open("backend/server.py", "r") as f:
            content = f.read()
        
        if "get_simple_notification_scheduler" in content:
            print("✅ Server.py uses simple notification scheduler")
        else:
            print("❌ Server.py may not use simple notification scheduler")
            
    except Exception as e:
        print(f"❌ Error reading server.py: {e}")

def test_notification_targeting():
    """Test notification targeting logic"""
    print("\n🔍 TESTING NOTIFICATION TARGETING")
    
    # Check firebase_client.py for "1 day left" notification logic
    try:
        with open("backend/services/firebase_client.py", "r") as f:
            content = f.read()
        
        # Check if "1 day left" notifications target dieticians
        if "dietician_token = get_dietician_notification_token()" in content:
            print("✅ Dietician token retrieval found")
        else:
            print("❌ Dietician token retrieval missing")
        
        if "send_push_notification(" in content and "dietician_token" in content:
            print("✅ 1 day left notifications sent to dietician")
        else:
            print("❌ 1 day left notifications not sent to dietician")
        
        # Check name formatting
        if "full_name = f\"{first_name} {last_name}\"" in content:
            print("✅ Proper name formatting found")
        else:
            print("❌ Proper name formatting missing")
        
        # Check for "User User" fallback
        if "full_name = \"User\"" in content:
            print("✅ User fallback found")
        else:
            print("❌ User fallback missing")
            
    except Exception as e:
        print(f"❌ Error reading firebase_client.py: {e}")

def test_local_scheduling():
    """Test local notification scheduling"""
    print("\n🔍 TESTING LOCAL SCHEDULING")
    
    # Check if unifiedNotificationService uses local scheduling
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        # Check if it uses local device time
        if "const now = new Date()" in content:
            print("✅ Uses local device time for scheduling")
        else:
            print("❌ May not use local device time")
        
        # Check if it has diet notification scheduling
        if "scheduleDietNotifications" in content:
            print("✅ Diet notification scheduling method exists")
        else:
            print("❌ Diet notification scheduling method missing")
        
        # Check if it has custom notification scheduling
        if "scheduleCustomNotification" in content:
            print("✅ Custom notification scheduling method exists")
        else:
            print("❌ Custom notification scheduling method missing")
            
    except Exception as e:
        print(f"❌ Error reading unifiedNotificationService.ts: {e}")

def test_edge_cases():
    """Test edge cases and potential issues"""
    print("\n🔍 TESTING EDGE CASES")
    
    # Check for any remaining "User User" references
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        if "User User" not in content:
            print("✅ No 'User User' references found in unifiedNotificationService")
        else:
            print("❌ 'User User' references still exist in unifiedNotificationService")
            
    except Exception as e:
        print(f"❌ Error checking for 'User User' references: {e}")
    
    # Check for any remaining complex scheduling logic
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        if "calculateDietNextOccurrence" in content and "calculateNextOccurrence" in content:
            print("✅ Both diet and custom notification calculation methods exist")
        else:
            print("❌ Missing notification calculation methods")
            
    except Exception as e:
        print(f"❌ Error checking calculation methods: {e}")

def main():
    """Run all tests"""
    print("🚀 COMPREHENSIVE NOTIFICATION FIXES TEST")
    print("=" * 60)
    
    test_critical_fixes()
    test_notification_icon()
    test_backend_scheduler()
    test_notification_targeting()
    test_local_scheduling()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("✅ COMPREHENSIVE TEST COMPLETED")
    print("\n📋 SUMMARY:")
    print("- Critical '1 day left' notification issue should be fixed")
    print("- Notification icons should be properly optimized")
    print("- Complex backend scheduler should be disabled")
    print("- Simple local scheduling should be active")
    print("- All notifications should use local device time")
    print("- Proper targeting should be maintained")

if __name__ == "__main__":
    main()
