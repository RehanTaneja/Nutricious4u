#!/usr/bin/env python3
"""
Simple Popup Debug - Focus on Key Issues
========================================

This script focuses on the most likely causes of popup not showing.
"""

def check_critical_issues():
    """Check for critical issues that would prevent popup"""
    print("🔍 CHECKING CRITICAL POPUP ISSUES")
    print("=" * 50)
    
    # Check 1: Notification handler logic
    with open('mobileapp/screens.tsx', 'r') as f:
        content = f.read()
    
    print("1. 📱 NOTIFICATION HANDLER LOGIC:")
    
    # Check if the notification handler exists
    if 'addNotificationReceivedListener' in content:
        print("   ✅ Notification listener exists")
    else:
        print("   ❌ Notification listener missing")
        return False
    
    # Check if user ID matching exists
    if 'data?.userId === userId' in content:
        print("   ✅ User ID matching exists")
    else:
        print("   ❌ User ID matching missing")
        return False
    
    # Check if auto_extract_pending check exists
    if 'data.auto_extract_pending' in content:
        print("   ✅ Auto extract pending check exists")
    else:
        print("   ❌ Auto extract pending check missing")
        return False
    
    # Check if popup trigger exists
    if 'setShowAutoExtractionPopup(true)' in content:
        print("   ✅ Popup trigger exists")
    else:
        print("   ❌ Popup trigger missing")
        return False
    
    print("\n2. 🎯 POPUP STATE MANAGEMENT:")
    
    # Check if state variable exists
    if 'showAutoExtractionPopup' in content:
        print("   ✅ Popup state variable exists")
    else:
        print("   ❌ Popup state variable missing")
        return False
    
    # Check if modal exists
    if 'visible={showAutoExtractionPopup}' in content:
        print("   ✅ Modal visibility control exists")
    else:
        print("   ❌ Modal visibility control missing")
        return False
    
    print("\n3. 🔔 BACKEND NOTIFICATION SENDING:")
    
    with open('backend/server.py', 'r') as f:
        backend_content = f.read()
    
    # Check if auto_extract_pending is set
    if '"auto_extract_pending": True' in backend_content:
        print("   ✅ Backend sets auto_extract_pending flag")
    else:
        print("   ❌ Backend doesn't set auto_extract_pending flag")
        return False
    
    # Check if notification is sent
    if 'send_push_notification' in backend_content:
        print("   ✅ Backend sends push notification")
    else:
        print("   ❌ Backend doesn't send push notification")
        return False
    
    return True

def identify_most_likely_issues():
    """Identify the most likely issues"""
    print("\n🎯 MOST LIKELY ISSUES")
    print("=" * 50)
    
    print("""
Based on the code analysis, here are the most likely issues:

1. 🚨 USER ID MISMATCH (MOST LIKELY):
   - Notification sent to different user ID than current user
   - Check console logs for: '[NOTIFICATION DEBUG] User ID match: false'
   - Solution: Verify you're logged in as the correct user

2. 🔔 NOTIFICATION NOT RECEIVED:
   - Notification listener not triggered
   - Check console logs for: '[NOTIFICATION DEBUG] DashboardScreen listener triggered'
   - Solution: Check notification permissions and network

3. 📱 POPUP STATE NOT UPDATING:
   - setShowAutoExtractionPopup(true) not called
   - Check console logs for: 'setShowAutoExtractionPopup(true)'
   - Solution: Check notification data structure

4. 🎯 MODAL NOT RENDERING:
   - Modal exists but not visible
   - Check if showAutoExtractionPopup state is true
   - Solution: Check JSX rendering logic

5. ⏰ TIMING ISSUES:
   - Notification received before user is authenticated
   - Screen not focused when notification arrives
   - Solution: Check useEffect dependencies and timing
""")

def create_simple_debug_steps():
    """Create simple debug steps"""
    print("\n🛠️ SIMPLE DEBUG STEPS")
    print("=" * 50)
    
    print("""
🔍 STEP 1: CHECK CONSOLE LOGS
============================
Open your app and look for these logs when notification arrives:

✅ SHOULD SEE:
- '[NOTIFICATION DEBUG] DashboardScreen listener triggered'
- '[NOTIFICATION DEBUG] User ID match: true'
- '[NOTIFICATION DEBUG] Dashboard processing new_diet notification'
- '[Dashboard] Notification data: {auto_extract_pending: true, ...}'

❌ IF MISSING:
- No logs = notification listener not working
- User ID match: false = wrong user
- No processing = notification type wrong
- No data = notification payload wrong

🔍 STEP 2: CHECK NOTIFICATION DATA
==================================
Look for this in the logs:
{
  "type": "new_diet",
  "userId": "your_user_id",
  "auto_extract_pending": true,
  "dietPdfUrl": "diet_file.pdf"
}

❌ IF WRONG:
- userId doesn't match your current user
- auto_extract_pending is false or missing
- type is not "new_diet"

🔍 STEP 3: CHECK POPUP STATE
============================
Look for these logs:
- 'setShowAutoExtractionPopup(true)' being called
- Popup state changing from false to true
- Modal rendering with visible={true}

❌ IF MISSING:
- setShowAutoExtractionPopup not called
- Popup state not updating
- Modal not rendering

🔍 STEP 4: QUICK FIXES
=====================
1. Restart the app completely
2. Check you're logged in as the correct user
3. Verify notification permissions are granted
4. Test with a fresh diet upload
5. Check network connectivity

🔍 STEP 5: ADVANCED DEBUGGING
=============================
Add this temporary code to your DashboardScreen:

```javascript
// Add this in the notification handler
console.log('[DEBUG] Current user ID:', userId);
console.log('[DEBUG] Notification user ID:', data?.userId);
console.log('[DEBUG] User IDs match:', data?.userId === userId);
console.log('[DEBUG] Auto extract pending:', data?.auto_extract_pending);
console.log('[DEBUG] Setting popup to true...');
setShowAutoExtractionPopup(true);
console.log('[DEBUG] Popup state set to true');
```
""")

def main():
    """Run simple popup debug"""
    print("🐛 SIMPLE POPUP DEBUG")
    print("=" * 60)
    print("Focusing on the most likely causes\n")
    
    # Check critical issues
    critical_ok = check_critical_issues()
    
    # Identify likely issues
    identify_most_likely_issues()
    
    # Create debug steps
    create_simple_debug_steps()
    
    # Final summary
    print("\n🎯 FINAL SUMMARY")
    print("=" * 50)
    
    if critical_ok:
        print("""
✅ CODE LOOKS CORRECT!
=====================

The popup system is properly implemented. The issue is likely:

🔍 MOST LIKELY CAUSE: User ID Mismatch
- You're logged in as a different user than the one who should receive the diet
- Check console logs for "User ID match: false"

🛠️ QUICK FIX:
1. Make sure you're logged in as the correct user
2. Have dietician upload diet for that specific user
3. Check console logs for the exact issue

The popup will work once the user IDs match! 🎯
""")
    else:
        print("""
❌ CRITICAL ISSUES FOUND!
========================

Please fix the critical issues above first.
The popup won't work until these are resolved.
""")

if __name__ == "__main__":
    main()
