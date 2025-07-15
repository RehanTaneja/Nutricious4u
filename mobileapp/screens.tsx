import React, { useState, useEffect, useRef, useContext } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TextInput, 
  Alert, 
  TouchableOpacity,
  SafeAreaView,
  KeyboardTypeOptions,
  FlatList,
  ActivityIndicator,
  StyleProp,
  ViewStyle,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Animated,
  Easing,
  TouchableWithoutFeedback,
  Keyboard,
  Modal,
  Button,
} from 'react-native';
import { auth } from './services/firebase';
import { Home, BookOpen, Dumbbell, Settings, Camera, Flame, Search, MessageCircle, Send, Eye, EyeOff, Pencil, Trash2 } from 'lucide-react-native';
import { searchFood, logFood, FoodItem, getLogSummary, LogSummaryResponse, createUserProfile, getUserProfile, updateUserProfile, UserProfile, API_URL, logWorkout, listRoutines, createRoutine, updateRoutine, deleteRoutine, logRoutine, Routine, RoutineItem, RoutineCreateRequest, RoutineUpdateRequest } from './services/api';
import { useIsFocused } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Svg, Circle, Text as SvgText, Path } from 'react-native-svg';
import { Picker } from '@react-native-picker/picker';
import { AppContext } from './contexts/AppContext';
import ConfettiCannon from 'react-native-confetti-cannon';
import { EmailAuthProvider } from 'firebase/auth';
import { KeyboardAwareScrollView } from 'react-native-keyboard-aware-scroll-view';
import firebase from './services/firebase';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import DateTimePicker from '@react-native-community/datetimepicker';
import * as Notifications from 'expo-notifications';
import { Pedometer } from 'expo-sensors';
import { LinearGradient } from 'expo-linear-gradient';
import { getWorkoutLogSummary, WorkoutLogSummaryResponse } from './services/api';

// Add activity level options and calculation utility at the top
const ACTIVITY_LEVELS: { label: string; value: string; multiplier: number }[] = [
  { label: 'Sedentary', value: 'sedentary', multiplier: 1.2 },
  { label: 'Light', value: 'light', multiplier: 1.375 },
  { label: 'Moderate', value: 'moderate', multiplier: 1.55 },
  { label: 'Very Active', value: 'very active', multiplier: 1.725 },
  { label: 'Extra Active', value: 'extra active', multiplier: 1.9 },
];

function calculateTargets({ weight, height, age, gender, activityLevel }:{ weight?: number, height?: number, age?: number, gender?: string, activityLevel?: string }) {
  if (!weight || !height || !age || !gender || !activityLevel) return { calories: 0, protein: 0, fat: 0 };
  const multiplier = ACTIVITY_LEVELS.find(l => l.value === activityLevel)?.multiplier || 1.2;
  let bmr = 0;
  if (gender === 'male') {
    bmr = 10 * weight + 6.25 * height - 5 * age + 5;
  } else {
    bmr = 10 * weight + 6.25 * height - 5 * age - 161;
  }
  const calories = Math.round(bmr * multiplier);
  const protein = Math.round(weight * 1.6); // 1.6g per kg
  const fat = Math.round((calories * 0.25) / 9); // 25% calories from fat
  return { calories, protein, fat };
}

// Add at the top of the file, after COLORS:
const EXERCISE_CALORIES_PER_MIN: { [key: string]: number } = {
  'Running': 10,
  'Walking': 4,
  'Cycling': 8,
  'Swimming': 9,
  'Push-ups': 7,
  'Squats': 6,
  'Yoga': 3,
  'HIIT': 12,
  'Dancing': 7,
  'Weight Lifting': 5,
};

// Add after EXERCISE_CALORIES_PER_MIN:
const WGER_CATEGORY_NAMES: { [key: number]: string } = {
  10: 'Abs',
  8: 'Arms',
  12: 'Back',
  14: 'Calves',
  15: 'Cardio',
  11: 'Chest',
  9: 'Legs',
  13: 'Shoulders',
};

// --- Color Palette ---
export const COLORS = {
  background: '#F0FFF4', // A very light, soft green
  primary: '#6EE7B7',     // A vibrant, friendly mint green
  primaryDark: '#34D399', // A darker shade for presses
  white: '#FFFFFF',
  text: '#27272A',       // A dark, modern text color
  placeholder: '#A1A1AA',
  error: '#EF4444',
  energy: '#FF6B6B',      // Vibrant coral for calories
  protein: '#4ECDC4',     // Soft teal for protein
  fat: '#FFD93D',        // Bright yellow for fat
  logFood: '#6C5CE7',    // Soft purple
  scanFood: '#00B894',   // Fresh green
  logWorkout: '#FF7675', // Soft red
  streakRed: '#FFB3B3', // very light red
  streakActive: '#FFA500', // bright orange
  streakInactive: '#A1A1AA', // gray
  streakYellow: '#FFD93D', // yellow
  streakVibrant: '#FF6B00', // vibrant flame
  chartBars: [
    '#A8E6CF',  // Mint
    '#DCEDC1',  // Light lime
    '#FFD3B6',  // Peach
    '#FFAAA5',  // Salmon
    '#FF8B94',  // Pink
    '#A8E6CF',  // Mint
    '#DCEDC1',  // Light lime
  ],
  lightGreen: '#E6F8F0', // A very light green for bot messages
};

// --- Reusable Styled Components ---

interface StyledInputProps {
  placeholder: string;
  value: string;
  onChangeText: (text: string) => void;
  secureTextEntry?: boolean;
  keyboardType?: KeyboardTypeOptions;
  onFocus?: () => void;
}

const StyledInput = ({ placeholder, value, onChangeText, secureTextEntry = false, keyboardType = 'default', onFocus }: StyledInputProps) => (
  <TextInput
    style={styles.input}
    placeholder={placeholder}
    placeholderTextColor={COLORS.placeholder}
    value={value}
    onChangeText={onChangeText}
    secureTextEntry={secureTextEntry}
    autoCapitalize="none"
    keyboardType={placeholder.toLowerCase().includes('serving') || placeholder.toLowerCase().includes('quantity') || placeholder.toLowerCase().includes('duration') ? 'default' : keyboardType}
    onFocus={onFocus}
  />
);

interface StyledButtonProps {
  title: string;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  disabled?: boolean;
}

const StyledButton = ({ title, onPress, style, disabled = false }: StyledButtonProps) => (
  <TouchableOpacity 
    style={[styles.button, disabled && styles.disabledButton, style]} 
    onPress={onPress}
    disabled={disabled}
    activeOpacity={0.8}
  >
    <Text style={styles.buttonText}>{title}</Text>
  </TouchableOpacity>
);

const ErrorPopup = ({ message, onClose }: { message: string; onClose: () => void }) => (
  <View style={styles.errorPopupOverlay}>
    <View style={styles.errorPopup}>
      <Text style={styles.errorTitle}>❌ Error</Text>
      <Text style={styles.errorMessage}>{message}</Text>
      <TouchableOpacity style={styles.errorButton} onPress={onClose}>
        <Text style={styles.errorButtonText}>Dismiss</Text>
      </TouchableOpacity>
    </View>
  </View>
);

// --- Login/Signup Screen ---

const LoginSignupScreen = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoLoginTried, setAutoLoginTried] = useState(false);
  const [checkingCredentials, setCheckingCredentials] = useState(true);
  const [loadingLogin, setLoadingLogin] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotError, setForgotError] = useState<string | null>(null);
  const [forgotSuccess, setForgotSuccess] = useState(false);
  const [googleError, setGoogleError] = useState<string | null>(null);
  WebBrowser.maybeCompleteAuthSession();
  const [request, response, promptAsync] = Google.useIdTokenAuthRequest({
    clientId: Platform.select({
      android: '383526478160-29on25eqdhqukfukt4uirp4iqjdbeor4.apps.googleusercontent.com',
      ios: '383526478160-em6g7gb6qov60mds6aanjfg1r7rqbqer.apps.googleusercontent.com',
      default: '383526478160-e8eq7b8pr1bslp6tmbbs8b8sdno0jt12.apps.googleusercontent.com', // Optional: for Expo Go/dev
    }),
  });

  useEffect(() => {
    if (response?.type === 'success') {
      const { id_token } = response.params;
      if (id_token) {
        const credential = firebase.auth.GoogleAuthProvider.credential(id_token);
        firebase.auth().signInWithCredential(credential)
          .catch((error) => {
            setGoogleError(error.message || 'Google sign-in failed.');
          });
      }
    } else if (response?.type === 'error') {
      setGoogleError('Google sign-in was cancelled or failed.');
    }
  }, [response]);

  useEffect(() => {
    // Check for saved credentials and auto-login if present
    const checkSavedCredentials = async () => {
      try {
        const savedEmail = await AsyncStorage.getItem('savedEmail');
        const savedPassword = await AsyncStorage.getItem('savedPassword');
        if (savedEmail && savedPassword) {
          setEmail(savedEmail);
          setPassword(savedPassword);
          setRememberMe(true);
          setLoadingLogin(true);
          try {
            await auth.signInWithEmailAndPassword(savedEmail, savedPassword);
          } catch (e) {
            // Ignore error, user can try logging in manually
          }
          setLoadingLogin(false);
        }
      } catch (error) {
        console.error('Error loading saved credentials:', error);
      } finally {
        setCheckingCredentials(false);
      }
    };
    checkSavedCredentials();
  }, []);

  // Auto-login only after both email and password are set from remembered credentials
  // (Removed: auto-login effect that triggers when rememberMe is set)

  const handleSignUp = async () => {
    if (!email || !password || !firstName || !lastName || !age || !gender) {
      setError('Please fill in all fields');
      return;
    }

    try {
      const userCredential = await auth.createUserWithEmailAndPassword(email, password);
      const user = userCredential.user;

      if (user) {
        // Create user profile
        await createUserProfile({
          userId: user.uid,
          firstName,
          lastName,
          age: parseInt(age),
          gender,
          email,
          stepGoal: 10000,
          caloriesBurnedGoal: 500
        });

        // Save credentials if remember me is checked
        if (rememberMe) {
          await AsyncStorage.setItem('savedEmail', email);
          await AsyncStorage.setItem('savedPassword', password);
        }
      }
    } catch (error: any) {
      setError(error.message);
    }
  };

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please enter email and password');
      return;
    }
    setLoadingLogin(true);
    try {
      await auth.signInWithEmailAndPassword(email, password);
      if (rememberMe) {
        await AsyncStorage.setItem('savedEmail', email);
        await AsyncStorage.setItem('savedPassword', password);
      } else {
        await AsyncStorage.removeItem('savedEmail');
        await AsyncStorage.removeItem('savedPassword');
      }
    } catch (error: any) {
      setError('Wrong email or password. Please try again.');
    } finally {
      setLoadingLogin(false);
    }
  };

  const handleForgotPassword = async () => {
    setForgotError(null);
    setForgotSuccess(false);
    if (!forgotEmail) {
      setForgotError('Please enter your email address.');
      return;
    }
    setForgotLoading(true);
    try {
      await auth.sendPasswordResetEmail(forgotEmail.trim());
      setForgotSuccess(true);
    } catch (error: any) {
      if (error.code === 'auth/user-not-found') {
        setForgotError('No user found with this email.');
      } else if (error.code === 'auth/invalid-email') {
        setForgotError('Invalid email address.');
      } else {
        setForgotError('Failed to send reset email. Please try again.');
      }
    } finally {
      setForgotLoading(false);
    }
  };

  if (checkingCredentials || loadingLogin) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', padding: 24, paddingTop: 50 }}
          keyboardShouldPersistTaps="handled"
        >
          <View style={{alignItems: 'center'}}>
            <Text style={styles.title}>Nutricious4u</Text>
            <Text style={styles.subtitle}>Welcome! Let's get started.</Text>
            
            {!isLogin && (
              <>
                <Text style={styles.inputLabel}>First Name</Text>
                <StyledInput
                  placeholder="First Name"
                  value={firstName}
                  onChangeText={setFirstName}
                />
                <Text style={styles.inputLabel}>Last Name</Text>
                <StyledInput
                  placeholder="Last Name"
                  value={lastName}
                  onChangeText={setLastName}
                />
                <Text style={styles.inputLabel}>Age</Text>
                <StyledInput
                  placeholder="Age"
                  value={age}
                  onChangeText={setAge}
                  keyboardType="numeric"
                />
                <Text style={styles.inputLabel}>Gender</Text>
                <View style={styles.genderContainer}>
                  <TouchableOpacity 
                    style={[styles.genderButton, gender === 'male' && styles.genderButtonSelected]} 
                    onPress={() => setGender('male')}
                  >
                    <Text style={[styles.genderButtonText, gender === 'male' && styles.genderButtonTextSelected]}>Male</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.genderButton, gender === 'female' && styles.genderButtonSelected]} 
                    onPress={() => setGender('female')}
                  >
                    <Text style={[styles.genderButtonText, gender === 'female' && styles.genderButtonTextSelected]}>Female</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.genderButton, gender === 'other' && styles.genderButtonSelected]} 
                    onPress={() => setGender('other')}
                  >
                    <Text style={[styles.genderButtonText, gender === 'other' && styles.genderButtonTextSelected]}>Other</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
            
            <Text style={styles.inputLabel}>Email</Text>
            <StyledInput
              placeholder="Email"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
            />
            <Text style={styles.inputLabel}>Password</Text>
            <View style={styles.passwordInputWrapper}>
              <TextInput
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                style={{ flex: 1, paddingVertical: 14, fontSize: 16, color: COLORS.text, backgroundColor: 'transparent', borderWidth: 0 }}
              />
              <TouchableOpacity onPress={() => setShowPassword((v) => !v)} style={styles.eyeIcon}>
                {showPassword ? <EyeOff color={COLORS.placeholder} size={22} /> : <Eye color={COLORS.placeholder} size={22} />}
              </TouchableOpacity>
            </View>
            {/* Forgot Password Link */}
            {isLogin && (
              <TouchableOpacity onPress={() => setShowForgotPassword(true)} style={{ alignSelf: 'flex-end', marginBottom: 8 }}>
                <Text style={{ color: COLORS.primary, fontSize: 14 }}>Forgot Password?</Text>
              </TouchableOpacity>
            )}

            <View style={styles.rememberMeContainer}>
              <TouchableOpacity 
                style={styles.checkbox} 
                onPress={() => setRememberMe(!rememberMe)}
              >
                {rememberMe && <View style={styles.checkboxInner} />}
              </TouchableOpacity>
              <Text style={styles.rememberMeText}>Remember me</Text>
            </View>
            
            <View style={styles.buttonContainer}>
              <StyledButton 
                title={isLogin ? "Login" : "Sign Up"} 
                onPress={isLogin ? handleLogin : handleSignUp} 
              />
              <TouchableOpacity 
                style={styles.switchButton} 
                onPress={() => setIsLogin(!isLogin)}
              >
                <Text style={styles.switchButtonText}>
                  {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Login"}
                </Text>
              </TouchableOpacity>
              {/* Google Sign-In Button */}
              <TouchableOpacity
                style={{
                  marginTop: 16,
                  backgroundColor: COLORS.primary,
                  borderRadius: 20,
                  paddingVertical: 14,
                  paddingHorizontal: 24,
                  alignItems: 'center',
                  flexDirection: 'row',
                  justifyContent: 'center',
                  shadowColor: COLORS.primary,
                  shadowOffset: { width: 0, height: 2 },
                  shadowOpacity: 0.15,
                  shadowRadius: 4,
                  elevation: 4,
                }}
                disabled={!request}
                onPress={() => {
                  setGoogleError(null);
                  promptAsync();
                }}
              >
                <Text style={{ color: COLORS.text, fontWeight: 'bold', fontSize: 16 }}>Sign in with Google</Text>
              </TouchableOpacity>
              {googleError && (
                <Text style={{ color: 'red', marginTop: 8 }}>{googleError}</Text>
              )}
            </View>

            {error && (
              <ErrorPopup 
                message={error} 
                onClose={() => setError(null)} 
              />
            )}
          </View>
        </ScrollView>
        {/* Forgot Password Modal */}
        <Modal
          visible={showForgotPassword}
          animationType="slide"
          transparent
          onRequestClose={() => setShowForgotPassword(false)}
        >
          <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
            <View style={styles.errorPopupOverlay}>
              <View style={styles.errorPopup}>
                <Text style={styles.errorTitle}>Reset Password</Text>
                <Text style={styles.errorMessage}>Enter your email address to receive a password reset link.</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Email"
                  value={forgotEmail}
                  onChangeText={setForgotEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
                {forgotError && <Text style={styles.errorMessage}>{forgotError}</Text>}
                {forgotSuccess && <Text style={{ color: COLORS.primary, marginTop: 8 }}>Reset email sent! Check your inbox.</Text>}
                <View style={{ flexDirection: 'row', marginTop: 16 }}>
                  <TouchableOpacity
                    style={[styles.errorButton, { flex: 1, marginRight: 8, backgroundColor: COLORS.primary }]}
                    onPress={handleForgotPassword}
                    disabled={forgotLoading}
                  >
                    <Text style={styles.errorButtonText}>{forgotLoading ? 'Sending...' : 'Send'}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.errorButton, { flex: 1, marginLeft: 8, backgroundColor: '#aaa' }]}
                    onPress={() => {
                      setShowForgotPassword(false);
                      setForgotEmail('');
                      setForgotError(null);
                      setForgotSuccess(false);
                    }}
                  >
                    <Text style={styles.errorButtonText}>Cancel</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </Modal>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// --- Circular Progress with Consumed / Target and Burned Overlay ---
const CircularProgress = ({ 
  value, 
  maxValue, 
  burned = 0,
  size = 120, 
  strokeWidth = 10, 
  title, 
  unit,
  color 
}: { 
  value: number; 
  maxValue: number; 
  burned?: number;
  size?: number; 
  strokeWidth?: number; 
  title: string;
  unit: string;
  color: string;
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const progress = Math.min(value / maxValue, 1);
  const burnedProgress = Math.min(burned / maxValue, 1);
  const progressOffset = circumference * (1 - progress);
  const burnedOffset = circumference * (1 - burnedProgress);

  return (
    <View style={styles.circularProgressContainer}>
      <Svg width={size} height={size}>
        {/* Background circle */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={`${color}40`}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress circle (net calories) */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={progressOffset}
          strokeLinecap="round"
          fill="none"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        {/* Burned overlay arc (orange) */}
        {burned > 0 && (
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={COLORS.streakActive}
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={burnedOffset}
            strokeLinecap="round"
            fill="none"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        )}
        {/* Center text: consumed / target */}
        <SvgText
          x={size / 2}
          y={size / 2 - 5}
          fontSize="16"
          fill={COLORS.text}
          textAnchor="middle"
        >
          {`${Math.round(value)} / ${Math.round(maxValue)}`}
        </SvgText>
        <SvgText
          x={size / 2}
          y={size / 2 + 15}
          fontSize="12"
          fill={COLORS.placeholder}
          textAnchor="middle"
        >
          {unit}
        </SvgText>
      </Svg>
      <Text style={[styles.circularProgressTitle, { color }]}>{title}</Text>
    </View>
  );
};

// --- DashboardScreen ---
const DashboardScreen = ({ navigation, route }: { navigation: any, route?: any }) => {
  const [summary, setSummary] = useState<LogSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [burnedToday, setBurnedToday] = useState(0);
  const [stepsToday, setStepsToday] = useState(0);
  const isFocused = useIsFocused();
  const userId = auth.currentUser?.uid;
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const refresh = route?.params?.refresh;
  const [showFoodModal, setShowFoodModal] = useState(false);
  const [showWorkoutModal, setShowWorkoutModal] = useState(false);
  const [foodName, setFoodName] = useState('');
  const [foodQty, setFoodQty] = useState('');
  const [workoutName, setWorkoutName] = useState('');
  const [workoutQty, setWorkoutQty] = useState('');
  const [showFoodSuccess, setShowFoodSuccess] = useState(false);
  const [showWorkoutSuccess, setShowWorkoutSuccess] = useState(false);
  const [showFoodError, setShowFoodError] = useState(false);
  const [showWorkoutError, setShowWorkoutError] = useState(false);
  const [workoutError, setWorkoutError] = useState('');
  const [workoutSummary, setWorkoutSummary] = useState<WorkoutLogSummaryResponse | null>(null);

  // Fetch user profile for targets whenever focused
  useEffect(() => {
    const fetchProfile = async () => {
      if (!userId) return;
      try {
        const profile = await getUserProfile(userId);
        setUserProfile(profile);
      } catch {}
    };
    if (isFocused) fetchProfile();
  }, [userId, isFocused, route?.params?.refresh]);

  // --- Persist calories burned and steps for the current day ---
  const getTodayKey = () => {
    const d = new Date();
    return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  };

  // Load burnedToday and stepsToday from AsyncStorage on mount or day change
  useEffect(() => {
    const loadPersisted = async () => {
      const todayKey = getTodayKey();
      const burned = await AsyncStorage.getItem('burnedToday_' + todayKey);
      const steps = await AsyncStorage.getItem('stepsToday_' + todayKey);
      setBurnedToday(safeNumber(Number(burned)));
      setStepsToday(safeNumber(Number(steps)));
    };
    loadPersisted();
  }, [isFocused, getTodayKey()]);

  // Persist burnedToday and stepsToday whenever they change
  useEffect(() => {
    const todayKey = getTodayKey();
    AsyncStorage.setItem('burnedToday_' + todayKey, String(safeNumber(burnedToday)));
  }, [burnedToday]);
  useEffect(() => {
    const todayKey = getTodayKey();
    AsyncStorage.setItem('stepsToday_' + todayKey, String(safeNumber(stepsToday)));
  }, [stepsToday]);

  // Fetch step count for today
  useEffect(() => {
    let isMounted = true;
    const fetchSteps = async () => {
      try {
        const end = new Date();
        const start = new Date();
        start.setHours(0, 0, 0, 0);
        const result = await Pedometer.getStepCountAsync(start, end);
        if (isMounted) setStepsToday(result.steps);
      } catch (e) {
        if (isMounted) setStepsToday(0);
      }
    };
    fetchSteps();
    return () => { isMounted = false; };
  }, [isFocused, refresh, showFoodSuccess, showWorkoutSuccess]);

  // Fetch summary (nutrition) and workout calories for today
  const fetchSummary = async () => {
    if (!userId) {
      setError('User not authenticated');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const [foodData, workoutData] = await Promise.all([
        getLogSummary(userId),
        getWorkoutLogSummary(userId)
      ]);
      setSummary(foodData);
      setWorkoutSummary(workoutData);
      // Set burnedToday from workout summary for today
      const today = new Date().toISOString().slice(0, 10);
      const todayWorkout = workoutData.history.find((d) => d.day === today);
      setBurnedToday(todayWorkout ? todayWorkout.calories : 0);
    } catch (e) {
      setError('Could not load dashboard data.');
      console.error('Dashboard data error:', e);
    } finally {
      setLoading(false);
    }
  };

  // Refresh summary after logging food or workout
  useEffect(() => {
    if (isFocused && userId) {
      fetchSummary();
    }
  }, [isFocused, userId, refresh, showFoodSuccess, showWorkoutSuccess]);

  // Handler to update calories burned from workout log
  const handleWorkoutLogged = (caloriesBurned: number) => {
    setBurnedToday(prev => prev + caloriesBurned);
    setShowWorkoutSuccess(true);
    // Optionally, show a toast or popup here
    Alert.alert('Success', 'Workout logged successfully!');
    // Do NOT call fetchSummary() here
  };

  // Handler to update after food log
  const handleFoodLogged = () => {
    setShowFoodSuccess(true);
    fetchSummary();
  };

  const SummaryCard = ({ title, value, unit }: { title: string; value: string | number; unit: string }) => (
    <View style={styles.summaryCard}>
      <Text style={styles.summaryTitle}>{title}</Text>
      <Text style={styles.summaryValue}>{value}</Text>
      <Text style={styles.summaryUnit}>{unit}</Text>
    </View>
  );

  // --- Food Modal Handler ---
  const [foodLoading, setFoodLoading] = useState(false);
  const [workoutLoading, setWorkoutLoading] = useState(false); // Add this line
  const handleLogFoodModal = async () => {
    if (!foodName.trim() || !foodQty.trim()) {
      setShowFoodError(true);
      return;
    }
    const userId = auth.currentUser?.uid;
    if (userId) {
      try {
        setFoodLoading(true);
        // If foodQty is not a number, send as string; if it is a number, send as string
        await logFood(userId, foodName.trim(), foodQty);
        setShowFoodModal(false);
        setShowFoodSuccess(true);
        setFoodName('');
        setFoodQty('');
        fetchSummary();
      } catch {
        setShowFoodError(true);
      } finally {
        setFoodLoading(false);
      }
    }
  };

  // --- Workout Modal Handler ---
  const handleLogWorkoutModal = async () => {
    if (!workoutName.trim() || !workoutQty.trim()) {
      setShowWorkoutError(true);
      setWorkoutError('Please enter a valid workout name and duration.');
      return;
    }
    
    const userId = auth.currentUser?.uid;
    if (!userId) {
      setShowWorkoutError(true);
      setWorkoutError('User not authenticated.');
      return;
    }
    
    try {
      setWorkoutLoading(true); // Set loading true
      // Call the backend API to log the workout
      const workoutData = {
        userId: userId,
        exerciseId: "1",
        exerciseName: workoutName.trim(),
        type: "cardio",
        duration: workoutQty.trim(),
        sets: null,
        reps: null,
        date: null
      };
      
      const result = await logWorkout(workoutData);
      const caloriesBurned = result.calories || 0;
      
      // Update the calories burned tracker
      setBurnedToday(prev => {
        const updated = safeNumber(prev) + safeNumber(caloriesBurned);
        const todayKey = getTodayKey();
        AsyncStorage.setItem('burnedToday_' + todayKey, String(updated));
        return updated;
      });
      
      setShowWorkoutModal(false);
      setShowWorkoutSuccess(true);
      setWorkoutName('');
      setWorkoutQty('');
      
      // Show success popup
      setTimeout(() => setShowWorkoutSuccess(false), 1500);
    } catch (error: any) {
      console.error('Error logging workout:', error);
      let errorMessage = 'Failed to log workout. Please try again.';
      
      // Provide more specific error messages
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. The AI is taking longer than expected. Please try again.';
      } else if (error.message === 'Network Error') {
        errorMessage = 'Network connection issue. Please check your internet connection and try again.';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error. Please try again in a moment.';
      }
      
      setShowWorkoutError(true);
      setWorkoutError(errorMessage);
    } finally {
      setWorkoutLoading(false); // Set loading false
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, {justifyContent: 'center'}]}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={[styles.container, {justifyContent: 'center', alignItems: 'center'}]}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={fetchSummary}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const todayData = summary?.history?.[0] || {
    calories: 0,
    protein: 0,
    fat: 0,
    carbs: 0
  };

  // Get targets from userProfile if available
  const targetCalories = userProfile?.targetCalories || 2000;
  const targetProtein = userProfile?.targetProtein || 150;
  const targetFat = userProfile?.targetFat || 65;
  const targetSteps = userProfile?.stepGoal ?? 10000;
  const targetBurned = userProfile?.caloriesBurnedGoal ?? 0;

  return (
    <SafeAreaView style={[styles.container, { paddingHorizontal: 16, paddingTop: 50 }]}> 
      <View style={styles.headerContainer}>
        <Text style={styles.screenTitle}>Dashboard</Text>
      </View>
      {/* --- Single Rectangle Widget --- */}
      <SummaryWidget
        todayData={todayData}
        targets={{ calories: targetCalories, protein: targetProtein, fat: targetFat, steps: targetSteps, burned: targetBurned }}
        stepsToday={stepsToday}
        burnedToday={burnedToday}
        onPress={() => navigation.navigate('TrackingDetails', { summary, stepsToday, burnedToday, userProfile, workoutSummary })}
      />
      {/* --- End Widget --- */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: COLORS.logFood }]}
          onPress={() => setShowFoodModal(true)}
        >
          <Search color={COLORS.white} size={24} />
          <Text style={styles.actionButtonText}>Log Food</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: COLORS.scanFood }]} 
          disabled
        >
          <Camera color={COLORS.white} size={24} />
          <Text style={styles.actionButtonText}>Scan Food</Text>
          <Text style={styles.comingSoonText}>Coming Soon</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: COLORS.logWorkout }]}
          onPress={() => setShowWorkoutModal(true)}
        >
          <Dumbbell color={COLORS.white} size={24} />
          <Text style={styles.actionButtonText}>Log Workout</Text>
        </TouchableOpacity>
      </View>
      {/* Routines Button */}
      <TouchableOpacity
        style={styles.routinesButton}
        onPress={() => navigation.navigate('Routine')}
        activeOpacity={0.85}
      >
        <Text style={styles.routinesButtonText}>Routines</Text>
      </TouchableOpacity>
      {/* Log Food Modal */}
      <Modal
        visible={showFoodModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowFoodModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Log Food</Text>
            <Text style={styles.modalLabel}>Name of the food</Text>
            <TextInput
              style={styles.modalInput}
              value={foodName}
              onChangeText={setFoodName}
              placeholder="e.g. Apple"
            />
            <Text style={styles.modalLabel}>Quantity</Text>
            <TextInput
              style={styles.modalInput}
              value={foodQty}
              onChangeText={setFoodQty}
              placeholder="e.g. 100 (grams)"
            />
            <View style={styles.modalButtonRow}>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: foodLoading ? COLORS.placeholder : COLORS.primary }]}
                onPress={handleLogFoodModal}
                disabled={foodLoading}
              >
                {foodLoading ? (
                  <ActivityIndicator color={COLORS.white} />
                ) : (
                  <Text style={styles.modalButtonText}>Log</Text>
                )}
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: COLORS.error }]}
                onPress={() => {
                  setShowFoodModal(false);
                  setFoodName('');
                  setFoodQty('');
                }}
                disabled={foodLoading}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.poweredBy}>Powered by Google Gemini 2.5 Flash</Text>
          </View>
        </View>
      </Modal>
      {/* Food Error Popup */}
      <Modal
        visible={showFoodError}
        animationType="fade"
        transparent
        onRequestClose={() => setShowFoodError(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.errorPopup}>
            <Text style={styles.errorTitle}>Error</Text>
            <Text style={styles.errorMessage}>Please enter a valid food name and quantity.</Text>
            <TouchableOpacity style={styles.errorButton} onPress={() => setShowFoodError(false)}>
              <Text style={styles.errorButtonText}>Dismiss</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      {/* Food Success Popup */}
      <Modal
        visible={showFoodSuccess}
        animationType="fade"
        transparent
        onRequestClose={() => setShowFoodSuccess(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.successPopup}>
            <Text style={styles.successTitle}>🎉 Food successfully logged!</Text>
            <TouchableOpacity
              style={styles.bigCloseButton}
              onPress={() => setShowFoodSuccess(false)}
            >
              <Text style={styles.bigCloseButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      {/* Log Workout Modal */}
      <Modal
        visible={showWorkoutModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowWorkoutModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Log Workout</Text>
            <Text style={styles.modalLabel}>Name of the workout</Text>
            <TextInput
              style={styles.modalInput}
              value={workoutName}
              onChangeText={setWorkoutName}
              placeholder="e.g. Running"
            />
            <Text style={styles.modalLabel}>Duration</Text>
            <TextInput
              style={styles.modalInput}
              value={workoutQty}
              onChangeText={setWorkoutQty}
              placeholder="e.g. 30 (minutes)"
            />
            <View style={styles.modalButtonRow}>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: workoutLoading ? COLORS.placeholder : COLORS.primary }]}
                onPress={handleLogWorkoutModal}
                disabled={workoutLoading}
              >
                {workoutLoading ? (
                  <ActivityIndicator color={COLORS.white} />
                ) : (
                  <Text style={styles.modalButtonText}>Log</Text>
                )}
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: COLORS.error }]}
                onPress={() => {
                  setShowWorkoutModal(false);
                  setWorkoutName('');
                  setWorkoutQty('');
                }}
                disabled={workoutLoading}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.poweredBy}>Powered by Google Gemini 2.5 Flash</Text>
          </View>
        </View>
      </Modal>
      {/* Workout Error Popup */}
      <Modal
        visible={showWorkoutError}
        animationType="fade"
        transparent
        onRequestClose={() => setShowWorkoutError(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.errorPopup}>
            <Text style={styles.errorTitle}>Error</Text>
            <Text style={styles.errorMessage}>{workoutError || 'Please enter a valid workout name and duration.'}</Text>
            <TouchableOpacity style={styles.errorButton} onPress={() => setShowWorkoutError(false)}>
              <Text style={styles.errorButtonText}>Dismiss</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      {/* Workout Success Popup */}
      <Modal
        visible={showWorkoutSuccess}
        animationType="fade"
        transparent
        onRequestClose={() => setShowWorkoutSuccess(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.successPopup}>
            <Text style={styles.successTitle}>🎉 Workout successfully logged!</Text>
            <TouchableOpacity
              style={styles.bigCloseButton}
              onPress={() => setShowWorkoutSuccess(false)}
            >
              <Text style={styles.bigCloseButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const FoodLogScreen = ({ navigation, route }: { navigation: any, route?: any }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FoodItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [servingSizes, setServingSizes] = useState<{ [id: string]: string }>({});
  const { onFoodLogged } = route.params || {};
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [confetti, setConfetti] = useState(false);
  const [successFood, setSuccessFood] = useState<string | null>(null);

  const handleSearch = async () => {
    if (searchQuery.trim() === '') return;
    setLoading(true);
    setError('');
    setSearchResults([]);
    try {
      // Use the new backend endpoint for USDA search
      const response = await fetch(`${API_URL}/food/search?query=${encodeURIComponent(searchQuery)}`);
      if (!response.ok) throw new Error('Failed to fetch food data.');
      const data = await response.json();
      setSearchResults(data.foods);
      // Set default serving size to 100 for all results
      const defaultSizes: { [id: string]: string } = {};
      data.foods.forEach((item: FoodItem) => { defaultSizes[item.id] = '100'; });
      setServingSizes(defaultSizes);
    } catch (e) {
      setError('Failed to fetch food data. Please try again.');
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleLogFood = async (item: FoodItem) => {
    const userId = auth.currentUser?.uid;
    if (!userId) {
      Alert.alert('Error', 'You must be logged in to log food.');
      return;
    }
    try {
      const servingSize = servingSizes[item.id] || '100';
      await logFood(userId, item.name, servingSize);
      setSuccessFood(item.name);
      setShowConfetti(true);
      setExpandedId(null);
      if (onFoodLogged) onFoodLogged();
      setTimeout(() => setShowConfetti(false), 3000);
      setShowSuccess(true);
      setConfetti(true);
    } catch (e) {
      Alert.alert('Error', 'Failed to log food item.');
      console.error(e);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { paddingTop: 50 }]}> 
      <View style={styles.headerContainer}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 4, minWidth: 40, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 22, color: COLORS.primaryDark }}>{'<'} </Text>
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Log Food</Text>
        <View style={{ minWidth: 40 }} />
      </View>
      <View style={styles.logContainer}>
        <StyledInput
          placeholder="e.g., 'Apple'"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        <StyledButton title="Search" onPress={handleSearch} />
        <TouchableOpacity style={[styles.button, styles.disabledButton]} disabled>
          <Camera color={COLORS.white} size={20} style={{marginRight: 8}}/>
          <Text style={styles.buttonText}>Scan with Camera (Coming Soon)</Text>
        </TouchableOpacity>
        {loading && <ActivityIndicator size="large" color={COLORS.primary} style={{marginTop: 20}} />}
        {error && <Text style={styles.errorText}>{error}</Text>}
        <FlatList
          data={searchResults}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.foodItem, expandedId === item.id && { minHeight: 120, backgroundColor: COLORS.primary + '10' }]}
              onPress={() => setExpandedId(expandedId === item.id ? null : item.id)}
              activeOpacity={0.85}
            >
              <View style={{flex: 1}}>
                <Text style={styles.foodName}>{item.name}</Text>
                <Text style={styles.foodDetails}>
                  {Math.round(item.calories)} kcal · P: {item.protein.toFixed(1)}g F: {item.fat.toFixed(1)}g
                </Text>
              </View>
              {expandedId === item.id && (
                <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12 }}>
                  <TextInput
                    style={{
                      width: 60,
                      height: 36,
                      borderColor: COLORS.primary,
                      borderWidth: 1,
                      borderRadius: 8,
                      marginRight: 8,
                      textAlign: 'center',
                      backgroundColor: COLORS.white,
                      fontSize: 16,
                      paddingVertical: 4,
                      paddingHorizontal: 0,
                      alignSelf: 'center',
                    }}
                    value={servingSizes[item.id]}
                    onChangeText={text => setServingSizes(s => ({ ...s, [item.id]: text.replace(/[^0-9]/g, '') }))}
                    keyboardType="numeric"
                    placeholder="g"
                    maxLength={4}
                  />
                  <Text style={{ marginRight: 8 }}>g</Text>
                  <TouchableOpacity style={styles.logButton} onPress={() => handleLogFood(item)}>
                    <Text style={styles.logButtonText}>Log</Text>
                  </TouchableOpacity>
                </View>
              )}
            </TouchableOpacity>
          )}
          style={{marginTop: 16}}
        />
        {showConfetti && <ConfettiCannon count={80} origin={{x: 200, y: 0}} fadeOut explosionSpeed={350} fallSpeed={2500} />} 
      </View>
      {showSuccess && (
        <View style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.4)',
          justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }}>
          <View style={{
            backgroundColor: '#e6ffe6',
            borderRadius: 24,
            padding: 32,
            alignItems: 'center',
            width: '80%',
            shadowColor: '#00C851',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.3,
            shadowRadius: 8,
            elevation: 8,
          }}>
            <Text style={{ fontSize: 36, marginBottom: 8 }}>🎉</Text>
            <Text style={{ fontSize: 22, fontWeight: 'bold', color: '#009e60', marginBottom: 8 }}>Food Logged!</Text>
            <Text style={{ fontSize: 18, color: '#333', marginBottom: 16, textAlign: 'center' }}>
              {successFood ? `${successFood} has been added to your log!` : 'Food has been logged!'}
            </Text>
            <TouchableOpacity
              style={{
                backgroundColor: '#4ee44e',
                paddingVertical: 16,
                paddingHorizontal: 40,
                borderRadius: 16,
                marginTop: 8,
                shadowColor: '#4ee44e',
                shadowOffset: { width: 0, height: 2 },
                shadowOpacity: 0.2,
                shadowRadius: 4,
                elevation: 4,
              }}
              onPress={() => {
                setShowSuccess(false);
                setConfetti(false);
                setSuccessFood(null);
                navigation.reset({
                  index: 0,
                  routes: [{ name: 'Main', params: { refresh: Date.now() } }],
                });
              }}
              activeOpacity={0.85}
            >
              <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 18 }}>Close</Text>
            </TouchableOpacity>
          </View>
          {confetti && (
            <ConfettiCannon
              count={80}
              origin={{ x: 200, y: 0 }}
              fadeOut
              explosionSpeed={400}
              fallSpeed={2500}
            />
          )}
        </View>
      )}
    </SafeAreaView>
  );
};

const WorkoutLogScreen = ({ navigation, route }: { navigation: any, route?: any }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedExercise, setSelectedExercise] = useState<any | null>(null);
  const [duration, setDuration] = useState('');
  const [sets, setSets] = useState('');
  const [reps, setReps] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const userId = auth.currentUser?.uid;
  // For calorie update
  const onWorkoutLogged = route?.params?.onWorkoutLogged;

  // Cardio categories in Wger: 4 (Cardio), 10 (Running), 13 (Cycling), etc.
  const CARDIO_CATEGORIES = [4, 10, 13];

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError('');
    setSearchResults([]);
    setSelectedExercise(null);
    try {
      const res = await fetch(`https://wger.de/api/v2/exerciseinfo/?language=2&status=50&limit=20&name=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      const filtered = (data.results || []).filter((item: any) => {
        const query = searchQuery.trim().toLowerCase();
        let names: string[] = [];
        if (Array.isArray(item.translations)) {
          names = item.translations.map((t: any) => t.name?.toLowerCase() || '').filter(Boolean);
        }
        if (item.name) names.push(item.name.toLowerCase());
        return names.some(n => n.includes(query));
      });
      setSearchResults(filtered);
      if (filtered.length === 0) setError('No exercises found.');
    } catch (e) {
      setError('Failed to fetch exercises.');
    } finally {
      setLoading(false);
    }
  };

  const handleLog = async () => {
    if (!selectedExercise) return;
    setError('');
    let type = CARDIO_CATEGORIES.includes(selectedExercise.category) ? 'cardio' : 'strength';
    
    // Handle duration validation for cardio workouts
    if (type === 'cardio') {
      if (!duration.trim()) { 
        setError('Enter duration'); 
        return; 
      }
    }
    
    if (type === 'strength' && (!sets || !reps)) { 
      setError('Enter sets and reps'); 
      return; 
    }
    
    try {
      // Call the backend API to log the workout
      const workoutData = {
        userId: auth.currentUser?.uid || "",
        exerciseId: "1",
        exerciseName: selectedExercise.name,
        type: type,
        duration: duration.trim(),
        sets: sets || null,
        reps: reps || null,
        date: null
      };
      
      const result = await logWorkout(workoutData);
      const caloriesBurned = result.calories || 0;
      
      // Call parent/dashboard to update calories
      if (onWorkoutLogged) onWorkoutLogged(caloriesBurned);
      setShowSuccess(true);
      setSelectedExercise(null); setDuration(''); setSets(''); setReps('');
    } catch (error) {
      console.error('Error logging workout:', error);
      setError('Failed to log workout. Please try again.');
    }
  };

  return (
    <SafeAreaView style={[styles.container, {backgroundColor: COLORS.background, paddingTop: 50}]}> 
      <View style={styles.headerContainer}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 4, minWidth: 40, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 22, color: COLORS.primaryDark }}>{'<'} </Text>
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Log Workout</Text>
        <View style={{ minWidth: 40 }} />
      </View>
      {!selectedExercise && (
        <View style={styles.logContainer}>
          <StyledInput
            placeholder="Search exercise (e.g. Running, Push-up)"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          <StyledButton title="Search" onPress={handleSearch} />
          {loading && <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 20 }} />}
          {error && <Text style={styles.errorText}>{error}</Text>}
          <FlatList
            data={searchResults}
            keyExtractor={item => item.id.toString()}
            renderItem={({ item }) => (
              <TouchableOpacity style={styles.workoutResultBox} onPress={() => setSelectedExercise(item)}>
                <Text style={[styles.foodName, {fontSize: 20, fontWeight: 'bold', textAlign: 'center'}]}>
                  {(() => {
                    // Prefer English translation name
                    const en = item.translations.find((t: any) => t.language === 2 && t.name);
                    if (en && en.name) return en.name;
                    // Fallbacks
                    return item.name || (item.id ? `Exercise #${item.id}` : 'Unnamed Exercise');
                  })()}
                </Text>
              </TouchableOpacity>
            )}
            style={{ marginTop: 16 }}
          />
        </View>
      )}
      {selectedExercise && (
        <View style={styles.logContainer}>
          <Text style={[styles.foodName, {fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginBottom: 16}]}>{selectedExercise.name}</Text>
          {CARDIO_CATEGORIES.includes(selectedExercise.category) ? (
            <StyledInput
              placeholder="Duration (minutes)"
              value={duration}
              onChangeText={setDuration}
              keyboardType="numeric"
            />
          ) : (
            <>
              <StyledInput
                placeholder="Sets"
                value={sets}
                onChangeText={setSets}
                keyboardType="numeric"
              />
              <StyledInput
                placeholder="Reps per set"
                value={reps}
                onChangeText={setReps}
                keyboardType="numeric"
              />
            </>
          )}
          <StyledButton title="Log Workout" onPress={handleLog} />
          <TouchableOpacity onPress={() => setSelectedExercise(null)} style={{ marginTop: 12 }}>
            <Text style={{ color: COLORS.error }}>Cancel</Text>
          </TouchableOpacity>
          {error && <Text style={styles.errorText}>{error}</Text>}
        </View>
      )}
      {showSuccess && (
        <View style={styles.errorPopupOverlay}>
          <View style={styles.errorPopup}>
            <Text style={styles.errorTitle}>✅ Success</Text>
            <Text style={styles.errorMessage}>Workout logged successfully!</Text>
            <TouchableOpacity style={styles.errorButton} onPress={() => setShowSuccess(false)}>
              <Text style={styles.errorButtonText}>Dismiss</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
};

const SettingsScreen = ({ navigation }: { navigation: any }) => {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const userId = auth.currentUser?.uid;
        if (!userId) return;
        const profile = await getUserProfile(userId);
        if (profile) {
          setUserProfile(profile);
        } else {
          setUserProfile(null); // No profile found, do not show error
        }
      } catch (e) {
        setError('Could not load user profile.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleUpdateProfile = async () => {
    const userId = auth.currentUser?.uid;
    if (!userId || !userProfile) return;

    try {
      const updatedProfile = await updateUserProfile(userId, {
        firstName: userProfile.firstName,
        lastName: userProfile.lastName,
        age: parseInt(userProfile.age.toString()),
        gender: userProfile.gender
      });
      setUserProfile(updatedProfile);
      setIsEditing(false);
      Alert.alert('Success', 'Profile updated successfully');
    } catch (error) {
      console.error('Error updating profile:', error);
      Alert.alert('Error', 'Failed to update profile');
    }
  };

  const handleLogout = async () => {
    try {
      // Clear saved credentials BEFORE signing out
      await AsyncStorage.removeItem('savedEmail');
      await AsyncStorage.removeItem('savedPassword');
      await new Promise(res => setTimeout(res, 150)); // Ensure storage is cleared before signOut
      await auth.signOut();
    } catch (error) {
      console.error('Error signing out:', error);
      Alert.alert('Error', 'Failed to sign out');
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { paddingTop: 32, paddingHorizontal: 16 }]}> 
        <ActivityIndicator size="large" color={COLORS.primary} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { paddingTop: 32, paddingHorizontal: 16 }]}> 
      <View style={styles.settingsContainer}>
        <Text style={styles.screenTitle}>Settings</Text>
        {error ? (
          <Text style={styles.errorText}>{error}</Text>
        ) : userProfile ? (
          <>
            <View style={styles.settingsButtonRow}>
              <TouchableOpacity
                style={styles.settingsAccountButton}
                onPress={() => navigation.navigate('AccountSettings')}
                activeOpacity={0.85}
              >
                <Text style={styles.settingsAccountButtonText}>Account Settings</Text>
              </TouchableOpacity>
            </View>
            {/* Login Settings Button */}
            <View style={styles.settingsButtonRow}>
              <TouchableOpacity
                style={styles.loginSettingsButton}
                onPress={() => navigation.navigate('LoginSettings')}
                activeOpacity={0.85}
              >
                <Text style={styles.loginSettingsButtonText}>Login Settings</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.settingsButtonRow}>
              <TouchableOpacity
                style={styles.notificationSettingsButton}
                onPress={() => navigation.navigate('NotificationSettings')}
                activeOpacity={0.85}
              >
                <Text style={styles.notificationSettingsButtonText}>Notification Settings</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.settingsButtonRow}>
              <StyledButton 
                title="Logout" 
                onPress={handleLogout}
                style={styles.settingsLogoutButton}
              />
            </View>
          </>
        ) : (
          <Text style={styles.noDataText}>No profile found. Please create your profile.</Text>
        )}
      </View>
    </SafeAreaView>
  );
};

// --- QnA Screen ---
const QnAScreen = ({ navigation, route }: { navigation: any; route: any }) => {
  const { userId } = route.params;
  const { setHasCompletedQuiz } = useContext(AppContext);
  const [currentWeight, setCurrentWeight] = useState('');
  const [goalWeight, setGoalWeight] = useState('');
  const [height, setHeight] = useState('');
  const [dietaryPreference, setDietaryPreference] = useState('');
  const [favouriteCuisine, setFavouriteCuisine] = useState('');
  const [allergies, setAllergies] = useState('');
  const [medicalConditions, setMedicalConditions] = useState('');
  const [activityLevel, setActivityLevel] = useState('sedentary');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [targets, setTargets] = useState({ calories: 0, protein: 0, fat: 0 });
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    // Recalculate targets when relevant fields change
    setTargets(
      calculateTargets({
        weight: Number(currentWeight),
        height: Number(height),
        age: Number(age),
        gender,
        activityLevel,
      })
    );
  }, [currentWeight, height, age, gender, activityLevel]);

  const handleSubmit = async () => {
    console.log('[handleSubmit] Starting submission...');
    if (!currentWeight || !goalWeight || !height || !dietaryPreference || !age || !gender) {
      console.log('[handleSubmit] Validation failed.');
      setError('Please fill in all required fields');
      return;
    }
    console.log('[handleSubmit] Validation passed. Setting loading to true.');
    setLoading(true);
    setError(null);
    try {
      const profileData = {
        currentWeight: Number(currentWeight),
        goalWeight: Number(goalWeight),
        height: Number(height),
        dietaryPreference,
        favouriteCuisine,
        allergies,
        medicalConditions,
        activityLevel,
        age: Number(age),
        gender,
        targetCalories: targets.calories,
        targetProtein: targets.protein,
        targetFat: targets.fat,
      };
      console.log('[handleSubmit] Calling updateUserProfile with data:', JSON.stringify(profileData, null, 2));
      const response = await updateUserProfile(userId, profileData);
      
      console.log('[handleSubmit] updateUserProfile successful with response:', response);
      await AsyncStorage.setItem('hasCompletedQuiz', 'true');
      console.log('[handleSubmit] AsyncStorage updated.');
      setHasCompletedQuiz(true);
      console.log('[handleSubmit] Quiz completion state updated.');

    } catch (e: any) {
      console.error('[handleSubmit] Error caught:', e);
      if (e.response) {
        console.error('[handleSubmit] Error response data:', e.response.data);
        console.error('[handleSubmit] Error response status:', e.response.status);
      } else {
        console.error('[handleSubmit] Error has no response object. Message:', e.message);
      }
      setError(e.message || 'An unexpected error occurred. Please try again.');
    } finally {
      console.log('[handleSubmit] In finally block. Setting loading to false.');
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : -100}
      >
        <ScrollView
          ref={scrollRef}
          contentContainerStyle={{ paddingHorizontal: 24, paddingTop: 50, paddingBottom: 40 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
            <Text style={[styles.title, { fontSize: 28, textAlign: 'center', marginBottom: 24 }]}>Tell us about yourself</Text>
            
            <Text style={styles.inputLabel}>Current Weight (kg)</Text>
            <StyledInput placeholder="Current Weight (kg)" value={currentWeight} onChangeText={setCurrentWeight} keyboardType="numeric" />
            
            <Text style={styles.inputLabel}>Goal Weight (kg)</Text>
            <StyledInput placeholder="Goal Weight (kg)" value={goalWeight} onChangeText={setGoalWeight} keyboardType="numeric" />
            
            <Text style={styles.inputLabel}>Height (cm)</Text>
            <StyledInput placeholder="Height (cm)" value={height} onChangeText={setHeight} keyboardType="numeric" />
            
            <Text style={styles.inputLabel}>Age</Text>
            <StyledInput placeholder="Age" value={age} onChangeText={setAge} keyboardType="numeric" />
            
            <Text style={styles.inputLabel}>Gender</Text>
            <View style={styles.pickerWrapper}>
              <Picker selectedValue={gender} onValueChange={setGender} style={styles.picker}>
                <Picker.Item label="Select gender..." value="" />
                <Picker.Item label="Male" value="male" />
                <Picker.Item label="Female" value="female" />
                <Picker.Item label="Other" value="other" />
              </Picker>
            </View>
            
            <Text style={styles.inputLabel}>Daily Activity Level</Text>
            <View style={styles.pickerWrapper}>
              <Picker selectedValue={activityLevel} onValueChange={setActivityLevel} style={styles.picker}>
                {ACTIVITY_LEVELS.map(l => <Picker.Item key={l.value} label={l.label} value={l.value} />)}
              </Picker>
            </View>
            
            <Text style={styles.inputLabel}>Dietary Preference</Text>
            <View style={styles.pickerWrapper}>
              <Picker selectedValue={dietaryPreference} onValueChange={setDietaryPreference} style={styles.picker}>
                <Picker.Item label="Select preference..." value="" />
                <Picker.Item label="Vegetarian" value="vegetarian" />
                <Picker.Item label="Non Vegetarian" value="non-vegetarian" />
                <Picker.Item label="Vegan" value="vegan" />
                <Picker.Item label="Eggetarian" value="eggetarian" />
                <Picker.Item label="Pescatarian" value="pescatarian" />
                <Picker.Item label="Keto" value="keto" />
                <Picker.Item label="Other" value="other" />
              </Picker>
            </View>
            
            <Text style={styles.inputLabel}>Favourite Cuisine (optional)</Text>
            <StyledInput placeholder="Favourite Cuisine" value={favouriteCuisine} onChangeText={setFavouriteCuisine} />
            
            <Text style={styles.inputLabel}>Allergies (optional)</Text>
            <StyledInput placeholder="Allergies" value={allergies} onChangeText={setAllergies} />
            
            <Text style={styles.inputLabel}>Medical Conditions (optional)</Text>
            <StyledInput 
              placeholder="Medical Conditions" 
              value={medicalConditions} 
              onChangeText={setMedicalConditions}
              onFocus={() => {
                setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
              }}
            />

            <View style={{ marginVertical: 12 }}>
              <Text style={{ fontWeight: 'bold', color: '#888', fontSize: 16 }}>Your Calculated Daily Targets</Text>
              <Text style={{ fontSize: 15, color: '#222', marginTop: 4 }}>Calories: {targets.calories} kcal</Text>
              <Text style={{ fontSize: 15, color: '#222' }}>Protein: {targets.protein} g</Text>
              <Text style={{ fontSize: 15, color: '#222' }}>Fat: {targets.fat} g</Text>
            </View>

            <StyledButton title={loading ? 'Saving...' : 'Save & Continue'} onPress={handleSubmit} disabled={loading} />
            {error && <ErrorPopup message={error} onClose={() => setError(null)} />}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// --- Account Settings Screen ---
const AccountSettingsScreen = ({ navigation }: { navigation: any }) => {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [editProfile, setEditProfile] = useState<UserProfile | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [targets, setTargets] = useState({ calories: 0, protein: 0, fat: 0 });
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const userId = auth.currentUser?.uid;
        if (!userId) return;
        const profile = await getUserProfile(userId);
        if (profile) {
          setUserProfile(profile);
          setEditProfile(profile);
          setTargets({
            calories: profile.targetCalories || 0,
            protein: profile.targetProtein || 0,
            fat: profile.targetFat || 0,
          });
        }
      } catch (e) {
        setError('Could not load user profile.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  useEffect(() => {
    if (!editProfile) return;
    setTargets(
      calculateTargets({
        weight: Number(editProfile.currentWeight),
        height: Number(editProfile.height),
        age: Number(editProfile.age),
        gender: editProfile.gender,
        activityLevel: editProfile.activityLevel,
      })
    );
    setHasUnsavedChanges(true);
  }, [editProfile?.currentWeight, editProfile?.height, editProfile?.age, editProfile?.gender, editProfile?.activityLevel, editProfile?.stepGoal, editProfile?.caloriesBurnedGoal]);

  const handleSave = async () => {
    if (!editProfile) return;
    setLoading(true);
    try {
      await updateUserProfile(editProfile.userId, {
        ...editProfile,
        targetCalories: targets.calories,
        targetProtein: targets.protein,
        targetFat: targets.fat,
        stepGoal: editProfile.stepGoal,
        caloriesBurnedGoal: editProfile.caloriesBurnedGoal,
      });
      setUserProfile(editProfile);
      setIsEditing(false);
      setHasUnsavedChanges(false);
      setShowSuccessPopup(true);
      setTimeout(() => setShowSuccessPopup(false), 1500);
      navigation.setParams({ refresh: Date.now() }); // This triggers DashboardScreen to refresh and pick up new goals
    } catch (e) {
      setError('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <ActivityIndicator size="large" color={COLORS.primary} style={{ flex: 1, alignSelf: 'center' }} />;
  }

  if (!userProfile) {
    return <Text style={styles.errorText}>No profile found.</Text>;
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 60 : 0}
      >
        <ScrollView
          contentContainerStyle={{ flexGrow: 1, padding: 24, paddingBottom: 40 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 24, marginTop: 32 }}>
            <TouchableOpacity onPress={() => navigation.goBack()} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Text style={{ color: COLORS.primary, fontSize: 32, fontWeight: 'bold', padding: 8, marginRight: 8 }}>{'←'}</Text>
            </TouchableOpacity>
            <Text style={{ fontSize: 28, fontWeight: 'bold', color: COLORS.text }}>Account Settings</Text>
          </View>
          <Text style={styles.inputLabel}>First Name</Text>
          <StyledInput
            placeholder="First Name"
            value={editProfile?.firstName || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, firstName: text }); setHasUnsavedChanges(true); }}
          />
          <Text style={styles.inputLabel}>Last Name</Text>
          <StyledInput
            placeholder="Last Name"
            value={editProfile?.lastName || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, lastName: text }); setHasUnsavedChanges(true); }}
          />
          <Text style={styles.inputLabel}>Age</Text>
          <StyledInput
            placeholder="Age"
            value={editProfile?.age?.toString() || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, age: Number(text) }); setHasUnsavedChanges(true); }}
            keyboardType="numeric"
          />
          <Text style={styles.inputLabel}>Gender</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={editProfile?.gender || ''}
              onValueChange={(value: string) => { setEditProfile({ ...editProfile!, gender: value }); setHasUnsavedChanges(true); }}
              style={styles.picker}
              itemStyle={{ fontSize: 18 }}
            >
              <Picker.Item label="Select gender..." value="" />
              <Picker.Item label="Male" value="male" />
              <Picker.Item label="Female" value="female" />
              <Picker.Item label="Other" value="other" />
            </Picker>
          </View>
          <Text style={styles.inputLabel}>Daily Activity Level</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={editProfile?.activityLevel || 'sedentary'}
              onValueChange={(value: string) => { setEditProfile({ ...editProfile!, activityLevel: value }); setHasUnsavedChanges(true); }}
              style={styles.picker}
              itemStyle={{ fontSize: 18 }}
            >
              {ACTIVITY_LEVELS.map(l => (
                <Picker.Item key={l.value} label={l.label} value={l.value} />
              ))}
            </Picker>
          </View>
          <Text style={styles.inputLabel}>Current Weight (kg)</Text>
          <StyledInput
            placeholder="Current Weight (kg)"
            value={editProfile?.currentWeight?.toString() || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, currentWeight: Number(text) }); setHasUnsavedChanges(true); }}
            keyboardType="numeric"
          />
          <Text style={styles.inputLabel}>Goal Weight (kg)</Text>
          <StyledInput
            placeholder="Goal Weight (kg)"
            value={editProfile?.goalWeight?.toString() || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, goalWeight: Number(text) }); setHasUnsavedChanges(true); }}
            keyboardType="numeric"
          />
          <Text style={styles.inputLabel}>Height (cm)</Text>
          <StyledInput
            placeholder="Height (cm)"
            value={editProfile?.height?.toString() || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, height: Number(text) }); setHasUnsavedChanges(true); }}
            keyboardType="numeric"
          />
          <Text style={styles.inputLabel}>Dietary Preference</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={editProfile?.dietaryPreference || ''}
              onValueChange={(value: string) => { setEditProfile({ ...editProfile!, dietaryPreference: value }); setHasUnsavedChanges(true); }}
              style={styles.picker}
              itemStyle={{ fontSize: 18 }}
            >
              <Picker.Item label="Select preference..." value="" />
              <Picker.Item label="Vegetarian" value="vegetarian" />
              <Picker.Item label="Non Vegetarian" value="non-vegetarian" />
              <Picker.Item label="Vegan" value="vegan" />
              <Picker.Item label="Eggetarian" value="eggetarian" />
              <Picker.Item label="Pescatarian" value="pescatarian" />
              <Picker.Item label="Keto" value="keto" />
              <Picker.Item label="Other" value="other" />
            </Picker>
          </View>
          <Text style={styles.inputLabel}>Favourite Cuisine (optional)</Text>
          <StyledInput
            placeholder="Favourite Cuisine"
            value={editProfile?.favouriteCuisine || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, favouriteCuisine: text }); setHasUnsavedChanges(true); }}
          />
          <Text style={styles.inputLabel}>Allergies (optional)</Text>
          <StyledInput
            placeholder="Allergies"
            value={editProfile?.allergies || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, allergies: text }); setHasUnsavedChanges(true); }}
          />
          <Text style={styles.inputLabel}>Medical Conditions (optional)</Text>
          <StyledInput
            placeholder="Medical Conditions"
            value={editProfile?.medicalConditions || ''}
            onChangeText={text => { setEditProfile({ ...editProfile!, medicalConditions: text }); setHasUnsavedChanges(true); }}
          />
          <View style={{ marginVertical: 12 }}>
            <Text style={{ fontWeight: 'bold', color: '#888', fontSize: 16 }}>Your Calculated Daily Targets</Text>
            <Text style={{ fontSize: 15, color: '#222', marginTop: 4 }}>Calories: {targets.calories} kcal</Text>
            <Text style={{ fontSize: 15, color: '#222' }}>Protein: {targets.protein} g</Text>
            <Text style={{ fontSize: 15, color: '#222' }}>Fat: {targets.fat} g</Text>
          </View>
          <View style={{ marginVertical: 12 }}>
            <Text style={{ fontWeight: 'bold', color: '#888', fontSize: 16 }}>Daily Step Goal</Text>
            <View style={styles.pickerWrapper}>
              <Picker
                selectedValue={editProfile?.stepGoal ?? 10000}
                onValueChange={value => { setEditProfile({ ...editProfile!, stepGoal: value }); setHasUnsavedChanges(true); }}
                style={styles.picker}
                itemStyle={{ fontSize: 18 }}
              >
                {[...Array(20)].map((_, i) => (
                  <Picker.Item key={i} label={`${(i+1)*1000}`} value={(i+1)*1000} />
                ))}
              </Picker>
            </View>
          </View>
          <View style={{ marginVertical: 12 }}>
            <Text style={{ fontWeight: 'bold', color: '#888', fontSize: 16 }}>Daily Calories Burned Goal</Text>
            <View style={styles.pickerWrapper}>
              <Picker
                selectedValue={editProfile?.caloriesBurnedGoal ?? 0}
                onValueChange={value => { setEditProfile({ ...editProfile!, caloriesBurnedGoal: value }); setHasUnsavedChanges(true); }}
                style={styles.picker}
                itemStyle={{ fontSize: 18 }}
              >
                {[...Array(21)].map((_, i) => (
                  <Picker.Item key={i} label={`${i*100}`} value={i*100} />
                ))}
              </Picker>
            </View>
          </View>
          <StyledButton title="Save" onPress={handleSave} disabled={!hasUnsavedChanges || loading} />
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
        </ScrollView>
        {/* Success Popup: match LoginSettingsScreen style exactly */}
        <Modal
          visible={showSuccessPopup}
          animationType="fade"
          transparent
          onRequestClose={() => setShowSuccessPopup(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.successPopup}>
              <Text style={styles.successTitle}>Changes made successfully!</Text>
              <TouchableOpacity
                style={styles.bigCloseButton}
                onPress={() => setShowSuccessPopup(false)}
              >
                <Text style={styles.bigCloseButtonText}>Close</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export const ChatbotScreen = () => {
  const [messages, setMessages] = useState([
    { id: '1', text: 'Hello! How can I help you today?', sender: 'bot' }
  ]);
  const [inputText, setInputText] = useState('');
  const flatListRef = useRef<FlatList>(null);

  const handleSend = () => {
    if (inputText.trim().length > 0) {
      const newMessage = { id: Date.now().toString(), text: inputText, sender: 'user' };
      setMessages(prevMessages => [...prevMessages, newMessage]);
      setInputText('');

      setTimeout(() => {
        const botMessage = { id: Date.now().toString(), text: 'Hi', sender: 'bot' };
        setMessages(prevMessages => [...prevMessages, botMessage]);
      }, 1000);
    }
  };

  useEffect(() => {
    if (flatListRef.current) {
      flatListRef.current.scrollToEnd({ animated: true });
    }
  }, [messages]);

  const renderMessage = ({ item }: { item: { id: string, text: string; sender: string } }) => {
    const isUserMessage = item.sender === 'user';
    return (
      <View style={[
        styles.messageBubble,
        isUserMessage ? styles.userMessage : styles.botMessage
      ]}>
        <Text style={styles.messageText}>{item.text}</Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.chatbotContainer}>
      <KeyboardAvoidingView 
        style={{ flex: 1 }} 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={item => item.id}
          contentContainerStyle={{ paddingVertical: 10, paddingHorizontal: 10 }}
        />
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.chatInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type a message..."
            placeholderTextColor={COLORS.placeholder}
          />
          <TouchableOpacity onPress={handleSend} style={styles.sendButton}>
            <Send color={COLORS.primary} size={24} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export const LoginSettingsScreen = ({ navigation }: { navigation: any }) => {
  const [email, setEmail] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [emailPassword, setEmailPassword] = useState('');
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSuccess, setEmailSuccess] = useState(false);
  const [emailVerifyMsg, setEmailVerifyMsg] = useState<string | null>(null);

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);

  // Keep email in sync with Firebase user
  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      setEmail(user?.email || '');
    });
    return unsubscribe;
  }, []);

  // Change Email
  const handleChangeEmail = async () => {
    setEmailError(null);
    setEmailVerifyMsg(null);
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!newEmail || !emailPassword) {
      setEmailError('Please fill in all fields.');
      return;
    }
    if (!emailRegex.test(newEmail)) {
      setEmailError('Please enter a valid email address.');
      return;
    }
    setEmailLoading(true);
    try {
      const user = auth.currentUser;
      if (!user || !user.email) throw new Error('No user logged in');
      if (newEmail === user.email) {
        setEmailError('New email cannot be the same as your current email.');
        setEmailLoading(false);
        return;
      }
      // Re-authenticate
      const credential = firebase.auth.EmailAuthProvider.credential(user.email, emailPassword);
      await user.reauthenticateWithCredential(credential);
      // Set language code for email
      auth.languageCode = 'en';
      // ActionCodeSettings with Firebase Hosting domain
      const actionCodeSettings = {
        url: 'https://nutricious4u-63158.firebaseapp.com/email-change-complete',
        handleCodeInApp: true,
      };
      // Try verifyBeforeUpdateEmail
      if (user.verifyBeforeUpdateEmail) {
        await user.verifyBeforeUpdateEmail(newEmail, actionCodeSettings);
        setEmailVerifyMsg('A verification link has been sent to your new email address. Please check your inbox and spam/junk folder. If you do not receive the email, you can resend it or contact support.');
      } else {
        await user.updateEmail(newEmail);
        await user.sendEmailVerification(actionCodeSettings);
        setEmailVerifyMsg('Your email has been updated. Please verify your new email address.');
      }
      setEmailSuccess(true);
      setNewEmail('');
      setEmailPassword('');
    } catch (e) {
      console.log('[ChangeEmail] Error object:', e);
      setEmailError(getFirebaseErrorMessage(e));
      setEmailSuccess(false);
    } finally {
      setEmailLoading(false);
    }
  };

  // Resend verification email button
  const handleResendVerification = async () => {
    setEmailError(null);
    setEmailVerifyMsg(null);
    setEmailLoading(true);
    try {
      const user = auth.currentUser;
      if (!user || !user.email) throw new Error('No user logged in');
      // Set language for email
      auth.languageCode = 'en';
      const actionCodeSettings = {
        url: 'https://nutricious4u-63158.firebaseapp.com/email-change-complete',
        handleCodeInApp: true,
      };
      if (user.verifyBeforeUpdateEmail && newEmail) {
        await user.verifyBeforeUpdateEmail(newEmail, actionCodeSettings);
        setEmailVerifyMsg('A verification email has been resent. Please check your inbox and spam/junk folder.');
      } else if (newEmail) {
        await user.updateEmail(newEmail);
        await user.sendEmailVerification(actionCodeSettings);
        setEmailVerifyMsg('A verification email has been resent. Please check your inbox and spam/junk folder.');
      } else {
        setEmailError('Please enter the new email to resend verification.');
      }
    } catch (e) {
      console.error('handleResendVerification error:', e);
      const err = e as any;
      const code = err.code || err.errorCode || '';
      setEmailError(firebaseErrorMessages[code] || err.message || 'Failed to resend verification email. Please try again or contact support if the problem persists.');
    } finally {
      setEmailLoading(false);
    }
  };

  // Change Password
  const handleChangePassword = async () => {
    setPasswordError(null);
    if (!oldPassword || !newPassword || !confirmPassword) {
      setPasswordError('Please fill in all fields.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }
    if (oldPassword === newPassword) {
      setPasswordError('New password must be different from old password.');
      return;
    }
    setPasswordLoading(true);
    try {
      const user = auth.currentUser;
      if (!user || !user.email) throw new Error('No user logged in');
      const cred = EmailAuthProvider.credential(user.email, oldPassword);
      await user.reauthenticateWithCredential(cred);
      await user.updatePassword(newPassword);
      setPasswordSuccess(true);
      setShowSuccessPopup(true);
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      // Update saved password in AsyncStorage if Remember Me is enabled
      const savedEmail = await AsyncStorage.getItem('savedEmail');
      if (savedEmail) {
        await AsyncStorage.setItem('savedPassword', newPassword);
      }
    } catch (e: any) {
      console.log('Password change error:', e);
      const code = e.code || e.errorCode || '';
      if (code === 'auth/weak-password') {
        setPasswordError('Password is too weak. Please use a stronger password.');
      } else if (
        code === 'auth/wrong-password' ||
        code === 'auth/invalid-credential' ||
        code === 'auth/invalid-login-credentials'
      ) {
        setPasswordError('Invalid password.');
      } else if (code === 'auth/user-mismatch') {
        setPasswordError('Invalid credentials. Please try again.');
      } else if (code === 'auth/requires-recent-login') {
        setPasswordError('Please log in again and try this action.');
      } else if (typeof e === 'string' && e.toLowerCase().includes('password')) {
        setPasswordError('Invalid password.');
      } else {
        setPasswordError('Failed to update password. Please try again.');
      }
    } finally {
      setPasswordLoading(false);
    }
  };

  // Listen for email verification and update backend (Firestore) after verification
  useEffect(() => {
    let lastEmail = email;
    let lastVerified = auth.currentUser?.emailVerified;
    const unsubscribe = auth.onAuthStateChanged(async (user) => {
      if (
        user &&
        user.email &&
        user.uid &&
        user.email !== lastEmail &&
        user.emailVerified &&
        !lastVerified // Only trigger on transition from unverified to verified
      ) {
        try {
          await updateUserProfile(user.uid, { email: user.email });
          lastEmail = user.email;
          lastVerified = true;
          setEmailSuccess(true);
          setShowSuccessPopup(true);
        } catch (err) {
          setEmailError('Email verified, but failed to update backend. Please contact support.');
          setEmailSuccess(false);
          setShowSuccessPopup(false);
          console.error('Failed to update backend with new email:', err);
        }
      } else {
        lastVerified = user?.emailVerified;
      }
    });
    return unsubscribe;
  }, [email]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 60 : 0}
      >
        <KeyboardAwareScrollView
          contentContainerStyle={{ flexGrow: 1, padding: 24, paddingBottom: 40 }}
          style={{ flex: 1 }}
          keyboardShouldPersistTaps="handled"
          enableOnAndroid={true}
          extraScrollHeight={24}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 24, marginTop: 32 }}>
            <TouchableOpacity onPress={() => navigation.goBack()} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Text style={{ color: COLORS.primary, fontSize: 32, fontWeight: 'bold', padding: 8, marginRight: 8 }}>{'←'}</Text>
            </TouchableOpacity>
            <Text style={{ fontSize: 28, fontWeight: 'bold', color: COLORS.text }}>Login Settings</Text>
          </View>

          {/* Show current email */}
          <Text style={styles.inputLabel}>Current Email</Text>
          <Text style={{ marginBottom: 12, fontSize: 16, color: COLORS.text }}>{email || 'Not available'}</Text>

          {/* Change Password Section */}
          <Text style={[styles.sectionTitle, { marginTop: 32 }]}>Change Password</Text>
          <Text style={styles.inputLabel}>Old Password</Text>
          <TextInput
            style={styles.input}
            value={oldPassword}
            onChangeText={setOldPassword}
            placeholder="Enter old password"
            secureTextEntry
          />
          <Text style={styles.inputLabel}>New Password</Text>
          <View style={styles.passwordInputWrapper}>
            <TextInput
              placeholder="New Password"
              value={newPassword}
              onChangeText={setNewPassword}
              secureTextEntry={!showNewPassword}
              style={{ flex: 1, paddingVertical: 14, fontSize: 16, color: COLORS.text, backgroundColor: 'transparent', borderWidth: 0 }}
            />
            <TouchableOpacity onPress={() => setShowNewPassword((v) => !v)} style={styles.eyeIcon}>
              {showNewPassword ? <EyeOff color={COLORS.placeholder} size={22} /> : <Eye color={COLORS.placeholder} size={22} />}
            </TouchableOpacity>
          </View>
          <Text style={styles.inputLabel}>Confirm New Password</Text>
          <View style={styles.passwordInputWrapper}>
            <TextInput
              placeholder="Confirm New Password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showConfirmPassword}
              style={{ flex: 1, paddingVertical: 14, fontSize: 16, color: COLORS.text, backgroundColor: 'transparent', borderWidth: 0 }}
            />
            <TouchableOpacity onPress={() => setShowConfirmPassword((v) => !v)} style={styles.eyeIcon}>
              {showConfirmPassword ? <EyeOff color={COLORS.placeholder} size={22} /> : <Eye color={COLORS.placeholder} size={22} />}
            </TouchableOpacity>
          </View>
          <TouchableOpacity style={[styles.button, { marginTop: 8 }]} onPress={handleChangePassword} disabled={passwordLoading}>
            <Text style={styles.buttonText}>{passwordLoading ? 'Saving...' : 'Save'}</Text>
          </TouchableOpacity>
          {passwordError && <Text style={styles.errorText}>{passwordError}</Text>}
        </KeyboardAwareScrollView>
        {/* Success Popup */}
        <Modal
          visible={showSuccessPopup}
          animationType="fade"
          transparent
          onRequestClose={() => setShowSuccessPopup(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.successPopup}>
              <Text style={styles.successTitle}>Changes made successfully!</Text>
              <TouchableOpacity
                style={styles.bigCloseButton}
                onPress={() => setShowSuccessPopup(false)}
              >
                <Text style={styles.bigCloseButtonText}>Close</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// --- Notification Settings Screen ---
const NOTIFICATIONS_KEY = 'userNotifications';

const NotificationSettingsScreen = ({ navigation }: { navigation: any }) => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'add' | 'edit'>('add');
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [time, setTime] = useState(new Date());
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [error, setError] = useState('');

  const DEFAULT_NOTIFICATIONS: { message: string; hour: number; minute: number }[] = [
    { message: "Good morning, don't forget to have a glass of water!!", hour: 8, minute: 0 },
    { message: "It's lunch time", hour: 14, minute: 0 },
    { message: "Time for a healthy snack!", hour: 17, minute: 0 },
    { message: "Time to wind down. Prepare for a restful sleep!", hour: 22, minute: 0 },
  ];

  // Helper to convert IST hour/minute to local time
  function getLocalTimeFromIST(hour: number, minute: number): Date {
    const now = new Date();
    // IST is UTC+5:30
    const istOffset = 5.5 * 60; // in minutes
    const localOffset = -now.getTimezoneOffset(); // in minutes
    const diff = localOffset - istOffset;
    const localDate = new Date(now);
    localDate.setHours(hour, minute, 0, 0);
    localDate.setMinutes(localDate.getMinutes() + diff);
    return localDate;
  }

  useEffect(() => {
    loadNotifications();
    // Request notification permissions only
    (async () => {
      const { status } = await Notifications.getPermissionsAsync();
      if (status !== 'granted') {
        await Notifications.requestPermissionsAsync();
        console.log('[Notifications] Requested notification permissions.');
      } else {
        console.log('[Notifications] Notification permissions already granted.');
      }
    })();
  }, []);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await AsyncStorage.getItem(NOTIFICATIONS_KEY);
      let parsed = [];
      if (data) {
        const all = JSON.parse(data);
        parsed = all.filter((n: any) => n.message && n.message.trim());
        setNotifications(parsed);
        // Cancel scheduled notifications for removed/blank entries
        const removed = all.filter((n: any) => !n.message || !n.message.trim());
        for (const n of removed) {
          if (n.scheduledId) {
            try { 
              await Notifications.cancelScheduledNotificationAsync(n.scheduledId); 
              console.log('[Notifications] Cancelled orphaned scheduledId:', n.scheduledId);
            } catch (e) {
              console.log('[Notifications] Error cancelling orphaned scheduledId:', n.scheduledId, e);
            }
          }
        }
        // Save back filtered list if any were removed
        if (parsed.length !== all.length) {
          await AsyncStorage.setItem(NOTIFICATIONS_KEY, JSON.stringify(parsed));
          console.log('[Notifications] Cleaned AsyncStorage, removed blank notifications.');
        }
        // If there are notifications, show them
        if (parsed.length > 0) {
          setNotifications(parsed);
        } else {
          // No notifications: inject defaults
          const defaults: any[] = [];
          for (const def of DEFAULT_NOTIFICATIONS) {
            const localTime = getLocalTimeFromIST(def.hour, def.minute);
            let scheduledId = null;
            // @ts-ignore
            const trigger: any = {
              type: 'calendar',
              hour: localTime.getHours(),
              minute: localTime.getMinutes(),
              repeats: true,
            };
            try {
              scheduledId = await Notifications.scheduleNotificationAsync({
                content: { title: 'Reminder', body: def.message },
                trigger,
              });
            } catch (e) {}
            defaults.push({
              id: Date.now().toString() + Math.random().toString().slice(2, 8),
              message: def.message,
              time: localTime.toISOString(),
              scheduledId,
            });
          }
          setNotifications(defaults);
          await AsyncStorage.setItem(NOTIFICATIONS_KEY, JSON.stringify(defaults));
        }
      } else {
        // No notifications at all: inject defaults
        const defaults: any[] = [];
        for (const def of DEFAULT_NOTIFICATIONS) {
          const localTime = getLocalTimeFromIST(def.hour, def.minute);
          let scheduledId = null;
          // @ts-ignore
          const trigger: any = {
            type: 'calendar',
            hour: localTime.getHours(),
            minute: localTime.getMinutes(),
            repeats: true,
          };
          try {
            scheduledId = await Notifications.scheduleNotificationAsync({
              content: { title: 'Reminder', body: def.message },
              trigger,
            });
          } catch (e) {}
          defaults.push({
            id: Date.now().toString() + Math.random().toString().slice(2, 8),
            message: def.message,
            time: localTime.toISOString(),
            scheduledId,
          });
        }
        setNotifications(defaults);
        await AsyncStorage.setItem(NOTIFICATIONS_KEY, JSON.stringify(defaults));
      }
    } catch (e) {
      setNotifications([]);
    }
    setLoading(false);
  };

  const saveNotifications = async (newList: any[]) => {
    setNotifications(newList);
    await AsyncStorage.setItem(NOTIFICATIONS_KEY, JSON.stringify(newList));
    console.log('[Notifications] Saved to AsyncStorage:', newList);
  };

  const openAddModal = () => {
    setModalMode('add');
    setCurrentId(null);
    setMessage('');
    setTime(new Date());
    setShowModal(true);
    setError('');
  };

  const openEditModal = (notif: any) => {
    setModalMode('edit');
    setCurrentId(notif.id);
    setMessage(notif.message);
    setTime(new Date(notif.time));
    setShowModal(true);
    setError('');
  };

  const handleDelete = async (id: string) => {
    const notif = notifications.find(n => n.id === id);
    if (notif && notif.scheduledId) {
      try {
        await Notifications.cancelScheduledNotificationAsync(notif.scheduledId);
        console.log('[Notifications] Cancelled scheduledId on delete:', notif.scheduledId);
      } catch (e) {
        console.log('[Notifications] Error cancelling scheduledId on delete:', notif.scheduledId, e);
      }
    }
    const newList = notifications.filter(n => n.id !== id);
    await saveNotifications(newList);
    console.log('[Notifications] Deleted notification with id:', id);
  };

  const handleSave = async () => {
    if (!message.trim()) {
      setError('Message cannot be empty');
      console.log('[Notifications] Tried to save blank message.');
      return;
    }
    // Use selected hour/minute, but keep today's date (local time)
    const now = new Date();
    const selected = new Date(now);
    selected.setHours(time.getHours());
    selected.setMinutes(time.getMinutes());
    selected.setSeconds(0);
    selected.setMilliseconds(0);
    let scheduledId = null;
    let trigger;
    if (Platform.OS === 'ios') {
      // iOS supports calendar triggers
      trigger = {
        type: 'calendar',
        hour: selected.getHours(),
        minute: selected.getMinutes(),
        repeats: true,
      };
    } else {
      // Android: schedule for the next occurrence of the selected time
      let next = new Date();
      next.setHours(time.getHours());
      next.setMinutes(time.getMinutes());
      next.setSeconds(0);
      next.setMilliseconds(0);
      if (next <= now) {
        // If the time has already passed today, schedule for tomorrow
        next.setDate(next.getDate() + 1);
      }
      // Calculate seconds until next occurrence
      const seconds = Math.max(1, Math.floor((next.getTime() - Date.now()) / 1000));
      // Use 'timeInterval' as the type for Android
      trigger = {
        type: 'timeInterval',
        seconds,
        repeats: false
      } as any;
    }
    try {
      scheduledId = await Notifications.scheduleNotificationAsync({
        content: { title: 'Reminder', body: message },
        trigger,
      });
      console.log('[Notifications] Scheduled notification:', { scheduledId, message, trigger });
      if (Platform.OS === 'android') {
        // On Android, set up a listener to reschedule for the next day when notification is received
        Notifications.addNotificationReceivedListener(async (notification) => {
          if (notification.request.content.body === message) {
            let next = new Date();
            next.setDate(next.getDate() + 1);
            next.setHours(time.getHours());
            next.setMinutes(time.getMinutes());
            next.setSeconds(0);
            next.setMilliseconds(0);
            const seconds = Math.max(1, Math.floor((next.getTime() - Date.now()) / 1000));
            await Notifications.scheduleNotificationAsync({
              content: { title: 'Reminder', body: message },
              trigger: {
                type: 'timeInterval',
                seconds,
                repeats: false
              } as any,
            });
            console.log('[Notifications] Rescheduled daily notification for next day:', next);
          }
        });
      }
    } catch (e) {
      setError('Failed to schedule notification');
      console.log('[Notifications] Error scheduling notification:', e);
      return;
    }
    let newList;
    if (modalMode === 'add') {
      newList = [
        ...notifications,
        { id: Date.now().toString(), message, time: selected.toISOString(), scheduledId },
      ];
      console.log('[Notifications] Added new notification:', { message, time: selected.toISOString(), scheduledId });
    } else {
      // Cancel old scheduled notification
      const old = notifications.find(n => n.id === currentId);
      if (old && old.scheduledId) {
        try {
          await Notifications.cancelScheduledNotificationAsync(old.scheduledId);
          console.log('[Notifications] Cancelled old scheduledId on edit:', old.scheduledId);
        } catch (e) {
          console.log('[Notifications] Error cancelling old scheduledId on edit:', old.scheduledId, e);
        }
      }
      newList = notifications.map(n =>
        n.id === currentId
          ? { ...n, message, time: selected.toISOString(), scheduledId }
          : n
      );
      console.log('[Notifications] Edited notification:', { id: currentId, message, time: selected.toISOString(), scheduledId });
    }
    await saveNotifications(newList);
    setShowModal(false);
  };

  const renderItem = ({ item }: { item: any }) => (
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: COLORS.background, borderRadius: 16, padding: 16, marginVertical: 8, shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 4, elevation: 2 }}>
      <View style={{ flex: 1 }}>
        <Text style={{ color: COLORS.text, fontSize: 18, fontWeight: 'bold' }}>{item.message}</Text>
        <Text style={{ color: COLORS.placeholder, fontSize: 15, marginTop: 4 }}>{new Date(item.time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST</Text>
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <TouchableOpacity onPress={() => openEditModal(item)} style={{ marginRight: 16 }}>
          <Pencil color={COLORS.primary} size={22} />
        </TouchableOpacity>
        <TouchableOpacity onPress={() => handleDelete(item.id)}>
          <Trash2 color={COLORS.error} size={22} />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={[styles.container, { paddingTop: 32, paddingHorizontal: 16 }]}> 
      <View style={styles.settingsContainer}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 24 }}>
          <TouchableOpacity onPress={() => navigation.goBack()} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Text style={{ color: COLORS.primary, fontSize: 32, fontWeight: 'bold', padding: 8, marginRight: 8 }}>{'←'}</Text>
          </TouchableOpacity>
          <Text style={[styles.screenTitle, { flex: 1, textAlign: 'center', marginLeft: -36 }]}>Notification Settings</Text>
          <View style={{ width: 40 }} />
        </View>
        {loading ? (
          <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
        ) : notifications.length === 0 ? (
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <Text style={{ color: COLORS.placeholder, fontSize: 18, textAlign: 'center' }}>
              You have no notifications yet.
            </Text>
            <TouchableOpacity style={styles.addNotificationButton} onPress={openAddModal}>
              <Text style={styles.addNotificationButtonText}>Add Notification</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            <FlatList
              data={notifications}
              keyExtractor={item => item.id}
              renderItem={renderItem}
              ListFooterComponent={
                <TouchableOpacity style={styles.addNotificationButton} onPress={openAddModal}>
                  <Text style={styles.addNotificationButtonText}>Add Notification</Text>
                </TouchableOpacity>
              }
              contentContainerStyle={{ paddingBottom: 0 }}
            />
          </>
        )}
        {/* Add/Edit Modal */}
        <Modal
          visible={showModal}
          animationType="slide"
          transparent
          onRequestClose={() => setShowModal(false)}
        >
          <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
            <View style={styles.modalOverlay}>
              <View style={styles.modalContainer}>
                <Text style={styles.modalTitle}>{modalMode === 'add' ? 'Add Notification' : 'Edit Notification'}</Text>
                <Text style={styles.modalLabel}>Message</Text>
                <TextInput
                  style={styles.modalInput}
                  value={message}
                  onChangeText={setMessage}
                  placeholder="Enter your custom message"
                  maxLength={100}
                />
                <Text style={styles.modalLabel}>Time (IST)</Text>
                <TouchableOpacity
                  style={[styles.modalInput, { justifyContent: 'center', height: 48 }]}
                  onPress={() => setShowTimePicker(true)}
                >
                  <Text style={{ color: COLORS.text, fontSize: 16 }}>
                    {time.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST
                  </Text>
                </TouchableOpacity>
                {showTimePicker && (
                  <DateTimePicker
                    value={time}
                    mode="time"
                    is24Hour={true}
                    display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                    onChange={(event, selectedDate) => {
                      setShowTimePicker(false);
                      if (selectedDate) setTime(selectedDate);
                    }}
                  />
                )}
                {error ? <Text style={{ color: COLORS.error, marginTop: 8 }}>{error}</Text> : null}
                <View style={styles.modalButtonRow}>
                  <TouchableOpacity
                    style={[styles.modalButton, { backgroundColor: COLORS.primary }]}
                    onPress={handleSave}
                  >
                    <Text style={styles.modalButtonText}>{modalMode === 'add' ? 'Add' : 'Save'}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.modalButton, { backgroundColor: COLORS.error }]}
                    onPress={() => setShowModal(false)}
                  >
                    <Text style={styles.modalButtonText}>Cancel</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </Modal>
      </View>
    </SafeAreaView>
  );
};

// --- Rectangle Summary Widget ---
const SummaryWidget = ({ todayData, targets, stepsToday, burnedToday, onPress }: any) => {
  // Define unique, dark/vibrant colors for each label
  const labelColors = {
    Calories: '#B91C1C', // dark red
    Protein: '#0E7490', // dark teal
    Fat: '#B45309',     // dark amber
    Steps: '#065F46',   // dark green
    Burned: '#A21CAF',  // dark purple
  };
  const items = [
    { label: 'Calories', value: safeNumber(todayData.calories), target: targets.calories, color: COLORS.energy, labelColor: labelColors.Calories },
    { label: 'Protein', value: safeNumber(todayData.protein), target: targets.protein, color: COLORS.protein, labelColor: labelColors.Protein },
    { label: 'Fat', value: safeNumber(todayData.fat), target: targets.fat, color: COLORS.fat, labelColor: labelColors.Fat },
    { label: 'Steps', value: stepsToday, target: targets.steps, color: COLORS.primaryDark, labelColor: labelColors.Steps },
    { label: 'Burned', value: safeNumber(burnedToday), target: targets.burned, color: COLORS.streakActive, labelColor: labelColors.Burned },
  ];
  return (
    <TouchableOpacity activeOpacity={0.85} onPress={onPress} style={styles.summaryWidgetContainer}>
      <LinearGradient
        colors={[COLORS.lightGreen, COLORS.white]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.summaryWidgetBg}
      >
        {items.map((item, idx) => {
          const progress = item.target ? Math.min(1, item.value / item.target) : 0;
          return (
            <View key={item.label} style={styles.summaryWidgetRow}>
              <Text style={[styles.summaryWidgetLabel, { color: item.labelColor }]}>{item.label}</Text>
              <View style={styles.summaryWidgetBarBg}>
                <View style={[styles.summaryWidgetBar, { backgroundColor: item.color, width: `${progress * 100}%` }]} />
              </View>
            </View>
          );
        })}
      </LinearGradient>
    </TouchableOpacity>
  );
};

// --- Tracking Details Screen ---
const TrackingDetailsScreen = ({ navigation, route }: { navigation: any, route: any }) => {
  const { summary, stepsToday, burnedToday, userProfile, workoutSummary } = route.params || {};
  
  // Get targets from userProfile if available
  const targetCalories = userProfile?.targetCalories || 2000;
  const targetProtein = userProfile?.targetProtein || 150;
  const targetFat = userProfile?.targetFat || 65;
  const targetSteps = userProfile?.stepGoal ?? 10000;
  const targetBurned = userProfile?.caloriesBurnedGoal ?? 500;

  // --- Build last 7 days (rolling window) ---
  const today = new Date();
  const last7Dates: string[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    last7Dates.push(d.toISOString().slice(0, 10)); // 'YYYY-MM-DD'
  }
  // Map summary.history to a lookup by date
  const historyByDate: { [date: string]: any } = {};
  (summary?.history || []).forEach((item: any) => {
    if (item.day) {
      historyByDate[item.day] = item;
    }
  });
  // Build data arrays for each metric
  const caloriesData = last7Dates.map(date => ({ value: historyByDate[date]?.calories || 0 }));
  const proteinData = last7Dates.map(date => ({ value: historyByDate[date]?.protein || 0 }));
  const fatData = last7Dates.map(date => ({ value: historyByDate[date]?.fat || 0 }));
  const stepsData = last7Dates.map((date, idx) => ({ value: idx === 6 ? stepsToday : (historyByDate[date]?.steps || 0) }));
  // Add burnedData from workoutSummary if available
  const burnedData = (route.params?.workoutSummary?.history || []).map((item: any) => ({ value: item.calories || 0 }));
  while (burnedData.length < 7) burnedData.unshift({ value: 0 });
  // X-axis labels (DD/MM)
  const xLabels = last7Dates.map(date => {
    const d = new Date(date);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit' });
  });

  // Chart colors
  const chartColors = {
    calories: '#FF6B6B',
    protein: '#4ECDC4', 
    fat: '#FFD93D',
    steps: '#34D399',
    burned: '#FFA500'
  };

  const renderChart = (data: any[], title: string, color: string, target: number, xLabels: string[]) => {
    // Ensure we have exactly 7 data points
    const chartData = data.slice(0, 7);
    while (chartData.length < 7) {
      chartData.push({ value: 0 });
    }
    
    // Set specific max values for different chart types
    let maxValue, yLabels;
    if (title.includes('Calories')) {
      maxValue = 3000;
      yLabels = [0, 500, 1000, 1500, 2000, 2500, 3000];
    } else if (title.includes('Protein')) {
      maxValue = Math.max(...chartData.map(d => d.value), target) * 1.2;
      yLabels = [0, Math.round(maxValue/4), Math.round(maxValue/2), Math.round(maxValue*3/4), Math.round(maxValue)];
    } else if (title.includes('Fat')) {
      maxValue = Math.max(...chartData.map(d => d.value), target) * 1.2;
      yLabels = [0, Math.round(maxValue/4), Math.round(maxValue/2), Math.round(maxValue*3/4), Math.round(maxValue)];
    } else if (title.includes('Steps')) {
      maxValue = 15000;
      yLabels = [0, 3000, 6000, 9000, 12000, 15000];
    } else {
      maxValue = Math.max(...chartData.map(d => d.value), target) * 1.2;
      yLabels = [0, Math.round(maxValue/4), Math.round(maxValue/2), Math.round(maxValue*3/4), Math.round(maxValue)];
    }
    
    const chartHeight = 140;
    const chartWidth = 260;
    const yAxisWidth = 40;
    
    return (
      <View style={styles.chartContainer}>
        <Text style={[styles.chartTitle, { color }]}>{title}</Text>
        <View style={styles.chartArea}>
          {/* Y-axis labels */}
          <View style={styles.yAxis}>
            {yLabels.map((label, index) => (
              <Text key={index} style={styles.yAxisLabel}>
                {label >= 1000 ? `${label/1000}k` : label}
              </Text>
            ))}
          </View>
          {/* Chart content */}
          <View style={[styles.chartContent, { width: chartWidth }]}> 
            {/* Goal line (dotted) */}
            <View style={[styles.goalLine, { 
              top: chartHeight - (target / maxValue) * chartHeight,
              borderColor: color,
              borderWidth: 2,
              borderStyle: 'dashed',
              backgroundColor: 'transparent',
              width: chartWidth,
            }]} />
            {/* Trend line */}
            <Svg width={chartWidth} height={chartHeight} style={styles.trendLine}>
              <Path
                d={chartData.map((item: any, index: number) => {
                  let x = (index / (chartData.length - 1)) * chartWidth;
                  let y = chartHeight - (item.value / maxValue) * chartHeight;
                  // Clamp x/y to stay inside chart
                  x = Math.max(4, Math.min(chartWidth - 4, x));
                  y = Math.max(4, Math.min(chartHeight - 4, y));
                  return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
                }).join(' ')}
                stroke={color}
                strokeWidth={2}
                fill="none"
              />
            </Svg>
            {/* Data points */}
            {chartData.map((item: any, index: number) => {
              let x = (index / (chartData.length - 1)) * chartWidth;
              let y = chartHeight - (item.value / maxValue) * chartHeight;
              // Clamp x/y to stay inside chart
              x = Math.max(4, Math.min(chartWidth - 4, x));
              y = Math.max(4, Math.min(chartHeight - 4, y));
              return (
                <View key={index} style={[styles.dataPoint, { 
                  left: x - 4,
                  top: y - 4,
                  backgroundColor: color,
                  width: 8,
                  height: 8,
                  borderRadius: 4
                }]} />
              );
            })}
            {/* X-axis labels */}
            <View style={[styles.xAxis, { width: chartWidth, left: 0, marginLeft: 0, paddingHorizontal: 0, paddingLeft: 0, position: 'absolute', bottom: -40 }]}> 
              {xLabels.map((label, index) => (
                <Text key={index} style={styles.xAxisLabel}>
                  {label}
                </Text>
              ))}
            </View>
          </View>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { paddingHorizontal: 16, paddingTop: 50 }]}> 
      <View style={styles.headerContainer}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 4, minWidth: 40, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 22, color: COLORS.primaryDark }}>{'<'} </Text>
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Consumption</Text>
        <View style={{ minWidth: 40 }} />
      </View>
      <ScrollView style={{ marginTop: 16 }}>
        {/* Current Status Cards */}
        <View style={styles.statusGrid}>
          <View style={styles.statusCard}>
            <Text style={[styles.statusLabel, { color: chartColors.calories }]}>Calories</Text>
            <Text style={styles.statusValue}>{caloriesData[6]?.value || 0} / {targetCalories}</Text>
          </View>
          <View style={styles.statusCard}>
            <Text style={[styles.statusLabel, { color: chartColors.protein }]}>Protein</Text>
            <Text style={styles.statusValue}>{proteinData[6]?.value || 0} / {targetProtein}g</Text>
          </View>
          <View style={styles.statusCard}>
            <Text style={[styles.statusLabel, { color: chartColors.fat }]}>Fat</Text>
            <Text style={styles.statusValue}>{fatData[6]?.value || 0} / {targetFat}g</Text>
          </View>
          <View style={styles.statusCard}>
            <Text style={[styles.statusLabel, { color: chartColors.steps }]}>Steps</Text>
            <Text style={styles.statusValue}>{stepsToday} / {targetSteps}</Text>
          </View>
          <View style={styles.statusCard}>
            <Text style={[styles.statusLabel, { color: chartColors.burned }]}>Burned</Text>
            <Text style={styles.statusValue}>{burnedToday} / {targetBurned}</Text>
          </View>
        </View>

        {/* Charts */}
        {renderChart(
          caloriesData,
          'Calories Trend',
          chartColors.calories,
          targetCalories,
          xLabels
        )}
        {renderChart(
          proteinData,
          'Protein Trend', 
          chartColors.protein,
          targetProtein,
          xLabels
        )}
        {renderChart(
          fatData,
          'Fat Trend',
          chartColors.fat, 
          targetFat,
          xLabels
        )}
        {renderChart(
          stepsData,
          'Steps Trend',
          chartColors.steps,
          targetSteps,
          xLabels
        )}
        {renderChart(burnedData, 'Calories Burned', chartColors.burned, targetBurned, xLabels)}
      </ScrollView>
    </SafeAreaView>
  );
};

// --- Routine Screen ---
const RoutineScreen = ({ navigation }: { navigation: any }) => {
  const userId = auth.currentUser?.uid;
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingRoutine, setEditingRoutine] = useState<Routine | null>(null);
  const [routineName, setRoutineName] = useState('');
  const [routineItems, setRoutineItems] = useState<RoutineItem[]>([]);
  const [itemType, setItemType] = useState<'food' | 'workout'>('food');
  const [itemName, setItemName] = useState('');
  const [itemQuantity, setItemQuantity] = useState('');
  const [itemError, setItemError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loggingId, setLoggingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const fetchRoutines = async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      console.log('[Routine] Fetching routines for user:', userId);
      const data = await listRoutines(userId);
      setRoutines(data);
    } catch (e: any) {
      console.error('[Routine] Failed to load routines:', e);
      setError('Failed to load routines. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRoutines();
    // eslint-disable-next-line
  }, [userId]);

  const openCreateModal = () => {
    setEditingRoutine(null);
    setRoutineName('');
    setRoutineItems([]);
    setShowModal(true);
  };

  const openEditModal = (routine: Routine) => {
    setEditingRoutine(routine);
    setRoutineName(routine.name);
    setRoutineItems(routine.items);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setRoutineName('');
    setRoutineItems([]);
    setEditingRoutine(null);
    setItemName('');
    setItemQuantity('');
    setItemError(null);
  };

  const handleAddItem = () => {
    if (!itemName.trim()) {
      setItemError('Enter a name');
      return;
    }
    if (!itemQuantity.trim()) {
      setItemError(itemType === 'food' ? 'Enter serving size' : 'Enter duration');
      return;
    }
    setRoutineItems([...routineItems, { type: itemType, name: itemName.trim(), quantity: itemQuantity.trim() }]);
    setItemName('');
    setItemQuantity('');
    setItemError(null);
  };

  const handleRemoveItem = (idx: number) => {
    setRoutineItems(routineItems.filter((_, i) => i !== idx));
  };

  const handleSaveRoutine = async () => {
    if (!routineName.trim()) {
      setItemError('Enter a routine name');
      return;
    }
    if (routineItems.length === 0) {
      setItemError('Add at least one food or workout');
      return;
    }
    setSaving(true);
    try {
      if (editingRoutine) {
        console.log('[Routine] Updating routine:', editingRoutine.id, routineName, routineItems);
        await updateRoutine(userId!, editingRoutine.id, { name: routineName, items: routineItems });
        setSuccessMessage('Routine updated successfully!');
      } else {
        console.log('[Routine] Creating routine:', routineName, routineItems);
        await createRoutine(userId!, { name: routineName, items: routineItems });
        setSuccessMessage('Routine created successfully!');
      }
      setShowSuccess(true);
      closeModal();
      fetchRoutines();
    } catch (e: any) {
      console.error('[Routine] Failed to save routine:', e);
      setItemError('Failed to save routine. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteRoutine = async (routineId: string) => {
    setDeletingId(routineId);
    try {
      console.log('[Routine] Deleting routine:', routineId);
      await deleteRoutine(userId!, routineId);
      setSuccessMessage('Routine deleted successfully!');
      setShowSuccess(true);
      fetchRoutines();
    } catch (e: any) {
      console.error('[Routine] Failed to delete routine:', e);
      setError('Failed to delete routine. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleLogRoutine = async (routineId: string) => {
    setLoggingId(routineId);
    try {
      console.log('[Routine] Logging routine:', routineId);
      await logRoutine(userId!, routineId);
      setSuccessMessage('Routine logged successfully!');
      setShowSuccess(true);
      fetchRoutines();
      // Trigger dashboard refresh
      navigation.navigate('Main', { screen: 'Dashboard', params: { refresh: Date.now() } });
    } catch (e: any) {
      console.error('[Routine] Failed to log routine:', e);
      setError('Failed to log routine. Please try again.');
    } finally {
      setLoggingId(null);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { paddingHorizontal: 16, paddingTop: 50 }]}> 
      <View style={styles.headerContainer}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 4, minWidth: 40, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 22, color: COLORS.primaryDark }}>{'<'} </Text>
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Routine</Text>
        <View style={{ minWidth: 40 }} />
      </View>
      {loading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : error ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <Text style={styles.errorText}>{error}</Text>
          <StyledButton title="Retry" onPress={fetchRoutines} />
        </View>
      ) : routines.length === 0 ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <Text style={{ fontSize: 18, color: COLORS.placeholder, textAlign: 'center' }}>No routines yet. Create your first routine!</Text>
        </View>
      ) : (
        <FlatList
          data={routines}
          keyExtractor={item => item.id}
          refreshing={refreshing}
          onRefresh={() => { setRefreshing(true); fetchRoutines(); }}
          renderItem={({ item }) => (
            <View style={{ backgroundColor: COLORS.white, borderRadius: 18, padding: 18, marginBottom: 14, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 6, elevation: 2 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
                <Text style={{ fontSize: 22, fontWeight: 'bold', color: COLORS.text, flex: 1 }}>{item.name}</Text>
                <TouchableOpacity onPress={() => openEditModal(item)} style={{ marginRight: 12 }}>
                  <Pencil color={COLORS.primaryDark} size={26} />
                </TouchableOpacity>
                <TouchableOpacity onPress={() => handleDeleteRoutine(item.id)} disabled={deletingId === item.id} style={{ padding: 8 }}>
                  {deletingId === item.id ? <ActivityIndicator size={22} color={COLORS.error} /> : <Trash2 color={COLORS.error} size={28} />}
                </TouchableOpacity>
              </View>
              <View style={{ flexDirection: 'row', marginBottom: 8 }}>
                <Text style={{ color: COLORS.energy, fontWeight: 'bold', marginRight: 12 }}>Calories: {Math.round(item.calories)}</Text>
                <Text style={{ color: COLORS.protein, fontWeight: 'bold', marginRight: 12 }}>Protein: {Math.round(item.protein)}</Text>
                <Text style={{ color: COLORS.fat, fontWeight: 'bold', marginRight: 12 }}>Fat: {Math.round(item.fat)}</Text>
                <Text style={{ color: COLORS.streakActive, fontWeight: 'bold' }}>Burned: {Math.round(item.burned)}</Text>
              </View>
              <View style={{ marginBottom: 8 }}>
                {item.items.map((it, idx) => (
                  <View key={idx} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8, paddingVertical: 8, paddingHorizontal: 8, backgroundColor: '#F7F7FA', borderRadius: 10 }}>
                    <Text style={{ color: COLORS.text, fontSize: 18, flex: 1, fontWeight: '500' }}>
                      {it.type === 'food' ? '🍎' : '🏋️‍♂️'} {it.name} {it.quantity ? `(${it.quantity}${it.type === 'food' ? 'g' : ' min'})` : ''}
                    </Text>
                    <TouchableOpacity onPress={() => {}} disabled style={{ opacity: 0.3 }}>
                      <Trash2 color={COLORS.error} size={24} />
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
              <StyledButton
                title={loggingId === item.id ? 'Logging...' : 'Log Routine'}
                onPress={() => handleLogRoutine(item.id)}
                disabled={loggingId === item.id}
                style={{ marginTop: 4, borderRadius: 12, backgroundColor: COLORS.primaryDark }}
              />
            </View>
          )}
          contentContainerStyle={{ paddingBottom: 120 }}
        />
      )}
      {/* Create Routine Button at Bottom */}
      <View style={{ position: 'absolute', bottom: 32, left: 0, right: 0, alignItems: 'center', zIndex: 10 }}>
        <StyledButton title="Create Routine" onPress={openCreateModal} style={{ width: 220, borderRadius: 22, backgroundColor: COLORS.primary, paddingVertical: 18, shadowColor: COLORS.primary, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.18, shadowRadius: 8, elevation: 8 }} />
      </View>
      {/* Success Popup */}
      <Modal
        visible={showSuccess}
        animationType="fade"
        transparent
        onRequestClose={() => setShowSuccess(false)}
      >
        <View style={styles.successPopupOverlay}>
          <View style={styles.successPopup}>
            <Text style={styles.successTitle}>{successMessage}</Text>
            <TouchableOpacity style={styles.bigCloseButton} onPress={() => setShowSuccess(false)}>
              <Text style={styles.bigCloseButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      {/* Error Popup */}
      <Modal
        visible={!!error}
        animationType="fade"
        transparent
        onRequestClose={() => setError(null)}
      >
        <View style={styles.errorPopupOverlay}>
          <View style={styles.errorPopup}>
            <Text style={styles.errorTitle}>Error</Text>
            <Text style={styles.errorMessage}>{error}</Text>
            <TouchableOpacity style={styles.errorButton} onPress={() => setError(null)}>
              <Text style={styles.errorButtonText}>Dismiss</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      {/* Create/Edit Routine Modal */}
      <Modal
        visible={showModal}
        animationType="slide"
        transparent
        onRequestClose={closeModal}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <View style={styles.modalOverlay}>
            <View style={styles.modalContainer}>
              <Text style={styles.modalTitle}>{editingRoutine ? 'Edit Routine' : 'Create Routine'}</Text>
              <StyledInput
                placeholder="Routine Name"
                value={routineName}
                onChangeText={setRoutineName}
              />
              <View style={{ flexDirection: 'row', marginBottom: 8 }}>
                <TouchableOpacity
                  style={{ flex: 1, backgroundColor: itemType === 'food' ? COLORS.primary : COLORS.background, borderRadius: 8, padding: 10, marginRight: 4, alignItems: 'center' }}
                  onPress={() => setItemType('food')}
                >
                  <Text style={{ color: itemType === 'food' ? COLORS.white : COLORS.text }}>Food</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={{ flex: 1, backgroundColor: itemType === 'workout' ? COLORS.primary : COLORS.background, borderRadius: 8, padding: 10, marginLeft: 4, alignItems: 'center' }}
                  onPress={() => setItemType('workout')}
                >
                  <Text style={{ color: itemType === 'workout' ? COLORS.white : COLORS.text }}>Workout</Text>
                </TouchableOpacity>
              </View>
              <StyledInput
                placeholder={itemType === 'food' ? 'Food Name' : 'Workout Name'}
                value={itemName}
                onChangeText={setItemName}
              />
              <StyledInput
                placeholder={itemType === 'food' ? 'Serving Size (g)' : 'Duration (min)'}
                value={itemQuantity}
                onChangeText={setItemQuantity}
                keyboardType="numeric"
              />
              <StyledButton title={`Add ${itemType === 'food' ? 'Food' : 'Workout'}`} onPress={handleAddItem} style={{ marginTop: 6, marginBottom: 8 }} />
              {itemError && <Text style={{ color: COLORS.error, marginBottom: 8 }}>{itemError}</Text>}
              <ScrollView style={{ maxHeight: 120, marginBottom: 8 }}>
                {routineItems.map((it, idx) => (
                  <View key={idx} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
                    <Text style={{ flex: 1, color: COLORS.text }}>{it.type === 'food' ? '🍎' : '🏋️‍♂️'} {it.name} {it.quantity ? `(${it.quantity}${it.type === 'food' ? 'g' : ' min'})` : ''}</Text>
                    <TouchableOpacity onPress={() => handleRemoveItem(idx)}>
                      <Trash2 color={COLORS.error} size={18} />
                    </TouchableOpacity>
                  </View>
                ))}
              </ScrollView>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
                <StyledButton title="Save" onPress={handleSaveRoutine} disabled={saving} style={{ flex: 1, marginRight: 8 }} />
                <StyledButton title="Cancel" onPress={closeModal} style={{ flex: 1, backgroundColor: COLORS.error, marginLeft: 8 }} />
              </View>
            </View>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </SafeAreaView>
  );
};

// --- Stylesheet ---

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: COLORS.background,
  },
  authContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 24,
  },
  subtitle: {
    fontSize: 18,
    color: COLORS.text,
    marginBottom: 48,
  },
  input: {
    width: '100%',
    height: 50,
    backgroundColor: COLORS.white,
    borderColor: COLORS.primary,
    borderWidth: 1,
    borderRadius: 12, // Softer corners
    marginBottom: 16,
    paddingHorizontal: 16,
    fontSize: 16,
    color: COLORS.text,
  },
  buttonContainer: {
    marginTop: 16,
    width: '100%',
  },
  button: {
    width: '100%',
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12, // Softer corners
    alignItems: 'center',
    marginBottom: 12,
    // Shadow for depth
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: '600',
  },
  screenTitle: {
    fontSize: 34,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
    alignSelf: 'flex-start',
  },
  workoutHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 48,
    marginBottom: 24,
    justifyContent: 'center',
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  summaryContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: COLORS.white,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2.22,
    elevation: 3,
  },
  summaryTitle: {
    fontSize: 14,
    color: COLORS.placeholder,
    fontWeight: '600',
  },
  summaryValue: {
    fontSize: 28,
    color: COLORS.text,
    fontWeight: 'bold',
    marginVertical: 4,
  },
  summaryUnit: {
    fontSize: 12,
    color: COLORS.placeholder,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 16,
  },

  chart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 200,
    marginTop: 16,
  },
  barWrapper: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    height: '100%',
  },
  bar: {
    width: '60%',
    borderRadius: 6,
  },
  barLabel: {
    fontSize: 12,
    color: COLORS.text,
    marginTop: 4,
  },
  barValue: {
    fontSize: 10,
    color: COLORS.placeholder,
    marginTop: 2,
  },
  logContainer: {
    flex: 1,
    paddingHorizontal: 24,
  },
  disabledButton: {
    backgroundColor: '#A1A1AA',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  errorText: {
    color: COLORS.error,
    textAlign: 'center',
    marginTop: 16,
  },
  foodItem: {
    backgroundColor: COLORS.white,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2.22,
    elevation: 3,
  },
  foodName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  foodDetails: {
    fontSize: 14,
    color: COLORS.placeholder,
    marginTop: 4,
  },
  logButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  logButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
  },
  genderContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 16,
  },
  genderButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.primary,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  genderButtonSelected: {
    backgroundColor: COLORS.primary,
  },
  genderButtonText: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: '500',
  },
  genderButtonTextSelected: {
    color: COLORS.white,
  },
  rememberMeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: COLORS.primary,
    marginRight: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxInner: {
    width: 12,
    height: 12,
    backgroundColor: COLORS.primary,
    borderRadius: 2,
  },
  rememberMeText: {
    color: COLORS.text,
    fontSize: 14,
  },
  switchButton: {
    marginTop: 16,
  },
  switchButtonText: {
    color: COLORS.primary,
    fontSize: 14,
    textAlign: 'center',
  },
  settingsContainer: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 16,
  },
  settingsButtonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    marginVertical: 8,
  },
  settingsAccountButton: {
    width: '100%',
    height: 100,
    borderRadius: 24,
    backgroundColor: COLORS.logFood,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginVertical: 0,
    shadowColor: COLORS.logFood,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  settingsAccountButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 28,
    letterSpacing: 1,
  },
  settingsLogoutButton: {
    width: '100%',
    height: 100,
    borderRadius: 24,
    backgroundColor: '#FF3B30', // vibrant red
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginVertical: 0,
    marginTop: 0,
    marginBottom: 0,
    shadowColor: '#FF3B30',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  errorPopupOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  errorPopup: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 24,
    width: '80%',
    alignItems: 'center',
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#EF4444',
    marginBottom: 12,
  },
  errorMessage: {
    fontSize: 16,
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 20,
  },
  errorButton: {
    backgroundColor: '#EF4444',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  errorButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  noDataText: {
    color: COLORS.placeholder,
    fontSize: 16,
    textAlign: 'center',
    marginTop: 20,
  },
  retryButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  circularProgressContainer: {
    alignItems: 'center',
    marginHorizontal: 8,
  },
  circularProgressTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 8,
  },
  actionButton: {
    width: '30%',
    aspectRatio: 1,
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  actionButtonText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
    marginTop: 8,
    textAlign: 'center',
  },
  comingSoonText: {
    color: COLORS.white,
    fontSize: 10,
    opacity: 0.8,
    marginTop: 4,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
    marginTop: 12,
  },
  inputDescription: {
    fontSize: 13,
    color: COLORS.placeholder,
    marginBottom: 8,
    marginLeft: 2,
  },
  pickerWrapper: {
    height: 56,
    width: '100%',
    borderWidth: 1,
    borderColor: COLORS.placeholder,
    borderRadius: 12,
    justifyContent: 'center',
    marginBottom: 8,
    backgroundColor: COLORS.white,
  },
  picker: {
    width: '100%',
  },
  accountHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    paddingHorizontal: 24,
    paddingTop: 50,
  },
  accountBackArrow: {
    color: COLORS.primary,
    fontSize: 32,
    fontWeight: 'bold',
    padding: 8,
    marginRight: 8,
  },
  accountHeaderTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
    marginLeft: -36,
  },
  headerContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  streakContainer: {
    backgroundColor: COLORS.streakRed,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    minHeight: 32,
  },
  streakText: {
    color: COLORS.text,
    fontWeight: 'bold',
    fontSize: 18,
    marginLeft: 6,
  },
  workoutResultBox: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    paddingVertical: 28,
    paddingHorizontal: 16,
    marginBottom: 18,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 3,
  },
  successPopupOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  successPopup: {
    backgroundColor: '#22C55E', // green
    borderRadius: 12,
    padding: 24,
    width: '80%',
    alignItems: 'center',
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  successTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 12,
  },
  successMessage: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 20,
  },
  successButton: {
    backgroundColor: '#34D399', // vibrant light green
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  successButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  chatbotContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  chatInput: {
    flex: 1,
    padding: 10,
    borderWidth: 1,
    borderColor: COLORS.placeholder,
    borderRadius: 12,
    marginHorizontal: 10,
    marginVertical: 10,
    backgroundColor: COLORS.white,
  },
  inputContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 10,
    backgroundColor: COLORS.white,
  },
  sendButton: {
    padding: 10,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    marginHorizontal: 5,
  },
  messageBubble: {
    padding: 10,
    borderRadius: 12,
    marginVertical: 5,
  },
  userMessage: {
    backgroundColor: COLORS.primary,
    alignSelf: 'flex-end',
  },
  botMessage: {
    backgroundColor: COLORS.white,
    alignSelf: 'flex-start',
  },
  messageText: {
    color: COLORS.white,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modalContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 20,
    padding: 24,
    width: '90%',
    alignItems: 'stretch',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  modalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 8,
    marginBottom: 4,
  },
  modalInput: {
    backgroundColor: COLORS.background,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.placeholder,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    marginBottom: 8,
  },
  modalExplanation: {
    fontSize: 13,
    color: COLORS.placeholder,
    marginBottom: 12,
    marginTop: 2,
  },
  modalButtonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    marginHorizontal: 6,
    alignItems: 'center',
  },
  modalButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 16,
  },
  bigCloseButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 18,
    paddingHorizontal: 40,
    borderRadius: 16,
    marginTop: 24,
    alignItems: 'center',
  },
  bigCloseButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 22,
    letterSpacing: 1,
  },
  poweredBy: {
    marginTop: 18,
    fontSize: 13,
    color: COLORS.placeholder,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  passwordInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderColor: COLORS.primary,
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 16,
    paddingHorizontal: 8,
  },
  eyeIcon: {
    padding: 6,
  },
  loginSettingsButton: {
    width: '100%',
    height: 100,
    borderRadius: 24,
    backgroundColor: '#3B82F6', // blue
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginVertical: 0,
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  loginSettingsButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 28,
    letterSpacing: 1,
  },
  notificationSettingsButton: {
    width: '100%',
    height: 110,
    borderRadius: 24,
    backgroundColor: '#22223B', // dark blue-gray, not used elsewhere
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginVertical: 0,
    shadowColor: '#22223B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  notificationSettingsButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 28,
    letterSpacing: 1,
    textAlign: 'center',
    paddingHorizontal: 12,
  },
  addNotificationButton: {
    width: '100%',
    height: 70,
    borderRadius: 20,
    backgroundColor: '#22223B',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginTop: 20,
    marginBottom: 8,
    shadowColor: '#22223B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  addNotificationButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 26,
    letterSpacing: 1,
    textAlign: 'center',
    paddingHorizontal: 12,
  },
  summaryWidgetContainer: {
    width: '100%',
    borderRadius: 28,
    backgroundColor: COLORS.lightGreen,
    marginVertical: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 6,
  },
  summaryWidgetBg: {
    borderRadius: 28,
    padding: 24,
    width: '100%',
  },
  summaryWidgetRow: {
    marginBottom: 18,
  },
  summaryWidgetLabel: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  summaryWidgetBarBg: {
    width: '100%',
    height: 7,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  summaryWidgetBar: {
    height: 7,
    borderRadius: 4,
  },
  detailsCard: {
    backgroundColor: COLORS.white,
    borderRadius: 18,
    padding: 18,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  detailsCardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 6,
    color: COLORS.primaryDark,
  },
  detailsCardText: {
    fontSize: 16,
    color: COLORS.text,
    marginBottom: 2,
  },
  statusGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  statusCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    width: '48%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  statusLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statusValue: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  chartContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  chartArea: {
    height: 180,
    position: 'relative',
    marginBottom: 30,
    flexDirection: 'row',
  },
  goalLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 2,
    borderStyle: 'dashed',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  dataPoint: {
    position: 'absolute',
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  chartLine: {
    position: 'absolute',
    height: 2,
  },
  chartLegend: {
    fontSize: 14,
    color: COLORS.text,
    textAlign: 'center',
    fontWeight: '500',
  },
  yAxis: {
    width: 40,
    justifyContent: 'space-between',
    paddingVertical: 8,
    height: 140,
    flexDirection: 'column-reverse',
  },
  yAxisLabel: {
    fontSize: 12.5,
    color: COLORS.text,
    textAlign: 'right',
    paddingRight: 4,
    fontWeight: 'bold',
  },
  chartContent: {
    flex: 1,
    marginLeft: 8,
    position: 'relative',
    height: 140,
    marginRight: 0,
  },
  trendLine: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  xAxis: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
    paddingHorizontal: 45,
    paddingLeft: 53,
    position: 'absolute',
    bottom: -36,
    left: 0,
    right: 0,
  },
  xAxisLabel: {
    fontSize: 12.5,
    color: COLORS.text,
    textAlign: 'center',
    flex: 1,
    fontWeight: '500',
    marginHorizontal: 4,
  },
  routinesButton: {
    width: '100%',
    height: 60,
    borderRadius: 20,
    backgroundColor: '#22223B', // Unique dark blue-gray, not used elsewhere
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginTop: 10,
    marginBottom: 10,
    shadowColor: '#22223B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  routinesButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 24,
    letterSpacing: 1,
    textAlign: 'center',
    paddingHorizontal: 12,
  },
});

export { 
  LoginSignupScreen, 
  DashboardScreen, 
  FoodLogScreen, 
  WorkoutLogScreen, 
  SettingsScreen,
  QnAScreen,
  AccountSettingsScreen,
  NotificationSettingsScreen,
  TrackingDetailsScreen,
  RoutineScreen // <-- export the new screen
}; 

// Firebase Auth error code to user-friendly message mapping
const firebaseErrorMessages: { [key: string]: string } = {
  'auth/wrong-password': 'The password you entered is incorrect. Please try again.',
  'auth/invalid-credential': 'The password you entered is incorrect. Please try again.',
  'auth/user-not-found': 'No user found with this email.',
  'auth/email-already-in-use': 'This email is already in use. Please use a different email.',
  'auth/invalid-email': 'The email address format is invalid. Please check and try again.',
  'auth/requires-recent-login': 'For security reasons, please log in again and try this action.',
  'auth/too-many-requests': 'Too many attempts. Please wait a few minutes and try again.',
  'auth/network-request-failed': 'Network error. Please check your connection and try again.',
  'auth/internal-error': 'An internal error occurred. Please try again later.',
  'auth/invalid-login-credentials': 'The password you entered is incorrect. Please try again.',
};

function getFirebaseErrorMessage(error: any) {
  const code = error.code || error.errorCode || '';
  return firebaseErrorMessages[code] || error.message || 'An unknown error occurred.';
}

// Utility to ensure a safe number (never NaN)
function safeNumber(n: any) {
  return typeof n === 'number' && !isNaN(n) ? n : 0;
}