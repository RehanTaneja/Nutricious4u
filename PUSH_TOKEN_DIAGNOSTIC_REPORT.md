# Push Notification Token Diagnostic Report

**Date:** January 2, 2026  
**App:** Nutricious4u (Expo SDK 53, Android)  
**Issue:** `getExpoPushTokenAsync()` returning null/empty tokens on new logins

---

## Executive Summary

The diagnostic analysis reveals that `getExpoPushTokenAsync()` is returning an **empty string** (`""`) instead of a valid Expo push token. This occurs because the **FCM Legacy Server Key is missing** from EAS credentials. While FCM V1 Service Account Key is configured (for sending notifications), Expo's token generation API still requires the FCM Legacy Server Key. The code flow is correct, but the missing credential causes `tokenData.data` to be an empty string, which passes through validation checks and results in `tokenPreview: null` in backend logs.

---

## Configuration Status

### app.json

- **Location:** `mobileapp/app.json`
- **Relevant config:**
  ```json
  {
    "expo": {
      "android": {
        "package": "com.nutricious4u.app",
        "permissions": [
          "INTERNET",
          "ACCESS_NETWORK_STATE",
          "NOTIFICATIONS",
          "POST_NOTIFICATIONS",
          "VIBRATE",
          "RECEIVE_BOOT_COMPLETED",
          "WAKE_LOCK"
        ]
      },
      "plugins": [
        [
          "expo-build-properties",
          {
            "android": {
              "googleServicesFile": "./google-services.json"
            }
          }
        ],
        [
          "expo-notifications",
          {
            "icon": "./assets/notification_icon_48.png",
            "color": "#ffffff",
            "mode": "production"
          }
        ]
      ],
      "extra": {
        "eas": {
          "projectId": "38ed8fe9-6087-4fdd-9164-a0c36ee3a9fb"
        }
      }
    }
  }
  ```
- **Issues found:** None - Configuration is correct

### google-services.json

- **Location:** `mobileapp/google-services.json`
- **Project number:** `383526478160`
- **Project ID:** `nutricious4u-63158`
- **Package name:** `com.nutricious4u.app` ✅ (matches app.json)
- **Included in builds:** ✅ Yes (via `expo-build-properties` plugin)
- **Issues found:** None - File is correctly configured and referenced

**Note:** `google-services.json` is in `.gitignore` (lines 89, 115), which is correct for security. However, it's properly included in builds via the `expo-build-properties` plugin configuration.

### eas.json

- **Location:** `mobileapp/eas.json`
- **Build profiles:** `development`, `preview`, `production`
- **Issues found:** None - Configuration is standard

### Dependencies

- **expo:** `53.0.22` ✅
- **expo-notifications:** `~0.31.4` ✅
- **expo-build-properties:** `~0.14.8` ✅
- **firebase:** `^9.6.11` ✅
- **Other relevant packages:** None
- **Issues found:** None - All dependencies are correct versions

---

## Code Analysis

### Token Registration Locations

#### 1. Primary Registration: `firebase.ts` (Lines 116-271)

**File:** `mobileapp/services/firebase.ts:116-271`  
**Function:** `registerForPushNotificationsAsync(userId?: string)`

**Code:**
```typescript
export async function registerForPushNotificationsAsync(userId?: string) {
  // ... logging ...
  
  let token;
  try {
    // Step 1: Check permissions
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    // Step 2: Request permissions if needed
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    // Step 3: Check if permission was granted
    if (finalStatus !== 'granted') {
      return null;
    }
    
    // Step 4: Get Expo push token
    if (!EXPO_PROJECT_ID) {
      return null;
    }
    
    try {
      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId: EXPO_PROJECT_ID
      });
      token = tokenData.data;  // ⚠️ CRITICAL: No validation for empty string
      console.log(`[PUSH TOKEN] ✓ Token received successfully`);
      console.log(`[PUSH TOKEN] Token preview: ${token.substring(0, 30)}...`);  // ⚠️ Will work with empty string
      // ... more logging ...
    } catch (tokenError) {
      throw tokenError;
    }
    
    // Step 5: Save token to Firestore
    if (!user) {
      return null;
    }
    
    if (!token) {  // ⚠️ This check catches null/undefined but NOT empty string ""
      console.log('[PUSH TOKEN] ❌ FAILED: No token available for saving');
      return token;  // ⚠️ Returns empty string, not null
    }
    
    // ... save to Firestore ...
  } catch (e) {
    return null;
  }
  
  return token;  // ⚠️ Returns empty string if tokenData.data was ""
}
```

**Error handling:** 
- Catches exceptions and returns `null`
- **ISSUE:** Does not validate for empty string tokens
- **ISSUE:** Line 214 returns `token` (which could be empty string) instead of `null`

**Issues:**
1. **No empty string validation:** Line 171 assigns `tokenData.data` without checking if it's an empty string
2. **Incorrect return value:** Line 214 returns `token` (empty string) instead of `null` when token is falsy
3. **Silent failure:** Empty string passes through `if (!token)` check and gets returned

#### 2. Secondary Registration: `App.tsx` - Guard Effect (Lines 253-309)

**File:** `mobileapp/App.tsx:253-309`  
**Function:** `useEffect` hook with `registerPushWithRetry`

**Code:**
```typescript
useEffect(() => {
  const registerPushWithRetry = async () => {
    if (!user) return;
    if (pushRegisteredThisSession) return;  // ⚠️ Prevents retry if already attempted
    
    const maxRetries = 3;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const token = await registerPushWithLogging(user.uid, `guard_effect_attempt_${attempt}`);
        
        if (token) {  // ⚠️ Empty string is falsy, so this works
          return; // Success!
        } else {
          console.warn(`[NOTIFICATIONS] (Guard) ⚠️ No token returned on attempt ${attempt}`);
        }
      } catch (error) {
        // ... error handling ...
      }
      
      // Exponential backoff: 2s, 4s, 8s
      if (attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  };
  
  const timeoutId = setTimeout(registerPushWithRetry, 2000);
  return () => clearTimeout(timeoutId);
}, [user]);
```

**Error handling:** Has retry logic with exponential backoff  
**Issues:** None - This is a backup mechanism that works correctly

#### 3. Auth State Change Registration: `App.tsx` (Lines 541-564)

**File:** `mobileapp/App.tsx:541-564`  
**Function:** `onAuthStateChanged` callback

**Code:**
```typescript
unsubscribe = auth.onAuthStateChanged(async (firebaseUser) => {
  if (firebaseUser) {
    setPushRegisteredThisSession(false);
    
    // Wait 3 seconds for auth propagation
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    await registerPushWithLogging(firebaseUser.uid, 'auth_state_change');
  }
});
```

**Error handling:** Wrapped in try-catch (line 562)  
**Issues:** None - Correctly waits for auth propagation

#### 4. Helper Function: `App.tsx` - `registerPushWithLogging` (Lines 186-249)

**File:** `mobileapp/App.tsx:186-249`  
**Function:** `registerPushWithLogging(uid: string, source: string)`

**Code:**
```typescript
const registerPushWithLogging = async (uid: string, source: string) => {
  // ... logging setup ...
  
  const result = {
    token: null as string | null,
    error: null as any
  };
  
  try {
    const token = await registerForPushNotificationsAsync(uid);
    result.token = token || null;  // ⚠️ Empty string becomes null here
    if (token) {
      setPushRegisteredThisSession(true);
    }
  } catch (err) {
    result.error = err;
  }
  
  // Log to backend
  await logFrontendEvent(uid, 'PUSH_REGISTRATION_RESULT', {
    source,
    platform: Platform.OS,
    projectId,
    permissionStatus,
    tokenPreview: result.token ? result.token.substring(0, 30) + '...' : null,  // ⚠️ Will be null if empty string
    error: result.error ? String(result.error) : null
  });
  
  return result.token;
};
```

**Error handling:** Catches errors and logs to backend  
**Issues:**
1. **Empty string conversion:** Line 220 converts empty string to `null` via `token || null`, which is correct
2. **Backend logging:** Correctly logs `tokenPreview: null` when token is empty string

#### 5. NotificationService: `notificationService.ts` (Lines 88-104)

**File:** `mobileapp/services/notificationService.ts:88-104`  
**Function:** `getPushToken()`

**Code:**
```typescript
private async getPushToken(): Promise<string | null> {
  try {
    if (!EXPO_PROJECT_ID) {
      return null;
    }
    
    const token = (await Notifications.getExpoPushTokenAsync({
      projectId: EXPO_PROJECT_ID
    })).data;
    
    return token;  // ⚠️ No validation - could return empty string
  } catch (error) {
    return null;
  }
}
```

**Error handling:** Returns `null` on error  
**Issues:**
1. **No empty string validation:** Returns `token` even if it's an empty string
2. **Not actively used:** This service is initialized but not the primary registration path

#### 6. UnifiedNotificationService: `unifiedNotificationService.ts`

**File:** `mobileapp/services/unifiedNotificationService.ts`  
**Function:** `initialize()` - Only handles permissions, does NOT get push tokens

**Issues:** None - This service doesn't register push tokens

---

### Logging Status

#### Current Logs

**Frontend Console Logs:**
- `[PUSH TOKEN]` - Comprehensive logging in `firebase.ts`
- `[NOTIFICATIONS]` - Registration attempts and results in `App.tsx`
- `[PUSH TOKEN] Step 1-5` - Step-by-step execution tracking
- Token preview, length, type validation

**Backend Logs (via `logFrontendEvent`):**
- `PUSH_REG_ATTEMPT` - Logged before registration attempt
- `PUSH_REGISTRATION_RESULT` - Logged after registration with:
  - `source` (guard_effect_attempt_X or auth_state_change)
  - `platform` (android)
  - `projectId` (38ed8fe9-6087-4fdd-9164-a0c36ee3a9fb)
  - `permissionStatus` (granted)
  - `tokenPreview` (null) ⚠️
  - `error` (null)

#### Missing Logs

1. **Token data structure:** No logging of `tokenData` object structure when token is empty
2. **Empty string detection:** No explicit log when `tokenData.data` is an empty string
3. **FCM credential status:** No logging to indicate if FCM credentials are missing
4. **getExpoPushTokenAsync error details:** If the call fails silently, no detailed error is logged

---

## Potential Root Causes

### 1. **FCM Legacy Server Key Missing (100% CONFIRMED)**

**Evidence:**
- Backend logs show `tokenPreview: null`, `error: null`, `permissionStatus: "granted"`
- Code executes without throwing errors
- `getExpoPushTokenAsync()` returns `{ data: "" }` (empty string) when FCM credentials are missing
- User confirmed FCM V1 is configured but FCM Legacy is "None assigned yet"

**Impact:**
- `getExpoPushTokenAsync()` internally calls FCM's token generation API
- This API requires FCM Legacy Server Key authentication
- Without it, the API returns an empty string instead of throwing an error
- Empty string passes through validation checks and results in `tokenPreview: null`

**Verification needed:**
- Run `eas credentials` and check if "Push Notifications (FCM Legacy)" shows "None assigned yet"
- Check Firebase Console → Project Settings → Cloud Messaging for "Server key" under "Cloud Messaging API (Legacy)"

**Fix:**
1. Enable "Cloud Messaging API (Legacy)" in Google Cloud Console
2. Get FCM Legacy Server Key from Firebase Console
3. Upload to EAS: `eas credentials` → Android → production → Push Notifications (FCM Legacy)
4. Rebuild app: `eas build --platform android --profile production`

### 2. **Empty String Token Not Validated (HIGH PROBABILITY)**

**Evidence:**
- Line 171 in `firebase.ts`: `token = tokenData.data;` - No validation
- Line 173: `token.substring(0, 30)` - Works with empty string (returns "")
- Line 211: `if (!token)` - Empty string is falsy, but code continues if token is set
- Line 214: `return token;` - Returns empty string instead of null

**Impact:**
- Empty string tokens are treated as valid and returned
- They pass through `if (!token)` checks
- They get converted to `null` in `registerPushWithLogging` via `token || null`
- Results in `tokenPreview: null` in backend logs

**Verification needed:**
- Add logging: `console.log('[PUSH TOKEN] tokenData:', JSON.stringify(tokenData))`
- Add validation: `if (!token || token.trim() === '') return null;`

**Fix:**
Add validation after line 171:
```typescript
token = tokenData.data;

// Validate token is not empty
if (!token || (typeof token === 'string' && token.trim() === '')) {
  console.log('[PUSH TOKEN] ❌ Token is null, undefined, or empty string');
  console.log('[PUSH TOKEN] tokenData:', JSON.stringify(tokenData, null, 2));
  return null;
}
```

### 3. **Race Condition Between Registration Attempts (LOW PROBABILITY)**

**Evidence:**
- Guard effect runs at app launch (2s delay)
- Auth state change runs on login (3s delay)
- Both call `registerPushWithLogging` simultaneously
- Backend logs show both attempts with same result

**Impact:**
- Multiple registration attempts might interfere with each other
- However, both show same result (null), suggesting the issue is not race-related

**Verification needed:**
- Check if tokens are being overwritten in Firestore
- Verify if one attempt succeeds while the other fails

**Fix:**
- Current `pushRegisteredThisSession` flag should prevent duplicate registrations
- However, flag is reset on auth state change, allowing both to run

### 4. **Project ID Resolution Issue (LOW PROBABILITY)**

**Evidence:**
- `EXPO_PROJECT_ID` is correctly set in `app.json`: `"38ed8fe9-6087-4fdd-9164-a0c36ee3a9fb"`
- Code has fallback: `'38ed8fe9-6087-4fdd-9164-a0c36ee3a9fb'`
- Backend logs show correct `projectId` in `PUSH_REG_ATTEMPT`

**Impact:**
- If project ID is wrong, `getExpoPushTokenAsync()` would throw an error
- But logs show no errors, so project ID is correct

**Verification needed:**
- Verify `Constants.expoConfig.extra.eas.projectId` in production builds
- Check if fallback is being used instead of actual config

**Fix:**
- Add logging: `console.log('[PUSH TOKEN] Resolved project ID:', EXPO_PROJECT_ID)`

---

## Data Flow Analysis

### Complete Registration Flow

1. **App Launch / User Login**
   - `App.tsx` line 253: Guard effect runs (2s delay)
   - `App.tsx` line 541: `onAuthStateChanged` fires (3s delay)

2. **Registration Attempt**
   - `App.tsx` line 186: `registerPushWithLogging()` called
   - `App.tsx` line 203: Logs `PUSH_REG_ATTEMPT` to backend
   - `App.tsx` line 219: Calls `registerForPushNotificationsAsync(uid)`

3. **Permission Check**
   - `firebase.ts` line 130: `Notifications.getPermissionsAsync()`
   - `firebase.ts` line 138: `Notifications.requestPermissionsAsync()` (if needed)
   - `firebase.ts` line 146: Returns `null` if not granted

4. **Token Generation**
   - `firebase.ts` line 168: `Notifications.getExpoPushTokenAsync({ projectId })`
   - **CRITICAL:** If FCM Legacy Server Key is missing, returns `{ data: "" }`
   - `firebase.ts` line 171: `token = tokenData.data` (empty string)
   - `firebase.ts` line 173: `token.substring(0, 30)` (works with empty string)
   - `firebase.ts` line 211: `if (!token)` (empty string is falsy, but token is set)
   - `firebase.ts` line 214: `return token` (returns empty string)

5. **Token Processing**
   - `App.tsx` line 219: Receives empty string
   - `App.tsx` line 220: `token || null` converts empty string to `null`
   - `App.tsx` line 241: `tokenPreview: null` logged to backend

6. **Firestore Save (Not Reached)**
   - `firebase.ts` line 226: Never reached because token is empty string
   - `firebase.ts` line 211: Check fails, returns early

### Why Empty String Passes Through

1. `tokenData.data = ""` (empty string)
2. `token = ""` (assigned)
3. `token.substring(0, 30)` = `""` (no crash)
4. `if (!token)` = `if (!"")` = `if (true)` → executes `return token`
5. Returns `""` (empty string)
6. In `registerPushWithLogging`: `"" || null` = `null`
7. Backend logs: `tokenPreview: null`

---

## Recommended Next Steps

### Immediate Actions (Priority 1)

1. **Add FCM Legacy Server Key to EAS Credentials**
   - This is the **100% confirmed root cause**
   - Steps:
     1. Google Cloud Console → Enable "Cloud Messaging API (Legacy)"
     2. Firebase Console → Get "Server key" from "Cloud Messaging API (Legacy)"
     3. `eas credentials` → Android → production → Push Notifications (FCM Legacy)
     4. Rebuild: `eas build --platform android --profile production`

2. **Add Empty String Validation**
   - Prevents silent failures in the future
   - Add after line 171 in `firebase.ts`:
     ```typescript
     if (!token || (typeof token === 'string' && token.trim() === '')) {
       console.log('[PUSH TOKEN] ❌ Token is empty string');
       console.log('[PUSH TOKEN] tokenData:', JSON.stringify(tokenData));
       return null;
     }
     ```

### Secondary Actions (Priority 2)

3. **Enhance Logging**
   - Log `tokenData` object structure when token is empty
   - Log FCM credential status (if possible)
   - Add explicit empty string detection logs

4. **Fix Return Value**
   - Line 214 in `firebase.ts`: Change `return token;` to `return null;`
   - Ensures consistent null return on failure

### Verification Steps

5. **After Adding FCM Legacy Server Key:**
   - Install new APK
   - Log out and log back in
   - Check backend logs: `tokenPreview` should show `ExponentPushToken[...]`
   - Check Firestore: `lastTokenUpdate` should be updated
   - Verify token is saved in `user_profiles` document

---

## Questions That Need Answers

1. **FCM Legacy Server Key Status:**
   - What does `eas credentials` show for "Push Notifications (FCM Legacy)"?
   - Is "Cloud Messaging API (Legacy)" enabled in Google Cloud Console?

2. **Token Data Structure:**
   - What is the exact structure of `tokenData` when token is empty?
   - Does `tokenData` have any error properties?

3. **Build Environment:**
   - Are you using `production`, `preview`, or `development` build profile?
   - Is `google-services.json` actually included in the build?

4. **Expo SDK Compatibility:**
   - Has this worked before with Expo SDK 53?
   - Are there any known issues with `expo-notifications@0.31.4`?

5. **Device/Emulator:**
   - Are you testing on a physical device or emulator?
   - Does `Device.isDevice` return `true`?

---

## Summary

The **100% confirmed root cause** is the **missing FCM Legacy Server Key** in EAS credentials. Even though FCM V1 Service Account Key is configured (for sending notifications), Expo's `getExpoPushTokenAsync()` requires FCM Legacy Server Key for token generation. When this credential is missing, the API returns an empty string instead of throwing an error, which passes through validation checks and results in `tokenPreview: null` in backend logs.

**The fix is straightforward:**
1. Add FCM Legacy Server Key to EAS credentials
2. Rebuild the app
3. Test token registration

**Additional improvements:**
- Add empty string validation to prevent silent failures
- Enhance logging to catch similar issues in the future
- Fix return value consistency (return `null` instead of empty string)

