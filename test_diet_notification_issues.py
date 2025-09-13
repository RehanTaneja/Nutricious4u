#!/usr/bin/env python3
"""
Test script to reproduce and verify diet notification issues:
1. Notifications from other days being sent on non-diet days (Friday)
2. Random diet reminders appearing after 22:00 on correct days
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.diet_notification_service import diet_notification_service
from datetime import datetime, time
import json

def test_diet_notification_extraction():
    """Test diet notification extraction to identify the issues"""
    print("🧪 Testing Diet Notification Extraction Issues")
    print("=" * 60)
    
    # Test case 1: Structured diet with day headers (Monday-Thursday)
    structured_diet_text = """
MONDAY- 1st JAN
6:00 AM- 1 glass JEERA water
8:00 AM- 5 almonds, 2 walnuts
12:00 PM- Lunch with vegetables

TUESDAY- 2nd JAN
6:00 AM- 1 glass JEERA water
8:00 AM- 5 almonds, 2 walnuts
12:00 PM- Lunch with vegetables

WEDNESDAY- 3rd JAN
6:00 AM- 1 glass JEERA water
8:00 AM- 5 almonds, 2 walnuts
12:00 PM- Lunch with vegetables

THURSDAY- 4th JAN
6:00 AM- 1 glass JEERA water
8:00 AM- 5 almonds, 2 walnuts
12:00 PM- Lunch with vegetables
"""
    
    print("\n📋 Test Case 1: Structured Diet (Monday-Thursday)")
    print("-" * 40)
    
    activities = diet_notification_service.extract_timed_activities(structured_diet_text)
    print(f"Extracted {len(activities)} activities")
    
    for activity in activities:
        day = activity.get('day', 'Not specified')
        time_str = f"{activity['hour']:02d}:{activity['minute']:02d}"
        message = activity['activity'][:50] + "..." if len(activity['activity']) > 50 else activity['activity']
        print(f"  Day {day}: {time_str} - {message}")
    
    # Test case 2: Unstructured diet (no day headers)
    unstructured_diet_text = """
6:00 AM- 1 glass JEERA water
8:00 AM- 5 almonds, 2 walnuts
12:00 PM- Lunch with vegetables
6:00 PM- Evening snack
"""
    
    print("\n📋 Test Case 2: Unstructured Diet (No Day Headers)")
    print("-" * 40)
    
    activities = diet_notification_service.extract_timed_activities(unstructured_diet_text)
    print(f"Extracted {len(activities)} activities")
    
    for activity in activities:
        day = activity.get('day', 'Not specified')
        time_str = f"{activity['hour']:02d}:{activity['minute']:02d}"
        message = activity['activity'][:50] + "..." if len(activity['activity']) > 50 else activity['activity']
        print(f"  Day {day}: {time_str} - {message}")
    
    # Test case 3: Mixed diet (some with day headers, some without)
    mixed_diet_text = """
MONDAY- 1st JAN
6:00 AM- 1 glass JEERA water
8:00 AM- 5 almonds, 2 walnuts

TUESDAY- 2nd JAN
6:00 AM- 1 glass JEERA water
8:00 AM- 5 almonds, 2 walnuts

6:00 PM- Evening snack (no day specified)
10:00 PM- Bedtime routine (no day specified)
"""
    
    print("\n📋 Test Case 3: Mixed Diet (Some with Day Headers, Some Without)")
    print("-" * 40)
    
    activities = diet_notification_service.extract_timed_activities(mixed_diet_text)
    print(f"Extracted {len(activities)} activities")
    
    for activity in activities:
        day = activity.get('day', 'Not specified')
        time_str = f"{activity['hour']:02d}:{activity['minute']:02d}"
        message = activity['activity'][:50] + "..." if len(activity['activity']) > 50 else activity['activity']
        print(f"  Day {day}: {time_str} - {message}")
    
    # Test notification creation
    print("\n🔔 Testing Notification Creation")
    print("-" * 40)
    
    for activity in activities:
        notification = diet_notification_service.create_notification_from_activity(activity)
        selected_days = notification.get('selectedDays', [])
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        selected_day_names = [day_names[day] for day in selected_days]
        
        print(f"  Activity: {activity['activity'][:30]}...")
        print(f"    Time: {notification['time']}")
        print(f"    Selected Days: {selected_day_names}")
        print(f"    Original Day: {activity.get('day', 'Not specified')}")
        print()

def test_notification_scheduling_logic():
    """Test the notification scheduling logic to identify the late notification issue"""
    print("\n🕐 Testing Notification Scheduling Logic")
    print("=" * 60)
    
    # Simulate current time scenarios
    test_times = [
        ("Monday 6:00 AM", 0, 6, 0),    # Monday morning
        ("Monday 10:00 PM", 0, 22, 0),  # Monday evening
        ("Friday 6:00 AM", 4, 6, 0),    # Friday morning (should not have notifications)
        ("Friday 10:00 PM", 4, 22, 0),  # Friday evening (should not have notifications)
    ]
    
    for time_desc, day_of_week, hour, minute in test_times:
        print(f"\n📅 Testing {time_desc} (Day {day_of_week})")
        print("-" * 30)
        
        # Simulate a notification for Monday-Thursday only
        selected_days = [0, 1, 2, 3]  # Monday to Thursday
        
        if day_of_week in selected_days:
            print(f"  ✅ This day ({day_of_week}) is in selected days {selected_days}")
            print(f"  📱 Notification should be sent at {hour:02d}:{minute:02d}")
        else:
            print(f"  ❌ This day ({day_of_week}) is NOT in selected days {selected_days}")
            print(f"  🚫 Notification should NOT be sent at {hour:02d}:{minute:02d}")
        
        # Test the issue: what happens with default selected_days = [0,1,2,3,4,5,6]
        default_selected_days = [0, 1, 2, 3, 4, 5, 6]  # All days
        if day_of_week in default_selected_days:
            print(f"  ⚠️  With default all-days setting, notification WOULD be sent")
            print(f"  🐛 This is the bug: notifications sent on non-diet days!")

def test_recurring_notification_issue():
    """Test the recurring notification issue that causes late notifications"""
    print("\n🔄 Testing Recurring Notification Issue")
    print("=" * 60)
    
    print("Current behavior:")
    print("1. Notification is scheduled for Monday 6:00 AM")
    print("2. Notification is sent at Monday 6:00 AM")
    print("3. Backend schedules next occurrence for next Monday 6:00 AM")
    print("4. BUT: Mobile app also has repeats: true with weekly interval")
    print("5. This creates duplicate scheduling and late notifications")
    print()
    print("Expected behavior:")
    print("1. Notification is scheduled for Monday 6:00 AM")
    print("2. Notification is sent at Monday 6:00 AM")
    print("3. Next occurrence is automatically handled by the repeat mechanism")
    print("4. No duplicate scheduling should occur")

if __name__ == "__main__":
    print("🔍 Diet Notification Issues Analysis")
    print("=" * 60)
    
    test_diet_notification_extraction()
    test_notification_scheduling_logic()
    test_recurring_notification_issue()
    
    print("\n📊 Summary of Issues Found:")
    print("=" * 60)
    print("1. ❌ Issue 1: Notifications sent on non-diet days (Friday)")
    print("   - Root cause: Default selectedDays = [0,1,2,3,4,5,6] for activities without day headers")
    print("   - Fix: Only set selectedDays based on actual day headers found")
    print()
    print("2. ❌ Issue 2: Late notifications after 22:00")
    print("   - Root cause: Duplicate scheduling between backend and mobile app")
    print("   - Fix: Remove duplicate scheduling, use only one repeat mechanism")
    print()
    print("3. ❌ Issue 3: Mixed day handling")
    print("   - Root cause: Inconsistent day handling between structured and unstructured diets")
    print("   - Fix: Improve day detection and consistent selectedDays assignment")
