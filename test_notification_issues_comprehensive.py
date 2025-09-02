#!/usr/bin/env python3
"""
Comprehensive Notification Issues Test
Tests all notification systems to identify issues before fixes
"""

import os
import json
import re
from datetime import datetime

def test_notification_icon_configuration():
    """Test notification icon configuration"""
    print("\n🔍 TESTING NOTIFICATION ICON CONFIGURATION")
    
    # Check if notification icons exist
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

def test_notification_scheduler():
    """Test notification scheduler configuration"""
    print("\n🔍 TESTING NOTIFICATION SCHEDULER")
    
    try:
        with open("backend/services/notification_scheduler.py", "r") as f:
            content = f.read()
        
        # Check timezone handling
        if "pytz.UTC" in content:
            print("✅ UTC timezone usage found")
        else:
            print("❌ UTC timezone usage missing")
        
        # Check IST timezone usage
        if "pytz.timezone('Asia/Kolkata')" in content:
            print("⚠️ IST timezone usage found (may cause issues)")
        else:
            print("✅ No IST timezone usage")
        
        # Check user token usage
        if "get_user_notification_token" in content:
            print("✅ User notification token usage found")
        else:
            print("❌ User notification token usage missing")
        
        # Check notification sending to users
        if "send_push_notification(token=user_token" in content:
            print("✅ Regular diet notifications sent to users")
        else:
            print("❌ Regular diet notifications not sent to users")
            
    except Exception as e:
        print(f"❌ Error reading notification_scheduler.py: {e}")

def test_server_scheduled_jobs():
    """Test server scheduled jobs"""
    print("\n🔍 TESTING SERVER SCHEDULED JOBS")
    
    try:
        with open("backend/server.py", "r") as f:
            content = f.read()
        
        # Check for duplicate "1 day left" logic
        check_reminders_count = content.count("check_users_with_one_day_remaining")
        if check_reminders_count == 1:
            print("✅ Single check_users_with_one_day_remaining call found")
        else:
            print(f"⚠️ Multiple check_users_with_one_day_remaining calls found: {check_reminders_count}")
        
        # Check for duplicate notification sending
        if "send_push_notification" in content and "dietician_token" in content:
            print("✅ Dietician notification sending found")
        else:
            print("❌ Dietician notification sending missing")
            
    except Exception as e:
        print(f"❌ Error reading server.py: {e}")

def test_diet_notification_service():
    """Test diet notification service"""
    print("\n🔍 TESTING DIET NOTIFICATION SERVICE")
    
    try:
        with open("backend/services/diet_notification_service.py", "r") as f:
            content = f.read()
        
        # Check user token usage
        if "get_user_notification_token(user_id)" in content:
            print("✅ User notification token usage found")
        else:
            print("❌ User notification token usage missing")
        
        # Check notification sending to users
        if "send_push_notification(token=user_token" in content:
            print("✅ Diet notifications sent to users")
        else:
            print("❌ Diet notifications not sent to users")
            
    except Exception as e:
        print(f"❌ Error reading diet_notification_service.py: {e}")

def test_expo_notifications_configuration():
    """Test Expo notifications configuration"""
    print("\n🔍 TESTING EXPO NOTIFICATIONS CONFIGURATION")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        plugins = app_config.get("expo", {}).get("plugins", [])
        
        # Check expo-notifications plugin mode
        expo_notifications_plugin = None
        for plugin in plugins:
            if isinstance(plugin, list) and len(plugin) > 0 and plugin[0] == "expo-notifications":
                expo_notifications_plugin = plugin[1] if len(plugin) > 1 else {}
                break
        
        if expo_notifications_plugin:
            mode = expo_notifications_plugin.get("mode")
            if mode == "production":
                print("✅ Expo notifications plugin in production mode")
            else:
                print(f"⚠️ Expo notifications plugin mode: {mode}")
        else:
            print("❌ Expo notifications plugin not found")
            
    except Exception as e:
        print(f"❌ Error reading app.json: {e}")

def main():
    """Run all tests"""
    print("🚀 COMPREHENSIVE NOTIFICATION ISSUES TEST")
    print("=" * 50)
    
    test_notification_icon_configuration()
    test_notification_targeting()
    test_notification_scheduler()
    test_server_scheduled_jobs()
    test_diet_notification_service()
    test_expo_notifications_configuration()
    
    print("\n" + "=" * 50)
    print("✅ COMPREHENSIVE TEST COMPLETED")

if __name__ == "__main__":
    main()
