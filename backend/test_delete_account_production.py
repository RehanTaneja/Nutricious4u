#!/usr/bin/env python3
"""
Production account deletion test
"""
import requests
import json
import time
import sys

BASE_URL = 'https://nutricious4u-production.up.railway.app'
API_PREFIX = '/api'

def print_step(step, message):
    print(f'\n{"="*60}')
    print(f'[STEP {step}] {message}')
    print(f'{"="*60}')

def verify_user_exists(user_id):
    """Verify user exists before deletion"""
    print_step(1, f'Verifying user exists: {user_id}')
    try:
        response = requests.get(f'{BASE_URL}{API_PREFIX}/users/{user_id}/profile', timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            print(f'✅ User exists: {user_data.get("firstName", "N/A")} {user_data.get("lastName", "")}')
            print(f'   Email: {user_data.get("email", "N/A")}')
            print(f'   Subscription: {user_data.get("subscriptionPlan", "N/A")}')
            return True
        elif response.status_code == 404:
            print(f'❌ User not found (404)')
            return False
        else:
            print(f'❌ Unexpected status: {response.status_code}')
            print(f'   Response: {response.text[:200]}')
            return False
    except Exception as e:
        print(f'❌ Error verifying user: {e}')
        return False

def delete_account(user_id):
    """Delete user account"""
    print_step(2, f'Deleting account: {user_id}')
    start_time = time.time()
    try:
        response = requests.delete(f'{BASE_URL}{API_PREFIX}/users/{user_id}/account', timeout=100)
        duration = time.time() - start_time
        
        print(f'⏱️  Deletion took {duration:.2f} seconds')
        
        if response.status_code == 200:
            result = response.json()
            print('✅ Account deletion successful')
            print(f'\nDeleted items:')
            for item, value in result.get('deleted_items', {}).items():
                status = '✅' if value else '❌'
                print(f'  {status} {item}: {value}')
            return True, result.get('deleted_items', {})
        elif response.status_code == 404:
            print('❌ User not found (404) - may have been deleted already')
            return False, {}
        elif response.status_code == 408:
            print('❌ Request timed out (408)')
            return False, {}
        elif response.status_code == 403:
            print('❌ Forbidden (403) - User may be a dietician')
            return False, {}
        else:
            print(f'❌ Deletion failed: {response.status_code}')
            print(f'   Response: {response.text[:500]}')
            return False, {}
    except requests.exceptions.Timeout:
        print('❌ Request timed out (>100 seconds)')
        return False, {}
    except Exception as e:
        print(f'❌ Error deleting account: {e}')
        import traceback
        traceback.print_exc()
        return False, {}

def verify_deletion(user_id):
    """Verify user is completely deleted"""
    print_step(3, f'Verifying deletion: {user_id}')
    checks = {}
    
    # Check 1: Profile should return 404
    try:
        response = requests.get(f'{BASE_URL}{API_PREFIX}/users/{user_id}/profile', timeout=10)
        checks['profile'] = response.status_code == 404
        if checks['profile']:
            print('✅ Profile endpoint returns 404 (correct)')
        else:
            print(f'❌ Profile still exists: {response.status_code}')
    except Exception as e:
        print(f'❌ Error checking profile: {e}')
        checks['profile'] = False
    
    # Check 2: Lock status should return 404
    try:
        response = requests.get(f'{BASE_URL}{API_PREFIX}/users/{user_id}/lock-status', timeout=10)
        checks['lock_status'] = response.status_code == 404
        if checks['lock_status']:
            print('✅ Lock status returns 404 (correct)')
        else:
            print(f'❌ Lock status unexpected: {response.status_code}')
            if response.status_code == 500:
                print('   ⚠️  Server error - endpoint may need fixing')
    except Exception as e:
        print(f'❌ Error checking lock status: {e}')
        checks['lock_status'] = False
    
    # Check 3: Subscription status should return 404
    try:
        response = requests.get(f'{BASE_URL}{API_PREFIX}/subscription/status/{user_id}', timeout=10)
        checks['subscription'] = response.status_code == 404
        if checks['subscription']:
            print('✅ Subscription status returns 404 (correct)')
        else:
            print(f'❌ Subscription status unexpected: {response.status_code}')
    except Exception as e:
        print(f'❌ Error checking subscription: {e}')
        checks['subscription'] = False
    
    return checks

def main():
    print('\n' + '='*60)
    print('ACCOUNT DELETION TEST - PRODUCTION')
    print('='*60)
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = input('\nEnter user ID to test deletion (or press Enter to exit): ').strip()
        if not user_id:
            print('Test cancelled')
            return
    
    print(f'\n⚠️  WARNING: This will DELETE the account for user: {user_id}')
    confirm = input('Type "DELETE" to confirm: ').strip()
    if confirm != "DELETE":
        print('Test cancelled')
        return
    
    # Verify user exists first
    if not verify_user_exists(user_id):
        print('\n❌ User not found or cannot be accessed')
        return
    
    # Run deletion test
    success, deleted_items = delete_account(user_id)
    
    if not success:
        print('\n❌ Account deletion failed')
        return
    
    # Wait a moment for consistency
    time.sleep(2)
    
    # Verify deletion
    final_checks = verify_deletion(user_id)
    
    # Summary
    print('\n' + '='*60)
    print('TEST SUMMARY')
    print('='*60)
    print(f'Deletion Success: {"✅ YES" if success else "❌ NO"}')
    print(f'\nDeleted Items:')
    for item, value in deleted_items.items():
        status = '✅' if value else '❌'
        print(f'  {status} {item}: {value}')
    
    print(f'\nVerification Checks:')
    all_passed = all(final_checks.values())
    for check_name, check_result in final_checks.items():
        status = '✅ PASS' if check_result else '❌ FAIL'
        print(f'  {check_name}: {status}')
    
    if success and all_passed:
        print('\n🎉 All tests passed! Account deletion is working correctly.')
    elif success:
        print('\n⚠️  Deletion succeeded but some verification checks failed.')
    else:
        print('\n❌ Account deletion failed.')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nTest interrupted by user')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
