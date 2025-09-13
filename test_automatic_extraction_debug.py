#!/usr/bin/env python3
"""
Debug script to test automatic diet notification extraction
"""

import requests
import json

# Backend URL (adjust if needed)
BACKEND_URL = "https://nutricious4u-backend-production.up.railway.app"
# BACKEND_URL = "http://localhost:8000"  # Uncomment for local testing

def test_automatic_extraction_debug(user_id):
    """Test the automatic extraction debug endpoint"""
    print(f"🧪 Testing automatic extraction for user: {user_id}")
    print("=" * 60)
    
    try:
        # Test the debug endpoint
        response = requests.post(f"{BACKEND_URL}/api/users/{user_id}/diet/notifications/test-automatic")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test endpoint successful!")
            print(f"📄 Diet PDF URL: {result.get('diet_pdf_url', 'Not found')}")
            print(f"🔢 Extraction count: {result.get('extraction_count', 0)}")
            print(f"📅 Last upload: {result.get('user_data_last_upload', 'Not found')}")
            print(f"🤖 Automatic extraction working: {result.get('automatic_extraction_working', False)}")
            
            if result.get('notifications'):
                print(f"\n📋 Sample notifications (first 3):")
                for i, notif in enumerate(result['notifications'][:3], 1):
                    print(f"  {i}. {notif.get('time', 'No time')} - {notif.get('message', 'No message')}")
                    print(f"     Days: {notif.get('selectedDays', 'No days')}")
            
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
                
        else:
            print(f"❌ Test endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing automatic extraction: {e}")

def test_manual_extraction(user_id):
    """Test the manual extraction endpoint for comparison"""
    print(f"\n🔧 Testing manual extraction for user: {user_id}")
    print("=" * 60)
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/users/{user_id}/diet/notifications/extract")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Manual extraction successful!")
            print(f"📋 Message: {result.get('message', 'No message')}")
            print(f"🔢 Notification count: {len(result.get('notifications', []))}")
            
            if result.get('notifications'):
                print(f"\n📋 Sample notifications (first 3):")
                for i, notif in enumerate(result['notifications'][:3], 1):
                    print(f"  {i}. {notif.get('time', 'No time')} - {notif.get('message', 'No message')}")
                    print(f"     Days: {notif.get('selectedDays', 'No days')}")
        else:
            print(f"❌ Manual extraction failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing manual extraction: {e}")

def check_user_notifications(user_id):
    """Check what notifications are currently stored for the user"""
    print(f"\n📋 Checking stored notifications for user: {user_id}")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/users/{user_id}/diet/notifications")
        
        if response.status_code == 200:
            result = response.json()
            notifications = result.get('diet_notifications', [])
            print(f"✅ Found {len(notifications)} stored notifications")
            
            if notifications:
                print(f"\n📋 All stored notifications:")
                for i, notif in enumerate(notifications, 1):
                    print(f"  {i}. {notif.get('time', 'No time')} - {notif.get('message', 'No message')}")
                    print(f"     Days: {notif.get('selectedDays', 'No days')}")
                    print(f"     Source: {notif.get('source', 'Unknown')}")
                    print()
            else:
                print("⚠️ No notifications found in storage")
                
        else:
            print(f"❌ Failed to get notifications: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking notifications: {e}")

def main():
    """Main debug function"""
    print("🔍 Automatic Diet Extraction Debug")
    print("=" * 60)
    
    # You can replace this with any user ID you want to test
    user_id = input("Enter user ID to test (or press Enter for default): ").strip()
    if not user_id:
        user_id = "default_user_id"  # Replace with a real user ID
        
    print(f"\n🎯 Testing automatic extraction for user: {user_id}")
    
    # Run all tests
    test_automatic_extraction_debug(user_id)
    test_manual_extraction(user_id)
    check_user_notifications(user_id)
    
    print("\n📊 Debug Summary:")
    print("=" * 60)
    print("1. If automatic extraction shows 0 notifications but manual works:")
    print("   - Issue is in the automatic extraction process during upload")
    print("   - Check PDF URL handling in upload endpoint")
    print()
    print("2. If both show 0 notifications:")
    print("   - Issue is in the diet PDF format or content")
    print("   - Check if PDF has proper time patterns")
    print()
    print("3. If both work but you don't see notifications in app:")
    print("   - Issue is in mobile app notification handling")
    print("   - Check notification scheduling and display logic")
    print()
    print("🔧 Next Steps:")
    print("- Check backend logs during diet upload")
    print("- Verify diet PDF format and content")
    print("- Test notification popup timing and conditions")

if __name__ == "__main__":
    main()
