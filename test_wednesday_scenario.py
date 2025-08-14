#!/usr/bin/env python3
"""
Test script to simulate being on Wednesday and scheduling Thursday notifications
"""

from datetime import datetime, timedelta
import pytz

def test_wednesday_scenario():
    """Test the Wednesday scenario"""
    
    print("🧪 Testing Wednesday → Thursday Scenario")
    print("=" * 50)
    
    # Simulate being on Wednesday
    # Get current time in UTC
    now_utc = datetime.now(pytz.UTC)
    
    # Convert to IST
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = now_utc.astimezone(ist)
    
    # Force Wednesday (day 2)
    # Calculate how many days to subtract to get to Wednesday
    days_to_subtract = (now_ist.weekday() - 2) % 7
    if days_to_subtract == 0:
        days_to_subtract = 7  # If we're already on Wednesday, go to last Wednesday
    
    wednesday_ist = now_ist - timedelta(days=days_to_subtract)
    wednesday_ist = wednesday_ist.replace(hour=10, minute=0, second=0, microsecond=0)  # 10 AM Wednesday
    
    print(f"Simulated Wednesday IST: {wednesday_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {wednesday_ist.weekday()})")
    
    # Now schedule Thursday notifications
    target_day = 3  # Thursday
    target_time = "05:30"
    
    print(f"\n🔍 Scheduling Thursday notification at {target_time}:")
    print("=" * 50)
    
    # Parse the target time
    target_time_obj = datetime.strptime(target_time, '%H:%M').time()
    
    # Calculate days ahead
    days_ahead = (target_day - wednesday_ist.weekday()) % 7
    print(f"Days ahead calculation: ({target_day} - {wednesday_ist.weekday()}) % 7 = {days_ahead}")
    
    # Check if we need to go to next week
    if days_ahead == 0 and wednesday_ist.time() >= target_time_obj:
        days_ahead = 7
        print(f"Since current time ({wednesday_ist.time()}) >= target time ({target_time_obj}), days_ahead = 7")
    
    print(f"Final days ahead: {days_ahead}")
    
    # Calculate next occurrence
    next_occurrence_ist = wednesday_ist + timedelta(days=days_ahead)
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
    
    # Check if this is correct
    expected_day = "Thursday"
    actual_day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][next_occurrence_ist.weekday()]
    
    if actual_day == expected_day:
        print(f"✅ Correct! Scheduled for {actual_day}")
    else:
        print(f"❌ Wrong! Expected {expected_day}, got {actual_day}")
    
    # Also test Friday
    print(f"\n🔍 Scheduling Friday notification at {target_time}:")
    print("=" * 50)
    
    target_day_friday = 4  # Friday
    days_ahead_friday = (target_day_friday - wednesday_ist.weekday()) % 7
    print(f"Days ahead calculation: ({target_day_friday} - {wednesday_ist.weekday()}) % 7 = {days_ahead_friday}")
    
    if days_ahead_friday == 0 and wednesday_ist.time() >= target_time_obj:
        days_ahead_friday = 7
        print(f"Since current time ({wednesday_ist.time()}) >= target time ({target_time_obj}), days_ahead = 7")
    
    print(f"Final days ahead: {days_ahead_friday}")
    
    next_occurrence_friday_ist = wednesday_ist + timedelta(days=days_ahead_friday)
    next_occurrence_friday_ist = next_occurrence_friday_ist.replace(
        hour=target_time_obj.hour,
        minute=target_time_obj.minute,
        second=0,
        microsecond=0
    )
    
    next_occurrence_friday_utc = next_occurrence_friday_ist.astimezone(pytz.UTC)
    
    print(f"Next occurrence IST: {next_occurrence_friday_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_friday_ist.weekday()})")
    print(f"Next occurrence UTC: {next_occurrence_friday_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_friday_utc.weekday()})")
    
    expected_day_friday = "Friday"
    actual_day_friday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][next_occurrence_friday_ist.weekday()]
    
    if actual_day_friday == expected_day_friday:
        print(f"✅ Correct! Scheduled for {actual_day_friday}")
    else:
        print(f"❌ Wrong! Expected {expected_day_friday}, got {actual_day_friday}")

if __name__ == "__main__":
    test_wednesday_scenario()
