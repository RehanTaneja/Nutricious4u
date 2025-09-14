#!/usr/bin/env python3
"""
Day Conversion Debug Test
========================

This script specifically tests the day conversion logic between backend and frontend
to identify the exact cause of wrong day scheduling.
"""

import json
from datetime import datetime, time, timedelta
import pytz

def test_day_conversion_logic():
    """Test the exact day conversion logic used in the code"""
    print("🔍 TESTING DAY CONVERSION LOGIC")
    print("=" * 50)
    
    # Test the conversion logic from the code
    print("Backend day format: 0=Monday, 1=Tuesday, ..., 6=Sunday")
    print("JavaScript day format: 0=Sunday, 1=Monday, ..., 6=Saturday")
    print("Conversion used in code: js_day = (backend_day + 1) % 7")
    print()
    
    # Test all possible conversions
    for backend_day in range(7):
        js_day = (backend_day + 1) % 7
        
        backend_day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][backend_day]
        js_day_name = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][js_day]
        
        print(f"Backend day {backend_day} ({backend_day_name}) → JS day {js_day} ({js_day_name})")
        
        # Check if this conversion is correct
        if backend_day == 0 and js_day == 1:  # Monday → Monday
            print("  ✅ Correct: Monday → Monday")
        elif backend_day == 6 and js_day == 0:  # Sunday → Sunday
            print("  ✅ Correct: Sunday → Sunday")
        else:
            print(f"  ⚠️  Check: {backend_day_name} → {js_day_name}")

def test_actual_scheduling_scenarios():
    """Test actual scheduling scenarios with the conversion logic"""
    print("\n🔍 TESTING ACTUAL SCHEDULING SCENARIOS")
    print("=" * 50)
    
    # Simulate the frontend logic from unifiedNotificationService.ts
    def frontend_calculate_next_occurrence(hours: int, minutes: int, day_of_week: int) -> datetime:
        now = datetime.now(pytz.UTC)
        
        # This is the conversion from the code: jsSelectedDay = (dayOfWeek + 1) % 7
        js_selected_day = (day_of_week + 1) % 7
        
        print(f"  Input day_of_week: {day_of_week}")
        print(f"  Converted js_selected_day: {js_selected_day}")
        
        for day_offset in range(8):  # 0 to 7
            check_date = now + timedelta(days=day_offset)
            check_day = check_date.weekday()
            
            # Convert Python weekday to JavaScript format
            js_check_day = (check_day + 1) % 7
            
            print(f"    Day offset {day_offset}: check_date={check_date.strftime('%Y-%m-%d %A')}, check_day={check_day}, js_check_day={js_check_day}")
            
            if js_check_day == js_selected_day:
                occurrence = check_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                print(f"    ✅ Match found: {occurrence.strftime('%Y-%m-%d %H:%M:%S %A')}")
                
                if day_offset == 0 and occurrence > now:
                    return occurrence
                if day_offset > 0:
                    return occurrence
        
        # Fallback
        fallback = now + timedelta(days=7)
        return fallback.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    # Test scenarios
    test_cases = [
        (8, 0, 0, "Monday 8:00 AM"),
        (12, 0, 2, "Wednesday 12:00 PM"),
        (18, 0, 4, "Friday 6:00 PM"),
        (10, 0, 6, "Sunday 10:00 AM"),
    ]
    
    for hours, minutes, day_of_week, description in test_cases:
        print(f"\n📅 Testing: {description}")
        print(f"  Backend day: {day_of_week} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]})")
        
        result = frontend_calculate_next_occurrence(hours, minutes, day_of_week)
        print(f"  Result: {result.strftime('%Y-%m-%d %H:%M:%S %A')}")
        print(f"  Expected day: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]}")
        
        # Check if the result is on the correct day
        result_day = result.weekday()
        expected_day = day_of_week
        
        if result_day == expected_day:
            print("  ✅ CORRECT: Notification scheduled on correct day")
        else:
            print(f"  ❌ WRONG: Expected day {expected_day}, got day {result_day}")

def test_backend_frontend_mismatch():
    """Test for mismatches between backend and frontend logic"""
    print("\n🔍 TESTING BACKEND-FRONTEND MISMATCH")
    print("=" * 50)
    
    # Backend logic (from notification_scheduler.py)
    def backend_calculate_next_occurrence(hours: int, minutes: int, day_of_week: int) -> datetime:
        now = datetime.now(pytz.UTC)
        target_time = time(hours, minutes)
        
        days_ahead = (day_of_week - now.weekday()) % 7
        if days_ahead == 0 and now.time() >= target_time:
            days_ahead = 7
        
        next_occurrence = now + timedelta(days=days_ahead)
        return next_occurrence.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
    
    # Frontend logic (from unifiedNotificationService.ts)
    def frontend_calculate_next_occurrence(hours: int, minutes: int, day_of_week: int) -> datetime:
        now = datetime.now(pytz.UTC)
        js_selected_day = (day_of_week + 1) % 7
        
        for day_offset in range(8):
            check_date = now + timedelta(days=day_offset)
            check_day = check_date.weekday()
            js_check_day = (check_day + 1) % 7
            
            if js_check_day == js_selected_day:
                occurrence = check_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                if day_offset == 0 and occurrence > now:
                    return occurrence
                if day_offset > 0:
                    return occurrence
        
        fallback = now + timedelta(days=7)
        return fallback.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    # Test all days
    for day_of_week in range(7):
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
        
        backend_result = backend_calculate_next_occurrence(12, 0, day_of_week)
        frontend_result = frontend_calculate_next_occurrence(12, 0, day_of_week)
        
        print(f"\n{day_name} (day {day_of_week}):")
        print(f"  Backend:  {backend_result.strftime('%Y-%m-%d %H:%M:%S %A')} (weekday: {backend_result.weekday()})")
        print(f"  Frontend: {frontend_result.strftime('%Y-%m-%d %H:%M:%S %A')} (weekday: {frontend_result.weekday()})")
        
        if backend_result.date() == frontend_result.date():
            print("  ✅ MATCH: Same date")
        else:
            print("  ❌ MISMATCH: Different dates!")
            print(f"    Difference: {(frontend_result - backend_result).days} days")

def test_timezone_impact():
    """Test how timezone affects day calculations"""
    print("\n🔍 TESTING TIMEZONE IMPACT")
    print("=" * 50)
    
    # Test with different timezones
    timezones = [
        ('UTC', 'UTC'),
        ('IST', 'Asia/Kolkata'),
        ('EST', 'America/New_York'),
    ]
    
    test_time = (12, 0)  # 12:00 PM
    test_day = 0  # Monday
    
    for tz_name, tz_zone in timezones:
        print(f"\n📍 Testing in {tz_name} ({tz_zone})")
        tz = pytz.timezone(tz_zone)
        now_utc = datetime.now(pytz.UTC)
        now_local = now_utc.astimezone(tz)
        
        print(f"  Current UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_utc.weekday()})")
        print(f"  Current {tz_name}: {now_local.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_local.weekday()})")
        
        # Calculate next Monday 12:00 PM in local timezone
        days_ahead = (test_day - now_local.weekday()) % 7
        if days_ahead == 0 and now_local.time() >= time(*test_time):
            days_ahead = 7
        
        next_occurrence = now_local + timedelta(days=days_ahead)
        next_occurrence = next_occurrence.replace(hour=test_time[0], minute=test_time[1], second=0, microsecond=0)
        
        print(f"  Next Monday 12:00 PM in {tz_name}: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence.weekday()})")
        
        # Convert back to UTC
        next_occurrence_utc = next_occurrence.astimezone(pytz.UTC)
        print(f"  Same time in UTC: {next_occurrence_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_utc.weekday()})")

def main():
    """Run all day conversion tests"""
    print("🔬 DAY CONVERSION DEBUG TESTING")
    print("=" * 60)
    print("Testing day conversion logic between backend and frontend")
    print("=" * 60)
    
    try:
        test_day_conversion_logic()
        test_actual_scheduling_scenarios()
        test_backend_frontend_mismatch()
        test_timezone_impact()
        
        print("\n✅ DAY CONVERSION TESTING COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR DURING TESTING: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
