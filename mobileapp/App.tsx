import React, { useState, useEffect, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, Settings, MessageCircle, BookOpen, Utensils } from 'lucide-react-native';
import firebase, { auth, firestore, registerForPushNotificationsAsync, setupDietNotificationListener } from './services/firebase';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppContext } from './contexts/AppContext';
import { SubscriptionProvider, useSubscription } from './contexts/SubscriptionContext';
import { ActivityIndicator, View, Alert, Modal, TouchableOpacity, Text, StyleSheet, ScrollView } from 'react-native';
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
  MySubscriptionsScreen // <-- import my subscriptions screen
} from './screens';
import { getSubscriptionPlans, selectSubscription, SubscriptionPlan, getUserLockStatus, API_URL } from './services/api';

type User = firebase.User;

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// The new Tab Navigator with only Dashboard and Settings
const MainTabs = ({ isDietician, isFreeUser }: { isDietician: boolean; isFreeUser: boolean }) => (
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
    {!isDietician && !isFreeUser && <Tab.Screen name="Chatbot" component={ChatbotScreen} />}
    <Tab.Screen name="Settings" component={SettingsScreen} />
  </Tab.Navigator>
);

function AppContent() {
  const navigationRef = useRef<any>(null);
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
  const [showSubscriptionPopup, setShowSubscriptionPopup] = useState(false);
  const [subscriptionPlans, setSubscriptionPlans] = useState<SubscriptionPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [processingSubscription, setProcessingSubscription] = useState(false);
  const { showUpgradeModal, setShowUpgradeModal, isFreeUser, setIsFreeUser } = useSubscription();
  const [lastResetDate, setLastResetDate] = useState<string | null>(null);
  
  // App lock state
  const [isAppLocked, setIsAppLocked] = useState(false);
  const [amountDue, setAmountDue] = useState(0);
  const [showLockModal, setShowLockModal] = useState(false);

  // Daily reset mechanism
  const checkAndResetDailyData = async () => {
    if (!user?.uid) return;
    
    try {
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
      const storedDate = await AsyncStorage.getItem(`lastResetDate_${user.uid}`);
      
      if (storedDate !== today) {
        console.log('[Daily Reset] New day detected, resetting daily data');
        
        // Reset daily data by calling the backend with timeout
        const enhancedApi = await import('./services/api');
        const resetPromise = enhancedApi.default.post(`/user/${user.uid}/reset-daily`, {});
        
        // Add timeout to prevent hanging
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Daily reset timeout')), 15000) // Increased timeout
        );
        
        await Promise.race([resetPromise, timeoutPromise]);
        
        // Store the new date
        await AsyncStorage.setItem(`lastResetDate_${user.uid}`, today);
        setLastResetDate(today);
        
        // Force refresh of dashboard data
        setForceReload(x => x + 1);
      }
    } catch (error: any) {
      console.error('[Daily Reset] Error resetting daily data:', error);
      
      // Handle specific error types
      if (error.isClientClosedError || error.isIOSConnectionError) {
        console.log('[Daily Reset] Connection error, will retry later');
        // Don't show error to user, just log it
      } else {
        console.log('[Daily Reset] Other error, continuing without reset');
      }
      
      // Don't throw error to prevent login sequence failure
    }
  };

  // App lock check function
  const checkAppLockStatus = async () => {
    if (!user?.uid || isDietician) return; // Don't check for dieticians
    
    try {
      // Add timeout to prevent hanging
      const lockPromise = getUserLockStatus(user.uid);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('App lock check timeout')), 12000) // Increased timeout
      );
      
      const lockStatus = await Promise.race([lockPromise, timeoutPromise]);
      setIsAppLocked(lockStatus.isAppLocked);
      setAmountDue(lockStatus.amountDue);
      
      // Show lock modal if app is locked
      if (lockStatus.isAppLocked) {
        setShowLockModal(true);
      }
    } catch (error: any) {
      console.error('[App Lock] Error checking lock status:', error);
      
      // Handle specific error types
      if (error.isClientClosedError || error.isIOSConnectionError) {
        console.log('[App Lock] Connection error, will retry later');
        // Don't show error to user, just log it
      } else {
        console.log('[App Lock] Other error, continuing without lock check');
      }
      
      // Don't throw error to prevent login sequence failure
    }
  };

  const handleSubscriptionSelection = async (planId: string) => {
    if (!user?.uid) return;
    
    try {
      setProcessingSubscription(true);
      
      // Select the subscription (this now also updates the total amount)
      const result = await selectSubscription(user.uid, planId);
      
      if (result.success) {
        setShowSubscriptionPopup(false);
        setSelectedPlan(null);
        setHasActiveSubscription(true);
        // Refresh the app state
        setForceReload(x => x + 1);
      }
    } catch (error: any) {
      console.error('Error selecting subscription:', error);
      alert(error.message || 'Failed to select subscription');
    } finally {
      setProcessingSubscription(false);
    }
  };

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
                      id: firebaseUser.uid,
                      userId: firebaseUser.uid, // For backward compatibility
                      firstName: 'Ekta',
                      lastName: 'Taneja',
                      age: 30,
                      gender: 'female',
                      email: firebaseUser.email || 'nutricious4u@gmail.com',
                      currentWeight: 70,
                      goalWeight: 70,
                      height: 170,
                      dietaryPreference: 'vegetarian',
                      favouriteCuisine: '',
                      allergies: '',
                      medicalConditions: '',
                      targetCalories: 2000,
                      targetProtein: 150,
                      targetFat: 65,
                      activityLevel: 'moderate',
                      stepGoal: 10000,
                      caloriesBurnedGoal: 500
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
                    // Add delay before profile check to prevent conflicts
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
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
                  
                  // Check subscription status for non-dietician users - SEQUENTIAL to prevent 499 errors
                  if (!isDieticianAccount && profile) {
                    try {
                      // Add longer delay between API calls to prevent connection conflicts
                      await new Promise(resolve => setTimeout(resolve, 2000)); // Increased to 2 seconds
                      
                      const { getSubscriptionStatus, getQueueStatus } = await import('./services/api');
                      
                      // Log queue status before making requests
                      const queueStatus = getQueueStatus();
                      console.log('[Queue Status] Before subscription check:', queueStatus);
                      
                      const subscriptionStatus = await getSubscriptionStatus(firebaseUser.uid);
                      
                      // Check if user is on free plan or has active subscription
                      if (subscriptionStatus.isFreeUser || !subscriptionStatus.isSubscriptionActive) {
                        console.log('[Subscription Check] User is on free plan or has no active subscription');
                        console.log('[Subscription Check] subscriptionStatus:', subscriptionStatus);
                        setHasActiveSubscription(false);
                        setIsFreeUser(true);
                      } else {
                        console.log('[Subscription Check] User has active paid subscription');
                        console.log('[Subscription Check] subscriptionStatus:', subscriptionStatus);
                        setHasActiveSubscription(true);
                        setIsFreeUser(false);
                      }
                      
                      // Add longer delay before next API call
                      await new Promise(resolve => setTimeout(resolve, 2000)); // Increased to 2 seconds
                      
                      // Check and reset daily data (with error handling)
                      try {
                        await checkAndResetDailyData();
                      } catch (dailyResetError) {
                        console.log('[Daily Reset] Error during login sequence, continuing:', dailyResetError);
                      }
                      
                      // Add longer delay before next API call
                      await new Promise(resolve => setTimeout(resolve, 2000)); // Increased to 2 seconds
                      
                      // Check app lock status (with error handling)
                      try {
                        await checkAppLockStatus();
                      } catch (lockError) {
                        console.log('[App Lock] Error during login sequence, continuing:', lockError);
                      }
                      
                      // Log final queue status
                      const finalQueueStatus = getQueueStatus();
                      console.log('[Queue Status] After login sequence:', finalQueueStatus);
                    } catch (error) {
                      console.log('[Subscription Check] Error checking subscription status:', error);
                      // If we can't check subscription, assume they are free users
                      setHasActiveSubscription(false);
                      setIsFreeUser(true);
                    }
                  } else if (!isDieticianAccount && !profile) {
                    // New user without profile - default to free plan
                    setHasActiveSubscription(false);
                    setIsFreeUser(true);
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

  // Check app lock status when app comes to foreground
  useEffect(() => {
    if (user?.uid && !isDietician) {
      const checkLockOnFocus = () => {
        checkAppLockStatus();
      };

      // Add longer delay to prevent conflict with login sequence
      const initialCheck = setTimeout(() => {
        checkLockOnFocus();
      }, 5000); // Increased to 5 seconds to avoid conflict with login sequence

      // Set up interval to check periodically (every 60 seconds instead of 30)
      const interval = setInterval(checkLockOnFocus, 60000); // Increased interval

      return () => {
        clearTimeout(initialCheck);
        clearInterval(interval);
      };
    }
  }, [user?.uid, isDietician]);

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
      <NavigationContainer ref={navigationRef}>
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
          ) : (
            <>
              <Stack.Screen
                name="Main"
                children={() => <MainTabs isDietician={isDietician} isFreeUser={isFreeUser} />}
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

      {/* App Lock Modal */}
      <Modal
        visible={showLockModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => {}} // Prevent closing by back button
      >
        <View style={styles.lockModalOverlay}>
          <View style={styles.lockModalContainer}>
            <Text style={styles.lockModalTitle}>Amount Due Not Paid</Text>
            <Text style={styles.lockModalSubtitle}>
              Your app has been locked due to unpaid amount
            </Text>
            
            <View style={styles.lockModalAmountContainer}>
              <Text style={styles.lockModalAmountLabel}>Amount Due:</Text>
              <Text style={styles.lockModalAmount}>₹{amountDue.toLocaleString()}</Text>
            </View>
            
            <Text style={styles.lockModalMessage}>
              Please contact your dietician to unlock your app or pay the due amount.
            </Text>
            
            <View style={styles.lockModalButtons}>
              <TouchableOpacity
                style={styles.lockModalContactButton}
                onPress={() => {
                  // This could open a contact form or messaging feature
                  Alert.alert(
                    'Contact Dietician',
                    'Please contact your dietician to unlock your app.',
                    [{ text: 'OK' }]
                  );
                }}
              >
                <Text style={styles.lockModalContactButtonText}>Contact Dietician</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Upgrade Subscription Modal */}
      <Modal
        visible={showUpgradeModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowUpgradeModal(false)}
      >
        <View style={styles.upgradeModalOverlay}>
          <View style={styles.upgradeModalContainer}>
            <Text style={styles.upgradeModalTitle}>Upgrade to a Paid Plan</Text>
            <Text style={styles.upgradeModalSubtitle}>
              Get custom diet plans, AI chatbot assistance and custom notifications for your diet
            </Text>
            
            <View style={styles.upgradeModalButtons}>
              <TouchableOpacity
                style={styles.upgradeModalCancelButton}
                onPress={() => setShowUpgradeModal(false)}
              >
                <Text style={styles.upgradeModalCancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.upgradeModalUpgradeButton}
                onPress={() => {
                  setShowUpgradeModal(false);
                  // Navigate to my subscriptions
                  if (navigationRef.current) {
                    navigationRef.current.navigate('MySubscriptions');
                  }
                }}
              >
                <Text style={styles.upgradeModalUpgradeButtonText}>My Subscriptions</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Subscription Popup Modal */}
      <Modal
        visible={showSubscriptionPopup}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSubscriptionPopup(false)}
      >
        <View style={styles.subscriptionPopupOverlay}>
          <View style={styles.subscriptionPopupContainer}>
            <Text style={styles.subscriptionPopupTitle}>Select a Subscription Plan</Text>
            <Text style={styles.subscriptionPopupSubtitle}>
              Choose a plan to continue your fitness journey
            </Text>
            
            <ScrollView style={styles.subscriptionPlansScrollView} showsVerticalScrollIndicator={false}>
              {subscriptionPlans.map((plan) => (
                <TouchableOpacity
                  key={plan.planId}
                  style={[
                    styles.subscriptionPopupPlanItem,
                    selectedPlan === plan.planId && styles.subscriptionSelectedPlanItem
                  ]}
                  onPress={() => setSelectedPlan(plan.planId)}
                  activeOpacity={0.7}
                >
                  <View style={styles.subscriptionPopupPlanHeader}>
                    <Text style={styles.subscriptionPopupPlanName}>{plan.name}</Text>
                    <Text style={styles.subscriptionPopupPlanPrice}>₹{plan.price.toLocaleString()}</Text>
                  </View>
                  <Text style={styles.subscriptionPopupPlanDuration}>{plan.duration}</Text>
                  <Text style={styles.subscriptionPopupPlanDescription}>{plan.description}</Text>
                  {selectedPlan === plan.planId && (
                    <View style={styles.subscriptionPopupPlanSelectedIndicator}>
                      <Text style={styles.subscriptionPopupPlanSelectedText}>✓ Selected</Text>
                    </View>
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
            
            <View style={styles.subscriptionPopupButtons}>
              <TouchableOpacity
                style={styles.subscriptionPopupCancelButton}
                onPress={() => {
                  setShowSubscriptionPopup(false);
                  setSelectedPlan(null);
                }}
              >
                <Text style={styles.subscriptionPopupCancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[
                  styles.subscriptionPopupConfirmButton,
                  !selectedPlan && styles.subscriptionPopupConfirmButtonDisabled
                ]}
                onPress={() => selectedPlan && handleSubscriptionSelection(selectedPlan)}
                disabled={!selectedPlan || processingSubscription}
              >
                <Text style={styles.subscriptionPopupConfirmButtonText}>
                  {processingSubscription ? 'Processing...' : 'Confirm Selection'}
                </Text>
              </TouchableOpacity>
            </View>
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
  subscriptionPopupOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  subscriptionPopupContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    margin: 20,
    maxHeight: '80%',
    width: '90%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  subscriptionPopupTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#27272A',
    textAlign: 'center',
    marginBottom: 8,
  },
  subscriptionPopupSubtitle: {
    fontSize: 14,
    color: '#A1A1AA',
    textAlign: 'center',
    marginBottom: 20,
  },
  subscriptionPlansScrollView: {
    maxHeight: 300,
  },
  subscriptionPopupPlanItem: {
    backgroundColor: '#E6F8F0',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  subscriptionSelectedPlanItem: {
    borderColor: '#6EE7B7',
    backgroundColor: '#f0fff4',
  },
  subscriptionPopupPlanHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  subscriptionPopupPlanName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#27272A',
  },
  subscriptionPopupPlanPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#6EE7B7',
  },
  subscriptionPopupPlanDuration: {
    fontSize: 14,
    color: '#A1A1AA',
    marginBottom: 4,
  },
  subscriptionPopupPlanDescription: {
    fontSize: 14,
    color: '#27272A',
    lineHeight: 20,
  },
  subscriptionPopupPlanSelectedIndicator: {
    marginTop: 8,
    alignItems: 'center',
  },
  subscriptionPopupPlanSelectedText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#6EE7B7',
  },
  subscriptionPopupButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
    gap: 12,
  },
  subscriptionPopupCancelButton: {
    flex: 1,
    backgroundColor: '#A1A1AA',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  subscriptionPopupCancelButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  subscriptionPopupConfirmButton: {
    flex: 1,
    backgroundColor: '#6EE7B7',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  subscriptionPopupConfirmButtonDisabled: {
    backgroundColor: '#A1A1AA',
  },
  subscriptionPopupConfirmButtonText: {
    color: '#27272A',
    fontSize: 16,
    fontWeight: '600',
  },
  // App Lock Modal Styles
  lockModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  lockModalContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 24,
    margin: 20,
    width: '90%',
    maxWidth: 400,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 10,
  },
  lockModalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FF4444',
    textAlign: 'center',
    marginBottom: 8,
  },
  lockModalSubtitle: {
    fontSize: 16,
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 20,
  },
  lockModalAmountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    paddingVertical: 16,
    paddingHorizontal: 24,
    backgroundColor: '#FFF5F5',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#FF4444',
  },
  lockModalAmountLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginRight: 8,
  },
  lockModalAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FF4444',
  },
  lockModalMessage: {
    fontSize: 16,
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  lockModalButtons: {
    width: '100%',
  },
  lockModalContactButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  lockModalContactButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  // Upgrade Modal Styles
  upgradeModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  upgradeModalContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    margin: 20,
    width: '90%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  upgradeModalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#27272A',
    textAlign: 'center',
    marginBottom: 8,
  },
  upgradeModalSubtitle: {
    fontSize: 14,
    color: '#A1A1AA',
    textAlign: 'center',
    marginBottom: 24,
  },
  upgradeModalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  upgradeModalCancelButton: {
    backgroundColor: '#EF4444',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    flex: 0.48,
    alignItems: 'center',
  },
  upgradeModalCancelButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  upgradeModalUpgradeButton: {
    backgroundColor: '#10B981',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    flex: 0.48,
    alignItems: 'center',
  },
  upgradeModalUpgradeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default function App() {
  return (
    <SubscriptionProvider>
      <AppContent />
    </SubscriptionProvider>
  );
}