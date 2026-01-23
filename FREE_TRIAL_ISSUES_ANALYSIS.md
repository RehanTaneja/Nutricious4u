# Free Trial Issues Analysis

## Issues Identified

### Issue #1: My Diet Button Blocked for Free Trial Users

**Location:** `mobileapp/screens.tsx` line 1412-1418

**Problem:**
- `handleOpenDiet()` checks `isFreeUser` and blocks access if true
- `isFreeUser` is set to `true` for trial users because:
  - `SubscriptionContext.tsx` line 35: `setIsFreeUser(subscriptionStatus.isFreeUser || !subscriptionStatus.isSubscriptionActive)`
  - For trial users: `isSubscriptionActive = false`, so `isFreeUser` becomes `true`
  - Trial users should have access to their free trial diet PDF

**Root Cause:**
- `isFreeUser` logic doesn't account for `isTrialActive`
- Trial users are treated as free users, blocking diet access

**Fix Required:**
- Check `isTrialActive` before blocking diet access
- Allow trial users to access their diet PDF

---

### Issue #2: 3-Day Free Trial Countdown Not Showing

**Location:** `mobileapp/screens.tsx` line 1232-1290

**Problem:**
- Dashboard shows diet countdown (`daysLeft` from `getUserDiet`)
- No code to calculate/display trial countdown from `trialEndDate`
- Trial users see diet countdown (if diet exists) but not trial countdown

**Root Cause:**
- Missing logic to:
  1. Fetch `trialEndDate` from subscription status
  2. Calculate days/hours remaining until trial ends
  3. Display trial countdown on dashboard

**Fix Required:**
- Add trial countdown calculation from `trialEndDate`
- Display trial countdown separately from diet countdown
- Show "X days Y hours left in your free trial"

---

### Issue #3: Subscription Settings Shows "Unknown Plan"

**Location:** `mobileapp/screens.tsx` line 10963

**Problem:**
- Logic checks `subscription.isTrialActive` first (should show "Free Trial")
- If `isTrialActive` is false/undefined, falls back to `getPlanName(subscription.subscriptionPlan)`
- Backend sets `subscriptionPlan: "trial"` when trial is activated (line 5296 in `server.py`)
- But `getPlanName("trial")` should return "Free Trial" (line 10877)
- If `subscriptionPlan` is null/undefined, shows "No Plan" or "Unknown Plan"

**Root Cause:**
- Backend might not be setting `subscriptionPlan: "trial"` correctly
- Or frontend `subscription` object doesn't have `subscriptionPlan` field
- Or `isTrialActive` is not being set correctly

**Fix Required:**
- Verify backend sets `subscriptionPlan: "trial"` when trial is active
- Ensure frontend receives `subscriptionPlan` in subscription status
- Add fallback: if `isTrialActive` is true but plan is missing, show "Free Trial"

---

### Issue #4: Start and End Date Are Same

**Location:** `mobileapp/screens.tsx` line 10978-10989

**Problem:**
- Code shows start/end dates only if `!subscription.isTrialActive && !subscription.isFreeUser`
- For trial users: if `isTrialActive` is true, dates are hidden (correct)
- But if `isTrialActive` is false but user is on trial, dates might show incorrectly
- Backend might be setting `subscriptionStartDate` and `subscriptionEndDate` to same value for trial users

**Root Cause:**
- Backend might not be setting trial dates correctly
- Or `isTrialActive` check is preventing correct date display
- Trial users should only see `trialEndDate`, not subscription dates

**Fix Required:**
- Verify backend doesn't set `subscriptionStartDate`/`subscriptionEndDate` for trial users
- Ensure only `trialEndDate` is shown for trial users
- If dates are same, it's a backend issue setting dates incorrectly

---

## Backend Analysis

### Subscription Status Endpoint (`/api/subscription/status/{userId}`)

**Location:** `backend/server.py` line 4570-4632

**Current Logic:**
```python
isFreeUser = not user_data.get("isSubscriptionActive", False)
```

**Finding:**
- Trial activation (line 5298) sets `isSubscriptionActive = True` for trial users
- So `isFreeUser = False` for trial users (correct!)
- BUT frontend `SubscriptionContext` overrides this by checking `!subscriptionStatus.isSubscriptionActive` again

**Problem:**
- Backend correctly sets `isFreeUser = False` for trial users
- Frontend ignores this and recalculates `isFreeUser` incorrectly

**Fix Required:**
- Frontend should use backend's `isFreeUser` value, OR
- Frontend should check `isTrialActive` before setting `isFreeUser`

---

### Trial Activation Endpoint (`/api/subscription/activate-trial/{userId}`)

**Location:** `backend/server.py` line 5255-5325

**Current Logic:**
- Sets `subscriptionPlan: "trial"` (line 5296) ✅
- Sets `subscriptionStatus: "trial"` (line 5297) ✅
- Sets `freeTrialEndDate` (3 days from now) ✅
- Sets `isSubscriptionActive: True` (line 5298) ✅
- Sets `subscriptionStartDate` and `subscriptionEndDate` to same values (line 5299-5300) ❌

**Problem:**
- Line 5299-5300: Both `subscriptionStartDate` and `subscriptionEndDate` are set to `start_date` and `end_date`
- These are the trial start/end dates, so they appear the same in the UI
- Trial users shouldn't have `subscriptionStartDate`/`subscriptionEndDate` - only `trialEndDate`

**Fix Required:**
- Don't set `subscriptionStartDate`/`subscriptionEndDate` for trial users
- Only set `freeTrialStartDate` and `freeTrialEndDate`

---

## Frontend Analysis

### SubscriptionContext

**Location:** `mobileapp/contexts/SubscriptionContext.tsx` line 27-41

**Current Logic:**
```typescript
setIsFreeUser(subscriptionStatus.isFreeUser || !subscriptionStatus.isSubscriptionActive);
```

**Problem:**
- Doesn't check `isTrialActive`
- Trial users get `isFreeUser = true`

**Fix Required:**
```typescript
setIsFreeUser(
  !subscriptionStatus.isTrialActive && 
  (subscriptionStatus.isFreeUser || !subscriptionStatus.isSubscriptionActive)
);
```

---

### DashboardScreen

**Location:** `mobileapp/screens.tsx` line 1160-1462

**Missing:**
- Trial countdown calculation
- Trial countdown display

**Fix Required:**
- Fetch `trialEndDate` from subscription status
- Calculate days/hours remaining
- Display trial countdown widget

---

## Summary of Required Fixes

### Backend Fixes:
1. **`activate_free_trial`**: Remove `subscriptionStartDate` and `subscriptionEndDate` from update (lines 5299-5300)
   - Only set `freeTrialStartDate` and `freeTrialEndDate`
   - Don't set subscription dates for trial users
2. **`get_subscription_status`**: Already correct - sets `isFreeUser = False` when `isSubscriptionActive = True`
   - But could add explicit check: `isFreeUser = not (isSubscriptionActive or isTrialActive)`

### Frontend Fixes:
1. **`SubscriptionContext`** (line 35): Fix `isFreeUser` logic:
   ```typescript
   // Current (WRONG):
   setIsFreeUser(subscriptionStatus.isFreeUser || !subscriptionStatus.isSubscriptionActive);
   
   // Fixed:
   setIsFreeUser(
     !subscriptionStatus.isTrialActive && 
     (subscriptionStatus.isFreeUser || !subscriptionStatus.isSubscriptionActive)
   );
   ```

2. **`DashboardScreen.handleOpenDiet`** (line 1414): Allow access for trial users:
   ```typescript
   // Current (WRONG):
   if (isFreeUser) { ... }
   
   // Fixed: Need to check subscription status for isTrialActive
   // OR: Check if user has diet PDF available
   ```

3. **`DashboardScreen`**: Add trial countdown calculation and display
   - Fetch `trialEndDate` from subscription status
   - Calculate days/hours remaining
   - Display countdown widget

4. **`MySubscriptionsScreen`** (line 10963): Already has correct logic, but verify `subscriptionPlan` is received

---

## Test Cases to Verify

1. **Trial User Diet Access:**
   - User activates trial → Should be able to open diet PDF
   - `isFreeUser` should be `false` for trial users

2. **Trial Countdown:**
   - User activates trial → Should see "X days Y hours left in your free trial"
   - Countdown should update in real-time

3. **Subscription Settings:**
   - Trial user → Should see "Free Trial" as plan name
   - Should see "Trial End Date" (not start/end dates)

4. **Date Display:**
   - Trial user → Should only see `trialEndDate`
   - Should not see `subscriptionStartDate`/`subscriptionEndDate`
