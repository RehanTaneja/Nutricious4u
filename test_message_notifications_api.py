#!/usr/bin/env python3
"""
Simple API-based test for Message Notification System
Tests both user->dietician and dietician->user notification flows using HTTP requests
"""

import json
import requests
import sys
from datetime import datetime

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

def check_backend_health():
    """Check if backend is running"""
    print_section("Checking backend health")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Backend is running")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend - is it running?")
        print_info(f"Expected backend at: {BACKEND_URL}")
        return False
    except Exception as e:
        print_error(f"Error checking backend: {e}")
        return False

def check_token_status(user_id):
    """Check token status for a user"""
    print_section(f"Checking token status for: {user_id}")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/notifications/debug/token/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print_info(f"User ID: {data.get('userId')}")
            print_info(f"Is Dietician: {data.get('isDietician')}")
            print_info(f"Token Found: {data.get('tokenFound')}")
            
            if data.get('tokenFound'):
                print_success(f"Token: {data.get('tokenPreview')}")
                print_info(f"Token Valid: {data.get('tokenValid')}")
                print_info(f"Platform: {data.get('platform', 'N/A')}")
                print_info(f"Last Update: {data.get('lastUpdate', 'N/A')}")
                return True
            else:
                print_error("No token found")
                errors = data.get('errors', [])
                for error in errors:
                    print_warning(error)
                return False
        else:
            print_error(f"HTTP error: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error checking token: {e}")
        return False

def send_message_notification(recipient_id, sender_name, message, is_dietician, sender_user_id=None):
    """Send a message notification"""
    direction = "Dietician -> User" if is_dietician else "User -> Dietician"
    print_section(f"Testing: {direction}")
    
    payload = {
        "recipientId": recipient_id,
        "type": "message",
        "message": message,
        "senderName": sender_name,
        "isDietician": is_dietician
    }
    
    if sender_user_id:
        payload["senderUserId"] = sender_user_id
    
    print_info(f"Sending notification...")
    print_info(f"  Recipient: {recipient_id}")
    print_info(f"  Sender: {sender_name}")
    print_info(f"  Message: {message}")
    print_info(f"  Is Dietician: {is_dietician}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/notifications/send",
            json=payload,
            timeout=10
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_info(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print_success("Notification sent successfully!")
                return True
            else:
                print_error(f"Notification failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print_error(f"HTTP error: {response.status_code}")
            print_info(f"Response: {response.text}")
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

def main():
    """Main test function"""
    print_header("MESSAGE NOTIFICATION SYSTEM - API TEST")
    
    # Check backend health
    if not check_backend_health():
        print_error("Backend is not available. Please start the backend server.")
        print_info("Run: cd backend && python server.py")
        sys.exit(1)
    
    # Test user ID - you can change this to test with a specific user
    TEST_USER_ID = "test_user_123"  # Replace with actual user ID from your database
    
    print_header("TOKEN STATUS CHECK")
    
    # Check dietician token
    dietician_has_token = check_token_status("dietician")
    
    # Check user token (using placeholder - replace with actual user ID)
    print_warning(f"Using test user ID: {TEST_USER_ID}")
    print_info("Replace TEST_USER_ID in script with actual user ID from your database")
    user_has_token = check_token_status(TEST_USER_ID)
    
    print_header("NOTIFICATION SENDING TESTS")
    
    test_results = {
        "user_to_dietician": False,
        "dietician_to_user": False
    }
    
    # Test 1: User -> Dietician
    print_section("TEST 1: User sends message to Dietician")
    test_results["user_to_dietician"] = send_message_notification(
        recipient_id="dietician",
        sender_name="Test User",
        message="Hello Dietician! This is a test message from user.",
        is_dietician=False,
        sender_user_id=TEST_USER_ID
    )
    
    # Test 2: Dietician -> User
    print_section("TEST 2: Dietician sends message to User")
    test_results["dietician_to_user"] = send_message_notification(
        recipient_id=TEST_USER_ID,
        sender_name="Dietician",
        message="Hello User! This is a test message from dietician.",
        is_dietician=True,
        sender_user_id="dietician"
    )
    
    # Summary
    print_header("TEST SUMMARY")
    
    print_section("Backend API Tests")
    if test_results["user_to_dietician"]:
        print_success("User -> Dietician: API CALL SUCCESS")
    else:
        print_error("User -> Dietician: API CALL FAILED")
    
    if test_results["dietician_to_user"]:
        print_success("Dietician -> User: API CALL SUCCESS")
    else:
        print_error("Dietician -> User: API CALL FAILED")
    
    print_section("Token Status")
    if dietician_has_token:
        print_success("Dietician has valid push token")
    else:
        print_error("Dietician does NOT have push token")
    
    if user_has_token:
        print_success(f"User {TEST_USER_ID} has valid push token")
    else:
        print_error(f"User {TEST_USER_ID} does NOT have push token")
    
    print_section("Important Notes")
    print_info("1. API calls being successful means the backend is working correctly")
    print_info("2. For actual notifications to appear on devices:")
    print_info("   - Users must have valid push tokens (logged into mobile app)")
    print_info("   - Mobile app must be running or in background")
    print_info("   - Notification handlers must be properly set up in the app")
    
    print_section("Next Steps")
    if not dietician_has_token:
        print_warning("⚠️  Dietician needs to log into mobile app to register push token")
    if not user_has_token:
        print_warning("⚠️  User needs to log into mobile app to register push token")
    
    print_info("\n📱 To verify end-to-end:")
    print_info("1. Log in as dietician on one device")
    print_info("2. Log in as user on another device")
    print_info("3. Send messages between them")
    print_info("4. Verify notifications appear on recipient's device")
    print_info("5. Check backend logs for detailed flow")
    
    print_header("TEST COMPLETE")
    
    # Return exit code based on test results
    api_tests_passed = all(test_results.values())
    sys.exit(0 if api_tests_passed else 1)

if __name__ == "__main__":
    main()

