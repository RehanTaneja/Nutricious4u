#!/usr/bin/env python3
"""
Test Notification Debug
=======================

This script helps debug the notification issue by checking:
1. If the notification listener is properly set up
2. If the popup state management is correct
3. If there are any obvious issues in the code
"""

def check_notification_listener():
    """Check if notification listener is properly set up"""
    print("🔍 CHECKING NOTIFICATION LISTENER SETUP")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        content = f.read()
    
    # Find DashboardScreen
    dashboard_start = content.find('const DashboardScreen = ({ navigation, route }: { navigation: any, route?: any }) => {')
    if dashboard_start == -1:
        print("❌ Could not find DashboardScreen")
        return False
    
    dashboard_end = content.find('const NotificationSettingsScreen', dashboard_start)
    dashboard_code = content[dashboard_start:dashboard_end]
    
    # Check for notification listener
    listener_checks = [
        ("useEffect for notifications", "useEffect(() => {" in dashboard_code),
        ("Notification listener", "addNotificationReceivedListener" in dashboard_code),
        ("User ID check", "if (!userId) return" in dashboard_code),
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

def check_popup_state():
    """Check popup state management"""
    print("\n🔍 CHECKING POPUP STATE MANAGEMENT")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        content = f.read()
    
    # Check for popup state variables
    state_checks = [
        ("showAutoExtractionPopup state", "showAutoExtractionPopup" in content),
        ("setShowAutoExtractionPopup", "setShowAutoExtractionPopup" in content),
        ("useState declaration", "useState<boolean>(false)" in content),
    ]
    
    all_passed = True
    for check_name, check_pattern in state_checks:
        if check_pattern in content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    return all_passed

def check_popup_modal():
    """Check popup modal rendering"""
    print("\n🔍 CHECKING POPUP MODAL RENDERING")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        content = f.read()
    
    # Find the popup modal
    modal_start = content.find('Auto-Extraction Popup Modal')
    if modal_start == -1:
        print("❌ Could not find popup modal")
        return False
    
    modal_end = content.find('</Modal>', modal_start)
    modal_code = content[modal_start:modal_end]
    
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

def check_notification_handler_logic():
    """Check the notification handler logic"""
    print("\n🔍 CHECKING NOTIFICATION HANDLER LOGIC")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        content = f.read()
    
    # Find the notification handler
    handler_start = content.find('// Handle new diet notifications')
    if handler_start == -1:
        print("❌ Could not find notification handler")
        return False
    
    handler_end = content.find('} catch (error) {', handler_start)
    handler_code = content[handler_start:handler_end]
    
    # Check handler logic
    logic_checks = [
        ("Type check", "data?.type === 'new_diet'" in handler_code),
        ("User ID check", "data?.userId === userId" in handler_code),
        ("Auto extract check", "data.auto_extract_pending" in handler_code),
        ("Popup trigger", "setShowAutoExtractionPopup(true)" in handler_code),
        ("Console logging", "console.log" in handler_code),
    ]
    
    all_passed = True
    for check_name, check_pattern in logic_checks:
        if check_pattern in handler_code:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    return all_passed

def create_debug_guide():
    """Create a debug guide for the user"""
    print("\n🐛 DEBUG GUIDE FOR USER")
    print("=" * 50)
    
    print("""
🔍 STEP-BY-STEP DEBUGGING:

1. 📱 OPEN REACT NATIVE DEBUGGER:
   - Open your app in development mode
   - Open React Native debugger or browser console
   - Look for console logs

2. 🔔 TRIGGER NOTIFICATION:
   - Login as dietician
   - Upload a new diet for the user
   - Login as the user
   - Wait for notification

3. 📋 CHECK THESE LOGS:
   Look for these specific log messages:
   
   ✅ SHOULD SEE:
   - '[NOTIFICATION DEBUG] DashboardScreen listener triggered'
   - '[NOTIFICATION DEBUG] Notification data: {...}'
   - '[NOTIFICATION DEBUG] User ID match: true'
   - '[NOTIFICATION DEBUG] Dashboard processing new_diet notification'
   - '[Dashboard] Notification data: {auto_extract_pending: true, ...}'
   
   ❌ IF MISSING:
   - Notification listener not set up
   - User ID mismatch
   - Notification not being received

4. 🔍 CHECK NOTIFICATION DATA:
   The notification data should contain:
   {
     "type": "new_diet",
     "userId": "your_user_id",
     "auto_extract_pending": true,
     "dietPdfUrl": "diet_file.pdf",
     "cacheVersion": "v1.0",
     "timestamp": "2024-09-13T..."
   }

5. 🎯 CHECK POPUP STATE:
   Look for:
   - 'setShowAutoExtractionPopup(true)' being called
   - Popup state changing from false to true
   - Modal rendering with visible={true}

6. 🚨 COMMON ISSUES:
   - User ID mismatch between notification and current user
   - Notification listener not being triggered
   - Platform-specific notification handling
   - State not updating properly
   - Modal not rendering due to JSX issues

7. 🛠️ QUICK FIXES TO TRY:
   - Restart the app completely
   - Check if you're logged in as the correct user
   - Verify the notification payload in console
   - Test with a fresh diet upload
   - Check if notification permissions are granted
""")
    
    return True

def main():
    """Run all checks"""
    print("🐛 NOTIFICATION DEBUG TEST")
    print("=" * 60)
    print("Debugging why popup doesn't show after notification\n")
    
    checks = [
        ("Notification Listener", check_notification_listener),
        ("Popup State", check_popup_state),
        ("Popup Modal", check_popup_modal),
        ("Handler Logic", check_notification_handler_logic),
        ("Debug Guide", create_debug_guide),
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
    print("\n🎯 DEBUG TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {check_name}")
    
    print(f"\n📊 SUMMARY: {passed}/{total} checks passed")
    
    if passed == total:
        print("""
🎉 ALL CHECKS PASSED!
====================

The code looks correct. The issue is likely:
1. User ID mismatch in notification
2. Notification listener not being triggered
3. Platform-specific notification handling
4. Timing issues

🔍 NEXT STEPS:
1. Check console logs as described in debug guide
2. Verify notification payload
3. Test with fresh diet upload
4. Check user authentication
""")
    else:
        print(f"""
⚠️  {total - passed} CHECKS FAILED
================================

Please fix the failed checks above.
The popup won't work until these are resolved.
""")

if __name__ == "__main__":
    main()
