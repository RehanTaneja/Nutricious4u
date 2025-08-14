# Backend Notification Scheduling Implementation

## 🎯 **Overview**

This document outlines the implementation of a **server-side notification scheduling system** that actually sends notifications based on the selected days. The previous system only handled local scheduling on the mobile device, but now the backend properly manages day-based notification scheduling and delivery.

## 🔧 **Key Changes Made**

### **1. Backend Notification Scheduler Service**

**File: `backend/services/notification_scheduler.py`**
- **New service** that handles day-based notification scheduling
- **Stores scheduled notifications** in Firestore for tracking
- **Sends notifications** at the correct times on selected days
- **Automatic rescheduling** for next week after sending
- **Cleanup** of old notifications

**Key Features:**
- ✅ Day-based scheduling (Monday-Sunday)
- ✅ Time-based notification sending
- ✅ Automatic rescheduling for recurring notifications
- ✅ Status tracking (scheduled, sent, failed)
- ✅ Cleanup of old notifications

### **2. Updated Diet Notification Service**

**File: `backend/services/diet_notification_service.py`**
- **Added `selectedDays` field** to notification objects
- **Default to all days** for extracted notifications
- **Added `isActive` field** for notification management

### **3. New Backend API Endpoints**

**File: `backend/server.py`**

#### **POST `/users/{user_id}/diet/notifications/schedule`**
- Schedules all active notifications for a user based on their day preferences
- Called automatically after extraction or manual scheduling

#### **PUT `/users/{user_id}/diet/notifications/{notification_id}`**
- Updates a specific notification including day preferences
- Automatically reschedules notifications after update

#### **DELETE `/users/{user_id}/diet/notifications/{notification_id}`**
- Deletes a specific notification
- Automatically reschedules remaining notifications

### **4. Enhanced Diet Upload Process**

**File: `backend/server.py`**
- **Automatic scheduling** after notification extraction
- **Backend handles all scheduling** instead of frontend

### **5. Periodic Notification Scheduler**

**File: `backend/server.py`**
- **Runs every minute** to check for due notifications
- **Sends notifications** that are scheduled for the current time
- **Automatic rescheduling** for next week
- **Cleanup** of old notifications (hourly)

### **6. Updated Frontend Integration**

**File: `mobileapp/services/api.ts`**
- **New API functions** for backend notification management
- `updateDietNotification()` - Update notifications with day preferences
- `scheduleDietNotifications()` - Manual scheduling endpoint

**File: `mobileapp/screens.tsx`**
- **Removed local scheduling** logic
- **Uses backend scheduling** for all operations
- **Sends day preferences** to backend when updating notifications
- **Simplified notification management**

## 🏗️ **Architecture**

### **Before (Local Scheduling Only)**
```
Frontend (Mobile App):
├── ✅ Day selection UI
├── ✅ Local notification scheduling
├── ❌ No server-side reliability
├── ❌ Notifications lost if app closed

Backend (Server):
├── ✅ Extract notifications
├── ✅ Store in Firestore
├── ❌ NO day-based scheduling
├── ❌ NO notification sending
```

### **After (Server-Side Scheduling)**
```
Frontend (Mobile App):
├── ✅ Day selection UI
├── ✅ Send preferences to backend
├── ✅ Display notifications from backend
├── ❌ No local scheduling

Backend (Server):
├── ✅ Extract notifications
├── ✅ Store with day preferences
├── ✅ Schedule based on selected days
├── ✅ Send notifications at correct times
├── ✅ Automatic rescheduling
├── ✅ Status tracking and cleanup
```

## 📊 **Database Schema**

### **User Notifications Collection**
```json
{
  "user_id": "string",
  "diet_notifications": [
    {
      "id": "string",
      "message": "string",
      "time": "HH:MM",
      "hour": number,
      "minute": number,
      "source": "diet_pdf",
      "original_text": "string",
      "selectedDays": [0, 1, 2, 3, 4, 5, 6],
      "isActive": true
    }
  ],
  "extracted_at": "ISO timestamp",
  "diet_pdf_url": "string"
}
```

### **Scheduled Notifications Collection**
```json
{
  "user_id": "string",
  "notification_id": "string",
  "message": "string",
  "time": "HH:MM",
  "day": number,
  "scheduled_for": "ISO timestamp",
  "status": "scheduled|sent|failed",
  "created_at": "ISO timestamp",
  "sent_at": "ISO timestamp (optional)",
  "failed_at": "ISO timestamp (optional)"
}
```

## 🔄 **Workflow**

### **1. Notification Extraction**
1. User uploads diet PDF
2. Backend extracts notifications
3. **Automatic scheduling** on backend
4. Notifications stored with day preferences

### **2. Day-Based Scheduling**
1. Backend calculates next occurrence for each selected day
2. Stores scheduled notification in Firestore
3. Sets status to "scheduled"

### **3. Notification Sending**
1. **Every minute**, scheduler checks for due notifications
2. Sends notifications that are scheduled for current time
3. Updates status to "sent"
4. **Automatically schedules** next occurrence for next week

### **4. User Updates**
1. User modifies notification (time, message, days)
2. Frontend sends update to backend
3. Backend **reschedules all notifications** for user
4. Old scheduled notifications are replaced

## 🚀 **Benefits**

### **✅ Reliability**
- **Server-side scheduling** ensures notifications are sent even if app is closed
- **Automatic rescheduling** for recurring notifications
- **Status tracking** for monitoring and debugging

### **✅ Scalability**
- **Centralized scheduling** can handle multiple users
- **Efficient database queries** for due notifications
- **Cleanup processes** prevent database bloat

### **✅ User Experience**
- **Accurate day-based delivery** based on user preferences
- **Consistent notification timing** across devices
- **No dependency on app state**

### **✅ Maintainability**
- **Clear separation** between frontend and backend
- **Comprehensive logging** for debugging
- **Testable components** with clear interfaces

## 🧪 **Testing**

### **Test Script: `test_backend_notification_scheduling.py`**
- Tests notification extraction and scheduling
- Tests day preference updates
- Tests notification deletion
- Tests manual scheduling

### **Manual Testing**
1. Upload diet PDF with timed activities
2. Verify notifications are extracted and scheduled
3. Update notification day preferences
4. Verify notifications are sent on correct days
5. Test notification deletion and rescheduling

## 📋 **Dependencies**

### **New Backend Dependencies**
```
pytz==2023.3  # Timezone handling for scheduling
```

### **Updated Files**
- `backend/services/notification_scheduler.py` (NEW)
- `backend/services/diet_notification_service.py`
- `backend/server.py`
- `backend/requirements.txt`
- `mobileapp/services/api.ts`
- `mobileapp/screens.tsx`

## 🎉 **Result**

The notification system now **actually sends notifications based on the selected days** with:

- ✅ **Server-side reliability** - notifications sent even if app is closed
- ✅ **Day-based scheduling** - notifications only sent on selected days
- ✅ **Automatic rescheduling** - notifications continue weekly
- ✅ **User preference support** - full day selection functionality
- ✅ **Production-ready** - scalable and maintainable architecture

The system is now **production-ready** and provides a robust, reliable notification experience for users.
