#!/usr/bin/env python3
"""
Comprehensive account deletion test - creates test user, adds data, then deletes
"""
import requests
import json
import time
import sys
from datetime import datetime, timedelta

BASE_URL = 'https://nutricious4u-production.up.railway.app'
API_PREFIX = '/api'

def print_step(step, message):
    print(f'\n{"="*60}')
    print(f'[STEP {step}] {message}')
    print(f'{"="*60}')

def print_success(message):
    print(f'✅ {message}')

def print_error(message):
    print(f'❌ {message}')

def print_info(message):
    print(f'ℹ️  {message}')

def create_test_user_profile(user_id, email, first_name="Test", last_name="User"):
    """Create a test user profile"""
    print_step(1, f'Creating test user profile: {user_id}')
    
    profile_data = {
        "userId": user_id,
        "firstName": first_name,
        "lastName": last_name,
        "age": 25,
        "gender": "male",
        "email": email,
        "currentWeight": 70.0,
        "goalWeight": 65.0,
        "height": 175.0,
        "dietaryPreference": "vegetarian",
        "favouriteCuisine": "Indian",
        "allergies": "None",
        "medicalConditions": "None",
        "activityLevel": "moderate",
        "targetCalories": 2000.0,
        "targetProtein": 150.0,
        "targetFat": 65.0,
        "stepGoal": 10000,
        "caloriesBurnedGoal": 500,
        "subscriptionPlan": "1month",
        "subscriptionStartDate": datetime.now().isoformat(),
        "subscriptionEndDate": (datetime.now() + timedelta(days=30)).isoformat(),
        "isSubscriptionActive": True,
        "currentSubscriptionAmount": 5000.0,
        "totalAmountPaid": 5000.0
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}{API_PREFIX}/users/profile',
            json=profile_data,
            timeout=30
        )
        if response.status_code in [200, 201]:
            print_success(f'User profile created: {user_id}')
            return True
        else:
            print_error(f'Failed to create profile: {response.status_code}')
            print_error(f'Response: {response.text[:300]}')
            return False
    except Exception as e:
        print_error(f'Error creating profile: {e}')
        return False

def add_test_data(user_id):
    """Add various types of test data"""
    print_step(2, f'Adding test data for user: {user_id}')
    
    added = {
        "food_logs": 0,
        "workout_logs": 0,
        "routines": 0
    }
    
    # Add food logs
    print_info('Adding food logs...')
    for i in range(3):
        food_log = {
            "userId": user_id,
            "foodName": f"Test Food {i+1}",
            "servingSize": "100g",
            "calories": 250.0 + (i * 50),
            "protein": 10.0 + (i * 5),
            "fat": 5.0 + (i * 2),
            "carbs": 30.0 + (i * 10),
            "timestamp": (datetime.now() - timedelta(days=i)).isoformat()
        }
        try:
            response = requests.post(
                f'{BASE_URL}{API_PREFIX}/food/log',
                json=food_log,
                timeout=30
            )
            if response.status_code == 200:
                added["food_logs"] += 1
        except Exception as e:
            print_error(f'Error adding food log {i+1}: {e}')
    
    print_success(f'Added {added["food_logs"]} food logs')
    
    # Add workout logs
    print_info('Adding workout logs...')
    for i in range(2):
        workout_log = {
            "userId": user_id,
            "exerciseName": f"Test Exercise {i+1}",
            "duration": 30 + (i * 15),
            "calories": 150.0 + (i * 50),
            "date": (datetime.now() - timedelta(days=i)).isoformat()
        }
        try:
            response = requests.post(
                f'{BASE_URL}{API_PREFIX}/workout/log',
                json=workout_log,
                timeout=30
            )
            if response.status_code == 200:
                added["workout_logs"] += 1
        except Exception as e:
            print_error(f'Error adding workout log {i+1}: {e}')
    
    print_success(f'Added {added["workout_logs"]} workout logs')
    
    # Add a routine
    print_info('Adding routine...')
    routine = {
        "userId": user_id,
        "name": "Test Routine",
        "exercises": [
            {"name": "Push-ups", "sets": 3, "reps": 10},
            {"name": "Squats", "sets": 3, "reps": 15}
        ],
        "createdAt": datetime.now().isoformat()
    }
    try:
        response = requests.post(
            f'{BASE_URL}{API_PREFIX}/routines',
            json=routine,
            timeout=30
        )
        if response.status_code in [200, 201]:
            added["routines"] += 1
            print_success('Added 1 routine')
    except Exception as e:
        print_error(f'Error adding routine: {e}')
    
    print_info(f'Total data added: {sum(added.values())} items')
    return added

def verify_user_exists(user_id):
    """Verify user exists"""
    try:
        response = requests.get(f'{BASE_URL}{API_PREFIX}/users/{user_id}/profile', timeout=10)
        return response.status_code == 200
    except:
        return False

def delete_account(user_id):
    """Delete user account"""
    print_step(3, f'Deleting account: {user_id}')
    start_time = time.time()
    try:
        response = requests.delete(f'{BASE_URL}{API_PREFIX}/users/{user_id}/account', timeout=100)
        duration = time.time() - start_time
        
        print_info(f'Deletion took {duration:.2f} seconds')
        
        if response.status_code == 200:
            result = response.json()
            print_success('Account deletion successful')
            print_info('\nDeleted items:')
            for item, value in result.get('deleted_items', {}).items():
                status = '✅' if value else '❌'
                print(f'  {status} {item}: {value}')
            return True, result.get('deleted_items', {})
        else:
            print_error(f'Deletion failed: {response.status_code}')
            print_error(f'Response: {response.text[:500]}')
            return False, {}
    except Exception as e:
        print_error(f'Error deleting account: {e}')
        import traceback
        traceback.print_exc()
        return False, {}

def verify_deletion(user_id):
    """Verify user is completely deleted"""
    print_step(4, f'Verifying deletion: {user_id}')
    checks = {}
    
    endpoints = [
        ('Profile', f'/users/{user_id}/profile'),
        ('Lock Status', f'/users/{user_id}/lock-status'),
        ('Subscription Status', f'/subscription/status/{user_id}')
    ]
    
    for name, path in endpoints:
        try:
            response = requests.get(f'{BASE_URL}{API_PREFIX}{path}', timeout=10)
            checks[name] = response.status_code == 404
            if checks[name]:
                print_success(f'{name}: Returns 404 (correct)')
            else:
                print_error(f'{name}: Returns {response.status_code} (expected 404)')
        except Exception as e:
            print_error(f'{name}: Error - {e}')
            checks[name] = False
    
    return checks

def main():
    print('\n' + '='*60)
    print('COMPREHENSIVE ACCOUNT DELETION TEST')
    print('='*60)
    
    # Use provided user ID or create a test one
    if len(sys.argv) > 1:
        test_user_id = sys.argv[1]
        print_info(f'Using provided user ID: {test_user_id}')
        
        # Check if user exists
        if verify_user_exists(test_user_id):
            print_info('User already exists, will add test data and then delete')
        else:
            print_error('User does not exist. Cannot proceed.')
            return
    else:
        # Generate test user ID
        test_user_id = f"test_delete_{int(time.time())}"
        test_email = f"test_delete_{int(time.time())}@test.com"
        print_info(f'Generated test user ID: {test_user_id}')
        
        # Create user profile
        if not create_test_user_profile(test_user_id, test_email):
            print_error('Failed to create test user. Exiting.')
            return
    
    # Add test data
    added_data = add_test_data(test_user_id)
    time.sleep(1)  # Brief pause
    
    # Verify data was added
    print_info('Verifying data was added...')
    if verify_user_exists(test_user_id):
        print_success('User exists with data')
    else:
        print_error('User not found after adding data')
        return
    
    # Delete account
    success, deleted_items = delete_account(test_user_id)
    
    if not success:
        print_error('Account deletion failed')
        return
    
    # Wait for consistency
    time.sleep(2)
    
    # Verify deletion
    checks = verify_deletion(test_user_id)
    
    # Summary
    print_step(5, 'Test Summary')
    print(f'Deletion Success: {"✅ YES" if success else "❌ NO"}')
    print(f'\nData Added:')
    for item, count in added_data.items():
        print(f'  {item}: {count}')
    print(f'\nDeleted Items:')
    for item, value in deleted_items.items():
        status = '✅' if value else '❌'
        print(f'  {status} {item}: {value}')
    print(f'\nVerification Checks:')
    all_passed = all(checks.values())
    for check_name, check_result in checks.items():
        status = '✅ PASS' if check_result else '❌ FAIL'
        print(f'  {check_name}: {status}')
    
    if success and all_passed:
        print_success('\n🎉 All tests passed! Account deletion is working correctly.')
        return 0
    elif success:
        print_error('\n⚠️  Deletion succeeded but some verification checks failed.')
        return 1
    else:
        print_error('\n❌ Account deletion failed.')
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print('\n\nTest interrupted by user')
        sys.exit(1)
    except Exception as e:
        print_error(f'\nTest failed with error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
