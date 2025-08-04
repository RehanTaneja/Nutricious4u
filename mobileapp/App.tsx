import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, Settings, MessageCircle, BookOpen } from 'lucide-react-native';
import firebase, { auth, firestore, registerForPushNotificationsAsync, setupDietNotificationListener } from './services/firebase';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppContext } from './contexts/AppContext';
import { ActivityIndicator, View, Alert, Modal, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { getUserProfile } from './services/api';
import { ChatbotScreen } from './ChatbotScreen';

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
  UploadDietScreen // <-- import the new screen
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

  useEffect(() => {
    let unsubscribe: any;
    let notificationUnsubscribe: any;
    let dietNotificationSubscription: any;
    
    const checkAuthAndProfile = async () => {
      try {
        setCheckingAuth(true);
        setError(null);
        
        // Register for push notifications
        await registerForPushNotificationsAsync();
        
        // Set up diet notification listener
        dietNotificationSubscription = setupDietNotificationListener();
        
        unsubscribe = auth.onAuthStateChanged(async (firebaseUser) => {
          try {
          console.log('[AuthStateChanged] firebaseUser:', firebaseUser);
          if (firebaseUser) {
            setUser(firebaseUser);
            setCheckingProfile(true);
            try {
              // Always fetch Firestore user doc
              const userDocRef = firestore.collection('users').doc(firebaseUser.uid);
              let userDoc = await userDocRef.get();
              let userData = userDoc.data();
              console.log('[Dietician Debug] userDoc.exists:', userDoc.exists, 'userData:', userData);
              // If not present, create for dietician
              if (!userDoc.exists && firebaseUser.email === 'nutricious4u@gmail.com') {
                await userDocRef.set({
                  isDietician: true,
                  firstName: 'Ekta',
                  lastName: 'Taneja',
                  email: firebaseUser.email
                });
                userDoc = await userDocRef.get();
                userData = userDoc.data();
                setForceReload(x => x + 1); // force re-render
                console.log('[Dietician Debug] Created dietician userDoc:', userData);
              }
              const isDieticianAccount = !!userData?.isDietician;
              setIsDietician(isDieticianAccount);
              // Debug log
              console.log('[Dietician Check]', {
                email: firebaseUser.email,
                isDieticianAccount,
                userData,
                hasCompletedQuiz,
                checkingAuth,
                checkingProfile
              });
              
              // Set up real-time notification listener for non-dietician users
              if (!isDieticianAccount) {
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
              }
              
              // Dietician skips quiz
              if (isDieticianAccount) {
                setHasCompletedQuiz(true);
                console.log('[Dietician Debug] Skipping quiz for dietician');
              } else {
                const profile = await getUserProfile(firebaseUser.uid);
                const isQuizComplete = !!(profile && profile.currentWeight && profile.height);
                setHasCompletedQuiz(isQuizComplete);
                await AsyncStorage.setItem('hasCompletedQuiz', isQuizComplete ? 'true' : 'false');
                console.log('[Dietician Debug] User quiz status:', isQuizComplete);
              }
            } catch (e) {
              setHasCompletedQuiz(false);
              await AsyncStorage.setItem('hasCompletedQuiz', 'false');
              console.log('[Dietician Debug] Error in checkAuthAndProfile:', e);
            }
            setCheckingProfile(false);
          } else {
            setUser(null);
            setHasCompletedQuiz(false);
            setIsDietician(false);
            // Only check for saved credentials and auto-login on app start, not on every logout
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
            }
          }
          setCheckingAuth(false);
        } catch (innerError) {
          console.error('Error in auth state change:', innerError);
          setCheckingAuth(false);
          setCheckingProfile(false);
        }
      });
      } catch (error) {
        console.error('Error in checkAuthAndProfile:', error);
        setCheckingAuth(false);
        setCheckingProfile(false);
      }
    };
    
    checkAuthAndProfile();
    
    return () => {
      if (unsubscribe) unsubscribe();
      if (notificationUnsubscribe) notificationUnsubscribe();
      if (dietNotificationSubscription) dietNotificationSubscription.remove();
    };
  }, [forceReload]);

  if (checkingAuth || checkingProfile) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.background }}>
        <ActivityIndicator size="large" color={COLORS.primary} />
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