#!/usr/bin/env python3
"""
Comprehensive Test Script for Message Notification System
Tests both user->dietician and dietician->user notification flows
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import Firebase initialization
from services.firebase_client import initialize_firebase, db, get_dietician_notification_token

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")

def print_section(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}>>> {text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# Backend URL
BACKEND_URL = "http://localhost:8000"

def check_token_status(user_id, user_type="user"):
    """Check if a user has a valid push notification token"""
    print_section(f"Checking token status for {user_type}: {user_id}")
    
    try:
        if user_id == "dietician":
            # Special case for dietician
            token = get_dietician_notification_token()
            if token:
                print_success(f"Dietician token found: {token[:30]}...")
                return token
            else:
                print_error("No dietician token found")
                return None
        else:
            # Regular user
            doc = db.collection("user_profiles").document(user_id).get()
            if not doc.exists:
                print_error(f"User document not found for {user_id}")
                return None
            
            data = doc.to_dict()
            token = data.get("expoPushToken") or data.get("notificationToken")
            
            if token:
                print_success(f"User token found: {token[:30]}...")
                print_info(f"Platform: {data.get('platform', 'unknown')}")
                print_info(f"Last token update: {data.get('lastTokenUpdate', 'unknown')}")
                return token
            else:
                print_error(f"No token found for user {user_id}")
                return None
                
    except Exception as e:
        print_error(f"Error checking token: {e}")
        return None

def test_message_notification(recipient_id, sender_name, message, is_dietician, sender_user_id=None):
    """Test sending a message notification"""
    direction = "Dietician -> User" if is_dietician else "User -> Dietician"
    print_section(f"Testing message notification: {direction}")
    
    payload = {
        "recipientId": recipient_id,
        "type": "message",
        "message": message,
        "senderName": sender_name,
        "isDietician": is_dietician
    }
    
    if sender_user_id:
        payload["senderUserId"] = sender_user_id
    
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/notifications/send",
            json=payload,
            timeout=10
        )
        
        print_info(f"Response status: {response.status_code}")
        print_info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print_success("Notification sent successfully!")
                return True
            else:
                print_error(f"Notification failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print_error(f"HTTP error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Request timeout")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Request error: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def verify_notification_data(notification_data, expected_from_dietician=None, expected_from_user=None):
    """Verify notification data has correct flags"""
    print_section("Verifying notification data structure")
    
    print_info(f"Notification type: {notification_data.get('type')}")
    print_info(f"Sender name: {notification_data.get('senderName')}")
    print_info(f"Message: {notification_data.get('message')}")
    
    if expected_from_dietician is not None:
        has_flag = notification_data.get('fromDietician', False)
        if has_flag == expected_from_dietician:
            print_success(f"fromDietician flag is correct: {has_flag}")
        else:
            print_error(f"fromDietician flag is incorrect: expected {expected_from_dietician}, got {has_flag}")
            return False
    
    if expected_from_user is not None:
        has_flag = notification_data.get('fromUser')
        if (has_flag is not None) == expected_from_user:
            print_success(f"fromUser flag is present: {has_flag}")
        else:
            print_error(f"fromUser flag is missing or incorrect")
            return False
    
    return True

def get_test_user_id():
    """Get a test user ID from Firestore"""
    print_section("Finding test user")
    
    try:
        # Get any non-dietician user
        users_ref = db.collection("user_profiles")
        users = users_ref.where("isDietician", "==", False).limit(1).stream()
        
        for user in users:
            user_id = user.id
            data = user.to_dict()
            print_success(f"Found test user: {user_id}")
            print_info(f"Name: {data.get('firstName', '')} {data.get('lastName', '')}")
            print_info(f"Email: {data.get('email', 'unknown')}")
            return user_id
        
        # If no non-dietician user found, get any user
        all_users = db.collection("user_profiles").limit(1).stream()
        for user in all_users:
            user_id = user.id
            print_warning(f"Using user (may be dietician): {user_id}")
            return user_id
        
        print_error("No users found in database")
        return None
        
    except Exception as e:
        print_error(f"Error finding test user: {e}")
        return None

def check_dietician_exists():
    """Check if dietician account exists and has isDietician flag"""
    print_section("Checking dietician account")
    
    try:
        # Check by email
        users_ref = db.collection("user_profiles")
        dietician_query = users_ref.where("email", "==", "nutricious4u@gmail.com").limit(1).stream()
        
        for user in dietician_query:
            data = user.to_dict()
            is_dietician = data.get("isDietician", False)
            
            print_success(f"Found dietician account: {user.id}")
            print_info(f"Email: {data.get('email')}")
            print_info(f"isDietician flag: {is_dietician}")
            
            if not is_dietician:
                print_warning("Dietician account does not have isDietician=True flag!")
                print_info("This may cause issues with token lookup")
            
            return user.id, is_dietician
        
        print_error("Dietician account not found with email nutricious4u@gmail.com")
        
        # Try finding by isDietician flag
        dietician_query = users_ref.where("isDietician", "==", True).limit(1).stream()
        for user in dietician_query:
            data = user.to_dict()
            print_warning(f"Found account with isDietician flag: {user.id}")
            print_info(f"Email: {data.get('email')}")
            return user.id, True
        
        return None, False
        
    except Exception as e:
        print_error(f"Error checking dietician account: {e}")
        return None, False

def main():
    """Main test function"""
    print_header("MESSAGE NOTIFICATION SYSTEM - COMPREHENSIVE TEST")
    
    # Initialize Firebase
    print_section("Initializing Firebase")
    try:
        initialize_firebase()
        print_success("Firebase initialized successfully")
    except Exception as e:
        print_error(f"Failed to initialize Firebase: {e}")
        return
    
    # Check dietician account
    dietician_id, has_dietician_flag = check_dietician_exists()
    if not dietician_id:
        print_error("Cannot proceed without dietician account")
        return
    
    # Get test user
    test_user_id = get_test_user_id()
    if not test_user_id:
        print_error("Cannot proceed without test user")
        return
    
    # Check tokens
    print_header("TOKEN STATUS CHECK")
    
    dietician_token = check_token_status("dietician", "dietician")
    user_token = check_token_status(test_user_id, "user")
    
    if not dietician_token:
        print_warning("Dietician does not have a push token registered!")
        print_info("The dietician needs to log into the mobile app to register for notifications")
    
    if not user_token:
        print_warning(f"User {test_user_id} does not have a push token registered!")
        print_info("The user needs to log into the mobile app to register for notifications")
    
    # Test notifications
    print_header("NOTIFICATION SENDING TESTS")
    
    test_results = {
        "user_to_dietician": False,
        "dietician_to_user": False
    }
    
    # Test 1: User -> Dietician
    print_section("TEST 1: User sends message to Dietician")
    test_results["user_to_dietician"] = test_message_notification(
        recipient_id="dietician",
        sender_name="Test User",
        message="Hello Dietician! This is a test message from user.",
        is_dietician=False,
        sender_user_id=test_user_id
    )
    
    # Test 2: Dietician -> User
    print_section("TEST 2: Dietician sends message to User")
    test_results["dietician_to_user"] = test_message_notification(
        recipient_id=test_user_id,
        sender_name="Dietician",
        message="Hello User! This is a test message from dietician.",
        is_dietician=True,
        sender_user_id=dietician_id
    )
    
    # Summary
    print_header("TEST SUMMARY")
    
    print_section("Results")
    if test_results["user_to_dietician"]:
        print_success("User -> Dietician: PASSED")
    else:
        print_error("User -> Dietician: FAILED")
    
    if test_results["dietician_to_user"]:
        print_success("Dietician -> User: PASSED")
    else:
        print_error("Dietician -> User: FAILED")
    
    print_section("Next Steps")
    if not dietician_token:
        print_warning("1. Dietician needs to log in to mobile app to register push token")
    if not user_token:
        print_warning("2. Test user needs to log in to mobile app to register push token")
    if not has_dietician_flag:
        print_warning("3. Dietician account needs isDietician=True flag set in Firestore")
    
    print_section("Verification")
    print_info("To verify notifications are working:")
    print_info("1. Log in as dietician on mobile device")
    print_info("2. Log in as user on another mobile device")
    print_info("3. Send messages in both directions")
    print_info("4. Check that notifications appear on the recipient's device")
    print_info("5. Check backend logs for detailed notification flow")
    
    print_header("TEST COMPLETE")
    
    # Return exit code based on test results
    all_passed = all(test_results.values())
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

