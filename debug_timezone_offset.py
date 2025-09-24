#!/usr/bin/env python3

from datetime import datetime, timezone
import pytz

def debug_timezone_offset():
    """Debug timezone offset calculation to understand the correct logic"""
    
    print("🕐 DEBUGGING TIMEZONE OFFSET CALCULATION")
    print("=" * 50)
    
    # Current times
    local_time = datetime.now()
    utc_time = datetime.now(timezone.utc)
    
    print(f"Local time: {local_time}")
    print(f"UTC time: {utc_time}")
    
    # Python timezone offset calculation
    local_tz = local_time.astimezone()
    python_offset_seconds = local_tz.utcoffset().total_seconds()
    python_offset_minutes = int(python_offset_seconds / 60)
    
    print(f"\nPython timezone offset:")
    print(f"  Seconds: {python_offset_seconds}")
    print(f"  Minutes: {python_offset_minutes}")
    print(f"  Hours: {python_offset_minutes / 60}")
    
    # JavaScript getTimezoneOffset() equivalent
    # JavaScript returns the opposite sign and is in minutes
    js_offset_minutes = int(-python_offset_minutes)
    
    print(f"\nJavaScript getTimezoneOffset() equivalent:")
    print(f"  Minutes: {js_offset_minutes}")
    print(f"  Hours: {js_offset_minutes / 60}")
    
    print(f"\nTo convert UTC to local time:")
    print(f"  UTC time: {utc_time}")
    print(f"  Add Python offset: {utc_time} + {python_offset_minutes} minutes")
    
    from datetime import timedelta
    calculated_local = utc_time.replace(tzinfo=None) + timedelta(minutes=python_offset_minutes)
    print(f"  Result: {calculated_local}")
    print(f"  Expected: {local_time}")
    print(f"  Match: {'✅' if abs((calculated_local - local_time).total_seconds()) < 60 else '❌'}")
    
    print(f"\nUsing JavaScript offset (WRONG WAY):")
    calculated_local_js = utc_time.replace(tzinfo=None) - timedelta(minutes=js_offset_minutes)
    print(f"  UTC - JS_offset: {utc_time} - {js_offset_minutes} minutes = {calculated_local_js}")
    print(f"  Match: {'✅' if abs((calculated_local_js - local_time).total_seconds()) < 60 else '❌'}")
    
    print(f"\nCORRECT BACKEND CALCULATION:")
    print(f"  If frontend sends JS offset: {js_offset_minutes}")
    print(f"  Backend should do: UTC + JS_offset = {utc_time} + {js_offset_minutes} minutes")
    backend_correct = utc_time.replace(tzinfo=None) + timedelta(minutes=js_offset_minutes)
    print(f"  Result: {backend_correct}")
    print(f"  Match: {'✅' if abs((backend_correct - local_time).total_seconds()) < 60 else '❌'}")

if __name__ == "__main__":
    debug_timezone_offset()
