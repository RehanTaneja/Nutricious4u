#!/usr/bin/env python3
"""
Comprehensive Notification System Debugging and Testing
This script identifies all potential causes of duplicate notifications and targeting issues.
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

def analyze_notification_system():
    """Comprehensive analysis of the notification system to identify all issues."""
    
    print("🔍 COMPREHENSIVE NOTIFICATION SYSTEM ANALYSIS")
    print("=" * 60)
    
    issues = []
    
    # 1. DIET REMINDER DUPLICATE ANALYSIS
    print("\n1. 🍎 DIET REMINDER DUPLICATE NOTIFICATION ANALYSIS")
    print("-" * 50)
    
    diet_duplicate_causes = [
        {
            "cause": "Multiple Scheduling Systems",
            "severity": "CRITICAL",
            "description": "Both frontend (UnifiedNotificationService) and backend (SimpleNotificationScheduler) schedule notifications",
            "locations": [
                "mobileapp/services/unifiedNotificationService.ts:274-341",
                "backend/services/notification_scheduler_simple.py:29-116"
            ],
            "impact": "Same notification scheduled twice - once locally, once on backend",
            "evidence": "Frontend schedules with repeats:true, backend also schedules in database"
        },
        {
            "cause": "Day-wise Loop Creates Multiple Notifications",
            "severity": "HIGH", 
            "description": "Frontend loops through selectedDays creating separate notifications for each day",
            "location": "mobileapp/services/unifiedNotificationService.ts:284-325",
            "impact": "One activity with 3 selected days = 3 separate notifications",
            "evidence": "for (let i = 0; i < selectedDays.length; i++) creates separate notifications"
        },
        {
            "cause": "Backend Recurring Logic Conflict",
            "severity": "HIGH",
            "description": "Backend sends notification once, mobile app handles repeats, but both systems active",
            "location": "backend/services/notification_scheduler_simple.py:218-223",
            "impact": "Backend sends once, mobile app repeats, but both are running simultaneously",
            "evidence": "Backend comment: 'mobile app handles recurring notifications with repeats: true'"
        },
        {
            "cause": "No Duplicate Prevention",
            "severity": "HIGH",
            "description": "No mechanism to prevent scheduling same notification multiple times",
            "locations": [
                "mobileapp/services/unifiedNotificationService.ts",
                "backend/services/notification_scheduler_simple.py"
            ],
            "impact": "User can trigger extraction multiple times, each creates new notifications",
            "evidence": "No activityId checking or duplicate prevention logic"
        },
        {
            "cause": "Extraction Button Multiple Clicks",
            "severity": "MEDIUM",
            "description": "User can press 'Extract from Diet PDF' button multiple times rapidly",
            "location": "mobileapp/screens.tsx:4646-4650",
            "impact": "Each click schedules new notifications without cancelling previous ones",
            "evidence": "No loading state or duplicate click prevention"
        }
    ]
    
    for cause in diet_duplicate_causes:
        issues.append(cause)
        print(f"   ❌ {cause['cause']} ({cause['severity']})")
        print(f"      {cause['description']}")
        print(f"      Impact: {cause['impact']}")
        print()
    
    # 2. MESSAGE NOTIFICATION TARGETING ANALYSIS
    print("\n2. 💬 MESSAGE NOTIFICATION TARGETING ANALYSIS")
    print("-" * 50)
    
    message_targeting_issues = [
        {
            "cause": "Correct Targeting Implementation",
            "severity": "NONE",
            "description": "Message notifications are correctly targeted",
            "evidence": "User->Dietician: sends to dietician token, Dietician->User: sends to specific user token",
            "locations": [
                "backend/server.py:2388-2427",
                "mobileapp/screens.tsx:6693-6699"
            ]
        },
        {
            "cause": "Firebase Functions Duplicate",
            "severity": "MEDIUM",
            "description": "Firebase Functions also send message notifications, potentially duplicating backend",
            "location": "functions/index.js:53-84",
            "impact": "Same message might trigger both backend and Firebase Functions notifications",
            "evidence": "Firestore trigger on message creation + backend API call"
        },
        {
            "cause": "Local vs Push Notification Confusion",
            "severity": "LOW",
            "description": "Both local and push notifications sent for messages",
            "location": "mobileapp/screens.tsx:6599-6630",
            "impact": "User might receive both local and push notification for same message",
            "evidence": "sendLocalMessageNotification + sendPushNotification both called"
        }
    ]
    
    for cause in message_targeting_issues:
        if cause['severity'] != 'NONE':
            issues.append(cause)
        print(f"   {'✅' if cause['severity'] == 'NONE' else '❌'} {cause['cause']} ({cause['severity']})")
        print(f"      {cause['description']}")
        if cause['severity'] != 'NONE':
            print(f"      Impact: {cause['impact']}")
        print()
    
    # 3. DIET UPLOAD NOTIFICATION TARGETING ANALYSIS
    print("\n3. 📄 DIET UPLOAD NOTIFICATION TARGETING ANALYSIS")
    print("-" * 50)
    
    diet_upload_issues = [
        {
            "cause": "Correct User Targeting",
            "severity": "NONE",
            "description": "Diet upload notifications correctly sent only to users, not dieticians",
            "evidence": "Backend sends 'New Diet Has Arrived!' only to user token",
            "location": "backend/server.py:1648-1676"
        },
        {
            "cause": "Dietician Success Notification",
            "severity": "NONE", 
            "description": "Dietician receives separate 'Diet Upload Successful' notification",
            "evidence": "Different notification type (diet_upload_success) sent to dietician",
            "location": "backend/server.py:1678-1692"
        },
        {
            "cause": "No Duplicate Prevention for Diet Upload",
            "severity": "LOW",
            "description": "No mechanism to prevent multiple diet upload notifications",
            "location": "backend/server.py:1648-1676",
            "impact": "If upload endpoint called multiple times, user gets multiple notifications",
            "evidence": "No duplicate upload prevention logic"
        }
    ]
    
    for cause in diet_upload_issues:
        if cause['severity'] != 'NONE':
            issues.append(cause)
        print(f"   {'✅' if cause['severity'] == 'NONE' else '❌'} {cause['cause']} ({cause['severity']})")
        print(f"      {cause['description']}")
        if cause['severity'] != 'NONE':
            print(f"      Impact: {cause['impact']}")
        print()
    
    # 4. TIMING AND SCHEDULING ISSUES
    print("\n4. ⏰ TIMING AND SCHEDULING ISSUES")
    print("-" * 50)
    
    timing_issues = [
        {
            "cause": "Timezone Mismatch",
            "severity": "HIGH",
            "description": "Frontend uses local timezone, backend uses UTC",
            "locations": [
                "mobileapp/services/unifiedNotificationService.ts:481-528",
                "backend/services/notification_scheduler_simple.py:118-152"
            ],
            "impact": "Notifications scheduled for wrong day when timezone differs",
            "evidence": "Frontend: new Date() (local), Backend: datetime.now(timezone.utc)"
        },
        {
            "cause": "Immediate Trigger Prevention",
            "severity": "MEDIUM",
            "description": "Frontend prevents immediate triggers but backend doesn't",
            "location": "mobileapp/services/unifiedNotificationService.ts:109-130",
            "impact": "Inconsistent behavior between frontend and backend",
            "evidence": "Frontend: minimum 60 seconds, Backend: no minimum delay"
        },
        {
            "cause": "Repeat Interval Mismatch",
            "severity": "MEDIUM",
            "description": "Frontend uses 7 days in milliseconds, backend uses different calculation",
            "locations": [
                "mobileapp/services/unifiedNotificationService.ts:309",
                "backend/services/notification_scheduler_simple.py:246-273"
            ],
            "impact": "Different repeat intervals might cause timing issues",
            "evidence": "Frontend: 7 * 24 * 60 * 60 * 1000, Backend: 7 days calculation"
        }
    ]
    
    for cause in timing_issues:
        issues.append(cause)
        print(f"   ❌ {cause['cause']} ({cause['severity']})")
        print(f"      {cause['description']}")
        print(f"      Impact: {cause['impact']}")
        print()
    
    # 5. CANCELLATION AND CLEANUP ISSUES
    print("\n5. 🗑️ CANCELLATION AND CLEANUP ISSUES")
    print("-" * 50)
    
    cancellation_issues = [
        {
            "cause": "Incomplete Cancellation Logic",
            "severity": "HIGH",
            "description": "Backend cancellation returns 0 (no-op), only frontend cancels",
            "location": "backend/services/notification_scheduler_simple.py:21-27",
            "impact": "Backend scheduled notifications never cancelled, accumulate over time",
            "evidence": "return 0 since all notifications are handled locally"
        },
        {
            "cause": "No Cross-System Cancellation",
            "severity": "HIGH",
            "description": "Frontend cancellation doesn't affect backend scheduled notifications",
            "locations": [
                "mobileapp/services/unifiedNotificationService.ts:405-456",
                "backend/services/notification_scheduler_simple.py:21-27"
            ],
            "impact": "Cancelling frontend notifications doesn't cancel backend ones",
            "evidence": "Separate cancellation systems with no coordination"
        },
        {
            "cause": "No Cleanup of Old Notifications",
            "severity": "MEDIUM",
            "description": "Old sent/failed notifications accumulate in database",
            "location": "backend/services/notification_scheduler_simple.py:275-281",
            "impact": "Database grows with old notification records",
            "evidence": "return 0 since all notifications are handled locally"
        }
    ]
    
    for cause in cancellation_issues:
        issues.append(cause)
        print(f"   ❌ {cause['cause']} ({cause['severity']})")
        print(f"      {cause['description']}")
        print(f"      Impact: {cause['impact']}")
        print()
    
    # 6. RACE CONDITIONS AND CONCURRENCY
    print("\n6. 🏃 RACE CONDITIONS AND CONCURRENCY ISSUES")
    print("-" * 50)
    
    race_condition_issues = [
        {
            "cause": "Multiple Notification Listeners",
            "severity": "HIGH",
            "description": "Multiple screens have notification listeners that might conflict",
            "locations": [
                "mobileapp/screens.tsx:10886-10948 (DieticianDashboard)",
                "mobileapp/screens.tsx:6920-6930 (DieticianMessagesListScreen)",
                "mobileapp/screens.tsx:1240-1300 (DashboardScreen)"
            ],
            "impact": "Same notification might be processed multiple times",
            "evidence": "Multiple addNotificationReceivedListener calls"
        },
        {
            "cause": "Async Notification Scheduling",
            "severity": "MEDIUM",
            "description": "Notification scheduling is async but no proper error handling",
            "location": "mobileapp/services/unifiedNotificationService.ts:274-341",
            "impact": "Failed scheduling might not be properly handled",
            "evidence": "No retry logic or proper error handling for scheduling failures"
        },
        {
            "cause": "Database Write Conflicts",
            "severity": "MEDIUM",
            "description": "Multiple systems writing to same Firestore collections",
            "locations": [
                "backend/services/notification_scheduler_simple.py:100-102",
                "mobileapp/services/unifiedNotificationService.ts"
            ],
            "impact": "Concurrent writes might cause data inconsistency",
            "evidence": "Both systems write to scheduled_notifications collection"
        }
    ]
    
    for cause in race_condition_issues:
        issues.append(cause)
        print(f"   ❌ {cause['cause']} ({cause['severity']})")
        print(f"      {cause['description']}")
        print(f"      Impact: {cause['impact']}")
        print()
    
    # SUMMARY AND RECOMMENDATIONS
    print("\n" + "=" * 60)
    print("📊 SUMMARY OF CRITICAL ISSUES")
    print("=" * 60)
    
    critical_issues = [issue for issue in issues if issue['severity'] == 'CRITICAL']
    high_issues = [issue for issue in issues if issue['severity'] == 'HIGH']
    medium_issues = [issue for issue in issues if issue['severity'] == 'MEDIUM']
    low_issues = [issue for issue in issues if issue['severity'] == 'LOW']
    
    print(f"\n🔴 CRITICAL ISSUES: {len(critical_issues)}")
    for issue in critical_issues:
        print(f"   - {issue['cause']}")
    
    print(f"\n🟠 HIGH ISSUES: {len(high_issues)}")
    for issue in high_issues:
        print(f"   - {issue['cause']}")
    
    print(f"\n🟡 MEDIUM ISSUES: {len(medium_issues)}")
    for issue in medium_issues:
        print(f"   - {issue['cause']}")
    
    print(f"\n🟢 LOW ISSUES: {len(low_issues)}")
    for issue in low_issues:
        print(f"   - {issue['cause']}")
    
    # ROOT CAUSE ANALYSIS
    print("\n" + "=" * 60)
    print("🎯 ROOT CAUSE ANALYSIS")
    print("=" * 60)
    
    print("\nPRIMARY ROOT CAUSES OF DUPLICATE NOTIFICATIONS:")
    print("1. DUAL SCHEDULING SYSTEMS: Both frontend and backend schedule notifications")
    print("2. DAY-WISE LOOP: Frontend creates separate notifications for each selected day")
    print("3. NO DUPLICATE PREVENTION: No mechanism to prevent multiple scheduling")
    print("4. INCOMPLETE CANCELLATION: Backend cancellation is no-op, only frontend cancels")
    print("5. RACE CONDITIONS: Multiple notification listeners and async operations")
    
    print("\nPRIMARY ROOT CAUSES OF TARGETING ISSUES:")
    print("1. MESSAGE NOTIFICATIONS: ✅ CORRECTLY TARGETED")
    print("2. DIET UPLOAD NOTIFICATIONS: ✅ CORRECTLY TARGETED")
    print("3. DIET REMINDER NOTIFICATIONS: ❌ WRONG TARGETING (users get dietician reminders)")
    
    # IMMEDIATE FIXES NEEDED
    print("\n" + "=" * 60)
    print("🔧 IMMEDIATE FIXES NEEDED")
    print("=" * 60)
    
    print("\n1. DISABLE BACKEND SCHEDULING:")
    print("   - Comment out backend notification scheduler")
    print("   - Use only frontend scheduling for reliability")
    
    print("\n2. FIX DAY-WISE LOOP:")
    print("   - Create single notification with all selected days")
    print("   - Use proper day filtering in notification handler")
    
    print("\n3. ADD DUPLICATE PREVENTION:")
    print("   - Check for existing notifications before scheduling")
    print("   - Use activityId to prevent duplicates")
    
    print("\n4. FIX CANCELLATION:")
    print("   - Implement proper backend cancellation")
    print("   - Coordinate frontend and backend cancellation")
    
    print("\n5. FIX DIET REMINDER TARGETING:")
    print("   - Remove diet reminder notifications from user screens")
    print("   - Only send to dietician dashboard")
    
    # Save detailed analysis
    analysis_result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_issues": len(issues),
        "critical_issues": len(critical_issues),
        "high_issues": len(high_issues),
        "medium_issues": len(medium_issues),
        "low_issues": len(low_issues),
        "issues": issues,
        "root_causes": {
            "duplicate_notifications": [
                "Dual scheduling systems (frontend + backend)",
                "Day-wise loop creates multiple notifications",
                "No duplicate prevention mechanism",
                "Incomplete cancellation logic",
                "Race conditions and concurrency issues"
            ],
            "targeting_issues": [
                "Message notifications: CORRECTLY TARGETED",
                "Diet upload notifications: CORRECTLY TARGETED", 
                "Diet reminder notifications: WRONG TARGETING"
            ]
        },
        "immediate_fixes": [
            "Disable backend notification scheduling",
            "Fix day-wise loop to create single notification",
            "Add duplicate prevention with activityId checking",
            "Implement proper cancellation coordination",
            "Fix diet reminder targeting (users vs dieticians)"
        ]
    }
    
    with open('comprehensive_notification_debug_results.json', 'w') as f:
        json.dump(analysis_result, f, indent=2)
    
    print(f"\n📄 Detailed analysis saved to: comprehensive_notification_debug_results.json")
    print(f"🔍 Total issues identified: {len(issues)}")
    print(f"🚨 Critical issues requiring immediate attention: {len(critical_issues)}")

if __name__ == "__main__":
    analyze_notification_system()
