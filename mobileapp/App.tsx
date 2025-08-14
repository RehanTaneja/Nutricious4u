import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, Settings, MessageCircle, BookOpen, Utensils } from 'lucide-react-native';
import firebase, { auth, firestore, registerForPushNotificationsAsync, setupDietNotificationListener } from './services/firebase';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppContext } from './contexts/AppContext';
import { ActivityIndicator, View, Alert, Modal, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { getUserProfile, createUserProfile } from './services/api';
import { ChatbotScreen } from './ChatbotScreen';
import { 
  API_KEY, 
  AUTH_DOMAIN, 
  PROJECT_ID, 
  STORAGE_BUCKET, 
  MESSAGING_SENDER_ID, 
  APP_ID,
  PRODUCTION_BACKEND_URL 
} from '@env';

import {
  LoginSignupScreen,
  DashboardScreen,
  FoodLogScreen,
  WorkoutLogScreen,
  SettingsScreen,
  COLORS,
  LoginSettingsScreen,
  NotificationSettingsScreen,
  TrackingDetailsScreen,
  RoutineScreen, // <-- import the new screen
  DieticianScreen, // <-- import DieticianScreen
  DieticianMessageScreen, // <-- import the new message screen
  DieticianMessagesListScreen, // <-- import the new messages list screen
  ScheduleAppointmentScreen, // <-- import the schedule appointment screen
  DieticianDashboardScreen, // <-- import the dietician dashboard screen
  UploadDietScreen, // <-- import the new screen
  RecipesScreen, // <-- import the new recipes screen
  SubscriptionSelectionScreen, // <-- import subscription selection screen
  MySubscriptionsScreen, // <-- import my subscriptions screen
  NotificationsScreen // <-- import notifications screen
} from './screens';

type User = firebase.User;

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// The new Tab Navigator with only Dashboard and Settings
const MainTabs = ({ isDietician }: { isDietician: boolean }) => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      headerShown: false, // The Stack Navigator will handle the header
      tabBarIcon: ({ color, size }) => {
        if (route.name === 'Dashboard') {
          return <Home color={color} size={size} />;
        } else if (route.name === 'Recipes') {
          return <Utensils color={color} size={size} />; // Use utensils icon
        } else if (route.name === 'Messages') {
          // Use MessageCircle for dietician, BookOpen for user
          return isDietician ? <MessageCircle color={color} size={size} /> : <BookOpen color={color} size={size} />;
        } else if (route.name === 'Dietician') {
          return <BookOpen color={color} size={size} />;
        } else if (route.name === 'UploadDiet') {
          return <BookOpen color={color} size={size} />;
        } else if (route.name === 'Chatbot') {
          return <MessageCircle color={color} size={size} />;
        } else if (route.name === 'Settings') {
          return <Settings color={color} size={size} />;
        }
        return null;
      },
      tabBarActiveTintColor: COLORS.primary,
      tabBarInactiveTintColor: COLORS.placeholder,
    })}
  >
    <Tab.Screen name="Dashboard" component={isDietician ? DieticianDashboardScreen : DashboardScreen} />
    <Tab.Screen name="Recipes" component={RecipesScreen} options={{ title: 'Recipes' }} />
    {isDietician ? (
      <>
        <Tab.Screen name="Messages" component={DieticianMessagesListScreen} options={{ title: 'Messages' }} />
        <Tab.Screen name="UploadDiet" component={UploadDietScreen} options={{ title: 'Upload Diet' }} />
      </>
    ) : (
      <Tab.Screen name="Dietician" component={DieticianScreen} />
    )}
    {!isDietician && <Tab.Screen name="Chatbot" component={ChatbotScreen} />}
    <Tab.Screen name="Settings" component={SettingsScreen} />
  </Tab.Navigator>
);

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasCompletedQuiz, setHasCompletedQuiz] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [checkingProfile, setCheckingProfile] = useState(false);
  const [isDietician, setIsDietician] = useState(false);
  const [forceReload, setForceReload] = useState(0);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [firebaseInitialized, setFirebaseInitialized] = useState(false);
  const [hasActiveSubscription, setHasActiveSubscription] = useState<boolean | null>(null);

  useEffect(() => {
    let unsubscribe: any;
    let notificationUnsubscribe: any;
    let dietNotificationSubscription: any;
    let timeoutId: any;
    
    // Set a timeout to prevent infinite loading
    timeoutId = setTimeout(() => {
      console.log('Loading timeout reached, forcing app to continue');
      setLoading(false);
      setCheckingAuth(false);
      setCheckingProfile(false);
    }, 15000); // Increased to 15 seconds
    
    const initializeApp = async () => {
      try {
        // Debug environment variables
        console.log('=== ENVIRONMENT VARIABLES DEBUG ===');
        console.log('API_KEY:', API_KEY ? 'SET' : 'MISSING');
        console.log('AUTH_DOMAIN:', AUTH_DOMAIN ? 'SET' : 'MISSING');
        console.log('PROJECT_ID:', PROJECT_ID ? 'SET' : 'MISSING');
        console.log('STORAGE_BUCKET:', STORAGE_BUCKET ? 'SET' : 'MISSING');
        console.log('MESSAGING_SENDER_ID:', MESSAGING_SENDER_ID ? 'SET' : 'MISSING');
        console.log('APP_ID:', APP_ID ? 'SET' : 'MISSING');
        console.log('PRODUCTION_BACKEND_URL:', PRODUCTION_BACKEND_URL ? 'SET' : 'MISSING');
        console.log('__DEV__:', __DEV__);
        console.log('=====================================');
        
        // Test environment variable loading
        const envTest = {
          API_KEY: !!API_KEY,
          AUTH_DOMAIN: !!AUTH_DOMAIN,
          PROJECT_ID: !!PROJECT_ID,
          STORAGE_BUCKET: !!STORAGE_BUCKET,
          MESSAGING_SENDER_ID: !!MESSAGING_SENDER_ID,
          APP_ID: !!APP_ID,
          PRODUCTION_BACKEND_URL: !!PRODUCTION_BACKEND_URL
        };
        
        const missingVars = Object.entries(envTest)
          .filter(([key, value]) => !value)
          .map(([key]) => key);
        
        if (missingVars.length > 0) {
          console.error('Missing environment variables:', missingVars);
          setError(`Missing environment variables: ${missingVars.join(', ')}`);
          setLoading(false);
          return;
        }
        
        setFirebaseInitialized(true);
        
        // Check if Firebase is properly initialized
        if (!firebase.apps.length) {
          console.error('Firebase not initialized');
          setError('Firebase configuration error - no apps found');
          setLoading(false);
          return;
        }
        
        // Initialize other services
        await initializeServices();
      } catch (error) {
        console.error('Error initializing app:', error);
        setError(`Failed to initialize app: ${error}`);
      } finally {
        // Always clear loading state
        setLoading(false);
        setCheckingAuth(false);
        setCheckingProfile(false);
        if (timeoutId) clearTimeout(timeoutId);
      }
    };

    const initializeServices = async () => {
      try {
        
        // Register for push notifications
        try {
          await registerForPushNotificationsAsync();
        } catch (error) {
          console.warn('Push notification registration failed:', error);
        }
        
        // Set up diet notification listener
        try {
          dietNotificationSubscription = setupDietNotificationListener();
        } catch (error) {
          console.warn('Diet notification listener setup failed:', error);
        }
        
        
        // Set up auth state listener
        unsubscribe = auth.onAuthStateChanged(async (firebaseUser) => {
          try {
            console.log('[AuthStateChanged] firebaseUser:', firebaseUser);
            
            if (firebaseUser) {
              setUser(firebaseUser);
              setCheckingProfile(true);
              
              try {
                // Check if user is dietician by trying to get their profile from backend
                // For dietician account, we'll handle this through the backend API
                const isDieticianAccount = firebaseUser.email === 'nutricious4u@gmail.com';
                setIsDietician(isDieticianAccount);
                
                // For dietician, we'll create their profile through the backend if needed
                if (isDieticianAccount) {
                  try {
                    // Create dietician profile through backend (don't check if exists first)
                    await createUserProfile({
                      userId: firebaseUser.uid,
                      firstName: 'Ekta',
                      lastName: 'Taneja',
                      age: 30,
                      gender: 'female',
                      email: firebaseUser.email || 'nutricious4u@gmail.com'
                    });
                    setForceReload(x => x + 1); // force re-render
                  } catch (error) {
                    console.error('Error handling dietician profile:', error);
                  }
                }
                
                // Set up real-time notification listener for non-dietician users
                if (!isDieticianAccount) {
                  try {
                    notificationUnsubscribe = firestore
                      .collection('notifications')
                      .where('userId', '==', firebaseUser.uid)
                      .where('read', '==', false)
                      .onSnapshot(snapshot => {
                        snapshot.docChanges().forEach(change => {
                          if (change.type === 'added') {
                            const notification = change.doc.data();
                            // Mark notification as read immediately to prevent re-triggering
                            firestore.collection('notifications').doc(change.doc.id).update({
                              read: true
                            });
                            
                            setNotificationMessage(notification.message);
                            setShowNotification(true);
                          }
                        });
                      }, error => {
                        console.error('Error listening to notifications:', error);
                      });
                  } catch (error) {
                    console.warn('Failed to set up notification listener:', error);
                  }
                }
                
                // Dietician skips quiz
                if (isDieticianAccount) {
                  setHasCompletedQuiz(true);
                  console.log('[Dietician Debug] Skipping quiz for dietician');
                } else {
                  // For regular users, check if they have a profile
                  let profile = null;
                  try {
                    profile = await getUserProfile(firebaseUser.uid);
                    if (profile && profile.firstName && profile.firstName !== 'User') {
                      setHasCompletedQuiz(true);
                      await AsyncStorage.setItem('hasCompletedQuiz', 'true');
                      console.log('[Profile Check] User has completed profile, quiz status: true');
                    } else {
                      setHasCompletedQuiz(false);
                      await AsyncStorage.setItem('hasCompletedQuiz', 'false');
                      console.log('[Profile Check] User has no profile or placeholder profile, quiz status: false');
                    }
                  } catch (error) {
                    console.log('[Profile Check] Error checking profile, assuming quiz not completed:', error);
                    setHasCompletedQuiz(false);
                    await AsyncStorage.setItem('hasCompletedQuiz', 'false');
                  }
                  
                  // Check subscription status for non-dietician users
                  if (!isDieticianAccount && profile) {
                    try {
                      const { getSubscriptionStatus } = await import('./services/api');
                      const subscriptionStatus = await getSubscriptionStatus(firebaseUser.uid);
                      
                      // If user has no active subscription, redirect to subscription selection
                      if (!subscriptionStatus.isSubscriptionActive) {
                        // Navigate to subscription selection
                        // This will be handled in the navigation logic
                        console.log('[Subscription Check] User has no active subscription');
                        setHasActiveSubscription(false);
                      } else {
                        console.log('[Subscription Check] User has active subscription');
                        setHasActiveSubscription(true);
                      }
                    } catch (error) {
                      console.log('[Subscription Check] Error checking subscription status:', error);
                      // If we can't check subscription, assume they need one
                      setHasActiveSubscription(false);
                    }
                  } else if (!isDieticianAccount && !profile) {
                    // New user without profile - they'll need subscription after quiz
                    setHasActiveSubscription(false);
                  }
                }
              } catch (e) {
                console.error('Error in user profile setup:', e);
                setHasCompletedQuiz(false);
                await AsyncStorage.setItem('hasCompletedQuiz', 'false');
              }
              setCheckingProfile(false);
            } else {
              setUser(null);
              setHasCompletedQuiz(false);
              setIsDietician(false);
              setHasActiveSubscription(null);
              
              // Only check for saved credentials and auto-login on app start, not on every logout
              try {
                const savedEmail = await AsyncStorage.getItem('savedEmail');
                const savedPassword = await AsyncStorage.getItem('savedPassword');
                if (savedEmail && savedPassword) {
                  try {
                    await auth.signInWithEmailAndPassword(savedEmail, savedPassword);
                    return;
                  } catch (e) {
                    // Auto-login failed, proceed to show login screen.
                    console.log('[Dietician Debug] Auto-login failed:', e);
                  }
                } else {
                  // No saved credentials, showing login screen
                }
              } catch (error) {
                console.warn('Failed to check saved credentials:', error);
              }
              setCheckingAuth(false);
              setCheckingProfile(false);
              setLoading(false);
              if (timeoutId) clearTimeout(timeoutId);
            }
            setCheckingAuth(false);
            if (timeoutId) clearTimeout(timeoutId);
          } catch (innerError) {
            console.error('Error in auth state change:', innerError);
            setCheckingAuth(false);
            setCheckingProfile(false);
            setError(`Auth error: ${innerError}`);
            if (timeoutId) clearTimeout(timeoutId);
          }
        });
      } catch (error) {
        console.error('Error in initializeServices:', error);
        setCheckingAuth(false);
        setCheckingProfile(false);
        setError(`Service initialization error: ${error}`);
      } finally {
        setCheckingAuth(false);
        setCheckingProfile(false);
        setLoading(false);
        if (timeoutId) clearTimeout(timeoutId);
      }
    };
    
    initializeApp();
    
    return () => {
      if (unsubscribe) unsubscribe();
      if (notificationUnsubscribe) notificationUnsubscribe();
      if (dietNotificationSubscription) dietNotificationSubscription.remove();
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [forceReload]);

  // Show error screen if there's a critical error
  if (error) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.background }}>
        <Text style={{ fontSize: 18, color: 'red', textAlign: 'center', marginBottom: 20 }}>
          {error}
        </Text>
        <TouchableOpacity 
          style={{ backgroundColor: COLORS.primary, padding: 15, borderRadius: 8 }}
          onPress={() => {
            setError(null);
            setLoading(true);
            setCheckingAuth(true);
            setCheckingProfile(false);
          }}
        >
          <Text style={{ color: 'white', fontSize: 16 }}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (checkingAuth || checkingProfile || loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.background }}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={{ marginTop: 10, color: COLORS.text }}>Loading...</Text>
        <Text style={{ marginTop: 5, color: COLORS.placeholder, fontSize: 12 }}>
          {checkingAuth ? 'Checking authentication...' : checkingProfile ? 'Loading profile...' : 'Initializing...'}
        </Text>
      </View>
    );
  }

  const { QnAScreen, AccountSettingsScreen } = require('./screens');

  return (
    <AppContext.Provider value={{ hasCompletedQuiz, setHasCompletedQuiz }}>
      <NavigationContainer>
        <Stack.Navigator>
          {!user ? (
            <Stack.Screen
              name="Login"
              component={LoginSignupScreen}
              options={{ headerShown: false }}
            />
          ) : !hasCompletedQuiz && !isDietician ? (
            <Stack.Screen
              name="QnA"
              component={QnAScreen}
              initialParams={{ userId: user.uid }}
              options={{ headerShown: false }}
            />
          ) : hasCompletedQuiz && !isDietician && hasActiveSubscription === false ? (
            <Stack.Screen
              name="SubscriptionSelection"
              component={SubscriptionSelectionScreen}
              options={{ headerShown: false }}
            />
          ) : (
            <>
              <Stack.Screen
                name="Main"
                children={() => <MainTabs isDietician={isDietician} />}
                options={{ headerShown: false }}
              />
              <Stack.Screen name="DieticianMessage" component={DieticianMessageScreen} options={{ headerShown: false }} />
              <Stack.Screen name="ScheduleAppointment" component={ScheduleAppointmentScreen} options={{ headerShown: false }} />
              <Stack.Screen name="LogFood" component={FoodLogScreen} options={{ headerShown: false }} />
              <Stack.Screen name="LogWorkout" component={WorkoutLogScreen} options={{ headerShown: false }} />
              <Stack.Screen name="AccountSettings" component={AccountSettingsScreen} options={{ headerShown: false }} />
              <Stack.Screen name="LoginSettings" component={LoginSettingsScreen} options={{ headerShown: false }} />
              <Stack.Screen name="NotificationSettings" component={NotificationSettingsScreen} options={{ headerShown: false }} />
              <Stack.Screen name="TrackingDetails" component={TrackingDetailsScreen} options={{ headerShown: false }} />
              <Stack.Screen name="Routine" component={RoutineScreen} options={{ headerShown: false }} />
              <Stack.Screen name="SubscriptionSelection" component={SubscriptionSelectionScreen} options={{ headerShown: false }} />
              <Stack.Screen name="MySubscriptions" component={MySubscriptionsScreen} options={{ headerShown: false }} />
              <Stack.Screen name="Notifications" component={NotificationsScreen} options={{ headerShown: false }} />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
      
      {/* Custom Notification Modal */}
      <Modal
        visible={showNotification}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowNotification(false)}
      >
        <View style={styles.notificationOverlay}>
          <View style={styles.notificationPopup}>
            <Text style={styles.notificationTitle}>Appointment Update</Text>
            <Text style={styles.notificationMessage}>{notificationMessage}</Text>
            <TouchableOpacity 
              style={styles.notificationButton} 
              onPress={() => setShowNotification(false)}
            >
              <Text style={styles.notificationButtonText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </AppContext.Provider>
  );
}

const styles = StyleSheet.create({
  notificationOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  notificationPopup: {
    backgroundColor: '#34D399',
    borderRadius: 16,
    padding: 24,
    margin: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  notificationTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  notificationMessage: {
    fontSize: 16,
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 22,
  },
  notificationButton: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  notificationButtonText: {
    color: '#34D399',
    fontSize: 16,
    fontWeight: 'bold',
  },
});