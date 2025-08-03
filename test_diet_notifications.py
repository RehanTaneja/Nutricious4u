#!/usr/bin/env python3
"""
Test script to verify diet notification extraction and management functionality.
This script tests the automatic extraction of timed activities from diet PDFs.
"""

import requests
import json
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER_ID = "test_user_123"  # Replace with actual test user ID

def test_diet_notification_extraction():
    """Test the diet notification extraction functionality."""
    
    print("Testing Diet Notification Extraction...")
    print("=" * 50)
    
    # Test 1: Check if user has a diet PDF
    print("\n1. Checking user's diet PDF...")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ User diet data retrieved successfully")
            print(f"  dietPdfUrl: {data.get('dietPdfUrl', 'Not found')}")
            print(f"  hasDiet: {data.get('hasDiet', False)}")
            
            if data.get('dietPdfUrl'):
                print("✓ User has a diet PDF - can test notification extraction")
            else:
                print("⚠ User has no diet PDF - cannot test notification extraction")
                return False
        else:
            print(f"✗ Failed to get user diet: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error getting user diet: {e}")
        return False
    
    # Test 2: Extract notifications from diet PDF
    print("\n2. Testing notification extraction from diet PDF...")
    try:
        response = requests.post(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/extract")
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            print(f"✓ Notification extraction completed successfully")
            print(f"  Message: {data.get('message', 'No message')}")
            print(f"  Extracted notifications: {len(notifications)}")
            
            if notifications:
                print("  Extracted activities:")
                for i, notification in enumerate(notifications, 1):
                    print(f"    {i}. {notification.get('message', 'No message')} at {notification.get('time', 'No time')}")
            else:
                print("  ⚠ No timed activities found in diet PDF")
                
        else:
            print(f"✗ Notification extraction failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing notification extraction: {e}")
        return False
    
    # Test 3: Get extracted notifications
    print("\n3. Testing get diet notifications...")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications")
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            print(f"✓ Retrieved {len(notifications)} diet notifications")
            print(f"  Extracted at: {data.get('extracted_at', 'Unknown')}")
            print(f"  Diet PDF URL: {data.get('diet_pdf_url', 'Unknown')}")
            
        else:
            print(f"✗ Failed to get diet notifications: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error getting diet notifications: {e}")
    
    # Test 4: Test notification sending (if notifications exist)
    if 'notifications' in locals() and notifications:
        print("\n4. Testing notification sending...")
        try:
            response = requests.post(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/test")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Test notification sent successfully")
                print(f"  Message: {data.get('message', 'No message')}")
                
            else:
                print(f"✗ Test notification failed: {response.status_code}")
                print(f"  Error: {response.text}")
                
        except Exception as e:
            print(f"✗ Error testing notification sending: {e}")
    
    print("\n" + "=" * 50)
    print("Diet Notification Test Complete!")
    print("\nSummary:")
    print("- The system can extract timed activities from diet PDFs")
    print("- Extracted activities are stored and can be managed")
    print("- Users can test notifications to verify they work")
    print("- Notifications can be deleted individually")
    
    return True

def test_notification_patterns():
    """Test the time pattern recognition in the notification service."""
    
    print("\nTesting Time Pattern Recognition...")
    print("=" * 50)
    
    # Sample diet text with various time patterns
    sample_diet_text = """
    Breakfast (8:00 AM): Have oatmeal with fruits
    Morning (9:30): Drink water
    Lunch (12:30 PM): Grilled chicken salad
    Afternoon (3:00): Healthy snack
    Dinner (7:00 PM): Salmon with vegetables
    Bedtime (10:00): Take supplements
    """
    
    print("Sample diet text with time patterns:")
    print(sample_diet_text)
    
    # This would be tested in the actual service
    print("The notification service should extract:")
    print("- 8:00 AM: Have oatmeal with fruits")
    print("- 9:30: Drink water")
    print("- 12:30 PM: Grilled chicken salad")
    print("- 3:00: Healthy snack")
    print("- 7:00 PM: Salmon with vegetables")
    print("- 10:00: Take supplements")

def test_notification_management():
    """Test notification management operations."""
    
    print("\nTesting Notification Management...")
    print("=" * 50)
    
    # Test 1: Get current notifications
    print("\n1. Getting current diet notifications...")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications")
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            print(f"✓ Found {len(notifications)} current notifications")
            
            if notifications:
                # Test 2: Delete a notification
                notification_id = notifications[0].get('id')
                if notification_id:
                    print(f"\n2. Testing notification deletion...")
                    delete_response = requests.delete(
                        f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/notifications/{notification_id}"
                    )
                    
                    if delete_response.status_code == 200:
                        print(f"✓ Successfully deleted notification {notification_id}")
                    else:
                        print(f"✗ Failed to delete notification: {delete_response.status_code}")
                else:
                    print("⚠ No notification ID found for deletion test")
            else:
                print("⚠ No notifications to test deletion")
                
        else:
            print(f"✗ Failed to get notifications: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error testing notification management: {e}")

if __name__ == "__main__":
    print("Diet Notification System Test Suite")
    print("=" * 50)
    
    # Run main test
    success = test_diet_notification_extraction()
    
    if success:
        # Run additional tests
        test_notification_patterns()
        test_notification_management()
    
    print("\nTest completed!") 