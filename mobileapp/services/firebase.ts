import firebase from 'firebase/compat/app';
import 'firebase/compat/auth';
import 'firebase/compat/firestore';
import { Platform } from 'react-native';
import { 
  API_KEY, 
  AUTH_DOMAIN, 
  PROJECT_ID, 
  STORAGE_BUCKET, 
  MESSAGING_SENDER_ID, 
  APP_ID 
} from '@env';
import * as Notifications from 'expo-notifications';
import { logger } from '../utils/logger';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

// Debug environment variables
console.log('=== FIREBASE CONFIG DEBUG ===');
console.log('API_KEY:', API_KEY ? `${API_KEY.substring(0, 10)}...` : 'MISSING');
console.log('AUTH_DOMAIN:', AUTH_DOMAIN || 'MISSING');
console.log('PROJECT_ID:', PROJECT_ID || 'MISSING');
console.log('STORAGE_BUCKET:', STORAGE_BUCKET || 'MISSING');
console.log('MESSAGING_SENDER_ID:', MESSAGING_SENDER_ID || 'MISSING');
console.log('APP_ID:', APP_ID || 'MISSING');
console.log('================================');

// Firebase configuration
const firebaseConfig = {
  apiKey: API_KEY,
  authDomain: AUTH_DOMAIN,
  projectId: PROJECT_ID,
  storageBucket: STORAGE_BUCKET,
  messagingSenderId: MESSAGING_SENDER_ID,
  appId: APP_ID
};

console.log('Firebase config object:', firebaseConfig);

// Initialize Firebase
let firebaseApp: firebase.app.App;

// Check if environment variables are available
if (!API_KEY || !AUTH_DOMAIN || !PROJECT_ID || !STORAGE_BUCKET || !MESSAGING_SENDER_ID || !APP_ID) {
  const missingVars = [];
  if (!API_KEY) missingVars.push('API_KEY');
  if (!AUTH_DOMAIN) missingVars.push('AUTH_DOMAIN');
  if (!PROJECT_ID) missingVars.push('PROJECT_ID');
  if (!STORAGE_BUCKET) missingVars.push('STORAGE_BUCKET');
  if (!MESSAGING_SENDER_ID) missingVars.push('MESSAGING_SENDER_ID');
  if (!APP_ID) missingVars.push('APP_ID');
  
  console.error('Missing Firebase environment variables:', missingVars);
  throw new Error(`Firebase environment variables are missing: ${missingVars.join(', ')}. Please add them to EAS environment variables.`);
}

  try {
    console.log('Checking Firebase apps length:', firebase.apps.length);
    console.log('Firebase apps:', firebase.apps);
    
    if (!firebase.apps.length) {
      console.log('Initializing Firebase app...');
      firebaseApp = firebase.initializeApp(firebaseConfig);
      console.log('Firebase initialized successfully');
      
      // iOS-specific Firebase optimization
      if (Platform.OS === 'ios') {
        console.log('[iOS] Applying Firebase performance optimizations');
        // Configure Firebase for iOS stability
        firebase.firestore().settings({
          cacheSizeBytes: firebase.firestore.CACHE_SIZE_UNLIMITED,
          experimentalForceLongPolling: false, // Use WebSocket for better performance on iOS
        });
      }
    } else {
      firebaseApp = firebase.apps[0];
      console.log('Firebase already initialized');
    }
  } catch (error) {
    console.error('Firebase initialization error:', error);
    throw new Error(`Firebase initialization failed: ${error}`);
  }

export const auth = firebase.auth();
export const firestore = firebase.firestore();

export default firebase;

export async function registerForPushNotificationsAsync() {
  let token;
  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    if (finalStatus !== 'granted') {
      logger.log('Failed to get push token for push notification!');
      return;
    }
    
    // Platform-specific token generation for EAS builds
    if (Platform.OS === 'ios') {
      // For iOS EAS builds, use Expo push token
      token = (await Notifications.getExpoPushTokenAsync({
        projectId: '23b497a5-baac-44c7-82a4-487a59bfff5b' // Your project ID
      })).data;
    } else {
      // For Android EAS builds, use Expo push token
      token = (await Notifications.getExpoPushTokenAsync({
        projectId: '23b497a5-baac-44c7-82a4-487a59bfff5b' // Your project ID
      })).data;
    }
    
    logger.log('Expo push token:', token);
    logger.log('Platform:', Platform.OS);
    logger.log('Token type:', typeof token);
    
    // Save token to Firestore with error handling
    try {
      const user = auth.currentUser;
      if (user && token) {
        await firebase.firestore().collection('user_profiles').doc(user.uid).set({ 
          expoPushToken: token,
          platform: Platform.OS,
          lastTokenUpdate: new Date().toISOString()
        }, { merge: true });
        logger.log('Saved expoPushToken to Firestore with platform info');
      }
    } catch (error) {
      logger.log('Failed to save push token to Firestore:', error);
    }
  } catch (e) {
    logger.log('Error registering for push notifications:', e);
  }
  return token;
}

// Global notification listener for new_diet notifications
export function setupDietNotificationListener() {
  try {
    logger.log('Setting up GLOBAL diet notification listener for platform:', Platform.OS);
    
    const subscription = Notifications.addNotificationReceivedListener(notification => {
      const data = notification.request.content.data;
      
      logger.log('🌍 GLOBAL NOTIFICATION RECEIVED:', notification.request.content.title);
      logger.log('🌍 Notification data:', data);
      
      // Handle new_diet notifications globally
      if (data?.type === 'new_diet') {
        logger.log('🌍 New diet notification received globally for user:', data.userId);
        
        // Send to backend for logging
        if (!__DEV__ && data.userId) {
          try {
            const { logFrontendEvent } = require('./api');
            logFrontendEvent(data.userId, 'GLOBAL_NOTIFICATION_RECEIVED', {
              type: 'new_diet',
              notificationData: data,
              title: notification.request.content.title,
              body: notification.request.content.body,
              platform: Platform.OS,
              autoExtractPending: data?.auto_extract_pending
            });
          } catch (logError) {
            logger.log('Failed to log global notification event:', logError);
          }
        }
        
        // Store notification data for DashboardScreen to pick up
        if (data?.auto_extract_pending) {
          try {
            // Store in AsyncStorage so DashboardScreen can check for it
            const AsyncStorage = require('@react-native-async-storage/async-storage').default;
            AsyncStorage.setItem('pending_auto_extract', JSON.stringify({
              userId: data.userId,
              auto_extract_pending: true,
              timestamp: new Date().toISOString(),
              notificationData: data,
              source: 'foreground' // Mark as from foreground
            }));
            logger.log('🌍 Stored pending auto extract flag for DashboardScreen');
          } catch (storageError) {
            logger.log('Failed to store pending auto extract flag:', storageError);
          }
        }
      }
    });

    // Also add response listener for when user taps notification (CRITICAL for closed app)
    const responseSubscription = Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data;
      
      logger.log('🌍 Global notification response received:', response);
      logger.log('🌍 Response data:', data);
      
      // Handle new_diet notifications when user taps them (app was closed/backgrounded)
      if (data?.type === 'new_diet') {
        logger.log('🌍 New diet notification tapped globally for user:', data.userId);
        
        // Send to backend for logging
        if (!__DEV__ && data.userId) {
          try {
            const { logFrontendEvent } = require('./api');
            logFrontendEvent(data.userId, 'GLOBAL_NOTIFICATION_TAPPED', {
              type: 'new_diet',
              notificationData: data,
              title: response.notification.request.content.title,
              body: response.notification.request.content.body,
              platform: Platform.OS,
              autoExtractPending: data?.auto_extract_pending
            });
          } catch (logError) {
            logger.log('Failed to log global notification tap event:', logError);
          }
        }
        
        // Store notification data for DashboardScreen to pick up
        if (data?.auto_extract_pending) {
          try {
            // Store in AsyncStorage so DashboardScreen can check for it
            const AsyncStorage = require('@react-native-async-storage/async-storage').default;
            AsyncStorage.setItem('pending_auto_extract', JSON.stringify({
              userId: data.userId,
              auto_extract_pending: true,
              timestamp: new Date().toISOString(),
              notificationData: data,
              source: 'notification_tap' // Mark as from notification tap
            }));
            logger.log('🌍 Stored pending auto extract flag from notification tap');
          } catch (storageError) {
            logger.log('Failed to store pending auto extract flag from tap:', storageError);
          }
        }
      }
    });

    // Return combined subscription
    return {
      remove: () => {
        subscription.remove();
        responseSubscription.remove();
      }
    };
  } catch (error) {
    logger.log('Failed to setup global diet notification listener:', error);
    // Return a dummy subscription to prevent crashes
    return {
      remove: () => {}
    };
  }
} 