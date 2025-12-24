#!/usr/bin/env python3
"""
Deep Push Notification Diagnostic - Analyze each user in detail
"""

import os
import json
from datetime import datetime

def initialize_firebase():
    import firebase_admin
    from firebase_admin import credentials, firestore
    try:
        app = firebase_admin.get_app()
        return firestore.client()
    except ValueError:
        cred = credentials.Certificate('backend/services/firebase_service_account.json')
        firebase_admin.initialize_app(cred)
        return firestore.client()

def main():
    db = initialize_firebase()
    
    print("=" * 80)
    print("DETAILED USER ANALYSIS - PUSH NOTIFICATION TOKENS")
    print("=" * 80)
    
    users = list(db.collection("user_profiles").stream())
    
    for user in users:
        data = user.to_dict()
        user_id = user.id
        
        print(f"\n{'─' * 80}")
        print(f"USER: {data.get('firstName', 'N/A')} {data.get('lastName', '')}")
        print(f"{'─' * 80}")
        print(f"  ID: {user_id}")
        print(f"  Email: {data.get('email', 'N/A')}")
        print(f"  Is Dietician: {data.get('isDietician', False)}")
        print(f"  Platform: {data.get('platform', 'NOT SET')}")
        print(f"  Subscription: {data.get('subscriptionPlan', 'NOT SET')}")
        
        # Token status
        expo_token = data.get('expoPushToken')
        notif_token = data.get('notificationToken')
        
        print(f"\n  TOKEN STATUS:")
        if expo_token:
            print(f"    ✅ expoPushToken: {expo_token[:40]}...")
        else:
            print(f"    ❌ expoPushToken: MISSING")
            
        if notif_token:
            print(f"    ✅ notificationToken: {notif_token[:40]}...")
        else:
            print(f"    ❌ notificationToken: MISSING")
            
        last_update = data.get('lastTokenUpdate')
        if last_update:
            print(f"    📅 Last Token Update: {last_update}")
        else:
            print(f"    📅 Last Token Update: NEVER")
        
        # Check what fields exist
        print(f"\n  ALL FIELDS IN DOCUMENT:")
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"    - {key}: {value}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    with_token = sum(1 for u in users for d in [u.to_dict()] if d.get('expoPushToken') or d.get('notificationToken'))
    without_token = len(users) - with_token
    unknown_platform = sum(1 for u in users for d in [u.to_dict()] if not d.get('platform'))
    
    print(f"  Total users: {len(users)}")
    print(f"  With push tokens: {with_token}")
    print(f"  Without push tokens: {without_token}")
    print(f"  Unknown platform: {unknown_platform}")
    
    if unknown_platform > 0:
        print(f"\n  ⚠️  {unknown_platform} users have no 'platform' field set.")
        print(f"     This suggests they either:")
        print(f"     1. Registered before push tokens were implemented")
        print(f"     2. Never logged in after push was added")
        print(f"     3. The token registration isn't saving the platform")

if __name__ == "__main__":
    main()

