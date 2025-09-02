#!/usr/bin/env python3
"""
Notification Icon Debug Test
Comprehensive analysis of notification icon configuration for EAS builds
"""

import os
import json
import re
from datetime import datetime

def test_notification_icon_files():
    """Test notification icon files existence and properties"""
    print("🔍 TESTING NOTIFICATION ICON FILES")
    
    icon_files = [
        "mobileapp/assets/notification_icon.png",
        "mobileapp/assets/small_notification_icon.png",
        "mobileapp/assets/adaptive-icon.png",
        "mobileapp/assets/logo.png"
    ]
    
    for icon_file in icon_files:
        if os.path.exists(icon_file):
            size = os.path.getsize(icon_file)
            print(f"✅ {icon_file} exists ({size} bytes)")
        else:
            print(f"❌ {icon_file} missing")
    
    # Check specific properties
    try:
        import subprocess
        result = subprocess.run(['file', 'mobileapp/assets/notification_icon.png'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ notification_icon.png properties: {result.stdout.strip()}")
        else:
            print(f"❌ Could not read notification_icon.png properties")
    except Exception as e:
        print(f"⚠️ Could not check file properties: {e}")

def test_app_json_configuration():
    """Test app.json notification configuration"""
    print("\n🔍 TESTING APP.JSON CONFIGURATION")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        # Check main notification config
        notification_config = app_config.get("expo", {}).get("notification", {})
        if notification_config:
            icon_path = notification_config.get("icon")
            color = notification_config.get("color")
            android_mode = notification_config.get("androidMode")
            
            print(f"✅ Main notification config found")
            print(f"   Icon: {icon_path}")
            print(f"   Color: {color}")
            print(f"   Android Mode: {android_mode}")
            
            # Check if icon path is correct
            if icon_path == "./assets/notification_icon.png":
                print("✅ Icon path correctly configured")
            else:
                print(f"❌ Icon path misconfigured: {icon_path}")
        else:
            print("❌ Main notification config missing")
        
        # Check expo-notifications plugin
        plugins = app_config.get("expo", {}).get("plugins", [])
        expo_notifications_plugin = None
        
        for plugin in plugins:
            if isinstance(plugin, list) and len(plugin) > 0 and plugin[0] == "expo-notifications":
                expo_notifications_plugin = plugin[1] if len(plugin) > 1 else {}
                break
        
        if expo_notifications_plugin:
            plugin_icon = expo_notifications_plugin.get("icon")
            plugin_color = expo_notifications_plugin.get("color")
            plugin_mode = expo_notifications_plugin.get("mode")
            
            print(f"✅ Expo notifications plugin found")
            print(f"   Icon: {plugin_icon}")
            print(f"   Color: {plugin_color}")
            print(f"   Mode: {plugin_mode}")
            
            # Check if plugin icon matches main config
            if plugin_icon == icon_path:
                print("✅ Plugin icon matches main config")
            else:
                print(f"❌ Plugin icon mismatch: {plugin_icon} vs {icon_path}")
        else:
            print("❌ Expo notifications plugin not found")
            
    except Exception as e:
        print(f"❌ Error reading app.json: {e}")

def test_android_specific_config():
    """Test Android-specific notification configuration"""
    print("\n🔍 TESTING ANDROID-SPECIFIC CONFIGURATION")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        android_config = app_config.get("expo", {}).get("android", {})
        if android_config:
            print("✅ Android config found")
            
            # Check adaptive icon
            adaptive_icon = android_config.get("adaptiveIcon", {})
            if adaptive_icon:
                foreground_image = adaptive_icon.get("foregroundImage")
                background_color = adaptive_icon.get("backgroundColor")
                
                print(f"   Adaptive Icon: {foreground_image}")
                print(f"   Background Color: {background_color}")
                
                if foreground_image == "./assets/logo.png":
                    print("✅ Adaptive icon correctly configured")
                else:
                    print(f"❌ Adaptive icon misconfigured: {foreground_image}")
            else:
                print("❌ Adaptive icon config missing")
            
            # Check permissions
            permissions = android_config.get("permissions", [])
            required_permissions = ["VIBRATE", "RECEIVE_BOOT_COMPLETED", "WAKE_LOCK"]
            
            for permission in required_permissions:
                if permission in permissions:
                    print(f"✅ {permission} permission found")
                else:
                    print(f"❌ {permission} permission missing")
        else:
            print("❌ Android config missing")
            
    except Exception as e:
        print(f"❌ Error checking Android config: {e}")

def test_ios_specific_config():
    """Test iOS-specific notification configuration"""
    print("\n🔍 TESTING IOS-SPECIFIC CONFIGURATION")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        ios_config = app_config.get("expo", {}).get("ios", {})
        if ios_config:
            print("✅ iOS config found")
            
            # Check background modes
            info_plist = ios_config.get("infoPlist", {})
            background_modes = info_plist.get("UIBackgroundModes", [])
            
            if "remote-notification" in background_modes:
                print("✅ remote-notification background mode found")
            else:
                print("❌ remote-notification background mode missing")
            
            # Check bundle identifier
            bundle_id = ios_config.get("bundleIdentifier")
            if bundle_id:
                print(f"✅ Bundle identifier: {bundle_id}")
            else:
                print("❌ Bundle identifier missing")
        else:
            print("❌ iOS config missing")
            
    except Exception as e:
        print(f"❌ Error checking iOS config: {e}")

def test_eas_configuration():
    """Test EAS build configuration"""
    print("\n🔍 TESTING EAS BUILD CONFIGURATION")
    
    try:
        with open("eas.json", "r") as f:
            eas_config = json.load(f)
        
        if eas_config:
            print("✅ EAS config found")
            
            # Check build profiles
            build_profiles = eas_config.get("build", {})
            for profile_name, profile_config in build_profiles.items():
                print(f"   Profile: {profile_name}")
                if "distribution" in profile_config:
                    print(f"     Distribution: {profile_config['distribution']}")
                if "env" in profile_config:
                    print(f"     Environment variables: {len(profile_config['env'])} set")
        else:
            print("❌ EAS config missing")
            
    except Exception as e:
        print(f"❌ Error reading EAS config: {e}")

def test_notification_icon_optimization():
    """Test notification icon optimization"""
    print("\n🔍 TESTING NOTIFICATION ICON OPTIMIZATION")
    
    try:
        # Check notification icon size
        notification_icon_path = "mobileapp/assets/notification_icon.png"
        if os.path.exists(notification_icon_path):
            size = os.path.getsize(notification_icon_path)
            
            if size < 10000:  # Under 10KB
                print(f"✅ Notification icon properly sized ({size} bytes)")
            else:
                print(f"❌ Notification icon too large ({size} bytes)")
            
            # Check if it's the right dimensions
            import subprocess
            result = subprocess.run(['file', notification_icon_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                if "96 x 96" in result.stdout:
                    print("✅ Notification icon has correct dimensions (96x96)")
                else:
                    print(f"❌ Notification icon has wrong dimensions: {result.stdout.strip()}")
            else:
                print("⚠️ Could not verify icon dimensions")
        else:
            print("❌ Notification icon file not found")
            
    except Exception as e:
        print(f"❌ Error checking icon optimization: {e}")

def test_platform_compatibility():
    """Test platform compatibility for notification icons"""
    print("\n🔍 TESTING PLATFORM COMPATIBILITY")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        platforms = app_config.get("expo", {}).get("platforms", [])
        if platforms:
            print(f"✅ Platforms configured: {', '.join(platforms)}")
            
            # Check if both iOS and Android are supported
            if "ios" in platforms and "android" in platforms:
                print("✅ Both iOS and Android platforms supported")
            else:
                print("❌ Missing platform support")
        else:
            print("❌ No platforms configured")
            
        # Check if notification icon is configured for both platforms
        notification_config = app_config.get("expo", {}).get("notification", {})
        if notification_config and "icon" in notification_config:
            print("✅ Notification icon configured for all platforms")
        else:
            print("❌ Notification icon not configured for all platforms")
            
    except Exception as e:
        print(f"❌ Error checking platform compatibility: {e}")

def main():
    """Run all notification icon debug tests"""
    print("🚀 NOTIFICATION ICON DEBUG TEST")
    print("=" * 60)
    
    test_notification_icon_files()
    test_app_json_configuration()
    test_android_specific_config()
    test_ios_specific_config()
    test_eas_configuration()
    test_notification_icon_optimization()
    test_platform_compatibility()
    
    print("\n" + "=" * 60)
    print("✅ NOTIFICATION ICON DEBUG TEST COMPLETED")
    print("\n📋 ANALYSIS SUMMARY:")
    print("- All notification icon files should be present and properly sized")
    print("- App.json should have correct notification configuration")
    print("- Both iOS and Android should be properly configured")
    print("- EAS build configuration should be correct")
    print("- Notification icons should be optimized for both platforms")

if __name__ == "__main__":
    main()
