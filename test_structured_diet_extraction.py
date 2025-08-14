#!/usr/bin/env python3
"""
Test script for structured diet notification extraction.
Tests the new extraction method with the sample diet format.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.diet_notification_service import diet_notification_service

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
    activities = diet_notification_service.extract_timed_activities(sample_diet)
    
    print(f"📊 Extracted {len(activities)} activities")
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
    print("🔍 Detailed Analysis:")
    print("-" * 30)
    
    # Test notification creation
    notifications = []
    for activity in activities:
        notification = diet_notification_service.create_notification_from_activity(activity)
        notifications.append(notification)
        print(f"  📱 Notification: {notification['time']} - {notification['message']}")
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
