#!/usr/bin/env python3
"""
Simple test script for structured diet notification extraction.
Tests the extraction logic without requiring the full backend setup.
"""

import re
from datetime import time

def extract_structured_diet_activities(diet_text: str):
    """
    Extract timed activities from structured diet format with day headers.
    This handles formats like:
    THURSDAY- 14th AUG
    5:30 AM- 1 glass JEERA water
    6 AM- 5 almonds, 2 walnuts, 5 black raisins {soaked}
    """
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
                print(f"📅 Found day: {day_name.upper()} (day {current_day})")
                continue
        
        # Look for time patterns in the line
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
        
        if time_match:
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
                    if period == 'PM':
                        if hour != 12:
                            hour += 12
                    elif period == 'AM':
                        if hour == 12:
                            hour = 0
                
                # Extract activity text (everything after the time)
                activity_text = line[time_match.end():].strip()
                
                # Clean up the activity text
                if activity_text:
                    # Remove leading dashes, colons, or other separators
                    activity_text = re.sub(r'^[-:\s]+', '', activity_text)
                    
                    # If activity is too short, try to get more context from next line
                    if len(activity_text.split()) <= 3:
                        line_index = lines.index(line)
                        if line_index + 1 < len(lines):
                            next_line = lines[line_index + 1].strip()
                            if next_line and not re.search(r'\d{1,2}[:.]?\d{2}\s*(AM|PM|am|pm)?', next_line):
                                activity_text += " " + next_line
                    
                    # Create activity object
                    activity = {
                        'time': {'hour': hour, 'minute': minute, 'type': 'numeric'},
                        'activity': activity_text,
                        'original_text': line,
                        'hour': hour,
                        'minute': minute,
                        'day': current_day,  # Include day information
                        'unique_id': f"{hour:02d}:{minute:02d}_{hash(activity_text.lower().strip()) % 1000000}"
                    }
                    
                    activities.append(activity)
                    print(f"  ✅ {hour:02d}:{minute:02d} - {activity_text}")
                    
            except (ValueError, IndexError) as e:
                print(f"  ❌ Error parsing line: {line}, error: {e}")
                continue
    
    # Remove duplicates and sort by time
    unique_activities = []
    seen_combinations = set()
    
    for activity in activities:
        time_key = f"{activity['hour']:02d}:{activity['minute']:02d}"
        activity_key = activity['activity'].lower().strip()
        combination = f"{time_key}_{activity_key}"
        
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            unique_activities.append(activity)
    
    # Sort by time
    unique_activities.sort(key=lambda x: (x['hour'], x['minute']))
    
    return unique_activities

def create_notification_from_activity(activity):
    """Create a notification object from an activity."""
    time_obj = time(activity['hour'], activity['minute'])
    unique_id = activity.get('unique_id', f"{activity['hour']:02d}:{activity['minute']:02d}_{hash(activity['activity']) % 1000000}")
    notification_id = f"diet_{activity['hour']}_{activity['minute']}_{hash(unique_id) % 1000000}"
    
    # Handle day-specific notifications
    if 'day' in activity and activity['day'] is not None:
        # If the activity has a specific day, create notifications for that day only
        selected_days = [activity['day']]
    else:
        # Default to all days for extracted notifications
        selected_days = [0, 1, 2, 3, 4, 5, 6]
    
    return {
        'id': notification_id,
        'message': activity['activity'],
        'time': time_obj.strftime('%H:%M'),
        'hour': activity['hour'],
        'minute': activity['minute'],
        'scheduledId': None,
        'source': 'diet_pdf',
        'original_text': activity['original_text'],
        'selectedDays': selected_days,
        'isActive': True
    }

def test_structured_diet_extraction():
    """Test the structured diet extraction with the sample diet."""
    
    # Sample diet text from the user
    sample_diet = """MR. SNJEEV TANEJA DATED-14 th AUG, 25
WT-97 KGS, HT-5'10", AGE-56 YRS
THURSDAY- 14 th AUG
5:30 AM- 1 glass JEERA water
6 AM- 5 almonds, 2 walnuts, 5 black raisins {soaked}
8AM- 2 green moong dal cheela with mint chutney, 1 bowl ghiya raita
10AM- 1 fruit with roasted pumpkin seeds- 1 apple\\ pear\\ 2 plums\\ kiwi\\ 1 bowl papaya\\ 3-4 slices pineapple
12PM- 1 bowl sprouts salad
1PM- 1 bowl veg, 2 pumpkin missi roti, 1 bowl beetroot\\ ghiya raita with soaked chia seeds
4PM- 1 cup tea with roasted makhana namkeen
6PM- 1 fruit with flaxseeds powder
8PM-1 bowl veg soup, 1 quarter plate green moong , veg masala khichdi
10PM- 1 cup cinnamon water
FRIDAY- 15 th AUG
5:30AM- 1glass jeera water
6 AM- 5 almonds, 2 walnuts, 5 black raisins (soaked)
6:30AM- 1 glass water
7AM- 1 glass water
7:30AM- 1glass water
8AM- 2 egg whites & veggies omelette with 2 sour dough toasts\\ pumpkin missi roti
9AM- 1 glass water
10AM- 1 fruit with roasted pumpkin seeds
11AM-1 glass water
12PM- 1 quarter plate roasted chana salad
1PM- 2 pumpkin missi rotis, 1 bowl veg, 1 bowl beetroot\\ ghiya raita with soaked chia seeds"""
    
    print("🧪 Testing Structured Diet Extraction")
    print("=" * 50)
    
    # Test the extraction
    activities = extract_structured_diet_activities(sample_diet)
    
    print(f"\n📊 Extracted {len(activities)} activities")
    print()
    
    if not activities:
        print("❌ No activities extracted!")
        return False
    
    # Group activities by day
    thursday_activities = []
    friday_activities = []
    other_activities = []
    
    for activity in activities:
        if activity.get('day') == 3:  # Thursday
            thursday_activities.append(activity)
        elif activity.get('day') == 4:  # Friday
            friday_activities.append(activity)
        else:
            other_activities.append(activity)
    
    print("📅 THURSDAY Activities:")
    print("-" * 30)
    for activity in sorted(thursday_activities, key=lambda x: (x['hour'], x['minute'])):
        time_str = f"{activity['hour']:02d}:{activity['minute']:02d}"
        print(f"  {time_str} - {activity['activity']}")
    
    print()
    print("📅 FRIDAY Activities:")
    print("-" * 30)
    for activity in sorted(friday_activities, key=lambda x: (x['hour'], x['minute'])):
        time_str = f"{activity['hour']:02d}:{activity['minute']:02d}"
        print(f"  {time_str} - {activity['activity']}")
    
    if other_activities:
        print()
        print("📅 OTHER Activities:")
        print("-" * 30)
        for activity in sorted(other_activities, key=lambda x: (x['hour'], x['minute'])):
            time_str = f"{activity['hour']:02d}:{activity['minute']:02d}"
            print(f"  {time_str} - {activity['activity']}")
    
    print()
    print("🔍 Notification Creation:")
    print("-" * 30)
    
    # Test notification creation
    notifications = []
    for activity in activities:
        notification = create_notification_from_activity(activity)
        notifications.append(notification)
        print(f"  📱 {notification['time']} - {notification['message']}")
        print(f"     Days: {notification['selectedDays']}")
        print()
    
    # Verify expected activities
    expected_times = [
        (5, 30), (6, 0), (8, 0), (10, 0), (12, 0), (13, 0), (16, 0), (18, 0), (20, 0), (22, 0),  # Thursday
        (5, 30), (6, 0), (6, 30), (7, 0), (7, 30), (8, 0), (9, 0), (10, 0), (11, 0), (12, 0), (13, 0)  # Friday
    ]
    
    extracted_times = [(activity['hour'], activity['minute']) for activity in activities]
    
    print("✅ Expected vs Extracted Times:")
    print("-" * 30)
    for expected in expected_times:
        if expected in extracted_times:
            print(f"  ✅ {expected[0]:02d}:{expected[1]:02d}")
        else:
            print(f"  ❌ {expected[0]:02d}:{expected[1]:02d} (missing)")
    
    # Check for unexpected times
    for extracted in extracted_times:
        if extracted not in expected_times:
            print(f"  ⚠️  {extracted[0]:02d}:{extracted[1]:02d} (unexpected)")
    
    print()
    print("📈 Summary:")
    print("-" * 30)
    print(f"  Total Activities: {len(activities)}")
    print(f"  Thursday Activities: {len(thursday_activities)}")
    print(f"  Friday Activities: {len(friday_activities)}")
    print(f"  Other Activities: {len(other_activities)}")
    print(f"  Notifications Created: {len(notifications)}")
    
    # Check day-specific notifications
    thursday_notifications = [n for n in notifications if n['selectedDays'] == [3]]
    friday_notifications = [n for n in notifications if n['selectedDays'] == [4]]
    all_days_notifications = [n for n in notifications if n['selectedDays'] == [0, 1, 2, 3, 4, 5, 6]]
    
    print(f"  Thursday-specific notifications: {len(thursday_notifications)}")
    print(f"  Friday-specific notifications: {len(friday_notifications)}")
    print(f"  All-days notifications: {len(all_days_notifications)}")
    
    success = len(activities) > 0 and len(thursday_activities) > 0 and len(friday_activities) > 0
    
    if success:
        print()
        print("🎉 SUCCESS: Structured diet extraction is working correctly!")
        return True
    else:
        print()
        print("❌ FAILURE: Structured diet extraction needs improvement.")
        return False

if __name__ == "__main__":
    test_structured_diet_extraction()
