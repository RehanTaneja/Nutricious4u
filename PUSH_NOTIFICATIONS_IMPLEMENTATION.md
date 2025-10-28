# Push Notifications System Implementation

## Overview

This document describes the new push notification system built from scratch for the Nutricious4u app. The system handles real-time notifications for:

1. **Messages** - Bidirectional notifications between users and dieticians
2. **Appointments** - Notifications to dietician when users schedule/cancel appointments  
3. **Diet Countdown** - Notifications to dietician when users have 1 day left in their diet

**Important**: Local scheduled diet notifications are completely separate and unchanged.

## Architecture

### Backend Components

**New API Endpoint**: `/push-notifications/send`
- Handles all push notification types
- Non-blocking - failures don't break app functionality
- Uses existing `SimpleNotificationService` for sending

**Scheduled Job**: `check_diet_countdown_job()`
- Runs every 6 hours automatically
- Checks all users for 1-day-left status
- Sends notifications to dietician for each user needing new diet

### Frontend Components

**API Helper**: `sendPushNotification()` in `services/api.ts`
- Wrapper for backend push notification endpoint
- Handles errors gracefully (non-blocking)
- Returns success/failure status

**Integration Points**:
- Message sending (DieticianMessageScreen)
- Appointment scheduling (ScheduleAppointmentScreen)
- Appointment cancellation (ScheduleAppointmentScreen)

## How It Works

### Message Notifications

**User → Dietician:**
```
1. User sends message via app
2. Message saved to Firestore
3. Frontend calls sendPushNotification({
     type: 'message',
     recipientId: 'dietician',
     senderName: 'John Doe',
     message: 'Hello...',
     isFromDietician: false
   })
4. Backend retrieves dietician push token
5. Backend sends notification via Expo Push Service
6. Dietician receives notification even if app is closed
```

**Dietician → User:**
```
1. Dietician sends message via app
2. Message saved to Firestore
3. Frontend calls sendPushNotification({
     type: 'message',
     recipientId: '<userId>',
     senderName: 'Dietician',
     message: 'Hello...',
     isFromDietician: true
   })
4. Backend retrieves user push token
5. Backend sends notification via Expo Push Service
6. User receives notification even if app is closed
```

### Appointment Notifications

**Appointment Scheduled:**
```
1. User schedules appointment via app
2. Appointment saved to Firestore
3. Frontend calls sendPushNotification({
     type: 'appointment_scheduled',
     userName: 'John Doe',
     date: '1/15/2025',
     timeSlot: '10:00'
   })
4. Backend sends notification to dietician
5. Dietician sees: "New Appointment Scheduled - John Doe scheduled..."
```

**Appointment Cancelled:**
```
1. User cancels appointment via app
2. Appointment deleted from Firestore
3. Frontend calls sendPushNotification({
     type: 'appointment_cancelled',
     userName: 'John Doe',
     date: '1/15/2025',
     timeSlot: '10:00'
   })
4. Backend sends notification to dietician
5. Dietician sees: "Appointment Cancelled - John Doe cancelled..."
```

### Diet Countdown Notifications

**Automatic Daily Check:**
```
1. Scheduled job runs every 6 hours
2. Job queries all user profiles
3. For each user:
   - Calculate days left: 168 hours - (now - lastDietUpload)
   - If 24-47 hours remaining (1 day left):
     - Send notification to dietician
4. Dietician sees: "Diet Expiring Soon ⏰ - John Doe has 1 day left..."
```

## Technical Details

### Backend Endpoint

```python
POST /push-notifications/send

Request body:
{
  "type": "message" | "appointment_scheduled" | "appointment_cancelled",
  "recipientId": "<userId or 'dietician'>",
  "senderName": "John Doe",
  "message": "Hello...",
  "isFromDietician": false,
  "userName": "John Doe",
  "date": "1/15/2025",
  "timeSlot": "10:00"
}

Response:
{
  "success": true | false
}
```

### Push Token Management

**Token Registration:**
- Handled by existing `registerForPushNotificationsAsync()` in `firebase.ts`
- Tokens stored in Firestore `user_profiles` collection
- Field: `expoPushToken`

**Token Retrieval:**
- Users: Direct lookup by userId in `user_profiles`
- Dietician: Query where `isDietician == true`

### Error Handling

**Frontend:**
- All push notification calls wrapped in try-catch
- Errors logged but don't block main functionality
- Non-blocking design ensures app continues working

**Backend:**
- Validates notification type and required fields
- Returns HTTP 400 for invalid requests
- Returns HTTP 500 for server errors
- Comprehensive logging for debugging

## Testing

### Test Scripts Included

1. **test_push_notifications_messages.py**
   - Tests user → dietician messages
   - Tests dietician → user messages

2. **test_push_notifications_appointments.py**
   - Tests appointment scheduling notifications
   - Tests appointment cancellation notifications

3. **test_push_notifications_diet_countdown.py**
   - Creates test user with 1 day left
   - Verifies dietician receives notification

4. **test_local_diet_notifications_verification.py**
   - Verifies local diet notifications unchanged
   - Checks critical files and functions

### Manual Testing Checklist

**Message Notifications:**
- [ ] User sends message with app open → Dietician receives notification
- [ ] User sends message with app closed → Dietician receives notification
- [ ] Dietician sends message with app open → User receives notification
- [ ] Dietician sends message with app closed → User receives notification
- [ ] Notification shows correct sender name
- [ ] Notification shows message preview

**Appointment Notifications:**
- [ ] User schedules appointment → Dietician receives notification
- [ ] User cancels appointment → Dietician receives notification
- [ ] Notification shows correct user name, date, and time
- [ ] Notifications work with app closed

**Diet Countdown:**
- [ ] User with 1 day left → Dietician receives notification
- [ ] Multiple users with 1 day left → Dietician receives multiple notifications
- [ ] Notification shows correct user name
- [ ] Scheduled job runs automatically

**Local Diet Notifications (Should Still Work):**
- [ ] Upload diet PDF with notifications
- [ ] Extract notifications from PDF
- [ ] Select notification days
- [ ] Notifications fire at correct times
- [ ] User receives diet reminder notifications

## What Was NOT Changed

The following systems remain completely untouched:

- **Local Diet Notifications**: `unifiedNotificationService.ts`, `notificationService.ts`
- **Diet Extraction**: `diet_notification_service.py`
- **Token Registration**: `firebase.ts` registration logic
- **All Other App Features**: Food logging, workout tracking, recipes, etc.

## Troubleshooting

### Notifications Not Received

**Check 1: Push Token Registered**
```
- Open app
- Check Firestore user_profiles/<userId>
- Verify expoPushToken field exists
- Token should start with "ExponentPushToken["
```

**Check 2: Backend Logs**
```
- Check server logs for "[PUSH NOTIFICATION]" entries
- Look for success/failure messages
- Verify recipient ID is correct
```

**Check 3: Device Settings**
```
- Ensure notifications enabled for app
- Check Do Not Disturb is off
- Try force-closing and reopening app
```

### Scheduled Job Not Running

**Check 1: Server Startup Logs**
```
- Look for "Diet countdown scheduler started"
- Verify server started successfully
```

**Check 2: Job Execution**
```
- Check logs for "[DIET COUNTDOWN]" entries
- Job runs every 6 hours
- Can restart server to trigger immediately
```

## Deployment

### Backend Deployment

1. Push changes to repository
2. Backend auto-deploys on Railway
3. Verify server starts successfully
4. Check logs for scheduler initialization

### Frontend Deployment

1. Build new EAS build: `eas build --platform android/ios`
2. Test push notifications thoroughly
3. Submit to app stores
4. Users must update to receive/send push notifications

## Maintenance

### Monitoring

- Monitor backend logs for "[PUSH NOTIFICATION]" and "[DIET COUNTDOWN]"
- Check for failed notification sends
- Verify scheduled job runs successfully

### Common Issues

**Issue**: Token not found
**Solution**: User needs to login again to register token

**Issue**: Notification not delivered
**Solution**: Check Expo Push Service status, verify token validity

**Issue**: Scheduled job not running
**Solution**: Check server uptime, verify job initialization

## Future Enhancements

Potential improvements:
- Add notification preferences (enable/disable by type)
- Add notification history/archive
- Add retry logic for failed notifications
- Add notification batching for multiple users
- Add analytics/tracking for notification delivery

## Support

For issues or questions:
1. Check backend logs for errors
2. Verify push tokens are registered
3. Test with included test scripts
4. Check device notification settings
5. Review troubleshooting section above

