#!/usr/bin/env python3
"""
Manual Notification Test Script
Tests notification functionality manually
"""

import requests
import json
import time

def test_notification_configuration():
    """Test notification configuration"""
    print("🔍 TESTING NOTIFICATION CONFIGURATION")
    
    # Test the diet reminder endpoint
    try:
        response = requests.post("http://localhost:8000/api/diet/check-reminders")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Diet reminder endpoint working: {data}")
        else:
            print(f"❌ Diet reminder endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Diet reminder endpoint error: {e}")

def test_notification_icon():
    """Test notification icon configuration"""
    print("\n🔍 TESTING NOTIFICATION ICON")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        notification_config = app_config.get("expo", {}).get("notification", {})
        icon_path = notification_config.get("icon")
        
        if icon_path == "./assets/notification_icon.png":
            print("✅ Notification icon configured correctly")
        else:
            print(f"❌ Notification icon misconfigured: {icon_path}")
            
    except Exception as e:
        print(f"❌ Error reading app.json: {e}")

def main():
    """Run manual tests"""
    print("🚀 MANUAL NOTIFICATION TEST")
    print("=" * 40)
    
    test_notification_configuration()
    test_notification_icon()
    
    print("\n" + "=" * 40)
    print("✅ MANUAL TEST COMPLETED")
    print("\n📋 NEXT STEPS:")
    print("1. Build app: eas build --platform android --profile preview")
    print("2. Test notifications in both Expo Go and EAS builds")
    print("3. Verify '1 day left' notifications go to dieticians only")
    print("4. Verify regular diet notifications go to users")
    print("5. Verify notification icons are visible")

if __name__ == "__main__":
    main()
