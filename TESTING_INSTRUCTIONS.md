# 📱 MESSAGE NOTIFICATION TESTING INSTRUCTIONS

## ✅ **CODE FIXES VERIFIED**

All code changes have been verified and are in place:
- ✅ Backend includes fromDietician/fromUser flags
- ✅ Backend handles "dietician" recipient correctly
- ✅ Backend includes sender user ID tracking
- ✅ Frontend sends complete notification data
- ✅ Frontend handlers check for correct flags
- ✅ Debug endpoints added for troubleshooting

---

## 🧪 **MANUAL TESTING REQUIRED**

To verify the notifications work end-to-end, follow these steps:

### **Prerequisites:**

1. **Backend Running:**
   ```bash
   cd backend
   python3 server.py
   ```
   
2. **Two Mobile Devices:**
   - Device A: Logged in as dietician (nutricious4u@gmail.com)
   - Device B: Logged in as regular user

3. **Ensure Tokens Registered:**
   - Both users should have logged in at least once
   - Check token status:
     ```bash
     curl http://localhost:8000/notifications/debug/token/dietician
     curl http://localhost:8000/notifications/debug/token/<user_id>
     ```

---

## 📋 **TEST CASE 1: User → Dietician Notification**

### **Steps:**

1. **On User Device (Device B):**
   - Open the app
   - Navigate to Messages screen
   - Send a message to dietician
   - Example: "Hello, I have a question about my diet"

2. **On Dietician Device (Device A):**
   - Should receive notification
   - Notification should show: "You have a new message from [User Name]"
   - Tap notification → Should navigate to messages screen

3. **Verify in Backend Logs:**
   ```bash
   tail -f backend/server.log | grep "SimpleNotification"
   ```
   
   Look for:
   - `[SimpleNotification] ===== MESSAGE NOTIFICATION =====`
   - `[SimpleNotification] Recipient: dietician`
   - `[SimpleNotification] Is Dietician: False`
   - `[SimpleNotification] Setting fromUser=<user_id>`
   - `[SimpleNotification] Getting dietician token (special case)`
   - `[SimpleNotification] ✅ Dietician token found`
   - `[SimpleNotification] ✅ Notification sent successfully`

### **Expected Results:**
- ✅ Notification appears on dietician's device
- ✅ Notification has correct sender name
- ✅ Tapping notification navigates to messages
- ✅ Backend logs show successful flow
- ✅ No errors in backend logs

---

## 📋 **TEST CASE 2: Dietician → User Notification**

### **Steps:**

1. **On Dietician Device (Device A):**
   - Open the app
   - Navigate to Messages screen
   - Select a user from the list
   - Send a message to that user
   - Example: "I've reviewed your diet plan"

2. **On User Device (Device B):**
   - Should receive notification
   - Notification should show: "You have a new message from your dietician"
   - Tap notification → Should navigate to messages screen

3. **Verify in Backend Logs:**
   ```bash
   tail -f backend/server.log | grep "SimpleNotification"
   ```
   
   Look for:
   - `[SimpleNotification] ===== MESSAGE NOTIFICATION =====`
   - `[SimpleNotification] Recipient: <user_id>`
   - `[SimpleNotification] Is Dietician: True`
   - `[SimpleNotification] Setting fromDietician=True`
   - `[SimpleNotification] ✅ Token found for user`
   - `[SimpleNotification] ✅ Notification sent successfully`

### **Expected Results:**
- ✅ Notification appears on user's device
- ✅ Notification message is correct
- ✅ Tapping notification navigates to messages
- ✅ Backend logs show successful flow
- ✅ No errors in backend logs

---

## 🔍 **DEBUGGING CHECKLIST**

If notifications don't appear, check these in order:

### **1. Token Registration**
```bash
# Check dietician token
curl http://localhost:8000/notifications/debug/token/dietician

# Check user token (replace with actual user ID)
curl http://localhost:8000/notifications/debug/token/<user_id>
```

**Expected Response:**
```json
{
  "tokenFound": true,
  "tokenValid": true,
  "tokenPreview": "ExponentPushToken[...]",
  "platform": "ios" or "android"
}
```

**If token not found:**
- User needs to log into mobile app
- Check that `registerForPushNotificationsAsync()` is being called after login
- Verify notification permissions are granted on device

### **2. Backend API Test**

Test the notification endpoint directly:

**User → Dietician:**
```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipientId": "dietician",
    "type": "message",
    "message": "Test message from user",
    "senderName": "Test User",
    "senderUserId": "test_user_123",
    "isDietician": false
  }'
```

**Dietician → User:**
```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipientId": "USER_ID_HERE",
    "type": "message",
    "message": "Test message from dietician",
    "senderName": "Dietician",
    "senderUserId": "dietician",
    "isDietician": true
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Notification sent successfully"
}
```

### **3. Mobile App Logs**

Check the mobile app console for:

**When notification received:**
```
[Dashboard] Received message notification from dietician: ...
or
[DieticianDashboard] Received message from user: ...
```

**When notification sent:**
```
[Message Notifications] Sending push notification: ...
[Message Notifications] Push notification sent successfully
```

### **4. Backend Logs**

Monitor backend logs in real-time:
```bash
tail -f backend/server.log
```

Look for error patterns:
- `❌ No token found for user`
- `❌ Failed to send notification`
- `Invalid token format`
- Connection errors to Expo Push Service

---

## 🚨 **COMMON ISSUES & SOLUTIONS**

### **Issue 1: "No token found"**
**Cause:** User hasn't logged into mobile app yet
**Solution:** 
- Log into mobile app on the device
- Grant notification permissions when prompted
- Wait a few seconds for token to register
- Check token status with debug endpoint

### **Issue 2: "Invalid token format"**
**Cause:** Token doesn't start with "ExponentPushToken"
**Solution:**
- Re-register token by logging out and back in
- Check that app is using EAS build, not Expo Go
- Verify `projectId` is correct in `registerForPushNotificationsAsync()`

### **Issue 3: Notification sent but not received**
**Cause:** Device-side issue or Expo Push Service issue
**Solution:**
- Check internet connection on device
- Verify app has notification permissions
- Check if app is in background or foreground (both should work)
- Try force-closing and reopening the app
- Check Expo Push Service status: https://status.expo.dev/

### **Issue 4: Wrong person receives notification**
**Cause:** This was the original bug - should be fixed now
**Solution:**
- Verify all code changes are deployed
- Run verification script: `python3 verify_notification_fix.py`
- Check backend logs for correct fromUser/fromDietician flags
- Ensure frontend handlers are checking for correct flags

### **Issue 5: Dietician token not found**
**Cause:** Dietician account doesn't have `isDietician: true` flag
**Solution:**
1. Check Firestore `user_profiles` collection
2. Find dietician account (nutricious4u@gmail.com)
3. Add field: `isDietician: true`
4. Verify with debug endpoint

---

## 📊 **SUCCESS INDICATORS**

You'll know the system is working when:

1. **Backend logs show:**
   - ✅ Token found for both users
   - ✅ Correct recipient ID identified
   - ✅ Correct flags set (fromUser/fromDietician)
   - ✅ Notification sent successfully to Expo
   - ✅ No errors or warnings

2. **Mobile apps show:**
   - ✅ Messages appear in chat immediately
   - ✅ Notifications appear on recipient's device
   - ✅ Notifications have correct content
   - ✅ Tapping notification navigates correctly
   - ✅ No console errors

3. **User experience is:**
   - ✅ Smooth and instant
   - ✅ Clear who sent the message
   - ✅ Easy to navigate to conversation
   - ✅ Works in both directions
   - ✅ No duplicate notifications

---

## 🎯 **FINAL VERIFICATION**

Run through this complete flow once everything is working:

1. **Clean State Test:**
   - Force close both apps
   - Clear all notifications on both devices
   - Open user app
   - Open dietician app

2. **Bidirectional Test:**
   - User sends: "Hello Dietician"
   - Verify dietician receives notification ✅
   - Dietician replies: "Hello User"
   - Verify user receives notification ✅

3. **Navigation Test:**
   - User taps notification → Goes to messages ✅
   - Dietician taps notification → Goes to that user's chat ✅

4. **Multiple Messages Test:**
   - Send 3 messages from user
   - Verify dietician gets 3 notifications ✅
   - Send 3 messages from dietician
   - Verify user gets 3 notifications ✅

5. **Background Test:**
   - Put app in background on user device
   - Send message from dietician
   - Verify notification appears even when app in background ✅

---

## 📞 **NEED HELP?**

If you're stuck:

1. **Check verification:** `python3 verify_notification_fix.py`
2. **Check tokens:** Use debug endpoint
3. **Check logs:** Look for errors in backend logs
4. **Test API directly:** Use curl commands above
5. **Check mobile console:** Look for notification events

---

## ✅ **WHEN TESTING IS COMPLETE**

Once all tests pass:
- ✅ Mark this document as reviewed
- ✅ Document any issues found
- ✅ Update deployment checklist
- ✅ Deploy to production
- ✅ Monitor production logs for first few days

**Message notification system is now production-ready!** 🎉

