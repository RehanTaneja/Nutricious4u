#!/usr/bin/env python3
"""
Test script to verify the timezone fix for day calculations
"""

from datetime import datetime, timedelta
import pytz

def test_timezone_fix():
    """Test the timezone fix for day calculations"""
    
    print("🧪 Testing Timezone Fix for Day Calculations")
    print("=" * 60)
    
    # Get current time in UTC
    now_utc = datetime.now(pytz.UTC)
    print(f"Current UTC: {now_utc}")
    print(f"Current UTC weekday: {now_utc.weekday()} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now_utc.weekday()]})")
    
    # Convert to IST
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = now_utc.astimezone(ist)
    print(f"Current IST: {now_ist}")
    print(f"Current IST weekday: {now_ist.weekday()} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now_ist.weekday()]})")
    
    # Test with Thursday (day 3) and Friday (day 4) notifications
    test_days = [3, 4]  # Thursday and Friday
    test_time = "05:30"  # 5:30 AM
    
    print(f"\n📅 Testing notifications for {test_time}:")
    print("=" * 60)
    
    for day in test_days:
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
        
        # Parse the notification time
        target_time = datetime.strptime(test_time, '%H:%M').time()
        
        # Calculate next occurrence of this day and time in IST
        days_ahead = (day - now_ist.weekday()) % 7
        if days_ahead == 0 and now_ist.time() >= target_time:
            days_ahead = 7
        
        # Calculate the next occurrence in IST
        next_occurrence_ist = now_ist + timedelta(days=days_ahead)
        next_occurrence_ist = next_occurrence_ist.replace(
            hour=target_time.hour, 
            minute=target_time.minute, 
            second=0, 
            microsecond=0
        )
        
        # Convert back to UTC for storage
        next_occurrence_utc = next_occurrence_ist.astimezone(pytz.UTC)
        
        print(f"  📅 {day_name} (day {day}):")
        print(f"    Current IST weekday: {now_ist.weekday()}")
        print(f"    Target weekday: {day}")
        print(f"    Days ahead calculation: ({day} - {now_ist.weekday()}) % 7 = {days_ahead}")
        print(f"    Next occurrence IST: {next_occurrence_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_ist.weekday()})")
        print(f"    Next occurrence UTC: {next_occurrence_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_utc.weekday()})")
        print()
    
    # Test what happens if we're on Thursday and want Thursday notifications
    print("🔍 Testing Thursday → Thursday scenario:")
    print("=" * 60)
    
    # Simulate being on Thursday in IST
    thursday_ist = now_ist.replace(weekday=3)  # Thursday is day 3
    print(f"Simulated Thursday IST: {thursday_ist}")
    
    # Calculate Thursday notification (day 3)
    thursday_day = 3
    days_ahead = (thursday_day - thursday_ist.weekday()) % 7
    if days_ahead == 0 and thursday_ist.time() >= target_time:
        days_ahead = 7
    
    next_thursday_ist = thursday_ist + timedelta(days=days_ahead)
    next_thursday_ist = next_thursday_ist.replace(
        hour=target_time.hour, 
        minute=target_time.minute, 
        second=0, 
        microsecond=0
    )
    
    next_thursday_utc = next_thursday_ist.astimezone(pytz.UTC)
    
    print(f"  Days ahead: {days_ahead}")
    print(f"  Next Thursday IST: {next_thursday_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_thursday_ist.weekday()})")
    print(f"  Next Thursday UTC: {next_thursday_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_thursday_utc.weekday()})")
    
    # Test what happens if we're on Thursday and want Friday notifications
    print("\n🔍 Testing Thursday → Friday scenario:")
    print("=" * 60)
    
    # Calculate Friday notification (day 4)
    friday_day = 4
    days_ahead = (friday_day - thursday_ist.weekday()) % 7
    if days_ahead == 0 and thursday_ist.time() >= target_time:
        days_ahead = 7
    
    next_friday_ist = thursday_ist + timedelta(days=days_ahead)
    next_friday_ist = next_friday_ist.replace(
        hour=target_time.hour, 
        minute=target_time.minute, 
        second=0, 
        microsecond=0
    )
    
    next_friday_utc = next_friday_ist.astimezone(pytz.UTC)
    
    print(f"  Days ahead: {days_ahead}")
    print(f"  Next Friday IST: {next_friday_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_friday_ist.weekday()})")
    print(f"  Next Friday UTC: {next_friday_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_friday_utc.weekday()})")

if __name__ == "__main__":
    test_timezone_fix()
