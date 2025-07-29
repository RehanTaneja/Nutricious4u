# Diet Notifications Setup Guide

This guide explains how to set up and test the push notification system for the diet feature.

## Features Implemented

### 1. User Notifications
- **New Diet Notification**: When a dietician uploads a new diet for a user, the user receives a push notification saying "New Diet Has Arrived!"

### 2. Dietician Notifications  
- **Diet Reminder**: When any user has 1 day remaining in their 7-day countdown, the dietician receives a notification with the user's name

## Backend Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Firebase Service Account
Ensure you have the Firebase service account JSON file at:
```
backend/services/firebase_service_account.json
```

### 3. Environment Variables
Make sure your Firebase configuration is properly set up in the service account file.

## Mobile App Setup

### 1. Expo Push Tokens
The app automatically registers for push notifications and saves the Expo push token to Firestore in the `expoPushToken` field.

### 2. Notification Permissions
The app requests notification permissions on startup. Users must grant permission to receive notifications.

## Testing the System

### 1. Test Diet Upload and User Notification
1. Start the backend server: `python server.py`
2. Use the dietician app to upload a diet for a user
3. The user should receive a notification: "New Diet Has Arrived!"

### 2. Test Diet Reminder for Dietician
1. Manually trigger the reminder check:
```bash
cd backend
python test_notifications.py
```

2. Or call the API endpoint directly:
```bash
curl -X POST http://localhost:8000/api/diet/check-reminders
```

### 3. Test Push Notifications Directly
Edit `backend/test_notifications.py` and replace the token with a real Expo push token, then run:
```bash
python test_notifications.py
```

## Setting Up Scheduled Notifications

### Option 1: Cron Job (Recommended)
Add this to your crontab to run daily at 9 AM:
```bash
0 9 * * * cd /path/to/your/project/backend && python schedule_notifications.py >> /var/log/diet_notifications.log 2>&1
```

### Option 2: Systemd Timer (Linux)
Create a systemd service and timer for more robust scheduling.

### Option 3: Cloud Scheduler (Google Cloud)
If deploying on Google Cloud, use Cloud Scheduler to call the API endpoint:
```
POST https://your-backend-url.com/api/diet/check-reminders
```

## API Endpoints

### Upload Diet (Dietician Only)
```
POST /api/users/{user_id}/diet/upload
Content-Type: multipart/form-data
Body: file (PDF), dietician_id
```

### Check Diet Reminders
```
POST /api/diet/check-reminders
```

### Get User Diet
```
GET /api/users/{user_id}/diet
```

### List Non-Dietician Users
```
GET /api/users/non-dietician
```

## Troubleshooting

### 1. Notifications Not Working
- Check that users have granted notification permissions
- Verify Expo push tokens are saved in Firestore
- Check the backend logs for notification errors
- Test with the notification test script

### 2. Scheduled Jobs Not Running
- Check cron job syntax and paths
- Verify the script has execute permissions
- Check log files for errors
- Test the script manually first

### 3. Firebase Issues
- Verify service account JSON file exists and is valid
- Check Firebase project configuration
- Ensure proper permissions for Firestore and Storage

## Development Notes

### Notification Flow
1. **User gets new diet**: 
   - Dietician uploads PDF → Backend saves to Firebase Storage → Updates Firestore → Sends notification to user

2. **Dietician gets reminder**:
   - Scheduled job checks all users → Calculates days remaining → Sends notification to dietician if any user has 1 day left

### Token Management
- Expo push tokens are automatically saved to Firestore when users open the app
- Tokens are stored in the `expoPushToken` field of user profiles
- The system falls back to `notificationToken` field for compatibility

### Real-time Updates
- Users see diet updates in real-time via Firestore listeners
- Notifications are sent immediately when diets are uploaded
- Countdown timers update automatically 