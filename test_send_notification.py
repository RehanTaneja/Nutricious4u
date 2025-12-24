#!/usr/bin/env python3
"""
Test sending a real push notification to verify tokens work
"""

import json
import requests
from datetime import datetime

def send_test_notification(token: str, user_name: str):
    """Send a test notification to the given token"""
    
    print(f"\n{'='*60}")
    print(f"SENDING TEST NOTIFICATION")
    print(f"{'='*60}")
    print(f"To: {user_name}")
    print(f"Token: {token[:40]}...")
    
    payload = {
        "to": token,
        "title": "🔔 Push Notification Test",
        "body": f"Test at {datetime.now().strftime('%H:%M:%S')} - If you see this, notifications are WORKING!",
        "sound": "default",
        "priority": "high",
        "data": {
            "type": "diagnostic_test",
            "timestamp": datetime.now().isoformat(),
            "test_id": f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    }
    
    print(f"\nPayload: {json.dumps(payload, indent=2)}")
    print(f"\nSending to Expo Push Service...")
    
    try:
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        result = response.json()
        print(f"Response Body: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            status = result.get("data", {}).get("status")
            if status == "ok":
                print(f"\n✅ SUCCESS! Notification sent successfully!")
                print(f"   Check {user_name}'s device for the notification.")
                return True
            elif status == "error":
                error_msg = result.get("data", {}).get("message", "Unknown")
                error_details = result.get("data", {}).get("details", {})
                print(f"\n❌ EXPO ERROR: {error_msg}")
                
                if "DeviceNotRegistered" in error_msg:
                    print("   → Token is INVALID or EXPIRED!")
                    print("   → User needs to log out and log back in to get a new token.")
                elif "InvalidCredentials" in error_msg:
                    print("   → APNs/FCM credentials are MISSING!")
                    print("   → Run 'eas credentials' to configure push credentials.")
                elif error_details:
                    print(f"   → Error details: {error_details}")
                return False
        else:
            print(f"\n❌ HTTP ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        return False


def main():
    # Initialize Firebase
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    try:
        app = firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate('backend/services/firebase_service_account.json')
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    print("=" * 60)
    print("PUSH NOTIFICATION TOKEN TEST")
    print("=" * 60)
    
    # Get users with tokens
    users_with_tokens = []
    
    for user in db.collection("user_profiles").stream():
        data = user.to_dict()
        token = data.get("expoPushToken") or data.get("notificationToken")
        if token and token.startswith("ExponentPushToken"):
            users_with_tokens.append({
                "id": user.id,
                "name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
                "token": token,
                "platform": data.get("platform", "unknown"),
                "is_dietician": data.get("isDietician", False),
                "last_update": data.get("lastTokenUpdate", "unknown")
            })
    
    if not users_with_tokens:
        print("❌ No users with valid push tokens found!")
        return
    
    print(f"\nFound {len(users_with_tokens)} users with tokens:")
    for i, user in enumerate(users_with_tokens):
        print(f"  {i+1}. {user['name']} ({user['platform']}) - {'Dietician' if user['is_dietician'] else 'User'}")
        print(f"      Token: {user['token'][:30]}...")
        print(f"      Last update: {user['last_update']}")
    
    # Test each user
    print("\n" + "=" * 60)
    print("TESTING EACH TOKEN")
    print("=" * 60)
    
    results = {}
    for user in users_with_tokens:
        success = send_test_notification(user['token'], user['name'])
        results[user['name']] = success
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {name}: {status}")
    
    successful = sum(1 for s in results.values() if s)
    print(f"\nTotal: {successful}/{len(results)} notifications sent successfully")
    
    if successful == len(results):
        print("\n🎉 All tokens are valid! Push notifications are working!")
        print("   The issue is that NEW users are not getting tokens registered.")
    else:
        print("\n⚠️  Some tokens are invalid. Users need to re-login to refresh tokens.")


if __name__ == "__main__":
    main()

