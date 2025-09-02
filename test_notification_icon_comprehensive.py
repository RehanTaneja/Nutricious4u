#!/usr/bin/env python3
"""
Comprehensive Notification Icon Test
Tests all notification icon configurations after fixes
"""

import os
import json
import re
from datetime import datetime

def test_notification_icon_files():
    """Test all notification icon files"""
    print("🔍 TESTING NOTIFICATION ICON FILES")
    
    icon_files = [
        "mobileapp/assets/notification_icon_24.png",
        "mobileapp/assets/notification_icon_36.png",
        "mobileapp/assets/notification_icon_48.png",
        "mobileapp/assets/notification_icon_72.png",
        "mobileapp/assets/notification_icon_96.png",
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
    
    # Check specific properties of key icons
    key_icons = [
        ("mobileapp/assets/notification_icon_96.png", "96x96"),
        ("mobileapp/assets/notification_icon_48.png", "48x48"),
        ("mobileapp/assets/notification_icon_24.png", "24x24")
    ]
    
    for icon_path, expected_size in key_icons:
        if os.path.exists(icon_path):
            try:
                import subprocess
                result = subprocess.run(['file', icon_path], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    if expected_size in result.stdout:
                        print(f"✅ {icon_path} has correct dimensions: {expected_size}")
                    else:
                        print(f"❌ {icon_path} has wrong dimensions: {result.stdout.strip()}")
                else:
                    print(f"⚠️ Could not read {icon_path} properties")
            except Exception as e:
                print(f"⚠️ Could not check {icon_path} properties: {e}")

def test_app_json_notification_config():
    """Test app.json notification configuration"""
    print("\n🔍 TESTING APP.JSON NOTIFICATION CONFIGURATION")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        # Check main notification config
        notification_config = app_config.get("expo", {}).get("notification", {})
        if notification_config:
            print("✅ Main notification config found")
            
            # Check main icon
            main_icon = notification_config.get("icon")
            if main_icon == "./assets/notification_icon_96.png":
                print("✅ Main notification icon correctly configured")
            else:
                print(f"❌ Main notification icon misconfigured: {main_icon}")
            
            # Check platform-specific icons
            ios_icon = notification_config.get("ios", {}).get("icon")
            android_icon = notification_config.get("android", {}).get("icon")
            
            if ios_icon == "./assets/notification_icon_96.png":
                print("✅ iOS notification icon correctly configured")
            else:
                print(f"❌ iOS notification icon misconfigured: {ios_icon}")
            
            if android_icon == "./assets/notification_icon_48.png":
                print("✅ Android notification icon correctly configured")
            else:
                print(f"❌ Android notification icon misconfigured: {android_icon}")
            
            # Check other properties
            color = notification_config.get("color")
            android_mode = notification_config.get("androidMode")
            android_title = notification_config.get("androidCollapsedTitle")
            
            if color == "#ffffff":
                print("✅ Notification color correctly configured")
            else:
                print(f"❌ Notification color misconfigured: {color}")
            
            if android_mode == "default":
                print("✅ Android mode correctly configured")
            else:
                print(f"❌ Android mode misconfigured: {android_mode}")
            
            if android_title == "Nutricious4u":
                print("✅ Android collapsed title correctly configured")
            else:
                print(f"❌ Android collapsed title misconfigured: {android_title}")
        else:
            print("❌ Main notification config missing")
            
    except Exception as e:
        print(f"❌ Error reading app.json notification config: {e}")

def test_platform_specific_notification_config():
    """Test platform-specific notification configuration"""
    print("\n🔍 TESTING PLATFORM-SPECIFIC NOTIFICATION CONFIGURATION")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        # Check iOS notification config
        ios_config = app_config.get("expo", {}).get("ios", {})
        if ios_config:
            ios_notification = ios_config.get("notification", {})
            if ios_notification:
                ios_icon = ios_notification.get("icon")
                ios_color = ios_notification.get("color")
                
                if ios_icon == "./assets/notification_icon_96.png":
                    print("✅ iOS platform notification icon correctly configured")
                else:
                    print(f"❌ iOS platform notification icon misconfigured: {ios_icon}")
                
                if ios_color == "#ffffff":
                    print("✅ iOS platform notification color correctly configured")
                else:
                    print(f"❌ iOS platform notification color misconfigured: {ios_color}")
            else:
                print("❌ iOS platform notification config missing")
        else:
            print("❌ iOS config missing")
        
        # Check Android notification config
        android_config = app_config.get("expo", {}).get("android", {})
        if android_config:
            android_notification = android_config.get("notification", {})
            if android_notification:
                android_icon = android_notification.get("icon")
                android_color = android_notification.get("color")
                
                if android_icon == "./assets/notification_icon_48.png":
                    print("✅ Android platform notification icon correctly configured")
                else:
                    print(f"❌ Android platform notification icon misconfigured: {android_icon}")
                
                if android_color == "#ffffff":
                    print("✅ Android platform notification color correctly configured")
                else:
                    print(f"❌ Android platform notification color misconfigured: {android_color}")
            else:
                print("❌ Android platform notification config missing")
        else:
            print("❌ Android config missing")
            
    except Exception as e:
        print(f"❌ Error reading platform-specific config: {e}")

def test_expo_notifications_plugin():
    """Test expo-notifications plugin configuration"""
    print("\n🔍 TESTING EXPO-NOTIFICATIONS PLUGIN")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
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
            
            print("✅ Expo notifications plugin found")
            
            if plugin_icon == "./assets/notification_icon_96.png":
                print("✅ Plugin icon correctly configured")
            else:
                print(f"❌ Plugin icon misconfigured: {plugin_icon}")
            
            if plugin_color == "#ffffff":
                print("✅ Plugin color correctly configured")
            else:
                print(f"❌ Plugin color misconfigured: {plugin_color}")
            
            if plugin_mode == "production":
                print("✅ Plugin mode correctly configured (production)")
            else:
                print(f"❌ Plugin mode misconfigured: {plugin_mode}")
        else:
            print("❌ Expo notifications plugin not found")
            
    except Exception as e:
        print(f"❌ Error reading expo-notifications plugin: {e}")

def test_icon_size_optimization():
    """Test icon size optimization"""
    print("\n🔍 TESTING ICON SIZE OPTIMIZATION")
    
    # Check if all notification icons are properly sized
    notification_icons = [
        ("mobileapp/assets/notification_icon_24.png", 24, 5000),  # 24x24, max 5KB
        ("mobileapp/assets/notification_icon_36.png", 36, 8000),  # 36x36, max 8KB
        ("mobileapp/assets/notification_icon_48.png", 48, 10000), # 48x48, max 10KB
        ("mobileapp/assets/notification_icon_72.png", 72, 15000), # 72x72, max 15KB
        ("mobileapp/assets/notification_icon_96.png", 96, 20000)  # 96x96, max 20KB
    ]
    
    for icon_path, expected_size, max_bytes in notification_icons:
        if os.path.exists(icon_path):
            actual_size = os.path.getsize(icon_path)
            
            if actual_size <= max_bytes:
                print(f"✅ {icon_path} properly sized ({actual_size} bytes, max {max_bytes})")
            else:
                print(f"❌ {icon_path} too large ({actual_size} bytes, max {max_bytes})")
            
            # Check dimensions
            try:
                import subprocess
                result = subprocess.run(['file', icon_path], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    expected_dim = f"{expected_size} x {expected_size}"
                    if expected_dim in result.stdout:
                        print(f"   ✅ Correct dimensions: {expected_dim}")
                    else:
                        print(f"   ❌ Wrong dimensions: {result.stdout.strip()}")
                else:
                    print(f"   ⚠️ Could not verify dimensions")
            except Exception as e:
                print(f"   ⚠️ Error checking dimensions: {e}")
        else:
            print(f"❌ {icon_path} missing")

def test_eas_build_compatibility():
    """Test EAS build compatibility"""
    print("\n🔍 TESTING EAS BUILD COMPATIBILITY")
    
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
                
                # Check if production profile has autoIncrement
                if profile_name == "production":
                    if profile_config.get("autoIncrement"):
                        print("     ✅ Auto-increment enabled for production")
                    else:
                        print("     ❌ Auto-increment disabled for production")
        else:
            print("❌ EAS config missing")
            
        # Check if app.json has correct project ID
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        project_id = app_config.get("expo", {}).get("extra", {}).get("eas", {}).get("projectId")
        if project_id:
            print(f"✅ EAS project ID configured: {project_id}")
        else:
            print("❌ EAS project ID missing")
            
    except Exception as e:
        print(f"❌ Error checking EAS compatibility: {e}")

def test_notification_icon_consistency():
    """Test notification icon consistency across configurations"""
    print("\n🔍 TESTING NOTIFICATION ICON CONSISTENCY")
    
    try:
        with open("mobileapp/app.json", "r") as f:
            app_config = json.load(f)
        
        # Get all icon configurations
        main_icon = app_config.get("expo", {}).get("notification", {}).get("icon")
        ios_icon = app_config.get("expo", {}).get("notification", {}).get("ios", {}).get("icon")
        android_icon = app_config.get("expo", {}).get("notification", {}).get("android", {}).get("icon")
        ios_platform_icon = app_config.get("expo", {}).get("ios", {}).get("notification", {}).get("icon")
        android_platform_icon = app_config.get("expo", {}).get("android", {}).get("notification", {}).get("icon")
        
        # Check if iOS icons are consistent
        if main_icon == ios_icon == ios_platform_icon:
            print("✅ iOS notification icons are consistent")
        else:
            print("❌ iOS notification icons are inconsistent")
            print(f"   Main: {main_icon}")
            print(f"   iOS (main): {ios_icon}")
            print(f"   iOS (platform): {ios_platform_icon}")
        
        # Check if Android icons are consistent
        if android_icon == android_platform_icon:
            print("✅ Android notification icons are consistent")
        else:
            print("❌ Android notification icons are inconsistent")
            print(f"   Android (main): {android_icon}")
            print(f"   Android (platform): {android_platform_icon}")
        
        # Check if icons exist
        all_icons = [main_icon, ios_icon, android_icon, ios_platform_icon, android_platform_icon]
        all_icons = [icon for icon in all_icons if icon]
        
        for icon in all_icons:
            icon_path = f"mobileapp/{icon[2:]}"  # Remove "./" prefix
            if os.path.exists(icon_path):
                print(f"✅ Icon file exists: {icon}")
            else:
                print(f"❌ Icon file missing: {icon}")
                
    except Exception as e:
        print(f"❌ Error checking icon consistency: {e}")

def main():
    """Run all notification icon tests"""
    print("🚀 COMPREHENSIVE NOTIFICATION ICON TEST")
    print("=" * 70)
    
    test_notification_icon_files()
    test_app_json_notification_config()
    test_platform_specific_notification_config()
    test_expo_notifications_plugin()
    test_icon_size_optimization()
    test_eas_build_compatibility()
    test_notification_icon_consistency()
    
    print("\n" + "=" * 70)
    print("✅ COMPREHENSIVE NOTIFICATION ICON TEST COMPLETED")
    print("\n📋 FIXES IMPLEMENTED:")
    print("- Created multiple icon sizes (24x24, 36x36, 48x48, 72x72, 96x96)")
    print("- Added platform-specific notification icon configurations")
    print("- Updated main notification configuration")
    print("- Ensured consistency across all configurations")
    print("- Optimized icon sizes for better compatibility")
    print("\n🎯 EXPECTED RESULTS:")
    print("- Notification icons should now work in EAS builds")
    print("- Both iOS and Android should display proper icons")
    print("- Icons should be visible in all notification types")
    print("- Better compatibility across different device densities")

if __name__ == "__main__":
    main()
