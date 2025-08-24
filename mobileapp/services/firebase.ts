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
    token = (await Notifications.getExpoPushTokenAsync()).data;
    logger.log('Expo push token:', token);
    
    // Save token to Firestore with error handling
    try {
      const user = auth.currentUser;
      if (user && token) {
        await firebase.firestore().collection('user_profiles').doc(user.uid).set({ 
          expoPushToken: token 
        }, { merge: true });
        logger.log('Saved expoPushToken to Firestore');
      }
    } catch (error) {
      logger.log('Failed to save push token to Firestore:', error);
    }
  } catch (e) {
    logger.log('Error registering for push notifications:', e);
  }
  return token;
}

// Add notification listener for diet notifications
export function setupDietNotificationListener() {
  try {
    const subscription = Notifications.addNotificationReceivedListener(notification => {
      logger.log('Notification received:', notification);
      
      // Handle diet-related notifications
      const data = notification.request.content.data;
      if (data?.type === 'new_diet') {
        logger.log('New diet notification received for user:', data.userId);
        // You can add custom handling here if needed
      } else if (data?.type === 'diet_reminder') {
        logger.log('Diet reminder notification received for dietician');
        // You can add custom handling here if needed
      }
    });

    return subscription;
  } catch (error) {
    logger.log('Failed to setup diet notification listener:', error);
    // Return a dummy subscription to prevent crashes
    return {
      remove: () => {}
    };
  }
} 