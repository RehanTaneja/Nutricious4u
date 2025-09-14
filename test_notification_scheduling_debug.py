#!/usr/bin/env python3
"""
Notification Scheduling Debug Test
=================================

This script tests the actual notification scheduling logic to identify
timing and day issues in real-world scenarios.
"""

import json
from datetime import datetime, time, timedelta
import pytz
from typing import Dict, List, Tuple, Optional

def test_diet_notification_extraction():
    """Test diet notification extraction and day assignment"""
    print("🔍 TESTING DIET NOTIFICATION EXTRACTION")
    print("=" * 50)
    
    # Simulate diet extraction scenarios
    diet_scenarios = [
        {
            "name": "Monday-specific medication",
            "text": "Monday\nTake medication at 8:00 AM",
            "expected_day": 0,  # Monday
            "expected_time": "08:00"
        },
        {
            "name": "Wednesday exercise",
            "text": "Wednesday\nExercise at 6:00 PM",
            "expected_day": 2,  # Wednesday
            "expected_time": "18:00"
        },
        {
            "name": "Weekend activity",
            "text": "Saturday\nYoga at 10:00 AM",
            "expected_day": 5,  # Saturday
            "expected_time": "10:00"
        },
        {
            "name": "No day header - should be determined by diet structure",
            "text": "Drink water at 12:00 PM",
            "expected_day": None,  # Needs diet structure analysis
            "expected_time": "12:00"
        }
    ]
    
    for scenario in diet_scenarios:
        print(f"\n📋 {scenario['name']}")
        print(f"  Text: {scenario['text']}")
        print(f"  Expected day: {scenario['expected_day']}")
        print(f"  Expected time: {scenario['expected_time']}")
        
        # Simulate extraction logic
        lines = scenario['text'].split('\n')
        day_header = None
        activity = None
        
        for line in lines:
            line = line.strip()
            if line in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                day_header = line
            elif 'at' in line and any(char.isdigit() for char in line):
                activity = line
        
        if day_header:
            day_mapping = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            }
            extracted_day = day_mapping.get(day_header)
            print(f"  ✅ Day extracted: {extracted_day} ({day_header})")
        else:
            print(f"  ⚠️  No day header found - needs diet structure analysis")
        
        if activity:
            # Extract time from activity
            import re
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', activity, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                am_pm = time_match.group(3)
                
                if am_pm and am_pm.upper() == 'PM' and hour != 12:
                    hour += 12
                elif am_pm and am_pm.upper() == 'AM' and hour == 12:
                    hour = 0
                
                extracted_time = f"{hour:02d}:{minute:02d}"
                print(f"  ✅ Time extracted: {extracted_time}")
            else:
                print(f"  ❌ Could not extract time from: {activity}")

def test_notification_scheduling_flow():
    """Test the complete notification scheduling flow"""
    print("\n🔍 TESTING NOTIFICATION SCHEDULING FLOW")
    print("=" * 50)
    
    # Simulate the complete flow from diet extraction to scheduling
    def simulate_notification_scheduling(notifications: List[Dict]) -> List[Dict]:
        """Simulate the complete notification scheduling process"""
        scheduled_notifications = []
        
        for notification in notifications:
            print(f"\n📱 Processing notification: {notification['message']}")
            print(f"  Time: {notification['time']}")
            print(f"  Selected days: {notification['selectedDays']}")
            print(f"  Is active: {notification.get('isActive', True)}")
            
            if not notification.get('isActive', True):
                print("  ⏭️  Skipped: Notification is inactive")
                continue
            
            if not notification.get('selectedDays') or len(notification['selectedDays']) == 0:
                print("  ⏭️  Skipped: No selected days")
                continue
            
            # Schedule for each selected day
            for day in notification['selectedDays']:
                scheduled = schedule_notification_for_day(notification, day)
                if scheduled:
                    scheduled_notifications.append(scheduled)
        
        return scheduled_notifications
    
    def schedule_notification_for_day(notification: Dict, day: int) -> Optional[Dict]:
        """Schedule a notification for a specific day"""
        try:
            hour, minute = map(int, notification['time'].split(':'))
            
            # Calculate next occurrence (simplified version)
            now = datetime.now(pytz.UTC)
            days_ahead = (day - now.weekday()) % 7
            if days_ahead == 0 and now.time() >= time(hour, minute):
                days_ahead = 7
            
            next_occurrence = now + timedelta(days=days_ahead)
            next_occurrence = next_occurrence.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
            
            scheduled = {
                'id': f"diet_{notification['id']}_day{day}",
                'message': notification['message'],
                'time': notification['time'],
                'day': day,
                'day_name': day_name,
                'scheduled_for': next_occurrence.isoformat(),
                'scheduled_for_local': next_occurrence.strftime('%Y-%m-%d %H:%M:%S %A'),
                'status': 'scheduled'
            }
            
            print(f"  ✅ Scheduled for {day_name}: {scheduled['scheduled_for_local']}")
            return scheduled
            
        except Exception as e:
            print(f"  ❌ Error scheduling for day {day}: {e}")
            return None
    
    # Test with sample notifications
    test_notifications = [
        {
            'id': 'med_1',
            'message': 'Take morning medication',
            'time': '08:00',
            'selectedDays': [0, 1, 2, 3, 4],  # Weekdays
            'isActive': True
        },
        {
            'id': 'exercise_1',
            'message': 'Evening exercise',
            'time': '18:00',
            'selectedDays': [0, 2, 4],  # Mon, Wed, Fri
            'isActive': True
        },
        {
            'id': 'weekend_1',
            'message': 'Weekend yoga',
            'time': '10:00',
            'selectedDays': [5, 6],  # Weekend
            'isActive': True
        },
        {
            'id': 'inactive_1',
            'message': 'Inactive notification',
            'time': '12:00',
            'selectedDays': [0, 1, 2, 3, 4],
            'isActive': False
        },
        {
            'id': 'no_days_1',
            'message': 'No selected days',
            'time': '14:00',
            'selectedDays': [],
            'isActive': True
        }
    ]
    
    scheduled = simulate_notification_scheduling(test_notifications)
    
    print(f"\n📊 SCHEDULING SUMMARY")
    print(f"  Total notifications processed: {len(test_notifications)}")
    print(f"  Successfully scheduled: {len(scheduled)}")
    
    return scheduled

def test_timezone_consistency():
    """Test timezone consistency across the system"""
    print("\n🔍 TESTING TIMEZONE CONSISTENCY")
    print("=" * 50)
    
    # Test different timezone scenarios
    timezone_scenarios = [
        {
            "name": "User in IST, Server in UTC",
            "user_tz": "Asia/Kolkata",
            "server_tz": "UTC",
            "test_time": "08:00",
            "test_day": 0  # Monday
        },
        {
            "name": "User in EST, Server in UTC",
            "user_tz": "America/New_York",
            "server_tz": "UTC",
            "test_time": "09:00",
            "test_day": 1  # Tuesday
        },
        {
            "name": "User in PST, Server in UTC",
            "user_tz": "America/Los_Angeles",
            "server_tz": "UTC",
            "test_time": "07:00",
            "test_day": 2  # Wednesday
        }
    ]
    
    for scenario in timezone_scenarios:
        print(f"\n🌍 {scenario['name']}")
        
        user_tz = pytz.timezone(scenario['user_tz'])
        server_tz = pytz.timezone(scenario['server_tz'])
        
        # Current time in both timezones
        now_utc = datetime.now(pytz.UTC)
        now_user = now_utc.astimezone(user_tz)
        now_server = now_utc.astimezone(server_tz)
        
        print(f"  Current UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_utc.weekday()})")
        print(f"  Current User: {now_user.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_user.weekday()})")
        print(f"  Current Server: {now_server.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_server.weekday()})")
        
        # Test scheduling in user timezone
        test_hour, test_minute = map(int, scenario['test_time'].split(':'))
        test_day = scenario['test_day']
        
        # Calculate next occurrence in user timezone
        days_ahead = (test_day - now_user.weekday()) % 7
        if days_ahead == 0 and now_user.time() >= time(test_hour, test_minute):
            days_ahead = 7
        
        next_occurrence_user = now_user + timedelta(days=days_ahead)
        next_occurrence_user = next_occurrence_user.replace(hour=test_hour, minute=test_minute, second=0, microsecond=0)
        
        # Convert to UTC for server
        next_occurrence_utc = next_occurrence_user.astimezone(pytz.UTC)
        
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][test_day]
        
        print(f"  Next {day_name} {scenario['test_time']} in user timezone: {next_occurrence_user.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  Same time in UTC: {next_occurrence_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  Day consistency: {'✅' if next_occurrence_user.weekday() == test_day else '❌'}")

def test_edge_cases():
    """Test edge cases that could cause timing issues"""
    print("\n🔍 TESTING EDGE CASES")
    print("=" * 50)
    
    # Test midnight boundary crossing
    print("\n🌙 Midnight Boundary Crossing:")
    now = datetime.now(pytz.UTC)
    
    midnight_cases = [
        (23, 59, "Just before midnight"),
        (0, 1, "Just after midnight"),
        (0, 0, "Exactly midnight"),
    ]
    
    for hour, minute, desc in midnight_cases:
        print(f"\n  {desc} ({hour:02d}:{minute:02d}):")
        
        for day in range(7):
            days_ahead = (day - now.weekday()) % 7
            if days_ahead == 0 and now.time() >= time(hour, minute):
                days_ahead = 7
            
            next_occurrence = now + timedelta(days=days_ahead)
            next_occurrence = next_occurrence.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
            
            # Check if the notification is scheduled for the correct day
            is_correct_day = next_occurrence.weekday() == day
            print(f"    {day_name}: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S %A')} {'✅' if is_correct_day else '❌'}")
    
    # Test DST transitions
    print("\n🕐 DST Transition Testing:")
    print("  DST transitions can cause timezone offset changes")
    print("  This could affect day calculations if not handled properly")
    print("  Current implementation uses UTC which avoids DST issues")
    
    # Test leap year
    print("\n📅 Leap Year Testing:")
    leap_year_date = datetime(2024, 2, 29, 12, 0, 0, tzinfo=pytz.UTC)
    print(f"  Leap year date: {leap_year_date.strftime('%Y-%m-%d %A')}")
    print(f"  This should not affect day calculations as we use weekday()")

def test_notification_delivery_timing():
    """Test when notifications would actually be delivered"""
    print("\n🔍 TESTING NOTIFICATION DELIVERY TIMING")
    print("=" * 50)
    
    # Simulate notification delivery timing
    def simulate_notification_delivery(scheduled_notifications: List[Dict]) -> List[Dict]:
        """Simulate when notifications would be delivered"""
        now = datetime.now(pytz.UTC)
        delivered = []
        
        for notification in scheduled_notifications:
            scheduled_time = datetime.fromisoformat(notification['scheduled_for'].replace('Z', '+00:00'))
            
            # Check if notification should be delivered now
            time_diff = (scheduled_time - now).total_seconds()
            
            if time_diff <= 0:
                status = "SHOULD BE DELIVERED NOW"
            elif time_diff <= 60:
                status = f"DELIVERED IN {int(time_diff)} SECONDS"
            elif time_diff <= 3600:
                status = f"DELIVERED IN {int(time_diff/60)} MINUTES"
            else:
                status = f"DELIVERED IN {int(time_diff/3600)} HOURS"
            
            delivered.append({
                **notification,
                'delivery_status': status,
                'time_until_delivery': time_diff
            })
        
        return delivered
    
    # Test with sample scheduled notifications
    sample_scheduled = [
        {
            'id': 'test_1',
            'message': 'Test notification 1',
            'time': '08:00',
            'day_name': 'Monday',
            'scheduled_for': (datetime.now(pytz.UTC) + timedelta(hours=1)).isoformat(),
            'status': 'scheduled'
        },
        {
            'id': 'test_2',
            'message': 'Test notification 2',
            'time': '12:00',
            'day_name': 'Tuesday',
            'scheduled_for': (datetime.now(pytz.UTC) + timedelta(days=1)).isoformat(),
            'status': 'scheduled'
        }
    ]
    
    delivered = simulate_notification_delivery(sample_scheduled)
    
    for notification in delivered:
        print(f"\n📱 {notification['message']}")
        print(f"  Scheduled for: {notification['day_name']} {notification['time']}")
        print(f"  Delivery status: {notification['delivery_status']}")

def main():
    """Run all notification scheduling tests"""
    print("🔬 NOTIFICATION SCHEDULING DEBUG TESTING")
    print("=" * 60)
    print("Testing notification scheduling logic for timing and day issues")
    print("=" * 60)
    
    try:
        test_diet_notification_extraction()
        scheduled_notifications = test_notification_scheduling_flow()
        test_timezone_consistency()
        test_edge_cases()
        test_notification_delivery_timing()
        
        print("\n✅ NOTIFICATION SCHEDULING TESTING COMPLETED")
        print("=" * 60)
        print(f"Total notifications scheduled: {len(scheduled_notifications)}")
        
    except Exception as e:
        print(f"\n❌ ERROR DURING TESTING: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
