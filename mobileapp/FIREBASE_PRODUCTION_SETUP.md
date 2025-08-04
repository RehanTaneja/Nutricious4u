# Firebase Production Setup Guide

## 1. Firebase Console Configuration

### Authentication Setup:
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project: `nutricious4u-63158`
3. Go to **Authentication** → **Sign-in method**
4. Enable these providers:
   - ✅ Email/Password
   - ✅ Google (for Google Sign-in)
   - ✅ Phone (for phone authentication)

### Google Sign-in Setup:
1. In **Authentication** → **Sign-in method** → **Google**
2. Click **Enable**
3. Add your support email
4. Save

### Phone Authentication Setup:
1. In **Authentication** → **Sign-in method** → **Phone**
2. Click **Enable**
3. Add your test phone numbers if needed
4. Save

## 2. Firestore Security Rules

Update your Firestore rules in `firestore.rules`:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own profile
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Users can read/write their own food logs
    match /food_logs/{logId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.userId;
    }
    
    // Users can read/write their own workout logs
    match /workout_logs/{logId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.userId;
    }
    
    // Users can read/write their own routines
    match /routines/{routineId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.userId;
    }
    
    // Notifications - users can read their own
    match /notifications/{notificationId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.userId;
    }
    
    // User profiles for push tokens
    match /user_profiles/{userId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == userId;
    }
  }
}
```

## 3. Storage Rules

Update your storage rules in `storage.rules`:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Users can upload their own diet PDFs
    match /diet_pdfs/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && 
        request.auth.uid == userId;
    }
    
    // Users can upload their own profile images
    match /profile_images/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && 
        request.auth.uid == userId;
    }
  }
}
```

## 4. Push Notifications Setup

### For Android:
1. Go to **Project Settings** → **Cloud Messaging**
2. Add your Android app if not already added
3. Download the updated `google-services.json`
4. Replace the existing file in your mobile app

### For iOS:
1. Go to **Project Settings** → **Cloud Messaging**
2. Add your iOS app if not already added
3. Download the updated `GoogleService-Info.plist`
4. Replace the existing file in your mobile app

## 5. Environment Variables Check

Ensure these are set in your mobile app `.env`:
```
API_KEY=AIzaSyAcuwyzmZlNdS47-4xjO_M74AkCwVgKPN0
AUTH_DOMAIN=nutricious4u-63158.firebaseapp.com
PROJECT_ID=nutricious4u-63158
STORAGE_BUCKET=nutricious4u-63158.firebasestorage.app
MESSAGING_SENDER_ID=383526478160
APP_ID=1:383526478160:web:511c06b0bd494318068c55
PRODUCTION_BACKEND_URL=your-deployed-backend-url
```

## 6. Test Authentication

After setup, test these features:
- ✅ Email/Password signup/login
- ✅ Google Sign-in
- ✅ Phone authentication
- ✅ Push notifications
- ✅ Firestore data read/write
- ✅ Storage upload/download 