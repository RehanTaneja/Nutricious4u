#!/usr/bin/env python3
"""
DEEP DIAGNOSTIC SCRIPT: Token Update Issue
==========================================
This script performs a comprehensive analysis of why push tokens are not updating.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent / "backend" / "services"
sys.path.insert(0, str(backend_dir.parent))

# Initialize Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        print("✓ Firebase already initialized")
    except ValueError:
        # Find the service account file
        service_account_paths = [
            Path(__file__).parent / "backend" / "services" / "firebase_service_account.json",
            Path(__file__).parent / "firebase_service_account.json",
            Path(__file__).parent / "backend" / "firebase_service_account.json",
        ]
        
        cred_path = None
        for path in service_account_paths:
            if path.exists():
                cred_path = path
                break
        
        if not cred_path:
            print("❌ Firebase service account file not found!")
            print("Searched in:", [str(p) for p in service_account_paths])
            sys.exit(1)
        
        print(f"✓ Found service account: {cred_path}")
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
        print("✓ Firebase initialized successfully")
    
    return firestore.client()

def format_timestamp(ts):
    """Format a timestamp for display"""
    if ts is None:
        return "NEVER"
    if isinstance(ts, str):
        try:
            # Try to parse ISO format
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            return ts
    if hasattr(ts, 'timestamp'):
        # Firestore timestamp
        dt = ts.timestamp()
        return datetime.fromtimestamp(dt).strftime("%Y-%m-%d %H:%M:%S UTC")
    return str(ts)

def time_ago(ts):
    """Return human-readable time difference"""
    if ts is None:
        return "never"
    
    now = datetime.utcnow()
    
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
        except:
            return "unknown"
    elif hasattr(ts, 'timestamp'):
        dt = datetime.fromtimestamp(ts.timestamp())
    else:
        return "unknown"
    
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hours ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minutes ago"
    else:
        return f"{diff.seconds} seconds ago"

def analyze_user_profiles(db):
    """Analyze all user profiles for token issues"""
    print("\n" + "="*80)
    print("📊 USER PROFILES ANALYSIS")
    print("="*80)
    
    try:
        users = db.collection('user_profiles').get()
        user_list = list(users)
        print(f"\n📈 Total users in user_profiles: {len(user_list)}")
    except Exception as e:
        print(f"❌ Error fetching user_profiles: {e}")
        return
    
    # Categorize users
    with_token = []
    without_token = []
    recent_updates = []  # Updated in last 24 hours
    
    now = datetime.utcnow()
    
    print("\n" + "-"*80)
    print("DETAILED USER ANALYSIS:")
    print("-"*80)
    
    for user_doc in user_list:
        data = user_doc.to_dict()
        user_id = user_doc.id
        
        # Extract relevant fields
        token = data.get('expoPushToken') or data.get('notificationToken')
        platform = data.get('platform', 'unknown')
        last_update = data.get('lastTokenUpdate')
        first_name = data.get('firstName', 'Unknown')
        email = data.get('email', 'No email')
        
        has_token = bool(token)
        
        print(f"\n👤 {first_name} ({user_id[:8]}...)")
        print(f"   Email: {email}")
        print(f"   Platform: {platform}")
        print(f"   Has Token: {'✅ Yes' if has_token else '❌ No'}")
        
        if has_token:
            print(f"   Token: {token[:30]}..." if len(token) > 30 else f"   Token: {token}")
            with_token.append(user_id)
        else:
            without_token.append(user_id)
        
        print(f"   Last Token Update: {format_timestamp(last_update)} ({time_ago(last_update)})")
        
        # Check if updated recently
        if last_update:
            try:
                if isinstance(last_update, str):
                    update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00')).replace(tzinfo=None)
                elif hasattr(last_update, 'timestamp'):
                    update_dt = datetime.fromtimestamp(last_update.timestamp())
                else:
                    update_dt = None
                
                if update_dt and (now - update_dt).days < 1:
                    recent_updates.append(user_id)
                    print(f"   🆕 RECENT UPDATE!")
            except Exception as e:
                print(f"   ⚠️ Could not parse update time: {e}")
        
        # Show all notification-related fields
        notification_fields = ['expoPushToken', 'notificationToken', 'pushToken', 
                               'fcmToken', 'platform', 'lastTokenUpdate', 'tokenUpdatedAt']
        existing_fields = {k: v for k, v in data.items() if k in notification_fields and v}
        if existing_fields:
            print(f"   All notification fields: {list(existing_fields.keys())}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"   Total users: {len(user_list)}")
    print(f"   With token: {len(with_token)} ({100*len(with_token)//len(user_list) if user_list else 0}%)")
    print(f"   Without token: {len(without_token)} ({100*len(without_token)//len(user_list) if user_list else 0}%)")
    print(f"   Updated in last 24h: {len(recent_updates)}")
    
    if not recent_updates:
        print("\n   ⚠️ NO TOKENS UPDATED IN THE LAST 24 HOURS!")
        print("   This indicates the token registration is NOT working!")
    
    return {
        'total': len(user_list),
        'with_token': len(with_token),
        'without_token': len(without_token),
        'recent_updates': len(recent_updates)
    }

def check_specific_users(db):
    """Check specific known users"""
    print("\n" + "="*80)
    print("🔍 CHECKING SPECIFIC USERS (Rehan & Dietician)")
    print("="*80)
    
    # Find Rehan and Dietician by email
    users = db.collection('user_profiles').get()
    
    for user_doc in users:
        data = user_doc.to_dict()
        email = data.get('email', '').lower()
        
        if 'rehan' in email or 'nutricious4u' in email:
            print(f"\n📧 Found user: {email}")
            print(f"   User ID: {user_doc.id}")
            print(f"   First Name: {data.get('firstName', 'N/A')}")
            print(f"   Platform: {data.get('platform', 'N/A')}")
            
            token = data.get('expoPushToken')
            if token:
                print(f"   Token: {token}")
                print(f"   Token length: {len(token)}")
                print(f"   Valid format: {token.startswith('ExponentPushToken[')}")
            else:
                print(f"   Token: ❌ MISSING!")
            
            print(f"   Last Token Update: {format_timestamp(data.get('lastTokenUpdate'))}")
            print(f"   Time ago: {time_ago(data.get('lastTokenUpdate'))}")

def diagnose_potential_issues(db, stats):
    """Diagnose potential issues based on the analysis"""
    print("\n" + "="*80)
    print("🔬 DIAGNOSIS")
    print("="*80)
    
    issues = []
    
    if stats['recent_updates'] == 0:
        issues.append({
            'severity': 'CRITICAL',
            'issue': 'No tokens updated in last 24 hours',
            'explanation': 'This means registerForPushNotificationsAsync is either not being called, '
                          'or is failing silently before the Firestore save.',
            'possible_causes': [
                '1. Function not being called at all',
                '2. Permission not granted (user denied notifications)',
                '3. getExpoPushTokenAsync() failing',
                '4. Firestore save failing (permission or network issue)',
                '5. User object not available during registration',
                '6. Build does not contain latest code changes'
            ]
        })
    
    if stats['without_token'] > stats['with_token']:
        issues.append({
            'severity': 'HIGH',
            'issue': f"{stats['without_token']}/{stats['total']} users have no token",
            'explanation': 'Most users are not getting tokens assigned.',
            'possible_causes': [
                '1. Registration function failing early',
                '2. New user onboarding not triggering registration',
                '3. Silent failures in the registration flow'
            ]
        })
    
    if not issues:
        issues.append({
            'severity': 'INFO',
            'issue': 'No critical issues detected in Firestore data',
            'explanation': 'The data looks okay. The issue might be in the app code flow.',
            'possible_causes': []
        })
    
    for issue in issues:
        print(f"\n🔴 [{issue['severity']}] {issue['issue']}")
        print(f"   {issue['explanation']}")
        if issue['possible_causes']:
            print("   Possible causes:")
            for cause in issue['possible_causes']:
                print(f"      {cause}")
    
    return issues

def check_if_code_changes_are_deployed():
    """Check if the code changes are likely in the deployed build"""
    print("\n" + "="*80)
    print("📦 CODE DEPLOYMENT CHECK")
    print("="*80)
    
    # Check firebase.ts for our fixes
    firebase_ts_path = Path(__file__).parent / "mobileapp" / "services" / "firebase.ts"
    
    if firebase_ts_path.exists():
        content = firebase_ts_path.read_text()
        
        checks = [
            ('return null; // FIX: Return null to signal failure', 'Failure return fix'),
            ('return null; // FIX: Return null (not token)', 'No user return fix'),
            ('setNotificationChannelAsync', 'Android channel setup'),
        ]
        
        print("\nChecking firebase.ts for applied fixes:")
        all_present = True
        for pattern, name in checks:
            if pattern in content:
                print(f"   ✅ {name}: Present in code")
            else:
                print(f"   ❌ {name}: NOT found in code")
                all_present = False
        
        if all_present:
            print("\n   ✅ All code fixes are present in the source code.")
            print("   ⚠️ BUT: You need to BUILD a new APK and INSTALL it for changes to take effect!")
        else:
            print("\n   ❌ Some fixes are missing from the code!")
    else:
        print(f"   ❌ Could not find firebase.ts at {firebase_ts_path}")

def main():
    print("="*80)
    print("🔍 DEEP DIAGNOSTIC: WHY ARE PUSH TOKENS NOT UPDATING?")
    print("="*80)
    print(f"   Run time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Initialize Firebase
    db = initialize_firebase()
    
    # Run analyses
    stats = analyze_user_profiles(db)
    check_specific_users(db)
    diagnose_potential_issues(db, stats)
    check_if_code_changes_are_deployed()
    
    print("\n" + "="*80)
    print("🎯 NEXT STEPS TO IDENTIFY ROOT CAUSE")
    print("="*80)
    print("""
1. VERIFY BUILD CONTAINS LATEST CODE:
   - Did you run 'eas build' AFTER the code changes were made?
   - Did you install the NEW build on the test devices?
   
2. CHECK DEVICE LOGS:
   - Connect device via USB
   - Run: adb logcat | grep -E "(PUSH TOKEN|NOTIFICATIONS)"
   - Look for the debug output from registerForPushNotificationsAsync
   
3. TEST NOTIFICATION PERMISSION:
   - On the device, go to Settings > Apps > Nutricious4u > Notifications
   - Verify notifications are enabled
   
4. CHECK FIRESTORE RULES:
   - Ensure authenticated users can write to user_profiles/{userId}
   
5. MANUAL TOKEN TEST:
   - After logging in, immediately check Firestore
   - If token appears briefly then disappears, there's a race condition
""")
    
    print("\n" + "="*80)
    print("🔑 MOST LIKELY ROOT CAUSE BASED ON THIS ANALYSIS:")
    print("="*80)
    
    if stats['recent_updates'] == 0:
        print("""
THE BUILD LIKELY DOES NOT CONTAIN THE LATEST CODE FIXES.

To verify:
1. Check when the current installed APK was built
2. Check when the code fixes were committed
3. If build is older than fixes, you need to:
   a. Run: cd mobileapp && eas build --platform android --profile production
   b. Download and install the new APK
   c. Have users log out and log back in
""")
    else:
        print("""
Some tokens ARE being updated. The issue might be:
1. Specific users have notification permission denied
2. Network issues during Firestore save
3. Timing issues with authentication flow
""")

if __name__ == "__main__":
    main()

