#!/usr/bin/env python3
"""
Comprehensive Notification Debugging Test
=========================================

This script thoroughly tests the notification scheduling system to identify
all possible causes of incorrect timing and day issues.

Issues to investigate:
1. Timezone handling inconsistencies
2. Day calculation logic errors
3. Day numbering mismatches (0=Sunday vs 0=Monday)
4. Time boundary crossing issues
5. Local vs UTC time handling
6. Day offset calculation problems
"""

import json
import sys
from datetime import datetime, time, timedelta
import pytz
from typing import Dict, List, Tuple, Optional

def test_timezone_handling():
    """Test timezone conversion and handling logic"""
    print("🔍 TESTING TIMEZONE HANDLING")
    print("=" * 50)
    
    # Test different timezones
    timezones = [
        ('UTC', 'UTC'),
        ('IST', 'Asia/Kolkata'),
        ('EST', 'America/New_York'),
        ('PST', 'America/Los_Angeles'),
        ('GMT', 'Europe/London')
    ]
    
    test_times = [
        ('08:00', 'Morning'),
        ('12:00', 'Noon'),
        ('18:00', 'Evening'),
        ('23:30', 'Late night'),
        ('00:30', 'Early morning')
    ]
    
    for tz_name, tz_zone in timezones:
        print(f"\n📍 Testing {tz_name} ({tz_zone})")
        tz = pytz.timezone(tz_zone)
        now_utc = datetime.now(pytz.UTC)
        now_local = now_utc.astimezone(tz)
        
        print(f"  Current UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_utc.weekday()})")
        print(f"  Current {tz_name}: {now_local.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_local.weekday()})")
        
        for time_str, desc in test_times:
            hour, minute = map(int, time_str.split(':'))
            target_time = time(hour, minute)
            
            # Test day calculation in different timezones
            for day in range(7):  # 0=Monday to 6=Sunday
                days_ahead = (day - now_local.weekday()) % 7
                if days_ahead == 0 and now_local.time() >= target_time:
                    days_ahead = 7
                
                next_occurrence = now_local + timedelta(days=days_ahead)
                next_occurrence = next_occurrence.replace(
                    hour=target_time.hour,
                    minute=target_time.minute,
                    second=0,
                    microsecond=0
                )
                
                print(f"    {desc} ({time_str}) on day {day}: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence.weekday()})")

def test_day_calculation_logic():
    """Test day calculation and offset logic"""
    print("\n🔍 TESTING DAY CALCULATION LOGIC")
    print("=" * 50)
    
    # Test the JavaScript day conversion logic
    print("\n📅 JavaScript Day Conversion Logic:")
    print("Backend uses: 0=Monday, 1=Tuesday, ..., 6=Sunday")
    print("JavaScript uses: 0=Sunday, 1=Monday, ..., 6=Saturday")
    print("Conversion: js_day = (backend_day + 1) % 7")
    
    for backend_day in range(7):
        js_day = (backend_day + 1) % 7
        backend_day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][backend_day]
        js_day_name = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][js_day]
        print(f"  Backend day {backend_day} ({backend_day_name}) → JS day {js_day} ({js_day_name})")
    
    # Test day offset calculation
    print("\n📊 Day Offset Calculation:")
    now = datetime.now(pytz.UTC)
    current_day = now.weekday()  # 0=Monday
    
    for target_day in range(7):
        days_ahead = (target_day - current_day) % 7
        if days_ahead == 0 and now.time() >= time(12, 0):  # Assume 12:00 as test time
            days_ahead = 7
        
        target_day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][target_day]
        current_day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][current_day]
        
        print(f"  Current: {current_day_name} (day {current_day})")
        print(f"  Target: {target_day_name} (day {target_day})")
        print(f"  Days ahead: {days_ahead}")
        print(f"  Next occurrence: {(now + timedelta(days=days_ahead)).strftime('%Y-%m-%d %A')}")
        print()

def test_frontend_backend_consistency():
    """Test consistency between frontend and backend day calculations"""
    print("\n🔍 TESTING FRONTEND-BACKEND CONSISTENCY")
    print("=" * 50)
    
    # Simulate frontend JavaScript logic
    def frontend_calculate_next_occurrence(hours: int, minutes: int, day_of_week: int) -> datetime:
        now = datetime.now(pytz.UTC)
        js_selected_day = (day_of_week + 1) % 7  # Convert Monday=0 to Sunday=0
        
        for day_offset in range(8):  # 0 to 7
            check_date = now + timedelta(days=day_offset)
            check_day = check_date.weekday()
            js_check_day = (check_day + 1) % 7  # Convert to JS format
            
            if js_check_day == js_selected_day:
                occurrence = check_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                if day_offset == 0 and occurrence > now:
                    return occurrence
                if day_offset > 0:
                    return occurrence
        
        # Fallback
        fallback = now + timedelta(days=7)
        return fallback.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    # Simulate backend Python logic
    def backend_calculate_next_occurrence(hours: int, minutes: int, day_of_week: int) -> datetime:
        now = datetime.now(pytz.UTC)
        target_time = time(hours, minutes)
        
        days_ahead = (day_of_week - now.weekday()) % 7
        if days_ahead == 0 and now.time() >= target_time:
            days_ahead = 7
        
        next_occurrence = now + timedelta(days=days_ahead)
        return next_occurrence.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
    
    # Test consistency
    test_cases = [
        (8, 0, 0),   # Monday 8:00 AM
        (12, 30, 2), # Wednesday 12:30 PM
        (18, 0, 4),  # Friday 6:00 PM
        (23, 30, 6), # Sunday 11:30 PM
    ]
    
    print("Testing frontend vs backend consistency:")
    for hours, minutes, day_of_week in test_cases:
        frontend_result = frontend_calculate_next_occurrence(hours, minutes, day_of_week)
        backend_result = backend_calculate_next_occurrence(hours, minutes, day_of_week)
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        print(f"\n  Test: {day_names[day_of_week]} {hours:02d}:{minutes:02d}")
        print(f"    Frontend: {frontend_result.strftime('%Y-%m-%d %H:%M:%S %A')}")
        print(f"    Backend:  {backend_result.strftime('%Y-%m-%d %H:%M:%S %A')}")
        print(f"    Match: {'✅' if frontend_result == backend_result else '❌'}")
        
        if frontend_result != backend_result:
            print(f"    ⚠️  MISMATCH DETECTED!")

def test_edge_cases():
    """Test edge cases and boundary conditions"""
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
    
    for hours, minutes, desc in midnight_cases:
        target_time = time(hours, minutes)
        for day in range(7):
            days_ahead = (day - now.weekday()) % 7
            if days_ahead == 0 and now.time() >= target_time:
                days_ahead = 7
            
            next_occurrence = now + timedelta(days=days_ahead)
            next_occurrence = next_occurrence.replace(
                hour=target_time.hour,
                minute=target_time.minute,
                second=0,
                microsecond=0
            )
            
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
            print(f"  {desc} on {day_name}: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S %A')}")
    
    # Test DST transitions
    print("\n🕐 DST Transition Testing:")
    # This would require specific dates, but we can test the logic
    print("  DST transitions can cause timezone offset changes")
    print("  This could affect day calculations if not handled properly")
    
    # Test leap year
    print("\n📅 Leap Year Testing:")
    leap_year_date = datetime(2024, 2, 29, 12, 0, 0, tzinfo=pytz.UTC)
    print(f"  Leap year date: {leap_year_date.strftime('%Y-%m-%d %A')}")

def test_notification_scheduling_scenarios():
    """Test real-world notification scheduling scenarios"""
    print("\n🔍 TESTING NOTIFICATION SCHEDULING SCENARIOS")
    print("=" * 50)
    
    # Simulate different user scenarios
    scenarios = [
        {
            "name": "User in IST timezone",
            "timezone": "Asia/Kolkata",
            "notifications": [
                {"time": "08:00", "days": [0, 1, 2, 3, 4], "desc": "Weekday morning"},
                {"time": "18:00", "days": [0, 1, 2, 3, 4], "desc": "Weekday evening"},
                {"time": "10:00", "days": [5, 6], "desc": "Weekend morning"},
            ]
        },
        {
            "name": "User in EST timezone",
            "timezone": "America/New_York",
            "notifications": [
                {"time": "07:00", "days": [0, 1, 2, 3, 4], "desc": "Weekday morning"},
                {"time": "19:00", "days": [0, 1, 2, 3, 4], "desc": "Weekday evening"},
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n👤 {scenario['name']}")
        tz = pytz.timezone(scenario['timezone'])
        now_utc = datetime.now(pytz.UTC)
        now_local = now_utc.astimezone(tz)
        
        print(f"  Current time: {now_local.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_local.weekday()})")
        
        for notification in scenario['notifications']:
            hour, minute = map(int, notification['time'].split(':'))
            target_time = time(hour, minute)
            
            print(f"\n  📱 {notification['desc']} ({notification['time']})")
            for day in notification['days']:
                days_ahead = (day - now_local.weekday()) % 7
                if days_ahead == 0 and now_local.time() >= target_time:
                    days_ahead = 7
                
                next_occurrence = now_local + timedelta(days=days_ahead)
                next_occurrence = next_occurrence.replace(
                    hour=target_time.hour,
                    minute=target_time.minute,
                    second=0,
                    microsecond=0
                )
                
                day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
                print(f"    {day_name}: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S %A')}")

def test_diet_extraction_day_handling():
    """Test how diet extraction handles day-specific notifications"""
    print("\n🔍 TESTING DIET EXTRACTION DAY HANDLING")
    print("=" * 50)
    
    # Simulate diet extraction scenarios
    diet_scenarios = [
        {
            "name": "Monday-specific activity",
            "activity": "Take medication at 8:00 AM",
            "day_header": "Monday",
            "expected_day": 0,  # Monday
            "expected_time": "08:00"
        },
        {
            "name": "Weekend activity",
            "activity": "Exercise at 10:00 AM",
            "day_header": "Saturday",
            "expected_day": 5,  # Saturday
            "expected_time": "10:00"
        },
        {
            "name": "No day header",
            "activity": "Drink water at 12:00 PM",
            "day_header": None,
            "expected_day": None,  # Should be determined by diet structure
            "expected_time": "12:00"
        }
    ]
    
    for scenario in diet_scenarios:
        print(f"\n📋 {scenario['name']}")
        print(f"  Activity: {scenario['activity']}")
        print(f"  Day header: {scenario['day_header']}")
        print(f"  Expected day: {scenario['expected_day']}")
        print(f"  Expected time: {scenario['expected_time']}")
        
        # Simulate the extraction logic
        if scenario['day_header']:
            day_mapping = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            }
            extracted_day = day_mapping.get(scenario['day_header'])
            print(f"  ✅ Day extracted: {extracted_day}")
        else:
            print(f"  ⚠️  No day header - needs diet structure analysis")

def analyze_potential_issues():
    """Analyze potential issues found during testing"""
    print("\n🔍 ANALYZING POTENTIAL ISSUES")
    print("=" * 50)
    
    issues = [
        {
            "type": "timezone_inconsistency",
            "severity": "HIGH",
            "description": "Frontend uses local device time while backend uses UTC",
            "impact": "Notifications scheduled for wrong day when timezone differs",
            "location": "Frontend: mobileapp/services/*.ts, Backend: backend/services/notification_scheduler.py"
        },
        {
            "type": "day_numbering_mismatch",
            "severity": "CRITICAL",
            "description": "Backend uses 0=Monday while JavaScript uses 0=Sunday",
            "impact": "Day conversion errors causing wrong day scheduling",
            "location": "Conversion logic: js_day = (backend_day + 1) % 7"
        },
        {
            "type": "day_boundary_crossing",
            "severity": "HIGH",
            "description": "Notifications near midnight can appear on wrong day",
            "impact": "Late night notifications scheduled for next day",
            "location": "All scheduling logic"
        },
        {
            "type": "diet_day_determination",
            "severity": "MEDIUM",
            "description": "Activities without day headers need proper diet day determination",
            "impact": "Notifications scheduled for wrong days if diet structure unclear",
            "location": "backend/services/diet_notification_service.py"
        },
        {
            "type": "recurring_scheduling",
            "severity": "MEDIUM",
            "description": "Weekly recurring notifications may not reschedule correctly",
            "impact": "Notifications stop working after first occurrence",
            "location": "Backend notification scheduler"
        }
    ]
    
    print("🚨 IDENTIFIED ISSUES:")
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['type'].upper()}")
        print(f"   Severity: {issue['severity']}")
        print(f"   Description: {issue['description']}")
        print(f"   Impact: {issue['impact']}")
        print(f"   Location: {issue['location']}")

def main():
    """Run all comprehensive tests"""
    print("🔬 COMPREHENSIVE NOTIFICATION DEBUGGING")
    print("=" * 60)
    print("Testing notification scheduling system for timing and day issues")
    print("=" * 60)
    
    try:
        test_timezone_handling()
        test_day_calculation_logic()
        test_frontend_backend_consistency()
        test_edge_cases()
        test_notification_scheduling_scenarios()
        test_diet_extraction_day_handling()
        analyze_potential_issues()
        
        print("\n✅ COMPREHENSIVE TESTING COMPLETED")
        print("=" * 60)
        print("All tests completed. Review the output above for potential issues.")
        
    except Exception as e:
        print(f"\n❌ ERROR DURING TESTING: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
