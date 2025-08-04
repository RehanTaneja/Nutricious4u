# Production Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Configuration
- [ ] Update `mobileapp/.env` with your production backend URL:
  ```
  PRODUCTION_BACKEND_URL=your-actual-production-backend-url.com
  ```
- [ ] Ensure all Firebase configuration is correct
- [ ] Verify all API keys are valid for production

### 2. Backend Deployment
- [ ] Deploy your backend server to a production environment
- [ ] Update the `PRODUCTION_BACKEND_URL` in `.env` to point to your deployed backend
- [ ] Ensure CORS is properly configured for your production domain
- [ ] Test all API endpoints from the production environment

### 3. EAS Build Configuration
- [ ] Configure EAS CLI: `eas login`
- [ ] Set up your project: `eas build:configure`
- [ ] For iOS App Store submission, update `eas.json`:
  ```json
  {
    "submit": {
      "production": {
        "ios": {
          "appleId": "your-actual-apple-id@example.com",
          "ascAppId": "your-actual-app-store-connect-app-id",
          "appleTeamId": "your-actual-apple-team-id"
        }
      }
    }
  }
  ```
- [ ] For Android Play Store submission:
  ```json
  {
    "submit": {
      "production": {
        "android": {
          "serviceAccountKeyPath": "./path-to-your-actual-service-account.json",
          "track": "production"
        }
      }
    }
  }
  ```

### 4. Build Commands
```bash
# Development build
eas build --profile development --platform ios
eas build --profile development --platform android

# Preview build (for testing)
eas build --profile preview --platform all

# Production build
eas build --profile production --platform all
```

### 5. Submission Commands
```bash
# Submit to App Store (iOS)
eas submit --profile production --platform ios

# Submit to Play Store (Android)
eas submit --profile production --platform android
```

## Important Notes

1. **Backend URL**: Make sure your production backend is deployed and accessible before building the app.

2. **Environment Variables**: The app uses environment variables for configuration. Ensure all required variables are set in your `.env` file.

3. **Firebase Configuration**: Verify that your Firebase project is properly configured for production.

4. **API Keys**: Ensure all API keys (Firebase, Gemini, etc.) are valid for production use.

5. **Testing**: Test the app thoroughly in preview builds before submitting to app stores.

## Troubleshooting

### Common Issues:
1. **Backend Connection Errors**: Ensure your production backend is running and accessible
2. **Build Failures**: Check that all dependencies are properly configured
3. **App Store Rejection**: Ensure all app store guidelines are followed

### Support:
- Check EAS documentation: https://docs.expo.dev/eas/
- Review Expo build logs for detailed error information
- Test with preview builds before production submission 