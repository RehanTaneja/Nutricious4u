#!/usr/bin/env python3
"""
Verify Token Update Script

This script monitors the dietician's push token in Firestore in real-time.
Run this BEFORE logout/login to verify the token gets updated.

Usage:
    python3 verify_token_update.py
"""

import firebase_admin
from firebase_admin import credentials, firestore
import time
from datetime import datetime

# Initialize Firebase
try:
    app = firebase_admin.get_app()
except:
    cred = credentials.Certificate('backend/services/firebase_service_account.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

DIETICIAN_ID = 'mBVlWBBpoaXyOVr8Y4AoHZunq9f1'

def get_token_info():
    """Get current token info from Firestore"""
    doc = db.collection('user_profiles').document(DIETICIAN_ID).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    return {
        'platform': data.get('platform', 'NOT_SET'),
        'lastTokenUpdate': data.get('lastTokenUpdate', 'NEVER'),
        'token': data.get('expoPushToken', None),
        'tokenPreview': data.get('expoPushToken', 'NONE')[:45] + '...' if data.get('expoPushToken') and len(data.get('expoPushToken', '')) > 45 else data.get('expoPushToken', 'NONE')
    }

def format_info(info):
    """Format token info for display"""
    if not info:
        return "Document not found!"
    return f"""
  Platform:        {info['platform']}
  Last Update:     {info['lastTokenUpdate']}
  Token Preview:   {info['tokenPreview']}
"""

print("="*70)
print("🔍 PUSH TOKEN VERIFICATION MONITOR")
print("="*70)
print()
print(f"Monitoring user: {DIETICIAN_ID}")
print()

initial_info = get_token_info()
print("📌 INITIAL STATE:")
print(format_info(initial_info))

if initial_info:
    if initial_info['platform'] == 'ios':
        print("⚠️  WARNING: Platform is 'ios' - if testing on Android, this should change!")
    
    if initial_info['lastTokenUpdate'] != 'NEVER':
        try:
            update_date = datetime.fromisoformat(initial_info['lastTokenUpdate'].replace('Z', '+00:00'))
            days_old = (datetime.now(update_date.tzinfo) - update_date).days
            if days_old > 1:
                print(f"⚠️  WARNING: Token is {days_old} days old - should update to today's date!")
        except:
            pass

print()
print("="*70)
print("👆 NOW PERFORM THESE STEPS ON THE DEVICE:")
print("="*70)
print("""
1. Open the app on the Samsung tablet
2. Go to Settings/Profile
3. Tap LOG OUT (must actually log out, not just reinstall)
4. Close the app completely
5. Re-open the app
6. Log in with the dietician account
7. GRANT notification permission when prompted
""")
print("="*70)
print("⏳ WATCHING FOR CHANGES... (Press Ctrl+C to stop)")
print("="*70)
print()

last_info = initial_info
check_count = 0

try:
    while True:
        time.sleep(3)  # Check every 3 seconds
        check_count += 1
        
        current_info = get_token_info()
        
        if current_info != last_info:
            print()
            print("="*70)
            print("✅ TOKEN CHANGED!")
            print("="*70)
            print()
            print("BEFORE:")
            print(format_info(last_info))
            print("AFTER:")
            print(format_info(current_info))
            
            # Analyze the change
            if current_info['platform'] != last_info['platform']:
                print(f"✅ Platform changed: {last_info['platform']} → {current_info['platform']}")
            
            if current_info['token'] != last_info['token']:
                print(f"✅ Token changed: Token was updated!")
            
            if current_info['lastTokenUpdate'] != last_info['lastTokenUpdate']:
                print(f"✅ Timestamp changed: {last_info['lastTokenUpdate']} → {current_info['lastTokenUpdate']}")
            
            print()
            print("🎉 Token registration is working!")
            last_info = current_info
        else:
            # Show a dot every 10 checks to indicate we're still watching
            if check_count % 10 == 0:
                print(f"... still watching (checked {check_count} times)")

except KeyboardInterrupt:
    print()
    print()
    print("="*70)
    print("📊 FINAL RESULT")
    print("="*70)
    
    final_info = get_token_info()
    print()
    print("FINAL STATE:")
    print(format_info(final_info))
    
    if final_info == initial_info:
        print("❌ TOKEN WAS NOT UPDATED!")
        print()
        print("This means one of:")
        print("  1. User did not complete logout/login")
        print("  2. registerForPushNotificationsAsync() never ran")
        print("  3. Function ran but failed silently")
        print()
        print("NEXT STEP: Get device logs using 'adb logcat | grep PUSH'")
    else:
        print("✅ TOKEN WAS UPDATED!")
        print()
        print("Push token registration is now working.")
