# How to Get Device Logs for Push Token Registration

## The Problem
Token registration logs use `console.log()` which only appears in device logs, NOT backend logs.

## For Android (Samsung Tablet):

### Option 1: Using adb logcat

1. Enable Developer Options on the device:
   - Settings → About Phone → Tap "Build Number" 7 times

2. Enable USB Debugging:
   - Settings → Developer Options → Enable "USB Debugging"

3. Connect device via USB to computer

4. Run this command to capture logs:
```bash
adb logcat | grep -E "PUSH TOKEN|NOTIFICATIONS|registerForPush"
```

5. Now open the app and log in
6. Watch for these log patterns:
```
🔔 [PUSH TOKEN REGISTRATION] START
[PUSH TOKEN] Platform: android
[PUSH TOKEN] User ID provided: ...
[PUSH TOKEN] ✓ Token received successfully
[PUSH TOKEN] ✓ Token saved successfully to Firestore
```

### Option 2: Using React Native Debugger

If you have access to development build:
1. Shake device or press Cmd+D
2. Select "Debug JS Remotely"
3. Open Chrome DevTools
4. Console will show all logs

### Option 3: Using Expo Dev Client

If using Expo Dev Client:
1. Open Expo Dev Client
2. Look at the terminal where `npx expo start` is running
3. Logs will appear there

## What to Look For:

### If token registration is WORKING:
```
═══════════════════════════════════════════════════════════════
🔔 [PUSH TOKEN REGISTRATION] START
═══════════════════════════════════════════════════════════════
[PUSH TOKEN] Time: 2025-12-27T...
[PUSH TOKEN] Platform: android  ← Should be "android"!
[PUSH TOKEN] User ID provided: mBVlWBBpoaXyOVr8Y4AoHZunq9f1
[PUSH TOKEN] Step 1: Checking existing notification permissions...
[PUSH TOKEN] ✓ Existing permission status: granted
[PUSH TOKEN] ✓ Permission granted successfully
[PUSH TOKEN] Step 3: Getting Expo push token...
[PUSH TOKEN] ✓ Token received successfully
[PUSH TOKEN] Token preview: ExponentPushToken[NEW_TOKEN_...
[PUSH TOKEN] Step 4: Saving token to Firestore...
[PUSH TOKEN] ✓ Token saved successfully to Firestore
═══════════════════════════════════════════════════════════════
🔔 [PUSH TOKEN REGISTRATION] SUCCESS
═══════════════════════════════════════════════════════════════
```

### If token registration is FAILING:
```
[PUSH TOKEN] ❌ FAILED: Notification permission not granted
```
or
```
[PUSH TOKEN] ❌ Missing Expo project ID, cannot request push token
```
or
```
[PUSH TOKEN] ❌ FAILED to get Expo push token
```
or
```
[PUSH TOKEN] ❌ FAILED to save push token to Firestore
```

### If token registration is NOT RUNNING at all:
You won't see ANY of these logs. This means:
- `registerForPushNotificationsAsync` is never called
- The auth state change handler is not triggering it
- Or the guard conditions are skipping it

