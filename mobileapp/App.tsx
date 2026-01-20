import React, { useState, useEffect, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, Settings, MessageCircle, BookOpen, Utensils } from 'lucide-react-native';
import firebase, { auth, firestore, setupDietNotificationListener } from './services/firebase';
import { registerAndSavePushToken } from './services/pushTokenManager';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { simpleNotificationHandler } from './services/simpleNotificationHandler';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppContext } from './contexts/AppContext';
import { SubscriptionProvider, useSubscription } from './contexts/SubscriptionContext';
import { ActivityIndicator, View, Alert, Modal, TouchableOpacity, Text, StyleSheet, ScrollView, Platform, SafeAreaView } from 'react-native';
import { getUserProfile, createUserProfile, clearProfileCache, resetDailyData, logFrontendEvent, getLogSummary } from './services/api';
import { ChatbotScreen } from './ChatbotScreen';
import { SafeAreaProvider } from 'react-native-safe-area-context';
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
  MandatoryTrialActivationPopup, // <-- import mandatory trial activation popup
  MandatoryPlanSelectionPopup, // <-- import mandatory plan selection popup
  QnAScreen,
  AccountSettingsScreen
} from './screens';
import { getSubscriptionPlans, selectSubscription, SubscriptionPlan, getUserLockStatus, API_URL, getSubscriptionStatus, getQueueStatus, activateFreeTrial, getTrialStatus } from './services/api';

type User = firebase.User;

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// The new Tab Navigator with only Dashboard and Settings
const MainTabs = ({ isDietician, isFreeUser }: { isDietician: boolean; isFreeUser: boolean }) => {
  console.log('[MAIN TABS] 🚀 MainTabs component rendering with props:', { isDietician, isFreeUser });
  
  // Log MainTabs rendering to backend for EAS builds
  React.useEffect(() => {
    const logMainTabsRender = async () => {
      try {
        const currentUser = auth.currentUser;
        if (currentUser && !__DEV__) {
          await logFrontendEvent(currentUser.uid, 'MAINTABS_RENDER_START', {
            isDietician,
            isFreeUser,
            platform: Platform.OS
          });
        }
      } catch (error) {
        console.warn('Failed to log MainTabs render:', error);
      }
    };
    logMainTabsRender();
  }, [isDietician, isFreeUser]);
  
  // Add iOS-specific error boundary
  try {
    return (
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
    <Tab.Screen 
      name="Dashboard" 
      component={isDietician ? DieticianDashboardScreen : DashboardScreen}
    />
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
  } catch (error) {
    console.error('[MAIN TABS] ❌ Error rendering MainTabs:', error);
    
    // Log error to backend for EAS builds
    const logError = async () => {
      try {
        const currentUser = auth.currentUser;
        if (currentUser && !__DEV__) {
          await logFrontendEvent(currentUser.uid, 'MAINTABS_RENDER_ERROR', {
            error: error instanceof Error ? error.message : String(error),
            stack: error instanceof Error ? error.stack : undefined,
            name: error instanceof Error ? error.name : 'Unknown',
            isDietician,
            isFreeUser,
            platform: Platform.OS
          });
        }
      } catch (logErr) {
        console.warn('Failed to log MainTabs error:', logErr);
      }
    };
    logError();
    
    // iOS-specific fallback
    if (Platform.OS === 'ios') {
      console.log('[MAIN TABS] [iOS] Returning fallback loading screen');
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.background }}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={{ color: COLORS.text, fontSize: 16, marginTop: 10 }}>Loading app...</Text>
        </View>
      );
    }
    
    throw error; // Re-throw for other platforms
  }
};

// Global login state to prevent profile requests during login
let isLoginInProgress = false;
// Set global flag for other components to check
(global as any).isLoginInProgress = false;

function AppContent() {
  const navigationRef = useRef<any>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasCompletedQuiz, setHasCompletedQuiz] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [checkingProfile, setCheckingProfile] = useState(false);
  const [isDietician, setIsDietician] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [firebaseInitialized, setFirebaseInitialized] = useState(false);
  const [hasActiveSubscription, setHasActiveSubscription] = useState<boolean | null>(null);
  const [showSubscriptionPopup, setShowSubscriptionPopup] = useState(false);
  const [pushRegisteredThisSession, setPushRegisteredThisSession] = useState(false);
  // Mandatory popup states
  const [showMandatoryTrialPopup, setShowMandatoryTrialPopup] = useState(false);
  const [showMandatoryPlanPopup, setShowMandatoryPlanPopup] = useState(false);
  const [showTrialSuccessPopup, setShowTrialSuccessPopup] = useState(false);
  const [trialSuccessMessage, setTrialSuccessMessage] = useState('');
  const [showRenewalPopup, setShowRenewalPopup] = useState(false);
  const [renewalMessage, setRenewalMessage] = useState('');
  const [showPlanSwitchPopup, setShowPlanSwitchPopup] = useState(false);
  const [planSwitchMessage, setPlanSwitchMessage] = useState('');
  const [activatingTrial, setActivatingTrial] = useState(false);
  const [selectingPlan, setSelectingPlan] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [availablePlans, setAvailablePlans] = useState<SubscriptionPlan[]>([]);
  const [subscriptionStatus, setSubscriptionStatus] = useState<any>(null);

  // Helper: register push with logging so we can see results in backend logs
  const registerPushWithLogging = async (uid: string, source: string) => {
    console.log(`[NOTIFICATIONS] (${source}) Starting push registration for user: ${uid.substring(0, 8)}...`);
    console.log(`[NOTIFICATIONS] (${source}) Platform: ${Platform.OS}`);
    const projectId =
      (Constants?.expoConfig?.extra as any)?.eas?.projectId ||
      (Constants as any)?.easConfig?.projectId ||
      process.env.EXPO_PROJECT_ID ||
      'MISSING';
    console.log(`[NOTIFICATIONS] (${source}) Project ID: ${projectId}`);
    
    let permissionStatus: string | null = null;
    try {
      const { status } = await Notifications.getPermissionsAsync();
      permissionStatus = status;
      console.log(`[NOTIFICATIONS] (${source}) Permission status: ${permissionStatus}`);
    } catch (permErr) {
      console.warn(`[NOTIFICATIONS] (${source}) Failed to read notification permission:`, permErr);
    }

    if (!__DEV__) {
      try {
        await logFrontendEvent(uid, 'PUSH_REG_ATTEMPT', {
          source,
          platform: Platform.OS,
          projectId,
          permissionStatus
        });
      } catch (logErr) {
        console.warn(`[NOTIFICATIONS] (${source}) Failed to log push reg attempt:`, logErr);
      }
    }

    const result = {
      token: null as string | null,
      error: null as any
    };
    try {
      console.log(`[NOTIFICATIONS] (${source}) Calling registerAndSavePushToken...`);
      const token = await registerAndSavePushToken(uid);
      
      console.log(`[NOTIFICATIONS] (${source}) Token result:`, token ? `${token.substring(0, 30)}...` : 'null');
      
      result.token = token || null;
      if (token) {
        console.log(`[NOTIFICATIONS] (${source}) ✅ Token registered successfully`);
        console.log(`[NOTIFICATIONS] (${source}) Token preview:`, token.substring(0, 30) + '...');
        setPushRegisteredThisSession(true);
      } else {
        console.log(`[NOTIFICATIONS] (${source}) ❌ Token is null or empty`);
      }
    } catch (err: any) {
      console.log(`[NOTIFICATIONS] (${source}) ❌ Exception caught:`, err);
      console.log(`[NOTIFICATIONS] (${source}) Error message:`, err.message);
      console.log(`[NOTIFICATIONS] (${source}) Error code:`, err.code);
      result.error = err;
      console.error(`[NOTIFICATIONS] (${source}) ❌ Push registration failed:`, err);
      
      // LOG FIREBASE INITIALIZATION ERROR TO BACKEND
      if (!__DEV__) {
        try {
          await logFrontendEvent(uid, 'PUSH_TOKEN_ERROR', {
            platform: Platform.OS,
            projectId,
            errorMessage: err.message || String(err),
            errorType: err.constructor?.name || 'Unknown'
          });
        } catch (logErr) {
          console.warn(`[NOTIFICATIONS] (${source}) Failed to log error to backend:`, logErr);
        }
      }
    }

    // Log to backend for observability (only in production)
    if (!__DEV__) {
      try {
        await logFrontendEvent(uid, 'PUSH_REGISTRATION_RESULT', {
          source,
          platform: Platform.OS,
          projectId,
          permissionStatus,
          tokenPreview: result.token ? result.token.substring(0, 30) + '...' : null,
          error: result.error ? String(result.error) : null
        });
      } catch (logErr) {
        console.warn(`[NOTIFICATIONS] (${source}) Failed to log push registration result:`, logErr);
      }
    }
    return result.token;
  };

  // CRITICAL FIX: Force push registration on every app launch with retry logic
  // Previous guard was too restrictive and prevented re-registration on failures
  useEffect(() => {
    const registerPushWithRetry = async () => {
      if (!user) {
        console.log('[NOTIFICATIONS] (Guard) No user, skipping push registration');
        return;
      }

      // Skip if already successfully registered this session
      if (pushRegisteredThisSession) {
        console.log('[NOTIFICATIONS] (Guard) Already registered this session, skipping');
        return;
      }

      console.log('[NOTIFICATIONS] (Guard) 🚀 Starting push registration with retry logic');
      console.log('[NOTIFICATIONS] (Guard) User ID:', user.uid);
      console.log('[NOTIFICATIONS] (Guard) Platform:', Platform.OS);

      const maxRetries = 3;
      let lastError = null;

      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          console.log(`[NOTIFICATIONS] (Guard) Attempt ${attempt}/${maxRetries}`);
          
          const token = await registerPushWithLogging(user.uid, `guard_effect_attempt_${attempt}`);
          
          if (token) {
            console.log(`[NOTIFICATIONS] (Guard) ✅ SUCCESS on attempt ${attempt}`);
            console.log(`[NOTIFICATIONS] (Guard) Token: ${token.substring(0, 30)}...`);
            return; // Success!
          } else {
            console.warn(`[NOTIFICATIONS] (Guard) ⚠️ No token returned on attempt ${attempt}`);
          }
      } catch (error) {
          lastError = error;
          console.error(`[NOTIFICATIONS] (Guard) ❌ Attempt ${attempt} failed:`, error);
        }

        // Wait before retry (exponential backoff: 2s, 4s, 8s)
        if (attempt < maxRetries) {
          const delay = Math.pow(2, attempt) * 1000;
          console.log(`[NOTIFICATIONS] (Guard) Waiting ${delay}ms before retry...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }

      console.error(`[NOTIFICATIONS] (Guard) ❌ All ${maxRetries} registration attempts failed`);
      if (lastError) {
        console.error('[NOTIFICATIONS] (Guard) Last error:', lastError);
      }
    };

    // Add a small delay to ensure auth state is fully settled
    const timeoutId = setTimeout(registerPushWithRetry, 2000);
    
    return () => clearTimeout(timeoutId);
  }, [user]); // Removed pushRegisteredThisSession dependency to allow re-registration on app restart
  const [subscriptionPlans, setSubscriptionPlans] = useState<SubscriptionPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [processingSubscription, setProcessingSubscription] = useState(false);
  const { showUpgradeModal, setShowUpgradeModal, isFreeUser, setIsFreeUser, refreshSubscriptionStatus } = useSubscription();

  // Effect to check for mandatory popups when subscription status changes
  // This runs after user logs in and when subscription status is updated
  useEffect(() => {
    const checkSubscriptionForPopups = async () => {
      // Only check if user is logged in, not a dietician, and not already showing a popup
      if (!user?.uid || isDietician) {
        return;
      }
      
      // Don't check if popups are already showing
      if (showMandatoryTrialPopup || showMandatoryPlanPopup) {
        return;
      }

      try {
        // Add small delay to avoid conflicts with login sequence
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const status = await getSubscriptionStatus(user.uid);
        await checkAndShowMandatoryPopups(status);
      } catch (error) {
        console.error('[Subscription Popup Check] Error:', error);
      }
    };

    // Only check if user is logged in and app is not in loading state
    if (user && !checkingAuth && !checkingProfile && !loading) {
      checkSubscriptionForPopups();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, isDietician, checkingAuth, checkingProfile, loading]);
  const [lastResetDate, setLastResetDate] = useState<string | null>(null);
  
  // App lock state
  const [isAppLocked, setIsAppLocked] = useState(false);
  const [amountDue, setAmountDue] = useState(0);
  const [showLockModal, setShowLockModal] = useState(false);

  // Daily reset mechanism
  const checkAndResetDailyData = async () => {
    if (!user?.uid) return;
    
    try {
      // Use consistent local date calculation
      const todayDate = new Date();
      const todayYear = todayDate.getFullYear();
      const todayMonth = String(todayDate.getMonth() + 1).padStart(2, '0');
      const todayDay = String(todayDate.getDate()).padStart(2, '0');
      const today = `${todayYear}-${todayMonth}-${todayDay}`;
      
      const storedDate = await AsyncStorage.getItem(`lastResetDate_${user.uid}`);
      
      console.log(`[Daily Reset] Checking reset: stored=${storedDate}, today=${today}`);
      
      if (storedDate !== today) {
        console.log('[Daily Reset] New day detected, resetting daily data');
        
        try {
          // Reset daily data by calling the backend with timeout  
          const resetPromise = resetDailyData(user.uid);
          
          // Add timeout to prevent hanging
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Daily reset timeout')), 15000)
          );
          
          await Promise.race([resetPromise, timeoutPromise]);
          
          // Store the new date
          await AsyncStorage.setItem(`lastResetDate_${user.uid}`, today);
          setLastResetDate(today);
          
          console.log(`[Daily Reset] Successfully reset daily data for ${today}`);
        } catch (resetError) {
          console.error('[Daily Reset] Failed to reset daily data:', resetError);
          // Still update the stored date to prevent continuous retry
          await AsyncStorage.setItem(`lastResetDate_${user.uid}`, today);
          setLastResetDate(today);
        }
      } else {
        console.log('[Daily Reset] No reset needed - same day');
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
        // Refresh the subscription context to update UI immediately
        refreshSubscriptionStatus();
        // App state updated successfully
        console.log('[Subscription] App state updated successfully');
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
      let localNotificationSubscription: any;
      let timeoutId: any;
    
    // Set a timeout to prevent infinite loading - reduced for iOS stability
    timeoutId = setTimeout(() => {
      console.log('Loading timeout reached, forcing app to continue');
      setLoading(false);
      setCheckingAuth(false);
      setCheckingProfile(false);
      isLoginInProgress = false; // Clear login flag
      (global as any).isLoginInProgress = false; // Clear global flag
    }, Platform.OS === 'ios' ? 20000 : 15000); // Longer timeout for iOS builds
    
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
        isLoginInProgress = false; // Clear login flag
        (global as any).isLoginInProgress = false; // Clear global flag
        if (timeoutId) clearTimeout(timeoutId);
      }
    };

      const initializeServices = async () => {
        try {
          
          // Set up listener for local scheduled notifications (subscription reminders)
          localNotificationSubscription = Notifications.addNotificationReceivedListener(async (notification) => {
            const data = notification.request.content.data;
            const title = notification.request.content.title || 'Notification';
            const body = notification.request.content.body || '';
            
            console.log('[Local Notification] Received:', { type: data?.type, title, body });
            
            if (data?.type === 'subscription_reminder') {
              // Show reminder notification
              setNotificationMessage(body);
              setShowNotification(true);
            }
          });
          
          // Set up simple notification handler
        try {
          console.log('[NOTIFICATIONS] Setting up simple notification handler');
          simpleNotificationHandler.initialize();
          console.log('[NOTIFICATIONS] ✅ Simple notification handler setup successful');
        } catch (error) {
          console.warn('[NOTIFICATIONS] Simple notification handler setup failed:', error);
        }
        
        // Set up diet notification listener with platform-specific handling
        try {
          console.log('[NOTIFICATIONS] Setting up diet notification listener on platform:', Platform.OS);
          dietNotificationSubscription = setupDietNotificationListener();
          console.log('[NOTIFICATIONS] ✅ Diet notification listener setup successful');
        } catch (error) {
          console.warn('[NOTIFICATIONS] Diet notification listener setup failed:', error);
        }
        
        
        // Set up auth state listener
        unsubscribe = auth.onAuthStateChanged(async (firebaseUser) => {
          try {
            console.log('[AuthStateChanged] firebaseUser:', firebaseUser);
            
            if (firebaseUser) {
              setUser(firebaseUser);
              setCheckingProfile(true);
              isLoginInProgress = true; // Set login flag
              (global as any).isLoginInProgress = true; // Set global flag
              setPushRegisteredThisSession(false); // allow push registration once per session for this user
              
            // ✅ FIX: Register for push notifications AFTER user login with stable user ID
            try {
                // CRITICAL FIX: Wait for Firebase auth to fully propagate to Firestore
                // This resolves the timing issue where Firestore security rules fail
                // because request.auth is not yet synchronized with the new login
                console.log('[NOTIFICATIONS] Waiting 3s for auth token to propagate to Firestore...');
                await new Promise(resolve => setTimeout(resolve, 3000));
                console.log('[NOTIFICATIONS] Auth propagation delay complete, proceeding with registration');
                
                await registerPushWithLogging(firebaseUser.uid, 'auth_state_change');
            } catch (error) {
                console.error('[NOTIFICATIONS] ❌ Push notification registration failed:', error);
            }
              
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

                      caloriesBurnedGoal: 500
                    });
                    console.log('[Dietician Profile] Profile created successfully');
                  } catch (error) {
                    console.error('Error handling dietician profile:', error);
                  }
                }
                
                        // Set up real-time notification listener for non-dietician users
        if (!isDieticianAccount) {
          try {
            console.log('[NOTIFICATIONS] Setting up Firestore notification listener for user:', firebaseUser.uid);
            notificationUnsubscribe = firestore
              .collection('notifications')
              .where('userId', '==', firebaseUser.uid)
              .where('read', '==', false)
              .onSnapshot(snapshot => {
                console.log('[NOTIFICATIONS] Firestore notification snapshot received:', snapshot.docs.length, 'unread notifications');
                snapshot.docChanges().forEach(change => {
                  if (change.type === 'added') {
                    const notification = change.doc.data();
                    console.log('[NOTIFICATIONS] New notification received:', notification);
                    
                    // Mark notification as read immediately to prevent re-triggering
                    firestore.collection('notifications').doc(change.doc.id).update({
                      read: true
                    });
                    
                    // Handle different notification types with specific popups
                    const notificationType = notification.type;
                    const notificationBody = notification.body || notification.message || '';
                    
                    if (notificationType === 'subscription_renewed') {
                      // Show custom renewal popup
                      setRenewalMessage(notificationBody);
                      setShowRenewalPopup(true);
                      // Refresh subscription status
                      if (firebaseUser?.uid) {
                        getSubscriptionStatus(firebaseUser.uid).then(status => {
                          setSubscriptionStatus(status);
                          refreshSubscriptionStatus();
                        });
                      }
                    } else if (notificationType === 'plan_switched') {
                      // Show custom plan switch popup
                      setPlanSwitchMessage(notificationBody);
                      setShowPlanSwitchPopup(true);
                      // Refresh subscription status
                      if (firebaseUser?.uid) {
                        getSubscriptionStatus(firebaseUser.uid).then(status => {
                          setSubscriptionStatus(status);
                          refreshSubscriptionStatus();
                        });
                      }
                      // Don't process any other notifications after plan switch
                      return;
                    } else if (notificationType === 'subscription_expired' || notificationType === 'trial_expired') {
                      // Check if this is happening right after a plan switch - if so, skip the generic popup
                      // The plan switch popup already handled the notification
                      if (firebaseUser?.uid) {
                        getSubscriptionStatus(firebaseUser.uid).then(status => {
                          // Only show expiry popup if there's no pending plan switch and subscription is actually expired
                          // If a plan switch just happened, the plan_switched notification already handled it
                          const hasPendingSwitch = status.pendingPlanSwitch && status.pendingPlanSwitch.newPlanId;
                          const isActuallyExpired = !status.isSubscriptionActive && !status.isFreeUser;
                          
                          if (!hasPendingSwitch && isActuallyExpired) {
                            // Show custom expiry popup with plan selection
                            setNotificationMessage(notificationBody);
                            setShowNotification(true);
                            
                            if (status.requiresPlanSelection) {
                              // Fetch plans and show mandatory popup
                              getSubscriptionPlans().then(plans => {
                                setAvailablePlans(plans);
                                setShowMandatoryPlanPopup(true);
                              });
                            }
                          }
                          refreshSubscriptionStatus();
                        });
                      }
                    } else if (notificationType === 'payment_added') {
                      // Don't show payment_added notifications separately - they're included in subscription_expired
                      // Just refresh subscription status
                      if (firebaseUser?.uid) {
                        refreshSubscriptionStatus();
                      }
                    } else if (notificationType === 'payment_reminder' || notificationType === 'trial_reminder') {
                      // Show reminder notifications
                      setNotificationMessage(notificationBody);
                      setShowNotification(true);
                    } else {
                      // Show default notification popup for other types
                      setNotificationMessage(notificationBody);
                      setShowNotification(true);
                    }
                    console.log('[NOTIFICATIONS] ✅ Notification displayed to user');
                  }
                });
              }, error => {
                console.error('[NOTIFICATIONS] Error listening to Firestore notifications:', error);
              });
            console.log('[NOTIFICATIONS] ✅ Firestore notification listener setup successful');
          } catch (error) {
            console.warn('[NOTIFICATIONS] Failed to set up Firestore notification listener:', error);
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
                    
                    // Add EAS build-specific error handling
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
                    } catch (profileError: any) {
                      console.log('[Profile Check] Error checking profile:', profileError);
                      
                      // EAS build-specific fallback with iOS handling
                      if (!__DEV__) {
                        console.log('[EAS Build] Using fallback profile handling');
                        // For EAS builds, assume user needs to complete quiz
                        setHasCompletedQuiz(false);
                        await AsyncStorage.setItem('hasCompletedQuiz', 'false');
                        
                        // iOS-specific: Skip additional API calls to prevent crashes
                        if (Platform.OS === 'ios') {
                          console.log('[iOS EAS Build] Minimal initialization to prevent crashes');
                        setHasActiveSubscription(false);
                        setIsFreeUser(true);
                          setCheckingProfile(false);
                          isLoginInProgress = false;
                          (global as any).isLoginInProgress = false;
                        return; // Exit early to prevent further API calls
                        }
                        
                        // Android EAS: Continue with normal flow
                        setHasActiveSubscription(false);
                        setIsFreeUser(true);
                      } else {
                        // For Expo Go, use normal error handling
                        setHasCompletedQuiz(false);
                        await AsyncStorage.setItem('hasCompletedQuiz', 'false');
                      }
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
                      
                      // Log queue status before making requests
                      const queueStatus = getQueueStatus();
                      console.log('[Queue Status] Before subscription check:', queueStatus);
                      
                      // Add EAS build-specific timeout handling
                      const subscriptionPromise = getSubscriptionStatus(firebaseUser.uid);
                      const timeoutPromise = new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Subscription check timeout')), __DEV__ ? 15000 : 30000)
                      );
                      
                      const subscriptionStatus = await Promise.race([subscriptionPromise, timeoutPromise]) as any;
                      setSubscriptionStatus(subscriptionStatus);
                    
                    // Check if user is on free plan or has active subscription
                    // Only update isFreeUser if we have valid subscription status data
                    if (subscriptionStatus && typeof subscriptionStatus === 'object') {
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
                    } else {
                      console.log('[Subscription Check] Invalid subscription status, keeping current isFreeUser state');
                    }
                      
                      // Check for mandatory popups (trial activation or plan selection)
                      // Only check if user is not a dietician
                      if (!isDieticianAccount) {
                        await checkAndShowMandatoryPopups(subscriptionStatus);
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
                        console.log('[LOGIN SEQUENCE] Starting app lock status check...');
                        await checkAppLockStatus();
                        console.log('[LOGIN SEQUENCE] ✅ App lock status check completed successfully');
                      } catch (lockError) {
                        console.log('[LOGIN SEQUENCE] ❌ App lock status check failed:', lockError);
                      }
                      
                      // Log final queue status
                      const finalQueueStatus = getQueueStatus();
                      console.log('[LOGIN SEQUENCE] Final queue status:', finalQueueStatus);
                      
                      // Critical: Log completion of login sequence
                      console.log('[LOGIN SEQUENCE] 🎉 LOGIN SEQUENCE COMPLETED SUCCESSFULLY');
                      
                      // Log to backend for EAS builds
                      try {
                        await logFrontendEvent(firebaseUser.uid, 'LOGIN_SEQUENCE_COMPLETED', {
                          isDietician: isDieticianAccount,
                          hasProfile: !!profile,
                          subscriptionActive: hasActiveSubscription
                        });
                      } catch (logError) {
                        console.warn('Failed to log login completion:', logError);
                      }
                      
                      console.log('[LOGIN SEQUENCE] Setting completion flags...');
                      setCheckingProfile(false);
                      isLoginInProgress = false;
                      (global as any).isLoginInProgress = false;
                      console.log('[LOGIN SEQUENCE] ✅ All login flags cleared, app should now navigate to MainTabs');
                      
                      // Log navigation attempt
                      try {
                        await logFrontendEvent(firebaseUser.uid, 'NAVIGATION_TO_MAINTABS', {
                          checkingProfile: false,
                          isLoginInProgress: false
                        });
                      } catch (logError) {
                        console.warn('Failed to log navigation attempt:', logError);
                      }
                    } catch (error) {
                      console.log('[Subscription Check] Error checking subscription status:', error);
                      
                      // EAS build-specific fallback with iOS optimization
                      if (!__DEV__) {
                        console.log('[EAS Build] Using fallback subscription handling');
                        setHasActiveSubscription(false);
                        setIsFreeUser(true);
                        
                        // iOS-specific: Complete login early to prevent crashes
                        if (Platform.OS === 'ios') {
                          console.log('[iOS EAS Build] Completing login early due to subscription error');
                          setCheckingProfile(false);
                          isLoginInProgress = false;
                          (global as any).isLoginInProgress = false;
                        }
                      } else {
                        // If we can't check subscription, assume they are free users
                        setHasActiveSubscription(false);
                        setIsFreeUser(true);
                      }
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
              console.log('[LOGIN SEQUENCE] 🏁 Finalizing login sequence...');
              setCheckingProfile(false);
              isLoginInProgress = false; // Clear login flag
              (global as any).isLoginInProgress = false; // Clear global flag
              console.log('[LOGIN SEQUENCE] ✅ Login sequence finalized, user should see main app');
            } else {
              setUser(null);
              setHasCompletedQuiz(false);
              setIsDietician(false);
              setHasActiveSubscription(null);
              isLoginInProgress = false; // Clear login flag
              (global as any).isLoginInProgress = false; // Clear global flag
              
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
        if (localNotificationSubscription) localNotificationSubscription.remove();
        if (timeoutId) clearTimeout(timeoutId);
    };
  }, []); // Removed forceReload dependency to prevent unnecessary re-renders

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





  console.log('[APP RENDER] 🎨 App rendering with state:', {
    user: !!user,
    hasCompletedQuiz,
    isDietician,
    isFreeUser,
    checkingAuth,
    checkingProfile,
    loading
  });

  // Function to check and show mandatory popups based on subscription status
  const checkAndShowMandatoryPopups = async (subscriptionStatus: any) => {
    if (!user?.uid || isDietician) return;
    
    setSubscriptionStatus(subscriptionStatus);
    
    // Check if subscription was cancelled or requires plan selection
    const isCancelled = subscriptionStatus.subscriptionStatus === "cancelled";
    const needsPlanSelection = subscriptionStatus.requiresPlanSelection || isCancelled;
    
    // Check if user is on free plan (not paid plan) and hasn't used free trial
    const isOnFreePlan = subscriptionStatus.isFreeUser || !subscriptionStatus.isSubscriptionActive || 
                        subscriptionStatus.subscriptionPlan === "free" || 
                        !subscriptionStatus.subscriptionPlan;
    
    // Priority 1: If cancelled or requires plan selection, show plan selection popup
    if (needsPlanSelection) {
      console.log('[Mandatory Popup] User needs to select a plan (cancelled or expired), showing plan selection popup');
      try {
        const plans = await getSubscriptionPlans();
        setAvailablePlans(plans);
        setShowMandatoryPlanPopup(true);
      } catch (planError) {
        console.error('[Mandatory Popup] Failed to fetch plans:', planError);
        setShowMandatoryPlanPopup(true);
      }
    }
    // Priority 2: If on free plan and hasn't used trial, show trial activation popup
    else if (isOnFreePlan && !subscriptionStatus.freeTrialUsed) {
      console.log('[Mandatory Popup] User is on free plan and has not used free trial, showing trial activation popup');
      setShowMandatoryTrialPopup(true);
    }
  };

  // Function to refresh subscription status and check for mandatory popups
  // This can be called after cancellation or other subscription changes
  const refreshSubscriptionAndCheckPopups = async () => {
    if (!user?.uid || isDietician) return;
    
    try {
      const status = await getSubscriptionStatus(user.uid);
      await checkAndShowMandatoryPopups(status);
      
      // Update subscription state - only if status is valid
      if (status && typeof status === 'object') {
        if (status.isFreeUser || !status.isSubscriptionActive) {
          setHasActiveSubscription(false);
          setIsFreeUser(true);
        } else {
          setHasActiveSubscription(true);
          setIsFreeUser(false);
        }
      }
    } catch (error) {
      console.error('[Refresh Subscription] Error:', error);
    }
  };

  // Schedule subscription reminder notifications
  const scheduleSubscriptionReminders = async (endDate: string, planName: string, isTrial: boolean = false, planAmount?: number) => {
    try {
      const endDateTime = new Date(endDate);
      const now = new Date();
      
      // Calculate reminder times (30 mins, 15 mins, 5 mins before end)
      const reminder30min = new Date(endDateTime.getTime() - 30 * 60 * 1000);
      const reminder15min = new Date(endDateTime.getTime() - 15 * 60 * 1000);
      const reminder5min = new Date(endDateTime.getTime() - 5 * 60 * 1000);
      
      const reminders = [
        { time: reminder30min, minutes: 30 },
        { time: reminder15min, minutes: 15 },
        { time: reminder5min, minutes: 5 }
      ];
      
      // Format amount for display
      const amountText = planAmount ? `₹${planAmount.toLocaleString()}` : 'the plan amount';
      
      for (const reminder of reminders) {
        // Only schedule if the reminder time is in the future
        if (reminder.time > now) {
          const secondsUntilTrigger = Math.floor((reminder.time.getTime() - now.getTime()) / 1000);
          
          if (secondsUntilTrigger > 0) {
            let message = '';
            if (isTrial) {
              message = `Your free trial ends in ${reminder.minutes} minutes! Select a plan now to keep enjoying premium features like personalized diets, AI chatbot, and custom notifications.`;
            } else {
              if (reminder.minutes === 30) {
                message = `Your ${planName} ends in ${reminder.minutes} minutes. Payment of ${amountText} will be added to your total. Your premium features will continue if auto-renewal is enabled.`;
              } else if (reminder.minutes === 15) {
                message = `Your ${planName} ends in ${reminder.minutes} minutes. Payment of ${amountText} will be added to your total. Ensure auto-renewal is enabled to continue seamlessly.`;
              } else if (reminder.minutes === 5) {
                message = `Your ${planName} ends in ${reminder.minutes} minutes! Payment of ${amountText} will be added to your total. If auto-renewal is off, you'll need to select a new plan to continue.`;
              } else {
                message = `Your ${planName} ends in ${reminder.minutes} minutes. Payment of ${amountText} will be added to your total amount due.`;
              }
            }
            
            await Notifications.scheduleNotificationAsync({
              content: {
                title: isTrial ? 'Trial Ending Soon' : 'Plan Ending Soon',
                body: message,
                sound: 'default',
                data: {
                  type: 'subscription_reminder',
                  minutesRemaining: reminder.minutes,
                  isTrial: isTrial,
                  planName: planName
                }
              },
              trigger: {
                type: 'timeInterval',
                seconds: secondsUntilTrigger,
                repeats: false
              } as any
            });
            
            console.log(`[Subscription Reminders] Scheduled ${reminder.minutes}min reminder for ${reminder.time.toISOString()}`);
          }
        }
      }
    } catch (error) {
      console.error('[Subscription Reminders] Error scheduling reminders:', error);
      // Don't fail trial/plan activation if reminder scheduling fails
    }
  };

  // Handler for trial activation
  const handleActivateTrial = async () => {
    if (!user?.uid) return;
    
    try {
      setActivatingTrial(true);
      const result = await activateFreeTrial(user.uid);
      
      if (result.success) {
        console.log('[Trial Activation] Success:', result.message);
        setShowMandatoryTrialPopup(false);
        // Refresh subscription status
        const newStatus = await getSubscriptionStatus(user.uid);
        setSubscriptionStatus(newStatus);
        setHasActiveSubscription(true);
        setIsFreeUser(false);
        refreshSubscriptionStatus();
        
        // Schedule reminder notifications if trial end date is available
        if (result.trial?.endDate) {
          await scheduleSubscriptionReminders(result.trial.endDate, 'Free Trial', true);
        }
        
        // Show custom success popup instead of Alert
        setTrialSuccessMessage(result.message);
        setShowTrialSuccessPopup(true);
      }
    } catch (error: any) {
      console.error('[Trial Activation] Error:', error);
      Alert.alert('Error', error.message || 'Failed to activate free trial');
    } finally {
      setActivatingTrial(false);
    }
  };

  // Handler for plan selection
  const handleSelectPlan = (planId: string) => {
    setSelectedPlanId(planId);
  };

  const handleConfirmPlanSelection = async () => {
    if (!user?.uid || !selectedPlanId) return;
    
    try {
      setSelectingPlan(true);
      const result = await selectSubscription(user.uid, selectedPlanId);
      
      if (result.success) {
        console.log('[Plan Selection] Success:', result.message);
        setShowMandatoryPlanPopup(false);
        setSelectedPlanId(null);
        // Refresh subscription status
        const newStatus = await getSubscriptionStatus(user.uid);
        setSubscriptionStatus(newStatus);
        setHasActiveSubscription(true);
        setIsFreeUser(false);
        refreshSubscriptionStatus();
        
        // Schedule reminder notifications if subscription end date is available
        // Check both result.subscription.endDate and newStatus.subscriptionEndDate
        const endDate = result.subscription?.endDate || newStatus?.subscriptionEndDate;
        if (endDate) {
          const planName = selectedPlanId === '1month' ? '1 Month Plan' :
                          selectedPlanId === '2months' ? '2 Months Plan' :
                          selectedPlanId === '3months' ? '3 Months Plan' :
                          selectedPlanId === '6months' ? '6 Months Plan' : 'Plan';
          const planAmount = result.subscription?.amountPaid || newStatus?.currentSubscriptionAmount || 0;
          await scheduleSubscriptionReminders(endDate, planName, false, planAmount);
        }
        
        Alert.alert('Success', result.message);
      }
    } catch (error: any) {
      console.error('[Plan Selection] Error:', error);
      Alert.alert('Error', error.message || 'Failed to select plan');
    } finally {
      setSelectingPlan(false);
    }
  };

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
                children={() => {
                  console.log('[APP NAVIGATION] 🧭 Attempting to render MainTabs...');
                  
                  // Log navigation attempt to backend for EAS builds
                  const logNavigation = async () => {
                    try {
                      if (user && !__DEV__) {
                        await logFrontendEvent(user.uid, 'APP_NAVIGATION_ATTEMPT', {
                          isDietician,
                          isFreeUser,
                          hasCompletedQuiz,
                          checkingProfile,
                          loading,
                          platform: Platform.OS
                        });
                      }
                    } catch (logError) {
                      console.warn('Failed to log navigation attempt:', logError);
                    }
                  };
                  logNavigation();
                  
                  try {
                    // Critical checkpoint before MainTabs rendering
                    console.log('[APP NAVIGATION] ✅ About to render MainTabs with:', { isDietician, isFreeUser });
                    const result = <MainTabs isDietician={isDietician} isFreeUser={isFreeUser} />;
                    console.log('[APP NAVIGATION] 🎉 MainTabs rendered successfully');
                    return result;
                  } catch (error) {
                    console.error('[APP NAVIGATION] ❌ CRITICAL ERROR rendering MainTabs:', error);
                    console.error('[APP NAVIGATION] Error stack:', error instanceof Error ? error.stack : undefined);
                    console.error('[APP NAVIGATION] Error name:', error instanceof Error ? error.name : 'Unknown');
                    console.error('[APP NAVIGATION] Error message:', error instanceof Error ? error.message : String(error));
                    
                    // This is likely where the iOS crash is happening!
                    console.error('[APP NAVIGATION] 🚨 iOS CRASH DETECTED - This is likely the crash point!');
                    
                    // Log critical error to backend for EAS builds
                    const logCriticalError = async () => {
                      try {
                        if (user && !__DEV__) {
                          await logFrontendEvent(user.uid, 'CRITICAL_NAVIGATION_ERROR', {
                            error: error instanceof Error ? error.message : String(error),
                            stack: error instanceof Error ? error.stack : undefined,
                            name: error instanceof Error ? error.name : 'Unknown',
                            isDietician,
                            isFreeUser,
                            hasCompletedQuiz,
                            checkingProfile,
                            loading,
                            platform: Platform.OS,
                            crashLocation: 'APP_NAVIGATION_MAINTABS_RENDER'
                          });
                        }
                      } catch (logErr) {
                        console.warn('Failed to log critical error:', logErr);
                      }
                    };
                    logCriticalError();
                    
                    // iOS-specific error recovery
                    if (Platform.OS === 'ios') {
                      console.log('[APP NAVIGATION] [iOS] Attempting MainTabs recovery');
                      // Clear any potentially problematic state
                      clearProfileCache();
                      
                      // Log additional iOS debugging info
                      console.log('[APP NAVIGATION] [iOS] Current state at crash:', {
                        user: !!user,
                        hasCompletedQuiz,
                        isDietician,
                        isFreeUser,
                        isLoginInProgress,
                        checkingProfile
                      });
                      
                      // Return a simplified view for iOS
                      return (
                        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.background }}>
                          <ActivityIndicator size="large" color={COLORS.primary} />
                          <Text style={{ color: COLORS.text, fontSize: 16, marginTop: 10 }}>Initializing app...</Text>
                          <Text style={{ color: COLORS.placeholder, fontSize: 12, marginTop: 5 }}>iOS Error Recovery Mode</Text>
                        </View>
                      );
                    }
                    
                    return (
                      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.background }}>
                        <Text style={{ color: COLORS.text, fontSize: 16 }}>Loading app...</Text>
                      </View>
                    );
                  }
                }}
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

      {/* Mandatory Trial Activation Popup */}
      <MandatoryTrialActivationPopup
        visible={showMandatoryTrialPopup}
        onActivate={handleActivateTrial}
        activating={activatingTrial}
      />

      {/* Mandatory Plan Selection Popup */}
      <MandatoryPlanSelectionPopup
        visible={showMandatoryPlanPopup}
        plans={availablePlans}
        selectedPlan={selectedPlanId}
        onSelectPlan={handleSelectPlan}
        onConfirm={handleConfirmPlanSelection}
        confirming={selectingPlan}
        message={subscriptionStatus?.subscriptionStatus === 'trial' || subscriptionStatus?.isTrialActive === false
          ? "Select a plan below to continue enjoying personalized diet plans, AI chatbot support, and custom notifications."
          : "Select a plan to continue your fitness journey"}
      />

      {/* Trial Success Popup */}
      <Modal
        visible={showTrialSuccessPopup}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowTrialSuccessPopup(false)}
      >
        <View style={styles.notificationOverlay}>
          <View style={styles.notificationPopup}>
            <Text style={styles.notificationTitle}>🎉 Free Trial Activated!</Text>
            <Text style={styles.notificationMessage}>{trialSuccessMessage}</Text>
            <TouchableOpacity 
              style={styles.notificationButton} 
              onPress={() => setShowTrialSuccessPopup(false)}
            >
              <Text style={styles.notificationButtonText}>Got it!</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Subscription Renewal Popup */}
      <Modal
        visible={showRenewalPopup}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowRenewalPopup(false)}
      >
        <View style={styles.notificationOverlay}>
          <View style={styles.notificationPopup}>
            <Text style={styles.notificationTitle}>✅ Subscription Renewed!</Text>
            <Text style={styles.notificationMessage}>{renewalMessage}</Text>
            <TouchableOpacity 
              style={styles.notificationButton} 
              onPress={() => setShowRenewalPopup(false)}
            >
              <Text style={styles.notificationButtonText}>Got it!</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Plan Switch Popup */}
      <Modal
        visible={showPlanSwitchPopup}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowPlanSwitchPopup(false)}
      >
        <View style={styles.notificationOverlay}>
          <View style={styles.notificationPopup}>
            <Text style={styles.notificationTitle}>🔄 Plan Switched!</Text>
            <Text style={styles.notificationMessage}>{planSwitchMessage}</Text>
            <TouchableOpacity 
              style={styles.notificationButton} 
              onPress={() => setShowPlanSwitchPopup(false)}
            >
              <Text style={styles.notificationButtonText}>Got it!</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Subscription Renewal Popup */}
      <Modal
        visible={showRenewalPopup}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowRenewalPopup(false)}
      >
        <View style={styles.notificationOverlay}>
          <View style={styles.notificationPopup}>
            <Text style={styles.notificationTitle}>✅ Subscription Renewed!</Text>
            <Text style={styles.notificationMessage}>{renewalMessage}</Text>
            <TouchableOpacity 
              style={styles.notificationButton} 
              onPress={() => setShowRenewalPopup(false)}
            >
              <Text style={styles.notificationButtonText}>Got it!</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Plan Switch Popup */}
      <Modal
        visible={showPlanSwitchPopup}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowPlanSwitchPopup(false)}
      >
        <View style={styles.notificationOverlay}>
          <View style={styles.notificationPopup}>
            <Text style={styles.notificationTitle}>🔄 Plan Switched!</Text>
            <Text style={styles.notificationMessage}>{planSwitchMessage}</Text>
            <TouchableOpacity 
              style={styles.notificationButton} 
              onPress={() => setShowPlanSwitchPopup(false)}
            >
              <Text style={styles.notificationButtonText}>Got it!</Text>
            </TouchableOpacity>
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
    <SafeAreaProvider>
      <SubscriptionProvider>
        <AppContent />
      </SubscriptionProvider>
    </SafeAreaProvider>
  );
}