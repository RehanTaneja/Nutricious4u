#!/usr/bin/env python3
"""
Quick verification script to check that all message notification fixes are in place
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

def check_file_contains(filepath, pattern, description):
    """Check if file contains a pattern"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                print(f"{GREEN}✅{END} {description}")
                return True
            else:
                print(f"{RED}❌{END} {description}")
                return False
    except Exception as e:
        print(f"{RED}❌{END} {description} - Error: {e}")
        return False

def main():
    print(f"\n{BLUE}{BOLD}{'='*80}{END}")
    print(f"{BLUE}{BOLD}MESSAGE NOTIFICATION FIX VERIFICATION{END}".center(80))
    print(f"{BLUE}{BOLD}{'='*80}{END}\n")
    
    base_path = "/Users/rehantaneja/Documents/Nutricious4u-main copy"
    
    checks = []
    
    # Check 1: Backend - fromDietician flag
    print(f"\n{YELLOW}Backend Fixes:{END}")
    checks.append(check_file_contains(
        f"{base_path}/backend/services/simple_notification_service.py",
        r'fromDietician.*=.*True',
        "Backend includes 'fromDietician' flag in notification data"
    ))
    
    # Check 2: Backend - fromUser flag
    checks.append(check_file_contains(
        f"{base_path}/backend/services/simple_notification_service.py",
        r'fromUser.*=.*sender_user_id',
        "Backend includes 'fromUser' flag in notification data"
    ))
    
    # Check 3: Backend - dietician recipient handling
    checks.append(check_file_contains(
        f"{base_path}/backend/services/simple_notification_service.py",
        r'if user_id == "dietician"',
        "Backend handles 'dietician' as special recipient"
    ))
    
    # Check 4: Backend - get_dietician_notification_token call
    checks.append(check_file_contains(
        f"{base_path}/backend/services/simple_notification_service.py",
        r'get_dietician_notification_token\(\)',
        "Backend uses get_dietician_notification_token() for dietician"
    ))
    
    # Check 5: Backend - sender_user_id parameter
    checks.append(check_file_contains(
        f"{base_path}/backend/services/simple_notification_service.py",
        r'def send_message_notification\(.*sender_user_id',
        "Backend accepts sender_user_id parameter"
    ))
    
    # Check 6: Backend endpoint - passes senderUserId
    checks.append(check_file_contains(
        f"{base_path}/backend/server.py",
        r'sender_user_id.*=.*request\.get\(["\']senderUserId["\']\)',
        "Backend endpoint extracts senderUserId from request"
    ))
    
    # Check 7: Backend endpoint - passes to service
    checks.append(check_file_contains(
        f"{base_path}/backend/server.py",
        r'send_message_notification\(.*sender_user_id\)',
        "Backend endpoint passes senderUserId to service"
    ))
    
    # Check 8: Debug endpoint exists
    checks.append(check_file_contains(
        f"{base_path}/backend/server.py",
        r'@api_router\.get\("/notifications/debug/token/\{user_id\}"\)',
        "Debug endpoint for token status exists"
    ))
    
    print(f"\n{YELLOW}Frontend Fixes:{END}")
    
    # Check 9: Frontend API - sends senderUserId
    checks.append(check_file_contains(
        f"{base_path}/mobileapp/services/api.ts",
        r'senderUserId.*:.*senderUserId',
        "Frontend API sends senderUserId in request"
    ))
    
    print(f"\n{YELLOW}Frontend Handlers:{END}")
    
    # Check 10: User dashboard - fromDietician handler
    checks.append(check_file_contains(
        f"{base_path}/mobileapp/screens.tsx",
        r"data\?\.type === 'message_notification' && data\?\.fromDietician",
        "User dashboard checks for fromDietician flag"
    ))
    
    # Check 11: Dietician dashboard - fromUser handler
    checks.append(check_file_contains(
        f"{base_path}/mobileapp/screens.tsx",
        r"data\?\.type === 'message_notification' && data\?\.fromUser",
        "Dietician dashboard checks for fromUser flag"
    ))
    
    # Summary
    print(f"\n{BLUE}{BOLD}{'='*80}{END}")
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"{GREEN}{BOLD}✅ ALL CHECKS PASSED ({passed}/{total}){END}")
        print(f"\n{GREEN}Message notification system is correctly implemented!{END}")
        return 0
    else:
        print(f"{RED}{BOLD}❌ SOME CHECKS FAILED ({passed}/{total}){END}")
        print(f"\n{RED}Please review the failed checks above.{END}")
        return 1

if __name__ == "__main__":
    exit(main())

