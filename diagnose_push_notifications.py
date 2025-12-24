#!/usr/bin/env python3
"""
Comprehensive Push Notification Diagnostic Script
This script diagnoses why push notification token registration isn't working.

Run with: python diagnose_push_notifications.py
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}>>> {text}{Colors.END}")
    print(f"{Colors.BLUE}{'-'*50}{Colors.END}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.WHITE}ℹ️  {text}{Colors.END}")

def print_critical(text: str):
    print(f"{Colors.BOLD}{Colors.RED}🚨 CRITICAL: {text}{Colors.END}")

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Check if already initialized
        try:
            app = firebase_admin.get_app()
            print_success("Firebase already initialized")
            return firestore.client()
        except ValueError:
            pass
        
        # Try to find credentials
        cred_paths = [
            'backend/services/firebase_service_account.json',
            'services/firebase_service_account.json',
            'firebase_service_account.json',
        ]
        
        for path in cred_paths:
            if os.path.exists(path):
                print_info(f"Found credentials at: {path}")
                cred = credentials.Certificate(path)
                firebase_admin.initialize_app(cred)
                print_success("Firebase initialized successfully")
                return firestore.client()
        
        # Try environment variables
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        private_key = os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
        client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        
        if project_id and private_key and client_email:
            print_info("Using environment variables for Firebase")
            service_info = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(service_info)
            firebase_admin.initialize_app(cred)
            print_success("Firebase initialized from environment variables")
            return firestore.client()
        
        print_error("Could not find Firebase credentials")
        return None
        
    except Exception as e:
        print_error(f"Firebase initialization failed: {e}")
        return None


def diagnose_user_tokens(db) -> Dict[str, Any]:
    """Analyze all users' push notification tokens"""
    print_section("DIAGNOSING USER PUSH TOKENS")
    
    stats = {
        "total_users": 0,
        "dietician_count": 0,
        "regular_users": 0,
        "with_expo_token": 0,
        "with_notification_token": 0,
        "no_token": 0,
        "android_users": 0,
        "ios_users": 0,
        "unknown_platform": 0,
        "stale_tokens": 0,
        "recent_tokens": 0,
        "invalid_format_tokens": 0,
        "users_by_platform": defaultdict(list),
        "users_without_tokens": [],
        "users_with_tokens": [],
        "dietician_info": None,
    }
    
    try:
        users = db.collection("user_profiles").stream()
        
        for user in users:
            data = user.to_dict()
            user_id = user.id
            stats["total_users"] += 1
            
            is_dietician = data.get("isDietician", False)
            if is_dietician:
                stats["dietician_count"] += 1
                stats["dietician_info"] = {
                    "id": user_id,
                    "email": data.get("email"),
                    "has_token": bool(data.get("expoPushToken") or data.get("notificationToken")),
                    "token_preview": (data.get("expoPushToken") or data.get("notificationToken", ""))[:30] + "..." if (data.get("expoPushToken") or data.get("notificationToken")) else None,
                    "platform": data.get("platform", "unknown"),
                    "last_update": data.get("lastTokenUpdate"),
                }
                continue
            
            stats["regular_users"] += 1
            
            # Platform analysis
            platform = data.get("platform", "unknown")
            if platform == "android":
                stats["android_users"] += 1
            elif platform == "ios":
                stats["ios_users"] += 1
            else:
                stats["unknown_platform"] += 1
            
            # Token analysis
            expo_token = data.get("expoPushToken")
            notif_token = data.get("notificationToken")
            token = expo_token or notif_token
            last_update = data.get("lastTokenUpdate")
            
            user_info = {
                "id": user_id,
                "name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip() or "Unknown",
                "email": data.get("email", ""),
                "platform": platform,
                "has_expo_token": bool(expo_token),
                "has_notif_token": bool(notif_token),
                "token_preview": token[:30] + "..." if token else None,
                "last_update": last_update,
                "subscription": data.get("subscriptionPlan", "unknown"),
            }
            
            if token:
                stats["with_expo_token"] += 1
                stats["users_with_tokens"].append(user_info)
                
                # Check token format
                if not token.startswith("ExponentPushToken"):
                    stats["invalid_format_tokens"] += 1
                    user_info["token_valid"] = False
                else:
                    user_info["token_valid"] = True
                
                # Check staleness
                if last_update:
                    try:
                        update_date = datetime.fromisoformat(last_update.replace('Z', '+00:00').replace('+00:00', ''))
                        days_ago = (datetime.now() - update_date).days
                        user_info["days_since_update"] = days_ago
                        if days_ago > 30:
                            stats["stale_tokens"] += 1
                        else:
                            stats["recent_tokens"] += 1
                    except:
                        pass
                
                stats["users_by_platform"][platform].append(user_info)
            else:
                stats["no_token"] += 1
                stats["users_without_tokens"].append(user_info)
        
        # Print results
        print_info(f"Total users in database: {stats['total_users']}")
        print_info(f"  - Dietician accounts: {stats['dietician_count']}")
        print_info(f"  - Regular users: {stats['regular_users']}")
        
        print(f"\n{Colors.BOLD}Platform Distribution:{Colors.END}")
        print_info(f"  Android users: {stats['android_users']}")
        print_info(f"  iOS users: {stats['ios_users']}")
        print_info(f"  Unknown platform: {stats['unknown_platform']}")
        
        print(f"\n{Colors.BOLD}Token Status:{Colors.END}")
        if stats['with_expo_token'] > 0:
            print_success(f"Users WITH tokens: {stats['with_expo_token']}")
        else:
            print_critical(f"Users WITH tokens: {stats['with_expo_token']}")
            
        if stats['no_token'] > 0:
            print_error(f"Users WITHOUT tokens: {stats['no_token']}")
        else:
            print_success(f"Users WITHOUT tokens: {stats['no_token']}")
            
        print_info(f"Invalid format tokens: {stats['invalid_format_tokens']}")
        print_info(f"Recent tokens (<30 days): {stats['recent_tokens']}")
        print_info(f"Stale tokens (>30 days): {stats['stale_tokens']}")
        
        # Dietician info
        if stats["dietician_info"]:
            print(f"\n{Colors.BOLD}Dietician Account:{Colors.END}")
            d = stats["dietician_info"]
            print_info(f"  ID: {d['id']}")
            print_info(f"  Email: {d['email']}")
            print_info(f"  Platform: {d['platform']}")
            if d['has_token']:
                print_success(f"  Token: {d['token_preview']}")
            else:
                print_error(f"  Token: MISSING!")
            print_info(f"  Last update: {d['last_update']}")
        
        # Show users without tokens
        if stats['users_without_tokens']:
            print(f"\n{Colors.BOLD}{Colors.RED}Users WITHOUT Push Tokens:{Colors.END}")
            for u in stats['users_without_tokens'][:10]:
                print_warning(f"  - {u['name']} ({u['platform']}) - {u['email'] or 'no email'}")
            if len(stats['users_without_tokens']) > 10:
                print_info(f"  ... and {len(stats['users_without_tokens']) - 10} more")
        
        return stats
        
    except Exception as e:
        print_error(f"Error analyzing tokens: {e}")
        import traceback
        traceback.print_exc()
        return stats


def test_expo_push_service():
    """Test if Expo Push Service is reachable and responding"""
    print_section("TESTING EXPO PUSH SERVICE")
    
    try:
        # Test with a dummy (invalid) token to see if service is working
        test_payload = {
            "to": "ExponentPushToken[INVALID_TEST_TOKEN_12345]",
            "title": "Test",
            "body": "Test message",
            "sound": "default"
        }
        
        print_info("Sending test request to Expo Push Service...")
        
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            data=json.dumps(test_payload),
            timeout=10
        )
        
        print_info(f"Response status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print_success("Expo Push Service is reachable!")
            
            # Check for expected error (invalid token)
            if result.get("data", {}).get("status") == "error":
                error_msg = result.get("data", {}).get("message", "")
                if "DeviceNotRegistered" in error_msg or "InvalidCredentials" in error_msg:
                    print_success(f"Service responded correctly with expected error: {error_msg[:50]}...")
                else:
                    print_warning(f"Unexpected error: {error_msg}")
            else:
                print_success("Service responded with OK status")
                
            return True
        else:
            print_error(f"Expo Push Service returned error: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Expo Push Service request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Network error contacting Expo: {e}")
        return False
    except Exception as e:
        print_error(f"Error testing Expo service: {e}")
        return False


def test_send_real_notification(db, test_user_id: Optional[str] = None):
    """Test sending a real notification to a user"""
    print_section("TESTING REAL NOTIFICATION DELIVERY")
    
    if not test_user_id:
        # Find a user with a valid token
        print_info("Looking for a user with a valid push token...")
        
        users = db.collection("user_profiles").stream()
        for user in users:
            data = user.to_dict()
            token = data.get("expoPushToken") or data.get("notificationToken")
            if token and token.startswith("ExponentPushToken"):
                test_user_id = user.id
                test_token = token
                test_name = f"{data.get('firstName', '')} {data.get('lastName', '')}".strip()
                test_platform = data.get("platform", "unknown")
                break
        
        if not test_user_id:
            print_error("No users with valid push tokens found!")
            return False
    else:
        # Get the specified user's token
        doc = db.collection("user_profiles").document(test_user_id).get()
        if not doc.exists:
            print_error(f"User {test_user_id} not found!")
            return False
        data = doc.to_dict()
        test_token = data.get("expoPushToken") or data.get("notificationToken")
        test_name = f"{data.get('firstName', '')} {data.get('lastName', '')}".strip()
        test_platform = data.get("platform", "unknown")
    
    if not test_token:
        print_error(f"User {test_user_id} has no push token!")
        return False
    
    print_info(f"Test user: {test_name} ({test_user_id})")
    print_info(f"Platform: {test_platform}")
    print_info(f"Token: {test_token[:30]}...")
    
    # Send test notification
    test_payload = {
        "to": test_token,
        "title": "🔔 Push Notification Test",
        "body": f"Test at {datetime.now().strftime('%H:%M:%S')} - If you see this, notifications are working!",
        "sound": "default",
        "data": {
            "type": "diagnostic_test",
            "timestamp": datetime.now().isoformat(),
            "test_id": f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    }
    
    print_info("Sending test notification...")
    
    try:
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            data=json.dumps(test_payload),
            timeout=10
        )
        
        result = response.json()
        print_info(f"Expo response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            status = result.get("data", {}).get("status")
            if status == "ok":
                print_success("✅ NOTIFICATION SENT SUCCESSFULLY!")
                print_success(f"Check the device for user: {test_name}")
                return True
            elif status == "error":
                error_msg = result.get("data", {}).get("message", "Unknown error")
                error_details = result.get("data", {}).get("details", {})
                
                print_error(f"Expo returned error: {error_msg}")
                
                if "DeviceNotRegistered" in error_msg:
                    print_critical("Token is invalid/expired! User needs to re-login.")
                elif "InvalidCredentials" in error_msg:
                    print_critical("APNs/FCM credentials are missing! Configure in Expo/EAS.")
                elif error_details:
                    print_error(f"Error details: {error_details}")
                    
                return False
        else:
            print_error(f"HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error sending notification: {e}")
        return False


def check_android_specific_issues(db):
    """Check for Android-specific push notification issues"""
    print_section("ANDROID-SPECIFIC DIAGNOSTICS")
    
    android_users = []
    users = db.collection("user_profiles").stream()
    
    for user in users:
        data = user.to_dict()
        if data.get("platform") == "android" and not data.get("isDietician"):
            android_users.append({
                "id": user.id,
                "name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
                "token": data.get("expoPushToken") or data.get("notificationToken"),
                "last_update": data.get("lastTokenUpdate"),
            })
    
    print_info(f"Total Android users: {len(android_users)}")
    
    with_tokens = [u for u in android_users if u['token']]
    without_tokens = [u for u in android_users if not u['token']]
    
    print_info(f"  With tokens: {len(with_tokens)}")
    print_info(f"  Without tokens: {len(without_tokens)}")
    
    if len(without_tokens) == len(android_users) and len(android_users) > 0:
        print_critical("ALL Android users are missing push tokens!")
        print(f"\n{Colors.BOLD}Possible causes:{Colors.END}")
        print_warning("  1. EXPO_PROJECT_ID not set correctly in app.json/app.config.js")
        print_warning("  2. FCM credentials not configured in EAS")
        print_warning("  3. registerForPushNotificationsAsync function not being called")
        print_warning("  4. Permission denied by users")
        print_warning("  5. Google Play Services not available on devices")
    elif len(without_tokens) > len(with_tokens):
        print_warning(f"Most Android users ({len(without_tokens)}/{len(android_users)}) missing tokens")
    elif without_tokens:
        print_info(f"Some Android users missing tokens: {len(without_tokens)}")
    else:
        print_success("All Android users have tokens!")
    
    # Show Android users without tokens
    if without_tokens:
        print(f"\n{Colors.BOLD}Android users without tokens:{Colors.END}")
        for u in without_tokens[:5]:
            print_warning(f"  - {u['name']} ({u['id'][:8]}...)")


def check_message_notification_flow(db):
    """Check if message notifications can be sent"""
    print_section("MESSAGE NOTIFICATION FLOW CHECK")
    
    # Check if dietician has token
    dietician_token = None
    users = db.collection("user_profiles").where("isDietician", "==", True).limit(1).stream()
    
    for user in users:
        data = user.to_dict()
        dietician_token = data.get("expoPushToken") or data.get("notificationToken")
        dietician_id = user.id
        break
    
    if dietician_token:
        print_success(f"Dietician has push token: {dietician_token[:30]}...")
    else:
        print_critical("Dietician does NOT have a push token!")
        print_warning("  → Users cannot send message notifications to dietician")
        print_info("  Fix: Dietician needs to log into the app and grant notification permissions")
    
    # Check a sample user
    print(f"\n{Colors.BOLD}Checking sample user for notification capability:{Colors.END}")
    
    users = db.collection("user_profiles").stream()
    sample_user = None
    
    for user in users:
        data = user.to_dict()
        if not data.get("isDietician") and data.get("platform") == "android":
            sample_user = {
                "id": user.id,
                "name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
                "token": data.get("expoPushToken") or data.get("notificationToken"),
            }
            break
    
    if sample_user:
        print_info(f"Sample user: {sample_user['name']}")
        if sample_user['token']:
            print_success(f"  Token: {sample_user['token'][:30]}...")
            print_success("  → Dietician CAN send notifications to this user")
        else:
            print_error("  Token: MISSING")
            print_error("  → Dietician CANNOT send notifications to this user")


def generate_diagnosis_report(stats: Dict[str, Any]):
    """Generate a summary diagnosis report"""
    print_header("DIAGNOSIS SUMMARY")
    
    issues_found = []
    recommendations = []
    
    # Check for critical issues
    if stats.get('no_token', 0) > 0:
        pct = (stats['no_token'] / max(stats['regular_users'], 1)) * 100
        if pct >= 90:
            issues_found.append(f"CRITICAL: {pct:.0f}% of users have NO push token")
            recommendations.append("Token registration is completely broken - check App.tsx flow")
        elif pct >= 50:
            issues_found.append(f"SEVERE: {pct:.0f}% of users have NO push token")
            recommendations.append("Token registration failing for many users")
        else:
            issues_found.append(f"WARNING: {pct:.0f}% of users have NO push token")
    
    if stats.get('android_users', 0) > 0:
        android_without = len([u for u in stats.get('users_without_tokens', []) if u.get('platform') == 'android'])
        if android_without == stats['android_users']:
            issues_found.append("CRITICAL: ALL Android users missing tokens")
            recommendations.append("Check FCM configuration in EAS credentials")
            recommendations.append("Verify EXPO_PROJECT_ID in app.json")
    
    if stats.get('dietician_info') and not stats['dietician_info'].get('has_token'):
        issues_found.append("CRITICAL: Dietician has NO push token")
        recommendations.append("Dietician must re-login to the app and grant permissions")
    
    if stats.get('stale_tokens', 0) > stats.get('recent_tokens', 0):
        issues_found.append("WARNING: More stale tokens than recent ones")
        recommendations.append("Users may not be logging in regularly to refresh tokens")
    
    if stats.get('invalid_format_tokens', 0) > 0:
        issues_found.append(f"ERROR: {stats['invalid_format_tokens']} tokens have invalid format")
        recommendations.append("Check token generation in registerForPushNotificationsAsync")
    
    # Print issues
    if issues_found:
        print(f"{Colors.BOLD}{Colors.RED}Issues Found:{Colors.END}")
        for i, issue in enumerate(issues_found, 1):
            print(f"  {i}. {issue}")
    else:
        print_success("No critical issues found with token data!")
    
    # Print recommendations
    if recommendations:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}Recommendations:{Colors.END}")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    # Next steps
    print(f"\n{Colors.BOLD}{Colors.CYAN}Next Steps:{Colors.END}")
    print("  1. Check mobile app logs for '[PUSH TOKEN]' entries")
    print("  2. Verify app.json has correct eas.projectId")
    print("  3. Run 'eas credentials' to check FCM/APNs configuration")
    print("  4. Have a test user log in and check if token appears in Firestore")
    print("  5. Add console.log at start of registerForPushNotificationsAsync")


def main():
    print_header("PUSH NOTIFICATION DIAGNOSTIC TOOL")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    
    # Initialize Firebase
    db = initialize_firebase()
    if not db:
        print_critical("Cannot proceed without Firebase connection")
        sys.exit(1)
    
    # Run diagnostics
    print("\n")
    
    # 1. Check user tokens
    stats = diagnose_user_tokens(db)
    
    # 2. Test Expo Push Service
    test_expo_push_service()
    
    # 3. Check Android-specific issues
    check_android_specific_issues(db)
    
    # 4. Check message notification flow
    check_message_notification_flow(db)
    
    # 5. Generate summary report
    generate_diagnosis_report(stats)
    
    # 6. Optionally send a test notification
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}Would you like to send a test notification? (y/n):{Colors.END} ", end="")
    try:
        response = input().strip().lower()
        if response == 'y':
            test_send_real_notification(db)
    except:
        pass
    
    print_header("DIAGNOSTIC COMPLETE")


if __name__ == "__main__":
    main()

