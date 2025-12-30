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
import Constants from 'expo-constants';
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

// Setup Android notification channel (required for Android 8.0+)
if (Platform.OS === 'android') {
  Notifications.setNotificationChannelAsync('default', {
    name: 'Default',
    importance: Notifications.AndroidImportance.MAX,
    vibrationPattern: [0, 250, 250, 250],
    lightColor: '#FF231F7C',
  });
}

// Debug environment variables
console.log('=== FIREBASE CONFIG DEBUG ===');
console.log('API_KEY:', API_KEY ? `${API_KEY.substring(0, 10)}...` : 'MISSING');
console.log('AUTH_DOMAIN:', AUTH_DOMAIN || 'MISSING');
console.log('PROJECT_ID:', PROJECT_ID || 'MISSING');
console.log('STORAGE_BUCKET:', STORAGE_BUCKET || 'MISSING');
console.log('MESSAGING_SENDER_ID:', MESSAGING_SENDER_ID || 'MISSING');
console.log('APP_ID:', APP_ID || 'MISSING');
console.log('EXPO_PROJECT_ID:', (Constants?.expoConfig?.extra as any)?.eas?.projectId || (Constants as any)?.easConfig?.projectId || process.env.EXPO_PROJECT_ID || 'MISSING');
console.log('================================');

const EXPO_PROJECT_ID =
  (Constants?.expoConfig?.extra as any)?.eas?.projectId ||
  (Constants as any)?.easConfig?.projectId ||
  process.env.EXPO_PROJECT_ID ||
  '38ed8fe9-6087-4fdd-9164-a0c36ee3a9fb'; // fallback to known EAS project ID

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

export async function registerForPushNotificationsAsync(userId?: string) {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('🔔 [PUSH TOKEN REGISTRATION] START');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`[PUSH TOKEN] Time: ${new Date().toISOString()}`);
  console.log(`[PUSH TOKEN] Platform: ${Platform.OS}`);
  console.log(`[PUSH TOKEN] User ID provided: ${userId || 'None'}`);
  console.log(`[PUSH TOKEN] Current user: ${auth.currentUser?.uid || 'None'}`);
  console.log(`[PUSH TOKEN] Current user email: ${auth.currentUser?.email || 'None'}`);
  
  let token;
  try {
    // Step 1: Check existing permission status
    console.log('[PUSH TOKEN] Step 1: Checking existing notification permissions...');
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    console.log(`[PUSH TOKEN] ✓ Existing permission status: ${existingStatus}`);
    
    let finalStatus = existingStatus;
    
    // Step 2: Request permissions if needed
    if (existingStatus !== 'granted') {
      console.log('[PUSH TOKEN] Step 2: Permission not granted, requesting...');
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
      console.log(`[PUSH TOKEN] ✓ Permission request result: ${finalStatus}`);
    } else {
      console.log('[PUSH TOKEN] Step 2: Permission already granted, skipping request');
    }
    
    // Step 3: Check if permission was granted
    if (finalStatus !== 'granted') {
      console.log('[PUSH TOKEN] ❌ FAILED: Notification permission not granted');
      console.log(`[PUSH TOKEN] Final status: ${finalStatus}`);
      console.log('═══════════════════════════════════════════════════════════════');
      logger.log('Failed to get push token for push notification!');
      return null; // FIX: Return null to signal failure, enabling retry
    }
    
    console.log('[PUSH TOKEN] ✓ Permission granted successfully');
    
    // Step 4: Get Expo push token
    if (!EXPO_PROJECT_ID) {
      console.log('[PUSH TOKEN] ❌ Missing Expo project ID, cannot request push token');
      console.log('═══════════════════════════════════════════════════════════════');
      return null; // FIX: Return null to signal failure, enabling retry
    }

    console.log('[PUSH TOKEN] Step 3: Getting Expo push token...');
    console.log(`[PUSH TOKEN] Platform: ${Platform.OS}`);
    console.log(`[PUSH TOKEN] Project ID: ${EXPO_PROJECT_ID}`);
    
    try {
      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId: EXPO_PROJECT_ID
      });
      token = tokenData.data;
      console.log(`[PUSH TOKEN] ✓ Token received successfully`);
      console.log(`[PUSH TOKEN] Token preview: ${token.substring(0, 30)}...`);
      console.log(`[PUSH TOKEN] Token length: ${token.length}`);
      console.log(`[PUSH TOKEN] Token type: ${typeof token}`);
      console.log(`[PUSH TOKEN] Token starts with 'ExponentPushToken': ${token.startsWith('ExponentPushToken')}`);
    } catch (tokenError) {
      console.log('[PUSH TOKEN] ❌ FAILED to get Expo push token');
      console.error('[PUSH TOKEN] Token error:', tokenError);
      console.log('═══════════════════════════════════════════════════════════════');
      throw tokenError;
    }
    
    // Step 5: Save token to Firestore
    console.log('[PUSH TOKEN] Step 4: Saving token to Firestore...');
    try {
      // Use provided userId or get from auth
      const user = userId ? { uid: userId } : auth.currentUser;
      console.log(`[PUSH TOKEN] User for saving: ${user?.uid || 'None'}`);
      
      // CRITICAL FIX: Force refresh ID token to ensure Firestore has valid auth
      // This resolves the timing issue where Firestore's auth context may not be
      // synchronized with Firebase Auth immediately after onAuthStateChanged fires
      if (auth.currentUser) {
        console.log('[PUSH TOKEN] Refreshing ID token for Firestore auth...');
        try {
          await auth.currentUser.getIdToken(true);
          console.log('[PUSH TOKEN] ✓ ID token refreshed successfully');
        } catch (tokenRefreshError) {
          console.error('[PUSH TOKEN] ⚠️ ID token refresh failed:', tokenRefreshError);
          // Continue anyway - the existing token might still work
        }
      }
      
      if (!user) {
        console.log('[PUSH TOKEN] ❌ FAILED: No user available for saving token');
        console.log('═══════════════════════════════════════════════════════════════');
        return null; // FIX: Return null (not token) to signal failure - token wasn't saved!
      }
      
      if (!token) {
        console.log('[PUSH TOKEN] ❌ FAILED: No token available for saving');
        console.log('═══════════════════════════════════════════════════════════════');
        return token;
      }
      
      const saveData = { 
        expoPushToken: token,
        platform: Platform.OS,
        lastTokenUpdate: new Date().toISOString()
      };
      
      console.log(`[PUSH TOKEN] Saving to: user_profiles/${user.uid}`);
      console.log(`[PUSH TOKEN] Save data:`, JSON.stringify(saveData, null, 2));
      
      await firebase.firestore().collection('user_profiles').doc(user.uid).set(saveData, { merge: true });
      
      console.log('[PUSH TOKEN] ✓ Token saved successfully to Firestore');
      console.log(`[PUSH TOKEN] ✓ Token saved for user: ${user.uid}`);
      
      // Verify save was successful
      console.log('[PUSH TOKEN] Step 5: Verifying token was saved...');
      const doc = await firebase.firestore().collection('user_profiles').doc(user.uid).get();
      const savedData = doc.data();
      const savedToken = savedData?.expoPushToken;
      
      if (savedToken === token) {
        console.log('[PUSH TOKEN] ✓✓✓ VERIFICATION SUCCESS: Token matches saved token');
        console.log(`[PUSH TOKEN] Saved token preview: ${savedToken.substring(0, 30)}...`);
      } else {
        console.log('[PUSH TOKEN] ❌ VERIFICATION FAILED: Saved token does not match');
        console.log(`[PUSH TOKEN] Expected: ${token.substring(0, 30)}...`);
        console.log(`[PUSH TOKEN] Got: ${savedToken ? savedToken.substring(0, 30) + '...' : 'None'}`);
      }
      
      console.log('═══════════════════════════════════════════════════════════════');
      console.log('🔔 [PUSH TOKEN REGISTRATION] SUCCESS');
      console.log('═══════════════════════════════════════════════════════════════');
      
      logger.log('Saved expoPushToken to Firestore with platform info');
      logger.log(`Token saved for user: ${user.uid}`);
    } catch (error: any) {
      console.log('[PUSH TOKEN] ❌ FAILED to save push token to Firestore');
      console.error('[PUSH TOKEN] Save error code:', error?.code);
      console.error('[PUSH TOKEN] Save error message:', error?.message);
      console.error('[PUSH TOKEN] Full error:', error);
      console.log('═══════════════════════════════════════════════════════════════');
      logger.log('Failed to save push token to Firestore:', error);
      logger.log('Error code:', error?.code, 'Error message:', error?.message);
      return null; // FIX: Return null so caller knows save failed and retry can happen
    }
  } catch (e) {
    console.log('[PUSH TOKEN] ❌ CRITICAL ERROR in registerForPushNotificationsAsync');
    console.error('[PUSH TOKEN] Error:', e);
    console.log('═══════════════════════════════════════════════════════════════');
    logger.log('Error registering for push notifications:', e);
    return null; // FIX: Return null on any critical error to signal failure
  }
  
  return token;
}

// Simplified diet notification listener - just for basic setup
export function setupDietNotificationListener() {
  try {
    logger.log('Setting up basic diet notification listener for platform:', Platform.OS);
    
    // Return a dummy subscription to prevent crashes
    return {
      remove: () => {}
    };
  } catch (error) {
    logger.log('Failed to setup diet notification listener:', error);
    return {
      remove: () => {}
    };
  }
} 