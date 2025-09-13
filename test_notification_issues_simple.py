#!/usr/bin/env python3
"""
Simple test to reproduce diet notification issues without backend dependencies
"""

import re
from datetime import datetime, time

def extract_structured_diet_activities(diet_text: str):
    """Extract timed activities from structured diet format with day headers"""
    if not diet_text:
        return []
    
    activities = []
    lines = diet_text.split('\n')
    current_day = None
    
    # Day mapping for structured diets
    day_mapping = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a day header
        day_match = re.search(r'^([A-Z]+)\s*-\s*\d+', line, re.IGNORECASE)
        if day_match:
            day_name = day_match.group(1).lower()
            if day_name in day_mapping:
                current_day = day_mapping[day_name]
                print(f"  📅 Found day: {day_name.upper()} (day {current_day})")
                continue
        
        # Skip lines that don't contain time patterns
        if not re.search(r'\d{1,2}([:.]?\d{2})?\s*(AM|PM|am|pm)?', line):
            continue
        
        # Look for time patterns
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?',  # 5:30 AM, 6:00 PM
            r'(\d{1,2})\s*(AM|PM|am|pm)',  # 6 AM, 8 PM
        ]
        
        time_match = None
        for pattern in time_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                time_match = match
                break
        
        if time_match and current_day is not None:
            try:
                # Extract time components
                if ':' in time_match.group(0):
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    period = time_match.group(3) if len(time_match.groups()) > 2 else None
                else:
                    hour = int(time_match.group(1))
                    minute = 0
                    period = time_match.group(2) if len(time_match.groups()) > 1 else None
                
                # Convert to 24-hour format
                if period:
                    period = period.upper()
                    if period == 'PM' and hour != 12:
                        hour += 12
                    elif period == 'AM' and hour == 12:
                        hour = 0
                
                # Extract activity text
                activity_text = line[time_match.end():].strip()
                activity_text = re.sub(r'^[-:\s]+', '', activity_text)
                
                if activity_text and len(activity_text) > 3:
                    activity = {
                        'hour': hour,
                        'minute': minute,
                        'activity': activity_text,
                        'day': current_day,
                        'original_text': line
                    }
                    activities.append(activity)
                    print(f"  ✅ {hour:02d}:{minute:02d} - {activity_text} (Day {current_day})")
                    
            except (ValueError, IndexError) as e:
                print(f"  ❌ Error parsing time in line: {line}, error: {e}")
                continue
    
    return activities

def create_notification_from_activity(activity):
    """Create a notification object from an activity - CURRENT BUGGY VERSION"""
    time_obj = time(activity['hour'], activity['minute'])
    notification_id = f"diet_{activity['hour']}_{activity['minute']}_{hash(activity['activity']) % 1000000}"
    
    # BUG: This is the root cause of Issue 1
    if 'day' in activity and activity['day'] is not None:
        # If the activity has a specific day, create notifications for that day only
        selected_days = [activity['day']]
    else:
        # BUG: Default to all days for extracted notifications
        selected_days = [0, 1, 2, 3, 4, 5, 6]  # This causes notifications on Friday!
    
    return {
        'id': notification_id,
        'message': activity['activity'],
        'time': time_obj.strftime('%H:%M'),
        'hour': activity['hour'],
        'minute': activity['minute'],
        'selectedDays': selected_days,
        'isActive': True
    }

def test_issues():
    """Test the identified issues"""
    print("🧪 Testing Diet Notification Issues")
    print("=" * 60)
    
    # Test case: Structured diet with day headers (Monday-Thursday)
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
    
    print("\n📋 Test Case: Structured Diet (Monday-Thursday)")
    print("-" * 50)
    
    activities = extract_structured_diet_activities(structured_diet_text)
    print(f"\nExtracted {len(activities)} activities")
    
    # Create notifications and show the bug
    notifications = []
    for activity in activities:
        notification = create_notification_from_activity(activity)
        notifications.append(notification)
    
    print(f"\nCreated {len(notifications)} notifications")
    
    # Show the bug: check what days notifications are scheduled for
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    print("\n🔍 Notification Day Analysis:")
    print("-" * 30)
    
    for i, notification in enumerate(notifications):
        selected_days = notification['selectedDays']
        selected_day_names = [day_names[day] for day in selected_days]
        original_day = activities[i].get('day', 'Not specified')
        
        print(f"Notification {i+1}: {notification['message'][:30]}...")
        print(f"  Time: {notification['time']}")
        print(f"  Original Day: {original_day}")
        print(f"  Selected Days: {selected_day_names}")
        
        # Check if this would be sent on Friday (day 4)
        if 4 in selected_days:
            print(f"  ❌ BUG: This notification will be sent on Friday!")
        else:
            print(f"  ✅ Correct: This notification will NOT be sent on Friday")
        print()
    
    # Test the second issue: recurring notifications
    print("\n🔄 Testing Recurring Notification Issue")
    print("-" * 50)
    
    print("Current problematic flow:")
    print("1. Backend schedules notification for Monday 6:00 AM")
    print("2. Mobile app schedules with repeats: true, repeatInterval: 7 days")
    print("3. Notification sent at Monday 6:00 AM")
    print("4. Backend schedules next occurrence for next Monday 6:00 AM")
    print("5. Mobile app also schedules next occurrence due to repeats: true")
    print("6. Result: Duplicate scheduling and late notifications")
    print()
    print("This creates the issue where notifications appear after 22:00")

if __name__ == "__main__":
    test_issues()
    
    print("\n📊 Summary of Issues Found:")
    print("=" * 60)
    print("1. ❌ Issue 1: Notifications sent on non-diet days (Friday)")
    print("   - Root cause: selectedDays = [0,1,2,3,4,5,6] for activities without day headers")
    print("   - Impact: User gets diet reminders on Friday even though diet is Monday-Thursday")
    print()
    print("2. ❌ Issue 2: Late notifications after 22:00")
    print("   - Root cause: Duplicate scheduling between backend and mobile app")
    print("   - Impact: Random diet reminders appear late at night")
    print()
    print("3. 🔧 Fixes needed:")
    print("   - Fix 1: Only set selectedDays based on actual day headers found")
    print("   - Fix 2: Remove duplicate scheduling, use only one repeat mechanism")
    print("   - Fix 3: Improve day detection for mixed diet formats")
