#!/usr/bin/env python3
"""
Debug User ID Mismatch
======================

This script helps identify if there's a user ID mismatch between
the notification and the frontend user.
"""

def create_debug_instructions():
    """Create detailed debug instructions"""
    print("🐛 DEBUG INSTRUCTIONS FOR USER ID MISMATCH")
    print("=" * 60)
    
    print("""
🔍 STEP-BY-STEP DEBUGGING:

1. 📱 OPEN YOUR APP AND CHECK CONSOLE:
   - Open React Native debugger or browser console
   - Look for the notification logs

2. 🔔 WHEN NOTIFICATION ARRIVES, CHECK THESE LOGS:
   
   Look for this specific log:
   '[NOTIFICATION DEBUG] User ID match: true/false'
   
   If it shows 'false', that's the problem!

3. 📋 CHECK THE NOTIFICATION DATA:
   Look for this log:
   '[NOTIFICATION DEBUG] Notification data: {...}'
   
   The data should look like:
   {
     "type": "new_diet",
     "userId": "some_user_id_here",
     "auto_extract_pending": true,
     "dietPdfUrl": "diet_file.pdf",
     "cacheVersion": "v1.0",
     "timestamp": "2024-09-13T..."
   }

4. 🔍 COMPARE USER IDs:
   - Note the 'userId' in the notification data
   - Check what user ID your app is using
   - They should be the same!

5. 🚨 COMMON USER ID MISMATCH ISSUES:
   
   a) DIFFERENT USER ACCOUNTS:
      - You logged in as dietician to upload diet
      - But you're checking as a different user
      - Solution: Make sure you're logged in as the SAME user
   
   b) USER ID FORMAT DIFFERENCES:
      - Backend sends: "abc123"
      - Frontend expects: "abc123" (should match)
      - But sometimes there are extra characters or formatting
   
   c) AUTHENTICATION STATE:
      - User might not be fully authenticated when notification arrives
      - userId might be null or undefined
   
   d) NOTIFICATION TARGETING:
      - Notification might be sent to wrong user
      - Check if dietician uploaded diet for correct user

6. 🛠️ QUICK FIXES TO TRY:
   
   a) RESTART AND RE-TEST:
      - Log out completely
      - Log in as the user who should receive the diet
      - Have dietician upload diet for that specific user
      - Check console logs again
   
   b) CHECK USER AUTHENTICATION:
      - Make sure you're logged in as the correct user
      - Check if userId is not null in the app
   
   c) VERIFY DIET UPLOAD:
      - Make sure dietician uploaded diet for the correct user
      - Check the user ID in the upload process

7. 🔍 ADVANCED DEBUGGING:
   
   If you want to see the exact user IDs:
   
   Add this temporary code to your DashboardScreen:
   
   ```javascript
   // Add this in the notification handler
   console.log('[DEBUG] Current user ID:', userId);
   console.log('[DEBUG] Notification user ID:', data?.userId);
   console.log('[DEBUG] User IDs match:', data?.userId === userId);
   console.log('[DEBUG] User ID types:', typeof userId, typeof data?.userId);
   ```

8. 📞 IF STILL NOT WORKING:
   
   Send me these logs:
   - '[NOTIFICATION DEBUG] User ID match: ...'
   - '[NOTIFICATION DEBUG] Notification data: ...'
   - Current user ID from your app
   - User ID from the notification
   
   This will help me identify the exact mismatch!
""")
    
    return True

def check_notification_code():
    """Check the notification handling code for potential issues"""
    print("\n🔍 CHECKING NOTIFICATION HANDLING CODE")
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
    
    # Check for user ID comparison
    user_id_checks = [
        ("User ID comparison", "data?.userId === userId" in handler_code),
        ("User ID logging", "User ID match:" in handler_code),
        ("Data logging", "Notification data:" in handler_code),
        ("Type check", "data?.type === 'new_diet'" in handler_code),
        ("Auto extract check", "data.auto_extract_pending" in handler_code),
    ]
    
    all_passed = True
    for check_name, check_pattern in user_id_checks:
        if check_pattern in handler_code:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing")
            all_passed = False
    
    return all_passed

def main():
    """Run debug analysis"""
    print("🐛 USER ID MISMATCH DEBUG")
    print("=" * 60)
    print("Debugging potential user ID mismatch issue\n")
    
    checks = [
        ("Notification Code", check_notification_code),
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
    print("\n🎯 DEBUG RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {check_name}")
    
    print(f"\n📊 SUMMARY: {passed}/{total} checks passed")
    
    if passed == total:
        print("""
🎉 CODE LOOKS CORRECT!
=====================

The notification handling code is properly implemented.
The issue is likely a user ID mismatch.

🔍 NEXT STEPS:
1. Follow the debug instructions above
2. Check console logs for user ID comparison
3. Verify you're logged in as the correct user
4. Make sure dietician uploaded diet for the right user

The popup should work once the user IDs match! 🎯
""")
    else:
        print(f"""
⚠️  {total - passed} CHECKS FAILED
================================

Please fix the failed checks above.
""")

if __name__ == "__main__":
    main()
