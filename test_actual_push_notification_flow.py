#!/usr/bin/env python3
"""
ACTUAL PUSH NOTIFICATION FLOW TESTING
Tests the real push notification flow with actual data from the database
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
            print_info(f"Found Firebase service account at: {cred_path}")
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
# TEST 1: VERIFY DIETICIAN TOKEN
# =============================================================================
def test_dietician_token():
    print_header("TEST 1: VERIFY DIETICIAN TOKEN")
    
    try:
        # Find dietician account
        print_info("Looking for dietician account...")
        profiles = db.collection('user_profiles').where('isDietician', '==', True).limit(1).stream()
        
        dietician_data = None
        dietician_id = None
        
        for profile in profiles:
            dietician_id = profile.id
            dietician_data = profile.to_dict()
            break
        
        if not dietician_data:
            print_error("Dietician account not found!")
            return None, None
        
        print_success(f"Found dietician account: {dietician_id}")
        
        # Check token
        token = dietician_data.get('expoPushToken')
        platform = dietician_data.get('platform')
        last_update = dietician_data.get('lastTokenUpdate')
        email = dietician_data.get('email')
        
        print_info(f"Dietician details:")
        print_info(f"  User ID: {dietician_id}")
        print_info(f"  Email: {email}")
        print_info(f"  Platform: {platform}")
        print_info(f"  Last Token Update: {last_update}")
        print_info(f"  Token: {token}")
        
        if not token:
            print_error("Dietician has NO push token!")
            return None, dietician_id
        
        if not token.startswith("ExponentPushToken"):
            print_error(f"Invalid token format: {token}")
            return None, dietician_id
        
        # Check if token looks complete
        if len(token) < 50:
            print_warning(f"Token looks suspiciously short: {len(token)} characters")
            print_warning("Full token: " + token)
        else:
            print_success(f"Token format looks valid (length: {len(token)})")
        
        return token, dietician_id
        
    except Exception as e:
        print_error(f"Error checking dietician token: {e}")
        return None, None

# =============================================================================
# TEST 2: TEST EXPO PUSH SERVICE WITH ACTUAL TOKEN
# =============================================================================
def test_expo_with_real_token(token):
    print_header("TEST 2: SEND TEST NOTIFICATION VIA EXPO")
    
    if not token:
        print_error("No token provided, skipping test")
        return False
    
    try:
        notification = {
            "to": token,
            "sound": "default",
            "title": "🔔 Test Notification",
            "body": "This is a test from the diagnostic script. If you see this, push notifications are working!",
            "data": {
                "type": "test",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        print_info("Sending test notification to Expo...")
        print_info(f"  Token: {token[:30]}...")
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
                        
                        if 'DeviceNotRegistered' in error_msg:
                            print_error("TOKEN IS INVALID OR EXPIRED!")
                            print_error("User needs to log out and log back in to refresh token")
                        
                        return False
                    elif status == 'ok':
                        print_success("✅✅✅ NOTIFICATION SENT SUCCESSFULLY!")
                        print_success("Check the dietician's device for the notification")
                        return True
                elif isinstance(result['data'], list) and len(result['data']) > 0:
                    status = result['data'][0].get('status')
                    if status == 'error':
                        error_msg = result['data'][0].get('message', 'Unknown error')
                        print_error(f"Expo returned error: {error_msg}")
                        return False
                    elif status == 'ok':
                        print_success("✅✅✅ NOTIFICATION SENT SUCCESSFULLY!")
                        return True
        else:
            print_error(f"Expo returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error sending to Expo: {e}")
        return False
    
    return False

# =============================================================================
# TEST 3: TEST BACKEND MESSAGE NOTIFICATION
# =============================================================================
def test_backend_message_notification(dietician_id):
    print_header("TEST 3: BACKEND MESSAGE NOTIFICATION")
    
    try:
        # Get a real user
        print_info("Finding a real user...")
        users = db.collection('user_profiles').where('isDietician', '!=', True).limit(1).stream()
        
        user_id = None
        user_name = "Test User"
        
        for user in users:
            user_data = user.to_dict()
            user_id = user.id
            first_name = user_data.get('firstName', 'Test')
            last_name = user_data.get('lastName', 'User')
            user_name = f"{first_name} {last_name}".strip()
            break
        
        if not user_id:
            print_warning("No real user found, using test data")
            user_id = "test_user_123"
        
        print_success(f"Using user: {user_name} ({user_id})")
        
        # Test 1: User -> Dietician message
        print_info("\nTest 3.1: User -> Dietician Message Notification")
        payload = {
            "type": "message",
            "recipientId": "dietician",
            "senderName": user_name,
            "message": "Test message from diagnostic script",
            "isFromDietician": False
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
                print_success("Message notification should have been sent to dietician!")
            else:
                print_error("❌ Backend returned success=false")
                print_error("This means the backend couldn't send the notification")
                print_warning("Check backend logs for details")
        else:
            print_error(f"Backend returned error status: {response.status_code}")
        
        time.sleep(2)
        
        # Test 2: Dietician -> User message
        print_info("\nTest 3.2: Dietician -> User Message Notification")
        payload = {
            "type": "message",
            "recipientId": user_id,
            "senderName": "Dietician",
            "message": "Test response from dietician",
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
                print_success(f"Message notification should have been sent to {user_name}!")
            else:
                print_error("❌ Backend returned success=false")
                print_error(f"User {user_id} likely has no push token")
        
    except Exception as e:
        print_error(f"Error testing backend: {e}")

# =============================================================================
# TEST 4: TEST BACKEND APPOINTMENT NOTIFICATION
# =============================================================================
def test_backend_appointment_notification():
    print_header("TEST 4: BACKEND APPOINTMENT NOTIFICATION")
    
    try:
        # Test appointment scheduled
        print_info("Test 4.1: Appointment Scheduled Notification")
        payload = {
            "type": "appointment_scheduled",
            "userName": "Test User",
            "date": "11/10/2025",
            "timeSlot": "10:00"
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
                print_success("Appointment notification should have been sent to dietician!")
            else:
                print_error("❌ Backend returned success=false")
        
        time.sleep(2)
        
        # Test appointment cancelled
        print_info("\nTest 4.2: Appointment Cancelled Notification")
        payload = {
            "type": "appointment_cancelled",
            "userName": "Test User",
            "date": "11/10/2025",
            "timeSlot": "10:00"
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
                print_success("Cancellation notification should have been sent to dietician!")
            else:
                print_error("❌ Backend returned success=false")
        
    except Exception as e:
        print_error(f"Error testing appointments: {e}")

# =============================================================================
# TEST 5: CHECK BACKEND LOGS AND TOKEN LOOKUP
# =============================================================================
def test_backend_token_lookup(dietician_id):
    print_header("TEST 5: BACKEND TOKEN LOOKUP DEBUG")
    
    try:
        print_info("Testing backend's ability to find dietician token...")
        print_info(f"Using debug endpoint: /notifications/debug/token/dietician")
        
        response = requests.get(
            f"{BACKEND_URL}/notifications/debug/token/dietician",
            timeout=15
        )
        
        print_info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_info("Backend token lookup result:")
            print_info(json.dumps(result, indent=2))
            
            if result.get('tokenFound'):
                print_success("✅ Backend CAN find dietician token")
                print_info(f"Token preview: {result.get('tokenPreview')}")
            else:
                print_error("❌ Backend CANNOT find dietician token")
                print_error("This is the root cause!")
                
                errors = result.get('errors', [])
                if errors:
                    print_error("Errors from backend:")
                    for error in errors:
                        print_error(f"  - {error}")
        else:
            print_warning(f"Debug endpoint returned {response.status_code}")
            print_info(f"Response: {response.text}")
            
    except Exception as e:
        print_error(f"Error testing backend token lookup: {e}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    print_header("ACTUAL PUSH NOTIFICATION FLOW TESTING")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Verify dietician token
    token, dietician_id = test_dietician_token()
    
    if not token:
        print_error("\n❌ CRITICAL: Dietician has no valid token!")
        print_error("Cannot proceed with further tests")
        return
    
    time.sleep(2)
    
    # Test 2: Test Expo with real token
    expo_works = test_expo_with_real_token(token)
    
    time.sleep(2)
    
    # Test 3: Test backend message notifications
    test_backend_message_notification(dietician_id)
    
    time.sleep(2)
    
    # Test 4: Test backend appointment notifications
    test_backend_appointment_notification()
    
    time.sleep(2)
    
    # Test 5: Test backend token lookup
    test_backend_token_lookup(dietician_id)
    
    # Summary
    print_header("TEST SUMMARY")
    
    if expo_works:
        print_success("✅ Expo Push Service: WORKING")
        print_success("   The token is valid and Expo can deliver notifications")
    else:
        print_error("❌ Expo Push Service: FAILING")
        print_error("   Token may be invalid or expired")
    
    print_info("\nNext steps:")
    print_info("1. Check backend logs for any errors")
    print_info("2. Verify notifications were received on device")
    print_info("3. If Expo test succeeded but backend fails, issue is in backend code")
    print_info("4. If Expo test failed, token needs to be refreshed")
    
    print_info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

