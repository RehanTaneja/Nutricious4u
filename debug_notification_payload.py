#!/usr/bin/env python3
"""
Debug Notification Payload
==========================

This script simulates the exact notification payload that should be sent
and checks if the frontend is handling it correctly.
"""

import json

def simulate_notification_payload():
    """Simulate the exact notification payload from backend"""
    print("🔍 SIMULATING NOTIFICATION PAYLOAD")
    print("=" * 50)
    
    # This is the exact payload sent by backend
    notification_payload = {
        "type": "new_diet",
        "userId": "test_user_123",
        "auto_extract_pending": True,  # Flag to trigger popup
        "dietPdfUrl": "diet_2024_09_13.pdf",
        "cacheVersion": "v1.0",
        "timestamp": "2024-09-13T16:30:00.000Z"
    }
    
    print("📤 BACKEND SENDS:")
    print(json.dumps(notification_payload, indent=2))
    
    # Check frontend handling
    with open('mobileapp/screens.tsx', 'r') as f:
        frontend_content = f.read()
    
    # Find the notification handler
    handler_start = frontend_content.find('// Handle new diet notifications')
    handler_end = frontend_content.find('} catch (error) {', handler_start)
    
    if handler_start == -1 or handler_end == -1:
        print("❌ Could not find notification handler")
        return False
    
    handler_code = frontend_content[handler_start:handler_end]
    
    print("\n📱 FRONTEND HANDLES:")
    print("=" * 30)
    
    # Check each condition
    checks = [
        ("Notification type check", "data?.type === 'new_diet'"),
        ("User ID check", "data?.userId === userId"),
        ("Auto extract pending check", "data.auto_extract_pending"),
        ("Popup trigger", "setShowAutoExtractionPopup(true)"),
    ]
    
    all_passed = True
    for check_name, check_pattern in checks:
        if check_pattern in handler_code:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    return all_passed

def check_notification_listener_setup():
    """Check if notification listener is properly set up"""
    print("\n🔍 CHECKING NOTIFICATION LISTENER SETUP")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        frontend_content = f.read()
    
    # Check if listener is set up in DashboardScreen
    dashboard_start = frontend_content.find('const DashboardScreen = ({ navigation, route }: { navigation: any, route?: any }) => {')
    if dashboard_start == -1:
        print("❌ Could not find DashboardScreen")
        return False
    
    dashboard_end = frontend_content.find('const NotificationSettingsScreen', dashboard_start)
    dashboard_code = frontend_content[dashboard_start:dashboard_end]
    
    # Check for notification listener setup
    listener_checks = [
        ("useEffect for notifications", "useEffect(() => {" in dashboard_code),
        ("Notification listener", "addNotificationReceivedListener" in dashboard_code),
        ("User ID dependency", "if (!userId) return" in dashboard_code),
        ("Cleanup function", "subscription.remove()" in dashboard_code),
    ]
    
    all_passed = True
    for check_name, check_pattern in listener_checks:
        if check_pattern in dashboard_code:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    return all_passed

def check_popup_state_management():
    """Check popup state management"""
    print("\n🔍 CHECKING POPUP STATE MANAGEMENT")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        frontend_content = f.read()
    
    # Check for popup state variables
    state_checks = [
        ("showAutoExtractionPopup state", "showAutoExtractionPopup" in frontend_content),
        ("setShowAutoExtractionPopup", "setShowAutoExtractionPopup" in frontend_content),
        ("useState declaration", "useState<boolean>(false)" in frontend_content),
    ]
    
    all_passed = True
    for check_name, check_pattern in state_checks:
        if check_pattern in frontend_content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    return all_passed

def check_popup_modal_rendering():
    """Check if popup modal is properly rendered"""
    print("\n🔍 CHECKING POPUP MODAL RENDERING")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        frontend_content = f.read()
    
    # Find the popup modal
    modal_start = frontend_content.find('Auto-Extraction Popup Modal')
    if modal_start == -1:
        print("❌ Could not find popup modal")
        return False
    
    modal_end = frontend_content.find('</Modal>', modal_start)
    modal_code = frontend_content[modal_start:modal_end]
    
    # Check modal components
    modal_checks = [
        ("Modal visibility", "visible={showAutoExtractionPopup}" in modal_code),
        ("Extract button", "Extract Reminders" in modal_code),
        ("Later button", "Later" in modal_code),
        ("onPress handlers", "onPress=" in modal_code),
    ]
    
    all_passed = True
    for check_name, check_pattern in modal_checks:
        if check_pattern in modal_code:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    return all_passed

def create_debug_instructions():
    """Create debug instructions for the user"""
    print("\n🐛 DEBUG INSTRUCTIONS")
    print("=" * 50)
    
    instructions = [
        "1. Open React Native debugger or browser console",
        "2. Look for these log messages when notification arrives:",
        "   - '[NOTIFICATION DEBUG] DashboardScreen listener triggered'",
        "   - '[NOTIFICATION DEBUG] Notification data: {...}'",
        "   - '[NOTIFICATION DEBUG] User ID match: true/false'",
        "   - '[NOTIFICATION DEBUG] Dashboard processing new_diet notification'",
        "3. Check if 'auto_extract_pending' is true in the notification data",
        "4. Check if 'setShowAutoExtractionPopup(true)' is called",
        "5. Check if popup state changes from false to true",
        "6. Check if modal is rendered with visible={true}",
        "",
        "🔍 COMMON ISSUES TO CHECK:",
        "- User ID mismatch between notification and current user",
        "- Notification listener not set up properly",
        "- Popup state not updating",
        "- Modal not rendering due to JSX issues",
        "- Platform-specific notification handling differences",
    ]
    
    for instruction in instructions:
        print(instruction)
    
    return True

def main():
    """Run all debug checks"""
    print("🐛 NOTIFICATION PAYLOAD DEBUG")
    print("=" * 60)
    print("Debugging why popup doesn't show after notification\n")
    
    checks = [
        ("Notification Payload", simulate_notification_payload),
        ("Listener Setup", check_notification_listener_setup),
        ("State Management", check_popup_state_management),
        ("Modal Rendering", check_popup_modal_rendering),
        ("Debug Instructions", create_debug_instructions),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n🎯 DEBUG RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {check_name}")
    
    print(f"\n📊 SUMMARY: {passed}/{total} checks passed")
    
    if passed == total:
        print("""
🎉 ALL DEBUG CHECKS PASSED!
==========================

The notification handling code looks correct. The issue might be:
1. User ID mismatch in the notification
2. Notification listener not being triggered
3. Platform-specific notification handling
4. Timing issues with state updates

🔍 NEXT STEPS:
1. Check browser/React Native debugger console logs
2. Verify the notification payload contains correct user ID
3. Test with different notification scenarios
4. Check if notification listener is actually being called
""")
    else:
        print(f"""
⚠️  {total - passed} CHECKS FAILED
================================

Please fix the failed checks above.
The popup won't work until these issues are resolved.
""")

if __name__ == "__main__":
    main()
