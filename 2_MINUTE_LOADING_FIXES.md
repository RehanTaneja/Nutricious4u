# 2-Minute Loading Issue - Critical Fixes

## 🔴 Root Causes Identified

### Issue 1: API Timeout Too Long (60 seconds)
**Location**: `mobileapp/services/api.ts` (Line 151, 168)

**Problem**:
- iOS API timeout is set to **60 seconds**
- If an API call hangs, user waits full 60 seconds
- Multiple sequential API calls = multiple 60-second waits

**Current Code**:
```typescript
timeout: Platform.OS === 'ios' ? 60000 : 25000, // 60 seconds for iOS
```

**Impact**: Each hanging API call = 60 seconds of waiting

---

### Issue 2: Safety Timeout Cleared Too Early
**Location**: `mobileapp/App.tsx` (Line 523-530, 590)

**Problem**:
- Safety timeout set to 20 seconds (iOS) / 15 seconds (Android)
- But timeout is cleared in `finally` block (line 590) **before** login sequence completes
- If login sequence takes longer, timeout never fires

**Current Flow**:
```
1. Set timeout (20s for iOS)
2. Start login sequence
3. Login sequence takes 60+ seconds (API hangs)
4. Timeout should fire at 20s, but...
5. If any error occurs, finally block clears timeout
6. User waits full 60+ seconds
```

**Impact**: Safety timeout doesn't protect against long API hangs

---

### Issue 3: Sequential API Calls with Long Timeouts
**Location**: `mobileapp/App.tsx` (Line 900-963)

**Problem**:
- Profile check: Up to 60s timeout
- Subscription check: Up to 30s timeout (line 913)
- Daily reset: Up to 15s timeout (line 421)
- Lock status: Up to 12s timeout (line 463)

**Sequential Execution**:
```
1. Profile check (60s max) → 60s if hangs
2. Wait 2s delay
3. Subscription check (30s max) → 30s if hangs
4. Wait 2s delay
5. Daily reset (15s max) → 15s if hangs
6. Wait 2s delay
7. Lock status (12s max) → 12s if hangs
─────────────────────────────────────────
TOTAL: 60 + 2 + 30 + 2 + 15 + 2 + 12 = 123 seconds (2+ minutes)
```

**Impact**: If all API calls hang, user waits 2+ minutes

---

### Issue 4: getUserProfileSafe Blocks on Login
**Location**: `mobileapp/services/api.ts` (Line 761-770)

**Problem**:
- If login is in progress, waits 2 seconds
- Then makes API call (60s timeout)
- Total: 62 seconds if API hangs

**Current Code**:
```typescript
if (isLoginInProgress()) {
  await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s
}
return getUserProfile(userId); // Then 60s timeout
```

**Impact**: Adds 2 seconds + potential 60s wait

---

### Issue 5: No Early Exit for New Users
**Location**: `mobileapp/App.tsx` (Line 846-898)

**Problem**:
- New users wait through all delays and API calls
- Even though they have no profile/subscription
- Should exit early but doesn't

**Impact**: New users wait unnecessarily

---

## 🔧 Proposed Fixes (Priority Order)

### Fix 1: Reduce API Timeout (CRITICAL)
**Location**: `mobileapp/services/api.ts` (Line 151, 168)

**Change**: Reduce iOS timeout from 60s to 15s
```typescript
// Current:
timeout: Platform.OS === 'ios' ? 60000 : 25000, // 60 seconds

// Should be:
timeout: Platform.OS === 'ios' ? 15000 : 10000, // 15 seconds for iOS, 10s for Android
```

**Impact**: Reduces max wait per API call from 60s to 15s

---

### Fix 2: Fix Safety Timeout Logic (CRITICAL)
**Location**: `mobileapp/App.tsx` (Line 523-530, 590)

**Change**: Don't clear timeout until login actually completes
```typescript
// Current:
finally {
  setLoading(false);
  if (timeoutId) clearTimeout(timeoutId); // Cleared too early
}

// Should be:
// Don't clear timeout in finally - let it fire if needed
// Only clear when login sequence actually completes
```

**Better Approach**: Move timeout clearing to end of login sequence
```typescript
// At end of successful login sequence (line 1032-1035):
setCheckingProfile(false);
isLoginInProgress = false;
if (timeoutId) clearTimeout(timeoutId); // Clear here instead
```

**Impact**: Safety timeout actually protects against long waits

---

### Fix 3: Early Exit for New Users (HIGH PRIORITY)
**Location**: `mobileapp/App.tsx` (Line 846-898)

**Change**: Exit immediately if no profile
```typescript
// Check profile first (no delay needed)
profile = await getUserProfile(firebaseUser.uid).catch(() => null);

if (!profile && !isDieticianAccount) {
  // New user - exit immediately
  setHasCompletedQuiz(false);
  setHasActiveSubscription(false);
  setIsFreeUser(true);
  setCheckingProfile(false);
  isLoginInProgress = false;
  (global as any).isLoginInProgress = false;
  if (timeoutId) clearTimeout(timeoutId);
  return; // Exit early - skip all other checks
}
```

**Impact**: New users complete in < 5 seconds instead of 2+ minutes

---

### Fix 4: Reduce Subscription Check Timeout (HIGH PRIORITY)
**Location**: `mobileapp/App.tsx` (Line 913)

**Change**: Reduce from 30s to 10s
```typescript
// Current:
setTimeout(() => reject(new Error('Subscription check timeout')), __DEV__ ? 15000 : 30000)

// Should be:
setTimeout(() => reject(new Error('Subscription check timeout')), 10000) // 10s for all
```

**Impact**: Reduces subscription check wait from 30s to 10s

---

### Fix 5: Make Push Registration Non-Blocking (MEDIUM PRIORITY)
**Location**: `mobileapp/App.tsx` (Line 645-656)

**Change**: Don't wait for push registration
```typescript
// Current (BLOCKING):
await new Promise(resolve => setTimeout(resolve, 3000));
await registerPushWithLogging(firebaseUser.uid, 'auth_state_change');

// Should be (NON-BLOCKING):
registerPushWithLogging(firebaseUser.uid, 'auth_state_change').catch(err => {
  console.error('[NOTIFICATIONS] Push registration failed:', err);
});
// Continue immediately
```

**Impact**: Saves 3+ seconds

---

### Fix 6: Reduce All Delays (MEDIUM PRIORITY)
**Location**: `mobileapp/App.tsx` (Line 850, 904, 944, 954)

**Change**: Reduce or remove delays
```typescript
// Current delays:
- Profile check: 1000ms → Remove (not needed)
- Subscription check: 2000ms → 500ms
- Daily reset: 2000ms → Remove (can run after login)
- Lock status: 2000ms → Remove (can run after login)
```

**Impact**: Saves 5+ seconds

---

### Fix 7: Parallel Non-Critical Operations (LOW PRIORITY)
**Location**: `mobileapp/App.tsx` (Line 900-963)

**Change**: Run daily reset and lock status after login completes
```typescript
// Current (Sequential):
await subscription check
await daily reset
await lock status

// Should be:
await subscription check
// Complete login first
setCheckingProfile(false);
// Then run non-critical operations in background
Promise.all([
  checkAndResetDailyData().catch(() => {}),
  checkAppLockStatus().catch(() => {})
]);
```

**Impact**: Login completes faster, non-critical ops run in background

---

## 📊 Expected Improvement

### Current (Worst Case):
```
- Push registration: 3s
- Profile check: 60s (if hangs)
- Subscription check: 30s (if hangs)
- Daily reset: 15s (if hangs)
- Lock status: 12s (if hangs)
- Delays: 10s
─────────────────────────────
TOTAL: 130+ seconds (2+ minutes)
```

### After Fixes (Worst Case):
```
- Push registration: 0s (non-blocking)
- Profile check: 15s max (reduced timeout)
- Early exit for new users: < 1s
- Subscription check: 10s max (reduced timeout)
- Daily reset: Background (non-blocking)
- Lock status: Background (non-blocking)
- Delays: 0.5s (reduced)
─────────────────────────────
TOTAL: < 30 seconds (worst case)
NEW USERS: < 5 seconds
```

---

## 🎯 Implementation Priority

1. **Fix 1**: Reduce API timeout (CRITICAL) - Prevents 60s waits
2. **Fix 2**: Fix safety timeout (CRITICAL) - Actually protects users
3. **Fix 3**: Early exit for new users (HIGH) - Most users are new
4. **Fix 4**: Reduce subscription timeout (HIGH) - Common operation
5. **Fix 5**: Non-blocking push (MEDIUM) - Saves 3s
6. **Fix 6**: Reduce delays (MEDIUM) - Saves 5s
7. **Fix 7**: Parallel operations (LOW) - Nice to have

---

## ⚠️ Important Notes

- **API timeout of 60s is too long** - Most API calls should complete in < 5 seconds
- **Safety timeout doesn't work** - It's cleared before it can fire
- **New users wait unnecessarily** - Should exit immediately
- **Sequential execution multiplies delays** - Parallel where possible
