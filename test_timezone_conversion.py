#!/usr/bin/env python3
"""
Test script to check timezone conversion issue
"""

from datetime import datetime, timedelta
import pytz

def test_timezone_conversion():
    """Test timezone conversion to find the day offset issue"""
    
    print("🧪 Testing Timezone Conversion Issue")
    print("=" * 50)
    
    # Test with different days and times
    test_cases = [
        (3, "05:30", "Thursday 5:30 AM"),
        (4, "05:30", "Friday 5:30 AM"),
        (5, "05:30", "Saturday 5:30 AM"),
        (3, "22:30", "Thursday 10:30 PM"),
        (4, "22:30", "Friday 10:30 PM"),
    ]
    
    # Get current time in UTC
    now_utc = datetime.now(pytz.UTC)
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = now_utc.astimezone(ist)
    
    print(f"Current UTC: {now_utc}")
    print(f"Current IST: {now_ist}")
    print(f"Current IST weekday: {now_ist.weekday()}")
    print()
    
    for target_day, target_time, description in test_cases:
        print(f"🔍 Testing {description}:")
        print("-" * 40)
        
        # Parse the target time
        target_time_obj = datetime.strptime(target_time, '%H:%M').time()
        
        # Calculate days ahead
        days_ahead = (target_day - now_ist.weekday()) % 7
        if days_ahead == 0 and now_ist.time() >= target_time_obj:
            days_ahead = 7
        
        print(f"  Days ahead calculation: ({target_day} - {now_ist.weekday()}) % 7 = {days_ahead}")
        
        # Calculate next occurrence in IST
        next_occurrence_ist = now_ist + timedelta(days=days_ahead)
        next_occurrence_ist = next_occurrence_ist.replace(
            hour=target_time_obj.hour,
            minute=target_time_obj.minute,
            second=0,
            microsecond=0
        )
        
        # Convert to UTC
        next_occurrence_utc = next_occurrence_ist.astimezone(pytz.UTC)
        
        print(f"  Next occurrence IST: {next_occurrence_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_ist.weekday()})")
        print(f"  Next occurrence UTC: {next_occurrence_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence_utc.weekday()})")
        
        # Check if there's a day offset
        ist_weekday = next_occurrence_ist.weekday()
        utc_weekday = next_occurrence_utc.weekday()
        
        if ist_weekday != utc_weekday:
            print(f"  ⚠️  DAY OFFSET DETECTED!")
            print(f"     IST weekday: {ist_weekday} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][ist_weekday]})")
            print(f"     UTC weekday: {utc_weekday} ({['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][utc_weekday]})")
        else:
            print(f"  ✅ No day offset")
        
        print()
    
    # Test the specific issue: IST to UTC conversion at day boundary
    print("🔍 Testing Day Boundary Conversion:")
    print("-" * 40)
    
    # Test Thursday 5:30 AM IST
    thursday_5_30_ist = now_ist.replace(weekday=3, hour=5, minute=30, second=0, microsecond=0)
    thursday_5_30_utc = thursday_5_30_ist.astimezone(pytz.UTC)
    
    print(f"Thursday 5:30 AM IST: {thursday_5_30_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {thursday_5_30_ist.weekday()})")
    print(f"Thursday 5:30 AM UTC: {thursday_5_30_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {thursday_5_30_utc.weekday()})")
    
    # Test Thursday 10:30 PM IST
    thursday_10_30_ist = now_ist.replace(weekday=3, hour=22, minute=30, second=0, microsecond=0)
    thursday_10_30_utc = thursday_10_30_ist.astimezone(pytz.UTC)
    
    print(f"Thursday 10:30 PM IST: {thursday_10_30_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {thursday_10_30_ist.weekday()})")
    print(f"Thursday 10:30 PM UTC: {thursday_10_30_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {thursday_10_30_utc.weekday()})")

if __name__ == "__main__":
    test_timezone_conversion()
