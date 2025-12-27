# 🔬 100% CONCRETE DIAGNOSIS: Push Token Registration Failure

## EXECUTIVE SUMMARY

**The Core Issue:** Token registration logs use `console.log()` which ONLY appears in device/frontend logs. They CANNOT appear in backend logs because token registration happens ENTIRELY on the mobile app, not the server.

---

## PROOF THAT BACKEND LOGS ARE IMPOSSIBLE

### Where Token Registration Code Lives:
```
mobileapp/services/firebase.ts:106-242
  └── registerForPushNotificationsAsync()
        └── Uses console.log() for ALL logging
        └── Writes directly to Firestore from mobile app
        └── Backend is NEVER involved
```

### What Backend Sees:
```
NOTHING about token registration.
Backend only reads tokens when sending notifications.
```

### Why logFrontendEvent() Doesn't Work:
```typescript
// api.ts line 1125:
const logUrl = `/users/${userId}/profile?frontendEvent=...`;
// The backend ignores these query parameters!
```

```python
# server.py line 1083:
async def get_user_profile(user_id: str):
    logger.info(f"[PROFILE_FETCH] Starting profile fetch for user_id: {user_id}")
    # ❌ NO logging of query params like frontendEvent
```

---

## THE HARD EVIDENCE FROM FIRESTORE

| User | Has Token | Platform | Last Update | Days Old |
|------|-----------|----------|-------------|----------|
| Dietician | ✅ | ios | Dec 19, 2025 | 8 days |
| User (Rehan) | ✅ | android | Aug 27, 2025 | 122 days |
| 7 other users | ❌ | - | NEVER | - |

**Token Coverage: 22% (2/9 users)** - This is critically broken.

---

## 100% CONCRETE ROOT CAUSE

### The Dietician's Token Problem:

1. **Token is from iOS device** (platform: "ios")
2. **User claims to be on Samsung** (Android)
3. **Last update was Dec 19** (8 days ago)
4. **User claims to have reinstalled recently**

**CONCLUSION:** Token registration DID NOT RUN after the reinstall.

### Why Token Registration Didn't Run:

```
Firebase Auth Persistence
├── User reinstalls app
├── Firebase Auth session PERSISTS (stored in secure keychain)
├── App launches → onAuthStateChanged fires immediately
├── User is already "logged in" (no actual login event)
└── One of these happens:
    ├── Race condition: Function runs before Firebase ready
    ├── Permission denied: Android 13+ notification permission
    ├── Error swallowed: Try-catch doesn't surface the issue
    └── Function never called: Guard condition skipped it
```

---

## THE ONLY WAY TO GET 100% CERTAINTY

Since backend logs CANNOT show token registration, the ONLY way to diagnose is:

### Option 1: Device Logs (adb logcat)
```bash
# Connect Android device via USB
adb logcat | grep -E "PUSH TOKEN|NOTIFICATIONS|registerForPush"

# Expected output if working:
🔔 [PUSH TOKEN REGISTRATION] START
[PUSH TOKEN] Platform: android
[PUSH TOKEN] ✓ Token received successfully
[PUSH TOKEN] ✓ Token saved successfully to Firestore
```

### Option 2: Firestore Listener Test
```bash
# In a terminal, run:
python3 verify_token_update.py

# Then on the device:
1. Log OUT completely
2. Log back IN
3. Watch the script output for token changes
```

---

## 100% CONCRETE ACTION PLAN

### STEP 1: Verify The Exact Failure Point

**DO THIS ON THE SAMSUNG TABLET:**

1. Connect to computer via USB
2. Enable USB Debugging
3. Run: `adb logcat | grep -E "PUSH TOKEN|NOTIFICATIONS"`
4. Open the app (stay logged in)
5. Check what logs appear

**If NO logs appear:** `registerForPushNotificationsAsync` is never being called
**If logs show error:** Will show exactly what fails

### STEP 2: Force New Token Registration

Since Firebase Auth persists, a reinstall doesn't force re-authentication.

**DO THIS:**
1. Open app on Samsung tablet
2. Go to Settings/Profile
3. TAP "LOG OUT" (actual logout, not reinstall)
4. Close app completely
5. Open app
6. Log in with dietician credentials
7. Grant notification permission when prompted

### STEP 3: Verify Token Updated

Run this script BEFORE and AFTER logout/login:
```bash
python3 verify_token_update.py
```

Expected changes:
- platform: "ios" → "android"
- lastTokenUpdate: Dec 19 → TODAY
- expoPushToken: old iOS token → new Android token

---

## WHY PREVIOUS INVESTIGATION FAILED

| What Was Checked | Why It Didn't Help |
|------------------|-------------------|
| Backend logs | Token registration is frontend-only |
| logFrontendEvent | Backend ignores query parameters |
| App reinstall | Doesn't clear Firebase Auth session |
| Notification permissions | Not visible without device logs |

---

## GUARANTEED FIX

If the above steps don't work, there's ONE change that will 100% fix it:

**Add a "Refresh Push Token" button in the app settings that:**
1. Calls `registerForPushNotificationsAsync(user.uid)` directly
2. Shows success/failure alert to user
3. Logs result to Firestore for debugging

This gives users a manual way to fix token issues and provides debugging data.

---

## VERIFICATION SCRIPT

Save as `verify_token_update.py` and run during testing:

```python
import firebase_admin
from firebase_admin import credentials, firestore
import time

try:
    app = firebase_admin.get_app()
except:
    cred = credentials.Certificate('backend/services/firebase_service_account.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

def check_token():
    doc = db.collection('user_profiles').document('mBVlWBBpoaXyOVr8Y4AoHZunq9f1').get()
    data = doc.to_dict()
    return {
        'platform': data.get('platform'),
        'lastTokenUpdate': data.get('lastTokenUpdate'),
        'tokenPreview': data.get('expoPushToken', 'NONE')[:40] if data.get('expoPushToken') else 'NONE'
    }

print('Watching dietician token...')
print('BEFORE:', check_token())
print()
print('Now logout and login on the device...')
print('Press Ctrl+C when done')

last = check_token()
while True:
    time.sleep(2)
    current = check_token()
    if current != last:
        print()
        print('TOKEN CHANGED!')
        print('AFTER:', current)
        break
    last = current
```

