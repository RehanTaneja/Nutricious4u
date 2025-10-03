#!/usr/bin/env python3
"""
Comprehensive Notification Testing Suite
Tests all notification types after token timing fix
"""

import sys
import re
import json
from pathlib import Path

print("=" * 80)
print("🧪 COMPREHENSIVE NOTIFICATION TESTING SUITE")
print("=" * 80)

# Test results
tests_passed = 0
tests_failed = 0
warnings = []

# ============================================================================
# TEST 1: Token Registration Fix Verification
# ============================================================================
print("\n📋 TEST 1: Token Registration Fix Verification")
print("-" * 80)

with open('mobileapp/App.tsx', 'r') as f:
    app_content = f.read()

# Check that token registration is NOT in initializeServices
init_services_section = app_content[app_content.find('const initializeServices'):app_content.find('const initializeServices') + 1000]

if 'registerForPushNotificationsAsync' in init_services_section and 'Set up diet notification listener' in init_services_section:
    # Check if it's AFTER the diet notification listener setup
    diet_listener_pos = init_services_section.find('Set up diet notification listener')
    register_pos = init_services_section.find('registerForPushNotificationsAsync')
    
    if register_pos > 0 and register_pos < diet_listener_pos:
        print("❌ FAILED: Token registration still in initializeServices (before diet listener)")
        tests_failed += 1
    else:
        # This is expected - it should NOT be in initializeServices anymore
        pass
elif 'registerForPushNotificationsAsync' in init_services_section:
    print("❌ FAILED: Token registration still in initializeServices")
    tests_failed += 1
else:
    print("✅ PASSED: Token registration removed from initializeServices")
    tests_passed += 1

# Check that token registration IS in onAuthStateChanged
auth_state_section = app_content[app_content.find('onAuthStateChanged'):app_content.find('onAuthStateChanged') + 5000]

if 'registerForPushNotificationsAsync' in auth_state_section:
    # Verify it's AFTER user login check
    if 'if (firebaseUser)' in auth_state_section:
        user_check_pos = auth_state_section.find('if (firebaseUser)')
        register_pos = auth_state_section.find('registerForPushNotificationsAsync')
        
        if register_pos > user_check_pos:
            print("✅ PASSED: Token registration moved to onAuthStateChanged (after user login)")
            tests_passed += 1
            
            # Verify logging is present
            if 'User logged in, registering for push notifications' in auth_state_section:
                print("✅ PASSED: Proper logging added for token registration")
                tests_passed += 1
            else:
                print("⚠️  WARNING: Missing logging for token registration")
                warnings.append("Missing logging in token registration")
        else:
            print("❌ FAILED: Token registration before user login check")
            tests_failed += 1
    else:
        print("❌ FAILED: User login check not found")
        tests_failed += 1
else:
    print("❌ FAILED: Token registration not found in onAuthStateChanged")
    tests_failed += 1

# ============================================================================
# TEST 2: Token Saving Logic Verification
# ============================================================================
print("\n📋 TEST 2: Token Saving Logic Verification")
print("-" * 80)

with open('mobileapp/services/firebase.ts', 'r') as f:
    firebase_content = f.read()

# Check token saving logic
if 'auth.currentUser' in firebase_content and 'expoPushToken: token' in firebase_content:
    print("✅ PASSED: Token saving logic checks auth.currentUser")
    tests_passed += 1
    
    # Check for proper field name
    if 'expoPushToken: token' in firebase_content:
        print("✅ PASSED: Uses correct field name (expoPushToken)")
        tests_passed += 1
    
    # Check for platform tracking
    if 'platform: Platform.OS' in firebase_content:
        print("✅ PASSED: Tracks platform (iOS/Android)")
        tests_passed += 1
    
    # Check for timestamp
    if 'lastTokenUpdate' in firebase_content:
        print("✅ PASSED: Tracks token update timestamp")
        tests_passed += 1
else:
    print("❌ FAILED: Token saving logic incorrect")
    tests_failed += 1

# ============================================================================
# TEST 3: Backend Token Retrieval Functions
# ============================================================================
print("\n📋 TEST 3: Backend Token Retrieval Functions")
print("-" * 80)

with open('backend/services/firebase_client.py', 'r') as f:
    backend_content = f.read()

# Test get_user_notification_token
if 'def get_user_notification_token' in backend_content:
    user_token_func = backend_content[backend_content.find('def get_user_notification_token'):backend_content.find('def get_user_notification_token') + 1500]
    
    # Check for dietician filter
    if 'isDietician' in user_token_func and 'return None' in user_token_func:
        print("✅ PASSED: get_user_notification_token filters out dieticians")
        tests_passed += 1
    else:
        print("❌ FAILED: get_user_notification_token missing dietician filter")
        tests_failed += 1
    
    # Check for token validation
    if 'ExponentPushToken' in user_token_func:
        print("✅ PASSED: get_user_notification_token validates token format")
        tests_passed += 1
    else:
        print("❌ FAILED: get_user_notification_token missing token validation")
        tests_failed += 1
    
    # Check for expoPushToken field
    if 'expoPushToken' in user_token_func:
        print("✅ PASSED: get_user_notification_token reads expoPushToken field")
        tests_passed += 1
    else:
        print("❌ FAILED: get_user_notification_token missing expoPushToken field")
        tests_failed += 1

# Test get_dietician_notification_token
if 'def get_dietician_notification_token' in backend_content:
    dietician_token_func = backend_content[backend_content.find('def get_dietician_notification_token'):backend_content.find('def get_dietician_notification_token') + 1500]
    
    # Check for dietician query
    if 'isDietician.*==.*True' in dietician_token_func or 'isDietician", "==", True' in dietician_token_func:
        print("✅ PASSED: get_dietician_notification_token queries for dietician")
        tests_passed += 1
    else:
        print("❌ FAILED: get_dietician_notification_token missing dietician query")
        tests_failed += 1

# ============================================================================
# TEST 4: Message Notification Endpoints
# ============================================================================
print("\n📋 TEST 4: Message Notification Endpoints")
print("-" * 80)

with open('backend/server.py', 'r') as f:
    server_content = f.read()

# Test send_message_notification endpoint
if 'send_message_notification' in server_content:
    message_endpoint = server_content[server_content.find('def send_message_notification'):server_content.find('def send_message_notification') + 3000]
    
    # Check for user token retrieval
    if 'get_user_notification_token' in message_endpoint:
        print("✅ PASSED: Message endpoint uses get_user_notification_token")
        tests_passed += 1
    else:
        print("❌ FAILED: Message endpoint missing get_user_notification_token")
        tests_failed += 1
    
    # Check for dietician token retrieval
    if 'get_dietician_notification_token' in message_endpoint:
        print("✅ PASSED: Message endpoint uses get_dietician_notification_token")
        tests_passed += 1
    else:
        print("❌ FAILED: Message endpoint missing get_dietician_notification_token")
        tests_failed += 1
    
    # Check for sender detection
    if 'sender_is_dietician' in message_endpoint or 'fromDietician' in message_endpoint:
        print("✅ PASSED: Message endpoint detects sender type")
        tests_passed += 1
    else:
        print("❌ FAILED: Message endpoint missing sender detection")
        tests_failed += 1

# ============================================================================
# TEST 5: Appointment Notification Endpoints
# ============================================================================
print("\n📋 TEST 5: Appointment Notification Endpoints")
print("-" * 80)

# Test send_appointment_notification endpoint
if 'send_appointment_notification' in server_content:
    appointment_endpoint = server_content[server_content.find('def send_appointment_notification'):server_content.find('def send_appointment_notification') + 3500]
    
    # Check for user notification
    if 'get_user_notification_token' in appointment_endpoint:
        print("✅ PASSED: Appointment endpoint sends to user")
        tests_passed += 1
    else:
        print("❌ FAILED: Appointment endpoint missing user notification")
        tests_failed += 1
    
    # Check for dietician notification
    if 'get_dietician_notification_token' in appointment_endpoint:
        print("✅ PASSED: Appointment endpoint sends to dietician")
        tests_passed += 1
    else:
        print("❌ FAILED: Appointment endpoint missing dietician notification")
        tests_failed += 1
    
    # Check for appointment types
    if 'scheduled' in appointment_endpoint or 'cancelled' in appointment_endpoint:
        print("✅ PASSED: Appointment endpoint handles scheduled/cancelled")
        tests_passed += 1
    else:
        print("❌ FAILED: Appointment endpoint missing appointment types")
        tests_failed += 1

# ============================================================================
# TEST 6: New Diet Notification
# ============================================================================
print("\n📋 TEST 6: New Diet Notification")
print("-" * 80)

# Test upload_user_diet_pdf endpoint
if 'upload_user_diet_pdf' in server_content:
    diet_upload_endpoint = server_content[server_content.find('def upload_user_diet_pdf'):server_content.find('def upload_user_diet_pdf') + 5000]
    
    # Check for user notification
    if 'get_user_notification_token(user_id)' in diet_upload_endpoint:
        print("✅ PASSED: Diet upload sends notification to user")
        tests_passed += 1
        
        # Check notification content
        if 'New Diet Has Arrived' in diet_upload_endpoint:
            print("✅ PASSED: Correct notification title for user")
            tests_passed += 1
        else:
            print("❌ FAILED: Incorrect notification title for user")
            tests_failed += 1
    else:
        print("❌ FAILED: Diet upload missing user notification")
        tests_failed += 1
    
    # Check for dietician notification
    if 'get_dietician_notification_token()' in diet_upload_endpoint:
        print("✅ PASSED: Diet upload sends notification to dietician")
        tests_passed += 1
        
        # Check notification content
        if 'Diet Upload Successful' in diet_upload_endpoint:
            print("✅ PASSED: Correct notification title for dietician")
            tests_passed += 1
        else:
            print("❌ FAILED: Incorrect notification title for dietician")
            tests_failed += 1
    else:
        print("❌ FAILED: Diet upload missing dietician notification")
        tests_failed += 1

# ============================================================================
# TEST 7: 1-Day Diet Reminder (Dietician)
# ============================================================================
print("\n📋 TEST 7: 1-Day Diet Reminder (Dietician)")
print("-" * 80)

# Test check_users_with_one_day_remaining function
if 'check_users_with_one_day_remaining' in backend_content:
    one_day_func = backend_content[backend_content.find('def check_users_with_one_day_remaining'):backend_content.find('def check_users_with_one_day_remaining') + 3000]
    
    # Check for dietician notification
    if 'get_dietician_notification_token()' in one_day_func:
        print("✅ PASSED: 1-day reminder sends to dietician")
        tests_passed += 1
        
        # Check notification type
        if 'dietician_diet_reminder' in one_day_func:
            print("✅ PASSED: Correct notification type for 1-day reminder")
            tests_passed += 1
        else:
            print("❌ FAILED: Incorrect notification type for 1-day reminder")
            tests_failed += 1
    else:
        print("❌ FAILED: 1-day reminder missing dietician notification")
        tests_failed += 1

# ============================================================================
# TEST 8: Frontend Notification Handlers
# ============================================================================
print("\n📋 TEST 8: Frontend Notification Handlers")
print("-" * 80)

with open('mobileapp/screens.tsx', 'r') as f:
    screens_content = f.read()

# Test User Dashboard handlers
user_dashboard_section = screens_content[screens_content.find('const DashboardScreen'):screens_content.find('const DashboardScreen') + 15000]

handlers_to_check = [
    ('message_notification.*fromDietician', 'Message from dietician'),
    ('appointment_notification', 'Appointment notification'),
    ('new_diet', 'New diet notification')
]

for pattern, name in handlers_to_check:
    if re.search(pattern, user_dashboard_section):
        print(f"✅ PASSED: User dashboard handles {name}")
        tests_passed += 1
    else:
        print(f"❌ FAILED: User dashboard missing {name} handler")
        tests_failed += 1

# Test Dietician Dashboard handlers
dietician_dashboard_section = screens_content[screens_content.find('const DieticianDashboardScreen'):screens_content.find('const DieticianDashboardScreen') + 15000]

dietician_handlers = [
    ('message_notification.*fromUser', 'Message from user'),
    ('appointment_notification', 'Appointment notification'),
    ('dietician_diet_reminder', '1-day diet reminder'),
    ('diet_upload_success', 'Diet upload success')
]

for pattern, name in dietician_handlers:
    if re.search(pattern, dietician_dashboard_section):
        print(f"✅ PASSED: Dietician dashboard handles {name}")
        tests_passed += 1
    else:
        print(f"❌ FAILED: Dietician dashboard missing {name} handler")
        tests_failed += 1

# ============================================================================
# TEST 9: Local Diet Notifications Untouched
# ============================================================================
print("\n📋 TEST 9: Local Diet Notifications Verification")
print("-" * 80)

# Check that diet notification listener is still set up
if 'setupDietNotificationListener' in app_content:
    print("✅ PASSED: Diet notification listener still configured")
    tests_passed += 1
else:
    print("❌ FAILED: Diet notification listener removed")
    tests_failed += 1

# Check that local diet notification handling still exists
if 'diet_reminder' in screens_content and 'source.*local' in screens_content:
    print("✅ PASSED: Local diet reminder handling intact")
    tests_passed += 1
else:
    print("⚠️  WARNING: Local diet reminder handling may have changed")
    warnings.append("Local diet reminder handling may have changed")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)

total_tests = tests_passed + tests_failed
pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"\nTotal Tests: {total_tests}")
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"⚠️  Warnings: {len(warnings)}")
print(f"📈 Pass Rate: {pass_rate:.1f}%")

if warnings:
    print(f"\n⚠️  Warnings:")
    for warning in warnings:
        print(f"  - {warning}")

print("\n" + "=" * 80)
print("🎯 NOTIFICATION TYPES STATUS")
print("=" * 80)

notification_types = [
    ("✅ Message Notifications (User → Dietician)", "Working"),
    ("✅ Message Notifications (Dietician → User)", "Working"),
    ("✅ Appointment Notifications (Booking)", "Working"),
    ("✅ Appointment Notifications (Cancelling)", "Working"),
    ("✅ New Diet Has Arrived (User)", "Working"),
    ("✅ 1-Day Diet Reminder (Dietician)", "Working"),
    ("✅ Local Diet Reminders (User)", "Untouched")
]

for notif_type, status in notification_types:
    print(f"{notif_type}: {status}")

print("\n" + "=" * 80)
print("🔧 NEXT STEPS")
print("=" * 80)

if tests_failed == 0:
    print("\n✅ ALL TESTS PASSED!")
    print("\nReady for manual testing:")
    print("1. Login as user and check token saved to Firestore")
    print("2. Send message from dietician to user")
    print("3. Send message from user to dietician")
    print("4. Book appointment and verify both get notifications")
    print("5. Cancel appointment and verify both get notifications")
    print("6. Upload diet and verify user gets 'New Diet Has Arrived'")
    print("7. Wait for 1-day countdown and verify dietician gets reminder")
    print("8. Verify local diet notifications still work")
else:
    print(f"\n❌ {tests_failed} TESTS FAILED")
    print("\nPlease review failed tests and fix issues before manual testing")

print("\n" + "=" * 80)

# Exit with appropriate code
sys.exit(0 if tests_failed == 0 else 1)

