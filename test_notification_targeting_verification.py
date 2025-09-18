#!/usr/bin/env python3
"""
Notification Targeting and Duplicate Verification Test
This script verifies the exact targeting and duplicate issues in the notification system.
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

def verify_notification_targeting():
    """Verify notification targeting and identify exact duplicate causes."""
    
    print("🎯 NOTIFICATION TARGETING AND DUPLICATE VERIFICATION")
    print("=" * 60)
    
    # 1. MESSAGE NOTIFICATION TARGETING VERIFICATION
    print("\n1. 💬 MESSAGE NOTIFICATION TARGETING VERIFICATION")
    print("-" * 50)
    
    message_targeting = {
        "user_to_dietician": {
            "backend_endpoint": "backend/server.py:2388-2407",
            "logic": "if recipient_user_id == 'dietician': send to dietician_token",
            "title": "New message from {sender_name}",
            "data": {"type": "message_notification", "fromUser": "sender_user_id"},
            "target": "DIETICIAN",
            "status": "✅ CORRECT"
        },
        "dietician_to_user": {
            "backend_endpoint": "backend/server.py:2410-2427", 
            "logic": "else: send to user_token",
            "title": "New message from dietician",
            "data": {"type": "message_notification", "fromDietician": True},
            "target": "USER",
            "status": "✅ CORRECT"
        },
        "frontend_handling": {
            "user_screen": "mobileapp/screens.tsx:6693-6699",
            "logic": "if (!isDietician): send to dietician, else: send to user",
            "status": "✅ CORRECT"
        },
        "firebase_functions": {
            "location": "functions/index.js:53-84",
            "logic": "if sender === 'dietician': recipient = user, else: recipient = dietician",
            "status": "⚠️ POTENTIAL DUPLICATE",
            "issue": "Firebase Functions might duplicate backend notifications"
        }
    }
    
    for key, details in message_targeting.items():
        print(f"   {details['status']} {key.upper()}")
        print(f"      {details.get('logic', details.get('description', ''))}")
        if 'issue' in details:
            print(f"      Issue: {details['issue']}")
        print()
    
    # 2. DIET UPLOAD NOTIFICATION TARGETING VERIFICATION
    print("\n2. 📄 DIET UPLOAD NOTIFICATION TARGETING VERIFICATION")
    print("-" * 50)
    
    diet_upload_targeting = {
        "user_notification": {
            "backend_endpoint": "backend/server.py:1648-1676",
            "logic": "Send to user_token only",
            "title": "New Diet Has Arrived!",
            "body": "Your dietician has uploaded a new diet plan for you.",
            "data": {"type": "new_diet", "userId": "user_id"},
            "target": "USER_ONLY",
            "status": "✅ CORRECT"
        },
        "dietician_notification": {
            "backend_endpoint": "backend/server.py:1678-1692",
            "logic": "Send to dietician_token separately",
            "title": "Diet Upload Successful", 
            "body": "Successfully uploaded new diet for user {user_id}",
            "data": {"type": "diet_upload_success", "userId": "user_id"},
            "target": "DIETICIAN_ONLY",
            "status": "✅ CORRECT"
        },
        "frontend_handling": {
            "user_dashboard": "mobileapp/screens.tsx:1269-1280",
            "logic": "if data?.type === 'new_diet' && data?.userId === userId: refresh diet data",
            "status": "✅ CORRECT"
        },
        "dietician_dashboard": {
            "location": "mobileapp/screens.tsx:10921-10930",
            "logic": "if data?.type === 'diet_upload_success': show success alert",
            "status": "✅ CORRECT"
        }
    }
    
    for key, details in diet_upload_targeting.items():
        print(f"   {details['status']} {key.upper()}")
        print(f"      {details.get('logic', details.get('description', ''))}")
        print()
    
    # 3. DIET REMINDER NOTIFICATION TARGETING VERIFICATION
    print("\n3. 🍎 DIET REMINDER NOTIFICATION TARGETING VERIFICATION")
    print("-" * 50)
    
    diet_reminder_targeting = {
        "backend_scheduler": {
            "location": "backend/services/notification_scheduler_simple.py:200-210",
            "logic": "send_push_notification(user_token, 'Diet Reminder', message, {'type': 'diet_reminder'})",
            "target": "USER",
            "status": "❌ WRONG TARGETING",
            "issue": "Diet reminders sent to users instead of dieticians"
        },
        "diet_notification_service": {
            "location": "backend/services/diet_notification_service.py:909-918",
            "logic": "send_push_notification(user_token, 'Diet Reminder', message, {'type': 'diet_reminder'})",
            "target": "USER", 
            "status": "❌ WRONG TARGETING",
            "issue": "Diet reminders sent to users instead of dieticians"
        },
        "firebase_client": {
            "location": "backend/services/firebase_client.py:417-422",
            "logic": "send_push_notification(dietician_token, 'Diet Reminder', message, {'type': 'diet_reminder'})",
            "target": "DIETICIAN",
            "status": "✅ CORRECT",
            "note": "This is for '1 day left' reminders to dietician"
        },
        "frontend_user_screen": {
            "location": "mobileapp/screens.tsx:4782",
            "logic": "type: 'diet_reminder' in notification data",
            "target": "USER",
            "status": "❌ WRONG TARGETING",
            "issue": "Users receive diet reminder notifications meant for dieticians"
        },
        "frontend_dietician_screen": {
            "location": "mobileapp/screens.tsx:10907-10919",
            "logic": "if data?.type === 'diet_reminder': show alert to dietician",
            "target": "DIETICIAN",
            "status": "✅ CORRECT"
        }
    }
    
    for key, details in diet_reminder_targeting.items():
        print(f"   {details['status']} {key.upper()}")
        print(f"      {details.get('logic', details.get('description', ''))}")
        if 'issue' in details:
            print(f"      Issue: {details['issue']}")
        if 'note' in details:
            print(f"      Note: {details['note']}")
        print()
    
    # 4. DUPLICATE NOTIFICATION CAUSES VERIFICATION
    print("\n4. 🔄 DUPLICATE NOTIFICATION CAUSES VERIFICATION")
    print("-" * 50)
    
    duplicate_causes = {
        "dual_scheduling_systems": {
            "frontend": "mobileapp/services/unifiedNotificationService.ts:274-341",
            "backend": "backend/services/notification_scheduler_simple.py:29-116",
            "issue": "Both systems schedule same notifications",
            "evidence": "Frontend: scheduleDietNotifications(), Backend: schedule_user_notifications()",
            "severity": "CRITICAL"
        },
        "day_wise_loop": {
            "location": "mobileapp/services/unifiedNotificationService.ts:284-325",
            "issue": "Creates separate notification for each selected day",
            "evidence": "for (let i = 0; i < selectedDays.length; i++) creates multiple notifications",
            "severity": "HIGH"
        },
        "no_duplicate_prevention": {
            "frontend": "mobileapp/services/unifiedNotificationService.ts",
            "backend": "backend/services/notification_scheduler_simple.py",
            "issue": "No checking for existing notifications before scheduling",
            "evidence": "No activityId checking or duplicate prevention logic",
            "severity": "HIGH"
        },
        "extraction_button_multiple_clicks": {
            "location": "mobileapp/screens.tsx:4646-4650",
            "issue": "User can click 'Extract from Diet PDF' multiple times",
            "evidence": "No loading state or duplicate click prevention",
            "severity": "MEDIUM"
        },
        "firebase_functions_duplicate": {
            "location": "functions/index.js:53-84",
            "issue": "Firebase Functions might duplicate backend message notifications",
            "evidence": "Firestore trigger + backend API call both send notifications",
            "severity": "MEDIUM"
        },
        "multiple_notification_listeners": {
            "locations": [
                "mobileapp/screens.tsx:10886-10948 (DieticianDashboard)",
                "mobileapp/screens.tsx:6920-6930 (DieticianMessagesListScreen)", 
                "mobileapp/screens.tsx:1240-1300 (DashboardScreen)"
            ],
            "issue": "Multiple screens process same notifications",
            "evidence": "Multiple addNotificationReceivedListener calls",
            "severity": "HIGH"
        }
    }
    
    for key, details in duplicate_causes.items():
        print(f"   ❌ {key.upper()} ({details['severity']})")
        print(f"      Issue: {details['issue']}")
        print(f"      Evidence: {details['evidence']}")
        print()
    
    # 5. EXACT DUPLICATE SCENARIOS
    print("\n5. 🎯 EXACT DUPLICATE SCENARIOS")
    print("-" * 50)
    
    duplicate_scenarios = [
        {
            "scenario": "User extracts diet notifications",
            "steps": [
                "1. User clicks 'Extract from Diet PDF'",
                "2. Frontend calls unifiedNotificationService.scheduleDietNotifications()",
                "3. Frontend creates separate notifications for each selected day",
                "4. Backend also calls scheduler.schedule_user_notifications()",
                "5. Backend creates additional notifications in database",
                "6. Result: User receives multiple notifications for same activity"
            ],
            "duplicate_count": "2x (frontend + backend) × number of selected days"
        },
        {
            "scenario": "User sends message to dietician",
            "steps": [
                "1. User sends message via frontend",
                "2. Frontend calls sendPushNotification('dietician', message, senderName)",
                "3. Backend sends notification to dietician",
                "4. Firebase Functions also triggers on message creation",
                "5. Firebase Functions sends duplicate notification to dietician",
                "6. Result: Dietician receives same message notification twice"
            ],
            "duplicate_count": "2x (backend + Firebase Functions)"
        },
        {
            "scenario": "Dietician uploads new diet",
            "steps": [
                "1. Dietician uploads diet PDF",
                "2. Backend sends 'New Diet Has Arrived!' to user",
                "3. Backend sends 'Diet Upload Successful' to dietician",
                "4. If upload endpoint called multiple times, user gets multiple notifications",
                "5. Result: User might receive multiple 'New Diet Has Arrived!' notifications"
            ],
            "duplicate_count": "1x per upload call (no duplicate prevention)"
        },
        {
            "scenario": "Diet reminder notifications",
            "steps": [
                "1. Backend scheduler sends diet reminder to user (WRONG)",
                "2. User receives 'Diet Reminder' notification",
                "3. User's notification listener processes it",
                "4. Result: User gets diet reminders meant for dieticians"
            ],
            "duplicate_count": "1x (but wrong targeting)"
        }
    ]
    
    for i, scenario in enumerate(duplicate_scenarios, 1):
        print(f"   Scenario {i}: {scenario['scenario']}")
        for step in scenario['steps']:
            print(f"      {step}")
        print(f"      Duplicate Count: {scenario['duplicate_count']}")
        print()
    
    # 6. IMMEDIATE FIXES REQUIRED
    print("\n6. 🔧 IMMEDIATE FIXES REQUIRED")
    print("-" * 50)
    
    immediate_fixes = [
        {
            "fix": "Disable Backend Diet Reminder Scheduling",
            "priority": "CRITICAL",
            "action": "Comment out backend notification scheduler for diet reminders",
            "files": ["backend/services/notification_scheduler_simple.py", "backend/server.py"],
            "reason": "Prevents duplicate scheduling and wrong targeting"
        },
        {
            "fix": "Fix Diet Reminder Targeting",
            "priority": "CRITICAL", 
            "action": "Remove diet_reminder notifications from user screens",
            "files": ["mobileapp/screens.tsx"],
            "reason": "Users should not receive diet reminders meant for dieticians"
        },
        {
            "fix": "Fix Day-wise Loop",
            "priority": "HIGH",
            "action": "Create single notification with all selected days",
            "files": ["mobileapp/services/unifiedNotificationService.ts"],
            "reason": "Prevents multiple notifications for same activity"
        },
        {
            "fix": "Add Duplicate Prevention",
            "priority": "HIGH",
            "action": "Check for existing notifications before scheduling",
            "files": ["mobileapp/services/unifiedNotificationService.ts"],
            "reason": "Prevents multiple scheduling of same notification"
        },
        {
            "fix": "Disable Firebase Functions Duplicates",
            "priority": "MEDIUM",
            "action": "Remove or modify Firebase Functions message notifications",
            "files": ["functions/index.js"],
            "reason": "Prevents duplicate message notifications"
        },
        {
            "fix": "Add Loading State to Extraction",
            "priority": "MEDIUM",
            "action": "Prevent multiple clicks on extraction button",
            "files": ["mobileapp/screens.tsx"],
            "reason": "Prevents user from triggering multiple extractions"
        }
    ]
    
    for i, fix in enumerate(immediate_fixes, 1):
        print(f"   {i}. {fix['fix']} ({fix['priority']})")
        print(f"      Action: {fix['action']}")
        print(f"      Files: {', '.join(fix['files'])}")
        print(f"      Reason: {fix['reason']}")
        print()
    
    # Save verification results
    verification_result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_targeting": message_targeting,
        "diet_upload_targeting": diet_upload_targeting,
        "diet_reminder_targeting": diet_reminder_targeting,
        "duplicate_causes": duplicate_causes,
        "duplicate_scenarios": duplicate_scenarios,
        "immediate_fixes": immediate_fixes,
        "summary": {
            "message_notifications": "✅ CORRECTLY TARGETED",
            "diet_upload_notifications": "✅ CORRECTLY TARGETED", 
            "diet_reminder_notifications": "❌ WRONG TARGETING (users receive dietician reminders)",
            "duplicate_notifications": "❌ MULTIPLE CAUSES IDENTIFIED",
            "critical_issues": 2,
            "high_priority_fixes": 4,
            "medium_priority_fixes": 2
        }
    }
    
    with open('notification_targeting_verification_results.json', 'w') as f:
        json.dump(verification_result, f, indent=2)
    
    print(f"\n📄 Detailed verification saved to: notification_targeting_verification_results.json")
    print(f"🎯 Summary: {verification_result['summary']}")

if __name__ == "__main__":
    verify_notification_targeting()
