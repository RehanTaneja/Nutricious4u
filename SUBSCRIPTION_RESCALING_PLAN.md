# 📋 Comprehensive Plan: Rescaling Subscription & Trial Durations to Production Values

## 🎯 Objective
Rescale all testing durations back to production values without changing any functionality, logic, or app behavior. Only time values need to be adjusted.

---

## 📊 Current Testing State vs. Production Requirements

### **Trial Duration**
- **Current (Testing)**: 1 hour
- **Production**: 3 days
- **Change**: `timedelta(hours=1)` → `timedelta(days=3)`

### **Subscription Plan Durations**
- **Current (Testing)**: 
  - 1month: 1 hour
  - 2months: 2 hours
  - 3months: 3 hours
  - 6months: 6 hours
- **Production**:
  - 1month: 30 days
  - 2months: 60 days
  - 3months: 90 days
  - 6months: 180 days
- **Change**: `timedelta(hours=X)` → `timedelta(days=Y)` where Y = 30, 60, 90, 180

### **Reminder Notifications**
- **Current (Testing)**: 30 minutes, 15 minutes, 5 minutes before expiration
- **Production**: 1 week (7 days) and 1 day before expiration
- **Change**: Minute-based reminders → Day-based reminders

### **Backend Job Interval**
- **Current (Testing)**: Runs every 1 minute
- **Production**: Should run every 6 hours (21600 seconds)
- **Change**: `JOB_INTERVAL_SECONDS = 60` → `JOB_INTERVAL_SECONDS = 21600`

### **Payment Addition Timing**
- **Current (Testing)**: 5 minutes before plan ends
- **Production**: 1 day before plan ends
- **Change**: `timedelta(minutes=4-6)` → `timedelta(days=1)` check

---

## 🔍 Files Requiring Changes

### **Backend (`backend/server.py`)**

#### **1. Trial Activation (Line ~5103-5106)**
**Location**: `activate_free_trial()` function
- **Current**: `end_date = start_date + timedelta(hours=1)`
- **Change to**: `end_date = start_date + timedelta(days=3)`
- **Also update**: Success message from "1 hour" to "3 days" (line ~5133)

#### **2. Subscription Plan Durations - Multiple Locations**

**Location A: Plan Switch Function (Line ~3889-3895)**
- `activate_pending_plan_switch()` function
- Change all `timedelta(hours=X)` to `timedelta(days=Y)`

**Location B: Auto-Renewal Function (Line ~4010-4016)**
- `auto_renew_subscription()` function
- Change all `timedelta(hours=X)` to `timedelta(days=Y)`

**Location C: Subscription Selection (Line ~4427-4433)**
- `select_subscription()` function - initial plan selection
- Change all `timedelta(hours=X)` to `timedelta(days=Y)`

**Location D: Subscription Selection - Extend Current Plan (Line ~4470-4476)**
- `select_subscription()` function - extending existing plan
- Change all `timedelta(hours=X)` to `timedelta(days=Y)`

**Mapping**:
- `1month`: `hours=1` → `days=30`
- `2months`: `hours=2` → `days=60`
- `3months`: `hours=3` → `days=90`
- `6months`: `hours=6` → `days=180`

#### **3. Subscription Reminder Checks (Line ~3515-3554)**
**Location**: `check_subscription_reminders_job()` function - Active subscriptions

**Current Logic**:
- 30 minutes before: `timedelta(minutes=29) <= time_until_expiry <= timedelta(minutes=31)`
- 15 minutes before: `timedelta(minutes=14) <= time_until_expiry <= timedelta(minutes=16)`
- 5 minutes before: `timedelta(minutes=4) <= time_until_expiry <= timedelta(minutes=6)`

**Change to**:
- **1 week (7 days) before**: `timedelta(days=6.9) <= time_until_expiry <= timedelta(days=7.1)` or use hours: `timedelta(hours=165) <= time_until_expiry <= timedelta(hours=171)` (7 days ± 6 hours window)
- **1 day before**: `timedelta(hours=23) <= time_until_expiry <= timedelta(hours=25)` (1 day ± 1 hour window)

**Flag Usage** (keep existing flag structure):
- `oneWeek` flag: Use for 1 week reminder
- `oneDay` flag: Use for 1 day reminder
- `twoDays` flag: Can be removed or repurposed

**Payment Addition**:
- Currently at 5 minutes before
- Move to 1 day before (same check as 1 day reminder)

#### **4. Trial Reminder Checks (Line ~3598-3633)**
**Location**: `check_subscription_reminders_job()` function - Trial users

**Current Logic**:
- 30 minutes before: `timedelta(minutes=29) <= time_until_expiry <= timedelta(minutes=31)`
- 15 minutes before: `timedelta(minutes=14) <= time_until_expiry <= timedelta(minutes=16)`
- 5 minutes before: `timedelta(minutes=4) <= time_until_expiry <= timedelta(minutes=6)`

**Change to**:
- **1 week (7 days) before**: `timedelta(hours=165) <= time_until_expiry <= timedelta(hours=171)`
- **1 day before**: `timedelta(hours=23) <= time_until_expiry <= timedelta(hours=25)`

#### **5. Notification Message Functions**

**Location A: `send_payment_reminder_notification()` (Line ~3678-3744)**
- **Current**: Handles minutes (30, 15, 5) and days (1, 2, 7) for backward compatibility
- **Change**: 
  - Remove minute-based logic (lines ~3689-3701)
  - Update day-based messages to handle 1 day and 7 days specifically
  - Keep backward compatibility check but prioritize days

**Location B: `send_trial_reminder_notification()` (Line ~3746-3782)**
- **Current**: Only handles minutes (30, 15, 5)
- **Change**: 
  - Add day-based logic (1 day, 7 days)
  - Update messages to reflect days instead of minutes
  - Keep structure but change time units

#### **6. Payment Addition Function (Line ~3650)**
**Location**: `add_payment_on_plan_end()` function
- **Current comment**: "TESTING: 5 minutes before, normally 1 day before"
- **Change**: Update to trigger at 1 day before (already handled by reminder check logic)

#### **7. Backend Job Interval (Line ~5293)**
**Location**: `run_scheduled_jobs()` function
- **Current**: `JOB_INTERVAL_SECONDS = 60` (1 minute)
- **Change to**: `JOB_INTERVAL_SECONDS = 21600` (6 hours)
- **Note**: This is acceptable because:
  - 1 week reminder window is 6 hours wide (165-171 hours = 6 hour window)
  - 1 day reminder window is 2 hours wide (23-25 hours = 2 hour window)
  - Running every 6 hours will catch both windows reliably

---

### **Mobile App (`mobileapp/App.tsx`)**

#### **1. Subscription Reminder Scheduling (Line ~1244-1339)**
**Location**: `scheduleSubscriptionReminders()` function

**Current Logic**:
- Calculates reminders at: 30 minutes, 15 minutes, 5 minutes before end
- Uses `reminder.minutes` in messages

**Change to**:
- Calculate reminders at: 7 days (1 week) and 1 day before end
- Update calculation:
  ```typescript
  const reminder7days = new Date(endDateTime.getTime() - 7 * 24 * 60 * 60 * 1000);
  const reminder1day = new Date(endDateTime.getTime() - 1 * 24 * 60 * 60 * 1000);
  ```
- Update reminders array:
  ```typescript
  const reminders = [
    { time: reminder7days, days: 7 },
    { time: reminder1day, days: 1 }
  ];
  ```
- Update message generation to use `reminder.days` instead of `reminder.minutes`
- Update messages to reflect days (e.g., "ends in 7 days", "ends in 1 day")
- Update notification data: Change `minutesRemaining` to `daysRemaining` or keep both for compatibility

---

## ⚠️ Important Considerations & Limitations

### **1. Notification Scheduling Limits**

**Expo Notifications (`timeInterval` trigger)**:
- ✅ **No hard limit**: Expo's `timeInterval` with `seconds` parameter can handle very large values
- ✅ **Tested approach**: The codebase already uses this for diet notifications which can span weeks
- ✅ **Platform support**: Both iOS and Android support long-interval notifications via Expo
- ⚠️ **Best practice**: Schedule notifications when they're needed (at trial/plan activation) rather than relying on very long intervals

**Recommendation**: 
- The current approach of scheduling notifications at activation time is correct
- For 7-day and 1-day reminders, the `secondsUntilTrigger` will be:
  - 7 days = 604,800 seconds (well within limits)
  - 1 day = 86,400 seconds (well within limits)
- **No changes needed** to notification scheduling mechanism

### **2. Backend Job Frequency**

**Current**: Runs every 1 minute (for testing narrow windows)
**Production**: Should run every 6 hours

**Why 6 hours is acceptable**:
- 1 week reminder window: 6 hours wide (165-171 hours before expiry)
- 1 day reminder window: 2 hours wide (23-25 hours before expiry)
- Running every 6 hours ensures:
  - 1 week reminder will be caught (window is 6 hours wide)
  - 1 day reminder will be caught (window is 2 hours wide, job runs 4 times per day)
- **Alternative**: Could run every 4 hours for extra safety, but 6 hours is sufficient

### **3. Time Window Calculations**

**For Reminder Checks**:
- Use hour-based calculations for precision
- 1 week = 168 hours, use window: 165-171 hours (6 hour window)
- 1 day = 24 hours, use window: 23-25 hours (2 hour window)
- This accounts for job execution timing and ensures reminders are sent

**For Mobile Notifications**:
- Calculate exact times (7 days before, 1 day before)
- Schedule at exact times - no window needed (scheduled in advance)

### **4. Flag Management**

**Current Flag Structure**:
- `lastPaymentReminderSent`: `{oneWeek: bool, twoDays: bool, oneDay: bool}`
- Flags prevent duplicate notifications

**Changes Needed**:
- Keep `oneWeek` flag for 1 week reminder
- Keep `oneDay` flag for 1 day reminder
- `twoDays` flag: Can be removed or left unused (for future use)

### **5. Message Updates**

**Trial Reminders**:
- Current: "ends in X minutes"
- New: "ends in 7 days" or "ends in 1 day"

**Subscription Reminders**:
- Current: "ends in X minutes"
- New: "ends in 7 days" or "ends in 1 day"
- Keep payment amount messaging
- Keep auto-renewal messaging

### **6. Testing Considerations**

**Before Production Deployment**:
1. **Verify notification scheduling**: Test that notifications scheduled 7 days and 1 day in advance actually fire
2. **Verify backend reminders**: Test that backend job catches reminders within the time windows
3. **Verify payment addition**: Test that payment is added 1 day before plan ends
4. **Verify plan durations**: Test that plans actually last 30, 60, 90, 180 days
5. **Verify trial duration**: Test that trial lasts 3 days

**Recommended Test Approach**:
- Create test accounts with shortened durations (e.g., 1 hour trial, 2 hour plans)
- Verify all reminders fire correctly
- Then scale to production values

---

## 📝 Detailed Change List

### **Backend Changes (`backend/server.py`)**

| Line Range | Function | Change Description |
|------------|----------|-------------------|
| ~5106 | `activate_free_trial()` | `timedelta(hours=1)` → `timedelta(days=3)` |
| ~5133 | `activate_free_trial()` | Message: "1 hour" → "3 days" |
| ~3889-3895 | `activate_pending_plan_switch()` | All `timedelta(hours=X)` → `timedelta(days=Y)` |
| ~4010-4016 | `auto_renew_subscription()` | All `timedelta(hours=X)` → `timedelta(days=Y)` |
| ~4427-4433 | `select_subscription()` | All `timedelta(hours=X)` → `timedelta(days=Y)` |
| ~4470-4476 | `select_subscription()` | All `timedelta(hours=X)` → `timedelta(days=Y)` |
| ~3517-3526 | `check_subscription_reminders_job()` | 30 min check → 1 week check (165-171 hours) |
| ~3528-3538 | `check_subscription_reminders_job()` | 15 min check → Remove (not needed) |
| ~3541-3554 | `check_subscription_reminders_job()` | 5 min check → 1 day check (23-25 hours) + payment |
| ~3600-3609 | `check_subscription_reminders_job()` | Trial 30 min → 1 week check (165-171 hours) |
| ~3611-3621 | `check_subscription_reminders_job()` | Trial 15 min → Remove (not needed) |
| ~3623-3633 | `check_subscription_reminders_job()` | Trial 5 min → 1 day check (23-25 hours) |
| ~3689-3701 | `send_payment_reminder_notification()` | Remove minute-based logic |
| ~3704-3712 | `send_payment_reminder_notification()` | Update day messages for 1 and 7 days |
| ~3754-3765 | `send_trial_reminder_notification()` | Add day-based logic (1 day, 7 days) |
| ~5293 | `run_scheduled_jobs()` | `JOB_INTERVAL_SECONDS = 60` → `21600` |

### **Mobile App Changes (`mobileapp/App.tsx`)**

| Line Range | Function | Change Description |
|------------|----------|-------------------|
| ~1256-1265 | `scheduleSubscriptionReminders()` | Change reminder times: 30/15/5 min → 7 days/1 day |
| ~1278-1289 | `scheduleSubscriptionReminders()` | Update messages to use days instead of minutes |
| ~1302 | `scheduleSubscriptionReminders()` | Update notification data: `minutesRemaining` → `daysRemaining` |

---

## ✅ Verification Checklist

After implementing changes, verify:

- [ ] Trial activates for 3 days (not 1 hour)
- [ ] 1-month plan lasts 30 days (not 1 hour)
- [ ] 2-month plan lasts 60 days (not 2 hours)
- [ ] 3-month plan lasts 90 days (not 3 hours)
- [ ] 6-month plan lasts 180 days (not 6 hours)
- [ ] Reminder notification scheduled 7 days before expiration
- [ ] Reminder notification scheduled 1 day before expiration
- [ ] Backend sends reminder 1 week before expiration
- [ ] Backend sends reminder 1 day before expiration
- [ ] Payment added to totalAmountPaid 1 day before plan ends
- [ ] Backend job runs every 6 hours (not every minute)
- [ ] All notification messages use "days" instead of "minutes"
- [ ] No duplicate reminders sent
- [ ] Trial reminders work correctly
- [ ] Subscription reminders work correctly

---

## 🚀 Implementation Order

1. **Backend Duration Changes** (Trial + Plans)
   - Update all `timedelta(hours=X)` to `timedelta(days=Y)`
   - Update success messages

2. **Backend Reminder Logic**
   - Update time windows for reminder checks
   - Update notification message functions

3. **Backend Job Interval**
   - Change from 1 minute to 6 hours

4. **Mobile App Reminder Scheduling**
   - Update reminder calculation times
   - Update reminder messages

5. **Testing**
   - Test with actual durations
   - Verify all reminders fire correctly
   - Verify payment addition timing

---

## 📌 Notes

- **No functional changes**: Only time values are being adjusted
- **Notification system**: Already proven to work with long intervals (diet notifications)
- **Backend job**: 6-hour interval is sufficient for the reminder windows
- **Flag system**: Existing flag structure works, just update time checks
- **Message compatibility**: Update messages but keep same structure and flow

---

## ⚡ Quick Reference: Time Conversions

| Duration | Hours | Days | Seconds (for notifications) |
|----------|-------|------|----------------------------|
| Trial | - | 3 | 259,200 |
| 1 Month | 720 | 30 | 2,592,000 |
| 2 Months | 1,440 | 60 | 5,184,000 |
| 3 Months | 2,160 | 90 | 7,776,000 |
| 6 Months | 4,320 | 180 | 15,552,000 |
| 1 Week Reminder | 168 | 7 | 604,800 |
| 1 Day Reminder | 24 | 1 | 86,400 |

---

**End of Plan**
