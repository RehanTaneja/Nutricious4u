# 🔍 EAS Build Logging Guide

## The Problem
Frontend `console.log` statements are **NOT visible in EAS production builds**. This makes debugging the popup issue very difficult.

## The Solution
I've added **backend logging** that will show in your Railway logs, plus **frontend event logging** that sends data to the backend.

## 📱 What You'll See in Railway Logs

### 1. Backend Notification Sending
When a diet is uploaded, you'll see:
```
🚀 SENDING NOTIFICATION TO USER abc123
📱 Notification payload: {
  "type": "new_diet",
  "userId": "abc123",
  "auto_extract_pending": true,
  "dietPdfUrl": "diet_2024_09_13.pdf",
  "cacheVersion": "v1.0",
  "timestamp": "2024-09-13T16:30:00.000Z"
}
🔑 User token: ExponentPushToken[abc123...
✅ NOTIFICATION SENT SUCCESSFULLY to user abc123
🎯 Popup should appear with auto_extract_pending=True
```

### 2. Frontend Event Logging
When the notification is received, you'll see:
```
📱 FRONTEND EVENT LOG: {
  "userId": "abc123",
  "event": "NOTIFICATION_RECEIVED",
  "data": {
    "type": "new_diet",
    "notificationData": {...},
    "userMatch": true,
    "autoExtractPending": true
  }
}
```

### 3. Popup Trigger Logging
When popup is triggered, you'll see:
```
📱 FRONTEND EVENT LOG: {
  "userId": "abc123",
  "event": "POPUP_TRIGGERED",
  "data": {
    "reason": "auto_extract_pending",
    "popupState": "showing"
  }
}
```

## 🔍 How to Debug

### Step 1: Check Backend Logs
1. Go to your Railway dashboard
2. Check the logs for the notification sending
3. Look for the emoji indicators above

### Step 2: Check Frontend Events
1. Look for `📱 FRONTEND EVENT LOG:` entries
2. These show what the frontend is receiving and doing
3. Check if `userMatch` is `true`
4. Check if `autoExtractPending` is `true`

### Step 3: Identify Issues
- **No backend logs**: Notification not being sent
- **Backend logs but no frontend events**: Notification not received
- **Frontend events but no popup**: User ID mismatch or popup state issue
- **userMatch: false**: Wrong user ID
- **autoExtractPending: false**: Backend not setting flag correctly

## 🧪 Test Process

1. **Upload a diet** as dietician
2. **Check Railway logs** for backend notification sending
3. **Login as user** and wait for notification
4. **Check Railway logs** for frontend event logging
5. **Verify popup appears** on Dashboard

## 🚨 Common Issues

### Issue 1: No Backend Logs
- User token not found
- Notification service down
- Check user authentication

### Issue 2: Backend Logs but No Frontend Events
- Notification not received by device
- Check notification permissions
- Check network connectivity

### Issue 3: Frontend Events but No Popup
- User ID mismatch (`userMatch: false`)
- Popup state not updating
- Modal rendering issue

### Issue 4: autoExtractPending: false
- Backend not setting flag correctly
- Check diet upload process
- Check notification payload

## 🛠️ Quick Fixes

1. **Restart the app** completely
2. **Check user authentication** - make sure you're logged in as the correct user
3. **Verify notification permissions** are granted
4. **Test with fresh diet upload**
5. **Check network connectivity**

## 📊 Expected Flow

1. ✅ Backend sends notification with `auto_extract_pending: true`
2. ✅ Frontend receives notification
3. ✅ User ID matches (`userMatch: true`)
4. ✅ Auto extract pending is true (`autoExtractPending: true`)
5. ✅ Popup is triggered (`POPUP_TRIGGERED` event)
6. ✅ Popup appears on Dashboard

If any step fails, you'll see it in the Railway logs! 🎯
