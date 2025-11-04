#!/usr/bin/env python3
"""
ANDROID PUSH NOTIFICATION TESTING
Tests if Android push notifications are working
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Firebase imports
import firebase_admin
from firebase_admin import credentials, firestore

# Color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

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

# Initialize Firebase
print_header("INITIALIZING FIREBASE")
try:
    db = firestore.client()
    print_success("Firebase already initialized")
except:
    try:
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
        
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print_success("Firebase initialized successfully")
        else:
            print_error("Firebase service account file not found")
            sys.exit(1)
    except Exception as e:
        print_error(f"Failed to initialize Firebase: {e}")
        sys.exit(1)

BACKEND_URL = "https://nutricious4u-production.up.railway.app/api"

# =============================================================================
# TEST 1: FIND ALL ANDROID USERS
# =============================================================================
def find_android_users():
    print_header("TEST 1: FINDING ANDROID USERS")
    
    android_users = []
    ios_users = []
    unknown_users = []
    
    try:
        print_info("Scanning all user profiles...")
        profiles = db.collection('user_profiles').stream()
        
        for profile in profiles:
            data = profile.to_dict()
            user_id = profile.id
            platform = data.get('platform', 'unknown')
            token = data.get('expoPushToken')
            is_dietician = data.get('isDietician', False)
            
            user_info = {
                'id': user_id,
                'platform': platform,
                'has_token': bool(token),
                'token': token,
                'is_dietician': is_dietician,
                'email': data.get('email', 'N/A')
            }
            
            if platform == 'android':
                android_users.append(user_info)
                print_success(f"Found Android user: {user_id} (has token: {bool(token)})")
            elif platform == 'ios':
                ios_users.append(user_info)
                print_info(f"Found iOS user: {user_id} (has token: {bool(token)})")
            else:
                if token:
                    unknown_users.append(user_info)
                    print_warning(f"Found user with token but unknown platform: {user_id}")
        
        print_info(f"\nSummary:")
        print_info(f"  Android users: {len(android_users)}")
        print_info(f"  iOS users: {len(ios_users)}")
        print_info(f"  Unknown platform users with tokens: {len(unknown_users)}")
        
        return android_users, ios_users, unknown_users
        
    except Exception as e:
        print_error(f"Error finding users: {e}")
        return [], [], []

# =============================================================================
# TEST 2: TEST ANDROID PUSH NOTIFICATION VIA EXPO
# =============================================================================
def test_android_expo_push(token):
    print_header("TEST 2: TESTING ANDROID PUSH VIA EXPO")
    
    if not token:
        print_error("No token provided")
        return False
    
    try:
        notification = {
            "to": token,
            "sound": "default",
            "title": "🔔 Android Test Notification",
            "body": "This is a test for Android push notifications. If you see this on an Android device, it's working!",
            "data": {
                "type": "test_android",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        print_info("Sending test notification to Expo for Android...")
        print_info(f"  Token: {token[:40]}...")
        print_info(f"  Title: {notification['title']}")
        print_info(f"  Body: {notification['body']}")
        
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            headers={
                "Accept": "application/json",
                "Accept-encoding": "gzip, deflate",
                "Content-Type": "application/json",
            },
            json=notification,
            timeout=10
        )
        
        print_info(f"\nExpo Response:")
        print_info(f"  Status Code: {response.status_code}")
        print_info(f"  Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print_info(f"  Parsed: {json.dumps(result, indent=2)}")
            
            # Check for errors
            if 'data' in result:
                if isinstance(result['data'], dict):
                    status = result['data'].get('status')
                    if status == 'error':
                        error_msg = result['data'].get('message', 'Unknown error')
                        print_error(f"Expo returned error: {error_msg}")
                        
                        if 'FCM' in error_msg or 'Firebase' in error_msg:
                            print_error("ANDROID PUSH NOTIFICATIONS NOT CONFIGURED!")
                            print_error("FCM (Firebase Cloud Messaging) credentials missing")
                            print_error("Need to configure FCM in Expo")
                        
                        return False
                    elif status == 'ok':
                        print_success("✅✅✅ ANDROID NOTIFICATION SENT SUCCESSFULLY!")
                        print_success("Check the Android device for the notification")
                        return True
                elif isinstance(result['data'], list) and len(result['data']) > 0:
                    status = result['data'][0].get('status')
                    if status == 'error':
                        error_msg = result['data'][0].get('message', 'Unknown error')
                        print_error(f"Expo returned error: {error_msg}")
                        
                        if 'FCM' in error_msg or 'Firebase' in error_msg:
                            print_error("ANDROID PUSH NOTIFICATIONS NOT CONFIGURED!")
                            print_error("FCM credentials missing")
                        
                        return False
                    elif status == 'ok':
                        print_success("✅✅✅ ANDROID NOTIFICATION SENT SUCCESSFULLY!")
                        return True
        else:
            print_error(f"Expo returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error sending to Expo: {e}")
        return False
    
    return False

# =============================================================================
# TEST 3: TEST BACKEND MESSAGE TO ANDROID USER
# =============================================================================
def test_backend_message_to_android(android_user_id):
    print_header("TEST 3: BACKEND MESSAGE NOTIFICATION TO ANDROID USER")
    
    try:
        payload = {
            "type": "message",
            "recipientId": android_user_id,
            "senderName": "Test Sender",
            "message": "Test message to Android user",
            "isFromDietician": True
        }
        
        print_info(f"Payload: {json.dumps(payload, indent=2)}")
        print_info("Calling backend API...")
        
        response = requests.post(
            f"{BACKEND_URL}/push-notifications/send",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print_info(f"Response Status: {response.status_code}")
        print_info(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print_success("✅ Backend returned success=true")
                print_success("Android notification should have been sent!")
                return True
            else:
                print_error("❌ Backend returned success=false")
                print_warning("Check backend logs for details")
                return False
        else:
            print_error(f"Backend returned error status: {response.status_code}")
            return False
        
    except Exception as e:
        print_error(f"Error testing backend: {e}")
        return False

# =============================================================================
# TEST 4: CHECK FCM CONFIGURATION
# =============================================================================
def check_fcm_configuration():
    print_header("TEST 4: CHECKING FCM CONFIGURATION")
    
    print_info("Checking if FCM (Firebase Cloud Messaging) is configured...")
    print_info("Note: This requires checking Expo dashboard or app.json")
    
    # Check app.json if it exists
    try:
        if os.path.exists('app.json'):
            with open('app.json', 'r') as f:
                app_config = json.load(f)
            
            android_config = app_config.get('expo', {}).get('android', {})
            print_info(f"Android config in app.json: {json.dumps(android_config, indent=2)}")
            
            if 'package' in android_config:
                print_success(f"Android package name configured: {android_config['package']}")
            else:
                print_warning("Android package name not found in app.json")
        else:
            print_warning("app.json not found")
    except Exception as e:
        print_warning(f"Could not check app.json: {e}")
    
    print_info("\nTo verify FCM configuration:")
    print_info("1. Go to https://expo.dev")
    print_info("2. Navigate to your project")
    print_info("3. Check 'Credentials' section")
    print_info("4. Look for Android → Push Notifications")
    print_info("5. Should see FCM Server Key configured")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    print_header("ANDROID PUSH NOTIFICATION TESTING")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Find Android users
    android_users, ios_users, unknown_users = find_android_users()
    
    if not android_users:
        print_warning("\n⚠️  NO ANDROID USERS FOUND!")
        print_warning("Cannot test Android push notifications without Android users")
        print_info("\nPossible reasons:")
        print_info("1. All users are on iOS")
        print_info("2. Android users haven't logged in yet")
        print_info("3. Android users haven't granted notification permissions")
        print_info("4. Platform field not set correctly in database")
        
        if unknown_users:
            print_info(f"\nFound {len(unknown_users)} users with tokens but unknown platform:")
            for user in unknown_users:
                print_info(f"  - {user['id']}: {user['token'][:40]}...")
            print_info("These might be Android users - platform field not set")
        
        check_fcm_configuration()
        return
    
    # Find Android user with token
    android_user_with_token = None
    for user in android_users:
        if user['has_token']:
            android_user_with_token = user
            break
    
    if not android_user_with_token:
        print_warning("\n⚠️  NO ANDROID USERS WITH PUSH TOKENS!")
        print_warning("Android users exist but none have registered push tokens")
        print_info("Users need to:")
        print_info("1. Log into the mobile app on Android device")
        print_info("2. Grant notification permissions")
        print_info("3. Token will be automatically registered")
        
        check_fcm_configuration()
        return
    
    print_success(f"\nFound Android user with token: {android_user_with_token['id']}")
    token = android_user_with_token['token']
    
    time.sleep(2)
    
    # Test 2: Test Expo with Android token
    print_info(f"\nTesting with Android token...")
    expo_works = test_android_expo_push(token)
    
    time.sleep(2)
    
    # Test 3: Test backend message to Android user
    if android_user_with_token['id']:
        test_backend_message_to_android(android_user_with_token['id'])
    
    time.sleep(2)
    
    # Test 4: Check FCM configuration
    check_fcm_configuration()
    
    # Summary
    print_header("TEST SUMMARY")
    
    print_info(f"Android Users Found: {len(android_users)}")
    print_info(f"Android Users With Tokens: {sum(1 for u in android_users if u['has_token'])}")
    print_info(f"iOS Users Found: {len(ios_users)}")
    print_info(f"iOS Users With Tokens: {sum(1 for u in ios_users if u['has_token'])}")
    
    if expo_works:
        print_success("\n✅✅✅ ANDROID PUSH NOTIFICATIONS ARE WORKING!")
        print_success("Android users should be receiving notifications")
    else:
        print_error("\n❌❌❌ ANDROID PUSH NOTIFICATIONS ARE NOT WORKING!")
        print_error("Likely cause: FCM (Firebase Cloud Messaging) credentials not configured")
        print_error("Solution: Configure FCM in Expo dashboard")
    
    print_info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

