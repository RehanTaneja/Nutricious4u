#!/usr/bin/env python3
"""
Test script to check for systematic day offset
"""

from datetime import datetime, timedelta
import pytz

def test_day_offset():
    """Test for systematic day offset"""
    
    print("🧪 Testing for Systematic Day Offset")
    print("=" * 50)
    
    # Test the day calculation formula
    # The issue might be that we're calculating days ahead incorrectly
    
    # Get current time in UTC
    now_utc = datetime.now(pytz.UTC)
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = now_utc.astimezone(ist)
    
    print(f"Current IST: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_ist.weekday()})")
    print()
    
    # Test all days
    for target_day in range(7):
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][target_day]
        
        print(f"🔍 Testing {day_name} (day {target_day}):")
        
        # Current formula
        days_ahead = (target_day - now_ist.weekday()) % 7
        if days_ahead == 0 and now_ist.time() >= datetime.strptime("05:30", '%H:%M').time():
            days_ahead = 7
        
        # Calculate next occurrence
        next_occurrence = now_ist + timedelta(days=days_ahead)
        next_occurrence = next_occurrence.replace(hour=5, minute=30, second=0, microsecond=0)
        
        print(f"  Current weekday: {now_ist.weekday()}")
        print(f"  Target weekday: {target_day}")
        print(f"  Days ahead: {days_ahead}")
        print(f"  Next occurrence: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence.weekday()})")
        
        # Check if the result is correct
        expected_weekday = target_day
        actual_weekday = next_occurrence.weekday()
        
        if actual_weekday == expected_weekday:
            print(f"  ✅ Correct!")
        else:
            print(f"  ❌ Wrong! Expected {expected_weekday}, got {actual_weekday}")
        
        print()
    
    # Test the specific issue: if we're on Thursday and want Thursday notifications
    print("🔍 Testing Thursday → Thursday scenario:")
    print("-" * 40)
    
    # Simulate being on Thursday
    thursday_ist = now_ist.replace(hour=10, minute=0, second=0, microsecond=0)  # 10 AM Thursday
    if thursday_ist.weekday() != 3:
        # Adjust to Thursday
        days_to_add = (3 - thursday_ist.weekday()) % 7
        thursday_ist = thursday_ist + timedelta(days=days_to_add)
    
    print(f"Simulated Thursday IST: {thursday_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {thursday_ist.weekday()})")
    
    # Test Thursday notification
    target_day = 3  # Thursday
    days_ahead = (target_day - thursday_ist.weekday()) % 7
    if days_ahead == 0 and thursday_ist.time() >= datetime.strptime("05:30", '%H:%M').time():
        days_ahead = 7
    
    next_thursday = thursday_ist + timedelta(days=days_ahead)
    next_thursday = next_thursday.replace(hour=5, minute=30, second=0, microsecond=0)
    
    print(f"Days ahead: {days_ahead}")
    print(f"Next Thursday: {next_thursday.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_thursday.weekday()})")
    
    if next_thursday.weekday() == 3:
        print("✅ Correct! Next Thursday is Thursday")
    else:
        print(f"❌ Wrong! Expected Thursday (3), got {next_thursday.weekday()}")

if __name__ == "__main__":
    test_day_offset()
