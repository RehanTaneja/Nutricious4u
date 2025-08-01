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

const firebaseConfig = {
  apiKey: API_KEY,
  authDomain: AUTH_DOMAIN,
  projectId: PROJECT_ID,
  storageBucket: STORAGE_BUCKET,
  messagingSenderId: MESSAGING_SENDER_ID,
  appId: APP_ID,
};

if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}

export const auth = firebase.auth();
export const firestore = firebase.firestore();
export const googleProvider = new firebase.auth.GoogleAuthProvider();
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
      console.log('Failed to get push token for push notification!');
      return;
    }
    token = (await Notifications.getExpoPushTokenAsync()).data;
    console.log('Expo push token:', token);
    
    // Save token to Firestore
    const user = auth.currentUser;
    if (user && token) {
      await firebase.firestore().collection('user_profiles').doc(user.uid).set({ 
        expoPushToken: token 
      }, { merge: true });
      console.log('Saved expoPushToken to Firestore');
    }
  } catch (e) {
    console.log('Error registering for push notifications:', e);
  }
  return token;
}

// Add notification listener for diet notifications
export function setupDietNotificationListener() {
  const subscription = Notifications.addNotificationReceivedListener(notification => {
    console.log('Notification received:', notification);
    
    // Handle diet-related notifications
    const data = notification.request.content.data;
    if (data?.type === 'new_diet') {
      console.log('New diet notification received for user:', data.userId);
      // You can add custom handling here if needed
    } else if (data?.type === 'diet_reminder') {
      console.log('Diet reminder notification received for dietician');
      // You can add custom handling here if needed
    }
  });

  return subscription;
} 