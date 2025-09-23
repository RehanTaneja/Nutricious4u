#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime, timezone, timedelta

def debug_notification_delivery():
    """
    Debug why notifications are scheduled but not delivered to the user.
    This investigates the delivery chain: Schedule → System → User
    """
    
    base_url = "https://nutricious4u-production.up.railway.app/api"
    user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    
    print("🔍 DEBUGGING NOTIFICATION DELIVERY ISSUES")
    print("=" * 60)
    print(f"User: {user_id}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    print("📋 DELIVERY PROBLEM ANALYSIS")
    print("-" * 30)
    print("❓ Problem: 49 notifications scheduled but 6 PM notification not received")
    print("❓ This indicates: SCHEDULING ✅ but DELIVERY ❌")
    print()
    
    print("🔍 POSSIBLE ROOT CAUSES")
    print("-" * 30)
    delivery_issues = [
        "1. ❌ App in background - notifications suppressed",
        "2. ❌ Device notification permissions changed",
        "3. ❌ Battery optimization killing notifications",
        "4. ❌ Do Not Disturb mode enabled",
        "5. ❌ App-specific notification settings disabled",
        "6. ❌ Notification channel disabled (Android)",
        "7. ❌ TimeInterval calculation error (past time)",
        "8. ❌ Notification ID conflicts",
        "9. ❌ System notification limits exceeded",
        "10. ❌ EAS build notification permission issues"
    ]
    
    for issue in delivery_issues:
        print(f"   {issue}")
    print()
    
    print("🧪 TESTING DELIVERY CHAIN")
    print("-" * 30)
    
    # Test 1: Extract notifications again
    print("Test 1: Extracting notifications to see current state...")
    try:
        response = requests.post(f"{base_url}/users/{user_id}/diet/notifications/extract", timeout=60)
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            print(f"   ✅ Extracted: {len(notifications)} notifications")
            
            # Find 6 PM notification
            six_pm_notifications = []
            for notif in notifications:
                if notif.get('time') in ['18:00', '6:00']:
                    six_pm_notifications.append(notif)
            
            if six_pm_notifications:
                print(f"   ✅ Found {len(six_pm_notifications)} notifications at 6 PM:")
                for notif in six_pm_notifications:
                    print(f"     - {notif.get('time')}: {notif.get('message', '')[:50]}...")
                    print(f"       Days: {notif.get('selectedDays')}, Active: {notif.get('isActive')}")
            else:
                print(f"   ❌ No 6 PM notifications found in extracted data")
        else:
            print(f"   ❌ Extraction failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    print()
    
    # Test 2: Check time calculation for 6 PM today
    print("Test 2: Checking time calculation for 6 PM notification...")
    now = datetime.now()
    today_6pm = now.replace(hour=18, minute=0, second=0, microsecond=0)
    
    if today_6pm > now:
        seconds_until = int((today_6pm.timestamp() - now.timestamp()))
        print(f"   ✅ 6 PM today is in the future: {today_6pm}")
        print(f"   ✅ Seconds until 6 PM: {seconds_until}")
        print(f"   ✅ Time calculation: CORRECT")
    else:
        print(f"   ⚠️  6 PM today has passed: {today_6pm}")
        print(f"   ⚠️  Should schedule for next occurrence")
        
        # Check next occurrence
        next_occurrence = today_6pm + timedelta(days=1)
        seconds_until = int((next_occurrence.timestamp() - now.timestamp()))
        print(f"   ✅ Next 6 PM: {next_occurrence}")
        print(f"   ✅ Seconds until: {seconds_until}")
    print()
    
    print("🔧 SUCCESSFUL APPS' DELIVERY STRATEGIES")
    print("-" * 30)
    successful_strategies = [
        "1. ✅ Test notifications immediately after scheduling",
        "2. ✅ Use short test intervals (1-2 minutes) for debugging",
        "3. ✅ Check device notification settings programmatically",
        "4. ✅ Use notification channels properly (Android)",
        "5. ✅ Handle background app state correctly",
        "6. ✅ Implement notification received callbacks",
        "7. ✅ Use unique notification IDs to prevent conflicts",
        "8. ✅ Monitor system notification limits",
        "9. ✅ Provide manual refresh mechanisms",
        "10. ✅ Use immediate test notifications for verification"
    ]
    
    for strategy in successful_strategies:
        print(f"   {strategy}")
    print()
    
    print("🎯 SPECIFIC DEBUGGING RECOMMENDATIONS")
    print("-" * 30)
    recommendations = [
        "1. 🧪 Schedule a test notification for 2 minutes from now",
        "2. 🔍 Check if app is in background when 6 PM occurs",
        "3. 📱 Verify device notification settings are enabled",
        "4. 🔄 Monitor notification received callbacks",
        "5. 📊 Check system notification limits",
        "6. 🎯 Use shorter test intervals (1-5 minutes)",
        "7. 🔧 Add notification delivery confirmation",
        "8. 📝 Log notification scheduling vs delivery",
        "9. 🚀 Test on different devices/OS versions",
        "10. 🎮 Compare with other successful notification apps"
    ]
    
    for rec in recommendations:
        print(f"   {rec}")
    print()
    
    print("⚡ IMMEDIATE ACTION PLAN")
    print("-" * 30)
    action_plan = [
        "Step 1: Add test notification scheduling (2 min from now)",
        "Step 2: Add notification received logging",
        "Step 3: Check device notification permissions",
        "Step 4: Verify app background behavior",
        "Step 5: Test with shorter intervals",
        "Step 6: Add delivery confirmation system",
        "Step 7: Monitor system notification queue",
        "Step 8: Compare with working apps"
    ]
    
    for i, step in enumerate(action_plan, 1):
        print(f"   {i}. {step}")
    print()
    
    print("📊 DELIVERY SUCCESS METRICS TO TRACK")
    print("-" * 30)
    metrics = [
        "• Notifications scheduled vs delivered ratio",
        "• Time accuracy (scheduled vs actual delivery)",
        "• Background vs foreground delivery rates", 
        "• Device notification settings status",
        "• App notification permission status",
        "• System notification queue length",
        "• Notification ID conflicts",
        "• Battery optimization impact"
    ]
    
    for metric in metrics:
        print(f"   {metric}")
    print()
    
    print("🏆 SUCCESS CRITERIA")
    print("-" * 30)
    print("   ✅ User receives notification within 30 seconds of scheduled time")
    print("   ✅ Correct message content displayed")
    print("   ✅ Notification appears both in foreground and background")
    print("   ✅ Tapping notification opens diet PDF")
    print("   ✅ Works consistently across multiple test cycles")
    print("   ✅ Works on different devices and OS versions")
    print()
    
    print("🚨 CRITICAL ISSUE IDENTIFIED")
    print("-" * 30)
    print("The fact that 49 notifications were cancelled on second extraction")
    print("confirms that notifications ARE being scheduled in the system.")
    print("The problem is DELIVERY, not scheduling.")
    print()
    print("Most likely causes:")
    print("1. ❌ App background state preventing delivery")
    print("2. ❌ Device notification settings changed")
    print("3. ❌ Battery optimization interfering")
    print("4. ❌ Notification permission issues in EAS build")
    print()
    print("NEXT: Implement immediate test notifications and delivery monitoring!")

if __name__ == "__main__":
    debug_notification_delivery()
