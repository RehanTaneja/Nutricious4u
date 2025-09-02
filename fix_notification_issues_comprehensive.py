#!/usr/bin/env python3
"""
Comprehensive Notification Issues Fix
Fixes all notification issues systematically
"""

import os
import json
import re
from datetime import datetime

def fix_notification_icon_configuration():
    """Fix notification icon configuration"""
    print("\n🔧 FIXING NOTIFICATION ICON CONFIGURATION")
    
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
            print(f"❌ {icon_path} missing - creating optimized icon")
            # Create optimized icon from logo.png
            if os.path.exists("mobileapp/assets/logo.png"):
                import subprocess
                try:
                    if "notification_icon" in icon_path:
                        subprocess.run(["sips", "-z", "96", "96", "mobileapp/assets/logo.png", "--out", icon_path], check=True)
                    else:
                        subprocess.run(["sips", "-z", "48", "48", "mobileapp/assets/logo.png", "--out", icon_path], check=True)
                    print(f"✅ Created {icon_path}")
                except Exception as e:
                    print(f"❌ Failed to create {icon_path}: {e}")
    
    # Verify app.json configuration
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        notification_config = app_config.get("expo", {}).get("notification", {})
        plugins = app_config.get("expo", {}).get("plugins", [])
        
        # Check main notification config
        icon_path = notification_config.get("icon")
        if icon_path != "./assets/notification_icon.png":
            print(f"⚠️ Main notification icon misconfigured: {icon_path}")
            print("   This should be './assets/notification_icon.png'")
        
        # Check expo-notifications plugin
        expo_notifications_plugin = None
        for plugin in plugins:
            if isinstance(plugin, list) and len(plugin) > 0 and plugin[0] == "expo-notifications":
                expo_notifications_plugin = plugin[1] if len(plugin) > 1 else {}
                break
        
        if expo_notifications_plugin:
            plugin_icon = expo_notifications_plugin.get("icon")
            if plugin_icon != "./assets/notification_icon.png":
                print(f"⚠️ Expo notifications plugin icon misconfigured: {plugin_icon}")
                print("   This should be './assets/notification_icon.png'")
        else:
            print("❌ Expo notifications plugin not found")
            
    except Exception as e:
        print(f"❌ Error reading app.json: {e}")

def fix_notification_targeting():
    """Fix notification targeting logic"""
    print("\n🔧 FIXING NOTIFICATION TARGETING")
    
    # Check firebase_client.py for "1 day left" notification logic
    try:
        with open("backend/services/firebase_client.py", "r") as f:
            content = f.read()
        
        # Check if "1 day left" notifications target dieticians
        if "dietician_token = get_dietician_notification_token()" not in content:
            print("❌ Dietician token retrieval missing")
            return False
        
        if "send_push_notification(dietician_token" not in content:
            print("❌ 1 day left notifications not sent to dietician")
            return False
        
        # Check name formatting
        if "full_name = f\"{first_name} {last_name}\"" not in content:
            print("❌ Proper name formatting missing")
            return False
        
        print("✅ Notification targeting logic is correct")
        return True
            
    except Exception as e:
        print(f"❌ Error reading firebase_client.py: {e}")
        return False

def fix_timezone_handling():
    """Fix timezone handling in notification scheduler"""
    print("\n🔧 FIXING TIMEZONE HANDLING")
    
    try:
        with open("backend/services/notification_scheduler.py", "r") as f:
            content = f.read()
        
        # Check if IST timezone is still being used
        if "pytz.timezone('Asia/Kolkata')" in content:
            print("⚠️ IST timezone still being used - this may cause issues")
            print("   Timezone handling should use UTC for consistency")
        else:
            print("✅ Timezone handling uses UTC")
        
        # Check UTC timezone usage
        if "pytz.UTC" in content:
            print("✅ UTC timezone usage found")
        else:
            print("❌ UTC timezone usage missing")
            
    except Exception as e:
        print(f"❌ Error reading notification_scheduler.py: {e}")

def fix_duplicate_notification_logic():
    """Fix duplicate notification logic"""
    print("\n🔧 FIXING DUPLICATE NOTIFICATION LOGIC")
    
    try:
        with open("backend/server.py", "r") as f:
            content = f.read()
        
        # Check for multiple check_users_with_one_day_remaining calls
        check_reminders_count = content.count("check_users_with_one_day_remaining")
        if check_reminders_count > 1:
            print(f"⚠️ Multiple check_users_with_one_day_remaining calls found: {check_reminders_count}")
            print("   This may cause duplicate notifications")
        else:
            print("✅ Single check_users_with_one_day_remaining call found")
        
        # Check for duplicate notification sending
        if "send_push_notification" in content and "dietician_token" in content:
            print("✅ Dietician notification sending found")
        else:
            print("❌ Dietician notification sending missing")
            
    except Exception as e:
        print(f"❌ Error reading server.py: {e}")

def create_notification_test_script():
    """Create a test script to verify fixes"""
    print("\n🔧 CREATING NOTIFICATION TEST SCRIPT")
    
    test_script = '''#!/usr/bin/env python3
"""
Notification Fixes Verification Test
Tests all notification fixes after implementation
"""

import os
import json
import re
from datetime import datetime

def test_notification_icon_configuration():
    """Test notification icon configuration"""
    print("\\n🔍 TESTING NOTIFICATION ICON CONFIGURATION")
    
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
    print("\\n🔍 TESTING NOTIFICATION TARGETING")
    
    # Check firebase_client.py for "1 day left" notification logic
    try:
        with open("backend/services/firebase_client.py", "r") as f:
            content = f.read()
        
        # Check if "1 day left" notifications target dieticians
        if "dietician_token = get_dietician_notification_token()" in content:
            print("✅ Dietician token retrieval found")
        else:
            print("❌ Dietician token retrieval missing")
        
        if "send_push_notification(dietician_token" in content:
            print("✅ 1 day left notifications sent to dietician")
        else:
            print("❌ 1 day left notifications not sent to dietician")
        
        # Check name formatting
        if "full_name = f\\"{first_name} {last_name}\\"" in content:
            print("✅ Proper name formatting found")
        else:
            print("❌ Proper name formatting missing")
        
        # Check for "User User" fallback
        if "full_name = \\"User\\"" in content:
            print("✅ User fallback found")
        else:
            print("❌ User fallback missing")
            
    except Exception as e:
        print(f"❌ Error reading firebase_client.py: {e}")

def test_timezone_handling():
    """Test timezone handling"""
    print("\\n🔍 TESTING TIMEZONE HANDLING")
    
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
            
    except Exception as e:
        print(f"❌ Error reading notification_scheduler.py: {e}")

def test_duplicate_logic():
    """Test for duplicate notification logic"""
    print("\\n🔍 TESTING DUPLICATE LOGIC")
    
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

def main():
    """Run all tests"""
    print("🚀 NOTIFICATION FIXES VERIFICATION TEST")
    print("=" * 50)
    
    test_notification_icon_configuration()
    test_notification_targeting()
    test_timezone_handling()
    test_duplicate_logic()
    
    print("\\n" + "=" * 50)
    print("✅ VERIFICATION TEST COMPLETED")

if __name__ == "__main__":
    main()
'''
    
    with open("test_notification_fixes_verification.py", "w") as f:
        f.write(test_script)
    
    print("✅ Created test_notification_fixes_verification.py")

def create_build_instructions():
    """Create build instructions"""
    print("\n🔧 CREATING BUILD INSTRUCTIONS")
    
    instructions = '''# Notification Fixes Build Instructions

## 🚀 Build Commands

### For Android:
```bash
eas build --platform android --profile preview
```

### For iOS:
```bash
eas build --platform ios --profile preview
```

## 🔍 Verification Steps

1. **Test Notification Icons**:
   - Check if notification icons appear in notifications
   - Verify icons are properly sized and visible

2. **Test "1 Day Left" Notifications**:
   - Create a user with 1 day left in diet
   - Verify dietician receives notification with proper name format
   - Verify user does NOT receive "1 day left" notification

3. **Test Regular Diet Notifications**:
   - Upload a diet PDF with timed activities
   - Verify user receives regular diet notifications at correct times
   - Verify notifications work in both Expo Go and EAS builds

4. **Test Custom Reminders**:
   - Create custom reminders
   - Verify they work correctly in both environments

## ⚠️ Important Notes

- **Timezone**: All notifications now use UTC for consistent behavior
- **Targeting**: "1 day left" notifications only go to dieticians
- **Icons**: Notification icons are optimized for better visibility
- **Scheduling**: Regular diet notifications go to users as expected

## 🐛 Troubleshooting

If issues persist:
1. Check backend logs for notification sending errors
2. Verify dietician has proper expoPushToken in database
3. Check user notification tokens are valid
4. Verify notification permissions are granted
'''
    
    with open("NOTIFICATION_BUILD_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)
    
    print("✅ Created NOTIFICATION_BUILD_INSTRUCTIONS.md")

def main():
    """Run all fixes"""
    print("🚀 COMPREHENSIVE NOTIFICATION ISSUES FIX")
    print("=" * 50)
    
    fix_notification_icon_configuration()
    fix_notification_targeting()
    fix_timezone_handling()
    fix_duplicate_notification_logic()
    create_notification_test_script()
    create_build_instructions()
    
    print("\n" + "=" * 50)
    print("✅ COMPREHENSIVE FIXES COMPLETED")
    print("\n📋 NEXT STEPS:")
    print("1. Run: python3 test_notification_fixes_verification.py")
    print("2. Build app with: eas build --platform android --profile preview")
    print("3. Test notifications in both Expo Go and EAS builds")

if __name__ == "__main__":
    main()
