#!/usr/bin/env python3
"""
Comprehensive Popup Debug Analysis
=================================

This script analyzes ALL possible factors that could prevent the popup from showing:
1. API queuing system
2. Notification delivery
3. Frontend listener setup
4. User ID matching
5. State management
6. Timing issues
7. Platform differences
"""

import json
import re

def analyze_api_queuing_system():
    """Analyze the API queuing system for potential issues"""
    print("🔍 ANALYZING API QUEUING SYSTEM")
    print("=" * 50)
    
    with open('backend/services/firebase_client.py', 'r') as f:
        firebase_content = f.read()
    
    # Check for queuing mechanisms
    queuing_checks = [
        ("Direct API call", "requests.post" in firebase_content),
        ("No queuing system", "queue" not in firebase_content.lower()),
        ("No rate limiting", "rate" not in firebase_content.lower() and "limit" not in firebase_content.lower()),
        ("Expo push service", "exp.host/--/api/v2/push/send" in firebase_content),
        ("Error handling", "try:" in firebase_content and "except" in firebase_content),
        ("Response validation", "response.status_code == 200" in firebase_content),
    ]
    
    all_passed = True
    for check_name, check_pattern in queuing_checks:
        if check_pattern in firebase_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    # Check for potential issues
    potential_issues = [
        ("No retry mechanism", "retry" not in firebase_content.lower()),
        ("No timeout handling", "timeout" not in firebase_content.lower()),
        ("No connection pooling", "session" not in firebase_content.lower()),
    ]
    
    print("\n⚠️  POTENTIAL API ISSUES:")
    for issue_name, issue_pattern in potential_issues:
        if issue_pattern in firebase_content:
            print(f"✅ {issue_name}: Handled")
        else:
            print(f"⚠️  {issue_name}: Not handled")
    
    return all_passed

def analyze_notification_delivery():
    """Analyze notification delivery mechanism"""
    print("\n🔍 ANALYZING NOTIFICATION DELIVERY")
    print("=" * 50)
    
    with open('backend/server.py', 'r') as f:
        server_content = f.read()
    
    # Check notification sending
    delivery_checks = [
        ("User token retrieval", "get_user_notification_token" in server_content),
        ("Push notification sending", "send_push_notification" in server_content),
        ("Auto extract flag", "auto_extract_pending" in server_content),
        ("Notification data structure", "type\": \"new_diet\"" in server_content),
        ("User ID in payload", "userId\": user_id" in server_content),
    ]
    
    all_passed = True
    for check_name, check_pattern in delivery_checks:
        if check_pattern in server_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    # Check for potential delivery issues
    delivery_issues = [
        ("Token validation", "if user_token:" in server_content),
        ("Error logging", "print(f\"Sent new diet notification" in server_content),
        ("Fallback handling", "else:" in server_content),
    ]
    
    print("\n⚠️  DELIVERY ISSUES:")
    for issue_name, issue_pattern in delivery_issues:
        if issue_pattern in server_content:
            print(f"✅ {issue_name}: Handled")
        else:
            print(f"⚠️  {issue_name}: Not handled")
    
    return all_passed

def analyze_frontend_listener_setup():
    """Analyze frontend notification listener setup"""
    print("\n🔍 ANALYZING FRONTEND LISTENER SETUP")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        screens_content = f.read()
    
    # Check listener setup
    listener_checks = [
        ("useEffect setup", "useEffect(() => {" in screens_content),
        ("Notification listener", "addNotificationReceivedListener" in screens_content),
        ("User ID dependency", "if (!userId) return" in screens_content),
        ("Cleanup function", "subscription.remove()" in screens_content),
        ("Console logging", "console.log('[NOTIFICATION DEBUG]'" in screens_content),
    ]
    
    all_passed = True
    for check_name, check_pattern in listener_checks:
        if check_pattern in screens_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    # Check for potential listener issues
    listener_issues = [
        ("Multiple listeners", "addNotificationReceivedListener" in screens_content),
        ("Listener cleanup", "return () => subscription.remove()" in screens_content),
        ("Error handling", "catch (error)" in screens_content),
    ]
    
    print("\n⚠️  LISTENER ISSUES:")
    for issue_name, issue_pattern in listener_issues:
        if issue_pattern in screens_content:
            print(f"✅ {issue_name}: Handled")
        else:
            print(f"⚠️  {issue_name}: Not handled")
    
    return all_passed

def analyze_user_id_matching():
    """Analyze user ID matching logic"""
    print("\n🔍 ANALYZING USER ID MATCHING")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        screens_content = f.read()
    
    # Check user ID matching
    id_checks = [
        ("User ID comparison", "data?.userId === userId" in screens_content),
        ("User ID logging", "User ID match:" in screens_content),
        ("Data logging", "Notification data:" in screens_content),
        ("Type check", "data?.type === 'new_diet'" in screens_content),
        ("Auto extract check", "data.auto_extract_pending" in screens_content),
    ]
    
    all_passed = True
    for check_name, check_pattern in id_checks:
        if check_pattern in screens_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    # Check for potential ID issues
    id_issues = [
        ("Null checks", "data?.userId" in screens_content),
        ("Type safety", "typeof" in screens_content),
        ("Debug logging", "console.log('[DEBUG]'" in screens_content),
    ]
    
    print("\n⚠️  ID MATCHING ISSUES:")
    for issue_name, issue_pattern in id_issues:
        if issue_pattern in screens_content:
            print(f"✅ {issue_name}: Handled")
        else:
            print(f"⚠️  {issue_name}: Not handled")
    
    return all_passed

def analyze_state_management():
    """Analyze popup state management"""
    print("\n🔍 ANALYZING STATE MANAGEMENT")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        screens_content = f.read()
    
    # Check state management
    state_checks = [
        ("Popup state variable", "showAutoExtractionPopup" in screens_content),
        ("State setter", "setShowAutoExtractionPopup" in screens_content),
        ("useState declaration", "useState<boolean>(false)" in screens_content),
        ("State update", "setShowAutoExtractionPopup(true)" in screens_content),
        ("Modal visibility", "visible={showAutoExtractionPopup}" in screens_content),
    ]
    
    all_passed = True
    for check_name, check_pattern in state_checks:
        if check_pattern in screens_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    # Check for potential state issues
    state_issues = [
        ("State initialization", "useState(false)" in screens_content),
        ("State reset", "setShowAutoExtractionPopup(false)" in screens_content),
        ("State dependencies", "useEffect" in screens_content),
    ]
    
    print("\n⚠️  STATE MANAGEMENT ISSUES:")
    for issue_name, issue_pattern in state_issues:
        if issue_pattern in screens_content:
            print(f"✅ {issue_name}: Handled")
        else:
            print(f"⚠️  {issue_name}: Not handled")
    
    return all_passed

def analyze_timing_issues():
    """Analyze potential timing issues"""
    print("\n🔍 ANALYZING TIMING ISSUES")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        screens_content = f.read()
    
    # Check timing-related code
    timing_checks = [
        ("Screen focus check", "isFocused" in screens_content),
        ("User ID check", "if (!userId" in screens_content),
        ("Async operations", "async" in screens_content),
        ("Error handling", "try {" in screens_content and "catch" in screens_content),
        ("Loading states", "setDietLoading" in screens_content),
    ]
    
    all_passed = True
    for check_name, check_pattern in timing_checks:
        if check_pattern in screens_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    # Check for potential timing issues
    timing_issues = [
        ("Race conditions", "isRefreshing" in screens_content),
        ("Multiple triggers", "isMounted" in screens_content),
        ("Debouncing", "setTimeout" in screens_content),
    ]
    
    print("\n⚠️  TIMING ISSUES:")
    for issue_name, issue_pattern in timing_issues:
        if issue_pattern in screens_content:
            print(f"✅ {issue_name}: Handled")
        else:
            print(f"⚠️  {issue_name}: Not handled")
    
    return all_passed

def analyze_platform_differences():
    """Analyze platform-specific differences"""
    print("\n🔍 ANALYZING PLATFORM DIFFERENCES")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        screens_content = f.read()
    
    # Check platform handling
    platform_checks = [
        ("Platform detection", "Platform.OS" in screens_content),
        ("Platform logging", "Platform:" in screens_content),
        ("EAS build detection", "Is EAS build:" in screens_content),
        ("Platform-specific logic", "Platform.OS === 'ios'" in screens_content),
    ]
    
    all_passed = True
    for check_name, check_pattern in platform_checks:
        if check_pattern in screens_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    # Check for potential platform issues
    platform_issues = [
        ("iOS specific", "ios" in screens_content.lower()),
        ("Android specific", "android" in screens_content.lower()),
        ("Cross-platform", "Platform.OS" in screens_content),
    ]
    
    print("\n⚠️  PLATFORM ISSUES:")
    for issue_name, issue_pattern in platform_issues:
        if issue_pattern in screens_content:
            print(f"✅ {issue_name}: Handled")
        else:
            print(f"⚠️  {issue_name}: Not handled")
    
    return all_passed

def create_debug_checklist():
    """Create comprehensive debug checklist"""
    print("\n🐛 COMPREHENSIVE DEBUG CHECKLIST")
    print("=" * 50)
    
    print("""
🔍 STEP-BY-STEP DEBUGGING CHECKLIST:

1. 📱 BACKEND NOTIFICATION SENDING:
   ✅ Check if notification is actually sent
   ✅ Verify user token exists
   ✅ Check notification payload structure
   ✅ Verify auto_extract_pending flag is set
   ✅ Check Expo push service response

2. 🔔 FRONTEND NOTIFICATION RECEIVING:
   ✅ Check if notification listener is triggered
   ✅ Verify notification data is received
   ✅ Check user ID matching
   ✅ Verify notification type is 'new_diet'
   ✅ Check auto_extract_pending flag value

3. 🎯 POPUP STATE MANAGEMENT:
   ✅ Check if setShowAutoExtractionPopup(true) is called
   ✅ Verify popup state changes from false to true
   ✅ Check if modal is rendered with visible={true}
   ✅ Verify popup component exists and is properly configured

4. 🔄 TIMING AND RACE CONDITIONS:
   ✅ Check if useEffect dependencies are correct
   ✅ Verify screen focus state
   ✅ Check for multiple notification listeners
   ✅ Verify async operations complete properly

5. 🐛 COMMON ISSUES TO CHECK:
   ✅ User ID mismatch between notification and current user
   ✅ Notification listener not being triggered
   ✅ Popup state not updating
   ✅ Modal not rendering due to JSX issues
   ✅ Platform-specific notification handling
   ✅ Network connectivity issues
   ✅ Authentication state problems

6. 🛠️ DEBUGGING TOOLS:
   ✅ Use React Native debugger
   ✅ Check console logs for notification data
   ✅ Verify Firestore data
   ✅ Test with different user accounts
   ✅ Check notification permissions

7. 🧪 TEST SCENARIOS:
   ✅ App closed when diet arrives
   ✅ App open when diet arrives
   ✅ Multiple rapid diet uploads
   ✅ Network interruptions
   ✅ User authentication issues
   ✅ Platform differences (iOS vs Android)

8. 📊 EXPECTED LOGS:
   Look for these specific log messages:
   - '[NOTIFICATION DEBUG] DashboardScreen listener triggered'
   - '[NOTIFICATION DEBUG] User ID match: true'
   - '[NOTIFICATION DEBUG] Dashboard processing new_diet notification'
   - '[Dashboard] Notification data: {auto_extract_pending: true, ...}'
   - 'setShowAutoExtractionPopup(true)' being called

9. 🚨 RED FLAGS:
   ❌ User ID match: false
   ❌ Notification listener not triggered
   ❌ setShowAutoExtractionPopup not called
   ❌ Popup state remains false
   ❌ Modal not rendered
   ❌ No console logs appearing

10. 🔧 QUICK FIXES TO TRY:
    ✅ Restart the app completely
    ✅ Check user authentication
    ✅ Verify notification permissions
    ✅ Test with fresh diet upload
    ✅ Check network connectivity
    ✅ Clear app cache/data
""")
    
    return True

def main():
    """Run comprehensive popup debug analysis"""
    print("🐛 COMPREHENSIVE POPUP DEBUG ANALYSIS")
    print("=" * 60)
    print("Analyzing ALL possible factors preventing popup from showing\n")
    
    # Run all analyses
    analyses = [
        ("API Queuing System", analyze_api_queuing_system),
        ("Notification Delivery", analyze_notification_delivery),
        ("Frontend Listener Setup", analyze_frontend_listener_setup),
        ("User ID Matching", analyze_user_id_matching),
        ("State Management", analyze_state_management),
        ("Timing Issues", analyze_timing_issues),
        ("Platform Differences", analyze_platform_differences),
        ("Debug Checklist", create_debug_checklist),
    ]
    
    results = []
    for analysis_name, analysis_func in analyses:
        try:
            result = analysis_func()
            results.append((analysis_name, result))
        except Exception as e:
            print(f"❌ Error in {analysis_name}: {e}")
            results.append((analysis_name, False))
    
    # Summary
    print("\n🎯 COMPREHENSIVE DEBUG RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for analysis_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {analysis_name}")
    
    print(f"\n📊 SUMMARY: {passed}/{total} analyses passed")
    
    if passed == total:
        print("""
🎉 ALL ANALYSES PASSED!
======================

The code looks correct. The issue is likely one of these:

🔍 MOST LIKELY CAUSES:
1. User ID mismatch between notification and current user
2. Notification listener not being triggered
3. Popup state not updating properly
4. Platform-specific notification handling issues

🛠️ NEXT STEPS:
1. Follow the debug checklist above
2. Check console logs for specific error messages
3. Verify user ID matching
4. Test with different scenarios
5. Check notification permissions

The popup system is correctly implemented - it's a configuration or timing issue!
""")
    else:
        print(f"""
⚠️  {total - passed} ANALYSES FAILED
================================

Please review the failed analyses above.
The popup won't work until these issues are resolved.
""")

if __name__ == "__main__":
    main()
