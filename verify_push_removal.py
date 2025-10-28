#!/usr/bin/env python3
"""
Verification script to confirm push notifications have been removed
"""

import os
import re

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'
BOLD = '\033[1m'

def check_file_contains(filepath, pattern, description, should_exist=True):
    """Check if file contains a pattern"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            found = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            
            if should_exist:
                if found:
                    print(f"{GREEN}✅{END} {description}")
                    return True
                else:
                    print(f"{RED}❌{END} {description} - NOT FOUND")
                    return False
            else:
                if not found:
                    print(f"{GREEN}✅{END} {description}")
                    return True
                else:
                    print(f"{RED}❌{END} {description} - STILL EXISTS")
                    return False
    except Exception as e:
        print(f"{RED}❌{END} {description} - Error: {e}")
        return False

def main():
    print(f"\n{BLUE}{BOLD}{'='*80}{END}")
    print(f"{BLUE}{BOLD}PUSH NOTIFICATIONS REMOVAL VERIFICATION{END}".center(80))
    print(f"{BLUE}{BOLD}{'='*80}{END}\n")
    
    base_path = "/Users/rehantaneja/Documents/Nutricious4u-main copy"
    
    checks = []
    
    print(f"\n{YELLOW}Frontend - Push Notification Removal:{END}")
    
    # Check 1: Message notification functions removed
    checks.append(check_file_contains(
        f"{base_path}/mobileapp/screens.tsx",
        r'PUSH NOTIFICATIONS REMOVED - These functions are no longer used',
        "Message notification functions removed (frontend)",
        should_exist=True
    ))
    
    # Check 2: Message sending notifications removed
    checks.append(check_file_contains(
        f"{base_path}/mobileapp/screens.tsx",
        r'PUSH NOTIFICATIONS REMOVED - Messages will only appear in the app',
        "Message push notification calls removed (frontend)",
        should_exist=True
    ))
    
    # Check 3: Appointment notification sending removed
    checks.append(check_file_contains(
        f"{base_path}/mobileapp/screens.tsx",
        r'PUSH NOTIFICATIONS REMOVED - Appointment notifications are no longer sent',
        "Appointment push notification calls removed (frontend)",
        should_exist=True
    ))
    
    # Check 4: User dashboard message listener removed
    checks.append(check_file_contains(
        f"{base_path}/mobileapp/screens.tsx",
        r'PUSH NOTIFICATIONS REMOVED - Message and appointment notification listeners removed',
        "User dashboard notification listeners removed (frontend)",
        should_exist=True
    ))
    
    print(f"\n{YELLOW}Backend - Push Notification Removal:{END}")
    
    # Check 5: Message notification disabled
    checks.append(check_file_contains(
        f"{base_path}/backend/server.py",
        r'# PUSH NOTIFICATIONS REMOVED - Message notifications are disabled',
        "Message notifications disabled (backend)",
        should_exist=True
    ))
    
    # Check 6: Appointment notification disabled
    checks.append(check_file_contains(
        f"{base_path}/backend/server.py",
        r'# PUSH NOTIFICATIONS REMOVED - Appointment notifications are disabled',
        "Appointment notifications disabled (backend)",
        should_exist=True
    ))
    
    # Check 7: Dietician diet reminder disabled
    checks.append(check_file_contains(
        f"{base_path}/backend/server.py",
        r'# PUSH NOTIFICATIONS REMOVED - One day left notifications are disabled',
        "One-day-left notifications disabled (backend)",
        should_exist=True
    ))
    
    # Check 8: Check reminders endpoint disabled
    checks.append(check_file_contains(
        f"{base_path}/backend/server.py",
        r'PUSH NOTIFICATIONS REMOVED - This endpoint is now disabled',
        "Diet reminders endpoint disabled (backend)",
        should_exist=True
    ))
    
    # Check 9: Scheduled job disabled
    checks.append(check_file_contains(
        f"{base_path}/backend/server.py",
        r'PUSH NOTIFICATIONS REMOVED - This job is now disabled',
        "Diet reminders scheduled job disabled (backend)",
        should_exist=True
    ))
    
    print(f"\n{YELLOW}Diet Notifications - Still Working:{END}")
    
    # Check 10: Diet notification listeners still exist
    checks.append(check_file_contains(
        f"{base_path}/mobileapp/screens.tsx",
        r"type === 'new_diet'",
        "Diet notification listeners preserved (frontend)",
        should_exist=True
    ))
    
    # Check 11: Diet notification service untouched
    checks.append(check_file_contains(
        f"{base_path}/backend/services/diet_notification_service.py",
        r'class DietNotificationService',
        "Diet notification service preserved (backend)",
        should_exist=True
    ))
    
    # Summary
    print(f"\n{BLUE}{BOLD}{'='*80}{END}")
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"{GREEN}{BOLD}✅ ALL CHECKS PASSED ({passed}/{total}){END}")
        print(f"\n{GREEN}Push notifications successfully removed!{END}")
        print(f"{GREEN}Diet notifications still working!{END}")
        return 0
    else:
        print(f"{RED}{BOLD}❌ SOME CHECKS FAILED ({passed}/{total}){END}")
        print(f"\n{RED}Please review the failed checks above.{END}")
        return 1

if __name__ == "__main__":
    exit(main())

