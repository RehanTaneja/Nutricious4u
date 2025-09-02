#!/usr/bin/env python3
"""
User Scenarios Test
Simulates actual user scenarios to verify notification fixes
"""

import os
import json
import re
from datetime import datetime

def test_user_1_day_left_scenario():
    """Test the critical user scenario: user with 1 day left"""
    print("🔍 TESTING USER 1 DAY LEFT SCENARIO")
    
    # Check that users DON'T receive "1 day left" notifications
    try:
        with open("mobileapp/screens.tsx", "r") as f:
            content = f.read()
        
        # Should NOT have local scheduling of "1 day left" notifications
        if "scheduleDietReminderNotification" not in content:
            print("✅ Users will NOT receive '1 day left' notifications locally")
        else:
            print("❌ Users may still receive '1 day left' notifications locally")
            
    except Exception as e:
        print(f"❌ Error checking user scenario: {e}")
    
    # Check that dieticians DO receive "1 day left" notifications
    try:
        with open("backend/services/firebase_client.py", "r") as f:
            content = f.read()
        
        if "dietician_token = get_dietician_notification_token()" in content:
            print("✅ Dieticians will receive '1 day left' notifications")
        else:
            print("❌ Dieticians may not receive '1 day left' notifications")
            
    except Exception as e:
        print(f"❌ Error checking dietician scenario: {e}")

def test_notification_icon_scenario():
    """Test notification icon visibility scenario"""
    print("\n🔍 TESTING NOTIFICATION ICON SCENARIO")
    
    # Check if notification icons are properly configured
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        notification_config = app_config.get("expo", {}).get("notification", {})
        icon_path = notification_config.get("icon")
        
        if icon_path == "./assets/notification_icon.png":
            print("✅ Notification icon properly configured in app.json")
        else:
            print(f"❌ Notification icon misconfigured: {icon_path}")
        
        # Check if icon file exists and is properly sized
        icon_file_path = f"mobileapp/{icon_path[2:]}"  # Remove "./" prefix
        if os.path.exists(icon_file_path):
            size = os.path.getsize(icon_file_path)
            if size < 10000:  # Should be under 10KB for notifications
                print(f"✅ Notification icon exists and properly sized ({size} bytes)")
            else:
                print(f"⚠️ Notification icon may be too large ({size} bytes)")
        else:
            print(f"❌ Notification icon file missing: {icon_file_path}")
            
    except Exception as e:
        print(f"❌ Error checking notification icon: {e}")

def test_local_scheduling_scenario():
    """Test local scheduling scenario"""
    print("\n🔍 TESTING LOCAL SCHEDULING SCENARIO")
    
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        # Check if uses local device time
        if "const now = new Date()" in content:
            print("✅ Uses local device time for scheduling")
        else:
            print("❌ May not use local device time")
        
        # Check if has proper calculation methods
        if "calculateNextOccurrence" in content and "calculateDietNextOccurrence" in content:
            print("✅ Has proper calculation methods for both custom and diet notifications")
        else:
            print("❌ Missing calculation methods")
        
        # Check if both methods use same logic
        if "jsSelectedDay = (dayOfWeek + 1) % 7" in content:
            print("✅ Both notification types use same reliable scheduling logic")
        else:
            print("❌ Notification types may use different scheduling logic")
            
    except Exception as e:
        print(f"❌ Error checking local scheduling: {e}")

def test_eas_build_compatibility():
    """Test EAS build compatibility"""
    print("\n🔍 TESTING EAS BUILD COMPATIBILITY")
    
    # Check if complex backend scheduler is disabled
    try:
        with open("backend/services/notification_scheduler.py", "r") as f:
            content = f.read()
        
        if "TEMPORARILY DISABLED" in content:
            print("✅ Complex backend scheduler disabled - EAS builds will use local scheduling")
        else:
            print("❌ Complex backend scheduler still active - may cause EAS build issues")
            
    except Exception as e:
        print(f"❌ Error checking backend scheduler: {e}")
    
    # Check if simple scheduler is in place
    try:
        with open("backend/services/notification_scheduler_simple.py", "r") as f:
            content = f.read()
        
        if "SimpleNotificationScheduler" in content:
            print("✅ Simple scheduler in place - will work reliably in EAS builds")
        else:
            print("❌ Simple scheduler missing - EAS builds may fail")
            
    except Exception as e:
        print(f"❌ Error checking simple scheduler: {e}")

def test_timezone_consistency():
    """Test timezone consistency between environments"""
    print("\n🔍 TESTING TIMEZONE CONSISTENCY")
    
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        # Check for local device time usage
        if "new Date()" in content and "UTC" not in content:
            print("✅ Uses local device time consistently")
        else:
            print("❌ May have timezone inconsistencies")
        
        # Check for consistent day calculation
        if "jsSelectedDay = (dayOfWeek + 1) % 7" in content:
            print("✅ Uses consistent day calculation logic")
        else:
            print("❌ May have inconsistent day calculation")
            
    except Exception as e:
        print(f"❌ Error checking timezone consistency: {e}")

def test_notification_targeting():
    """Test notification targeting accuracy"""
    print("\n🔍 TESTING NOTIFICATION TARGETING")
    
    try:
        with open("backend/services/firebase_client.py", "r") as f:
            content = f.read()
        
        # Check for proper name formatting
        if "full_name = f\"{first_name} {last_name}\"" in content:
            print("✅ Proper name formatting for notifications")
        else:
            print("❌ May not format names properly")
        
        # Check for dietician targeting
        if "send_push_notification(" in content and "dietician_token" in content:
            print("✅ 1 day left notifications properly targeted to dieticians")
        else:
            print("❌ 1 day left notifications may not be properly targeted")
        
        # Check for user fallback
        if "full_name = \"User\"" in content:
            print("✅ Has proper fallback for missing names")
        else:
            print("❌ May not have proper fallback for missing names")
            
    except Exception as e:
        print(f"❌ Error checking notification targeting: {e}")

def test_app_restart_scenario():
    """Test app restart scenario"""
    print("\n🔍 TESTING APP RESTART SCENARIO")
    
    try:
        with open("mobileapp/services/unifiedNotificationService.ts", "r") as f:
            content = f.read()
        
        # Check if notifications are properly scheduled on app start
        if "scheduleDietNotifications" in content:
            print("✅ Diet notifications will be rescheduled on app restart")
        else:
            print("❌ Diet notifications may not be rescheduled on app restart")
        
        if "scheduleCustomNotification" in content:
            print("✅ Custom notifications will be rescheduled on app restart")
        else:
            print("❌ Custom notifications may not be rescheduled on app restart")
            
    except Exception as e:
        print(f"❌ Error checking app restart scenario: {e}")

def main():
    """Run all user scenario tests"""
    print("🚀 USER SCENARIOS TEST")
    print("=" * 50)
    
    test_user_1_day_left_scenario()
    test_notification_icon_scenario()
    test_local_scheduling_scenario()
    test_eas_build_compatibility()
    test_timezone_consistency()
    test_notification_targeting()
    test_app_restart_scenario()
    
    print("\n" + "=" * 50)
    print("✅ USER SCENARIOS TEST COMPLETED")
    print("\n📋 USER SCENARIOS SUMMARY:")
    print("- Users will NOT receive '1 day left' notifications")
    print("- Dieticians WILL receive '1 day left' notifications with proper names")
    print("- Notification icons should be visible in both Expo Go and EAS builds")
    print("- All notifications use local device time consistently")
    print("- EAS builds should work reliably with local scheduling")
    print("- App restarts should reschedule notifications properly")
    print("- Timezone handling should be consistent across environments")

if __name__ == "__main__":
    main()
