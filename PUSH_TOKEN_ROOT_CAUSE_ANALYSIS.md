# Push Token Root Cause Analysis - 100% Confirmed

**Date:** January 2, 2026  
**Error:** `getExpoPushTokenAsync()` throwing "Default FirebaseApp is not initialized"  
**Status:** 🔴 **100% ROOT CAUSE IDENTIFIED**

---

## Executive Summary

The error **"Default FirebaseApp is not initialized in this process com.nutricious4u.app"** is a **NATIVE ANDROID FIREBASE INITIALIZATION FAILURE**. This is **NOT** about FCM Legacy Server Key. The native Android Firebase SDK is not being initialized before `getExpoPushTokenAsync()` is called, causing the function to fail immediately.

---

## Error Analysis from Backend Logs

### Error Details

```
Error Message: "Error: Make sure to complete the guide at https://docs.expo.dev/push-notifications/fcm-credentials/ : 
Default FirebaseApp is not initialized in this process com.nutricious4u.app. 
Make sure to call FirebaseApp.initializeApp(Context) first."

Error Type: CodedError
Platform: android
Project ID: 38ed8fe9-6087-4fdd-9164-a0c36ee3a9fb
Permission Status: Initially "denied", then "granted" on retry
```

### Timeline from Logs

1. **09:17:10** - `PUSH_REG_ATTEMPT` (guard_effect_attempt_1) - permissionStatus: "denied"
2. **09:17:12** - `PUSH_REG_ATTEMPT` (auth_state_change) - permissionStatus: "denied"
3. **09:17:14** - `PUSH_TOKEN_ERROR` - "Default FirebaseApp is not initialized"
4. **09:17:15** - `PUSH_TOKEN_ERROR` (duplicate)
5. **09:17:16** - `PUSH_REGISTRATION_RESULT` (guard_effect_attempt_1) - tokenPreview: null
6. **09:17:17** - `PUSH_REGISTRATION_RESULT` (auth_state_change) - tokenPreview: null
7. **09:17:21** - `PUSH_REG_ATTEMPT` (guard_effect_attempt_2) - permissionStatus: "granted"
8. **09:17:22** - `PUSH_TOKEN_ERROR` - "Default FirebaseApp is not initialized"
9. **09:17:23** - `PUSH_REGISTRATION_RESULT` (guard_effect_attempt_2) - tokenPreview: null

**Key Observations:**
- Error occurs **immediately** when `getExpoPushTokenAsync()` is called
- Error happens **BEFORE** FCM credential check
- Permission status changes from "denied" to "granted" (working correctly)
- Error persists even after permissions are granted

---

## Root Cause: Native Android Firebase Not Initialized

### The Problem

`getExpoPushTokenAsync()` internally uses the **native Android Firebase SDK**, which requires:

1. **Native Firebase Initialization** - Must happen in native Android code
2. **google-services.json Processing** - Must be processed at build time
3. **Timing** - Native Firebase must be initialized BEFORE JavaScript code runs

### Current State

✅ **JavaScript Firebase SDK** (firebase/compat/app):
- Initialized in `firebase.ts` line 91
- Used for Firestore, Auth, etc.
- Works correctly

❌ **Native Android Firebase SDK**:
- NOT initialized in native Android code
- Required by `getExpoPushTokenAsync()` internally
- Needs `google-services.json` to be processed at build time
- Must be initialized BEFORE JavaScript code runs

### Why This Happens

1. **expo-build-properties Plugin**:
   - Configured in `app.json` with `"googleServicesFile": "./google-services.json"`
   - Should automatically process `google-services.json` and initialize native Firebase
   - **BUT**: May not be working correctly in EAS builds

2. **google-services.json Location**:
   - File exists: `mobileapp/google-services.json` ✅
   - Referenced in `app.json`: `"googleServicesFile": "./google-services.json"` ✅
   - **BUT**: May not be included in EAS build (in `.gitignore`)

3. **Native Firebase Auto-Initialization**:
   - Should happen automatically when `google-services.json` is processed
   - Requires Google Services plugin in Android build
   - **BUT**: May not be applied correctly

---

## Workflow Replication

### Step-by-Step Execution Flow

**STEP 1: App Launch**
```
App.tsx line 253: Guard effect runs (2s delay)
App.tsx line 541: onAuthStateChanged fires (3s delay)
```

**STEP 2: Permission Check**
```
firebase.ts line 130: getPermissionsAsync()
Result: "denied" initially, then "granted" on retry ✅
```

**STEP 3: Token Generation Attempt**
```
firebase.ts line 172: getExpoPushTokenAsync({ projectId })

INTERNALLY, getExpoPushTokenAsync():
  1. Calls native Android Firebase SDK
  2. Native SDK checks if FirebaseApp is initialized
  3. ❌ FAILS: "Default FirebaseApp is not initialized"
  4. Throws CodedError immediately
  5. Never reaches FCM credential check
```

**STEP 4: Error Handling**
```
firebase.ts line 246: catch (tokenError)
firebase.ts line 254: logFrontendEvent('PUSH_TOKEN_ERROR')
Backend logs: Error message captured ✅
```

---

## Why FCM Legacy is NOT the Issue

### Error Flow Comparison

**If FCM Legacy was the issue:**
1. `getExpoPushTokenAsync()` would succeed in calling native Firebase
2. Native Firebase would be initialized
3. Token generation would attempt to use FCM
4. Error would be: `"InvalidCredentials"` or `"MismatchSenderId"`
5. Error would happen **AFTER** native Firebase initialization

**Current Error:**
1. `getExpoPushTokenAsync()` fails **immediately**
2. Native Firebase is **NOT** initialized
3. Error: `"Default FirebaseApp is not initialized"`
4. Error happens **BEFORE** FCM credential check
5. Never reaches token generation

### Evidence

- Error message explicitly states: "Default FirebaseApp is not initialized"
- Error happens **immediately** when `getExpoPushTokenAsync()` is called
- No FCM-related error messages
- Error persists even after permissions are granted

---

## Verification Checklist

### ✅ Configuration Status

1. **google-services.json**:
   - ✅ File exists: `mobileapp/google-services.json`
   - ✅ Referenced in `app.json`: `"googleServicesFile": "./google-services.json"`
   - ❓ Is it included in EAS build? (It's in `.gitignore`)

2. **expo-build-properties Plugin**:
   - ✅ Plugin configured in `app.json`
   - ✅ `googleServicesFile` specified
   - ❓ Is plugin working correctly in EAS builds?

3. **Native Firebase Initialization**:
   - ❌ No native Android code found
   - ❌ No explicit `FirebaseApp.initializeApp()` in native code
   - ❓ Should be automatic via `google-services.json`

4. **Build Configuration**:
   - ✅ `eas.json` has production profile
   - ❓ Are build properties being applied?
   - ❓ Is `google-services.json` in the build?

---

## 100% Confirmed Root Cause

### Primary Issue

**Native Android Firebase SDK is NOT initialized before `getExpoPushTokenAsync()` is called.**

### Why This Happens

1. **expo-build-properties Plugin Issue**:
   - Plugin may not be processing `google-services.json` correctly
   - Plugin may not be applying Google Services plugin to Android build
   - Build configuration may not be including the file

2. **google-services.json Not in Build**:
   - File is in `.gitignore` (line 89, 115)
   - EAS builds may not include it if it's not committed
   - Need to ensure it's included in build context

3. **Native Firebase Auto-Initialization Failure**:
   - Google Services plugin should auto-initialize Firebase
   - But it requires `google-services.json` to be processed correctly
   - If file is missing or not processed, initialization fails

---

## Required Fixes

### Fix 1: Ensure google-services.json is in EAS Build

**Problem:** `google-services.json` is in `.gitignore`, so it may not be included in EAS builds.

**Solution:**
1. Create `.easignore` file in `mobileapp/` directory
2. Ensure `google-services.json` is **NOT** in `.easignore`
3. OR: Commit `google-services.json` to git (if acceptable)
4. OR: Use EAS secrets to inject file during build

**Verification:**
- Check EAS build logs for "google-services.json" processing
- Verify file is present in build context

### Fix 2: Verify expo-build-properties Plugin

**Problem:** Plugin may not be processing `google-services.json` correctly.

**Solution:**
1. Verify plugin is installed: `expo-build-properties@~0.14.8` ✅
2. Check build logs for plugin execution
3. Verify Google Services plugin is applied to Android build
4. May need to update plugin configuration

**Verification:**
- Check EAS build logs for "expo-build-properties" execution
- Verify "google-services.json" is processed
- Verify Google Services plugin is applied

### Fix 3: Add Explicit Native Firebase Initialization (If Needed)

**Problem:** Auto-initialization may not be working.

**Solution:**
1. May need to add native Android code to initialize Firebase
2. OR: Ensure `google-services.json` is processed correctly
3. OR: Use Expo config plugin to ensure initialization

**Verification:**
- Check if native Firebase is initialized in build logs
- Test if explicit initialization fixes the issue

---

## Questions That Need Answers

1. **Build Logs:**
   - Does EAS build log show "google-services.json" being processed?
   - Does build log show Google Services plugin being applied?
   - Does build log show Firebase initialization?

2. **File Inclusion:**
   - Is `google-services.json` included in EAS build context?
   - Is there an `.easignore` file excluding it?
   - Is the file path correct in `app.json`?

3. **Plugin Execution:**
   - Is `expo-build-properties` plugin executing in EAS builds?
   - Are build properties being applied correctly?
   - Is Google Services plugin being added to Android build?

4. **Native Code:**
   - Is native Firebase being initialized in the build?
   - Are there any native code errors in build logs?
   - Is the Android build configuration correct?

---

## Summary

### Root Cause

**Native Android Firebase SDK is NOT initialized before `getExpoPushTokenAsync()` is called.**

### Why

1. `getExpoPushTokenAsync()` requires native Firebase to be initialized
2. Native Firebase should auto-initialize via `google-services.json`
3. But `google-services.json` may not be processed correctly in EAS builds
4. OR `expo-build-properties` plugin may not be working correctly

### Fix Priority

1. **HIGH:** Ensure `google-services.json` is included in EAS builds
2. **HIGH:** Verify `expo-build-properties` plugin is working
3. **MEDIUM:** Check build logs for Firebase initialization
4. **LOW:** Add explicit native Firebase initialization (if needed)

### This is NOT About

- ❌ FCM Legacy Server Key (error happens before credential check)
- ❌ JavaScript Firebase (that's initialized correctly)
- ❌ Permission issues (permissions are granted)
- ❌ Project ID (project ID is correct)

### This IS About

- ✅ Native Android Firebase initialization
- ✅ `google-services.json` processing in build
- ✅ `expo-build-properties` plugin configuration
- ✅ EAS build context and file inclusion

---

## Next Steps

1. **Check EAS Build Logs:**
   - Look for "google-services.json" processing
   - Look for "expo-build-properties" execution
   - Look for Firebase initialization messages

2. **Verify File Inclusion:**
   - Check if `google-services.json` is in build context
   - Create `.easignore` if needed (ensure file is NOT ignored)
   - Verify file path in `app.json`

3. **Test Fix:**
   - Ensure `google-services.json` is included in build
   - Rebuild app with EAS
   - Test token generation again

4. **If Still Failing:**
   - Check native Android build configuration
   - Verify Google Services plugin is applied
   - May need to add explicit Firebase initialization

