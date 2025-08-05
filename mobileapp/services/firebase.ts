import firebase from 'firebase/compat/app';
import 'firebase/compat/auth';
import 'firebase/compat/firestore';
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

// Firebase configuration with fallbacks for missing env vars
const firebaseConfig = {
  apiKey: API_KEY || "your-api-key-here",
  authDomain: AUTH_DOMAIN || "your-project.firebaseapp.com",
  projectId: PROJECT_ID || "your-project-id",
  storageBucket: STORAGE_BUCKET || "your-project.firebasestorage.app",
  messagingSenderId: MESSAGING_SENDER_ID || "your-sender-id",
  appId: APP_ID || "your-app-id"
};

// Initialize Firebase with error handling
let firebaseApp: firebase.app.App;

try {
  if (!firebase.apps.length) {
    firebaseApp = firebase.initializeApp(firebaseConfig);
    console.log('Firebase initialized successfully');
  } else {
    firebaseApp = firebase.apps[0];
    console.log('Firebase already initialized');
  }
} catch (error) {
  console.error('Failed to initialize Firebase:', error);
  // Create a minimal Firebase app for fallback
  if (!firebase.apps.length) {
    firebaseApp = firebase.initializeApp({
      apiKey: 'fallback-key',
      authDomain: 'fallback-domain',
      projectId: 'fallback-project',
      storageBucket: 'fallback-bucket',
      messagingSenderId: '123456789',
      appId: 'fallback-app-id'
    });
  } else {
    firebaseApp = firebase.apps[0];
  }
}

export const auth = firebase.auth();
export const firestore = firebase.firestore();
export const googleProvider = new firebase.auth.GoogleAuthProvider();

// Configure Google Sign-In
googleProvider.addScope('email');
googleProvider.addScope('profile');

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