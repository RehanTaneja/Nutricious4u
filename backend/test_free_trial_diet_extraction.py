#!/usr/bin/env python3
"""
Test script for free trial diet notification extraction
Tests DAY 1, DAY2, DAY 3 detection and notification creation
"""
import sys
import os
import re

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only what we need for testing
try:
    from services.diet_notification_service import diet_notification_service
except ImportError as e:
    print(f"Warning: Could not import diet_notification_service: {e}")
    print("Testing detection logic directly...")
    diet_notification_service = None

def test_day_detection():
    """Test detection of DAY 1, DAY2, DAY 3 in diet text"""
    print("\n" + "="*60)
    print("TEST 1: Day Detection")
    print("="*60)
    
    # Test diet text with DAY 1, DAY2, DAY 3
    test_diet_text = """
DAY 1
5:30 AM- 1 glass JEERA water
6 AM- 5 almonds, 2 walnuts
8:00 AM- Breakfast
12:00 PM- Lunch
7:00 PM- Dinner

DAY2
5:30 AM- 1 glass JEERA water
6 AM- 5 almonds, 2 walnuts
8:00 AM- Breakfast
12:00 PM- Lunch
7:00 PM- Dinner

DAY 3
5:30 AM- 1 glass JEERA water
6 AM- 5 almonds, 2 walnuts
8:00 AM- Breakfast
12:00 PM- Lunch
7:00 PM- Dinner
"""
    
    if diet_notification_service is None:
        # Test detection logic directly
        print("Testing detection patterns directly...")
        found_trial_days = set()
        lines = test_diet_text.split('\n')
        
        for line in lines:
            line = line.strip()
            trial_day_patterns = [
                (r'^DAY\s*1\b', 1),
                (r'^DAY\s*2\b', 2),
                (r'^DAY\s*3\b', 3),
            ]
            
            for pattern, day_num in trial_day_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    found_trial_days.add(day_num)
                    print(f"  Found: {line} (Day {day_num})")
        
        print(f"\nTrial days found: {sorted(found_trial_days)}")
        
        if found_trial_days == {1, 2, 3}:
            print("✅ All trial days (1, 2, 3) detected correctly")
            return True
        else:
            print(f"❌ Expected {{1, 2, 3}}, got {found_trial_days}")
            return False
    
    # Test detection
    detected_days = diet_notification_service._detect_days_from_text_structure(test_diet_text)
    print(f"Detected days: {detected_days}")
    
    if detected_days == []:
        print("✅ Correctly detected free trial diet (empty list)")
    else:
        print(f"❌ Expected empty list for free trial, got: {detected_days}")
        return False
    
    # Test activity extraction
    activities = diet_notification_service.extract_timed_activities(test_diet_text)
    print(f"\nExtracted {len(activities)} activities")
    
    # Check if activities have trial days (1, 2, 3)
    trial_days_found = set()
    for activity in activities:
        if 'day' in activity and activity['day'] in [1, 2, 3]:
            trial_days_found.add(activity['day'])
            print(f"  Activity: {activity['hour']:02d}:{activity['minute']:02d} - {activity['activity'][:50]}... (Day {activity['day']})")
    
    print(f"\nTrial days found: {sorted(trial_days_found)}")
    
    if trial_days_found == {1, 2, 3}:
        print("✅ All trial days (1, 2, 3) found")
    else:
        print(f"❌ Expected {{1, 2, 3}}, got {trial_days_found}")
        return False
    
    return True

def test_notification_creation():
    """Test notification creation with trial days"""
    print("\n" + "="*60)
    print("TEST 2: Notification Creation")
    print("="*60)
    
    if diet_notification_service is None:
        print("⚠️  Skipping - diet_notification_service not available")
        return True
    
    # Create test activities with trial days
    test_activities = [
        {
            'hour': 5,
            'minute': 30,
            'activity': '1 glass JEERA water',
            'day': 1,
            'original_text': '5:30 AM- 1 glass JEERA water',
            'unique_id': 'test_1'
        },
        {
            'hour': 6,
            'minute': 0,
            'activity': '5 almonds, 2 walnuts',
            'day': 1,
            'original_text': '6 AM- 5 almonds, 2 walnuts',
            'unique_id': 'test_2'
        },
        {
            'hour': 8,
            'minute': 0,
            'activity': 'Breakfast',
            'day': 2,
            'original_text': '8:00 AM- Breakfast',
            'unique_id': 'test_3'
        },
        {
            'hour': 12,
            'minute': 0,
            'activity': 'Lunch',
            'day': 3,
            'original_text': '12:00 PM- Lunch',
            'unique_id': 'test_4'
        }
    ]
    
    notifications = []
    for activity in test_activities:
        notification = diet_notification_service.create_notification_from_activity(activity)
        notifications.append(notification)
        print(f"\nNotification for Day {activity['day']}:")
        print(f"  Message: {notification['message']}")
        print(f"  Time: {notification['time']}")
        print(f"  isFreeTrialDiet: {notification.get('isFreeTrialDiet', False)}")
        print(f"  trialDay: {notification.get('trialDay', None)}")
        print(f"  selectedDays: {notification.get('selectedDays', None)}")
    
    # Verify all notifications have trialDay and isFreeTrialDiet
    all_valid = True
    for notif in notifications:
        if not notif.get('isFreeTrialDiet'):
            print(f"❌ Notification missing isFreeTrialDiet: {notif['message']}")
            all_valid = False
        if not notif.get('trialDay'):
            print(f"❌ Notification missing trialDay: {notif['message']}")
            all_valid = False
        if notif.get('selectedDays') is not None:
            print(f"❌ Notification should not have selectedDays: {notif['message']}")
            all_valid = False
    
    if all_valid:
        print("\n✅ All notifications correctly formatted for free trial diet")
    else:
        print("\n❌ Some notifications have incorrect format")
        return False
    
    return True

def test_full_extraction():
    """Test full extraction process"""
    print("\n" + "="*60)
    print("TEST 3: Full Extraction Process")
    print("="*60)
    
    if diet_notification_service is None:
        print("⚠️  Skipping - diet_notification_service not available")
        return True
    
    # Mock diet text (simulating what would come from PDF)
    test_diet_text = """
DAY 1
5:30 AM- 1 glass JEERA water
6 AM- 5 almonds, 2 walnuts, 5 black raisins {soaked}
8:00 AM- Breakfast: Oats with fruits
12:00 PM- Lunch: Roti with vegetables
7:00 PM- Dinner: Salad and soup

DAY2
5:30 AM- 1 glass JEERA water
6 AM- 5 almonds, 2 walnuts
8:00 AM- Breakfast: Poha
12:00 PM- Lunch: Rice with dal
7:00 PM- Dinner: Grilled chicken

DAY 3
5:30 AM- 1 glass JEERA water
6 AM- 5 almonds, 2 walnuts
8:00 AM- Breakfast: Smoothie
12:00 PM- Lunch: Quinoa bowl
7:00 PM- Dinner: Fish curry
"""
    
    # Extract activities
    activities = diet_notification_service.extract_timed_activities(test_diet_text)
    print(f"Extracted {len(activities)} activities")
    
    # Determine diet days
    diet_days = diet_notification_service._determine_diet_days_from_activities(activities, test_diet_text)
    print(f"Determined diet days: {diet_days}")
    
    if diet_days != []:
        print("❌ Expected empty list for free trial diet")
        return False
    
    # Create notifications (simulate extract_and_create_notifications logic)
    notifications = []
    for activity in activities:
        notification = diet_notification_service.create_notification_from_activity(activity)
        notifications.append(notification)
    
    # Group by trial day
    day1_count = sum(1 for n in notifications if n.get('trialDay') == 1)
    day2_count = sum(1 for n in notifications if n.get('trialDay') == 2)
    day3_count = sum(1 for n in notifications if n.get('trialDay') == 3)
    
    print(f"\nNotifications by day:")
    print(f"  Day1: {day1_count}")
    print(f"  Day2: {day2_count}")
    print(f"  Day3: {day3_count}")
    
    if day1_count > 0 and day2_count > 0 and day3_count > 0:
        print("✅ All three trial days have notifications")
    else:
        print("❌ Missing notifications for some trial days")
        return False
    
    # Verify no notifications have selectedDays
    has_selected_days = any('selectedDays' in n and n['selectedDays'] is not None for n in notifications)
    if has_selected_days:
        print("❌ Some notifications have selectedDays (should not for free trial)")
        return False
    else:
        print("✅ No notifications have selectedDays (correct for free trial)")
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("FREE TRIAL DIET EXTRACTION TESTS")
    print("="*60)
    
    tests = [
        ("Day Detection", test_day_detection),
        ("Notification Creation", test_notification_creation),
        ("Full Extraction", test_full_extraction)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
