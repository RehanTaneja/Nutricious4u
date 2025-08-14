#!/usr/bin/env python3
"""
Test script to understand the day calculation issue
"""

from datetime import datetime, timedelta
import pytz

def test_day_issue():
    """Test the day calculation issue"""
    
    print("🧪 Testing Day Calculation Issue")
    print("=" * 50)
    
    # Simulate the scenario: We're on Thursday and want to schedule Thursday notifications
    # Current time: Thursday 22:27 IST (which is past 5:30 AM)
    
    # Get current time in UTC
    now_utc = datetime.now(pytz.UTC)
    print(f"Current UTC: {now_utc}")
    print(f"Current UTC weekday: {now_utc.weekday()} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now_utc.weekday()]})")
    
    # Convert to IST
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = now_utc.astimezone(ist)
    print(f"Current IST: {now_ist}")
    print(f"Current IST weekday: {now_ist.weekday()} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now_ist.weekday()]})")
    
    # Test the issue: Thursday notification at 5:30 AM
    target_day = 3  # Thursday
    target_time = "05:30"
    
    print(f"\n🔍 Testing Thursday notification at {target_time}:")
    print("=" * 50)
    
    # Parse the target time
    target_time_obj = datetime.strptime(target_time, '%H:%M').time()
    
    # Calculate days ahead
    days_ahead = (target_day - now_ist.weekday()) % 7
    print(f"Days ahead calculation: ({target_day} - {now_ist.weekday()}) % 7 = {days_ahead}")
    
    # Check if we need to go to next week
    if days_ahead == 0 and now_ist.time() >= target_time_obj:
        days_ahead = 7
        print(f"Since current time ({now_ist.time()}) >= target time ({target_time_obj}), days_ahead = 7")
    
    print(f"Final days ahead: {days_ahead}")
    
    # Calculate next occurrence
    next_occurrence_ist = now_ist + timedelta(days=days_ahead)
    next_occurrence_ist = next_occurrence_ist.replace(
        hour=target_time_obj.hour,
        minute=target_time_obj.minute,
        second=0,
        microsecond=0
    )
    
    # Convert to UTC
    next_occurrence_utc = next_occurrence_ist.astimezone(pytz.UTC)
    
    print(f"Next occurrence IST: {next_occurrence_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_ist.weekday()})")
    print(f"Next occurrence UTC: {next_occurrence_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_utc.weekday()})")
    
    # The issue might be that we're scheduling for next Thursday instead of today's Thursday
    # Let's test what happens if we schedule for today's Thursday
    print(f"\n🔍 Testing scheduling for today's Thursday:")
    print("=" * 50)
    
    # Force today's Thursday
    today_thursday_ist = now_ist.replace(hour=target_time_obj.hour, minute=target_time_obj.minute, second=0, microsecond=0)
    today_thursday_utc = today_thursday_ist.astimezone(pytz.UTC)
    
    print(f"Today's Thursday IST: {today_thursday_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {today_thursday_ist.weekday()})")
    print(f"Today's Thursday UTC: {today_thursday_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {today_thursday_utc.weekday()})")
    
    # Check if today's Thursday has already passed
    if today_thursday_ist <= now_ist:
        print("❌ Today's Thursday has already passed!")
        print("✅ This explains why it's going to next Thursday")
    else:
        print("✅ Today's Thursday is still in the future")
        print("❌ This means there's a bug in the logic")

if __name__ == "__main__":
    test_day_issue()
