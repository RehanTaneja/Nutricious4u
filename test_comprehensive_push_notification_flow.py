#!/usr/bin/env python3
"""
COMPREHENSIVE PUSH NOTIFICATION SYSTEM TESTING
This script thoroughly tests the entire push notification flow from end-to-end.
Checks all possible failure points and edge cases.
"""

import sys
import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional

# Firebase imports
import firebase_admin
from firebase_admin import credentials, firestore

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

# Test results storage
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "critical_issues": [],
    "warnings": [],
    "recommendations": []
}

def log_test_result(test_name: str, status: str, details: Dict):
    """Log a test result"""
    test_results["tests"].append({
        "name": test_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details
    })

def add_critical_issue(issue: str, details: str):
    """Add a critical issue"""
    test_results["critical_issues"].append({
        "issue": issue,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def add_warning(warning: str, details: str):
    """Add a warning"""
    test_results["warnings"].append({
        "warning": warning,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def add_recommendation(recommendation: str, details: str):
    """Add a recommendation"""
    test_results["recommendations"].append({
        "recommendation": recommendation,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

# Initialize Firebase
print_header("INITIALIZING FIREBASE")
try:
    # Try to get existing app
    db = firestore.client()
    print_success("Firebase already initialized")
except:
    # Initialize new app
    try:
        # Try multiple possible paths
        possible_paths = [
            'services/firebase_service_account.json',
            'backend/services/firebase_service_account.json',
            'firebase_service_account.json'
        ]
        
        cred_path = None
        for path in possible_paths:
            if os.path.exists(path):
                cred_path = path
                break
        
        if not cred_path:
            print_error("Firebase service account file not found")
            print_info("Attempting to initialize with environment variables...")
            # Try environment-based initialization
            import os
            project_id = os.getenv('FIREBASE_PROJECT_ID', 'nutricious4u-2024')
            private_key = os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
            client_email = os.getenv('FIREBASE_CLIENT_EMAIL', '')
            
            if not private_key or not client_email:
                print_error("Firebase credentials not found. Please ensure firebase_service_account.json exists or set environment variables.")
                sys.exit(1)
            
            service_account_info = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
            }
            cred = credentials.Certificate(service_account_info)
        else:
            print_info(f"Found Firebase service account at: {cred_path}")
            cred = credentials.Certificate(cred_path)
        
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print_success("Firebase initialized successfully")
    except Exception as e:
        print_error(f"Failed to initialize Firebase: {e}")
        sys.exit(1)

# Backend URL
BACKEND_URL = "https://nutricious4u-production.up.railway.app/api"

# =============================================================================
# TEST 1: VERIFY FIRESTORE COLLECTIONS STRUCTURE
# =============================================================================
def test_firestore_structure():
    print_header("TEST 1: FIRESTORE COLLECTIONS STRUCTURE")
    
    issues_found = []
    
    # Check user_profiles collection
    print_info("Checking user_profiles collection...")
    try:
        profiles = db.collection('user_profiles').limit(5).stream()
        profile_count = 0
        sample_profile = None
        for profile in profiles:
            profile_count += 1
            if sample_profile is None:
                sample_profile = profile.to_dict()
        
        if profile_count > 0:
            print_success(f"Found {profile_count} user profiles")
            print_info(f"Sample profile fields: {list(sample_profile.keys()) if sample_profile else 'None'}")
            
            # Check if sample profile has required fields
            if sample_profile:
                required_fields = ['expoPushToken', 'notificationToken']
                has_token = any(field in sample_profile for field in required_fields)
                if not has_token:
                    issues_found.append("User profiles missing push token fields")
                    print_warning("Sample profile does not have expoPushToken or notificationToken field")
                    add_critical_issue(
                        "Missing Push Tokens",
                        "User profiles do not have expoPushToken or notificationToken fields. Users cannot receive push notifications without tokens."
                    )
                else:
                    print_success("Sample profile has token field")
        else:
            issues_found.append("No user profiles found")
            print_warning("No user profiles found in database")
            
    except Exception as e:
        issues_found.append(f"Error accessing user_profiles: {str(e)}")
        print_error(f"Error accessing user_profiles: {e}")
    
    # Check chats collection
    print_info("Checking chats collection...")
    try:
        chats = db.collection('chats').limit(5).stream()
        chat_count = 0
        for chat in chats:
            chat_count += 1
        
        if chat_count > 0:
            print_success(f"Found {chat_count} chat conversations")
        else:
            print_warning("No chat conversations found")
            
    except Exception as e:
        issues_found.append(f"Error accessing chats: {str(e)}")
        print_error(f"Error accessing chats: {e}")
    
    # Check appointments collection
    print_info("Checking appointments collection...")
    try:
        appointments = db.collection('appointments').limit(5).stream()
        appointment_count = 0
        for appt in appointments:
            appointment_count += 1
        
        if appointment_count > 0:
            print_success(f"Found {appointment_count} appointments")
        else:
            print_warning("No appointments found")
            
    except Exception as e:
        issues_found.append(f"Error accessing appointments: {str(e)}")
        print_error(f"Error accessing appointments: {e}")
    
    status = "PASS" if len(issues_found) == 0 else "FAIL"
    log_test_result("Firestore Structure Check", status, {
        "issues_found": issues_found
    })
    
    return len(issues_found) == 0

# =============================================================================
# TEST 2: CHECK USER TOKENS REGISTRATION
# =============================================================================
def test_user_tokens():
    print_header("TEST 2: USER PUSH TOKEN REGISTRATION")
    
    issues_found = []
    token_stats = {
        "total_users": 0,
        "users_with_expo_token": 0,
        "users_with_notification_token": 0,
        "users_with_no_token": 0,
        "dietician_has_token": False,
        "sample_tokens": []
    }
    
    print_info("Scanning all user profiles for push tokens...")
    
    try:
        profiles = db.collection('user_profiles').stream()
        
        for profile in profiles:
            token_stats["total_users"] += 1
            data = profile.to_dict()
            user_id = profile.id
            
            # Check for tokens
            expo_token = data.get('expoPushToken')
            notif_token = data.get('notificationToken')
            is_dietician = data.get('isDietician', False)
            
            if expo_token:
                token_stats["users_with_expo_token"] += 1
                if len(token_stats["sample_tokens"]) < 3:
                    token_stats["sample_tokens"].append({
                        "user_id": user_id,
                        "token_preview": expo_token[:30] + "...",
                        "is_dietician": is_dietician,
                        "last_update": data.get('lastTokenUpdate', 'Unknown')
                    })
                
                # Verify token format
                if not expo_token.startswith("ExponentPushToken"):
                    issues_found.append(f"User {user_id} has invalid token format: {expo_token[:20]}...")
                    print_error(f"User {user_id} has invalid token format")
                    add_critical_issue(
                        f"Invalid Token Format for User {user_id}",
                        f"Token does not start with 'ExponentPushToken': {expo_token[:30]}..."
                    )
            elif notif_token:
                token_stats["users_with_notification_token"] += 1
            else:
                token_stats["users_with_no_token"] += 1
                print_warning(f"User {user_id} has no push token registered")
                
                if not is_dietician:  # Only warn for non-dietician users
                    add_warning(
                        f"User {user_id} Missing Token",
                        "User has not registered for push notifications. They need to log in and grant notification permissions."
                    )
            
            # Check dietician specifically
            if is_dietician:
                if expo_token or notif_token:
                    token_stats["dietician_has_token"] = True
                    print_success(f"Dietician ({user_id}) has push token registered")
                else:
                    print_error(f"Dietician ({user_id}) has NO push token registered")
                    add_critical_issue(
                        "Dietician Missing Push Token",
                        "Dietician account does not have a push token. They will not receive any push notifications for messages or appointments."
                    )
        
        # Print summary
        print_info(f"\n{'='*60}")
        print_info(f"TOKEN REGISTRATION SUMMARY:")
        print_info(f"{'='*60}")
        print_info(f"Total users: {token_stats['total_users']}")
        print_info(f"Users with expoPushToken: {token_stats['users_with_expo_token']}")
        print_info(f"Users with notificationToken: {token_stats['users_with_notification_token']}")
        print_info(f"Users with NO token: {token_stats['users_with_no_token']}")
        print_info(f"Dietician has token: {token_stats['dietician_has_token']}")
        
        if token_stats["sample_tokens"]:
            print_info("\nSample tokens:")
            for sample in token_stats["sample_tokens"]:
                print_info(f"  - User: {sample['user_id'][:20]}")
                print_info(f"    Token: {sample['token_preview']}")
                print_info(f"    Dietician: {sample['is_dietician']}")
                print_info(f"    Last Update: {sample['last_update']}")
        
        # Critical check: if no users have tokens, that's a major issue
        if token_stats["users_with_expo_token"] == 0 and token_stats["users_with_notification_token"] == 0:
            add_critical_issue(
                "NO USERS HAVE PUSH TOKENS",
                "Not a single user has registered for push notifications. This means the token registration flow is completely broken."
            )
            add_recommendation(
                "Fix Token Registration",
                "Check the registerForPushNotificationsAsync function in mobileapp/services/firebase.ts. Ensure it's being called after user login and that permissions are being requested correctly."
            )
        
        # If dietician doesn't have token, that's critical
        if not token_stats["dietician_has_token"]:
            add_recommendation(
                "Dietician Needs to Re-Login",
                "Ask the dietician to log out and log back in to the mobile app, and grant notification permissions when prompted."
            )
            
    except Exception as e:
        issues_found.append(f"Error scanning user tokens: {str(e)}")
        print_error(f"Error scanning user tokens: {e}")
    
    status = "PASS" if len(issues_found) == 0 and token_stats["dietician_has_token"] else "FAIL"
    log_test_result("User Token Registration", status, {
        "issues_found": issues_found,
        "token_stats": token_stats
    })
    
    return len(issues_found) == 0

# =============================================================================
# TEST 3: TEST BACKEND PUSH NOTIFICATION ENDPOINT
# =============================================================================
def test_backend_endpoint():
    print_header("TEST 3: BACKEND PUSH NOTIFICATION ENDPOINT")
    
    issues_found = []
    
    # Test 1: Check if endpoint is reachable
    print_info("Test 3.1: Checking if backend is reachable...")
    try:
        response = requests.get(f"{BACKEND_URL.replace('/api', '')}/health", timeout=10)
        if response.status_code == 200:
            print_success("Backend is reachable")
        else:
            print_warning(f"Backend health check returned status {response.status_code}")
    except Exception as e:
        issues_found.append(f"Backend not reachable: {str(e)}")
        print_error(f"Backend not reachable: {e}")
        add_critical_issue(
            "Backend Not Reachable",
            f"Cannot reach backend at {BACKEND_URL}. Push notifications cannot work if backend is down."
        )
    
    # Test 2: Test message notification endpoint
    print_info("\nTest 3.2: Testing message notification endpoint...")
    test_message_payload = {
        "type": "message",
        "recipientId": "test_user_id",
        "senderName": "Test Sender",
        "message": "This is a test message",
        "isFromDietician": False
    }
    
    try:
        print_info(f"Sending test payload: {json.dumps(test_message_payload, indent=2)}")
        response = requests.post(
            f"{BACKEND_URL}/push-notifications/send",
            json=test_message_payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print_info(f"Response status: {response.status_code}")
        print_info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print_success("Backend endpoint returned success (but user likely doesn't exist)")
            else:
                print_warning("Backend endpoint returned success=false")
                add_warning(
                    "Backend Endpoint Returns Failure",
                    f"Endpoint is working but returned success=false. This is expected for test user. Real users might have different issues."
                )
        elif response.status_code == 500:
            print_warning("Backend returned 500 error - check backend logs")
            issues_found.append("Backend returned 500 error for message notification")
            add_warning(
                "Backend Error for Message Notification",
                f"Backend returned 500 error. Check backend logs for details: {response.text}"
            )
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            issues_found.append(f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        issues_found.append(f"Error testing message notification endpoint: {str(e)}")
        print_error(f"Error testing message notification endpoint: {e}")
        add_critical_issue(
            "Message Notification Endpoint Failed",
            f"Failed to call message notification endpoint: {str(e)}"
        )
    
    # Test 3: Test appointment notification endpoint
    print_info("\nTest 3.3: Testing appointment notification endpoint...")
    test_appointment_payload = {
        "type": "appointment_scheduled",
        "userName": "Test User",
        "date": "2025-11-05",
        "timeSlot": "10:00"
    }
    
    try:
        print_info(f"Sending test payload: {json.dumps(test_appointment_payload, indent=2)}")
        response = requests.post(
            f"{BACKEND_URL}/push-notifications/send",
            json=test_appointment_payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print_info(f"Response status: {response.status_code}")
        print_info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print_success("Appointment notification endpoint is working")
        elif response.status_code == 500:
            print_warning("Backend returned 500 error - check backend logs")
            issues_found.append("Backend returned 500 error for appointment notification")
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            issues_found.append(f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        issues_found.append(f"Error testing appointment notification endpoint: {str(e)}")
        print_error(f"Error testing appointment notification endpoint: {e}")
    
    status = "PASS" if len(issues_found) == 0 else "WARNING"
    log_test_result("Backend Endpoint Test", status, {
        "issues_found": issues_found
    })
    
    return len(issues_found) == 0

# =============================================================================
# TEST 4: TEST EXPO PUSH NOTIFICATION SERVICE
# =============================================================================
def test_expo_push_service():
    print_header("TEST 4: EXPO PUSH NOTIFICATION SERVICE")
    
    issues_found = []
    
    # Get a real token from database
    print_info("Finding a real user token from database...")
    real_token = None
    try:
        profiles = db.collection('user_profiles').stream()
        for profile in profiles:
            data = profile.to_dict()
            token = data.get('expoPushToken') or data.get('notificationToken')
            if token and token.startswith("ExponentPushToken"):
                real_token = token
                print_success(f"Found real token: {token[:30]}...")
                break
    except Exception as e:
        print_error(f"Error finding real token: {e}")
        issues_found.append(f"Could not find real token: {str(e)}")
    
    if real_token:
        # Test sending to Expo Push Service
        print_info("\nTesting Expo Push Notification Service...")
        
        test_notification = {
            "to": real_token,
            "sound": "default",
            "title": "Test Notification",
            "body": "This is a test push notification from the diagnostic script",
            "data": {
                "type": "test",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            print_info(f"Sending test notification to Expo:")
            print_info(f"  Token: {real_token[:30]}...")
            print_info(f"  Title: {test_notification['title']}")
            print_info(f"  Body: {test_notification['body']}")
            
            response = requests.post(
                "https://exp.host/--/api/v2/push/send",
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
                json=test_notification,
                timeout=10
            )
            
            print_info(f"\nExpo Response:")
            print_info(f"  Status Code: {response.status_code}")
            print_info(f"  Response Body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print_info(f"  Parsed Response: {json.dumps(result, indent=2)}")
                
                # Check for errors in response
                if 'data' in result:
                    data = result['data']
                    if isinstance(data, dict):
                        if data.get('status') == 'error':
                            error_message = data.get('message', 'Unknown error')
                            print_error(f"Expo returned error: {error_message}")
                            issues_found.append(f"Expo error: {error_message}")
                            add_critical_issue(
                                "Expo Push Service Error",
                                f"Expo returned error when sending notification: {error_message}. This could mean the token is invalid or expired."
                            )
                            add_recommendation(
                                "User Needs to Re-Register Token",
                                "Ask the user to log out and log back in to refresh their push notification token."
                            )
                        elif data.get('status') == 'ok':
                            print_success("Expo accepted the notification successfully!")
                            print_info("Check if the notification was received on the device.")
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('status') == 'error':
                                error_message = item.get('message', 'Unknown error')
                                print_error(f"Expo returned error: {error_message}")
                                issues_found.append(f"Expo error: {error_message}")
                else:
                    print_success("Expo accepted the notification!")
            else:
                print_error(f"Expo returned non-200 status: {response.status_code}")
                issues_found.append(f"Expo returned status {response.status_code}")
                add_critical_issue(
                    "Expo Push Service Unavailable",
                    f"Expo push service returned status {response.status_code}. The service might be down or the request is malformed."
                )
                
        except Exception as e:
            print_error(f"Error testing Expo push service: {e}")
            issues_found.append(f"Expo push service error: {str(e)}")
            add_critical_issue(
                "Cannot Reach Expo Push Service",
                f"Failed to send test notification to Expo: {str(e)}"
            )
    else:
        print_error("No valid token found in database - cannot test Expo push service")
        issues_found.append("No valid token found for testing")
        add_critical_issue(
            "No Valid Tokens Found",
            "Cannot test Expo push service because no valid tokens are registered in the database."
        )
    
    status = "PASS" if len(issues_found) == 0 else "FAIL"
    log_test_result("Expo Push Service Test", status, {
        "issues_found": issues_found,
        "token_used": real_token[:30] + "..." if real_token else None
    })
    
    return len(issues_found) == 0

# =============================================================================
# TEST 5: SIMULATE REAL MESSAGE FLOW
# =============================================================================
def test_real_message_flow():
    print_header("TEST 5: SIMULATE REAL MESSAGE SENDING FLOW")
    
    issues_found = []
    
    # Find a real user and dietician
    print_info("Finding real user and dietician...")
    
    user_id = None
    user_name = None
    dietician_id = None
    
    try:
        profiles = db.collection('user_profiles').stream()
        for profile in profiles:
            data = profile.to_dict()
            if data.get('isDietician'):
                dietician_id = profile.id
                print_success(f"Found dietician: {dietician_id}")
            elif not user_id:
                user_id = profile.id
                user_name = f"{data.get('firstName', 'User')} {data.get('lastName', '')}".strip()
                print_success(f"Found user: {user_id} ({user_name})")
            
            if user_id and dietician_id:
                break
                
    except Exception as e:
        print_error(f"Error finding users: {e}")
        issues_found.append(f"Could not find users: {str(e)}")
    
    if user_id and dietician_id:
        # Step 1: Add message to Firestore (simulating frontend)
        print_info("\nStep 1: Adding message to Firestore...")
        try:
            message_data = {
                'text': 'Test message from diagnostic script',
                'sender': 'user',
                'timestamp': firestore.SERVER_TIMESTAMP,
            }
            
            db.collection('chats').document(user_id).collection('messages').add(message_data)
            print_success("Message added to Firestore")
            
            # Update chat summary
            db.collection('chats').document(user_id).set({
                'userId': user_id,
                'lastMessage': message_data['text'],
                'lastMessageTimestamp': firestore.SERVER_TIMESTAMP,
            }, merge=True)
            print_success("Chat summary updated")
            
        except Exception as e:
            print_error(f"Error adding message to Firestore: {e}")
            issues_found.append(f"Failed to add message: {str(e)}")
        
        # Step 2: Send push notification (simulating frontend)
        print_info("\nStep 2: Sending push notification via backend...")
        try:
            notification_payload = {
                "type": "message",
                "recipientId": "dietician",
                "senderName": user_name,
                "message": "Test message from diagnostic script",
                "isFromDietician": False
            }
            
            print_info(f"Payload: {json.dumps(notification_payload, indent=2)}")
            
            response = requests.post(
                f"{BACKEND_URL}/push-notifications/send",
                json=notification_payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            print_info(f"Response status: {response.status_code}")
            print_info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print_success("Push notification sent successfully!")
                else:
                    print_error("Push notification failed!")
                    issues_found.append("Backend returned success=false")
                    add_critical_issue(
                        "Push Notification Send Failed",
                        "Backend endpoint returned success=false. Check backend logs for details about why the notification failed."
                    )
            else:
                print_error(f"Backend returned error status: {response.status_code}")
                issues_found.append(f"Backend error: {response.status_code}")
                
        except Exception as e:
            print_error(f"Error sending push notification: {e}")
            issues_found.append(f"Failed to send notification: {str(e)}")
    else:
        print_error("Could not find both user and dietician")
        issues_found.append("Missing user or dietician")
    
    status = "PASS" if len(issues_found) == 0 else "FAIL"
    log_test_result("Real Message Flow Simulation", status, {
        "issues_found": issues_found,
        "user_id": user_id,
        "dietician_id": dietician_id
    })
    
    return len(issues_found) == 0

# =============================================================================
# TEST 6: CHECK APP.JSON CONFIGURATION
# =============================================================================
def test_app_json_config():
    print_header("TEST 6: APP.JSON NOTIFICATION CONFIGURATION")
    
    issues_found = []
    
    print_info("Checking app.json configuration...")
    try:
        with open('app.json', 'r') as f:
            app_config = json.load(f)
        
        expo_config = app_config.get('expo', {})
        
        # Check for notification settings
        notification_config = expo_config.get('notification', {})
        android_config = expo_config.get('android', {})
        ios_config = expo_config.get('ios', {})
        
        print_info("Current configuration:")
        print_info(f"  Notification config: {json.dumps(notification_config, indent=4)}")
        print_info(f"  Android config: {json.dumps(android_config, indent=4)}")
        print_info(f"  iOS config: {json.dumps(ios_config, indent=4)}")
        
        # Check for notification icon (Android)
        if 'notification' in android_config and 'icon' in android_config['notification']:
            print_success("Android notification icon configured")
        else:
            print_warning("Android notification icon not configured")
            add_recommendation(
                "Add Android Notification Icon",
                "Add notification icon to app.json: expo.android.notification.icon"
            )
        
        # Check for push notification entitlements (iOS)
        if 'infoPlist' in ios_config:
            print_success("iOS infoPlist configured")
        else:
            print_warning("iOS infoPlist not configured")
            add_recommendation(
                "Add iOS Push Notification Entitlements",
                "Add proper iOS configuration for push notifications in app.json"
            )
        
    except FileNotFoundError:
        print_error("app.json not found!")
        issues_found.append("app.json file not found")
        add_critical_issue(
            "app.json Missing",
            "Cannot find app.json file. This is required for Expo configuration."
        )
    except Exception as e:
        print_error(f"Error reading app.json: {e}")
        issues_found.append(f"Failed to read app.json: {str(e)}")
    
    status = "PASS" if len(issues_found) == 0 else "WARNING"
    log_test_result("App.json Configuration", status, {
        "issues_found": issues_found
    })
    
    return len(issues_found) == 0

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    print_header("COMPREHENSIVE PUSH NOTIFICATION DIAGNOSTIC TEST")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Backend URL: {BACKEND_URL}")
    
    # Run all tests
    test_results_summary = {}
    
    test_results_summary['firestore_structure'] = test_firestore_structure()
    time.sleep(1)
    
    test_results_summary['user_tokens'] = test_user_tokens()
    time.sleep(1)
    
    test_results_summary['backend_endpoint'] = test_backend_endpoint()
    time.sleep(1)
    
    test_results_summary['expo_push_service'] = test_expo_push_service()
    time.sleep(1)
    
    test_results_summary['real_message_flow'] = test_real_message_flow()
    time.sleep(1)
    
    test_results_summary['app_json_config'] = test_app_json_config()
    
    # Print final summary
    print_header("FINAL TEST SUMMARY")
    
    print_info("Test Results:")
    for test_name, passed in test_results_summary.items():
        status_icon = "✅" if passed else "❌"
        print(f"  {status_icon} {test_name}: {'PASSED' if passed else 'FAILED'}")
    
    # Print critical issues
    if test_results["critical_issues"]:
        print_error(f"\n🚨 CRITICAL ISSUES FOUND: {len(test_results['critical_issues'])}")
        for i, issue in enumerate(test_results["critical_issues"], 1):
            print_error(f"\n{i}. {issue['issue']}")
            print_error(f"   Details: {issue['details']}")
    
    # Print warnings
    if test_results["warnings"]:
        print_warning(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
        for i, warning in enumerate(test_results["warnings"], 1):
            print_warning(f"\n{i}. {warning['warning']}")
            print_warning(f"   Details: {warning['details']}")
    
    # Print recommendations
    if test_results["recommendations"]:
        print_info(f"\n💡 RECOMMENDATIONS: {len(test_results['recommendations'])}")
        for i, rec in enumerate(test_results["recommendations"], 1):
            print_info(f"\n{i}. {rec['recommendation']}")
            print_info(f"   Details: {rec['details']}")
    
    # Save results to file
    output_file = f"push_notification_diagnostic_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print_success(f"\n✅ Full results saved to: {output_file}")
    
    print_info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

