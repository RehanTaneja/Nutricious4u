# Notification Fixes Build Instructions

## 🚀 Build Commands

### For Android:
```bash
eas build --platform android --profile preview
```

### For iOS:
```bash
eas build --platform ios --profile preview
```

## 🔍 Verification Steps

1. **Test Notification Icons**:
   - Check if notification icons appear in notifications
   - Verify icons are properly sized and visible

2. **Test "1 Day Left" Notifications**:
   - Create a user with 1 day left in diet
   - Verify dietician receives notification with proper name format
   - Verify user does NOT receive "1 day left" notification

3. **Test Regular Diet Notifications**:
   - Upload a diet PDF with timed activities
   - Verify user receives regular diet notifications at correct times
   - Verify notifications work in both Expo Go and EAS builds

4. **Test Custom Reminders**:
   - Create custom reminders
   - Verify they work correctly in both environments

## ⚠️ Important Notes

- **Timezone**: All notifications now use UTC for consistent behavior
- **Targeting**: "1 day left" notifications only go to dieticians
- **Icons**: Notification icons are optimized for better visibility
- **Scheduling**: Regular diet notifications go to users as expected

## 🐛 Troubleshooting

If issues persist:
1. Check backend logs for notification sending errors
2. Verify dietician has proper expoPushToken in database
3. Check user notification tokens are valid
4. Verify notification permissions are granted
