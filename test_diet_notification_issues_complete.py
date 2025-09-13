#!/usr/bin/env python3
"""
Complete Diet Notification Issues Analysis

This script analyzes the exact problems with diet notifications:
1. Automatic extraction not working
2. Wrong day notifications (Friday when diet is Mon-Thu)
3. Random notifications after 22:00
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.diet_notification_service import diet_notification_service

def test_real_diet_extraction():
    """Test extraction with real diet format that causes issues"""
    
    # Real diet text that causes issues - note it's Thursday-Friday only
    real_diet = """MR. SNJEEV TANEJA DATED-14 th AUG, 25
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
1PM- 2 pumpkin missi rotis, 1 bowl veg, 1 bowl beetroot\\ ghiya raita with soaked chia seeds
2PM- 1 glass water
3PM- 1 glass water
4PM- 1 glass water
5PM- 1 glass water
6PM- 1 fruit with flaxseeds powder
7PM- 1 glass water
8PM- 1 glass water
9PM- 1 bowl veg soup
10PM- 1 cup turmeric milk
11PM- 1 glass water"""

    print("🔍 ANALYZING DIET NOTIFICATION ISSUES")
    print("=" * 60)
    print(f"📋 Diet covers: THURSDAY-FRIDAY only (2 days)")
    print(f"❌ Problem: User getting notifications on Saturday, Sunday, Monday, Tuesday, Wednesday")
    print()
    
    # Test the extraction
    activities = diet_notification_service.extract_timed_activities(real_diet)
    
    print(f"📊 Total activities extracted: {len(activities)}")
    print()
    
    # Group activities by day
    day_groups = {}
    for activity in activities:
        day = activity.get('day', 'unknown')
        if day not in day_groups:
            day_groups[day] = []
        day_groups[day].append(activity)
    
    # Analyze day detection
    print("📅 DAY DETECTION ANALYSIS:")
    print("-" * 40)
    for day, activities_list in day_groups.items():
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day] if isinstance(day, int) and 0 <= day <= 6 else str(day)
        print(f"  {day_name} ({day}): {len(activities_list)} activities")
    print()
    
    # Create notifications and analyze selectedDays
    print("📱 NOTIFICATION CREATION ANALYSIS:")
    print("-" * 40)
    
    notifications = []
    for activity in activities:
        notification = diet_notification_service.create_notification_from_activity(activity)
        notifications.append(notification)
    
    # Group notifications by selectedDays
    days_analysis = {}
    for notification in notifications:
        selected_days = str(notification.get('selectedDays', []))
        if selected_days not in days_analysis:
            days_analysis[selected_days] = []
        days_analysis[selected_days].append(notification)
    
    for selected_days, notif_list in days_analysis.items():
        print(f"  selectedDays {selected_days}: {len(notif_list)} notifications")
        if len(notif_list) <= 3:  # Show details for small groups
            for notif in notif_list:
                print(f"    - {notif['time']}: {notif['message'][:50]}...")
    
    print()
    
    # Test diet day determination
    print("🔍 DIET DAYS DETERMINATION:")
    print("-" * 40)
    
    diet_days = diet_notification_service._determine_diet_days_from_activities(activities, real_diet)
    day_names = [['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][d] for d in diet_days]
    print(f"  Determined diet days: {diet_days} ({', '.join(day_names)})")
    
    # Check if this matches the actual diet (Thursday=3, Friday=4)
    expected_days = [3, 4]  # Thursday, Friday
    if set(diet_days) == set(expected_days):
        print("  ✅ Diet days correctly detected!")
    else:
        print(f"  ❌ Wrong diet days! Expected: {expected_days} (Thu-Fri), Got: {diet_days}")
    
    print()
    
    # Analyze problematic notifications
    print("⚠️ PROBLEMATIC NOTIFICATION ANALYSIS:")
    print("-" * 40)
    
    problematic_notifications = []
    for notification in notifications:
        selected_days = notification.get('selectedDays', [])
        
        # Check for notifications scheduled on wrong days
        if not selected_days:
            problematic_notifications.append((notification, "No selected days"))
        elif set(selected_days) != set(expected_days):
            problematic_notifications.append((notification, f"Wrong days: {selected_days} instead of {expected_days}"))
        
        # Check for late notifications (after 22:00)
        time_str = notification.get('time', '')
        if ':' in time_str:
            hour = int(time_str.split(':')[0])
            if hour >= 22:
                problematic_notifications.append((notification, f"Late notification: {time_str}"))
    
    if problematic_notifications:
        print(f"  Found {len(problematic_notifications)} problematic notifications:")
        for notif, issue in problematic_notifications:
            print(f"    - {notif['time']}: {notif['message'][:40]}... | Issue: {issue}")
    else:
        print("  ✅ No problematic notifications found!")
    
    print()
    
    # Final summary
    print("📋 ISSUE SUMMARY:")
    print("-" * 40)
    print(f"1. Diet covers: Thursday-Friday ({len(expected_days)} days)")
    print(f"2. Activities extracted: {len(activities)}")
    print(f"3. Notifications created: {len(notifications)}")
    print(f"4. Diet days detected: {diet_days}")
    print(f"5. Problematic notifications: {len(problematic_notifications)}")
    
    if set(diet_days) != set(expected_days):
        print(f"🔥 ROOT CAUSE: Diet day detection is wrong!")
        print(f"   Expected: {expected_days} (Thu-Fri)")
        print(f"   Detected: {diet_days}")
        print(f"   This causes notifications on wrong days!")
    
    return activities, notifications, diet_days

def analyze_time_extraction():
    """Analyze time extraction patterns"""
    
    test_lines = [
        "5:30 AM- 1 glass JEERA water",
        "6 AM- 5 almonds, 2 walnuts, 5 black raisins {soaked}",
        "8AM- 2 green moong dal cheela with mint chutney",
        "10AM- 1 fruit with roasted pumpkin seeds",
        "12PM- 1 bowl sprouts salad",
        "1PM- 1 bowl veg, 2 pumpkin missi roti",
        "4PM- 1 cup tea with roasted makhana namkeen",
        "6PM- 1 fruit with flaxseeds powder",
        "8PM-1 bowl veg soup",
        "10PM- 1 cup cinnamon water",
        "11PM- 1 glass water",
    ]
    
    print("⏰ TIME EXTRACTION ANALYSIS:")
    print("-" * 40)
    
    for line in test_lines:
        # Test time extraction
        time_match = None
        for pattern in diet_notification_service.time_patterns:
            import re
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                time_match = match
                break
        
        if time_match:
            groups = time_match.groups()
            print(f"  '{line}' -> {groups}")
        else:
            print(f"  '{line}' -> NO MATCH")

if __name__ == "__main__":
    print("🧪 COMPREHENSIVE DIET NOTIFICATION ISSUE ANALYSIS")
    print("=" * 80)
    
    # Test real diet extraction
    activities, notifications, diet_days = test_real_diet_extraction()
    
    print("\n" + "=" * 80)
    
    # Test time extraction
    analyze_time_extraction()
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATIONS:")
    print("-" * 40)
    print("1. Fix diet day detection to correctly identify Thu-Fri only")
    print("2. Ensure selectedDays only includes detected diet days")
    print("3. Add validation to prevent notifications after 22:00 on wrong days") 
    print("4. Test automatic extraction trigger")
    print("5. Implement simple unified local scheduling approach")
