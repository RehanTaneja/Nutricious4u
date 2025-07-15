import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, Settings, MessageCircle } from 'lucide-react-native';
import firebase, { auth } from './services/firebase';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppContext } from './contexts/AppContext';
import { ActivityIndicator, View } from 'react-native';
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
  RoutineScreen // <-- import the new screen
} from './screens';

type User = firebase.User;

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// The new Tab Navigator with only Dashboard and Settings
const MainTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      headerShown: false, // The Stack Navigator will handle the header
      tabBarIcon: ({ color, size }) => {
        if (route.name === 'Dashboard') {
          return <Home color={color} size={size} />;
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
    <Tab.Screen name="Dashboard" component={DashboardScreen} />
    <Tab.Screen name="Chatbot" component={ChatbotScreen} />
    <Tab.Screen name="Settings" component={SettingsScreen} />
  </Tab.Navigator>
);

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasCompletedQuiz, setHasCompletedQuiz] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [checkingProfile, setCheckingProfile] = useState(false);

  useEffect(() => {
    let unsubscribe: any;
    const checkAuthAndProfile = async () => {
      setCheckingAuth(true);
      unsubscribe = auth.onAuthStateChanged(async (firebaseUser) => {
        if (firebaseUser) {
          setUser(firebaseUser);
          setCheckingProfile(true);
          try {
            const profile = await getUserProfile(firebaseUser.uid);
            const isQuizComplete = !!(profile && profile.currentWeight && profile.height);
            setHasCompletedQuiz(isQuizComplete);
            await AsyncStorage.setItem('hasCompletedQuiz', isQuizComplete ? 'true' : 'false');
          } catch (e) {
            setHasCompletedQuiz(false);
            await AsyncStorage.setItem('hasCompletedQuiz', 'false');
          }
          setCheckingProfile(false);
        } else {
          setUser(null);
          setHasCompletedQuiz(false);
          // Only check for saved credentials and auto-login on app start, not on every logout
          const savedEmail = await AsyncStorage.getItem('savedEmail');
          const savedPassword = await AsyncStorage.getItem('savedPassword');
          if (savedEmail && savedPassword) {
            try {
              await auth.signInWithEmailAndPassword(savedEmail, savedPassword);
              return;
            } catch (e) {
              // Auto-login failed, proceed to show login screen.
            }
          }
        }
        setCheckingAuth(false);
      });
    };
    checkAuthAndProfile();
    return () => { if (unsubscribe) unsubscribe(); };
  }, []);

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
          ) : !hasCompletedQuiz ? (
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
                children={MainTabs}
                options={{ headerShown: false }}
              />
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
    </AppContext.Provider>
  );
} 