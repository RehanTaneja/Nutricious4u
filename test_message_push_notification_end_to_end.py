#!/usr/bin/env python3
"""
COMPREHENSIVE MESSAGE PUSH NOTIFICATION END-TO-END TEST
This script simulates the EXACT flow of a user sending a message to dietician
and traces every single step to find where it's failing.
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

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

def print_step(step_num, text):
    print(f"{Colors.OKBLUE}{Colors.BOLD}[STEP {step_num}] {text}{Colors.ENDC}")

# Initialize Firebase
print_header("INITIALIZING FIREBASE")
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    # Try to get existing app
    try:
        db = firestore.client()
        print_success("Firebase already initialized")
    except:
        # Try multiple paths
        possible_paths = [
            'backend/services/firebase_service_account.json',
            'services/firebase_service_account.json',
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
            print_success(f"Firebase initialized from {cred_path}")
        else:
            print_error("Firebase service account file not found")
            sys.exit(1)
            
except Exception as e:
    print_error(f"Failed to initialize Firebase: {e}")
    sys.exit(1)

# Backend URL
BACKEND_URL = "https://nutricious4u-production.up.railway.app/api"

# Test results
results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "issues": [],
    "recommendations": []
}

def add_issue(issue, details):
    results["issues"].append({"issue": issue, "details": details})

def add_recommendation(rec, details):
    results["recommendations"].append({"recommendation": rec, "details": details})

# =============================================================================
# SIMULATE EXACT MESSAGE FLOW
# =============================================================================

print_header("SIMULATING EXACT MESSAGE SENDING FLOW")

print_info("This test simulates what happens when a user sends a message to the dietician")
print_info("We'll trace through every single step from frontend to backend to Expo\n")

# Step 1: Find a real user and dietician
print_step(1, "Finding real user and dietician in database")

user_id = None
user_name = None
user_token = None
dietician_id = None
dietician_token = None
dietician_email = None

try:
    profiles = db.collection('user_profiles').stream()
    
    for profile in profiles:
        data = profile.to_dict()
        
        # Check if this is the dietician
        if data.get('isDietician'):
            dietician_id = profile.id
            dietician_email = data.get('email', 'Unknown')
            dietician_token = data.get('expoPushToken') or data.get('notificationToken')
            print_success(f"Found dietician: {dietician_id}")
            print_info(f"  Email: {dietician_email}")
            if dietician_token:
                print_success(f"  Token: {dietician_token[:30]}...")
            else:
                print_error(f"  Token: MISSING")
                add_issue(
                    "Dietician Missing Push Token",
                    f"Dietician ({dietician_id}) has NO push token. This is why ALL message notifications fail."
                )
        
        # Find a regular user
        elif not user_id and not data.get('isDietician'):
            user_id = profile.id
            first_name = data.get('firstName', 'User')
            last_name = data.get('lastName', '')
            user_name = f"{first_name} {last_name}".strip()
            user_token = data.get('expoPushToken') or data.get('notificationToken')
            
            # Only use this user if they have a name
            if first_name != 'User' and first_name != 'Test':
                print_success(f"Found user: {user_id}")
                print_info(f"  Name: {user_name}")
                if user_token:
                    print_success(f"  Token: {user_token[:30]}...")
                else:
                    print_warning(f"  Token: MISSING (user can't receive notifications from dietician)")
    
    if not dietician_id:
        print_error("No dietician found in database!")
        add_issue("No Dietician", "Cannot find dietician account in user_profiles collection")
        sys.exit(1)
    
    if not user_id:
        print_error("No suitable user found in database!")
        add_issue("No User", "Cannot find a real user account for testing")
        sys.exit(1)
        
except Exception as e:
    print_error(f"Error finding users: {e}")
    sys.exit(1)

print()

# Step 2: Simulate message being saved to Firestore (what frontend does)
print_step(2, "Simulating message save to Firestore (what frontend does)")

message_text = "Test message from diagnostic script - " + datetime.now().strftime("%H:%M:%S")

try:
    print_info(f"Saving message to: chats/{user_id}/messages")
    print_info(f"Message content: {message_text}")
    
    message_data = {
        'text': message_text,
        'sender': 'user',
        'timestamp': firestore.SERVER_TIMESTAMP,
    }
    
    # Save message
    message_ref = db.collection('chats').document(user_id).collection('messages').add(message_data)
    print_success(f"Message saved with ID: {message_ref[1].id}")
    
    # Update chat summary
    db.collection('chats').document(user_id).set({
        'userId': user_id,
        'lastMessage': message_text,
        'lastMessageTimestamp': firestore.SERVER_TIMESTAMP,
    }, merge=True)
    print_success("Chat summary updated")
    
except Exception as e:
    print_error(f"Failed to save message: {e}")
    add_issue("Message Save Failed", f"Could not save message to Firestore: {str(e)}")
    sys.exit(1)

print()

# Step 3: Check what notification payload frontend would send
print_step(3, "Checking push notification payload (what frontend sends)")

notification_payload = {
    "type": "message",
    "recipientId": "dietician",  # Frontend sends "dietician" not the actual ID
    "senderName": user_name,
    "message": message_text,
    "isFromDietician": False
}

print_info("Frontend notification payload:")
print_info(json.dumps(notification_payload, indent=2))

print()

# Step 4: Call backend push notification endpoint
print_step(4, "Calling backend push notification endpoint")

try:
    print_info(f"Calling: {BACKEND_URL}/push-notifications/send")
    print_info("Request payload:")
    print_info(json.dumps(notification_payload, indent=2))
    
    response = requests.post(
        f"{BACKEND_URL}/push-notifications/send",
        json=notification_payload,
        headers={'Content-Type': 'application/json'},
        timeout=15
    )
    
    print_info(f"\nBackend response:")
    print_info(f"  Status Code: {response.status_code}")
    print_info(f"  Response Body: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('success'):
            print_success("Backend returned success=true")
            print_success("This means the notification was sent to Expo successfully!")
        else:
            print_error("Backend returned success=false")
            print_error("This means the notification was NOT sent")
            
            if not dietician_token:
                print_error("ROOT CAUSE: Dietician has no push token in database")
                print_error("Backend looked for dietician token but found NONE")
                add_issue(
                    "CRITICAL: Push Notification Failed",
                    "Backend returned success=false because dietician has no expoPushToken in user_profiles"
                )
                add_recommendation(
                    "IMMEDIATE FIX REQUIRED",
                    "Dietician must log into mobile app and grant notification permissions. This is the ONLY way to fix message notifications."
                )
            else:
                print_error("Unexpected failure - dietician HAS a token but notification still failed")
                add_issue(
                    "Unexpected Failure",
                    "Dietician has token but backend still returned failure. Check backend logs."
                )
    else:
        print_error(f"Backend returned error status: {response.status_code}")
        add_issue("Backend Error", f"Backend returned status {response.status_code}: {response.text}")
        
except Exception as e:
    print_error(f"Failed to call backend: {e}")
    add_issue("Backend Unreachable", f"Could not reach backend endpoint: {str(e)}")

print()

# Step 5: Check backend logs (simulation)
print_step(5, "What should happen in backend logs")

print_info("When backend receives the request, it should:")
print_info("  1. Receive POST /push-notifications/send")
print_info("  2. Parse type='message'")
print_info("  3. Look up recipientId='dietician'")
print_info("  4. Call get_dietician_notification_token()")
print_info("  5. Query Firestore: user_profiles WHERE isDietician = true")

if dietician_token:
    print_success("  6. Find token: " + dietician_token[:30] + "...")
    print_success("  7. Call Expo Push Service with token")
    print_success("  8. Expo returns success")
    print_success("  9. Backend returns {success: true}")
else:
    print_error("  6. NO TOKEN FOUND")
    print_error("  7. Cannot send to Expo without token")
    print_error("  8. Backend returns {success: false}")

print()

# Step 6: Test Expo directly if token exists
if dietician_token:
    print_step(6, "Testing Expo Push Service directly")
    
    try:
        expo_payload = {
            "to": dietician_token,
            "sound": "default",
            "title": "Test Message from Diagnostic",
            "body": f"{user_name}: {message_text}",
            "data": {
                "type": "message_notification",
                "senderName": user_name,
                "message": message_text,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        print_info("Sending direct test to Expo Push Service...")
        print_info("Payload:")
        print_info(json.dumps(expo_payload, indent=2))
        
        expo_response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            headers={
                "Accept": "application/json",
                "Accept-encoding": "gzip, deflate",
                "Content-Type": "application/json",
            },
            json=expo_payload,
            timeout=10
        )
        
        print_info(f"\nExpo response:")
        print_info(f"  Status: {expo_response.status_code}")
        print_info(f"  Body: {expo_response.text}")
        
        if expo_response.status_code == 200:
            expo_result = expo_response.json()
            
            if 'data' in expo_result:
                data = expo_result['data']
                if isinstance(data, dict):
                    if data.get('status') == 'ok':
                        print_success("✅✅✅ EXPO ACCEPTED THE NOTIFICATION!")
                        print_success("Notification should arrive on dietician's device")
                        print_info(f"Notification ID: {data.get('id', 'Unknown')}")
                    elif data.get('status') == 'error':
                        print_error(f"Expo returned error: {data.get('message', 'Unknown')}")
                        
                        error_message = data.get('message', '')
                        if 'DeviceNotRegistered' in error_message:
                            add_issue(
                                "Token Expired/Invalid",
                                "Expo says 'DeviceNotRegistered' - the token is old/expired. Dietician needs to re-login to get new token."
                            )
                        elif 'InvalidCredentials' in error_message:
                            add_issue(
                                "Invalid Token",
                                "Token format is invalid. Dietician needs to re-login to get valid token."
                            )
        else:
            print_error(f"Expo returned error status: {expo_response.status_code}")
            add_issue("Expo Service Error", f"Expo service returned {expo_response.status_code}")
            
    except Exception as e:
        print_error(f"Failed to test Expo directly: {e}")
        add_issue("Expo Unreachable", f"Could not reach Expo push service: {str(e)}")
else:
    print_step(6, "Skipping Expo test (no dietician token)")
    print_error("Cannot test Expo because dietician has no token")

print()

# Step 7: Check what user should see
print_step(7, "Expected behavior on devices")

print_info("On USER's device (sender):")
print_info("  - Message appears in chat immediately ✅")
print_info("  - No notification expected (they sent it)")
print()

print_info("On DIETICIAN's device (recipient):")
if dietician_token:
    print_success("  - Should receive push notification ✅")
    print_success("  - Notification banner shows: 'New message from {user_name}'")
    print_success("  - Notification body shows message text")
    print_success("  - Sound/vibration plays")
    print_success("  - Badge number increases")
    print_success("  - Tapping notification opens app to chat")
else:
    print_error("  - Will NOT receive any notification ❌")
    print_error("  - No banner, no sound, no badge")
    print_error("  - User must manually open app to see message")
    print_error("  - This is the current problem!")

print()

# Final Summary
print_header("TEST SUMMARY & FINDINGS")

print_info(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if results["issues"]:
    print_error(f"ISSUES FOUND: {len(results['issues'])}")
    for i, issue in enumerate(results["issues"], 1):
        print_error(f"\n{i}. {issue['issue']}")
        print_error(f"   Details: {issue['details']}")
else:
    print_success("No issues found!")

print()

if results["recommendations"]:
    print_warning(f"RECOMMENDATIONS: {len(results['recommendations'])}")
    for i, rec in enumerate(results["recommendations"], 1):
        print_warning(f"\n{i}. {rec['recommendation']}")
        print_warning(f"   Details: {rec['details']}")

print()

# Save results
output_file = f"message_push_notification_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
results["dietician_info"] = {
    "id": dietician_id,
    "email": dietician_email,
    "has_token": dietician_token is not None,
    "token_preview": dietician_token[:30] + "..." if dietician_token else None
}
results["user_info"] = {
    "id": user_id,
    "name": user_name,
    "has_token": user_token is not None,
    "token_preview": user_token[:30] + "..." if user_token else None
}

with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print_success(f"Results saved to: {output_file}")

print()
print_header("WHAT TO DO NEXT")

if not dietician_token:
    print_error("CRITICAL ISSUE: Dietician has no push token")
    print()
    print_info("IMMEDIATE FIX (2-3 minutes):")
    print_info("  1. Dietician logs into mobile app")
    print_info("  2. Grant notification permissions when prompted")
    print_info("  3. Token automatically registers")
    print_info("  4. Run this test again")
    print_info("  5. All notifications will work!")
    print()
    print_info("VERIFICATION:")
    print_info("  - Check Firebase Console")
    print_info(f"  - Go to user_profiles/{dietician_id}")
    print_info("  - Confirm expoPushToken field exists")
    print_info("  - Token should start with 'ExponentPushToken'")
else:
    print_success("Dietician has token - system should be working!")
    print_info("If notifications still not arriving:")
    print_info("  1. Check device notification settings")
    print_info("  2. Check Do Not Disturb is off")
    print_info("  3. Try re-logging into mobile app")
    print_info("  4. Check backend logs for errors")

