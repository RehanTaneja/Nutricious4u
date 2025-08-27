#!/usr/bin/env python3
"""
Notification Scheduling Analysis Test
Analyzes the day and time scheduling logic for diet reminders
"""

import json
from datetime import datetime, timedelta
import sys

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def print_success(message):
    print(f"✅ {message}")

def analyze_calculate_diet_next_occurrence():
    """Analyze the calculateDietNextOccurrence logic"""
    print_header("Analyzing calculateDietNextOccurrence Logic")
    
    # Simulate the JavaScript logic
    def calculate_diet_next_occurrence(hours, minutes, day_of_week=None):
        now = datetime.now()
        target_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        
        if day_of_week is not None:
            # Specific day of week
            current_day = now.weekday()  # Monday=0, Sunday=6
            target_day = (day_of_week + 1) % 7  # Convert Monday=0 to Sunday=0
            
            days_to_add = target_day - current_day
            if days_to_add <= 0:
                days_to_add += 7  # Next week if today or past
            
            occurrence = now + timedelta(days=days_to_add)
            occurrence = occurrence.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            
            # If it's today and time hasn't passed, use today
            if days_to_add == 7 and target_time > now:
                return target_time
            
            return occurrence
        else:
            # Daily occurrence
            if target_time > now:
                return target_time  # Today
            else:
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    # Test scenarios
    test_cases = [
        {"hours": 16, "minutes": 0, "day_of_week": 0, "description": "Monday 4:00 PM"},
        {"hours": 16, "minutes": 0, "day_of_week": 1, "description": "Tuesday 4:00 PM"},
        {"hours": 16, "minutes": 0, "day_of_week": 2, "description": "Wednesday 4:00 PM"},
        {"hours": 16, "minutes": 0, "day_of_week": 3, "description": "Thursday 4:00 PM"},
        {"hours": 16, "minutes": 0, "day_of_week": 4, "description": "Friday 4:00 PM"},
        {"hours": 16, "minutes": 0, "day_of_week": 5, "description": "Saturday 4:00 PM"},
        {"hours": 16, "minutes": 0, "day_of_week": 6, "description": "Sunday 4:00 PM"},
    ]
    
    current_time = datetime.now()
    print_info(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Current day: {current_time.strftime('%A')} (weekday: {current_time.weekday()})")
    print()
    
    for test_case in test_cases:
        hours = test_case["hours"]
        minutes = test_case["minutes"]
        day_of_week = test_case["day_of_week"]
        description = test_case["description"]
        
        next_occurrence = calculate_diet_next_occurrence(hours, minutes, day_of_week)
        time_diff = next_occurrence - current_time
        
        print_info(f"{description}:")
        print_info(f"  Next occurrence: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S')}")
        print_info(f"  Time until trigger: {time_diff}")
        
        # Check if this would trigger immediately
        if time_diff.total_seconds() < 3600:  # Less than 1 hour
            print_warning(f"  ⚠️  Would trigger within 1 hour!")
        
        print()

def analyze_scheduling_logic():
    """Analyze the scheduling logic for potential issues"""
    print_header("Analyzing Scheduling Logic")
    
    print_info("Analyzing the scheduleDietNotifications function:")
    print_info("1. For each notification in the array")
    print_info("2. For each selected day")
    print_info("3. Calculate next occurrence")
    print_info("4. Schedule with repeats: true, repeatInterval: 7 days")
    print()
    
    # Identify potential issues
    issues = []
    
    # Issue 1: Multiple notifications for same time on different days
    issues.append({
        "type": "Multiple Notifications",
        "description": "If selectedDays includes multiple days, multiple notifications are scheduled for the same time",
        "impact": "User receives multiple notifications for the same activity",
        "example": "4:00 PM notification scheduled for Monday, Tuesday, Wednesday = 3 notifications"
    })
    
    # Issue 2: Immediate scheduling
    issues.append({
        "type": "Immediate Scheduling",
        "description": "If the calculated time is in the past or very near future, notification might trigger immediately",
        "impact": "User receives notification right after extraction",
        "example": "Extract at 4:30 PM, but notification was scheduled for 4:00 PM today"
    })
    
    # Issue 3: Day calculation logic
    issues.append({
        "type": "Day Calculation",
        "description": "The day conversion logic might have edge cases",
        "impact": "Notifications scheduled for wrong days",
        "example": "Monday=0 conversion to Sunday=0 might cause issues"
    })
    
    # Issue 4: Repeat interval
    issues.append({
        "type": "Repeat Interval",
        "description": "7-day repeat interval might cause overlapping notifications",
        "impact": "Notifications might repeat at unexpected times",
        "example": "Weekly repetition might not align with intended schedule"
    })
    
    for i, issue in enumerate(issues, 1):
        print_warning(f"Issue {i}: {issue['type']}")
        print_info(f"  Description: {issue['description']}")
        print_info(f"  Impact: {issue['impact']}")
        print_info(f"  Example: {issue['example']}")
        print()

def analyze_user_scenario():
    """Analyze the specific user scenario"""
    print_header("Analyzing User Scenario")
    
    print_info("User reported:")
    print_info("- Received notification at 4:00 PM (correct)")
    print_info("- Received same notification 36 minutes later")
    print_info("- This happened right after pressing 'Extract from PDF'")
    print()
    
    # Analyze possible causes
    causes = [
        {
            "cause": "Immediate Trigger",
            "description": "Notification was scheduled for a time that had already passed today",
            "explanation": "If extraction happened at 4:36 PM, but notification was scheduled for 4:00 PM today, it would trigger immediately"
        },
        {
            "cause": "Multiple Day Scheduling",
            "description": "Same notification scheduled for multiple days",
            "explanation": "If selectedDays includes multiple days, the same notification gets scheduled multiple times"
        },
        {
            "cause": "Cancellation Not Working",
            "description": "Old notifications weren't properly cancelled",
            "explanation": "Previous notifications from earlier extractions are still active"
        },
        {
            "cause": "Time Calculation Error",
            "description": "Day/time calculation logic error",
            "explanation": "The calculateDietNextOccurrence function might have a bug"
        }
    ]
    
    for i, cause in enumerate(causes, 1):
        print_warning(f"Possible Cause {i}: {cause['cause']}")
        print_info(f"  Description: {cause['description']}")
        print_info(f"  Explanation: {cause['explanation']}")
        print()

def analyze_code_issues():
    """Analyze specific code issues"""
    print_header("Code Analysis - Potential Issues")
    
    issues = []
    
    # Issue 1: Day conversion logic
    issues.append({
        "file": "unifiedNotificationService.ts",
        "line": "calculateDietNextOccurrence",
        "issue": "Day conversion logic: targetDay = (dayOfWeek + 1) % 7",
        "problem": "This converts Monday=0 to Sunday=0, but might cause confusion",
        "impact": "Notifications might be scheduled for wrong days"
    })
    
    # Issue 2: Immediate scheduling check
    issues.append({
        "file": "unifiedNotificationService.ts",
        "line": "scheduleNotification",
        "issue": "secondsUntilTrigger = Math.max(1, ...)",
        "problem": "Minimum 1 second delay, but no maximum check",
        "impact": "Notifications could trigger immediately if time has passed"
    })
    
    # Issue 3: Multiple notifications for same activity
    issues.append({
        "file": "unifiedNotificationService.ts",
        "line": "scheduleDietNotifications",
        "issue": "for (const dayOfWeek of selectedDays)",
        "problem": "Creates multiple notifications for same activity on different days",
        "impact": "User gets multiple notifications for same activity"
    })
    
    # Issue 4: Repeat interval
    issues.append({
        "file": "unifiedNotificationService.ts",
        "line": "scheduleDietNotifications",
        "issue": "repeatInterval: 7 * 24 * 60 * 60",
        "problem": "7-day repeat might not align with intended schedule",
        "impact": "Notifications might repeat at unexpected times"
    })
    
    for i, issue in enumerate(issues, 1):
        print_warning(f"Code Issue {i}:")
        print_info(f"  File: {issue['file']}")
        print_info(f"  Line: {issue['line']}")
        print_info(f"  Issue: {issue['issue']}")
        print_info(f"  Problem: {issue['problem']}")
        print_info(f"  Impact: {issue['impact']}")
        print()

def provide_recommendations():
    """Provide recommendations to fix the issues"""
    print_header("Recommendations")
    
    recommendations = [
        {
            "priority": "HIGH",
            "issue": "Immediate notification trigger",
            "solution": "Add check to prevent scheduling notifications for times that have already passed today",
            "code": "if (nextOccurrence <= new Date()) { nextOccurrence.setDate(nextOccurrence.getDate() + 7); }"
        },
        {
            "priority": "MEDIUM",
            "issue": "Multiple notifications for same activity",
            "solution": "Consider grouping notifications by activity and time, not by day",
            "code": "Create one notification per activity with proper day filtering"
        },
        {
            "priority": "MEDIUM",
            "issue": "Day calculation logic",
            "solution": "Simplify day calculation logic to avoid confusion",
            "code": "Use consistent day numbering (0=Sunday or 0=Monday)"
        },
        {
            "priority": "LOW",
            "issue": "Repeat interval",
            "solution": "Verify that 7-day repeat aligns with intended schedule",
            "code": "Test weekly repetition to ensure it works as expected"
        }
    ]
    
    for rec in recommendations:
        priority_color = "🔴" if rec["priority"] == "HIGH" else "🟡" if rec["priority"] == "MEDIUM" else "🟢"
        print(f"{priority_color} {rec['priority']} Priority: {rec['issue']}")
        print_info(f"  Solution: {rec['solution']}")
        print_info(f"  Code: {rec['code']}")
        print()

def main():
    """Main analysis function"""
    print_header("Notification Scheduling Analysis")
    print_info("Analyzing diet reminder scheduling logic for timing issues")
    
    analyze_calculate_diet_next_occurrence()
    analyze_scheduling_logic()
    analyze_user_scenario()
    analyze_code_issues()
    provide_recommendations()
    
    print_header("Summary")
    print_warning("ISSUES DETECTED:")
    print_info("1. Immediate notification trigger possible")
    print_info("2. Multiple notifications for same activity")
    print_info("3. Day calculation logic complexity")
    print_info("4. Potential repeat interval issues")
    print()
    print_info("The 36-minute delay issue is likely caused by:")
    print_info("- Notification scheduled for a time that had already passed")
    print_info("- Multiple notifications being scheduled for the same activity")
    print_info("- Cancellation not working properly")

if __name__ == "__main__":
    main()
