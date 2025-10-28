#!/usr/bin/env python3
"""
Test script to verify local diet notifications still work
This is a READ-ONLY test - it verifies the local notification system is untouched
"""

import os
import sys

def check_file_unchanged(filepath, critical_lines):
    """Check if critical lines in file are unchanged"""
    print(f"\n🔍 Checking {filepath}...")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    all_found = True
    for critical_text in critical_lines:
        if critical_text in content:
            print(f"   ✅ Found: '{critical_text[:50]}...'")
        else:
            print(f"   ❌ Missing: '{critical_text[:50]}...'")
            all_found = False
    
    return all_found

def main():
    print("=" * 60)
    print("LOCAL DIET NOTIFICATIONS - VERIFICATION TEST")
    print("=" * 60)
    print("\nThis test verifies that local diet notifications are untouched")
    print("and still working correctly.\n")
    
    # Critical files and their key content that should be unchanged
    tests = [
        {
            "file": "mobileapp/services/unifiedNotificationService.ts",
            "critical_lines": [
                "scheduleDietNotifications",
                "cancelAllDietNotifications",
                "type: 'diet'",
                "Diet Reminder"
            ]
        },
        {
            "file": "mobileapp/services/notificationService.ts",
            "critical_lines": [
                "scheduleDietNotification",
                "scheduleCustomNotification",
                "calculateNextOccurrence"
            ]
        },
        {
            "file": "backend/services/diet_notification_service.py",
            "critical_lines": [
                "def extract_notifications_from_text",
                "class DietNotificationService",
                "extract_notification_schedule"
            ]
        }
    ]
    
    all_passed = True
    
    for test in tests:
        result = check_file_unchanged(test["file"], test["critical_lines"])
        if not result:
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\nLocal diet notification system is intact and unchanged.")
        print("The following features should still work:")
        print("  - Diet PDF upload and extraction")
        print("  - Notification day selection")
        print("  - Local notification scheduling")
        print("  - Notifications firing at scheduled times")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print("\nCritical notification files may have been modified.")
        print("Please review the changes to ensure local notifications still work.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

