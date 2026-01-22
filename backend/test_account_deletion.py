#!/usr/bin/env python3
"""
Comprehensive test script for account deletion functionality.
Tests the entire flow: create user -> add data -> delete account -> verify deletion
"""
import os
import sys
import asyncio
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api"

def print_step(step_num, message):
    """Print formatted test step"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {message}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def test_create_user():
    """Create a test user via Firebase Auth (simulated)"""
    print_step(1, "Creating Test User")
    
    # For testing, we'll use an existing test user or create one via your auth system
    # This is a placeholder - adjust based on your auth setup
    test_user_id = f"test_delete_{int(datetime.now().timestamp())}"
    test_email = f"test_delete_{int(datetime.now().timestamp())}@test.com"
    
    print_info(f"Test User ID: {test_user_id}")
    print_info(f"Test Email: {test_email}")
    
    # Note: In real testing, you'd create the user via Firebase Auth first
    # For now, we'll assume the user exists or create via your API
    
    return test_user_id, test_email

def test_add_user_data(user_id):
    """Add various data for the test user"""
    print_step(2, "Adding Test Data")
    
    added_data = {
        "food_logs": 0,
        "routines": 0,
        "workout_logs": 0,
        "notifications": 0,
        "appointments": 0,
        "chat_messages": 0
    }
    
    try:
        # Add food log
        food_log_data = {
            "userId": user_id,
            "foodName": "Test Food",
            "servingSize": "100",
            "calories": 250.0,
            "protein": 10.0,
            "fat": 5.0,
            "timestamp": datetime.now().isoformat()
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/food/log",
            json=food_log_data,
            timeout=30
        )
        if response.status_code == 200:
            added_data["food_logs"] = 1
            print_success(f"Added 1 food log")
        else:
            print_error(f"Failed to add food log: {response.status_code}")
    except Exception as e:
        print_error(f"Error adding food log: {e}")
    
    try:
        # Add workout log
        workout_data = {
            "userId": user_id,
            "exerciseName": "Test Exercise",
            "duration": 30,
            "calories": 150.0
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/workout/log",
            json=workout_data,
            timeout=30
        )
        if response.status_code == 200:
            added_data["workout_logs"] = 1
            print_success(f"Added 1 workout log")
        else:
            print_error(f"Failed to add workout log: {response.status_code}")
    except Exception as e:
        print_error(f"Error adding workout log: {e}")
    
    # Add notification (simulated - would normally come from system)
    # We'll skip this as it requires backend setup
    
    print_info(f"Added data summary: {added_data}")
    return added_data

def test_verify_user_exists(user_id):
    """Verify user exists before deletion"""
    print_step(3, "Verifying User Exists")
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/{user_id}/profile",
            timeout=10
        )
        if response.status_code == 200:
            user_data = response.json()
            print_success(f"User exists: {user_data.get('firstName', 'N/A')}")
            return True
        elif response.status_code == 404:
            print_error("User not found (404)")
            return False
        else:
            print_error(f"Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error verifying user: {e}")
        return False

def test_delete_account(user_id):
    """Test account deletion"""
    print_step(4, "Deleting Account")
    
    try:
        start_time = datetime.now()
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/users/{user_id}/account",
            timeout=100  # 100 seconds timeout for deletion
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_info(f"Deletion took {duration:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Account deletion successful")
            print_info(f"Deleted items: {json.dumps(result.get('deleted_items', {}), indent=2)}")
            return True, result.get('deleted_items', {})
        elif response.status_code == 404:
            print_error("User not found (404) - may have been deleted already")
            return False, {}
        elif response.status_code == 408:
            print_error("Request timed out (408)")
            return False, {}
        else:
            print_error(f"Deletion failed: {response.status_code} - {response.text}")
            return False, {}
    except requests.exceptions.Timeout:
        print_error("Request timed out (>100 seconds)")
        return False, {}
    except Exception as e:
        print_error(f"Error deleting account: {e}")
        return False, {}

def test_verify_user_deleted(user_id):
    """Verify user is completely deleted"""
    print_step(5, "Verifying User is Deleted")
    
    checks = {
        "user_profile": False,
        "lock_status": False,
        "profile_endpoint": False
    }
    
    # Check 1: User profile should not exist
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/{user_id}/profile",
            timeout=10
        )
        if response.status_code == 404:
            checks["user_profile"] = True
            print_success("User profile deleted (404)")
        else:
            print_error(f"User profile still exists: {response.status_code}")
    except Exception as e:
        print_error(f"Error checking user profile: {e}")
    
    # Check 2: Lock status should return 404
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/{user_id}/lock-status",
            timeout=10
        )
        if response.status_code == 404:
            checks["lock_status"] = True
            print_success("Lock status returns 404 (correct)")
        elif response.status_code == 500:
            print_error("Lock status returns 500 (should be 404)")
        else:
            print_error(f"Lock status unexpected: {response.status_code}")
    except Exception as e:
        print_error(f"Error checking lock status: {e}")
    
    # Check 3: Subscription status should return 404
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/subscription/status/{user_id}",
            timeout=10
        )
        if response.status_code == 404:
            checks["profile_endpoint"] = True
            print_success("Subscription status returns 404 (correct)")
        else:
            print_error(f"Subscription status unexpected: {response.status_code}")
    except Exception as e:
        print_error(f"Error checking subscription status: {e}")
    
    return checks

def main():
    """Run comprehensive account deletion test"""
    print("\n" + "="*60)
    print("ACCOUNT DELETION COMPREHENSIVE TEST")
    print("="*60)
    
    # For testing, use an existing test user ID
    # In production, you'd create a user first
    test_user_id = input("\nEnter test user ID to delete (or press Enter to skip): ").strip()
    
    if not test_user_id:
        print_info("Skipping test - no user ID provided")
        print_info("To test: Create a user first, then run this script with the user ID")
        return
    
    # Verify user exists
    if not test_verify_user_exists(test_user_id):
        print_error("User does not exist. Cannot test deletion.")
        return
    
    # Add some test data (optional)
    add_data = input("\nAdd test data before deletion? (y/n): ").strip().lower()
    if add_data == 'y':
        test_add_user_data(test_user_id)
    
    # Confirm deletion
    confirm = input(f"\n⚠️  Are you sure you want to DELETE user {test_user_id}? (yes/no): ").strip().lower()
    if confirm != "yes":
        print_info("Test cancelled")
        return
    
    # Delete account
    success, deleted_items = test_delete_account(test_user_id)
    
    if not success:
        print_error("Account deletion failed or timed out")
        return
    
    # Verify deletion
    checks = test_verify_user_deleted(test_user_id)
    
    # Summary
    print_step(6, "Test Summary")
    print(f"Deletion Success: {'✅ YES' if success else '❌ NO'}")
    print(f"Deleted Items: {json.dumps(deleted_items, indent=2)}")
    print(f"\nVerification Checks:")
    for check_name, check_result in checks.items():
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"  {check_name}: {status}")
    
    all_passed = success and all(checks.values())
    if all_passed:
        print_success("\n🎉 All tests passed! Account deletion is working correctly.")
    else:
        print_error("\n⚠️  Some tests failed. Please review the results above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
