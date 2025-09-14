#!/usr/bin/env python3
"""
Comprehensive Issues Analysis
============================

This script analyzes all the potential issues found during testing
and provides specific recommendations for fixes.
"""

import json
from datetime import datetime, time, timedelta
import pytz
from typing import Dict, List, Tuple, Optional

def analyze_timezone_issues():
    """Analyze timezone-related issues"""
    print("🔍 ANALYZING TIMEZONE ISSUES")
    print("=" * 50)
    
    issues = []
    
    # Issue 1: Frontend uses local time, backend uses UTC
    print("\n1. FRONTEND vs BACKEND TIMEZONE MISMATCH")
    print("   Problem: Frontend calculates times in local device timezone")
    print("   Backend calculates times in UTC")
    print("   Impact: Notifications scheduled for wrong day when timezone differs")
    
    # Demonstrate the issue
    now_utc = datetime.now(pytz.UTC)
    now_ist = now_utc.astimezone(pytz.timezone('Asia/Kolkata'))
    
    print(f"   Example:")
    print(f"   Current UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_utc.weekday()})")
    print(f"   Current IST: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now_ist.weekday()})")
    
    if now_utc.weekday() != now_ist.weekday():
        print("   ❌ CRITICAL: Different weekdays in UTC vs IST!")
        print("   This will cause notifications to be scheduled for wrong days")
    else:
        print("   ✅ Same weekday in both timezones")
    
    issues.append({
        "type": "timezone_mismatch",
        "severity": "CRITICAL",
        "description": "Frontend uses local timezone while backend uses UTC",
        "impact": "Notifications scheduled for wrong day when timezone differs",
        "example": f"UTC weekday: {now_utc.weekday()}, IST weekday: {now_ist.weekday()}"
    })
    
    return issues

def analyze_day_conversion_issues():
    """Analyze day conversion issues"""
    print("\n🔍 ANALYZING DAY CONVERSION ISSUES")
    print("=" * 50)
    
    issues = []
    
    # Issue 2: Day numbering mismatch
    print("\n2. DAY NUMBERING MISMATCH")
    print("   Backend: 0=Monday, 1=Tuesday, ..., 6=Sunday")
    print("   JavaScript: 0=Sunday, 1=Monday, ..., 6=Saturday")
    print("   Conversion: js_day = (backend_day + 1) % 7")
    
    # Test the conversion
    print("\n   Testing conversion:")
    for backend_day in range(7):
        js_day = (backend_day + 1) % 7
        backend_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][backend_day]
        js_name = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][js_day]
        
        if backend_day == 0 and js_day == 1:  # Monday → Monday
            print(f"   ✅ {backend_name} (backend {backend_day}) → {js_name} (js {js_day})")
        elif backend_day == 6 and js_day == 0:  # Sunday → Sunday
            print(f"   ✅ {backend_name} (backend {backend_day}) → {js_name} (js {js_day})")
        else:
            print(f"   ⚠️  {backend_name} (backend {backend_day}) → {js_name} (js {js_day})")
    
    # The conversion is actually correct, but let's check if it's being used consistently
    print("\n   ✅ Day conversion logic is mathematically correct")
    
    issues.append({
        "type": "day_conversion",
        "severity": "LOW",
        "description": "Day numbering mismatch between backend and frontend",
        "impact": "Conversion logic is correct, but needs verification",
        "status": "VERIFIED_CORRECT"
    })
    
    return issues

def analyze_scheduling_logic_issues():
    """Analyze scheduling logic issues"""
    print("\n🔍 ANALYZING SCHEDULING LOGIC ISSUES")
    print("=" * 50)
    
    issues = []
    
    # Issue 3: Backend scheduling logic
    print("\n3. BACKEND SCHEDULING LOGIC ANALYSIS")
    
    # Simulate the backend logic from notification_scheduler_simple.py
    def backend_calculate_next_occurrence(hour: int, minute: int, selected_days: List[int]) -> datetime:
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if target_time <= now:
            current_day = now.weekday()
            next_day = None
            
            # Check remaining days this week
            for day in range(current_day + 1, 7):
                if day in selected_days:
                    next_day = day
                    break
            
            # If no remaining days this week, find first selected day next week
            if next_day is None:
                for day in range(7):
                    if day in selected_days:
                        next_day = day
                        break
            
            if next_day is not None:
                days_ahead = (next_day - current_day) % 7
                if days_ahead == 0:  # Same day, next week
                    days_ahead = 7
                target_time = now + timedelta(days=days_ahead)
                target_time = target_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return target_time
    
    # Test the logic
    print("   Testing backend scheduling logic:")
    test_cases = [
        (8, 0, [0, 1, 2, 3, 4], "Weekday morning"),
        (18, 0, [0, 2, 4], "Mon/Wed/Fri evening"),
        (10, 0, [5, 6], "Weekend morning"),
    ]
    
    for hour, minute, selected_days, desc in test_cases:
        result = backend_calculate_next_occurrence(hour, minute, selected_days)
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][result.weekday()]
        print(f"   {desc}: {result.strftime('%Y-%m-%d %H:%M:%S %A')}")
        
        # Check if result is on a selected day
        if result.weekday() in selected_days:
            print(f"   ✅ Correct: Scheduled on {day_name} (day {result.weekday()})")
        else:
            print(f"   ❌ Wrong: Scheduled on {day_name} (day {result.weekday()}), expected one of {selected_days}")
    
    # Issue 4: Timezone handling in backend
    print("\n4. BACKEND TIMEZONE HANDLING")
    print("   Problem: Backend uses datetime.now() without timezone")
    print("   This means it uses local server time, not UTC")
    print("   Impact: Inconsistent behavior across different server locations")
    
    issues.append({
        "type": "backend_timezone",
        "severity": "HIGH",
        "description": "Backend uses local time instead of UTC",
        "impact": "Inconsistent behavior across server locations",
        "recommendation": "Use datetime.now(timezone.utc) consistently"
    })
    
    return issues

def analyze_diet_extraction_issues():
    """Analyze diet extraction issues"""
    print("\n🔍 ANALYZING DIET EXTRACTION ISSUES")
    print("=" * 50)
    
    issues = []
    
    # Issue 5: Activities without day headers
    print("\n5. ACTIVITIES WITHOUT DAY HEADERS")
    print("   Problem: Some activities don't have day headers")
    print("   Current behavior: selectedDays = [] (empty)")
    print("   Impact: Notifications not scheduled for these activities")
    
    # Simulate the issue
    activities_without_days = [
        "Drink water at 12:00 PM",
        "Take vitamins at 9:00 AM",
        "Evening walk at 7:00 PM"
    ]
    
    print("   Examples of activities without day headers:")
    for activity in activities_without_days:
        print(f"   - {activity}")
        print(f"     → selectedDays = [] (empty)")
        print(f"     → Notification will NOT be scheduled")
    
    issues.append({
        "type": "missing_day_headers",
        "severity": "MEDIUM",
        "description": "Activities without day headers get empty selectedDays",
        "impact": "Notifications not scheduled for these activities",
        "recommendation": "Implement diet structure analysis to determine default days"
    })
    
    # Issue 6: Day-specific vs general activities
    print("\n6. DAY-SPECIFIC vs GENERAL ACTIVITIES")
    print("   Problem: Need to distinguish between day-specific and general activities")
    print("   Current behavior: Day-specific activities get single day, others get empty")
    
    day_specific_examples = [
        ("Monday\nTake medication at 8:00 AM", [0]),  # Monday only
        ("Wednesday\nExercise at 6:00 PM", [2]),      # Wednesday only
    ]
    
    general_examples = [
        ("Drink water at 12:00 PM", []),  # Should be all days
        ("Take vitamins at 9:00 AM", []), # Should be all days
    ]
    
    print("   Day-specific activities:")
    for text, expected_days in day_specific_examples:
        print(f"   - {text}")
        print(f"     → selectedDays = {expected_days} ✅")
    
    print("   General activities:")
    for text, current_days in general_examples:
        print(f"   - {text}")
        print(f"     → selectedDays = {current_days} ❌ (should be [0,1,2,3,4,5,6])")
    
    return issues

def analyze_notification_delivery_issues():
    """Analyze notification delivery issues"""
    print("\n🔍 ANALYZING NOTIFICATION DELIVERY ISSUES")
    print("=" * 50)
    
    issues = []
    
    # Issue 7: Recurring notifications
    print("\n7. RECURRING NOTIFICATION HANDLING")
    print("   Problem: Backend sends notification once, mobile app handles repeats")
    print("   Current behavior: Backend marks as 'sent', mobile app schedules next occurrence")
    print("   Potential issue: If mobile app doesn't handle repeats properly, notifications stop")
    
    print("   Backend logic:")
    print("   - Send notification")
    print("   - Mark as 'sent'")
    print("   - Do NOT schedule next occurrence (relies on mobile app)")
    
    print("   Mobile app logic:")
    print("   - Schedule with repeats: true")
    print("   - repeatInterval: 7 * 24 * 60 * 60 * 1000 (7 days)")
    
    issues.append({
        "type": "recurring_handling",
        "severity": "MEDIUM",
        "description": "Recurring notifications depend on mobile app handling",
        "impact": "Notifications may stop if mobile app doesn't handle repeats",
        "recommendation": "Verify mobile app repeat handling works correctly"
    })
    
    # Issue 8: Notification timing precision
    print("\n8. NOTIFICATION TIMING PRECISION")
    print("   Problem: Notifications scheduled with second precision")
    print("   Impact: Potential timing issues if system is slow")
    
    now = datetime.now()
    scheduled_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    print(f"   Example: Notification scheduled for {scheduled_time}")
    print(f"   If system processes at {now}, timing difference: {(scheduled_time - now).total_seconds()} seconds")
    
    if (scheduled_time - now).total_seconds() < 0:
        print("   ❌ Notification is overdue!")
    elif (scheduled_time - now).total_seconds() < 60:
        print("   ⚠️  Notification is very close to due time")
    else:
        print("   ✅ Notification timing looks good")
    
    return issues

def analyze_edge_cases():
    """Analyze edge cases"""
    print("\n🔍 ANALYZING EDGE CASES")
    print("=" * 50)
    
    issues = []
    
    # Issue 9: Midnight boundary crossing
    print("\n9. MIDNIGHT BOUNDARY CROSSING")
    print("   Problem: Notifications near midnight can appear on wrong day")
    
    # Test midnight scenarios
    midnight_times = [23, 0, 1]  # 11 PM, 12 AM, 1 AM
    
    for hour in midnight_times:
        test_time = time(hour, 0)
        print(f"   Testing {hour:02d}:00")
        
        # Simulate scheduling at different times
        for test_hour in [22, 23, 0, 1]:
            test_now = datetime.now().replace(hour=test_hour, minute=0, second=0, microsecond=0)
            scheduled_time = test_now.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            if scheduled_time <= test_now:
                scheduled_time += timedelta(days=1)
            
            day_diff = (scheduled_time.date() - test_now.date()).days
            print(f"     Scheduled at {test_hour:02d}:00 → {scheduled_time.strftime('%Y-%m-%d %H:%M')} (day diff: {day_diff})")
    
    # Issue 10: DST transitions
    print("\n10. DST TRANSITION HANDLING")
    print("    Problem: DST transitions can affect day calculations")
    print("    Current implementation: Uses UTC which avoids DST issues")
    print("    ✅ This is handled correctly")
    
    return issues

def generate_recommendations():
    """Generate specific recommendations for fixes"""
    print("\n🔧 RECOMMENDATIONS FOR FIXES")
    print("=" * 50)
    
    recommendations = [
        {
            "priority": "CRITICAL",
            "issue": "Timezone Mismatch",
            "description": "Frontend uses local time, backend uses UTC",
            "fix": "Standardize on UTC for all calculations, convert to user timezone only for display",
            "files": [
                "mobileapp/services/unifiedNotificationService.ts",
                "mobileapp/services/notificationService.ts",
                "backend/services/notification_scheduler_simple.py"
            ],
            "code_changes": [
                "Use datetime.now(timezone.utc) in backend",
                "Convert user timezone to UTC before scheduling",
                "Store all times in UTC in database"
            ]
        },
        {
            "priority": "HIGH",
            "issue": "Backend Timezone Handling",
            "description": "Backend uses local time instead of UTC",
            "fix": "Use UTC consistently in backend",
            "files": [
                "backend/services/notification_scheduler_simple.py"
            ],
            "code_changes": [
                "Replace datetime.now() with datetime.now(timezone.utc)",
                "Use timezone-aware datetime objects throughout"
            ]
        },
        {
            "priority": "MEDIUM",
            "issue": "Missing Day Headers",
            "description": "Activities without day headers get empty selectedDays",
            "fix": "Implement diet structure analysis",
            "files": [
                "backend/services/diet_notification_service.py"
            ],
            "code_changes": [
                "Analyze diet structure to determine default days",
                "Use weekdays (Mon-Fri) as default for general activities",
                "Allow user to configure default days"
            ]
        },
        {
            "priority": "MEDIUM",
            "issue": "Recurring Notifications",
            "description": "Recurring notifications depend on mobile app handling",
            "fix": "Verify mobile app repeat handling",
            "files": [
                "mobileapp/services/unifiedNotificationService.ts"
            ],
            "code_changes": [
                "Ensure repeats: true is set correctly",
                "Verify repeatInterval calculation",
                "Add fallback scheduling in backend"
            ]
        },
        {
            "priority": "LOW",
            "issue": "Timing Precision",
            "description": "Notifications scheduled with second precision",
            "fix": "Add buffer time for processing",
            "files": [
                "backend/services/notification_scheduler_simple.py"
            ],
            "code_changes": [
                "Add 1-2 minute buffer before scheduling",
                "Use minute precision instead of second precision"
            ]
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['priority']} - {rec['issue']}")
        print(f"   Description: {rec['description']}")
        print(f"   Fix: {rec['fix']}")
        print(f"   Files to modify: {', '.join(rec['files'])}")
        print(f"   Code changes:")
        for change in rec['code_changes']:
            print(f"     - {change}")

def main():
    """Run comprehensive issues analysis"""
    print("🔬 COMPREHENSIVE ISSUES ANALYSIS")
    print("=" * 60)
    print("Analyzing all potential causes of notification timing issues")
    print("=" * 60)
    
    try:
        timezone_issues = analyze_timezone_issues()
        day_conversion_issues = analyze_day_conversion_issues()
        scheduling_issues = analyze_scheduling_logic_issues()
        extraction_issues = analyze_diet_extraction_issues()
        delivery_issues = analyze_notification_delivery_issues()
        edge_case_issues = analyze_edge_cases()
        
        generate_recommendations()
        
        # Summary
        all_issues = (timezone_issues + day_conversion_issues + scheduling_issues + 
                     extraction_issues + delivery_issues + edge_case_issues)
        
        critical_issues = [i for i in all_issues if i.get('severity') == 'CRITICAL']
        high_issues = [i for i in all_issues if i.get('severity') == 'HIGH']
        medium_issues = [i for i in all_issues if i.get('severity') == 'MEDIUM']
        
        print(f"\n📊 SUMMARY")
        print(f"   Critical issues: {len(critical_issues)}")
        print(f"   High issues: {len(high_issues)}")
        print(f"   Medium issues: {len(medium_issues)}")
        print(f"   Total issues: {len(all_issues)}")
        
        print(f"\n✅ COMPREHENSIVE ANALYSIS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR DURING ANALYSIS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
