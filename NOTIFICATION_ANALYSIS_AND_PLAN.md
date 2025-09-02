# Notification Analysis and Fix Plan

## 🚨 **CURRENT ISSUES IDENTIFIED**

### **1. "User User has 1 day remaining" Issue**
- **Problem**: Users receiving "1 day left" notifications instead of dieticians
- **Root Cause**: Notification targeting logic may be broken or there's a duplicate notification source
- **Impact**: Users getting notifications meant for dieticians

### **2. Notification Icon Not Visible**
- **Problem**: App logo not appearing in notifications
- **Root Cause**: Icon configuration or optimization issues
- **Impact**: Poor user experience, unprofessional appearance

### **3. Complex Notification Scheduler**
- **Problem**: Current scheduler is too complicated and may cause issues
- **Root Cause**: Multiple scheduling systems (backend + frontend) with complex logic
- **Impact**: Potential conflicts and unreliable behavior

## 📋 **COMPREHENSIVE NOTIFICATION LIST**

### **NOTIFICATIONS TO USERS:**
1. **New Diet Uploaded** - "New Diet Has Arrived!"
2. **Regular Diet Reminders** - "Take breakfast at 9:30 AM" (from diet PDF)
3. **Custom Reminders** - User-created reminders
4. **Subscription Expiring Soon** - "Your subscription will expire in 1 week"
5. **Subscription Auto-Renewed** - "Your subscription has been automatically renewed"
6. **Subscription Expired** - "Your subscription has expired"
7. **New Messages** - "New message from dietician"

### **NOTIFICATIONS TO DIETICIANS:**
1. **User Has 1 Day Left** - "[User Name] has 1 day left in their diet"
2. **Diet Upload Success** - "Successfully uploaded new diet for user [ID]"
3. **User Subscription Renewed** - "User [Name] has renewed their subscription"
4. **User Subscription Expired** - "User [Name] subscription has expired"
5. **New Messages from Users** - "New message from [User Name]"

## 🔧 **PROPOSED SIMPLE NOTIFICATION SYSTEM**

### **Phase 1: Comment Out Complex Scheduler**
- Comment out the entire `backend/services/notification_scheduler.py`
- Comment out complex scheduling logic in `server.py`
- Keep only essential notification sending functions

### **Phase 2: Create Simple Local-Only System**
- All notifications scheduled locally on device
- Use Expo's built-in notification scheduling
- Simple, reliable, guaranteed to work in EAS builds

### **Phase 3: Fix Icon Issues**
- Optimize notification icons properly
- Ensure correct configuration in `app.json`
- Test icon visibility in both Expo Go and EAS builds

### **Phase 4: Fix "1 Day Left" Targeting**
- Ensure only dieticians receive "1 day left" notifications
- Fix name formatting to show proper names
- Remove any duplicate notification sources

## 🧪 **TESTING STRATEGY**

### **Test 1: Icon Visibility**
- Test notification icons in Expo Go
- Test notification icons in EAS build
- Verify icons appear correctly

### **Test 2: Notification Targeting**
- Verify users don't receive "1 day left" notifications
- Verify dieticians receive "1 day left" notifications with proper names
- Test all user notifications work correctly

### **Test 3: Local Scheduling**
- Test custom reminders work correctly
- Test diet reminders work correctly
- Verify scheduling works in both environments

### **Test 4: Edge Cases**
- Test notifications at different times
- Test notifications on different days
- Test notifications with different timezones
- Test app restart scenarios

## ⚠️ **WAITING FOR CONFIRMATION**

Before proceeding with the implementation, I need your confirmation on:

1. **Should I comment out the complex backend notification scheduler?**
2. **Should I create a simple local-only notification system?**
3. **Should I focus on fixing the icon and targeting issues first?**
4. **Do you want me to proceed with the comprehensive testing approach?**

## 🎯 **NEXT STEPS**

Once you confirm, I will:

1. **Comment out complex scheduler** and create simple system
2. **Fix notification icon** configuration and optimization
3. **Fix "1 day left" targeting** to ensure only dieticians receive them
4. **Implement comprehensive testing** for all edge cases
5. **Verify everything works** in both Expo Go and EAS builds

Please confirm if you want me to proceed with this plan.
