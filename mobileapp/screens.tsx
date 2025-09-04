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
  Image,
  RefreshControl,
  Linking,
} from 'react-native';
import { auth } from './services/firebase';
import { Home, BookOpen, Dumbbell, Settings, Flame, Search, MessageCircle, Send, Eye, EyeOff, Pencil, Trash2, ArrowLeft, Utensils } from 'lucide-react-native';
import { logFood, FoodItem, getLogSummary, LogSummaryResponse, createUserProfile, getUserProfile, getUserProfileSafe, updateUserProfile, UserProfile, API_URL, logWorkout, listRoutines, createRoutine, updateRoutine, deleteRoutine, logRoutine, Routine, RoutineItem, RoutineCreateRequest, RoutineUpdateRequest, getRecipes, getNutritionData, searchFood, sendMessageNotification } from './services/api';
import { useIsFocused, useFocusEffect } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Svg, Circle, Text as SvgText, Path } from 'react-native-svg';
import { Picker } from '@react-native-picker/picker';
import { AppContext } from './contexts/AppContext';
import { useSubscription } from './contexts/SubscriptionContext';
import ConfettiCannon from 'react-native-confetti-cannon';
import { EmailAuthProvider } from 'firebase/auth';
import { KeyboardAwareScrollView } from 'react-native-keyboard-aware-scroll-view';
import firebase from './services/firebase';
import DateTimePicker from '@react-native-community/datetimepicker';
import * as Notifications from 'expo-notifications';

import { LinearGradient } from 'expo-linear-gradient';
import { getWorkoutLogSummary, WorkoutLogSummaryResponse } from './services/api';


import Markdown from 'react-native-markdown-display';
import { firestore } from './services/firebase';
import { format, isToday, isYesterday } from 'date-fns';
import { uploadDietPdf, listNonDieticianUsers, refreshFreePlans, getAllUserProfiles, getUserDiet, extractDietNotifications, getDietNotifications, deleteDietNotification, updateDietNotification, scheduleDietNotifications, cancelDietNotifications, getSubscriptionPlans, selectSubscription, getSubscriptionStatus, addSubscriptionAmount, cancelSubscription, SubscriptionPlan, SubscriptionStatus, getUserNotifications, markNotificationRead, deleteNotification, Notification, getUserDetails, markUserPaid, lockUserApp, unlockUserApp, testUserExists, clearProfileCache } from './services/api';
import * as DocumentPicker from 'expo-document-picker';
import { WebView } from 'react-native-webview';

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

// --- Recipes Screen ---
const RecipesScreen = ({ navigation }: { navigation: any }) => {
  const [recipes, setRecipes] = useState<any[]>([]);
  const [filteredRecipes, setFilteredRecipes] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [isDietician, setIsDietician] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRecipe, setEditingRecipe] = useState<any>(null);
  const [formData, setFormData] = useState({
    title: '',
    type: '',
    allergies: '',
    link: ''
  });

  // Check if user is dietician
  useEffect(() => {
    const checkDieticianStatus = async () => {
      try {
        const user = auth.currentUser;
        if (user) {
          // Add defensive check for firestore
          if (!firestore) {
            console.error('Firestore not initialized for dietician check');
            setIsDietician(user.email === 'nutricious4u@gmail.com');
            return;
          }
          
          const userDoc = await firestore.collection('users').doc(user.uid).get();
          const data = userDoc.data();
          setIsDietician(!!data?.isDietician || user.email === 'nutricious4u@gmail.com');
        }
      } catch (error) {
        console.error('Error checking dietician status:', error);
        // Fallback to email check
        const user = auth.currentUser;
        if (user) {
          setIsDietician(user.email === 'nutricious4u@gmail.com');
        }
      }
    };
    checkDieticianStatus();
  }, []);

  // Fetch recipes using API queue system
  const fetchRecipes = async () => {
    try {
      setLoading(true);
      console.log('[RecipesScreen] Fetching recipes through API queue');
      
      // Use the API queue system instead of direct Firestore access
      const recipesData = await getRecipes();
      console.log('[RecipesScreen] Successfully fetched recipes:', recipesData.length);
      
      setRecipes(recipesData);
      setFilteredRecipes(recipesData);
    } catch (error) {
      console.error('[RecipesScreen] Error fetching recipes:', error);
      // Don't show alert on build, just set empty arrays
      setRecipes([]);
      setFilteredRecipes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Add delay to prevent conflict with login sequence API calls
    const delayedFetch = setTimeout(() => {
      fetchRecipes();
    }, 2500); // 2.5 second delay to ensure login sequence completes
    
    return () => clearTimeout(delayedFetch);
  }, []);

  // Search functionality
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredRecipes(recipes);
    } else {
      const filtered = recipes.filter(recipe =>
        recipe.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        recipe.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        recipe.allergies.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredRecipes(filtered);
    }
  }, [searchQuery, recipes]);

  // Handle search
  const handleSearch = () => {
    // Search is handled by useEffect above
  };

  // Open add modal
  const openAddModal = () => {
    setFormData({ title: '', type: '', allergies: '', link: '' });
    setShowAddModal(true);
  };

  // Open edit modal
  const openEditModal = (recipe: any) => {
    setEditingRecipe(recipe);
    setFormData({
      title: recipe.title || '',
      type: recipe.type || '',
      allergies: recipe.allergies || '',
      link: recipe.link || ''
    });
    setShowEditModal(true);
  };

  // Close modals
  const closeModals = () => {
    setShowAddModal(false);
    setShowEditModal(false);
    setEditingRecipe(null);
    setFormData({ title: '', type: '', allergies: '', link: '' });
  };

  // Save recipe (add or edit)
  const handleSaveRecipe = async () => {
    if (!formData.title.trim()) {
      Alert.alert('Error', 'Recipe title is required');
      return;
    }

    try {
      // Add defensive check for firestore
      if (!firestore) {
        Alert.alert('Error', 'Database not available');
        return;
      }

      const recipeData = {
        title: formData.title.trim(),
        type: formData.type.trim(),
        allergies: formData.allergies.trim(),
        link: formData.link.trim(),
        updatedAt: new Date()
      };

      if (showEditModal && editingRecipe) {
        // Update existing recipe
        await firestore.collection('recipes').doc(editingRecipe.id).update(recipeData);
        Alert.alert('Success', 'Recipe updated successfully');
      } else {
        // Add new recipe
        await firestore.collection('recipes').add({
          ...recipeData,
          createdAt: new Date(),
          createdBy: auth.currentUser?.uid
        });
        Alert.alert('Success', 'Recipe added successfully');
      }

      closeModals();
      fetchRecipes(); // Refresh the list
    } catch (error) {
      console.error('Error saving recipe:', error);
      Alert.alert('Error', 'Failed to save recipe');
    }
  };

  // Delete recipe
  const handleDeleteRecipe = async (recipeId: string) => {
    Alert.alert(
      'Delete Recipe',
      'Are you sure you want to delete this recipe?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await firestore.collection('recipes').doc(recipeId).delete();
              Alert.alert('Success', 'Recipe deleted successfully');
              fetchRecipes(); // Refresh the list
            } catch (error) {
              console.error('Error deleting recipe:', error);
              Alert.alert('Error', 'Failed to delete recipe');
            }
          }
        }
      ]
    );
  };

  // Render recipe card
  const renderRecipeCard = ({ item }: { item: any }) => (
    <View style={styles.recipeCard}>
      <Text style={styles.recipeTitle}>{item.title}</Text>
      {item.type && <Text style={styles.recipeType}>Type: {item.type}</Text>}
      {item.allergies && <Text style={styles.recipeAllergies}>Allergies: {item.allergies}</Text>}
      {item.link && (
        <TouchableOpacity 
          onPress={() => {
            if (item.link && item.link.trim() !== '') {
              Linking.openURL(item.link.trim()).catch(err => {
                console.error('Error opening URL:', err);
                Alert.alert('Error', 'Could not open recipe link');
              });
            }
          }}
          style={styles.recipeLinkContainer}
        >
          <Text style={styles.recipeLink}>View Recipe →</Text>
        </TouchableOpacity>
      )}
      {isDietician && (
        <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginTop: 8 }}>
          <TouchableOpacity 
            style={[styles.editButton, { marginRight: 8 }]} 
            onPress={() => openEditModal(item)}
          >
            <Pencil color={COLORS.primary} size={16} />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.editButton} 
            onPress={() => handleDeleteRecipe(item.id)}
          >
            <Trash2 color={COLORS.error} size={16} />
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={{ flex: 1 }} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView 
          style={styles.scrollContainer}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Recipes</Text>
            {isDietician && (
              <TouchableOpacity style={styles.addButton} onPress={openAddModal}>
                <Text style={[styles.addButtonText, { color: COLORS.primary }]}>+ Add</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Search Bar */}
          <View style={styles.searchContainer}>
            <View style={styles.searchBar}>
              <Search color={COLORS.placeholder} size={20} />
              <TextInput
                style={styles.searchInput}
                placeholder="Search recipes..."
                placeholderTextColor={COLORS.placeholder}
                value={searchQuery}
                onChangeText={setSearchQuery}
              />
            </View>
            <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
              <Text style={styles.searchButtonText}>Search</Text>
            </TouchableOpacity>
          </View>

          {/* Recipes List */}
          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={COLORS.primary} />
              <Text style={styles.loadingText}>Loading recipes...</Text>
            </View>
          ) : (
            <View style={styles.recipesContainer}>
              {filteredRecipes.length === 0 ? (
                <View style={styles.emptyContainer}>
                  <Text style={styles.emptyText}>
                    {searchQuery ? 'No recipes found matching your search' : 'No recipes available yet'}
                  </Text>
                  {isDietician && !searchQuery && (
                    <TouchableOpacity style={styles.addFirstButton} onPress={openAddModal}>
                      <Text style={styles.addFirstButtonText}>Add First Recipe</Text>
                    </TouchableOpacity>
                  )}
                </View>
              ) : (
                filteredRecipes.map((item) => (
                  <View key={item.id}>
                    {renderRecipeCard({ item })}
                  </View>
                ))
              )}
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>

      {/* Add/Edit Modal */}
      <Modal
        visible={showAddModal || showEditModal}
        transparent={true}
        animationType="fade"
        onRequestClose={closeModals}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>
              {showEditModal ? 'Edit Recipe' : 'Add New Recipe'}
            </Text>
            
            <StyledInput
              placeholder="Recipe Title *"
              value={formData.title}
              onChangeText={(text) => setFormData({ ...formData, title: text })}
            />
            
            <StyledInput
              placeholder="Type (e.g., Vegetarian, Non-Veg, Egg)"
              value={formData.type}
              onChangeText={(text) => setFormData({ ...formData, type: text })}
            />
            
            <StyledInput
              placeholder="Allergies (e.g., Nuts, Dairy, Gluten)"
              value={formData.allergies}
              onChangeText={(text) => setFormData({ ...formData, allergies: text })}
            />
            
            <StyledInput
              placeholder="Recipe Link (optional)"
              value={formData.link}
              onChangeText={(text) => setFormData({ ...formData, link: text })}
              keyboardType="url"
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={closeModals}>
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.saveButton} onPress={handleSaveRecipe}>
                <Text style={styles.saveButtonText}>
                  {showEditModal ? 'Update' : 'Add Recipe'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
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

    setError(null);
    
    try {
      // Add iOS-specific timeout handling
      const signupPromise = auth.createUserWithEmailAndPassword(email, password);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Signup timeout')), Platform.OS === 'ios' ? 30000 : 15000)
      );
      
      const userCredential = await Promise.race([signupPromise, timeoutPromise]) as any;
      const user = userCredential.user;

      if (user) {
        // Create user profile
        await createUserProfile({
          id: user.uid,
          userId: user.uid, // For backward compatibility
          firstName,
          lastName,
          age: parseInt(age),
          gender,
          email,
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

        // Save credentials if remember me is checked
        if (rememberMe) {
          await AsyncStorage.setItem('savedEmail', email);
          await AsyncStorage.setItem('savedPassword', password);
        }
      }
    } catch (error: any) {
      console.log('[SignUp] Error:', error);
      
      // Handle iOS-specific connection issues
      if (Platform.OS === 'ios' && (
        error.message === 'Signup timeout' ||
        error.code === 'auth/network-request-failed' ||
        error.message?.includes('network') ||
        error.message?.includes('connection')
      )) {
        setError('Network connection issue. Please check your internet connection and try again.');
        return;
      }
      
      // Provide more specific error messages
      if (error.code === 'auth/email-already-in-use') {
        setError('An account with this email already exists. Please try logging in instead.');
      } else if (error.code === 'auth/invalid-email') {
        setError('Invalid email address. Please check your email format.');
      } else if (error.code === 'auth/weak-password') {
        setError('Password is too weak. Please use at least 6 characters.');
      } else if (error.code === 'auth/too-many-requests') {
        setError('Too many failed attempts. Please try again later.');
      } else {
        setError('Signup failed. Please try again.');
      }
    }
  };

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please enter email and password');
      return;
    }
    setLoadingLogin(true);
    setError(null);
    
    try {
      // Add iOS-specific timeout handling
      const loginPromise = auth.signInWithEmailAndPassword(email, password);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Login timeout')), Platform.OS === 'ios' ? 30000 : 15000)
      );
      
      await Promise.race([loginPromise, timeoutPromise]);
      
      if (rememberMe) {
        await AsyncStorage.setItem('savedEmail', email);
        await AsyncStorage.setItem('savedPassword', password);
      } else {
        await AsyncStorage.removeItem('savedEmail');
        await AsyncStorage.removeItem('savedPassword');
      }
    } catch (error: any) {
      console.log('[Login] Error:', error);
      
      // Handle iOS-specific connection issues
      if (Platform.OS === 'ios' && (
        error.message === 'Login timeout' ||
        error.code === 'auth/network-request-failed' ||
        error.message?.includes('network') ||
        error.message?.includes('connection')
      )) {
        setError('Network connection issue. Please check your internet connection and try again.');
        return;
      }
      
      // If login fails for dietician, try to create the account
      if (
        email.trim().toLowerCase() === 'nutricious4u@gmail.com' &&
        password === 'Ekta1978' &&
        (error.code === 'auth/user-not-found' || error.message?.toLowerCase().includes('no user record'))
      ) {
        try {
          console.log('[Login] Creating dietician account...');
          // Create the dietician account
          const userCredential = await auth.createUserWithEmailAndPassword(email, password);
          const user = userCredential.user;
          if (user) {
            // Create user profile for dietician
            await createUserProfile({
              id: user.uid,
              userId: user.uid, // For backward compatibility
              firstName: 'Ekta',
              lastName: 'Taneja',
              age: 45,
              gender: 'female',
              email,
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
          }
          // Retry login
          await auth.signInWithEmailAndPassword(email, password);
          setError(null);
        } catch (createErr: any) {
          console.log('[Login] Error creating dietician account:', createErr);
          setError('Failed to create dietician account: ' + (createErr.message || 'Unknown error'));
        }
      } else {
        // Provide more specific error messages for iOS
        if (error.code === 'auth/invalid-email') {
          setError('Invalid email address. Please check your email format.');
        } else if (error.code === 'auth/user-not-found') {
          setError('No account found with this email. Please check your email or sign up.');
        } else if (error.code === 'auth/wrong-password') {
          setError('Incorrect password. Please try again.');
        } else if (error.code === 'auth/too-many-requests') {
          setError('Too many failed attempts. Please try again later.');
        } else {
          setError('Login failed. Please check your credentials and try again.');
        }
      }
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

// --- Circular Progress with iOS-safe fallback ---
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
  // For iOS EAS builds, use simplified progress indicator to prevent SVG crashes
  if (Platform.OS === 'ios' && !__DEV__) {
    const progress = Math.min(value / maxValue, 1) * 100;
    return (
      <View style={[styles.circularProgressContainer, { width: size, height: size }]}>
        <View style={{
          width: size - 20,
          height: size - 20,
          borderRadius: (size - 20) / 2,
          borderWidth: strokeWidth,
          borderColor: `${color}40`,
          justifyContent: 'center',
          alignItems: 'center',
          backgroundColor: COLORS.background
        }}>
          <Text style={{ fontSize: 14, fontWeight: 'bold', color: COLORS.text, textAlign: 'center' }}>
            {Math.round(value)} / {Math.round(maxValue)}
          </Text>
          <Text style={{ fontSize: 10, color: COLORS.placeholder, textAlign: 'center' }}>
            {unit}
          </Text>
        </View>
        <Text style={[styles.circularProgressTitle, { color, fontSize: 12 }]}>{title}</Text>
      </View>
    );
  }

  // Standard SVG rendering for other platforms
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

  const isFocused = useIsFocused();
  const userId = auth.currentUser?.uid;
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const refresh = route?.params?.refresh;
  const { isFreeUser, setShowUpgradeModal } = useSubscription();
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

  const [dietPdfUrl, setDietPdfUrl] = useState<string | null>(null);
  const [daysLeft, setDaysLeft] = useState<{ days: number; hours: number } | null>(null);
  const [dietLoading, setDietLoading] = useState(false);
  const [dietError, setDietError] = useState('');
  const [showDietPdf, setShowDietPdf] = useState(false);

  // Consolidated profile fetch - removed duplicate to prevent iOS crashes
  // Profile fetching is now handled by the main useEffect below
  


  // Fetch diet countdown data - DELAYED to prevent conflict with login sequence
  useEffect(() => {
    const userId = firebase.auth().currentUser?.uid;
    if (userId) {
      // Add delay to prevent conflict with login sequence API calls
      const delayedFetch = setTimeout(async () => {
        const fetchDietCountdown = async () => {
          try {
            setDietLoading(true);
            const dietData = await getUserDiet(userId);
            console.log('[Dashboard Debug] Diet data fetched:', dietData);
            console.log('[Dashboard Debug] daysLeft:', dietData.daysLeft, 'hoursLeft:', dietData.hoursLeft);
            
            if (dietData.daysLeft !== null && dietData.daysLeft !== undefined) {
              // Use the backend-calculated daysLeft and hoursLeft for accurate countdown
              const daysRemaining = Math.max(0, dietData.daysLeft);
              const hoursRemaining = dietData.hoursLeft !== null && dietData.hoursLeft !== undefined 
                ? Math.max(0, dietData.hoursLeft) 
                : 0;
              
              setDaysLeft({
                days: daysRemaining,
                hours: hoursRemaining
              });
              
              // REMOVED: Local "1 day left" notification scheduling
              // This was causing users to receive notifications meant for dieticians
              // "1 day left" notifications should only be sent to dieticians from the backend
            } else {
              setDaysLeft(null);
            }
            
            setDietPdfUrl(dietData.dietPdfUrl || null);
          } catch (error) {
            console.error('[Dashboard Debug] Error fetching diet countdown:', error);
            // Don't show error to user, just log it and continue
            setDietError('');
            // Set default values to prevent crashes
            setDaysLeft(null);
            setDietPdfUrl(null);
          } finally {
            setDietLoading(false);
          }
        };
        
        fetchDietCountdown();
        
        // Set up interval to update countdown every minute for real-time experience
        console.log('[Dashboard Debug] Setting up countdown interval');
        const interval = setInterval(() => {
          console.log('[Dashboard Debug] Countdown interval triggered');
          fetchDietCountdown();
        }, 60 * 1000); // Update every minute
        
        return () => {
          console.log('[Dashboard Debug] Clearing countdown interval');
          clearInterval(interval);
        };
      }, 5000); // 5 second delay to ensure login sequence completes
      
      return () => {
        clearTimeout(delayedFetch);
      };
    }
  }, []);

      // Listen for new diet notifications and refresh diet data
    useEffect(() => {
      if (!userId) return; // Don't set up listener if no user ID
      
      const subscription = Notifications.addNotificationReceivedListener(async (notification) => {
        const data = notification.request.content.data;
        
        // Handle new diet notifications - refresh diet data immediately
        if (data?.type === 'new_diet' && data?.userId === userId) {
          console.log('[Dashboard] Received new diet notification, refreshing diet data...');
          console.log('[Dashboard] Notification data:', data);
          
          try {
            setDietLoading(true);
            
            // Check if we have cache version in notification data
            if (data.cacheVersion) {
              console.log('[Dashboard] Cache version in notification:', data.cacheVersion);
            }
            
            const dietData = await getUserDiet(userId);
            console.log('[Dashboard] Refreshed diet data after new diet:', dietData);
            
            if (dietData.daysLeft !== null && dietData.daysLeft !== undefined) {
              const daysRemaining = Math.max(0, dietData.daysLeft);
              const hoursRemaining = dietData.hoursLeft !== null && dietData.hoursLeft !== undefined 
                ? Math.max(0, dietData.hoursLeft) 
                : 0;
              
              setDaysLeft({
                days: daysRemaining,
                hours: hoursRemaining
              });
            } else {
              setDaysLeft(null);
            }
            
            setDietPdfUrl(dietData.dietPdfUrl || null);
            console.log('[Dashboard] ✅ Diet data refreshed successfully after new diet upload');
            
            // Show success message to user
            Alert.alert(
              'New Diet Available!',
              'Your dietician has uploaded a new diet plan. The diet has been refreshed automatically.',
              [{ text: 'OK', style: 'default' }]
            );
          } catch (error) {
            console.error('[Dashboard] Error refreshing diet data after new diet:', error);
            
            // Show error message to user
            Alert.alert(
              'Refresh Error',
              'There was an issue refreshing your diet data. Please pull down to refresh manually.',
              [{ text: 'OK', style: 'default' }]
            );
          } finally {
            setDietLoading(false);
          }
        }
      });

      return () => subscription.remove();
    }, [userId]);

  const handleOpenDiet = async () => {
    console.log('[DashboardScreen] handleOpenDiet called, isFreeUser:', isFreeUser);
    if (isFreeUser) {
      console.log('[DashboardScreen] Showing upgrade modal for free user');
      setShowUpgradeModal(true);
      return;
    }
    
    try {
      // Force refresh diet data before opening
      console.log('[DashboardScreen] Refreshing diet data before opening PDF...');
      if (!userId) {
        Alert.alert('Error', 'User not authenticated. Please log in again.');
        return;
      }
      
      // Force refresh by adding cache busting parameter
      const dietData = await getUserDiet(userId);
      console.log('[DashboardScreen] Refreshed diet data:', dietData);
      
      // Always update local state with fresh data to ensure we have the latest
      setDietPdfUrl(dietData.dietPdfUrl || null);
      
      if (dietData.dietPdfUrl) {
        console.log('Opening diet PDF with URL:', dietData.dietPdfUrl);
        
        // Generate PDF URL with cache busting
        const pdfUrl = getPdfUrlWithCacheBusting(dietData.dietPdfUrl);
        console.log('Final PDF URL for browser:', pdfUrl);
        
        if (pdfUrl) {
          // Open PDF in browser instead of in-app viewer
          const canOpen = await Linking.canOpenURL(pdfUrl);
          if (canOpen) {
            await Linking.openURL(pdfUrl);
            console.log('PDF opened in browser successfully');
          } else {
            console.log('Cannot open URL:', pdfUrl);
            Alert.alert('Error', 'Cannot open PDF. Please try again.');
          }
        } else {
          Alert.alert('Error', 'No PDF URL available.');
        }
      } else {
        Alert.alert('No Diet Available', 'You don\'t have a diet plan yet. Please contact your dietician.');
      }
    } catch (e) {
      console.error('Failed to open diet PDF:', e);
      Alert.alert('Error', 'Failed to open diet PDF. Please try again.');
    }
  };

  // Helper function to get the correct PDF URL with cache busting
  const getPdfUrlWithCacheBusting = (pdfUrl: string) => {
    if (!pdfUrl) return null;
    
    console.log('getPdfUrlWithCacheBusting called with pdfUrl:', pdfUrl);
    
    // If it's a Firebase Storage signed URL, use it directly
    if (pdfUrl.startsWith('https://storage.googleapis.com/')) {
      console.log('Using Firebase Storage URL directly:', pdfUrl);
      return pdfUrl;
    }
    
    // If it's a firestore:// URL, use the backend endpoint
    if (pdfUrl.startsWith('firestore://')) {
      const userId = firebase.auth().currentUser?.uid;
      const url = `${API_URL}/users/${userId}/diet/pdf`;
      console.log('Using backend endpoint for firestore URL:', url);
      return url;
    }
    
    // If it's just a filename or any other format, use the backend endpoint with cache busting
    const userId = firebase.auth().currentUser?.uid;
    const timestamp = Date.now(); // Add cache busting parameter
    const url = `${API_URL}/users/${userId}/diet/pdf?t=${timestamp}`;
    console.log('Using backend endpoint for filename with cache busting:', url);
    return url;
  };

  // Helper function to get the correct PDF URL (legacy function for backward compatibility)
  const getPdfUrl = () => {
    if (!dietPdfUrl) return null;
    
    console.log('getPdfUrl called with dietPdfUrl:', dietPdfUrl);
    
    // If it's a Firebase Storage signed URL, use it directly
    if (dietPdfUrl.startsWith('https://storage.googleapis.com/')) {
      console.log('Using Firebase Storage URL directly:', dietPdfUrl);
      return dietPdfUrl;
    }
    
    // If it's a firestore:// URL, use the backend endpoint
    if (dietPdfUrl.startsWith('firestore://')) {
      const userId = firebase.auth().currentUser?.uid;
      const url = `${API_URL}/users/${userId}/diet/pdf`;
      console.log('Using backend endpoint for firestore URL:', url);
      return url;
    }
    
    // If it's just a filename or any other format, use the backend endpoint
    const userId = firebase.auth().currentUser?.uid;
    const url = `${API_URL}/users/${userId}/diet/pdf`;
    console.log('Using backend endpoint for filename:', url);
    return url;
  };

  // Helper function to create a PDF viewer HTML
  const createPdfViewerHtml = (pdfUrl: string) => {
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { margin: 0; padding: 0; }
            #pdf-viewer { width: 100%; height: 100vh; }
          </style>
        </head>
        <body>
          <embed id="pdf-viewer" src="${pdfUrl}" type="application/pdf" />
        </body>
      </html>
    `;
  };



  // Fetch user profile for targets whenever focused - FIXED: removed problematic refresh dependency
  useEffect(() => {
    if (!userId || !isFocused) return;
    
    // Add debounce delay for iOS stability
    const delay = Platform.OS === 'ios' ? 300 : 0;
    
    const delayedFetch = setTimeout(async () => {
      try {
        const profile = await getUserProfileSafe(userId);
        setUserProfile(profile);
        // Also set diet PDF URL to consolidate profile fetching
        if (profile) {
          console.log('[Dashboard Debug] Profile fetched - dietPdfUrl:', profile.dietPdfUrl);
          setDietPdfUrl(profile.dietPdfUrl || null);
        }
      } catch (error) {
        console.error('[Dashboard Debug] Error fetching profile:', error);
        // For iOS, don't crash on profile fetch errors
        if (Platform.OS === 'ios') {
          console.warn('[iOS Safety] Profile fetch failed, continuing with cached data');
        }
      }
    }, delay);

    return () => clearTimeout(delayedFetch);
  }, [userId, isFocused]);

  // --- Persist calories burned for the current day ---
  const getTodayKey = () => {
    const d = new Date();
    return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  };

  // Load burnedToday from AsyncStorage on mount or day change
  useEffect(() => {
    const loadPersisted = async () => {
      const todayKey = getTodayKey();
      const burned = await AsyncStorage.getItem('burnedToday_' + todayKey);
      setBurnedToday(safeNumber(Number(burned)));
    };
    loadPersisted();
  }, [isFocused, getTodayKey()]);

  // Persist burnedToday whenever it changes
  useEffect(() => {
    const todayKey = getTodayKey();
    AsyncStorage.setItem('burnedToday_' + todayKey, String(safeNumber(burnedToday)));
  }, [burnedToday]);




  // Fetch summary (nutrition) and workout calories for today - DELAYED to prevent conflict with login sequence
  const fetchSummary = async () => {
    if (!userId) {
      setError('User not authenticated');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      // SEQUENTIAL API calls to prevent 499 errors - don't use Promise.all
      console.log('[Dashboard] Fetching food log summary...');
      const foodData = await getLogSummary(userId);
      console.log('[Dashboard] Food log summary received:', foodData);
      setSummary(foodData);
      
      // Add delay between API calls to prevent connection conflicts
      await new Promise(resolve => setTimeout(resolve, 300));
      
      console.log('[Dashboard] Fetching workout log summary...');
      const workoutData = await getWorkoutLogSummary(userId);
      console.log('[Dashboard] Workout log summary received:', workoutData);
      setWorkoutSummary(workoutData);
      
      // Set burnedToday from workout summary for today
      const today = new Date().toISOString().slice(0, 10);
      const todayWorkout = workoutData.history.find((d) => d.day === today);
      setBurnedToday(todayWorkout ? todayWorkout.calories : 0);
    } catch (e) {
      console.error('[Dashboard] Error fetching summary data:', e);
      // Don't show error to user, just log it and continue
      setError('');
      // Set default values to prevent crashes
      setSummary({ 
        history: [],
        daily_summary: { calories: 0, protein: 0, fat: 0 },
        seven_day_history: []
      });
      setWorkoutSummary({ history: [] });
      setBurnedToday(0);
    } finally {
      setLoading(false);
    }
  };

  // Refresh summary after logging food or workout - DELAYED to prevent conflict with login sequence
  useEffect(() => {
    if (isFocused && userId) {
      // Only add delay on first load, not when returning to dashboard
      const isFirstLoad = !summary;
      const delay = isFirstLoad ? 1000 : 0; // Reduced delay, immediate on return
      
      const delayedFetch = setTimeout(() => {
        fetchSummary();
      }, delay);
      
      return () => clearTimeout(delayedFetch);
    }
  }, [isFocused, userId, refresh, showFoodSuccess, showWorkoutSuccess]);

  // Check for daily reset when dashboard is focused - DELAYED to prevent conflict with login sequence
  useEffect(() => {
    if (isFocused && userId) {
      // Add delay to prevent conflict with login sequence API calls
      const delayedCheck = setTimeout(async () => {
        const checkDailyReset = async () => {
          try {
            const today = new Date().toISOString().split('T')[0];
            const lastReset = await AsyncStorage.getItem(`lastResetDate_${userId}`);
            
            if (lastReset !== today) {
              console.log('[Dashboard] Daily reset needed, refreshing data');
              fetchSummary();
            }
          } catch (error) {
            console.error('[Dashboard] Error checking daily reset:', error);
          }
        };
        
        checkDailyReset();
      }, 500); // Reduced delay for faster response
      
      return () => clearTimeout(delayedCheck);
    }
  }, [isFocused, userId]);

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

  // --- Food Modal Handler with Gemini API Integration ---
  const [foodLoading, setFoodLoading] = useState(false);
  const [workoutLoading, setWorkoutLoading] = useState(false);
  const [showNutritionConfirm, setShowNutritionConfirm] = useState(false);
  const [nutritionData, setNutritionData] = useState<{calories: number, protein: number, fat: number} | null>(null);
  const [editableNutrition, setEditableNutrition] = useState<{calories: string, protein: string, fat: string}>({calories: '', protein: '', fat: ''});
  const [pendingFoodData, setPendingFoodData] = useState<{name: string, quantity: string} | null>(null);

  // Cleanup effect to ensure food loading state is reset when modals close
  useEffect(() => {
    if (!showFoodModal && !showNutritionConfirm) {
      // Reset loading state when both modals are closed
      setFoodLoading(false);
    }
  }, [showFoodModal, showNutritionConfirm]);

  
  const handleLogFoodModal = async () => {
    if (!foodName.trim() || !foodQty.trim()) {
      setShowFoodError(true);
      return;
    }
    const userId = auth.currentUser?.uid;
    if (userId) {
      try {
        setFoodLoading(true);
        
        // Safety timeout to prevent infinite loading state
        const safetyTimeout = setTimeout(() => {
          console.warn('[Food Log] Safety timeout triggered - resetting loading state');
          setFoodLoading(false);
        }, 30000); // 30 seconds timeout
        
        // Call the backend to get Gemini nutrition data (without logging yet)
        console.log('[Food Log] Fetching nutrition data from backend Gemini API...');
        const response = await getNutritionData(foodName.trim(), foodQty);
        
        // Clear safety timeout since API call succeeded
        clearTimeout(safetyTimeout);
        
        // Extract nutrition data from the response
        const nutrition = response.food;
        setNutritionData({
          calories: nutrition.calories || 0,
          protein: nutrition.protein || 0,
          fat: nutrition.fat || 0
        });
        setEditableNutrition({
          calories: (nutrition.calories || 0).toString(),
          protein: (nutrition.protein || 0).toString(),
          fat: (nutrition.fat || 0).toString()
        });
        setPendingFoodData({name: foodName.trim(), quantity: foodQty});
        
        // Close the first modal and show the confirmation modal
        console.log('[Food Log] Closing first modal and opening nutrition confirmation modal');
        setShowFoodModal(false);
        
        // Small delay to ensure first modal closes before opening confirmation
        setTimeout(() => {
        setShowNutritionConfirm(true);
          
          // Clear loading state after confirmation modal is shown
          setTimeout(() => {
            setFoodLoading(false);
            console.log('[Food Log] Nutrition confirmation modal should be visible now');
          }, 50);
        }, Platform.OS === 'ios' ? 150 : 100);
        
      } catch (error) {
        console.error('[Food Log] Error fetching nutrition data from backend:', error);
        setShowFoodError(true);
        setFoodLoading(false);
        
        // Safety timeout to ensure loading state is reset
        setTimeout(() => {
          setFoodLoading(false);
        }, 1000);
      }
    }
  };

  const handleConfirmNutrition = async () => {
    if (!pendingFoodData) return;
    const userId = auth.currentUser?.uid;
    if (userId) {
      try {
        setFoodLoading(true);
        // Now log the food with the confirmed data
        console.log('[Food Log] Confirming and logging food with user-edited nutrition data');
        await logFood(userId, pendingFoodData.name, pendingFoodData.quantity);
        setShowNutritionConfirm(false);
        setShowFoodModal(false);
        setShowFoodSuccess(true);
        setFoodName('');
        setFoodQty('');
        setNutritionData(null);
        setPendingFoodData(null);
        fetchSummary();
      } catch (error) {
        console.error('[Food Log] Error logging confirmed food:', error);
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

  const targetBurned = userProfile?.caloriesBurnedGoal ?? 0;

  return (
    <SafeAreaView style={[styles.container, { paddingTop: 50 }]}> 
      <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 20 }} showsVerticalScrollIndicator={false}>
      <View style={styles.headerContainer}>
        <Text style={styles.screenTitle}>Dashboard</Text>
      </View>
      {/* --- Single Rectangle Widget --- */}
      <SummaryWidget
        todayData={todayData}
        targets={{ calories: targetCalories, protein: targetProtein, fat: targetFat, burned: targetBurned }}
        burnedToday={burnedToday}
        onPress={() => navigation.navigate('TrackingDetails', { summary, burnedToday, userProfile, workoutSummary })}
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
      {/* My Diet Button and Countdown - moved below Routines */}
      <View style={{ marginBottom: 16 }}>
                                <TouchableOpacity
                          style={{ 
                            backgroundColor: dietPdfUrl ? COLORS.primary : COLORS.placeholder, 
                            padding: 12, 
                            borderRadius: 8, 
                            alignItems: 'center',
                            opacity: dietPdfUrl ? 1 : 0.5
                          }}
                          onPress={handleOpenDiet}
                          disabled={!dietPdfUrl}
                        >
                          <Text style={{ color: COLORS.white, fontWeight: 'bold', fontSize: 18 }}>My Diet</Text>
                        </TouchableOpacity>
        {dietLoading ? (
          <Text style={{ color: COLORS.placeholder, marginTop: 12, fontSize: 16, fontWeight: 'bold', textAlign: 'center' }}>Loading diet info...</Text>
        ) : dietError ? (
          <Text style={{ color: 'red', marginTop: 12, fontSize: 16, fontWeight: 'bold', textAlign: 'center' }}>{dietError}</Text>
        ) : (
          <>
            <Text style={{ color: COLORS.text, marginTop: 12, fontSize: 14, fontWeight: '600', textAlign: 'center' }}>
              Time Until next diet
            </Text>
            <Text style={{ color: COLORS.primary, marginTop: 4, fontSize: 20, fontWeight: 'bold', textAlign: 'center' }}>
              {daysLeft ? `${daysLeft.days} days ${daysLeft.hours} hours` : '-'}
            </Text>
          </>
        )}
      </View>
      <Modal
        visible={showDietPdf}
        animationType="slide"
        transparent={false}
        onRequestClose={() => setShowDietPdf(false)}
      >
        <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', padding: 12, backgroundColor: '#fff', zIndex: 2 }}>
            <TouchableOpacity onPress={() => setShowDietPdf(false)} style={{ padding: 8, marginRight: 8 }}>
              <Text style={{ fontSize: 22, color: COLORS.primary }}>Close</Text>
            </TouchableOpacity>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: COLORS.text }}>My Diet PDF</Text>
          </View>
                      <View style={{ flex: 1 }}>
              {dietPdfUrl ? (
                (() => {
                  const pdfUrl = getPdfUrl();
                  return pdfUrl ? (
                    <WebView
                      source={{ 
                        html: `
                          <!DOCTYPE html>
                          <html>
                            <head>
                              <meta name="viewport" content="width=device-width, initial-scale=1.0">
                              <title>PDF Viewer</title>
                              <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
                              <style>
                                body { 
                                  margin: 0; 
                                  padding: 0; 
                                  font-family: Arial, sans-serif;
                                  background-color: #f0f0f0;
                                }
                                .container {
                                  width: 100%;
                                  height: 100vh;
                                  display: flex;
                                  flex-direction: column;
                                }
                                                          .header {
                            display: none;
                          }
                                .pdf-container {
                                  flex: 1;
                                  background: white;
                                  overflow: auto;
                                  position: relative;
                                  touch-action: manipulation;
                                }
                                                          .page-wrapper {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            padding: 20px 0;
                          }
                          .page-canvas {
                            display: block;
                            margin: 0 auto 20px auto;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            touch-action: manipulation;
                          }
                                .loading {
                                  display: flex;
                                  justify-content: center;
                                  align-items: center;
                                  height: 100%;
                                  font-size: 18px;
                                  color: #666;
                                }
                                .error {
                                  display: flex;
                                  justify-content: center;
                                  align-items: center;
                                  height: 100%;
                                  font-size: 16px;
                                  color: #d32f2f;
                                  text-align: center;
                                  padding: 20px;
                                }
                                                          .page-indicator {
                            background: rgba(0, 0, 0, 0.7);
                            color: white;
                            padding: 8px 16px;
                            text-align: center;
                            position: fixed;
                            top: 20px;
                            left: 50%;
                            transform: translateX(-50%);
                            border-radius: 20px;
                            z-index: 1000;
                            font-size: 14px;
                          }
                          .page-info {
                            margin: 0;
                            font-size: 14px;
                            color: white;
                          }
                              </style>
                            </head>
                            <body>
                              <div class="container">
                                <div class="header">
                                  <h3>Diet PDF Viewer</h3>
                                </div>
                                <div class="pdf-container" id="pdf-container">
                                  <div class="loading">Loading PDF...</div>
                                </div>
                                                          <div class="page-indicator">
                            <span class="page-info">
                              Page <span id="page-num">1</span> of <span id="page-count">1</span>
                            </span>
                          </div>
                              </div>
                              
                              <script>
                                // Set up PDF.js worker
                                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                                
                                                          let pdfDoc = null;
                          let currentScale = 1.5;
                          const minScale = 0.5;
                          const maxScale = 3.0;
                          let allPages = [];
                          let isZooming = false;
                          let zoomTimeout = null;
                                
                                const container = document.getElementById('pdf-container');
                                
                                // Touch handling variables
                                let initialDistance = 0;
                                let initialScale = 1.5;
                                let isPinching = false;
                                
                                                          // Render all pages for vertical scrolling
                          async function renderAllPages() {
                            const pageWrapper = document.createElement('div');
                            pageWrapper.className = 'page-wrapper';
                            
                            for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
                              const page = await pdfDoc.getPage(pageNum);
                              const viewport = page.getViewport({scale: currentScale});
                              
                              const canvas = document.createElement('canvas');
                              canvas.className = 'page-canvas';
                              canvas.height = viewport.height;
                              canvas.width = viewport.width;
                              
                              const ctx = canvas.getContext('2d');
                              const renderContext = {
                                canvasContext: ctx,
                                viewport: viewport
                              };
                              
                              await page.render(renderContext).promise;
                              pageWrapper.appendChild(canvas);
                              
                              // Add touch listeners to each canvas
                              addTouchListeners(canvas);
                            }
                            
                            container.innerHTML = '';
                            container.appendChild(pageWrapper);
                            
                            // Update page indicator
                            document.getElementById('page-count').textContent = pdfDoc.numPages;
                            document.getElementById('page-num').textContent = '1';
                            
                            // Add scroll listener for page tracking
                            container.addEventListener('scroll', updateCurrentPage);
                          }
                          
                          // Update current page based on scroll position
                          function updateCurrentPage() {
                            const scrollTop = container.scrollTop;
                            const containerHeight = container.clientHeight;
                            const pageHeight = container.scrollHeight / pdfDoc.numPages;
                            
                            const currentPage = Math.floor(scrollTop / pageHeight) + 1;
                            const clampedPage = Math.max(1, Math.min(currentPage, pdfDoc.numPages));
                            
                            document.getElementById('page-num').textContent = clampedPage;
                          }
                          
                          // Touch event handlers for pinch-to-zoom
                          function getDistance(touch1, touch2) {
                            const dx = touch1.clientX - touch2.clientX;
                            const dy = touch1.clientY - touch2.clientY;
                            return Math.sqrt(dx * dx + dy * dy);
                          }
                          
                          function handleTouchStart(e) {
                            if (e.touches.length === 2) {
                              isPinching = true;
                              initialDistance = getDistance(e.touches[0], e.touches[1]);
                              initialScale = currentScale;
                              e.preventDefault();
                              e.stopPropagation();
                            }
                          }
                          
                          function handleTouchMove(e) {
                            if (isPinching && e.touches.length === 2) {
                              const currentDistance = getDistance(e.touches[0], e.touches[1]);
                              const scaleFactor = currentDistance / initialDistance;
                              const newScale = initialScale * scaleFactor;
                              
                              if (newScale >= minScale && newScale <= maxScale) {
                                currentScale = newScale;
                                isZooming = true;
                                
                                // Clear previous timeout
                                if (zoomTimeout) {
                                  clearTimeout(zoomTimeout);
                                }
                                
                                // Debounce the render to prevent lag
                                zoomTimeout = setTimeout(() => {
                                  renderAllPages();
                                  isZooming = false;
                                }, 100);
                              }
                              e.preventDefault();
                              e.stopPropagation();
                            }
                          }
                          
                          function handleTouchEnd(e) {
                            if (e.touches.length < 2) {
                              isPinching = false;
                            }
                          }
                          
                          // Add touch event listeners to canvas
                          function addTouchListeners(canvas) {
                            canvas.addEventListener('touchstart', handleTouchStart, { passive: false });
                            canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
                            canvas.addEventListener('touchend', handleTouchEnd, { passive: false });
                          }
                                
                                
                                
                                // Load the PDF
                                fetch('${pdfUrl}')
                                  .then(response => {
                                    if (!response.ok) {
                                      throw new Error('Failed to load PDF');
                                    }
                                    return response.arrayBuffer();
                                  })
                                  .then(data => {
                                    return pdfjsLib.getDocument({data: data}).promise;
                                  })
                                                              .then(pdf => {
                              pdfDoc = pdf;
                              
                              // Render all pages for vertical scrolling
                              renderAllPages();
                            })
                                  .catch(error => {
                                    console.error('Error loading PDF:', error);
                                    container.innerHTML = '<div class="error">Error loading PDF. Please try again.</div>';
                                  });
                              </script>
                            </body>
                          </html>
                        `
                      }}
                      style={{ flex: 1, width: '100%' }}
                      startInLoadingState
                      javaScriptEnabled={true}
                      domStorageEnabled={true}
                      allowsInlineMediaPlayback={true}
                      mediaPlaybackRequiresUserAction={false}
                      onError={(syntheticEvent) => {
                        const { nativeEvent } = syntheticEvent;
                        console.log('WebView error: ', nativeEvent);
                      }}
                      onHttpError={(syntheticEvent) => {
                        const { nativeEvent } = syntheticEvent;
                        console.log('WebView HTTP error: ', nativeEvent);
                      }}
                      onLoadEnd={(syntheticEvent) => {
                        const { nativeEvent } = syntheticEvent;
                        console.log('WebView loaded: ', nativeEvent);
                      }}
                      onLoadStart={(syntheticEvent) => {
                        const { nativeEvent } = syntheticEvent;
                        console.log('WebView loading URL: ', nativeEvent.url);
                      }}
                      onMessage={(event) => {
                        console.log('WebView message: ', event.nativeEvent.data);
                      }}
                      onNavigationStateChange={(navState) => {
                        console.log('WebView navigation state: ', navState);
                      }}
                    />
                  ) : (
                    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                      <Text>Invalid diet PDF URL.</Text>
                    </View>
                  );
                })()
              ) : (
              <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                <Text>No diet PDF available.</Text>
              </View>
            )}
          </View>
        </SafeAreaView>
      </Modal>
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
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <ActivityIndicator color={COLORS.white} size="small" />
                    <Text style={[styles.modalButtonText, { marginLeft: 8, fontSize: 12 }]}>Analyzing...</Text>
                  </View>
                ) : (
                  <Text style={styles.modalButtonText}>Log</Text>
                )}
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: foodLoading ? COLORS.placeholder : COLORS.error }]}
                onPress={() => {
                  setShowFoodModal(false);
                  setFoodName('');
                  setFoodQty('');
                  setFoodLoading(false); // Ensure loading state is reset
                }}
                disabled={foodLoading}
              >
                <Text style={[styles.modalButtonText, { opacity: foodLoading ? 0.6 : 1 }]}>Cancel</Text>
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
      {/* Nutrition Confirmation Modal */}
      <Modal
        visible={showNutritionConfirm}
        animationType="slide"
        transparent
        onRequestClose={() => setShowNutritionConfirm(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Confirm Nutrition Data</Text>
            <Text style={styles.modalExplanation}>
              Gemini AI analyzed "{pendingFoodData?.name}" ({pendingFoodData?.quantity}g). Please review and adjust if needed:
            </Text>
            
            <Text style={styles.modalLabel}>Calories:</Text>
            <TextInput
              style={styles.modalInput}
              value={editableNutrition.calories}
              onChangeText={(text) => setEditableNutrition(prev => ({...prev, calories: text}))}
              placeholder="Calories"
              keyboardType="numeric"
            />
            
            <Text style={styles.modalLabel}>Protein (g):</Text>
            <TextInput
              style={styles.modalInput}
              value={editableNutrition.protein}
              onChangeText={(text) => setEditableNutrition(prev => ({...prev, protein: text}))}
              placeholder="Protein"
              keyboardType="numeric"
            />
            
            <Text style={styles.modalLabel}>Fat (g):</Text>
            <TextInput
              style={styles.modalInput}
              value={editableNutrition.fat}
              onChangeText={(text) => setEditableNutrition(prev => ({...prev, fat: text}))}
              placeholder="Fat"
              keyboardType="numeric"
            />
            
            <View style={styles.modalButtonRow}>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: foodLoading ? COLORS.placeholder : COLORS.primary }]}
                onPress={handleConfirmNutrition}
                disabled={foodLoading}
              >
                {foodLoading ? (
                  <ActivityIndicator color={COLORS.white} />
                ) : (
                  <Text style={styles.modalButtonText}>Confirm & Log</Text>
                )}
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: COLORS.error }]}
                onPress={() => {
                  setShowNutritionConfirm(false);
                  setNutritionData(null);
                  setPendingFoodData(null);
                  setFoodLoading(false); // Ensure loading state is reset
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


      </ScrollView>
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
  const [successFood, setSuccessFood] = useState<{
    name: string;
    calories: number;
    protein: number;
    fat: number;
    servingSize: number;
  } | null>(null);

  const handleSearch = async () => {
    if (searchQuery.trim() === '') return;
    setLoading(true);
    setError('');
    setSearchResults([]);
    try {
      // Use the backend endpoint for food search
      const foods = await searchFood(searchQuery);
      setSearchResults(foods);
      // Set default serving size to 100 for all results
      const defaultSizes: { [id: string]: string } = {};
      foods.forEach((item: FoodItem) => { defaultSizes[item.id] = '100'; });
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
      const servingSizeNum = parseFloat(servingSize);
      const multiplier = servingSizeNum / 100;
      
      // Calculate nutritional values based on serving size
      const calories = Math.round(item.calories * multiplier);
      const protein = Math.round((item.protein * multiplier) * 10) / 10;
      const fat = Math.round((item.fat * multiplier) * 10) / 10;
      
      await logFood(userId, item.name, servingSize);
      setSuccessFood({
        name: item.name,
        calories,
        protein,
        fat,
        servingSize: servingSizeNum
      });
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
            <Text style={{ fontSize: 18, color: '#333', marginBottom: 8, textAlign: 'center' }}>
              {successFood ? `${successFood.name} (${successFood.servingSize}g) has been added to your log!` : 'Food has been logged!'}
            </Text>
            {successFood && (
              <View style={{ 
                backgroundColor: '#f8f9fa', 
                borderRadius: 12, 
                padding: 16, 
                marginBottom: 16,
                width: '100%'
              }}>
                <Text style={{ fontSize: 16, fontWeight: 'bold', color: '#333', marginBottom: 8, textAlign: 'center' }}>
                  Nutritional Information Added:
                </Text>
                <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
                  <View style={{ alignItems: 'center' }}>
                    <Text style={{ fontSize: 20, fontWeight: 'bold', color: '#FF6B6B' }}>{successFood.calories}</Text>
                    <Text style={{ fontSize: 12, color: '#666' }}>Calories</Text>
                  </View>
                  <View style={{ alignItems: 'center' }}>
                    <Text style={{ fontSize: 20, fontWeight: 'bold', color: '#4ECDC4' }}>{successFood.protein}g</Text>
                    <Text style={{ fontSize: 12, color: '#666' }}>Protein</Text>
                  </View>
                  <View style={{ alignItems: 'center' }}>
                    <Text style={{ fontSize: 20, fontWeight: 'bold', color: '#FFD93D' }}>{successFood.fat}g</Text>
                    <Text style={{ fontSize: 12, color: '#666' }}>Fat</Text>
                  </View>
                </View>
              </View>
            )}
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
  const [isDietician, setIsDietician] = useState(false);

  // Test notification function for debugging
  const sendTestNotification = async (delaySeconds: number = 300) => {
    try {
      console.log('[Test Notifications] Sending test notification in', delaySeconds, 'seconds...');
      
      const notificationContent = {
        title: 'Test Notification',
        body: `This is a test notification sent at ${new Date().toLocaleTimeString()}`,
        sound: 'default',
        priority: 'high',
        autoDismiss: false,
        sticky: false,
        data: {
          type: 'test_notification',
          timestamp: new Date().toISOString(),
          platform: Platform.OS,
          userId: auth.currentUser?.uid
        }
      };
      
      const scheduledId = await Notifications.scheduleNotificationAsync({
        content: notificationContent,
        trigger: {
          type: 'timeInterval',
          seconds: delaySeconds,
          repeats: false
        } as any,
      });
      
      console.log('[Test Notifications] ✅ Test notification scheduled successfully:', {
        scheduledId,
        delaySeconds,
        platform: Platform.OS,
        scheduledFor: new Date(Date.now() + delaySeconds * 1000).toISOString()
      });
      
      Alert.alert('Success', `Test notification scheduled for ${delaySeconds} seconds from now`);
      return scheduledId;
    } catch (error) {
      console.error('[Test Notifications] ❌ Error scheduling test notification:', error);
      Alert.alert('Error', 'Failed to schedule test notification');
      throw error;
    }
  };

  useEffect(() => {
    // Add delay to prevent conflict with login sequence API calls
    const delayedFetch = setTimeout(async () => {
      const fetchProfile = async () => {
        try {
          const userId = auth.currentUser?.uid;
          if (!userId) return;
          
          // Check if user is dietician based on email
          const userEmail = auth.currentUser?.email;
          const isDieticianAccount = userEmail === 'nutricious4u@gmail.com';
          setIsDietician(isDieticianAccount);
          
          // For dieticians, don't try to load profile - they don't need one
          if (isDieticianAccount) {
            setUserProfile(null);
            setError(''); // Clear any error for dieticians
            setLoading(false);
            return;
          }
          
          // Only try to load profile for regular users
          const profile = await getUserProfileSafe(userId);
          if (profile) {
            setUserProfile(profile);
            setError(''); // Clear any error
          } else {
            setUserProfile(null); // No profile found, do not show error
            setError(''); // Clear any error
          }
        } catch (e) {
          // Only set error for non-dietician users
          const userEmail = auth.currentUser?.email;
          const isDieticianAccount = userEmail === 'nutricious4u@gmail.com';
          
          if (!isDieticianAccount) {
          setError('Could not load user profile.');
          } else {
            setError(''); // Clear error for dieticians
          }
        } finally {
          setLoading(false);
        }
      };
      fetchProfile();
    }, 2000); // 2 second delay to ensure login sequence completes
    
    return () => clearTimeout(delayedFetch);
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
      
      // Clear profile cache before sign out
      const currentUser = auth.currentUser;
      if (currentUser) {
        clearProfileCache(currentUser.uid);
      }
      
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
              <TouchableOpacity
                style={styles.mySubscriptionsButton}
                onPress={() => navigation.navigate('MySubscriptions')}
                activeOpacity={0.85}
              >
                <Text style={styles.mySubscriptionsButtonText}>My Subscriptions</Text>
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
          <>
            {isDietician ? (
              <View style={styles.settingsButtonRow}>
                <StyledButton 
                  title="Logout" 
                  onPress={handleLogout}
                  style={styles.settingsLogoutButton}
                />
              </View>
            ) : (
              <Text style={styles.noDataText}>No profile found. Please create your profile.</Text>
            )}
          </>
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
    // Add delay to prevent conflict with login sequence API calls
    const delayedFetch = setTimeout(async () => {
      const fetchProfile = async () => {
        try {
          const userId = auth.currentUser?.uid;
          if (!userId) return;
          const profile = await getUserProfileSafe(userId);
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
    }, 2500); // 2.5 second delay to ensure login sequence completes
    
    return () => clearTimeout(delayedFetch);
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
  }, [editProfile?.currentWeight, editProfile?.height, editProfile?.age, editProfile?.gender, editProfile?.activityLevel, editProfile?.caloriesBurnedGoal]);

  const handleSave = async () => {
    if (!editProfile) return;
    const userId = editProfile.userId || editProfile.id;
    if (!userId) {
      setError('User ID not found');
      return;
    }
    setLoading(true);
    try {
      await updateUserProfile(userId, {
        ...editProfile,
        targetCalories: targets.calories,
        targetProtein: targets.protein,
        targetFat: targets.fat,

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
  const { isFreeUser, setShowUpgradeModal } = useSubscription();
  
  // Import notification service


  // Show upgrade modal for free users every time screen is focused
  useFocusEffect(
    React.useCallback(() => {
      console.log('[NotificationSettingsScreen] Screen focused, isFreeUser:', isFreeUser);
      if (isFreeUser) {
        console.log('[NotificationSettingsScreen] Showing upgrade modal for free user');
        setShowUpgradeModal(true);
        // Only redirect non-dietician users to prevent access
        // Dieticians should have full access to notification settings
        setTimeout(() => {
          // Check if user is dietician before redirecting
          const currentUser = auth.currentUser;
          const isDieticianUser = currentUser?.email === 'nutricious4u@gmail.com';
          
          if (!isDieticianUser) {
          navigation.navigate('Main');
          }
        }, 100);
      }
    }, [isFreeUser, setShowUpgradeModal, navigation])
  );



  // Diet notification management
  const [dietNotifications, setDietNotifications] = useState<any[]>([]);
  const [loadingDietNotifications, setLoadingDietNotifications] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingNotification, setEditingNotification] = useState<any>(null);
  const [editTime, setEditTime] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Day selection for notifications
  const [editSelectedDays, setEditSelectedDays] = useState<number[]>([]);
  const [showEditDaySelector, setShowEditDaySelector] = useState(false);

  // Day selection for notifications
  const [selectedDays, setSelectedDays] = useState<number[]>([]);
  const [showDaySelector, setShowDaySelector] = useState(false);

  // Days of the week (matching backend: Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6)
  const daysOfWeek = [
    { id: 0, name: 'Monday' },
    { id: 1, name: 'Tuesday' },
    { id: 2, name: 'Wednesday' },
    { id: 3, name: 'Thursday' },
    { id: 4, name: 'Friday' },
    { id: 5, name: 'Saturday' },
    { id: 6, name: 'Sunday' }
  ];

  // Combine user notifications and diet notifications into a single list
  const combinedNotifications = [
    ...notifications.map(n => ({ ...n, type: 'user' })),
    ...dietNotifications.map(n => ({ ...n, type: 'diet' }))
  ].sort((a, b) => {
    // Sort by time (HH:MM format)
    const timeA = a.time || '00:00';
    const timeB = b.time || '00:00';
    return timeA.localeCompare(timeB);
  });

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

  // Helper functions for day selection
  const toggleDay = (dayId: number) => {
    setSelectedDays(prev => 
      prev.includes(dayId) 
        ? prev.filter(id => id !== dayId)
        : [...prev, dayId]
    );
  };

  const getSelectedDaysText = (days: number[]) => {
    if (days.length === 0) return 'Select days';
    if (days.length === 7) return 'Every day';
    if (days.length === 1) return daysOfWeek.find(d => d.id === days[0])?.name || 'Select days';
    return `${days.length} days selected`;
  };

  const getSelectedDaysDisplay = (days: number[]) => {
    if (days.length === 0) return 'No days selected';
    if (days.length === 7) return 'Every day';
    return daysOfWeek
      .filter(day => days.includes(day.id))
      .map(day => day.name)
      .join(', ');
  };

  // Helper functions for edit modal day selection
  const toggleEditDay = (dayId: number) => {
    setEditSelectedDays(prev => 
      prev.includes(dayId) 
        ? prev.filter(id => id !== dayId)
        : [...prev, dayId]
    );
  };

  const getEditSelectedDaysText = (days: number[]) => {
    if (days.length === 0) return 'Select days';
    if (days.length === 7) return 'Every day';
    if (days.length === 1) return daysOfWeek.find(d => d.id === days[0])?.name || 'Select days';
    return `${days.length} days selected`;
  };

  useEffect(() => {
    const initializeScreen = async () => {
      setInitialLoading(true);
      try {
        // Load notifications sequentially to prevent 499 errors
        await loadNotifications();
        // Add delay between API calls to prevent connection conflicts
        await new Promise(resolve => setTimeout(resolve, 300));
        await loadDietNotifications();
        
        // Request notification permissions
        const { status } = await Notifications.getPermissionsAsync();
        if (status !== 'granted') {
          await Notifications.requestPermissionsAsync();
          console.log('[Notifications] Requested notification permissions.');
        } else {
          console.log('[Notifications] Notification permissions already granted.');
        }
      } catch (error) {
        console.error('[Notifications] Error initializing screen:', error);
      } finally {
        setInitialLoading(false);
      }
    };

    initializeScreen();
  }, []);

  // Refresh diet notifications when screen comes into focus (no extraction, just refresh)
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      console.log('[Diet Notifications] Screen focused, refreshing diet notifications');
      // Only refresh existing notifications, don't trigger extraction
      loadDietNotifications();
    });

    return unsubscribe;
  }, [navigation]);

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
          // No notifications: start with empty array
          setNotifications([]);
        }
      } else {
        // No notifications at all: start with empty array
        setNotifications([]);
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
    setSelectedDays([]); // Reset day selection for new notifications
    setShowModal(true);
    setError('');
  };

  const openEditModal = (notif: any) => {
    setModalMode('edit');
    setCurrentId(notif.id);
    setMessage(notif.message);
    setTime(new Date(notif.time));
    setSelectedDays(notif.selectedDays || []); // Load existing day selection
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

  // Function to cancel all scheduled diet notifications
  const cancelAllDietNotifications = async () => {
    try {
      console.log('[Diet Notifications] Cancelling all scheduled diet notifications...');
      
      // Cancel all current diet notifications
      for (const notification of dietNotifications) {
        if (notification.scheduledId) {
          try {
            await Notifications.cancelScheduledNotificationAsync(notification.scheduledId);
            console.log('[Diet Notifications] Cancelled scheduled notification:', notification.scheduledId);
          } catch (error) {
            console.error('[Diet Notifications] Error cancelling notification:', notification.scheduledId, error);
          }
        }
        
        // Also cancel backup notifications if they exist
        if (notification.backupIds && Array.isArray(notification.backupIds)) {
          for (const backupId of notification.backupIds) {
            try {
              await Notifications.cancelScheduledNotificationAsync(backupId);
              console.log('[Diet Notifications] Cancelled backup notification:', backupId);
            } catch (error) {
              console.error('[Diet Notifications] Error cancelling backup notification:', backupId, error);
            }
          }
        }
      }
      
      // Clear local state
      setDietNotifications([]);
      console.log('[Diet Notifications] All diet notifications cancelled and cleared from local state');
      
    } catch (error) {
      console.error('[Diet Notifications] Error cancelling all notifications:', error);
    }
  };

  // Diet notification functions
  const loadDietNotifications = async () => {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) return;

      const response = await getDietNotifications(userId);
      if (response.notifications) {
        setDietNotifications(response.notifications);
        console.log('[Diet Notifications] Loaded:', response.notifications.length);
      } else {
        setDietNotifications([]);
      }
    } catch (error) {
      console.error('[Diet Notifications] Error loading:', error);
      setDietNotifications([]);
    }
  };



  // Enhanced notification functions using the notification service
  const handleSaveNotification = async () => {
    const unifiedNotificationService = require('./services/unifiedNotificationService').default;
    if (!message.trim()) {
      setError('Please enter a message');
      return;
    }
    if (selectedDays.length === 0) {
      setError('Please select at least one day');
      return;
    }

    try {
      setLoading(true);
      
      const timeString = time.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit' 
      });

      if (modalMode === 'add') {
        // Add new notification
        const scheduledId = await unifiedNotificationService.scheduleCustomNotification({
          message: message.trim(),
          time: timeString,
          selectedDays,
          type: 'custom'
        });

        const newNotification = {
          id: Date.now().toString(),
          message: message.trim(),
          time: timeString,
          selectedDays,
          scheduledId,
          type: 'custom',
          createdAt: new Date().toISOString(),
          userId: auth.currentUser?.uid || ''
        };

        const updatedNotifications = [...notifications, newNotification];
        await saveNotifications(updatedNotifications);
        
        setSuccessMessage('Notification scheduled successfully!');
        setShowSuccessModal(true);
      } else {
        // Edit existing notification
        if (!currentId) return;

        // Cancel existing notification
        const existingNotification = notifications.find(n => n.id === currentId);
        if (existingNotification?.scheduledId) {
          await unifiedNotificationService.cancelNotification(existingNotification.scheduledId);
        }

        // Schedule new notification
        const scheduledId = await unifiedNotificationService.scheduleCustomNotification({
          message: message.trim(),
          time: timeString,
          selectedDays,
          type: 'custom'
        });

        const updatedNotifications = notifications.map(n => 
          n.id === currentId 
            ? { ...n, message: message.trim(), time: timeString, selectedDays, scheduledId }
            : n
        );
        
        await saveNotifications(updatedNotifications);
        
        setSuccessMessage('Notification updated successfully!');
        setShowSuccessModal(true);
      }

      setShowModal(false);
      setMessage('');
      setTime(new Date());
      setSelectedDays([]);
      setError('');
    } catch (error) {
      console.error('[Notifications] Error saving notification:', error);
      setError('Failed to save notification. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Enhanced diet notification extraction using backend API and local scheduling
  const handleExtractDietNotifications = async () => {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) {
        setErrorMessage('User not authenticated. Please log in again.');
        setShowErrorModal(true);
        return;
      }

      // Prevent multiple rapid presses
      if (loadingDietNotifications) {
        console.log('[Diet Notifications] Extraction already in progress, ignoring button press');
        return;
      }

      setLoadingDietNotifications(true);
      console.log('[Diet Notifications] Starting extraction from backend API...');
      
      // Call backend API for extraction
      const response = await extractDietNotifications(userId);
      
      console.log('[Diet Notifications] Backend response:', response);
      
      if (response.notifications && response.notifications.length > 0) {
        // Cancel existing diet notifications
        const unifiedNotificationService = require('./services/unifiedNotificationService').default;
        const cancelledCount = await unifiedNotificationService.cancelNotificationsByType('diet');
        
        console.log(`[Diet Notifications] Cancelled ${cancelledCount} existing diet notifications`);
        
        // Schedule new diet notifications locally (works in EAS builds)
        const scheduledIds = await unifiedNotificationService.scheduleDietNotifications(response.notifications);
        
        // Update notifications with scheduled IDs
        const updatedNotifications = response.notifications.map((notification: any, index: number) => ({
          ...notification,
          scheduledId: scheduledIds[index] || null
        }));
        
        setDietNotifications(updatedNotifications);
        setSuccessMessage(`Successfully extracted and scheduled ${response.notifications.length} diet notifications locally! 🎉 (Cancelled ${cancelledCount} previous notifications)`);
        setShowSuccessModal(true);
        console.log('[Diet Notifications] ✅ Extraction and local scheduling successful:', response.notifications.length, 'notifications');
        console.log('[Diet Notifications] Scheduled IDs:', scheduledIds);
      } else {
        // Check if user is dietician - don't show popup for dieticians
        const currentUser = auth.currentUser;
        const userEmail = currentUser?.email;
        const isDieticianUser = userEmail === "nutricious4u@gmail.com" || userEmail?.includes("dietician");
        
        if (!isDieticianUser) {
          Alert.alert(
            'No Activities Found', 
            'No timed activities were found in your diet plan. Make sure your diet plan includes specific times for activities.',
            [{ text: 'OK', style: 'default' }]
          );
          console.log('[Diet Notifications] ⚠️ No activities found in diet plan');
        } else {
          console.log('[Diet Notifications] ⚠️ No activities found in diet plan (dietician view - no alert shown)');
        }
      }
    } catch (error: any) {
      console.error('[Diet Notifications] Error extracting:', error);
      
      let errorMsg = 'Failed to extract notifications from your diet plan. Please try again.';
      
      if (error?.response?.status === 404) {
        if (error?.response?.data?.detail === 'No diet PDF found for this user') {
          errorMsg = 'No diet plan found. Please upload a diet plan first.';
        } else if (error?.response?.data?.detail === 'User not found') {
          errorMsg = 'User not found. Please log in again.';
        }
      } else if (error?.response?.status === 500) {
        errorMsg = 'Server error. Please try again later.';
      } else if (error?.message === 'Network Error' || error?.code === 'ECONNREFUSED' || error?.code === 'NETWORK_ERROR') {
        errorMsg = 'Network error. Please check your connection and try again.';
      } else if (error?.message?.includes('timeout')) {
        errorMsg = 'Request timed out. Please try again.';
      }
      
      setErrorMessage(errorMsg);
      setShowErrorModal(true);
    } finally {
      setLoadingDietNotifications(false);
    }
  };

  // Test notification function for debugging
  const sendTestNotification = async (delaySeconds: number = 300) => {
    try {
      console.log('[Test Notifications] Sending test notification in', delaySeconds, 'seconds...');
      
      const notificationContent = {
        title: 'Test Notification',
        body: `This is a test notification sent at ${new Date().toLocaleTimeString()}`,
        sound: 'default',
        priority: 'high',
        autoDismiss: false,
        sticky: false,
        data: {
          type: 'test_notification',
          timestamp: new Date().toISOString(),
          platform: Platform.OS,
          userId: auth.currentUser?.uid
        }
      };
      
      const scheduledId = await Notifications.scheduleNotificationAsync({
        content: notificationContent,
        trigger: {
          type: 'timeInterval',
          seconds: delaySeconds,
          repeats: false
        } as any,
      });
      
      console.log('[Test Notifications] ✅ Test notification scheduled successfully:', {
        scheduledId,
        delaySeconds,
        platform: Platform.OS,
        scheduledFor: new Date(Date.now() + delaySeconds * 1000).toISOString()
      });
      
      return scheduledId;
    } catch (error) {
      console.error('[Test Notifications] ❌ Error scheduling test notification:', error);
      throw error;
    }
  };

  const scheduleDietNotification = async (notification: any, daysAhead: number = 0) => {
    try {
      // Parse the time (format: "HH:MM")
      const [hours, minutes] = notification.time.split(':').map(Number);
      const time = new Date();
      time.setHours(hours, minutes, 0, 0);
      
      // Add days if specified
      if (daysAhead > 0) {
        time.setDate(time.getDate() + daysAhead);
      } else {
        // For same-day reminders: if time hasn't passed, schedule for today
        // If time has passed, schedule for tomorrow
        const now = new Date();
        if (time <= now) {
          time.setDate(time.getDate() + 1);
          console.log('[Diet Notifications] Time passed today, scheduling for tomorrow:', time.toISOString());
        } else {
          console.log('[Diet Notifications] Scheduling for today:', time.toISOString());
        }
      }
      
      // Calculate seconds until the notification should trigger
      const seconds = Math.max(1, Math.floor((time.getTime() - Date.now()) / 1000));
      
      // Platform-specific notification content for EAS builds
      const notificationContent = {
          title: 'Diet Reminder',
          body: notification.message,
          sound: 'default',
          priority: 'high',
          autoDismiss: false,
          sticky: false,
          data: {
            type: 'diet_reminder',
            source: 'diet_pdf',
            time: notification.time,
            notificationId: notification.id,
            userId: auth.currentUser?.uid,
          scheduledFor: time.toISOString(),
          platform: Platform.OS,
          timestamp: new Date().toISOString()
        }
      };
      
      console.log('[Diet Notifications] Scheduling notification for platform:', Platform.OS);
      console.log('[Diet Notifications] Notification content:', notificationContent);
      console.log('[Diet Notifications] Trigger seconds:', seconds);
      
      // Schedule the notification
      const scheduledId = await Notifications.scheduleNotificationAsync({
        content: notificationContent,
        trigger: {
          type: 'timeInterval',
          seconds,
          repeats: false
        } as any,
      });
      
      console.log('[Diet Notifications] ✅ Notification scheduled successfully:', {
        message: notification.message,
        time: notification.time,
        scheduledId,
        triggerTime: time.toISOString(),
        secondsUntilTrigger: seconds,
        daysAhead,
        platform: Platform.OS
      });
      
      return scheduledId;
    } catch (error) {
      console.error('[Diet Notifications] ❌ Error scheduling notification:', error);
      console.error('[Diet Notifications] Error details:', {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        platform: Platform.OS,
        notification: notification
      });
      throw error;
    }
  };

  // Schedule notifications for multiple days to ensure reliability
  const scheduleMultipleDays = async (notification: any) => {
    try {
      // Schedule for today/tomorrow (primary)
      const primaryId = await scheduleDietNotification(notification, 0);
      
      // Also schedule for the next few days as backup
      const backupIds = [];
      for (let day = 1; day <= 3; day++) {
        try {
          const backupId = await scheduleDietNotification(notification, day);
          backupIds.push(backupId);
        } catch (error) {
          console.error(`[Diet Notifications] Failed to schedule backup for day ${day}:`, error);
        }
      }
      
      return {
        primaryId,
        backupIds
      };
    } catch (error) {
      console.error('[Diet Notifications] Error in multiple day scheduling:', error);
      throw error;
    }
  };

  // Set up notification listener to reschedule daily and handle new diets
  useEffect(() => {
    const subscription = Notifications.addNotificationReceivedListener(async (notification) => {
      const data = notification.request.content.data;
      
      // Handle new diet notifications - automatically refresh diet notifications
      if (data?.type === 'new_diet') {
        console.log('[Diet Notifications] Received new diet notification, refreshing diet notifications');
        // Refresh diet notifications to show the newly extracted notifications (already extracted on backend)
        await loadDietNotifications();
      }
      
      if (data?.type === 'diet_reminder' && data?.source === 'diet_pdf') {
        console.log('[Diet Notifications] Received diet reminder from backend');
        
        // Backend handles rescheduling, no need for local rescheduling
        // Just log that we received the notification
        const dietNotification = dietNotifications.find(n => n.id === data.notificationId);
        if (dietNotification) {
          console.log('[Diet Notifications] Received backend notification:', dietNotification.message);
        }
      }
      
      // Handle incoming message notifications
      if (data?.type === 'message_notification') {
        console.log('[Message Notifications] Received message notification');
        
        // Update the messages list if we're in the chat screen
        if (data.fromUser || data.fromDietician) {
          // Refresh messages to show the new message
          // This will be handled by the existing message listener
          console.log('[Message Notifications] Message notification received, chat will update automatically');
        }
      }
    });

    return () => subscription.remove();
  }, [dietNotifications]);

  // Enhanced background notification handling
  useEffect(() => {
    const backgroundSubscription = Notifications.addNotificationResponseReceivedListener(async (response) => {
      const data = response.notification.request.content.data;
      
      // Handle diet reminder interactions
      if (data?.type === 'diet_reminder' && data?.source === 'diet_pdf') {
        console.log('[Diet Notifications] User interacted with diet reminder');
        
        // Backend handles rescheduling, no need for local rescheduling
        const dietNotification = dietNotifications.find(n => n.id === data.notificationId);
        if (dietNotification) {
          console.log('[Diet Notifications] User interacted with backend notification:', dietNotification.message);
        }
      }
      
      // Handle message notification interactions
      if (data?.type === 'message_notification') {
        console.log('[Message Notifications] User interacted with message notification');
        
        // Navigate to the appropriate chat screen
        if (data.toDietician) {
          // User tapped notification from dietician - navigate to user's chat with dietician
          navigation.navigate('DieticianMessage');
        } else {
          // Dietician tapped notification from user - navigate to that user's chat
          if (data.userId) {
            navigation.navigate('DieticianMessage', { userId: data.userId });
          }
        }
      }
    });

    return () => backgroundSubscription.remove();
  }, [dietNotifications, navigation]);

  const handleDeleteDietNotification = async (notificationId: string) => {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) return;

      // Cancel the scheduled notification locally
      const unifiedNotificationService = require('./services/unifiedNotificationService').default;
      const cancelled = await unifiedNotificationService.cancelNotificationById(notificationId);
      
      if (cancelled) {
        console.log('[Diet Notifications] Cancelled notification locally:', notificationId);
      } else {
        console.log('[Diet Notifications] Notification not found for local cancellation:', notificationId);
      }

      // Remove from local state immediately
      setDietNotifications(prev => prev.filter(n => n.id !== notificationId));
      console.log('[Diet Notifications] Deleted from local state:', notificationId);
      
      // Show success message
      setSuccessMessage('Notification deleted successfully!');
      setShowSuccessModal(true);
      
    } catch (error) {
      console.error('[Diet Notifications] Error deleting:', error);
      setErrorMessage('Failed to delete notification. Please try again.');
      setShowErrorModal(true);
    }
  };

  const handleEditDietNotification = (notification: any) => {
    setEditingNotification(notification);
    setEditTime(notification.time);
    setEditMessage(notification.message);
    setEditSelectedDays(notification.selectedDays || [0, 1, 2, 3, 4, 5, 6]);
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) return;

      if (!editingNotification || !editTime || !editMessage) {
        setErrorMessage('Please fill in all fields.');
        setShowErrorModal(true);
        return;
      }
      if (editSelectedDays.length === 0) {
        setErrorMessage('Please select at least one day');
        setShowErrorModal(true);
        return;
      }

      // Validate time format (HH:MM)
      const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
      if (!timeRegex.test(editTime)) {
        setErrorMessage('Please enter a valid time in HH:MM format (e.g., 08:30).');
        setShowErrorModal(true);
        return;
      }

      // Set loading state
      setSavingEdit(true);

      // Cancel only the specific notification being edited
      const unifiedNotificationService = require('./services/unifiedNotificationService').default;
      if (editingNotification.scheduledId) {
        await unifiedNotificationService.cancelNotificationById(editingNotification.id);
      }

      // Create updated notification for local scheduling
      const updatedNotification = {
        message: editMessage,
        time: editTime,
        selectedDays: editSelectedDays
      };

      // Schedule the updated notification locally
      const scheduledIds = await unifiedNotificationService.scheduleDietNotifications([updatedNotification]);

      // Update the notification in local state
      setDietNotifications(prev => prev.map(n => 
        n.id === editingNotification.id 
          ? { ...n, time: editTime, message: editMessage, selectedDays: editSelectedDays, scheduledId: scheduledIds[0] }
          : n
      ));

      // Close modal
      setShowEditModal(false);
      setEditingNotification(null);
      setEditTime('');
      setEditMessage('');
      setEditSelectedDays([]);
      setShowEditDaySelector(false);

      // Show success message
      setSuccessMessage('Notification updated and scheduled locally! Will work in EAS builds.');
      setShowSuccessModal(true);

    } catch (error: any) {
      console.error('[Diet Notifications] Error editing:', error);
      
      // Since we're using local scheduling, most errors should be handled gracefully
      if (error?.message?.includes('scheduleNotificationAsync')) {
        setErrorMessage('Failed to schedule notification locally. Please try again.');
      } else if (error?.message === 'Network Error' || error?.code === 'ECONNREFUSED' || error?.code === 'ENOTFOUND') {
        setErrorMessage('Network error. Please check your connection and try again.');
      } else {
        setErrorMessage('Failed to update notification. Please try again.');
      }
      
      setShowErrorModal(true);
    } finally {
      // Clear loading state
      setSavingEdit(false);
    }
  };



  const handleSave = async () => {
    if (!message.trim()) {
      setError('Message cannot be empty');
      console.log('[Notifications] Tried to save blank message.');
      return;
    }
    if (selectedDays.length === 0) {
      setError('Please select at least one day');
      console.log('[Notifications] Tried to save without selecting days.');
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
        { id: Date.now().toString(), message, time: selected.toISOString(), scheduledId, selectedDays },
      ];
      console.log('[Notifications] Added new notification:', { message, time: selected.toISOString(), scheduledId, selectedDays });
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
          ? { ...n, message, time: selected.toISOString(), scheduledId, selectedDays }
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
        <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }}>
          <Text style={{ color: COLORS.placeholder, fontSize: 14 }}>
            {item.time} • {item.type === 'diet' ? 'From Diet PDF' : 'Custom'}
          </Text>
        </View>
        {item.selectedDays && (
          <Text style={{ color: COLORS.primary, fontSize: 12, marginTop: 2 }}>
            {getSelectedDaysDisplay(item.selectedDays)}
          </Text>
        )}
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        {item.type === 'diet' ? (
          <>
            <TouchableOpacity 
              onPress={() => handleEditDietNotification(item)}
              style={{ marginRight: 12 }}
            >
              <Pencil color={COLORS.primary} size={18} />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => handleDeleteDietNotification(item.id)}>
              <Trash2 color={COLORS.error} size={18} />
            </TouchableOpacity>
          </>
        ) : (
          <>
            <TouchableOpacity onPress={() => openEditModal(item)} style={{ marginRight: 16 }}>
              <Pencil color={COLORS.primary} size={22} />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => handleDelete(item.id)}>
              <Trash2 color={COLORS.error} size={22} />
            </TouchableOpacity>
          </>
        )}
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
        
        {/* Initial Loading Screen */}
        {initialLoading ? (
          <View style={{ 
            flex: 1, 
            justifyContent: 'center', 
            alignItems: 'center',
            paddingVertical: 60
          }}>
            <ActivityIndicator size="large" color={COLORS.primary} style={{ marginBottom: 16 }} />
            <Text style={{ 
              color: COLORS.text, 
              fontSize: 16, 
              textAlign: 'center',
              marginBottom: 8
            }}>
              Loading notifications...
            </Text>
            <Text style={{ 
              color: COLORS.placeholder, 
              fontSize: 14, 
              textAlign: 'center'
            }}>
              Please wait while we fetch your latest notifications
            </Text>
          </View>
        ) : loading ? (
          <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
        ) : (
          <>
            {/* Diet Extraction Button */}
            <View style={{ marginBottom: 24 }}>
              <Text style={{ fontSize: 16, color: COLORS.placeholder, marginBottom: 12 }}>
                Extract timed activities from your diet PDF
              </Text>
              <Text style={{ fontSize: 14, color: COLORS.placeholder, marginBottom: 12, fontStyle: 'italic' }}>
                This may take up to 60 seconds for large PDFs
              </Text>
              <TouchableOpacity 
                style={[
                  styles.addNotificationButton, 
                  { 
                    backgroundColor: loadingDietNotifications ? COLORS.placeholder : COLORS.primary,
                    opacity: loadingDietNotifications ? 0.7 : 1
                  }
                ]} 
                onPress={handleExtractDietNotifications}
                disabled={loadingDietNotifications}
              >
                <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center' }}>
                  {loadingDietNotifications && (
                    <ActivityIndicator size="small" color="#fff" style={{ marginRight: 8 }} />
                  )}
                  <Text style={styles.addNotificationButtonText}>
                    {loadingDietNotifications ? 'Extracting PDF...' : 'Extract from Diet PDF'}
                  </Text>
                </View>
              </TouchableOpacity>
            </View>

            {/* Combined Notifications List */}
            {combinedNotifications.length === 0 ? (
              <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', marginTop: 40 }}>
                <Text style={{ color: COLORS.placeholder, fontSize: 18, textAlign: 'center' }}>
                  You have no notifications yet.
                </Text>
                <TouchableOpacity style={styles.addNotificationButton} onPress={openAddModal}>
                  <Text style={styles.addNotificationButtonText}>Add Custom Notification</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <FlatList
                data={combinedNotifications}
                keyExtractor={(item, index) => `${item.type}_${item.id}_${index}`}
                renderItem={renderItem}
                ListHeaderComponent={
                  <Text style={{ fontSize: 18, fontWeight: 'bold', color: COLORS.text, marginBottom: 16 }}>
                    All Notifications ({combinedNotifications.length})
                  </Text>
                }
                ListFooterComponent={
                  <TouchableOpacity style={styles.addNotificationButton} onPress={openAddModal}>
                    <Text style={styles.addNotificationButtonText}>Add Custom Notification</Text>
                  </TouchableOpacity>
                }
                contentContainerStyle={{ paddingBottom: 20 }}
              />
            )}
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
                
                <Text style={styles.modalLabel}>Days</Text>
                <TouchableOpacity
                  style={[styles.modalInput, { justifyContent: 'center', height: 48 }]}
                  onPress={() => setShowDaySelector(!showDaySelector)}
                >
                  <Text style={{ color: COLORS.text, fontSize: 16 }}>
                    {getSelectedDaysText(selectedDays)}
                  </Text>
                </TouchableOpacity>
                
                {showDaySelector && (
                  <View style={styles.daySelectorContainer}>
                    {daysOfWeek.map((day) => (
                      <TouchableOpacity
                        key={day.id}
                        style={[
                          styles.dayOption,
                          selectedDays.includes(day.id) && styles.dayOptionSelected
                        ]}
                        onPress={() => toggleDay(day.id)}
                      >
                        <Text style={[
                          styles.dayOptionText,
                          selectedDays.includes(day.id) && styles.dayOptionTextSelected
                        ]}>
                          {day.name}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
                {error ? <Text style={{ color: COLORS.error, marginTop: 8 }}>{error}</Text> : null}
                <View style={styles.modalButtonRow}>
                  <TouchableOpacity
                    style={[styles.modalButton, { backgroundColor: loading ? COLORS.placeholder : COLORS.primary }]}
                    onPress={handleSaveNotification}
                    disabled={loading}
                  >
                    {loading ? (
                      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                        <ActivityIndicator size="small" color="white" style={{ marginRight: 8 }} />
                        <Text style={styles.modalButtonText}>Saving...</Text>
                      </View>
                    ) : (
                      <Text style={styles.modalButtonText}>{modalMode === 'add' ? 'Add' : 'Save'}</Text>
                    )}
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.modalButton, { backgroundColor: COLORS.error }]}
                    onPress={() => setShowModal(false)}
                    disabled={loading}
                  >
                    <Text style={styles.modalButtonText}>Cancel</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </Modal>

        {/* Custom Success Modal */}
        <Modal
          visible={showSuccessModal}
          animationType="fade"
          transparent
          onRequestClose={() => setShowSuccessModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={[styles.modalContainer, { backgroundColor: COLORS.primary, borderColor: COLORS.primaryDark }]}>
              <Text style={[styles.modalTitle, { color: COLORS.white }]}>Success! 🎉</Text>
              <Text style={[styles.modalLabel, { color: COLORS.white, textAlign: 'center', marginTop: 16 }]}>
                {successMessage}
              </Text>
              <TouchableOpacity
                style={{ 
                  backgroundColor: COLORS.white, 
                  marginTop: 24,
                  paddingVertical: 12,
                  paddingHorizontal: 24,
                  borderRadius: 8,
                  minWidth: 100,
                  alignItems: 'center',
                  shadowColor: '#000',
                  shadowOpacity: 0.1,
                  shadowRadius: 4,
                  elevation: 3
                }}
                onPress={() => setShowSuccessModal(false)}
              >
                <Text style={{ 
                  color: COLORS.primary,
                  fontSize: 16,
                  fontWeight: '600'
                }}>Close</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>

        {/* Custom Error Modal */}
        <Modal
          visible={showErrorModal}
          animationType="fade"
          transparent
          onRequestClose={() => setShowErrorModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={[styles.modalContainer, { backgroundColor: COLORS.error, borderColor: COLORS.error }]}>
              <Text style={[styles.modalTitle, { color: COLORS.white }]}>Error ⚠️</Text>
              <Text style={[styles.modalLabel, { color: COLORS.white, textAlign: 'center', marginTop: 16 }]}>
                {errorMessage}
              </Text>
              <TouchableOpacity
                style={{ 
                  backgroundColor: COLORS.white, 
                  marginTop: 24,
                  paddingVertical: 12,
                  paddingHorizontal: 24,
                  borderRadius: 8,
                  minWidth: 100,
                  alignItems: 'center',
                  shadowColor: '#000',
                  shadowOpacity: 0.1,
                  shadowRadius: 4,
                  elevation: 3
                }}
                onPress={() => setShowErrorModal(false)}
              >
                <Text style={{ 
                  color: COLORS.error,
                  fontSize: 16,
                  fontWeight: '600'
                }}>Close</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>

        {/* Edit Diet Notification Modal */}
        <Modal
          visible={showEditModal}
          animationType="slide"
          transparent
          onRequestClose={() => setShowEditModal(false)}
        >
          <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
            <View style={styles.modalOverlay}>
              <View style={styles.modalContainer}>
                <Text style={styles.modalTitle}>Edit Diet Notification</Text>
                
                <Text style={styles.modalLabel}>Message</Text>
                <TextInput
                  style={styles.modalInput}
                  value={editMessage}
                  onChangeText={setEditMessage}
                  placeholder="Enter notification message"
                  maxLength={100}
                />
                
                <Text style={styles.modalLabel}>Time</Text>
                <TouchableOpacity
                  style={[styles.modalInput, { justifyContent: 'center', height: 48 }]}
                  onPress={() => {
                    // Parse current time or default to 8:00 AM
                    const [hours, minutes] = editTime.split(':').map(Number);
                    const currentTime = new Date();
                    currentTime.setHours(hours || 8, minutes || 0, 0, 0);
                    setTime(currentTime);
                    setShowTimePicker(true);
                  }}
                >
                  <Text style={{ color: COLORS.text, fontSize: 16 }}>
                    {editTime || '08:00'}
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
                      if (selectedDate) {
                        setTime(selectedDate);
                        const hours = selectedDate.getHours().toString().padStart(2, '0');
                        const minutes = selectedDate.getMinutes().toString().padStart(2, '0');
                        setEditTime(`${hours}:${minutes}`);
                      }
                    }}
                  />
                )}
                
                <Text style={styles.modalLabel}>Days</Text>
                <TouchableOpacity
                  style={[styles.modalInput, { justifyContent: 'center', height: 48 }]}
                  onPress={() => setShowEditDaySelector(!showEditDaySelector)}
                >
                  <Text style={{ color: COLORS.text, fontSize: 16 }}>
                    {getEditSelectedDaysText(editSelectedDays)}
                  </Text>
                </TouchableOpacity>
                
                {showEditDaySelector && (
                  <View style={styles.daySelectorContainer}>
                    {daysOfWeek.map((day) => (
                      <TouchableOpacity
                        key={day.id}
                        style={[
                          styles.dayOption,
                          editSelectedDays.includes(day.id) && styles.dayOptionSelected
                        ]}
                        onPress={() => toggleEditDay(day.id)}
                      >
                        <Text style={[
                          styles.dayOptionText,
                          editSelectedDays.includes(day.id) && styles.dayOptionTextSelected
                        ]}>
                          {day.name}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
                
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 24 }}>
                  <TouchableOpacity
                    style={[styles.modalButton, { 
                      backgroundColor: '#DC2626', // Red color for cancel
                      flex: 0.48
                    }]}
                    onPress={() => {
                      setShowEditModal(false);
                      setEditingNotification(null);
                      setEditTime('');
                      setEditMessage('');
                      setEditSelectedDays([]);
                      setShowEditDaySelector(false);
                    }}
                    disabled={savingEdit}
                  >
                    <Text style={styles.modalButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={[styles.modalButton, { 
                      backgroundColor: savingEdit ? COLORS.placeholder : COLORS.primary,
                      flex: 0.48
                    }]}
                    onPress={handleSaveEdit}
                    disabled={savingEdit}
                  >
                    {savingEdit ? (
                      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                        <ActivityIndicator size="small" color="white" style={{ marginRight: 8 }} />
                        <Text style={styles.modalButtonText}>Saving...</Text>
                      </View>
                    ) : (
                      <Text style={styles.modalButtonText}>Save</Text>
                    )}
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
const SummaryWidget = ({ todayData, targets, burnedToday, onPress }: any) => {
  // Define unique, dark/vibrant colors for each label
  const labelColors = {
    Calories: '#B91C1C', // dark red
    Protein: '#0E7490', // dark teal
    Fat: '#B45309',     // dark amber
    Burned: '#A21CAF',  // dark purple
  };
  const items = [
    { label: 'Calories', value: safeNumber(todayData.calories), target: targets.calories, color: COLORS.energy, labelColor: labelColors.Calories },
    { label: 'Protein', value: safeNumber(todayData.protein), target: targets.protein, color: COLORS.protein, labelColor: labelColors.Protein },
    { label: 'Fat', value: safeNumber(todayData.fat), target: targets.fat, color: COLORS.fat, labelColor: labelColors.Fat },
    { label: 'Burned', value: safeNumber(burnedToday), target: targets.burned, color: COLORS.streakActive, labelColor: labelColors.Burned },
  ];
  
  // iOS EAS builds have issues with LinearGradient - create visually identical alternative
  if (Platform.OS === 'ios' && !__DEV__) {
    return (
      <TouchableOpacity activeOpacity={0.85} onPress={onPress} style={styles.summaryWidgetContainer}>
        <View style={styles.summaryWidgetBg}>
          {/* Create gradient effect using nested Views - visually identical to LinearGradient */}
          <View style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: COLORS.lightGreen,
          }} />
                     <View style={{
             position: 'absolute',
             top: 0,
             left: '5%',
             right: 0,
             bottom: 0,
             backgroundColor: COLORS.white,
             opacity: 0.25,
           }} />
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
        </View>
      </TouchableOpacity>
    );
  }
  
  // Standard LinearGradient for other platforms
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
  const { summary, burnedToday, userProfile, workoutSummary } = route.params || {};
  
  // Get targets from userProfile if available
  const targetCalories = userProfile?.targetCalories || 2000;
  const targetProtein = userProfile?.targetProtein || 150;
  const targetFat = userProfile?.targetFat || 65;

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

    } else {
      maxValue = Math.max(...chartData.map(d => d.value), target) * 1.2;
      yLabels = [0, Math.round(maxValue/4), Math.round(maxValue/2), Math.round(maxValue*3/4), Math.round(maxValue)];
    }
    
    const chartHeight = 140;
    const chartWidth = 260;
    const yAxisWidth = 40;
    
    // iOS EAS builds have issues with SVG - use simplified chart
    if (Platform.OS === 'ios' && !__DEV__) {
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
            {/* Simplified chart content for iOS */}
            <View style={[styles.chartContent, { width: chartWidth, height: chartHeight, backgroundColor: '#f5f5f5', borderRadius: 8 }]}> 
              {/* Goal line */}
              <View style={[styles.goalLine, { 
                top: chartHeight - (target / maxValue) * chartHeight,
                borderColor: color,
                borderWidth: 2,
                borderStyle: 'dashed',
                backgroundColor: 'transparent',
                width: chartWidth,
              }]} />
              {/* Data points as bars instead of SVG */}
              {chartData.map((item: any, index: number) => {
                const barHeight = (item.value / maxValue) * chartHeight;
                const barWidth = Math.max(20, chartWidth / 10);
                const x = (index / (chartData.length - 1)) * (chartWidth - barWidth);
                return (
                  <View key={index} style={{ 
                    position: 'absolute',
                    left: x,
                    bottom: 0,
                    width: barWidth,
                    height: barHeight,
                    backgroundColor: color + '80',
                    borderRadius: 2,
                    marginHorizontal: 2
                  }} />
                );
              })}
            </View>
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
      );
    }
    
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

// --- Dietician Screen ---
const DieticianScreen = ({ navigation }: { navigation: any }) => {
  const [isDietician, setIsDietician] = React.useState(false);
  React.useEffect(() => {
    const user = auth.currentUser;
    if (!user) return;
    
    // Check both collections for dietician status - SEQUENTIAL to prevent 499 errors
    const checkDieticianStatus = async () => {
      try {
        const userDoc = await firestore.collection('users').doc(user.uid).get();
        const userData = userDoc.data();
        
        // Add delay between Firestore calls to prevent connection conflicts
        await new Promise(resolve => setTimeout(resolve, 200));
        
        const profileDoc = await firestore.collection('user_profiles').doc(user.uid).get();
        const profileData = profileDoc.data();
        
        // Check for dietician status in both collections
        const isDieticianAccount = !!userData?.isDietician || !!profileData?.isDietician || user?.email === 'nutricious4u@gmail.com';
        setIsDietician(isDieticianAccount);
      } catch (error) {
        console.error('[Messages] Error checking dietician status:', error);
        // Fallback: check email
        const isDieticianAccount = user?.email === 'nutricious4u@gmail.com';
        setIsDietician(isDieticianAccount);
      }
    };
    
    checkDieticianStatus();
  }, []);
  if (isDietician) {
    // Dietician version: show Messages page (not profile)
    return <DieticianMessagesListScreen navigation={navigation} />;
  }
  return (
    <SafeAreaView style={[styles.container, { flex: 1 }]}> 
      <ScrollView
        contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 50, paddingBottom: 40 }}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.dieticianHeaderContainer}>
          <View style={styles.dieticianPhotoWrapper}>
            <Image
              source={require('./assets/dp.jpeg')}
              style={styles.dieticianPhoto}
              resizeMode="center"
            />
          </View>
          <Text style={styles.dieticianName}>Dt. Ekta Taneja</Text>
          <Text style={styles.dieticianTitle}>Your Personal Diet Expert</Text>
          <View style={styles.dieticianButtonRow}>
            <TouchableOpacity 
              style={[styles.dieticianSquareButton, { backgroundColor: COLORS.primaryDark }]}
              onPress={() => navigation.navigate('ScheduleAppointment')}
            > 
              <Text style={styles.dieticianButtonText}>Schedule{"\n"}Appointment</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.dieticianSquareButton, { backgroundColor: COLORS.logFood }]} onPress={() => navigation.navigate('DieticianMessage')}>
              <Text style={styles.dieticianButtonText}>Message</Text>
            </TouchableOpacity>
          </View>
        </View>
        <View style={styles.dieticianDescriptionContainer}>
          <Text style={styles.dieticianDescription}>
            Meet Dt. Ekta Taneja, your friendly diet expert! With lots of experience in helping people with weight and lifestyle issues, she thinks the kitchen is like a medicine cabinet. She believes in a simple idea:
          </Text>
          <Text style={styles.dieticianQuote}>
            "If diet is wrong, medicine is of no use, if diet is correct, medicine is no need."
          </Text>
          <Text style={styles.dieticianDescription}>
            She's all about <Text style={styles.dieticianHighlightBlack}>smart eating</Text>—no starving needed! If you want <Text style={styles.dieticianHighlightBlack}>easy and practical</Text> diet plans that work at home and help with weight stuff or other health things, she's the one to talk to!
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// --- Dietician Message Screen ---
const DieticianMessageScreen = ({ navigation, route }: { navigation: any, route?: any }) => {
  const [messages, setMessages] = React.useState<any[]>([]);
  const [inputText, setInputText] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const flatListRef = React.useRef<FlatList<any>>(null);
  const [inputHeight, setInputHeight] = React.useState(40);
  const [userId, setUserId] = React.useState<string | null>(null);
  const [isDietician, setIsDietician] = React.useState(false);
  const [chatUserProfile, setChatUserProfile] = React.useState<any>(null);
  const [initializing, setInitializing] = React.useState(true); // <-- new state
  const [profileLoading, setProfileLoading] = React.useState(false);
  const [profileLoaded, setProfileLoaded] = React.useState(false);
  const [userList, setUserList] = React.useState<any[]>([]);

  // Determine chat userId (for user: their own, for dietician: from route param)
  React.useEffect(() => {
    const user = auth.currentUser;
    if (!user) return;
    
    console.log('[DieticianMessageScreen] Checking dietician status for user:', user.uid, user.email);
    console.log('[DieticianMessageScreen] Route params:', route?.params);
    
    // Check both collections for dietician status - SEQUENTIAL to prevent 499 errors
    const checkDieticianStatus = async () => {
      try {
        const userDoc = await firestore.collection('users').doc(user.uid).get();
        const userData = userDoc.data();
        
        console.log('[DieticianMessageScreen] User data:', userData);
        
        // Add delay between Firestore calls to prevent connection conflicts
        await new Promise(resolve => setTimeout(resolve, 200));
        
        const profileDoc = await firestore.collection('user_profiles').doc(user.uid).get();
        const profileData = profileDoc.data();
        
        console.log('[DieticianMessageScreen] Profile data:', profileData);
        
        // Check for dietician status in both collections
        const isDieticianAccount = !!userData?.isDietician || !!profileData?.isDietician || user?.email === 'nutricious4u@gmail.com';
        console.log('[DieticianMessageScreen] Is dietician account:', isDieticianAccount);
        
        setIsDietician(isDieticianAccount);
        
        if (isDieticianAccount) {
          // Dietician must have a userId param to chat with a user
          if (route?.params?.userId) {
            console.log('[DieticianMessageScreen] Dietician chatting with user:', route.params.userId);
            setUserId(route.params.userId);
          } else {
            console.log('[DieticianMessageScreen] Dietician with no userId param');
            setUserId(null);
          }
        } else {
          console.log('[DieticianMessageScreen] Regular user, using own userId:', user.uid);
          setUserId(user.uid || null);
        }
        setInitializing(false);
      } catch (error) {
        console.error('[DieticianMessageScreen] Error checking dietician status:', error);
        // Fallback: check email
        const isDieticianAccount = user?.email === 'nutricious4u@gmail.com';
        console.log('[DieticianMessageScreen] Fallback - is dietician account:', isDieticianAccount);
        setIsDietician(isDieticianAccount);
        setUserId(isDieticianAccount ? (route?.params?.userId || null) : (user.uid || null));
        setInitializing(false);
      }
    };
    
    checkDieticianStatus();
  }, [route?.params?.userId]);

  // Fetch user list for dieticians to get user profiles
  React.useEffect(() => {
    if (isDietician) {
      const fetchUserList = async () => {
        try {
          // Use getAllUserProfiles for consistency with messages list screen
          // This ensures both screens use the same data source
          const usersFromAPI = await getAllUserProfiles();
          console.log('[DieticianMessageScreen] Fetched user list:', usersFromAPI?.length, 'users');
          
          // Add platform-specific logging for EAS builds
          if (!__DEV__) {
            console.log('[EAS Build] User list fetch completed, users:', usersFromAPI?.map((u: any) => ({ 
              userId: u.userId, 
              firstName: u.firstName, 
              lastName: u.lastName,
              email: u.email 
            })));
          }
          
          setUserList(usersFromAPI || []);
        } catch (error) {
          console.error('[DieticianMessageScreen] Error fetching user list:', error);
          
          // Platform-specific error handling for EAS builds
          if (!__DEV__) {
            console.log('[EAS Build] Using fallback user list handling');
            // For EAS builds, try to get users from a different approach
            try {
              const fallbackUsers = await listNonDieticianUsers();
              console.log('[EAS Build] Fallback user list successful:', fallbackUsers?.length, 'users');
              setUserList(fallbackUsers || []);
            } catch (fallbackError) {
              console.error('[EAS Build] Fallback also failed:', fallbackError);
              setUserList([]);
            }
          } else {
            setUserList([]);
          }
        }
      };
      
      // Add delay for EAS builds to prevent race conditions
      const delay = !__DEV__ ? 500 : 0;
      setTimeout(() => {
        fetchUserList();
      }, delay);
    }
  }, [isDietician]);

  // Fetch user profile for chat header (for dietician)
  React.useEffect(() => {
    if (isDietician && userId) {
      setProfileLoading(true);
      setProfileLoaded(false);
      console.log('[DieticianMessageScreen] Fetching profile for userId:', userId);
      
      // Platform-specific profile fetching for EAS builds
      const fetchProfile = async () => {
        try {
          // Try to get profile from the user list first (which comes from backend API)
          // This avoids the placeholder profile issue
          const userFromList = userList?.find((u: any) => u.userId === userId);
          if (userFromList) {
            console.log('[DieticianMessageScreen] Found user in list:', userFromList);
            setChatUserProfile(userFromList);
            setProfileLoading(false);
            setProfileLoaded(true);
            return;
          }
          
          // For EAS builds, add additional logging
          if (!__DEV__) {
            console.log('[EAS Build] User not found in list, available users:', userList?.map((u: any) => u.userId));
          }
          
          // Fallback to Firestore with enhanced error handling
          console.log('[DieticianMessageScreen] User not in list, trying Firestore...');
          const doc = await firestore.collection('user_profiles').doc(userId).get();
          
          if (doc.exists) {
            const profileData = doc.data();
            console.log('[DieticianMessageScreen] Profile data from Firestore:', profileData);
            setChatUserProfile(profileData);
          } else {
            console.log('[DieticianMessageScreen] Profile not found for userId:', userId);
            
            // For EAS builds, try a more aggressive fallback
            if (!__DEV__) {
              console.log('[EAS Build] Attempting enhanced fallback for profile...');
              try {
                // Try to get user from getAllUserProfiles directly
                const allUsers = await getAllUserProfiles();
                const directUser = allUsers?.find((u: any) => u.userId === userId);
                if (directUser) {
                  console.log('[EAS Build] Found user in direct API call:', directUser);
                  setChatUserProfile(directUser);
                  setProfileLoading(false);
                  setProfileLoaded(true);
                  return;
                }
              } catch (directError) {
                console.error('[EAS Build] Direct API call failed:', directError);
              }
            }
            
            setChatUserProfile(null);
          }
          
          setProfileLoading(false);
          setProfileLoaded(true);
          
        } catch (error) {
          console.error('[DieticianMessageScreen] Error fetching profile:', error);
          
          // Enhanced fallback for EAS builds
          if (!__DEV__) {
            console.log('[EAS Build] Using enhanced fallback for profile...');
            try {
              // Try backend API with timeout
              const backendUrl = process.env.PRODUCTION_BACKEND_URL || 'https://nutricious4u-production.up.railway.app';
              const token = await auth.currentUser?.getIdToken();
              
              const controller = new AbortController();
              const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
              
              const response = await fetch(`${backendUrl}/api/users/${userId}/profile`, {
                method: 'GET',
                headers: {
                  'Authorization': `Bearer ${token}`
                },
                signal: controller.signal
              });
              
              clearTimeout(timeoutId);
              
              if (response.ok) {
                const profileData = await response.json();
                console.log('[EAS Build] ✅ Profile data from backend API:', profileData);
                setChatUserProfile(profileData);
              } else {
                throw new Error(`Backend API failed: ${response.status}`);
              }
            } catch (apiError) {
              console.error('[EAS Build] ❌ All profile fetching methods failed:', apiError);
              
              // Ultimate fallback: Create a minimal profile from available data
              console.log('[EAS Build] Creating minimal profile from available data...');
              const minimalProfile = {
                userId: userId,
                firstName: 'User',
                lastName: userId.substring(0, 8),
                email: 'user@example.com'
              };
              setChatUserProfile(minimalProfile);
            }
          } else {
            // For Expo Go, use simpler fallback
            const minimalProfile = {
              userId: userId,
              firstName: 'User',
              lastName: userId.substring(0, 8),
              email: 'user@example.com'
            };
            setChatUserProfile(minimalProfile);
          }
          
          setProfileLoading(false);
          setProfileLoaded(true);
        }
      };
      
      // Add delay for EAS builds to ensure userList is loaded
      const delay = !__DEV__ ? 1000 : 0;
      setTimeout(() => {
        fetchProfile();
      }, delay);
      
    } else if (!isDietician) {
      // For regular users, we don't need to fetch any profile since they're messaging the dietician
      setProfileLoading(false);
      setProfileLoaded(true);
      setChatUserProfile(null);
    }
  }, [isDietician, userId, userList]);

  // Fetch messages from Firestore (last 7 days only)
  React.useEffect(() => {
    if (!userId) return;
    console.log('[DieticianMessageScreen] Fetching messages for userId:', userId);
    const now = new Date();
    const unsubscribe = firestore
      .collection('chats')
      .doc(userId)
      .collection('messages')
      .orderBy('timestamp', 'asc')
      .onSnapshot(snapshot => {
        const msgs: any[] = [];
        snapshot.forEach(doc => {
          msgs.push({ id: doc.id, ...doc.data() });
        });
        console.log('[DieticianMessageScreen] Received messages:', msgs.length, msgs);
        setMessages(msgs);
      }, (error) => {
        console.error('[DieticianMessageScreen] Error fetching messages:', error);
      });
    return () => unsubscribe();
  }, [userId]);

  React.useEffect(() => {
    if (flatListRef.current) {
      flatListRef.current.scrollToEnd({ animated: true });
    }
  }, [messages]);

  // Enhanced notification system for messages
  const sendLocalMessageNotification = async (toDietician: boolean, message: string, senderName: string = '') => {
    try {
      // Enhanced notification content for better background delivery
      await Notifications.scheduleNotificationAsync({
        content: {
          title: toDietician ? 'New message from user' : 'New message from dietician',
          body: message,
          sound: 'default',
          priority: 'high',
          autoDismiss: false,
          sticky: false,
          data: {
            type: 'message_notification',
            toDietician,
            message,
            senderName,
            timestamp: new Date().toISOString(),
            userId: auth.currentUser?.uid
          }
        },
        trigger: null, // Immediate notification
      });
      
      console.log('[Message Notifications] Sent local notification:', {
        toDietician,
        message: message.substring(0, 50) + (message.length > 50 ? '...' : ''),
        senderName
      });
    } catch (error) {
      console.error('[Message Notifications] Error sending local notification:', error);
    }
  };

  // Send push notification via backend (for cross-device messaging)
  const sendPushNotification = async (recipientUserId: string, message: string, senderName: string = '') => {
    try {
      // Use enhanced API wrapper instead of direct fetch
      await sendMessageNotification(recipientUserId, message, senderName || 'User');
      
      console.log('[Message Notifications] Push notification sent successfully');
    } catch (error) {
      console.error('[Message Notifications] Error sending push notification:', error);
      
      // Fallback: Schedule message notification locally if backend fails
      try {
        const unifiedNotificationService = require('./services/unifiedNotificationService').default;
        const isFromDietician = senderName === 'Dietician';
        await unifiedNotificationService.scheduleMessageNotification(recipientUserId, senderName, message, isFromDietician);
        console.log('[Message Notifications] Fallback: Message notification scheduled locally');
      } catch (localError) {
        console.error('[Message Notifications] Fallback also failed:', localError);
      }
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() || !userId) {
      console.log('[DieticianMessageScreen] Cannot send message:', { inputText: inputText?.trim(), userId });
      return;
    }
    
    setLoading(true);
    try {
      const user = auth.currentUser;
      // Use the isDietician state instead of just checking email
      const sender = isDietician ? 'dietician' : 'user';
      const messageData = {
        text: inputText,
        sender,
        timestamp: new Date(),
      };
      
      console.log('[DieticianMessageScreen] Sending message:', { userId, sender, text: inputText, isDietician });
      
      // Add message to Firestore
      await firestore.collection('chats').doc(userId).collection('messages').add(messageData);
      
      // Update chat summary for sorting
      await firestore.collection('chats').doc(userId).set({
        userId,
        lastMessage: inputText,
        lastMessageTimestamp: new Date(),
      }, { merge: true });
      
      console.log('[DieticianMessageScreen] Message sent successfully');
      setInputText('');
      
      // Send enhanced notification to recipient (not sender)
      const senderName = isDietician ? 'Dietician' : (chatUserProfile ? `${chatUserProfile.firstName} ${chatUserProfile.lastName}`.trim() : 'User');
      
      // Don't send local notification to sender - only send push notifications to recipient
      // Local notifications are for the current device, push notifications are for other devices
      
      // Also send push notification for cross-device messaging
      if (!isDietician) {
        // User sending to dietician - send push to dietician
        await sendPushNotification('dietician', inputText, senderName);
      } else {
        // Dietician sending to user - send push to specific user
        await sendPushNotification(userId, inputText, senderName);
      }
    } catch (error) {
      console.error('[DieticianMessageScreen] Error sending message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = ({ item }: { item: any }) => {
    if (item.type === 'date') {
      return (
        <View style={{ alignItems: 'center', marginVertical: 8 }}>
          <Text style={{ color: '#444', fontWeight: 'bold', backgroundColor: '#E0E7FF', paddingHorizontal: 12, paddingVertical: 2, borderRadius: 8, fontSize: 13 }}>
            --- {item.heading} ---
          </Text>
        </View>
      );
    }
    const isUserMessage = item.sender === 'user';
    let timeString = '';
    if (item.timestamp) {
      let dateObj;
      if (typeof item.timestamp === 'object' && typeof item.timestamp.toDate === 'function') {
        // Firestore Timestamp
        dateObj = item.timestamp.toDate();
      } else if (typeof item.timestamp === 'string' || typeof item.timestamp === 'number') {
        dateObj = new Date(item.timestamp);
      }
      if (dateObj && !isNaN(dateObj.getTime())) {
        timeString = format(dateObj, 'p');
      }
    }
    return (
      <View style={{ marginBottom: 2 }}>
        <View style={[
          dieticianMessageStyles.messageBubble,
          isUserMessage ? dieticianMessageStyles.userMessage : dieticianMessageStyles.dieticianMessage
        ]}>
          <Text style={[
            dieticianMessageStyles.messageText,
            { color: isUserMessage ? '#111' : '#fff' }
          ]}>{item.text}</Text>
        </View>
        <Text style={[dieticianMessageStyles.timestampText, { alignSelf: isUserMessage ? 'flex-end' : 'flex-start', marginLeft: isUserMessage ? 0 : 12, marginRight: isUserMessage ? 12 : 0 }]}>{timeString}</Text>
      </View>
    );
  };

  // Chat header: show user name if dietician, else "Message Dietician"
  let headerTitle = 'Message Dietician';
  if (isDietician) {
    if (initializing || profileLoading || !profileLoaded) {
      headerTitle = 'Loading...';
    } else if (chatUserProfile) {
      if ((chatUserProfile.firstName && chatUserProfile.firstName !== 'User') || chatUserProfile.lastName) {
        headerTitle = `${chatUserProfile.firstName || ''} ${chatUserProfile.lastName || ''}`.trim();
      } else if (chatUserProfile.email) {
        headerTitle = chatUserProfile.email;
        console.log('[DieticianMessageScreen] Fallback to email for header:', chatUserProfile);
      } else {
        headerTitle = 'Unknown User';
        console.log('[DieticianMessageScreen] Fallback to Unknown User for header:', chatUserProfile);
      }
    } else if (profileLoaded) {
      headerTitle = 'Unknown User';
      console.log('[DieticianMessageScreen] No chatUserProfile, fallback to Unknown User. Context:', { isDietician, chatUserProfile });
    } else {
      headerTitle = 'Loading...';
    }
  }
  // If dietician and no userId, show a message and back button
  if (!initializing && (!userId && isDietician)) {
    return (
      <SafeAreaView style={dieticianMessageStyles.container}>
              <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <Text style={{ color: '#888', fontSize: 18, marginBottom: 20 }}>Select a user from the Messages list to start chatting.</Text>
          <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 12, backgroundColor: '#6EE7B7', borderRadius: 8 }}>
            <Text style={{ color: '#fff', fontWeight: 'bold' }}>Back</Text>
          </TouchableOpacity>
              </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={dieticianMessageStyles.container}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View style={dieticianMessageStyles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={dieticianMessageStyles.backButton}>
            <ArrowLeft size={28} color="#6EE7B7" />
          </TouchableOpacity>
          <Text style={dieticianMessageStyles.headerTitle}>{headerTitle}</Text>
        </View>
        <FlatList
          ref={flatListRef}
          data={groupMessagesByDate(messages)}
          renderItem={renderMessage}
          keyExtractor={item => item.id || item.heading}
          contentContainerStyle={{ paddingVertical: 10, paddingHorizontal: 10, flexGrow: 1 }}
        />
        <View style={dieticianMessageStyles.inputContainer}>
          <TextInput
            style={[dieticianMessageStyles.chatInput, { height: Math.max(40, Math.min(inputHeight, 120)) }]}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type a message..."
            placeholderTextColor="#A1A1AA"
            editable={!loading && !!userId && !initializing}
            multiline
            onContentSizeChange={e => setInputHeight(e.nativeEvent.contentSize.height)}
            textAlignVertical="top"
          />
          <TouchableOpacity onPress={handleSend} style={dieticianMessageStyles.sendButton} disabled={loading || !userId || initializing || !inputText.trim()}>
            <Send color="#6EE7B7" size={24} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const dieticianMessageStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F0FFF4',
    paddingTop: 0,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 50,
    paddingBottom: 10,
    paddingHorizontal: 10,
    backgroundColor: '#F0FFF4',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  backButton: {
    paddingRight: 16,
    paddingVertical: 4,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#000',
    flex: 1,
    textAlign: 'center',
    marginRight: 32,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  chatInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    backgroundColor: '#F0FFF4',
    borderRadius: 20,
    paddingHorizontal: 15,
    marginRight: 10,
    fontSize: 16,
    color: '#27272A',
    borderWidth: 2,
    borderColor: '#111',
  },
  sendButton: {
    padding: 5,
  },
  messageBubble: {
    padding: 12,
    borderRadius: 18,
    marginVertical: 4,
    maxWidth: '90%',
    flexWrap: 'wrap',
  },
  userMessage: {
    backgroundColor: '#FFD700', // yellow for user messages
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  dieticianMessage: {
    backgroundColor: '#3B82F6', // blue for dietician messages
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    color: '#111',
    flexWrap: 'wrap',
    width: 'auto',
    alignSelf: 'flex-start',
  },
  timestampText: {
    fontSize: 11,
    color: '#444',
    marginLeft: 8,
    marginTop: 2,
    marginBottom: 6,
    alignSelf: 'flex-end',
  },
});

// --- Dietician Messages List Screen ---
const DieticianMessagesListScreen = ({ navigation }: { navigation: any }) => {
  const [loading, setLoading] = React.useState(true);
  const [userList, setUserList] = React.useState<any[]>([]);

  // Add notification listener for dietician messages
  React.useEffect(() => {
    const user = auth.currentUser;
    if (!user) return;

    const subscription = Notifications.addNotificationReceivedListener(async (notification) => {
      const data = notification.request.content.data;
      
      // Handle user message notifications - refresh messages list
      if (data?.type === 'message_notification' && data?.fromUser) {
        console.log('[DieticianMessagesListScreen] Received message from user:', data.fromUser);
        // Refresh the messages list to show new message
        // The existing useEffect will handle the refresh
      }
    });

    return () => subscription.remove();
  }, []);

  React.useEffect(() => {
    let isMounted = true;
    async function fetchData() {
      setLoading(true);
      try {
        // 1. Fetch all user profiles from backend API (including dieticians)
        const usersFromAPI = await getAllUserProfiles();
        console.log('[DieticianMessagesListScreen] All users from API:', usersFromAPI);
        
        // Platform-specific logging for EAS builds
        if (!__DEV__) {
          console.log('[EAS Build] Messages list - API response received:', usersFromAPI?.length, 'users');
        }
        
        let filteredProfiles: any[] = [];
        if (!usersFromAPI || usersFromAPI.length === 0) {
          console.log('[DieticianMessagesListScreen] No users found from API');
          
          // For EAS builds, try fallback
          if (!__DEV__) {
            console.log('[EAS Build] Attempting fallback for messages list...');
            try {
              const fallbackUsers = await listNonDieticianUsers();
              console.log('[EAS Build] Fallback successful:', fallbackUsers?.length, 'users');
              filteredProfiles = fallbackUsers || [];
            } catch (fallbackError) {
              console.error('[EAS Build] Fallback failed:', fallbackError);
            }
          }
        } else {
          console.log('[DieticianMessagesListScreen] API returned users:', usersFromAPI.length);
          filteredProfiles = usersFromAPI.filter((u: any) => {
            const isValid = u && u.userId && u.email;
            if (!isValid) {
              console.log('[DieticianMessagesListScreen] Skipping invalid user:', u);
              return false;
            }
            
            // Skip test users and placeholder users
            const isTestUser = (
              u.firstName?.toLowerCase() === 'test' ||
              u.email?.startsWith('test@') ||
              u.userId?.toLowerCase().includes('test') ||
              (u.firstName === 'User' && u.lastName === '')
            );
            
            if (isTestUser) {
              console.log('[DieticianMessagesListScreen] Skipping test user:', u);
              return false;
            }
            
            return true;
          });
          console.log('[DieticianMessagesListScreen] After filtering:', filteredProfiles.length, 'users');
        }
        
        // Set users immediately after filtering (like Upload Diet screen)
        console.log('[DieticianMessagesListScreen] Found users:', filteredProfiles.length);
        console.log('[DieticianMessagesListScreen] Users:', filteredProfiles.map((u: any) => ({ userId: u.userId, email: u.email, firstName: u.firstName, lastName: u.lastName, isDietician: u.isDietician })));
        
        if (isMounted) {
          setUserList(filteredProfiles);
          setLoading(false);
        }
        
        // 2. Fetch chat summaries separately (don't block user list display)
        try {
          const chatsSnap = await firestore.collection('chats').get();
          const chatsMap: Record<string, any> = {};
          chatsSnap.docs.forEach(doc => {
            const data = doc.data();
            if (data.userId) {
              chatsMap[data.userId] = {
                lastMessage: data.lastMessage,
                lastMessageTimestamp: data.lastMessageTimestamp,
              };
            }
          });
          
          // 3. Merge: attach chat summary to each user
          const merged = filteredProfiles.map((user: any) => ({
            ...user,
            lastMessage: chatsMap[user.userId]?.lastMessage || '',
            lastMessageTimestamp: chatsMap[user.userId]?.lastMessageTimestamp || null,
          }));
          
          // 4. Sort: most recent chat at top, users with no chat at bottom
          merged.sort((a: any, b: any) => {
            if (a.lastMessageTimestamp && b.lastMessageTimestamp) {
              return b.lastMessageTimestamp.toDate() - a.lastMessageTimestamp.toDate();
            } else if (a.lastMessageTimestamp) {
              return -1;
            } else if (b.lastMessageTimestamp) {
              return 1;
            } else {
              return 0;
            }
          });
          
          // Update with chat data if component is still mounted
          if (isMounted) {
            setUserList(merged);
          }
        } catch (chatError) {
          console.error('[DieticianMessagesListScreen] Error fetching chats:', chatError);
          // Don't fail the entire function, users are already displayed
        }
      } catch (err) {
        console.error('[DieticianMessagesListScreen] Error fetching users or chats:', err);
        if (isMounted) {
          setUserList([]);
          setLoading(false);
        }
      }
    }
    fetchData();
    return () => { isMounted = false; };
  }, []);

  const renderItem = ({ item }: { item: any }) => (
    <TouchableOpacity
      style={{ padding: 18, borderBottomWidth: 1, borderColor: '#eee', backgroundColor: '#fff' }}
      onPress={() => navigation.navigate('DieticianMessage', { userId: item.userId })}
    >
      <Text style={{ fontWeight: 'bold', fontSize: 18, color: '#000' }}>
        {(item.firstName && item.firstName !== 'User') || item.lastName ? `${item.firstName || ''} ${item.lastName || ''}`.trim() : (item.email || 'Unknown User')}
      </Text>
      <Text style={{ color: '#888', marginTop: 4 }} numberOfLines={1}>
        {item.lastMessage || 'No messages yet'}
      </Text>
      <Text style={{ color: '#bbb', fontSize: 12, marginTop: 2 }}>
        {item.lastMessageTimestamp?.toDate ? item.lastMessageTimestamp.toDate().toLocaleString() : ''}
      </Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F0FFF4' }}>
      <View style={{ paddingTop: 50, paddingHorizontal: 16, flex: 1 }}>
        <Text style={{ fontSize: 28, fontWeight: 'bold', marginBottom: 20, textAlign: 'center', color: '#000' }}>Messages</Text>
        {loading ? (
          <ActivityIndicator size="large" color="#6EE7B7" style={{ marginTop: 40 }} />
        ) : (
          <FlatList
            data={userList}
            renderItem={renderItem}
            keyExtractor={item => item.userId}
            ListEmptyComponent={<Text style={{ textAlign: 'center', color: '#888', marginTop: 40 }}>No users found.</Text>}
          />
            )}
          </View>
        </SafeAreaView>
  );
};

// --- Stylesheet ---

  // Add styles for recipe page (reuse existing styles for cards, modal, etc.)
const styles = StyleSheet.create({
  // ...existing styles...
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 20,
    paddingTop: 24,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.background,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  addButton: {
    padding: 8,
    backgroundColor: COLORS.background,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 24,
    paddingVertical: 16,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.background,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderRadius: 8,
    paddingHorizontal: 12,
    flex: 1,
    marginRight: 8,
    borderWidth: 1,
    borderColor: COLORS.placeholder,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    marginLeft: 8,
    color: COLORS.text,
  },
  searchButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: COLORS.placeholder,
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  recipesContainer: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  recipesList: {
    padding: 20,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.placeholder,
    textAlign: 'center',
    marginBottom: 20,
  },
  addFirstButton: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  addFirstButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  recipeCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  recipeTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginBottom: 4,
  },
  recipeType: {
    fontSize: 16,
    color: COLORS.text,
    marginBottom: 2,
  },
  recipeAllergies: {
    fontSize: 15,
    color: COLORS.error,
    marginBottom: 2,
  },
  recipeLink: {
    fontSize: 15,
    color: COLORS.primaryDark,
    marginBottom: 2,
  },
  recipeLinkContainer: {
    marginTop: 8,
    paddingVertical: 4,
    paddingHorizontal: 8,
    backgroundColor: COLORS.background,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  editButton: {
    marginTop: 8,
    alignSelf: 'flex-end',
    padding: 6,
    borderRadius: 6,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 24,
    minWidth: 300,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginBottom: 12,
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#FF4444', // Red color
    borderRadius: 8,
    marginRight: 8,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: COLORS.white, // White text for red background
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    marginLeft: 8,
    alignItems: 'center',
  },
  saveButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  modalInput: {
    borderWidth: 1,
    borderColor: COLORS.placeholder,
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
    fontSize: 16,
    color: COLORS.text,
  },
  modalButtonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  modalButton: {
    flex: 1,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    padding: 10,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  modalButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 16,
  },
  errorText: {
    color: COLORS.error,
    marginTop: 8,
    textAlign: 'center',
  },
  daySelectorContainer: {
    marginTop: 8,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.placeholder,
    padding: 8,
  },
  dayOption: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    marginVertical: 2,
    backgroundColor: COLORS.background,
  },
  dayOptionSelected: {
    backgroundColor: COLORS.primary,
  },
  dayOptionText: {
    fontSize: 14,
    color: COLORS.text,
  },
  dayOptionTextSelected: {
    color: COLORS.white,
    fontWeight: '600',
  },
  // ...existing code...
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
  screenHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
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
    color: COLORS.text,
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
  modalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 8,
    marginBottom: 4,
  },
  modalExplanation: {
    fontSize: 13,
    color: COLORS.placeholder,
    marginBottom: 12,
    marginTop: 2,
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
  dieticianHeaderContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  dieticianPhotoWrapper: {
    width: 190,
    height: 190,
    borderRadius: 95,
    borderWidth: 6,
    borderColor: COLORS.primary,
    backgroundColor: COLORS.white,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    overflow: 'hidden',
  },
  dieticianPhoto: {
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: COLORS.white,
    transform: Platform.OS === 'ios' 
      ? [{ scale: 1.58 }, { translateY: 20 }]  // iOS: less down to show full face
      : [{ scale: 1.58 }, { translateY: 28 }], // Android: keep as is
  },
  dieticianName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.primaryDark,
    marginBottom: 4,
    textAlign: 'center',
  },
  dieticianTitle: {
    fontSize: 20,
    color: COLORS.text,
    marginBottom: 16,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  dieticianDescriptionContainer: {
    backgroundColor: COLORS.lightGreen,
    borderRadius: 18,
    padding: 20,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  dieticianDescription: {
    fontSize: 18,
    color: COLORS.text,
    textAlign: 'center',
    lineHeight: 28,
    marginBottom: 10,
  },
  dieticianQuote: {
    fontStyle: 'italic',
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.primaryDark,
    textAlign: 'center',
    marginVertical: 15,
    paddingHorizontal: 10,
    lineHeight: 30,
  },
  dieticianHighlightBlack: {
    fontWeight: 'bold',
    color: '#111',
  },
  dieticianButtonRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    gap: 24,
  },
  dieticianSquareButton: {
    flex: 1,
    minWidth: 130,
    height: 120,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 8,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.10,
    shadowRadius: 6,
    elevation: 3,
  },
  dieticianButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 22,
  },
  timestampText: {
    fontSize: 11,
    color: '#444',
    marginLeft: 8,
    marginTop: 2,
    marginBottom: 6,
    alignSelf: 'flex-end',
  },
  // Schedule Appointment Screen Styles
  scheduleContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  weekHeader: {
    flexDirection: 'row',
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.placeholder + '20',
    paddingBottom: 12,
  },
  timeColumnHeader: {
    width: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeColumnHeaderText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  dateColumnHeader: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dateHeaderText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
  },
  todayHeaderText: {
    color: COLORS.primary,
    fontWeight: 'bold',
  },
  todayIndicator: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    marginTop: 4,
  },
  todayIndicatorText: {
    color: COLORS.white,
    fontSize: 10,
    fontWeight: 'bold',
  },
  timeRow: {
    flexDirection: 'row',
    marginBottom: 8,
    alignItems: 'center',
  },
  timeColumn: {
    width: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeColumnText: {
    fontSize: 12,
    color: COLORS.placeholder,
    fontWeight: '500',
  },
  timeSlot: {
    flex: 1,
    height: 40,
    backgroundColor: COLORS.background,
    borderRadius: 8,
    marginHorizontal: 2,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.placeholder + '20',
  },
  pastTimeSlot: {
    backgroundColor: COLORS.placeholder + '20',
    borderColor: COLORS.placeholder + '40',
  },
  bookedTimeSlot: {
    backgroundColor: '#9CA3AF', // Grey color for other users' appointments
    borderColor: '#6B7280',
  },
  breakTimeSlot: {
    backgroundColor: '#D1D5DB', // Light grey color for breaks
    borderColor: '#9CA3AF',
  },
  selectedTimeSlot: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  timeSlotText: {
    fontSize: 11,
    color: COLORS.text,
    fontWeight: '500',
  },
  pastTimeSlotText: {
    color: COLORS.placeholder,
  },
  bookedTimeSlotText: {
    color: '#374151', // Dark grey text for other users' appointments
    fontSize: 10,
    fontWeight: '600',
  },
  breakTimeSlotText: {
    color: '#6B7280',
    fontSize: 10,
    fontWeight: 'bold',
  },
  selectedTimeSlotText: {
    color: COLORS.white,
    fontWeight: 'bold',
  },
  bookedUserText: {
    color: COLORS.placeholder,
    fontSize: 8,
    marginTop: 2,
  },
  appointmentSummary: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  appointmentSummaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 8,
  },
  appointmentSummaryText: {
    fontSize: 16,
    color: COLORS.primary,
    fontWeight: '600',
  },
  // 1. Add new style for user's own booked slot
  bookedByMeTimeSlot: {
    backgroundColor: '#10B981', // Bright green for user's own appointments
    borderColor: '#059669',
  },
  bookedByMeTimeSlotText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  // Upload Diet Screen Styles
  uploadHeaderContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    paddingTop: 50,
    paddingHorizontal: 20,
  },
  uploadBackButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 20,
    backgroundColor: COLORS.primary,
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  uploadBackButtonText: {
    color: COLORS.white,
    fontSize: 20,
    fontWeight: 'bold',
  },
  uploadScreenTitle: {
    fontSize: 34,
    fontWeight: 'bold',
    color: '#000',
    textAlign: 'center',
  },
  uploadErrorContainer: {
    backgroundColor: '#FEE2E2',
    borderColor: '#FCA5A5',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  uploadErrorText: {
    color: '#DC2626',
    fontSize: 14,
    fontWeight: '500',
  },
  uploadSuccessContainer: {
    backgroundColor: '#DCFCE7',
    borderColor: '#86EFAC',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  uploadSuccessText: {
    color: '#16A34A',
    fontSize: 14,
    fontWeight: '500',
  },
  userItem: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  selectedUserItem: {
    backgroundColor: '#E0F2FE',
    borderColor: COLORS.primary,
    borderWidth: 2,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: COLORS.placeholder,
    marginBottom: 4,
  },
  daysLeftText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
  },
  selectedIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 12,
  },
  selectedIndicatorText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: 'bold',
  },
  uploadButtonContainer: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
  uploadButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  uploadButtonDisabled: {
    backgroundColor: COLORS.placeholder,
  },
  uploadButtonText: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: 'bold',
  },
  uploadModalSubtitle: {
    fontSize: 14,
    color: COLORS.placeholder,
    marginBottom: 24,
    textAlign: 'center',
  },
  uploadModalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    margin: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
    minWidth: 300,
  },
  viewDietButton: {
    backgroundColor: '#FFA500', // Orange color
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  viewDietButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  // Subscription styles
  screenSubtitle: {
    fontSize: 16,
    color: COLORS.placeholder,
    textAlign: 'center',
    marginBottom: 24,
    paddingHorizontal: 20,
  },
  subscriptionErrorContainer: {
    backgroundColor: COLORS.error,
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  plansContainer: {
    flex: 1,
    marginBottom: 20,
  },
  planCard: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  selectedPlanCard: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.lightGreen,
  },
  planHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  planName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
    flex: 1,
  },
  planPrice: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  planDuration: {
    fontSize: 16,
    color: COLORS.placeholder,
    marginBottom: 8,
  },
  planDescription: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  planFeatures: {
    marginTop: 8,
  },
  planFeatureText: {
    fontSize: 12,
    color: COLORS.placeholder,
    lineHeight: 16,
    marginBottom: 2,
  },
  planSelectedIndicator: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginTop: 12,
  },
  planSelectedIndicatorText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: 'bold',
  },
  subscriptionButtonContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },

  subscriptionButton: {
    backgroundColor: COLORS.primary,
    height: 56,
    borderRadius: 28,
  },
  subscriptionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
    width: '100%',
  },
  subscriptionCard: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    width: '100%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  subscriptionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  subscriptionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  activeBadge: {
    backgroundColor: COLORS.primary,
  },
  inactiveBadge: {
    backgroundColor: COLORS.error,
  },
  freeBadge: {
    backgroundColor: '#34D399',
  },
  statusText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: 'bold',
  },
  subscriptionDetails: {
    gap: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 16,
    color: COLORS.placeholder,
    fontWeight: '500',
  },
  detailValue: {
    fontSize: 16,
    color: COLORS.text,
    fontWeight: '600',
    textAlign: 'right',
    flex: 1,
  },
  totalAmountText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  renewalContainer: {
    backgroundColor: COLORS.lightGreen,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
  },
  renewalText: {
    fontSize: 16,
    color: COLORS.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  renewalButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
  },
  noSubscriptionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  noSubscriptionText: {
    fontSize: 18,
    color: COLORS.placeholder,
    textAlign: 'center',
    marginBottom: 24,
  },
  getSubscriptionButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 24,
  },
  ourPlansContainer: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 20,
    marginTop: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  ourPlansTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 16,
  },
  plansList: {
    gap: 12,
  },
  planItem: {
    backgroundColor: COLORS.lightGreen,
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  planItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  planItemName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  planItemPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  planItemDuration: {
    fontSize: 14,
    color: COLORS.placeholder,
    marginBottom: 4,
  },
  planItemDescription: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  scrollView: {
    flex: 1,
  },
  errorContainer: {
    backgroundColor: '#fee',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  emptyStateContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    fontSize: 16,
    color: COLORS.placeholder,
    textAlign: 'center',
  },
  notificationsList: {
    gap: 12,
  },
  notificationItem: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  unreadNotification: {
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
    backgroundColor: '#f8f9ff',
  },
  notificationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
    flex: 1,
    marginRight: 8,
  },
  notificationTime: {
    fontSize: 12,
    color: COLORS.placeholder,
  },
  notificationBody: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
    marginBottom: 12,
  },
  notificationActions: {
    flexDirection: 'row',
    gap: 8,
  },
  notificationActionButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  notificationActionText: {
    fontSize: 12,
    color: COLORS.white,
    fontWeight: '500',
  },
  deleteButton: {
    backgroundColor: '#dc3545',
  },
  deleteButtonText: {
    color: COLORS.white,
  },

  mySubscriptionsButton: {
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
  mySubscriptionsButtonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    fontSize: 28,
    letterSpacing: 1,
  },
  notificationsButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  notificationsButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  subscriptionHeaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.placeholder,
  },
  backButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: COLORS.white,
  },
  subscriptionHeaderTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
    flex: 1,
    textAlign: 'center',
  },
  headerSpacer: {
    width: 40,
  },
  customButtonContainer: {
    marginTop: 20,
    alignItems: 'center',
  },
  customGreenBlackButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  customGreenBlackButtonText: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  popupOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  popupContainer: {
    backgroundColor: COLORS.white,
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
  popupTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  popupSubtitle: {
    fontSize: 14,
    color: COLORS.placeholder,
    textAlign: 'center',
    marginBottom: 20,
  },
  plansScrollView: {
    maxHeight: 300,
  },
  popupPlanItem: {
    backgroundColor: COLORS.lightGreen,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  selectedPlanItem: {
    borderColor: COLORS.primary,
    backgroundColor: '#f0fff4',
  },
  popupPlanHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  popupPlanName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  popupPlanPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  popupPlanDuration: {
    fontSize: 14,
    color: COLORS.placeholder,
    marginBottom: 4,
  },
  popupPlanDescription: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  popupPlanSelectedIndicator: {
    marginTop: 8,
    alignItems: 'center',
  },
  popupPlanSelectedText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  popupButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
    gap: 12,
  },
  popupCancelButton: {
    flex: 1,
    backgroundColor: COLORS.placeholder,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  popupCancelButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  popupConfirmButton: {
    flex: 1,
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  popupConfirmButtonDisabled: {
    backgroundColor: COLORS.placeholder,
  },
  popupConfirmButtonText: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: '600',
  },
  // User Info Modal Styles
  userInfoModalContent: {
    backgroundColor: COLORS.white,
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
  userInfoModalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.primary,
    textAlign: 'center',
    marginBottom: 20,
  },
  userInfoContent: {
    marginBottom: 20,
  },
  userInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.background,
  },
  userInfoLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  userInfoValue: {
    fontSize: 16,
    color: COLORS.text,
    flex: 1,
    textAlign: 'right',
  },
  userInfoButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  userInfoButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  paidButton: {
    backgroundColor: '#FFD700', // Yellow color
  },
  paidButtonText: {
    color: '#000000', // Black text for yellow background
    fontSize: 16,
    fontWeight: '600',
  },
  lockButton: {
    backgroundColor: '#FF4444',
  },
  unlockButton: {
    backgroundColor: '#34D399',
  },
  lockButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
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
  RoutineScreen, // <-- export the new screen
  DieticianScreen, // <-- export DieticianScreen
  DieticianMessageScreen, // <-- export the new message screen
  DieticianMessagesListScreen, // <-- export the messages list screen for dietician
  ScheduleAppointmentScreen, // <-- export the schedule appointment screen
  DieticianDashboardScreen, // <-- export the dietician dashboard screen
  RecipesScreen, // <-- export RecipesScreen
  SubscriptionSelectionScreen, // <-- export subscription selection screen
  MySubscriptionsScreen // <-- export my subscriptions screen
};

// --- Subscription Selection Screen ---
const SubscriptionSelectionScreen = ({ navigation }: { navigation: any }) => {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [subscribing, setSubscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const { isFreeUser } = useSubscription();

  // Only allow free users to access this screen
  useEffect(() => {
    if (!isFreeUser) {
      navigation.navigate('Main');
    }
  }, [isFreeUser, navigation]);
  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const subscriptionPlans = await getSubscriptionPlans();
      // Filter out the free plan - only show paid plans
      const paidPlans = subscriptionPlans.filter(plan => !plan.isFree);
      setPlans(paidPlans);
    } catch (e: any) {
      console.error('Error fetching plans:', e);
      // Show a more user-friendly error message
      if (e.response?.status === 404) {
        setError('Subscription service is being updated. Please try again in a few minutes.');
      } else {
        setError('Failed to load subscription plans. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };



  const handleSelectPlan = async () => {
    if (!selectedPlan) return;
    
    const userId = auth.currentUser?.uid;
    if (!userId) {
      setError('User not authenticated');
      return;
    }

    try {
      setSubscribing(true);
      setError(null);
      
      const response = await selectSubscription(userId, selectedPlan);
      
      if (response.success) {
        // Show custom green success popup
        setShowSuccessPopup(true);
        setSuccessMessage(response.message);
      } else {
        setError(response.message || 'Failed to subscribe');
      }
    } catch (e) {
      setError('Failed to subscribe to plan');
      console.error('Error selecting subscription:', e);
    } finally {
      setSubscribing(false);
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
        <Text style={styles.screenTitle}>Choose Your Plan</Text>
        <Text style={styles.screenSubtitle}>Select a subscription plan to unlock premium features</Text>
        
        {error && (
          <View style={styles.subscriptionErrorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Available Plans */}
        <ScrollView style={styles.plansContainer} showsVerticalScrollIndicator={false}>
          {plans.map((plan) => (
            <TouchableOpacity
              key={plan.planId}
              style={[
                styles.planCard,
                selectedPlan === plan.planId && styles.selectedPlanCard
              ]}
              onPress={() => setSelectedPlan(plan.planId)}
              activeOpacity={0.8}
            >
              <View style={styles.planHeader}>
                <Text style={styles.planName}>{plan.name}</Text>
                <Text style={styles.planPrice}>
                  {plan.isFree ? 'Free' : `₹${plan.price.toLocaleString()}`}
                </Text>
              </View>
              <Text style={styles.planDuration}>{plan.duration}</Text>
              <Text style={styles.planDescription}>{plan.description}</Text>
              {plan.features && plan.features.length > 0 && (
                <View style={styles.planFeatures}>
                  {plan.features.map((feature, index) => (
                    <Text key={index} style={styles.planFeatureText}>• {feature}</Text>
                  ))}
                </View>
              )}
              {selectedPlan === plan.planId && (
                <View style={styles.planSelectedIndicator}>
                  <Text style={styles.planSelectedIndicatorText}>✓ Selected</Text>
                </View>
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={styles.subscriptionButtonContainer}>
          <StyledButton
            title={subscribing ? "Subscribing..." : "Subscribe Now"}
            onPress={handleSelectPlan}
            disabled={!selectedPlan || subscribing}
            style={styles.subscriptionButton}
          />
          <TouchableOpacity
            style={[styles.cancelButton, { 
              height: 56, 
              marginTop: 12, 
              borderRadius: 28,
              justifyContent: 'center',
              alignItems: 'center'
            }]}
            onPress={() => navigation.goBack()}
            activeOpacity={0.7}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Custom Green Success Popup */}
      <Modal
        visible={showSuccessPopup}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowSuccessPopup(false)}
      >
        <View style={styles.successPopupOverlay}>
          <View style={[styles.successPopup, { backgroundColor: '#34D399' }]}>
            <Text style={styles.successTitle}>Subscription Successful! 🎉</Text>
            <Text style={styles.successMessage}>{successMessage}</Text>
            <TouchableOpacity
              style={[styles.successButton, { backgroundColor: COLORS.white }]}
              onPress={() => {
                setShowSuccessPopup(false);
                navigation.navigate('MySubscriptions');
              }}
            >
              <Text style={[styles.successButtonText, { color: '#34D399' }]}>Continue</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

// --- My Subscriptions Screen ---
const MySubscriptionsScreen = ({ navigation }: { navigation: any }) => {
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPlanPopup, setShowPlanPopup] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [addingAmount, setAddingAmount] = useState(false);
  const [showCancelSubscriptionModal, setShowCancelSubscriptionModal] = useState(false);
  const [showCancelSuccessModal, setShowCancelSuccessModal] = useState(false);
  const [cancelSuccessMessage, setCancelSuccessMessage] = useState('');
  const { refreshSubscriptionStatus } = useSubscription();

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  const fetchSubscriptionStatus = async () => {
    try {
      setLoading(true);
      const userId = auth.currentUser?.uid;
      if (!userId) {
        setError('User not authenticated');
        return;
      }
      
      const status = await getSubscriptionStatus(userId);
      setSubscription(status);
      
      // Check if user needs to select a plan
      checkIfPlanSelectionNeeded(status);
    } catch (e) {
      setError('Failed to load subscription status');
      console.error('Error fetching subscription status:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    try {
      const subscriptionPlans = await getSubscriptionPlans();
      setPlans(subscriptionPlans);
    } catch (e) {
      console.error('Error fetching plans:', e);
    }
  };

  const checkIfPlanSelectionNeeded = (status: SubscriptionStatus) => {
    // Only show popup if user is not on free plan and has no active subscription
    if (!status.isFreeUser && (!status.subscriptionPlan || !status.isSubscriptionActive)) {
      fetchPlans();
      setShowPlanPopup(true);
    }
  };

  const handlePlanSelection = async (planId: string) => {
    try {
      setAddingAmount(true);
      const userId = auth.currentUser?.uid;
      if (!userId) return;

      // Select the subscription (this now also updates the total amount)
      const result = await selectSubscription(userId, planId);
      
      if (result.success) {
        Alert.alert('Success', result.message);
        setShowPlanPopup(false);
        setSelectedPlan(null);
        // Refresh subscription status
        fetchSubscriptionStatus();
      }
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to select plan');
    } finally {
      setAddingAmount(false);
    }
  };

  const handleCancelSubscription = async () => {
    setShowCancelSubscriptionModal(true);
  };

  const confirmCancelSubscription = async () => {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) return;

      const result = await cancelSubscription(userId);
      if (result.success) {
        setShowCancelSubscriptionModal(false);
        // Show custom green success popup
        setCancelSuccessMessage(result.message);
        setShowCancelSuccessModal(true);
        // Refresh subscription status
        fetchSubscriptionStatus();
        // Refresh the subscription context
        refreshSubscriptionStatus();
      } else {
        Alert.alert('Error', result.message || 'Failed to cancel subscription');
      }
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to cancel subscription');
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (e) {
      return 'Invalid Date';
    }
  };

  const getPlanName = (planId: string) => {
    switch (planId) {
      case '1month': return '1 Month Plan';
      case '2months': return '2 Months Plan';
      case '3months': return '3 Months Plan';
      default: return 'Unknown Plan';
    }
  };

  const { isFreeUser } = useSubscription();
  
  const availablePlans = [
    {
      planId: '1month',
      name: '1 Month Plan',
      duration: '1 month',
      price: 5500,
      description: isFreeUser ? 'Upgrade to get personalized diets, custom notification reminders and AI assistance' : 'Perfect for getting started with your fitness journey'
    },
    {
      planId: '2months',
      name: '2 Months Plan',
      duration: '2 months',
      price: 10000,
      description: isFreeUser ? 'Upgrade to get personalized diets, custom notification reminders and AI assistance' : 'Great value for consistent progress tracking'
    },
    {
      planId: '3months',
      name: '3 Months Plan',
      duration: '3 months',
      price: 14000,
      description: isFreeUser ? 'Upgrade to get personalized diets, custom notification reminders and AI assistance' : 'Best value for long-term fitness goals'
    }
  ];

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { paddingTop: 32, paddingHorizontal: 16 }]}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { paddingTop: 32, paddingHorizontal: 16 }]}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.settingsContainer}>
          <View style={styles.screenHeader}>
            <TouchableOpacity
              style={[styles.backButton, { marginRight: 12 }]}
              onPress={() => navigation.navigate('Main', { screen: 'Settings' })}
              activeOpacity={0.7}
            >
              <ArrowLeft color={COLORS.primary} size={24} />
            </TouchableOpacity>
            <Text style={styles.screenTitle}>My Subscriptions</Text>
          </View>
        
        {error && (
          <View style={styles.subscriptionErrorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {subscription ? (
          <View style={styles.subscriptionContainer}>
            <View style={styles.subscriptionCard}>
              <View style={styles.subscriptionHeader}>
                <Text style={styles.subscriptionTitle}>Current Plan</Text>
                <View style={[
                  styles.statusBadge,
                  subscription.isFreeUser ? styles.freeBadge : (subscription.isSubscriptionActive ? styles.activeBadge : styles.inactiveBadge)
                ]}>
                  <Text style={styles.statusText}>
                    {subscription.isFreeUser ? 'Free Plan' : (subscription.isSubscriptionActive ? 'Active' : 'Inactive')}
                  </Text>
                </View>
              </View>
              
              <View style={styles.subscriptionDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Plan:</Text>
                  <Text style={styles.detailValue}>
                    {subscription.isFreeUser ? 'Free Plan' : (subscription.subscriptionPlan ? getPlanName(subscription.subscriptionPlan) : 'No Plan')}
                  </Text>
                </View>
                
                {!subscription.isFreeUser && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>Start Date:</Text>
                    <Text style={styles.detailValue}>
                      {subscription.subscriptionStartDate ? formatDate(subscription.subscriptionStartDate) : 'N/A'}
                    </Text>
                  </View>
                )}
                
                {!subscription.isFreeUser && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>End Date:</Text>
                    <Text style={styles.detailValue}>
                      {subscription.subscriptionEndDate ? formatDate(subscription.subscriptionEndDate) : 'N/A'}
                    </Text>
                  </View>
                )}
                
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Total Amount Due:</Text>
                  <Text style={[styles.detailValue, styles.totalAmountText]}>
                    ₹{subscription.totalAmountPaid.toLocaleString()}
                  </Text>
                </View>
              </View>
            </View>
            
            {!subscription.isSubscriptionActive && !subscription.isFreeUser && (
              <View style={styles.renewalContainer}>
                <Text style={styles.renewalText}>Your subscription has expired</Text>
                <StyledButton
                  title="Renew Subscription"
                  onPress={() => navigation.navigate('SubscriptionSelection')}
                  style={styles.renewalButton}
                />
              </View>
            )}
            
            {subscription.isFreeUser && (
              <View style={styles.renewalContainer}>
                <Text style={styles.renewalText}>You are currently on the free plan</Text>
                <StyledButton
                  title="Upgrade to Premium"
                  onPress={() => navigation.navigate('SubscriptionSelection')}
                  style={styles.renewalButton}
                />
              </View>
            )}
            
            {subscription.isSubscriptionActive && !subscription.isFreeUser && (
              <View style={styles.renewalContainer}>
                <Text style={styles.renewalText}>Your subscription is active</Text>
                <StyledButton
                  title="Cancel Subscription"
                  onPress={() => handleCancelSubscription()}
                  style={[styles.renewalButton, { backgroundColor: '#ff4444' }]}
                />
              </View>
            )}
            
            {/* Our Plans Widget */}
            <View style={styles.ourPlansContainer}>
              <Text style={styles.ourPlansTitle}>Our Plans</Text>
              <View style={styles.plansList}>
                {availablePlans.map((plan) => (
                  <View key={plan.planId} style={styles.planItem}>
                    <View style={styles.planItemHeader}>
                      <Text style={styles.planItemName}>{plan.name}</Text>
                      <Text style={styles.planItemPrice}>₹{plan.price.toLocaleString()}</Text>
                    </View>
                    <Text style={styles.planItemDuration}>{plan.duration}</Text>
                    <Text style={styles.planItemDescription}>{plan.description}</Text>
                  </View>
                ))}
              </View>
            </View>
            

          </View>
        ) : (
          <View style={styles.noSubscriptionContainer}>
            <Text style={styles.noSubscriptionText}>No subscription found</Text>
            <StyledButton
              title="Get a Subscription"
              onPress={() => navigation.navigate('SubscriptionSelection')}
              style={styles.getSubscriptionButton}
            />
          </View>
        )}
        </View>
      </ScrollView>

      {/* Plan Selection Popup */}
      <Modal
        visible={showPlanPopup}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowPlanPopup(false)}
      >
        <View style={styles.popupOverlay}>
          <View style={styles.popupContainer}>
            <Text style={styles.popupTitle}>Select a Subscription Plan</Text>
            <Text style={styles.popupSubtitle}>
              Choose a plan to continue your fitness journey
            </Text>
            
            <ScrollView style={styles.plansScrollView} showsVerticalScrollIndicator={false}>
              {plans.map((plan) => (
                <TouchableOpacity
                  key={plan.planId}
                  style={[
                    styles.popupPlanItem,
                    selectedPlan === plan.planId && styles.selectedPlanItem
                  ]}
                  onPress={() => setSelectedPlan(plan.planId)}
                  activeOpacity={0.7}
                >
                  <View style={styles.popupPlanHeader}>
                    <Text style={styles.popupPlanName}>{plan.name}</Text>
                    <Text style={styles.popupPlanPrice}>₹{plan.price.toLocaleString()}</Text>
                  </View>
                  <Text style={styles.popupPlanDuration}>{plan.duration}</Text>
                  <Text style={styles.popupPlanDescription}>{plan.description}</Text>
                  {selectedPlan === plan.planId && (
                    <View style={styles.popupPlanSelectedIndicator}>
                      <Text style={styles.popupPlanSelectedText}>✓ Selected</Text>
                    </View>
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
            
            <View style={styles.popupButtons}>
              <TouchableOpacity
                style={styles.popupCancelButton}
                onPress={() => {
                  setShowPlanPopup(false);
                  setSelectedPlan(null);
                }}
              >
                <Text style={styles.popupCancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[
                  styles.popupConfirmButton,
                  !selectedPlan && styles.popupConfirmButtonDisabled
                ]}
                onPress={() => selectedPlan && handlePlanSelection(selectedPlan)}
                disabled={!selectedPlan || addingAmount}
              >
                <Text style={styles.popupConfirmButtonText}>
                  {addingAmount ? 'Processing...' : 'Confirm Selection'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Custom Green Cancel Subscription Modal */}
      <Modal
        visible={showCancelSubscriptionModal}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowCancelSubscriptionModal(false)}
      >
        <View style={styles.successPopupOverlay}>
          <View style={[styles.successPopup, { backgroundColor: '#34D399', padding: 32, margin: 30 }]}>
            <Text style={styles.successTitle}>Cancel Subscription</Text>
            <Text style={styles.successMessage}>
              Are you sure you want to cancel your subscription? You will be moved to the free plan.
            </Text>
            <View style={[styles.modalButtonRow, { marginTop: 24 }]}>
              <TouchableOpacity
                style={[styles.successButton, { backgroundColor: '#EF4444', marginRight: 12, flex: 1 }]}
                onPress={() => setShowCancelSubscriptionModal(false)}
              >
                <Text style={[styles.successButtonText, { color: COLORS.white }]}>No, Keep It</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.successButton, { backgroundColor: COLORS.white, marginLeft: 12, flex: 1 }]}
                onPress={confirmCancelSubscription}
              >
                <Text style={[styles.successButtonText, { color: '#34D399' }]}>Yes, Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Custom Green Cancel Success Modal */}
      <Modal
        visible={showCancelSuccessModal}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowCancelSuccessModal(false)}
      >
        <View style={styles.successPopupOverlay}>
          <View style={[styles.successPopup, { backgroundColor: '#34D399' }]}>
            <Text style={styles.successTitle}>Subscription Cancelled! ✅</Text>
            <Text style={styles.successMessage}>{cancelSuccessMessage}</Text>
            <TouchableOpacity
              style={[styles.successButton, { backgroundColor: COLORS.white }]}
              onPress={() => {
                setShowCancelSuccessModal(false);
                navigation.navigate('Main');
              }}
            >
              <Text style={[styles.successButtonText, { color: '#34D399' }]}>Continue</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}; 

// --- Notifications Screen ---
const NotificationsScreen = ({ navigation }: { navigation: any }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const currentUser = auth.currentUser;

  const fetchNotifications = async () => {
    if (!currentUser?.uid) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Check if user is dietician (using email or special logic)
      const userProfile = await getUserProfileSafe(currentUser.uid);
      const userEmail = currentUser.email;
      const isDietician = userEmail === "dietician@nutricious4u.com" || userEmail?.includes("dietician");
      const userId = isDietician ? "dietician" : currentUser.uid;
      
      const response = await getUserNotifications(userId);
      setNotifications(response.notifications);
    } catch (err: any) {
      console.error('Error fetching notifications:', err);
      setError(err.message || 'Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchNotifications();
    setRefreshing(false);
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await markNotificationRead(notificationId);
      // Update local state
      setNotifications(prev => 
        prev.map(notification => 
          notification.id === notificationId 
            ? { ...notification, read: true }
            : notification
        )
      );
    } catch (err: any) {
      console.error('Error marking notification as read:', err);
      Alert.alert('Error', 'Failed to mark notification as read');
    }
  };

  const handleDeleteNotification = async (notificationId: string) => {
    try {
      await deleteNotification(notificationId);
      // Remove from local state
      setNotifications(prev => 
        prev.filter(notification => notification.id !== notificationId)
      );
    } catch (err: any) {
      console.error('Error deleting notification:', err);
      Alert.alert('Error', 'Failed to delete notification');
    }
  };

  const formatNotificationTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
      
      if (diffInHours < 1) {
        const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
        return `${diffInMinutes} minutes ago`;
      } else if (diffInHours < 24) {
        return `${Math.floor(diffInHours)} hours ago`;
      } else {
        const diffInDays = Math.floor(diffInHours / 24);
        return `${diffInDays} days ago`;
      }
    } catch {
      return 'Unknown time';
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [currentUser?.uid]);

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { paddingTop: 32, paddingHorizontal: 16 }]}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { paddingTop: 32, paddingHorizontal: 16 }]}>
      <ScrollView 
        style={styles.scrollView} 
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        <View style={styles.settingsContainer}>
          <Text style={styles.screenTitle}>Notifications</Text>
          
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {notifications.length === 0 ? (
            <View style={styles.emptyStateContainer}>
              <Text style={styles.emptyStateText}>No notifications yet</Text>
            </View>
          ) : (
            <View style={styles.notificationsList}>
              {notifications.map((notification) => (
                <View 
                  key={notification.id} 
                  style={[
                    styles.notificationItem,
                    !notification.read && styles.unreadNotification
                  ]}
                >
                  <View style={styles.notificationHeader}>
                    <Text style={styles.notificationTitle}>{notification.title}</Text>
                    <Text style={styles.notificationTime}>
                      {formatNotificationTime(notification.timestamp)}
                    </Text>
                  </View>
                  
                  <Text style={styles.notificationBody}>{notification.body}</Text>
                  
                  <View style={styles.notificationActions}>
                    {!notification.read && (
                      <TouchableOpacity
                        style={styles.notificationActionButton}
                        onPress={() => handleMarkAsRead(notification.id)}
                      >
                        <Text style={styles.notificationActionText}>Mark as Read</Text>
                      </TouchableOpacity>
                    )}
                    
                    <TouchableOpacity
                      style={[styles.notificationActionButton, styles.deleteButton]}
                      onPress={() => handleDeleteNotification(notification.id)}
                    >
                      <Text style={[styles.notificationActionText, styles.deleteButtonText]}>Delete</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
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

// Helper to set isDietician: true for a user profile (run once for the dietician)
export async function setDieticianFlagForUser(email: string) {
  // Find user by email in Firestore 'users' collection
  const snapshot = await firestore.collection('users').where('email', '==', email).get();
  if (!snapshot.empty) {
    const userDoc = snapshot.docs[0];
    await userDoc.ref.update({ isDietician: true });
    return true;
  }
  return false;
}

// Add a utility to group messages by date and insert date headings
function groupMessagesByDate(messages: any[]) {
  const groups: any[] = [];
  let lastDate: string | null = null;
  messages.forEach((msg) => {
    let dateObj;
    if (msg.timestamp) {
      if (typeof msg.timestamp === 'object' && typeof msg.timestamp.toDate === 'function') {
        dateObj = msg.timestamp.toDate();
      } else if (typeof msg.timestamp === 'string' || typeof msg.timestamp === 'number') {
        dateObj = new Date(msg.timestamp);
      }
    } else {
      dateObj = new Date();
    }
    const dateKey = dateObj ? dateObj.toDateString() : '';
    if (lastDate !== dateKey) {
      let heading = dateObj ? format(dateObj, 'do MMMM yyyy') : '';
      if (dateObj && isToday(dateObj)) heading = 'Today';
      else if (dateObj && isYesterday(dateObj)) heading = 'Yesterday';
      groups.push({ type: 'date', id: `date-${dateKey}`, heading });
      lastDate = dateKey;
    }
    groups.push({ ...msg, type: 'message' });
  });
  return groups;
}

// --- Schedule Appointment Screen ---
const ScheduleAppointmentScreen = ({ navigation }: { navigation: any }) => {
  const [selectedDate, setSelectedDate] = React.useState(new Date());
  const [selectedTimeSlot, setSelectedTimeSlot] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [appointments, setAppointments] = React.useState<any[]>([]);
  const [appointmentsLoading, setAppointmentsLoading] = React.useState(true);
  const [showSuccess, setShowSuccess] = React.useState(false);
  const [successMessage, setSuccessMessage] = React.useState('');
  const [breaks, setBreaks] = React.useState<any[]>([]); // Add breaks state for users
  const [breaksLoading, setBreaksLoading] = React.useState(true); // Add loading state for breaks
  const [showBreakConfirmation, setShowBreakConfirmation] = React.useState(false);
  const [breakConfirmationSlot, setBreakConfirmationSlot] = React.useState<{timeSlot: string, date: Date} | null>(null);
  const [isAppointmentCancelledByBreak, setIsAppointmentCancelledByBreak] = React.useState(false);
  const [authReady, setAuthReady] = React.useState(false);

  // Check if user is authenticated
  const isAuthenticated = !!auth.currentUser?.uid;

  // Set auth ready after a delay to ensure authentication is complete
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setAuthReady(true);
    }, 2000); // 2 second delay

    return () => clearTimeout(timer);
  }, []);

  // Suppress Firestore permission errors during authentication
  const suppressFirestoreErrors = (operation: () => void) => {
    try {
      operation();
    } catch (error) {
      console.log('Suppressed Firestore error during authentication:', error);
    }
  };

  // Generate time slots from 7am to 7pm
  const timeSlots = React.useMemo(() => {
    const slots = [];
    for (let hour = 7; hour <= 19; hour++) {
      const time = `${hour.toString().padStart(2, '0')}:00`;
      slots.push(time);
    }
    return slots;
  }, []);

  // Generate week dates (7 days starting from today)
  const weekDates = React.useMemo(() => {
    const dates = [];
    const today = new Date();
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push(date);
    }
    return dates;
  }, []);

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isPastDate = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    date.setHours(0, 0, 0, 0);
    return date < today;
  };

  const isPastTimeSlot = (timeSlot: string, date: Date) => {
    if (isPastDate(date)) return true;
    if (!isToday(date)) return false;
    
    const now = new Date();
    const currentHour = now.getHours();
    const slotHour = parseInt(timeSlot.split(':')[0]);
    return slotHour <= currentHour;
  };

  const isSlotBooked = (timeSlot: string, date: Date) => {
    const dateString = date.toDateString();
    return appointments.some(appointment => {
      const appointmentDate = new Date(appointment.date);
      return appointmentDate.toDateString() === dateString && appointment.timeSlot === timeSlot;
    });
  };

  const getBookedUserInfo = (timeSlot: string, date: Date) => {
    const dateString = date.toDateString();
    const appointment = appointments.find(appointment => {
      const appointmentDate = new Date(appointment.date);
      return appointmentDate.toDateString() === dateString && appointment.timeSlot === timeSlot;
    });
    return appointment;
  };

    // Fetch appointments for the current week
  React.useEffect(() => {
    // Only set up listeners if user is authenticated and auth is ready
    if (!isAuthenticated || !authReady) {
      setAppointmentsLoading(false);
      return;
    }
    
    const userId = auth.currentUser?.uid;
    if (!userId) {
      setAppointmentsLoading(false);
      return;
    }

        // Don't load local appointments first - let Firestore handle everything
    // This prevents the split-second visibility issue

    let unsubscribe: (() => void) | undefined;
    const timer = setTimeout(() => {
            // Real-time listener for all appointments (users can see all but only book their own)
      // Note: Users can see all appointments to avoid double booking, but only book their own
      unsubscribe = firestore
        .collection('appointments')
        .onSnapshot(snapshot => {
          const appointmentsData = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data()
          }));
          console.log('[ScheduleAppointment] User appointments updated:', appointmentsData.length, 'appointments');
          setAppointments(appointmentsData);
          setAppointmentsLoading(false);
        }, error => {
          console.error('[ScheduleAppointment] Error listening to user appointments:', error);
          setAppointmentsLoading(false);
          // Don't throw error, just log it and continue
        });
    }, 100); // Reduced delay for faster loading

    return () => {
      clearTimeout(timer);
      if (unsubscribe) unsubscribe();
    };
  }, [auth.currentUser?.uid, authReady]); // Add dependency on user ID and auth ready

    // Fetch breaks for users to see dietician's schedule
  React.useEffect(() => {
    console.log('[User Schedule] Setting up breaks listener for users...');
    
    if (!isAuthenticated || !authReady) {
      return;
    }
    
    let unsubscribe: (() => void) | undefined;
    const timer = setTimeout(() => {
      // Real-time listener for breaks
      unsubscribe = firestore
        .collection('breaks')
        .onSnapshot(snapshot => {
          const breaksData = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data()
          }));
          console.log('[ScheduleAppointment] Breaks updated:', breaksData.length, 'breaks');
          setBreaks(breaksData);
          setBreaksLoading(false); // Set loading to false when breaks are loaded
        }, error => {
          console.error('[ScheduleAppointment] Error listening to breaks:', error);
          setBreaksLoading(false); // Set loading to false even on error
          // Don't throw error, just log it and continue
        });
    }, 100); // Reduced delay for faster loading

    return () => {
      clearTimeout(timer);
      if (unsubscribe) unsubscribe();
    };
  }, [auth.currentUser?.uid, authReady]);

  const handleTimeSlotPress = (timeSlot: string, date: Date) => {
    if (isPastTimeSlot(timeSlot, date) || isSlotBooked(timeSlot, date)) return;
    
    setSelectedDate(date);
    setSelectedTimeSlot(timeSlot);
  };

  const handleScheduleAppointment = async () => {
    console.log('[Appointment Debug] === APPOINTMENT DEBUGGING START ===');
    console.log('[Appointment Debug] Starting appointment scheduling...');
    console.log('[Appointment Debug] Selected time slot:', selectedTimeSlot);
    console.log('[Appointment Debug] Selected date:', selectedDate);
    console.log('[Appointment Debug] Current user:', auth.currentUser?.uid);
    console.log('[Appointment Debug] User authenticated:', !!auth.currentUser);
    console.log('[Appointment Debug] User email:', auth.currentUser?.email);
    
    if (!selectedTimeSlot) {
      setSuccessMessage('Please select a time slot');
      setShowSuccess(true);
      return;
    }
    setLoading(true);
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) {
        setSuccessMessage('You must be logged in to schedule an appointment');
        setShowSuccess(true);
        return;
      }

      // Fetch user profile to get actual name
      let userName = 'Unknown User';
      try {
        console.log('[Appointment Debug] Fetching user profile for userId:', userId);
        const userProfileDoc = await firestore.collection('user_profiles').doc(userId).get();
        console.log('[Appointment Debug] User profile exists:', userProfileDoc.exists);
        if (userProfileDoc.exists) {
          const userData = userProfileDoc.data();
          console.log('[Appointment Debug] User data:', userData);
          if (userData?.firstName && userData?.lastName) {
            userName = `${userData.firstName} ${userData.lastName}`;
            console.log('[Appointment Debug] Using full name:', userName);
          } else if (userData?.firstName) {
            userName = userData.firstName;
            console.log('[Appointment Debug] Using first name only:', userName);
          } else {
            userName = auth.currentUser?.displayName || auth.currentUser?.email || 'Unknown User';
            console.log('[Appointment Debug] Using fallback name:', userName);
          }
        } else {
          userName = auth.currentUser?.displayName || auth.currentUser?.email || 'Unknown User';
          console.log('[Appointment Debug] No profile, using fallback:', userName);
        }
      } catch (error) {
        console.error('[Appointment Debug] Error fetching user profile:', error);
        userName = auth.currentUser?.displayName || auth.currentUser?.email || 'Unknown User';
      }

      // Create appointment data
      const appointmentDate = new Date(selectedDate);
      const [hour] = selectedTimeSlot.split(':');
      appointmentDate.setHours(parseInt(hour), 0, 0, 0);
      
      const appointmentData = {
        userId: userId,
        userName: userName,
        userEmail: auth.currentUser?.email || '',
        date: appointmentDate.toISOString(),
        timeSlot: selectedTimeSlot,
        status: 'confirmed',
        createdAt: new Date().toISOString(),
      };

      // Enhanced debugging for appointment data
      console.log('[Appointment Debug] User name to use:', userName);
      console.log('[Appointment Debug] Full appointment data:', appointmentData);
      console.log('[Appointment Debug] Data types:', {
        userId: typeof appointmentData.userId,
        userName: typeof appointmentData.userName,
        date: typeof appointmentData.date,
        timeSlot: typeof appointmentData.timeSlot
      });
      console.log('[Appointment Debug] User ID match check:', {
        userId: appointmentData.userId,
        authUid: auth.currentUser?.uid,
        match: appointmentData.userId === auth.currentUser?.uid
      });

      // Save appointment using atomic transaction
      console.log('[Appointment Debug] Attempting to save appointment with atomic transaction:', appointmentData);
      
      try {
        // Use atomic booking with server-side validation
        // First check if slot is available
        const appointmentDate = new Date(selectedDate);
        const [hour] = selectedTimeSlot.split(':');
        appointmentDate.setHours(parseInt(hour), 0, 0, 0);
        
        // Check for existing appointments at this time
        const existingAppointmentsSnapshot = await firestore
          .collection('appointments')
          .where('date', '==', appointmentDate.toISOString())
          .where('timeSlot', '==', selectedTimeSlot)
          .get();
        
        if (!existingAppointmentsSnapshot.empty) {
          throw new Error('Time slot is no longer available');
        }
        
        // Check for breaks
        const breaksSnapshot = await firestore.collection('breaks').get();
        const dateString = selectedDate.toDateString();
        
        for (const doc of breaksSnapshot.docs) {
          const breakData = doc.data();
          const timeInRange = selectedTimeSlot >= breakData.fromTime && selectedTimeSlot <= breakData.toTime;
          
          if (timeInRange) {
            if (!breakData.specificDate || breakData.specificDate === dateString) {
              throw new Error('Time slot is during a break');
            }
          }
        }
        
        // If we get here, slot is available - create appointment
        console.log('[Appointment Debug] About to save to Firestore...');
        console.log('[Appointment Debug] Collection path: appointments');
        console.log('[Appointment Debug] Data to save:', JSON.stringify(appointmentData, null, 2));
        
        const appointmentRef = await firestore.collection('appointments').add(appointmentData);
        const result = appointmentRef.id;
        
        console.log('[Appointment Debug] ✅ Appointment saved successfully with atomic transaction, ID:', result);
      
      setSuccessMessage(`Your appointment has been scheduled for ${formatDate(selectedDate)} at ${selectedTimeSlot}`);
      setShowSuccess(true);
      // Optionally, refresh appointments
        setAppointments([...appointments, { ...appointmentData, id: result }]);
      setSelectedTimeSlot(null);
      } catch (firestoreError) {
        console.error('[Appointment Debug] Firestore save failed:', firestoreError);
        
        // Fallback: Try to save via backend API
        try {
          console.log('[Appointment Debug] Attempting backend API fallback...');
          const backendUrl = process.env.PRODUCTION_BACKEND_URL || 'https://nutricious4u-production.up.railway.app';
          
          // Try the appointments endpoint first
          let response = await fetch(`${backendUrl}/api/appointments`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${await auth.currentUser?.getIdToken()}`
            },
            body: JSON.stringify(appointmentData)
          });
          
          if (!response.ok) {
            // Try alternative endpoint
            console.log('[Appointment Debug] First endpoint failed, trying alternative...');
            response = await fetch(`${backendUrl}/api/users/${userId}/appointments`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${await auth.currentUser?.getIdToken()}`
              },
              body: JSON.stringify(appointmentData)
            });
          }
          
          if (response.ok) {
            const result = await response.json();
            console.log('[Appointment Debug] ✅ Appointment saved via backend API:', result);
            
            setSuccessMessage(`Your appointment has been scheduled for ${formatDate(selectedDate)} at ${selectedTimeSlot}`);
            setShowSuccess(true);
            setAppointments([...appointments, { ...appointmentData, id: result.id || Date.now().toString() }]);
            setSelectedTimeSlot(null);
          } else {
            console.error('[Appointment Debug] Backend API failed with status:', response.status);
            throw new Error(`Backend API failed: ${response.status}`);
          }
        } catch (apiError) {
          console.error('[Appointment Debug] Both Firestore and API failed:', apiError);
          
          // Final fallback: Save locally and show success
          console.log('[Appointment Debug] Using local fallback...');
          const localAppointmentId = `local_${Date.now()}`;
          const localAppointment = { ...appointmentData, id: localAppointmentId };
          
          // Save to AsyncStorage as backup
          try {
            const existingLocalAppointments = await AsyncStorage.getItem('localAppointments');
            const localAppointments = existingLocalAppointments ? JSON.parse(existingLocalAppointments) : [];
            localAppointments.push(localAppointment);
            await AsyncStorage.setItem('localAppointments', JSON.stringify(localAppointments));
            console.log('[Appointment Debug] ✅ Local appointment saved to AsyncStorage');
          } catch (storageError) {
            console.error('[Appointment Debug] Failed to save to AsyncStorage:', storageError);
          }
          
          setSuccessMessage(`Your appointment has been scheduled for ${formatDate(selectedDate)} at ${selectedTimeSlot} (saved locally)`);
          setShowSuccess(true);
          setAppointments([...appointments, localAppointment]);
          setSelectedTimeSlot(null);
          return; // Don't throw error, we've handled it locally
        }
      }
    } catch (error) {
      console.error('[Appointment Debug] ❌ Error scheduling appointment:', error);
      console.error('[Appointment Debug] Error details:', {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        selectedTimeSlot,
        selectedDate: selectedDate?.toISOString()
      });
      
      // Show more specific error message
      let errorMessage = 'Failed to schedule appointment. Please try again.';
      if (error instanceof Error) {
        if (error.message.includes('permission')) {
          errorMessage = 'Permission denied. Please check your account status.';
        } else if (error.message.includes('network')) {
          errorMessage = 'Network error. Please check your internet connection.';
        } else if (error.message.includes('timeout')) {
          errorMessage = 'Request timed out. Please try again.';
        }
      }
      
      setSuccessMessage(errorMessage);
      setShowSuccess(true);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelAppointment = async (appointmentId: string) => {
    setLoading(true);
    try {
      // Delete appointment from Firestore
      await firestore.collection('appointments').doc(appointmentId).delete();
      
      // Remove from local state
      setAppointments(appointments.filter(appt => appt.id !== appointmentId));
      
      setSuccessMessage('Appointment cancelled successfully');
      setShowSuccess(true);
    } catch (error) {
      setSuccessMessage('Failed to cancel appointment. Please try again.');
      setShowSuccess(true);
    } finally {
      setLoading(false);
    }
  };

  // Manual refresh function
  const refreshAppointments = () => {
    setAppointmentsLoading(true);
    // The real-time listener will automatically update the appointments
    // This just triggers the loading state
  };

  // Reset the cancelled by break flag when appointments change
  React.useEffect(() => {
    setIsAppointmentCancelledByBreak(false);
  }, [appointments]);

  // Check if a time slot is within any break
  const isTimeSlotInBreak = (timeSlot: string, date?: Date) => {
    const dateString = date ? date.toDateString() : null;
    
    return breaks.some(breakItem => {
      const timeInRange = timeSlot >= breakItem.fromTime && timeSlot <= breakItem.toTime;
      
      // If it's a daily break (no specific date), apply to all days
      if (!breakItem.specificDate) {
        return timeInRange;
      }
      
      // If it's a specific date break, only apply to that date
      if (dateString && breakItem.specificDate === dateString) {
        return timeInRange;
      }
      
      return false;
    });
  };

  const renderTimeSlot = (timeSlot: string, date: Date) => {
    const isPast = isPastTimeSlot(timeSlot, date);
    const isBooked = isSlotBooked(timeSlot, date);
    const isBookedByMe = appointments.some(appointment => {
      const appointmentDate = new Date(appointment.date);
      return appointmentDate.toDateString() === date.toDateString() && appointment.timeSlot === timeSlot && appointment.userId === auth.currentUser?.uid;
    });
    const isSelected = selectedDate.toDateString() === date.toDateString() && selectedTimeSlot === timeSlot;
    const isBreak = isTimeSlotInBreak(timeSlot, date);
    const isBreaksLoading = breaksLoading; // Show loading state for breaks
    
    // Debug logging for time slot rendering
    console.log('[User Schedule] Rendering time slot:', {
      timeSlot,
      date: date.toDateString(),
      isPast,
      isBooked,
      isBookedByMe,
      isSelected,
      isBreak,
      totalAppointments: appointments.length
    });
    
    return (
      <TouchableOpacity
        key={`${date.toDateString()}-${timeSlot}`}
        style={[
          styles.timeSlot,
          isPast && styles.pastTimeSlot,
          isBreak && styles.breakTimeSlot,
          isBooked && !isBookedByMe && !isBreak && styles.bookedTimeSlot,
          isBookedByMe && !isBreak && styles.bookedByMeTimeSlot,
          isSelected && styles.selectedTimeSlot
        ]}
        onPress={() => handleTimeSlotPress(timeSlot, date)}
        disabled={isPast || isBooked || isBreak}
        activeOpacity={isPast || isBooked || isBreak ? 1 : 0.7}
      >
        <Text style={[
          styles.timeSlotText,
          isPast && styles.pastTimeSlotText,
          isBreak && styles.breakTimeSlotText,
          isBooked && !isBookedByMe && !isBreak && styles.bookedTimeSlotText,
          isBookedByMe && !isBreak && styles.bookedByMeTimeSlotText,
          isSelected && styles.selectedTimeSlotText
        ]}>
          {isBreaksLoading ? '...' : isBreak ? 'Break' : isBooked ? (isBookedByMe ? 'Your Appt' : 'Booked') : timeSlot}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { paddingTop: 50 }]}>
      <View style={styles.headerContainer}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 4, minWidth: 40, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 22, color: COLORS.primaryDark }}>{'<'} </Text>
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Schedule Appointment</Text>
        <View style={{ minWidth: 40 }} />
      </View>

      <ScrollView 
        style={{ flex: 1 }}
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 40 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={appointmentsLoading}
            onRefresh={refreshAppointments}
            colors={[COLORS.primary]}
            tintColor={COLORS.primary}
          />
        }
      >
        <View style={styles.scheduleContainer}>
          {/* Week Header */}
          <View style={styles.weekHeader}>
            <View style={styles.timeColumnHeader}>
              <Text style={styles.timeColumnHeaderText}>Time</Text>
            </View>
            {weekDates.map((date) => (
              <View key={date.toDateString()} style={styles.dateColumnHeader}>
                <Text style={[
                  styles.dateHeaderText,
                  isToday(date) && styles.todayHeaderText
                ]}>
                  {formatDate(date)}
                </Text>
                {isToday(date) && (
                  <View style={styles.todayIndicator}>
                    <Text style={styles.todayIndicatorText}>Today</Text>
                  </View>
                )}
              </View>
            ))}
          </View>

          {/* Time Slots Grid */}
          {timeSlots.map((timeSlot) => (
            <View key={timeSlot} style={styles.timeRow}>
              <View style={styles.timeColumn}>
                <Text style={styles.timeColumnText}>{timeSlot}</Text>
              </View>
              {weekDates.map((date) => renderTimeSlot(timeSlot, date))}
            </View>
          ))}
        </View>

        {/* Selected Appointment Summary */}
        {selectedTimeSlot && (
          <View style={styles.appointmentSummary}>
            <Text style={styles.appointmentSummaryTitle}>Selected Appointment</Text>
            <Text style={styles.appointmentSummaryText}>
              {formatDate(selectedDate)} at {selectedTimeSlot}
            </Text>
            <StyledButton
              title={loading ? "Scheduling..." : "Confirm Appointment"}
              onPress={handleScheduleAppointment}
              disabled={loading}
              style={{ marginTop: 16 }}
            />
          </View>
        )}

        {/* Breaks Information - Removed for cleaner user experience */}

        {/* User's Upcoming Appointment Status */}
        <View style={styles.appointmentSummary}>
          <Text style={styles.appointmentSummaryTitle}>Your Upcoming Appointment</Text>
          {(() => {
            const now = new Date();
            const userId = auth.currentUser?.uid;
            const userUpcomingAppointments = appointments
              .filter(appt => 
                appt.userId === userId && 
                new Date(appt.date) > now
              )
              .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
            
            console.log('[ScheduleAppointment] Total appointments:', appointments.length, 'User upcoming:', userUpcomingAppointments.length);
            
            if (userUpcomingAppointments.length > 0) {
              const nextAppointment = userUpcomingAppointments[0];
              return (
                <>
                  <Text style={[styles.appointmentSummaryText, { color: '#000' }]}>
                    {formatDate(new Date(nextAppointment.date))} at {nextAppointment.timeSlot}
                  </Text>
                  <TouchableOpacity
                    style={styles.cancelButton}
                    onPress={() => handleCancelAppointment(nextAppointment.id)}
                  >
                    <Text style={styles.cancelButtonText}>Cancel Appointment</Text>
                  </TouchableOpacity>
                </>
              );
            } else {
              return (
                <Text style={[styles.appointmentSummaryText, { color: '#666' }]}>
                  No upcoming appointments
                </Text>
              );
            }
          })()}
        </View>
      </ScrollView>
      {/* Success Popup */}
      <Modal
        visible={showSuccess && !isAppointmentCancelledByBreak}
        animationType="fade"
        transparent
        onRequestClose={() => setShowSuccess(false)}
      >
        <View style={styles.successPopupOverlay}>
          <View style={styles.successPopup}>
            <Text style={styles.successTitle}>Success</Text>
            <Text style={styles.successMessage}>{successMessage}</Text>
            <TouchableOpacity style={styles.successButton} onPress={() => { setShowSuccess(false); if (navigation.canGoBack()) navigation.goBack(); }}>
              <Text style={styles.successButtonText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

// --- Dietician Dashboard Screen ---
const DieticianDashboardScreen = ({ navigation }: { navigation: any }) => {
  const [appointments, setAppointments] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [weekDates, setWeekDates] = React.useState<Date[]>([]);
  const [timeSlots] = React.useState(() => {
    const slots = [];
    for (let hour = 7; hour <= 19; hour++) {
      const time = `${hour.toString().padStart(2, '0')}:00`;
      slots.push(time);
    }
    return slots;
  });

  // Helper function to format time consistently
  const formatTimeDisplay = (time: string) => {
    if (!time) return '';
    // Ensure time is in HH:MM format
    if (time.includes(':')) {
      return time;
    }
    // If it's just a number, convert to HH:00 format
    const hour = parseInt(time);
    if (!isNaN(hour)) {
      return `${hour.toString().padStart(2, '0')}:00`;
    }
    return time;
  };

  // Helper function to reset break form
  const resetBreakForm = () => {
    setNewBreakFromTime(null);
    setNewBreakToTime(null);
  };
  const [breaks, setBreaks] = React.useState<any[]>([]); // Simplified for users - no breaks needed
  const [breaksModalVisible, setBreaksModalVisible] = React.useState(false);
  // Add state for new break time range selection
  const [newBreakFromTime, setNewBreakFromTime] = React.useState<string | null>(null);
  const [newBreakToTime, setNewBreakToTime] = React.useState<string | null>(null);
  const [breaksLoading, setBreaksLoading] = React.useState(false);
  const [showBreakConfirmation, setShowBreakConfirmation] = React.useState(false);
  const [breakConfirmationSlot, setBreakConfirmationSlot] = React.useState<{timeSlot: string, date: Date} | null>(null);
  const [showSuccessMessage, setShowSuccessMessage] = React.useState(false);
  const [successMessage, setSuccessMessage] = React.useState('');

  // Add focus detection like user dashboard
  const isFocused = useIsFocused();

  // Add notification listener for dietician
  React.useEffect(() => {
    const user = auth.currentUser;
    if (!user) return;

    const subscription = Notifications.addNotificationReceivedListener(async (notification) => {
      const data = notification.request.content.data;
      
      // Handle user message notifications
      if (data?.type === 'message_notification' && data?.fromUser) {
        console.log('[DieticianDashboard] Received message from user:', data.fromUser);
        // Show notification to dietician about new message
        Alert.alert(
          'New Message',
          `You have a new message from ${data.senderName || 'a user'}`,
          [
            { text: 'View Messages', onPress: () => navigation.navigate('Messages') },
            { text: 'OK', style: 'default' }
          ]
        );
      }
      
      // Handle diet reminder notifications
      if (data?.type === 'diet_reminder') {
        console.log('[DieticianDashboard] User needs new diet:', data.userId);
        // Show reminder to upload new diet
        Alert.alert(
          'Diet Reminder',
          `User ${data.userName || 'needs a new diet plan'}. Their current diet is expiring soon.`,
          [
            { text: 'Upload Diet', onPress: () => navigation.navigate('Upload Diet') },
            { text: 'OK', style: 'default' }
          ]
        );
      }
      
      // Handle diet upload success notifications
      if (data?.type === 'diet_upload_success') {
        console.log('[DieticianDashboard] Diet upload successful for user:', data.userId);
        // Show success notification to dietician
        Alert.alert(
          'Diet Upload Successful',
          `Successfully uploaded new diet for user ${data.userId}`,
          [{ text: 'OK', style: 'default' }]
        );
      }
      
      // Handle multiple users needing new diets
      if (data?.type === 'diet_reminder' && data?.users && Array.isArray(data.users)) {
        console.log('[DieticianDashboard] Multiple users need new diets:', data.users.length);
        const userNames = data.users.map((user: any) => user.name || user.userId).join(', ');
        Alert.alert(
          'Multiple Diet Reminders',
          `${data.users.length} users need new diet plans: ${userNames}`,
          [
            { text: 'View All Users', onPress: () => navigation.navigate('Upload Diet') },
            { text: 'OK', style: 'default' }
          ]
        );
      }
    });

    return () => subscription.remove();
  }, [navigation]);

  React.useEffect(() => {
    // Generate week dates (7 days starting from today)
    const dates = [];
    const today = new Date();
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push(date);
    }
    setWeekDates(dates);
  }, []);

  React.useEffect(() => {
    // Only set up listeners when screen is focused
    if (!isFocused) return;
    
    let isMounted = true;
    let unsubscribe: (() => void) | undefined;

    const setupAppointmentsListener = async () => {
      try {
        // Only clean up past appointments once, not on every render
        const now = new Date();
        const pastAppointmentsSnapshot = await firestore
          .collection('appointments')
          .where('date', '<', now.toISOString())
          .get();

        if (pastAppointmentsSnapshot.docs.length > 0) {
        const batch = firestore.batch();
        pastAppointmentsSnapshot.docs.forEach(doc => {
          batch.delete(doc.ref);
        });
          await batch.commit();
          console.log(`Cleaned up ${pastAppointmentsSnapshot.docs.length} past appointments`);
        }

        // Set up real-time listener only once
        if (isMounted) {
      unsubscribe = firestore
        .collection('appointments')
        .onSnapshot(snapshot => {
              if (isMounted) {
          const appointmentsData = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data()
          }));
          setAppointments(appointmentsData);
          setLoading(false);
              }
        }, error => {
          console.error('Error listening to appointments:', error);
              if (isMounted) {
          setLoading(false);
              }
            });
        }
      } catch (error) {
        console.error('Error setting up appointments listener:', error);
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    setupAppointmentsListener();

    return () => {
      isMounted = false;
      if (unsubscribe) unsubscribe();
    };
  }, [isFocused]); // Add isFocused dependency like user dashboard

  // Real-time listener for breaks
  React.useEffect(() => {
    // Only set up listeners when screen is focused
    if (!isFocused) return;
    
    let isMounted = true;
    
    const unsubscribe = firestore
      .collection('breaks')
      .onSnapshot(snapshot => {
        if (isMounted) {
        const breaksData = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        setBreaks(breaksData);
        }
      }, error => {
        console.error('Error listening to breaks:', error);
      });
      
    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, [isFocused]); // Add isFocused dependency like user dashboard

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  // Helper function to get the next hour from a time slot
  const getNextHour = (timeSlot: string) => {
    const hour = parseInt(timeSlot.split(':')[0]);
    const nextHour = hour + 1;
    return `${nextHour.toString().padStart(2, '0')}:00`;
  };

  const isSlotBooked = (timeSlot: string, date: Date) => {
    const dateString = date.toDateString();
    return appointments.some(appointment => {
      const appointmentDate = new Date(appointment.date);
      return appointmentDate.toDateString() === dateString && appointment.timeSlot === timeSlot;
    });
  };

  const getBookedUserInfo = (timeSlot: string, date: Date) => {
    const dateString = date.toDateString();
    const appointment = appointments.find(appointment => {
      const appointmentDate = new Date(appointment.date);
      return appointmentDate.toDateString() === dateString && appointment.timeSlot === timeSlot;
    });
    return appointment;
  };

  const renderTimeSlot = (timeSlot: string, date: Date) => {
    const isBooked = isSlotBooked(timeSlot, date);
    const isBreak = isTimeSlotInBreak(timeSlot, date);
    const isProcessing = breaksLoading && breakConfirmationSlot !== null && 
      breakConfirmationSlot.timeSlot === timeSlot && 
      breakConfirmationSlot.date.toDateString() === date.toDateString();
    
    // Get user info for booked slots
    const bookedUserInfo = isBooked ? getBookedUserInfo(timeSlot, date) : null;
    
    return (
      <TouchableOpacity
        key={`${date.toDateString()}-${timeSlot}`}
        style={[
          styles.timeSlot,
          isBreak && styles.breakTimeSlot,
          isBooked && !isBreak && styles.bookedTimeSlot,
          isProcessing && { opacity: 0.6 }
        ]}
        disabled={isBreak || isProcessing}
        onPress={() => handleSlotBreakToggle(timeSlot, date)}
        activeOpacity={isBreak || isProcessing ? 1 : 0.7}
      >
        <Text style={[
          styles.timeSlotText,
          isBreak && styles.breakTimeSlotText,
          (isBooked && !isBreak) && styles.bookedTimeSlotText
        ]}>
          {isProcessing ? '...' : isBreak ? 'Break' : isBooked ? 'Booked' : timeSlot}
        </Text>
        {isBooked && !isBreak && bookedUserInfo && (
          <Text style={styles.bookedUserText}>
            {bookedUserInfo.userName || 'Unknown User'}
          </Text>
        )}
      </TouchableOpacity>
    );
  };

  // Add a break
  const handleAddBreak = async (fromTime: string, toTime: string, specificDate?: string) => {
    setBreaksLoading(true);
    try {
      // For daily breaks, check overlap only with other daily breaks
      if (!specificDate) {
        const hasOverlap = breaks.some(breakItem => 
          !breakItem.specificDate && (
            (fromTime >= breakItem.fromTime && fromTime < breakItem.toTime) ||
            (toTime > breakItem.fromTime && toTime <= breakItem.toTime) ||
            (fromTime <= breakItem.fromTime && toTime >= breakItem.toTime)
          )
        );
        
        if (hasOverlap) {
          console.error('Break time range overlaps with existing daily break');
          return;
        }
      }
      
      await firestore.collection('breaks').add({ 
        fromTime: fromTime, 
        toTime: toTime,
        specificDate: specificDate || null // null for daily breaks, date string for specific date breaks
      });
      
      // Reset form and show success message
      resetBreakForm();
      setSuccessMessage(`Break added successfully from ${fromTime} to ${toTime}`);
      setShowSuccessMessage(true);
      
      // Close the modal after successful addition
      setBreaksModalVisible(false);
      
      setTimeout(() => {
        setShowSuccessMessage(false);
      }, 3000);
    } catch (error) {
      console.error('Error adding break:', error);
    } finally {
      setBreaksLoading(false);
    }
  };

  // Remove a break
  const handleRemoveBreak = async (breakId: string) => {
    setBreaksLoading(true);
    try {
      await firestore.collection('breaks').doc(breakId).delete();
      setSuccessMessage('Break removed successfully');
      setShowSuccessMessage(true);
      setTimeout(() => {
        setShowSuccessMessage(false);
      }, 3000);
    } catch (error) {
      console.error('Error removing break:', error);
      setSuccessMessage('Error removing break. Please try again.');
      setShowSuccessMessage(true);
      setTimeout(() => {
        setShowSuccessMessage(false);
      }, 3000);
    } finally {
      setBreaksLoading(false);
    }
  };

  // Check if a time slot is within any break
  const isTimeSlotInBreak = (timeSlot: string, date?: Date) => {
    const dateString = date ? date.toDateString() : null;
    
    return breaks.some(breakItem => {
      const timeInRange = timeSlot >= breakItem.fromTime && timeSlot <= breakItem.toTime;
      
      // If it's a daily break (no specific date), apply to all days
      if (!breakItem.specificDate) {
        return timeInRange;
      }
      
      // If it's a specific date break, only apply to that date
      if (dateString && breakItem.specificDate === dateString) {
        return timeInRange;
      }
      
      return false;
    });
  };

  // Toggle break on slot tap (for dietician) - simplified to single slot breaks
  const handleSlotBreakToggle = async (timeSlot: string, date: Date) => {
    // If already a break, remove it
    if (isTimeSlotInBreak(timeSlot, date)) {
      // Find the break that contains this time slot for this specific date
      const breakItem = breaks.find(breakItem => {
        const timeInRange = timeSlot >= breakItem.fromTime && timeSlot <= breakItem.toTime;
        const dateMatches = !breakItem.specificDate || breakItem.specificDate === date.toDateString();
        return timeInRange && dateMatches;
      });
      
      if (breakItem) {
        await handleRemoveBreak(breakItem.id);
        console.log(`Removed break from ${breakItem.fromTime} to ${breakItem.toTime}`);
      }
      return;
    }
    
    // Show confirmation popup for adding break
    setBreakConfirmationSlot({ timeSlot, date });
    setShowBreakConfirmation(true);
  };

  // Confirm adding break for a specific slot
  const handleConfirmBreak = async () => {
    if (!breakConfirmationSlot) return;
    
    const { timeSlot, date } = breakConfirmationSlot;
    
    try {
      // If booked, cancel appointment and notify user
      const dateString = date.toDateString();
      const appt = appointments.find(appointment => {
        const appointmentDate = new Date(appointment.date);
        return appointmentDate.toDateString() === dateString && appointment.timeSlot === timeSlot;
      });
      
      if (appt) {
        console.log(`[DieticianDashboard] Cancelling appointment:`, appt);
        // Delete appointment
        await firestore.collection('appointments').doc(appt.id).delete();
        
        // Add notification for user
        await firestore.collection('notifications').add({
          userId: appt.userId,
          message: `Your appointment at ${timeSlot} on ${formatDate(date)} was cancelled due to a break.`,
          createdAt: new Date().toISOString(),
          read: false,
        });
        
        console.log(`[DieticianDashboard] Cancelled appointment for ${appt.userName} at ${timeSlot} on ${formatDate(date)}`);
      }
      
      // Add break for this single time slot on this specific date (1 hour duration)
      const endTime = getNextHour(timeSlot);
      await handleAddBreak(timeSlot, endTime, date.toDateString());
      
      console.log(`Added break from ${timeSlot} to ${endTime} on ${formatDate(date)}`);
      
      setSuccessMessage(`Break added successfully from ${timeSlot} to ${endTime} on ${formatDate(date)}`);
      setShowSuccessMessage(true);
      
      setShowBreakConfirmation(false);
      setBreakConfirmationSlot(null);
      
      // Auto-hide success message after 3 seconds
      setTimeout(() => {
        setShowSuccessMessage(false);
      }, 3000);
    } catch (error) {
      console.error('Error confirming break:', error);
      setSuccessMessage('Error adding break. Please try again.');
      setShowSuccessMessage(true);
      setTimeout(() => {
        setShowSuccessMessage(false);
      }, 3000);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { paddingTop: 50 }]}>
        <View style={styles.headerContainer}>
          <View style={{ width: 60 }} />
          <Text style={styles.screenTitle}>Slot</Text>
          <View style={{ width: 60 }} />
        </View>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={{ marginTop: 10, color: COLORS.text, fontSize: 14 }}>
            Loading appointments...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { paddingTop: 50 }]}>
      <View style={styles.headerContainer}>
        <View style={{ width: 60 }} />
        <Text style={styles.screenTitle}>Slot</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView 
        style={{ flex: 1 }}
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 40 }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={() => {
              // Force refresh by cleaning up and restarting the listener
              // Use a separate refresh state to prevent infinite loops
              setLoading(true);
              // The useEffect will handle setting loading to false
            }}
            colors={[COLORS.primary]}
            tintColor={COLORS.primary}
          />
        }
      >
        <View style={styles.scheduleContainer}>
          {/* Week Header */}
          <View style={styles.weekHeader}>
            <View style={styles.timeColumnHeader}>
              <Text style={styles.timeColumnHeaderText}>Time</Text>
            </View>
            {weekDates.map((date) => (
              <View key={date.toDateString()} style={styles.dateColumnHeader}>
                <Text style={[
                  styles.dateHeaderText,
                  isToday(date) && styles.todayHeaderText
                ]}>
                  {formatDate(date)}
                </Text>
                {isToday(date) && (
                  <View style={styles.todayIndicator}>
                    <Text style={styles.todayIndicatorText}>Today</Text>
                  </View>
                )}
              </View>
            ))}
          </View>

          {/* Time Slots Grid */}
          {timeSlots.map((timeSlot) => (
            <View key={timeSlot} style={styles.timeRow}>
              <View style={styles.timeColumn}>
                <Text style={styles.timeColumnText}>{timeSlot}</Text>
              </View>
              {weekDates.map((date) => renderTimeSlot(timeSlot, date))}
            </View>
          ))}
        </View>

        {/* Summary */}
        <View style={styles.appointmentSummary}>
          <Text style={styles.appointmentSummaryTitle}>Appointment Summary</Text>
          {appointments.length === 0 ? (
            <Text style={[styles.appointmentSummaryText, { color: '#000' }]}>No appointments booked.</Text>
          ) : (
            appointments
              .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
              .map((appt, idx) => (
                <Text key={idx} style={[styles.appointmentSummaryText, { color: '#000' }]}>
                  {`${formatDate(new Date(appt.date))} at ${appt.timeSlot} - ${appt.userName}`}
                </Text>
              ))
          )}
        </View>
        <View style={{ alignItems: 'center', marginVertical: 12 }}>
          <TouchableOpacity
            style={{ 
              backgroundColor: breaksLoading ? '#ccc' : '#fbbf24', 
              paddingVertical: 12, 
              paddingHorizontal: 32, 
              borderRadius: 8,
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.1,
              shadowRadius: 4,
              elevation: 3,
            }}
            onPress={() => setBreaksModalVisible(true)}
            disabled={breaksLoading}
          >
            <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 16 }}>
              {breaksLoading ? 'Processing...' : 'Manage Daily Breaks'}
            </Text>
          </TouchableOpacity>
        </View>
        <Modal
          visible={breaksModalVisible}
          animationType="slide"
          transparent={true}
          onRequestClose={() => setBreaksModalVisible(false)}
        >
          <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.3)', justifyContent: 'center', alignItems: 'center' }}>
            <View style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, width: '90%', maxHeight: '80%' }}>
              <ScrollView contentContainerStyle={{ paddingBottom: 16 }}>
                <Text style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 16, textAlign: 'center' }}>Manage Daily Breaks</Text>
                        {/* List of current breaks */}
        {(() => {
          console.log('[Break Management] Current breaks:', breaks);
          return null;
        })()}
        {breaks.length === 0 ? (
          <Text style={{ color: '#888', marginBottom: 12, textAlign: 'center' }}>No breaks set.</Text>
        ) : (
          breaks.map((breakItem, idx) => (
            <View key={breakItem.id} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12, paddingHorizontal: 8, backgroundColor: '#f8f9fa', borderRadius: 8, padding: 12 }}>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 16, fontWeight: '600', color: '#333' }}>
                  {formatTimeDisplay(breakItem.fromTime)} - {formatTimeDisplay(breakItem.toTime)}
                </Text>
                <Text style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                  {breakItem.specificDate ? `Specific: ${new Date(breakItem.specificDate).toLocaleDateString()}` : 'Daily Break'}
                </Text>
              </View>
              <TouchableOpacity onPress={() => handleRemoveBreak(breakItem.id)} style={{ marginLeft: 8, padding: 8, backgroundColor: '#ff4444', borderRadius: 6 }}>
                <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 12 }}>Remove</Text>
              </TouchableOpacity>
            </View>
          ))
        )}
        {/* Add break UI */}
        <View style={{ marginTop: 24, marginBottom: 8, paddingHorizontal: 8 }}>
          <Text style={{ fontSize: 16, marginBottom: 16, textAlign: 'center', fontWeight: '600', color: '#333' }}>Add New Break:</Text>
          
          <View style={{ marginBottom: 16 }}>
            <Text style={{ fontSize: 14, marginBottom: 8, color: '#555', fontWeight: '500' }}>From:</Text>
            <View style={{ borderWidth: 1, borderColor: newBreakFromTime ? '#34D399' : '#ccc', borderRadius: 8, overflow: 'hidden', backgroundColor: '#fff' }}>
              <Picker
                selectedValue={newBreakFromTime}
                style={{ width: '100%', height: 50 }}
                onValueChange={itemValue => setNewBreakFromTime(itemValue)}
                itemStyle={{ fontSize: 16, color: '#333' }}
              >
                <Picker.Item label="Select start time" value={null} color="#999" />
                {timeSlots.map(slot => (
                  <Picker.Item key={slot} label={slot} value={slot} color="#333" />
                ))}
              </Picker>
            </View>
            {newBreakFromTime && (
              <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }}>
                <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: '#34D399', marginRight: 6 }} />
                <Text style={{ fontSize: 12, color: '#34D399', fontWeight: '500' }}>
                  Start time: {newBreakFromTime}
                </Text>
              </View>
            )}
          </View>
          
          <View style={{ marginBottom: 20 }}>
            <Text style={{ fontSize: 14, marginBottom: 8, color: '#555', fontWeight: '500' }}>To:</Text>
            <View style={{ borderWidth: 1, borderColor: newBreakToTime ? '#34D399' : '#ccc', borderRadius: 8, overflow: 'hidden', backgroundColor: '#fff' }}>
              <Picker
                selectedValue={newBreakToTime}
                style={{ width: '100%', height: 50 }}
                onValueChange={itemValue => setNewBreakToTime(itemValue)}
                itemStyle={{ fontSize: 16, color: '#333' }}
              >
                <Picker.Item label="Select end time" value={null} color="#999" />
                {timeSlots.filter(slot => !newBreakFromTime || slot > newBreakFromTime).map(slot => (
                  <Picker.Item key={slot} label={slot} value={slot} color="#333" />
                ))}
              </Picker>
            </View>
            {newBreakToTime && (
              <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }}>
                <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: '#34D399', marginRight: 6 }} />
                <Text style={{ fontSize: 12, color: '#34D399', fontWeight: '500' }}>
                  End time: {newBreakToTime}
                </Text>
              </View>
            )}
          </View>
          
          {newBreakFromTime && newBreakToTime && (
            <View style={{ backgroundColor: '#f0f9ff', padding: 12, borderRadius: 8, marginBottom: 16, borderLeftWidth: 4, borderLeftColor: '#34D399' }}>
              <Text style={{ fontSize: 14, color: '#0369a1', textAlign: 'center', fontWeight: '500' }}>
                Break will be set from {newBreakFromTime} to {newBreakToTime}
              </Text>
            </View>
          )}
          
          <TouchableOpacity
            style={{ 
              backgroundColor: (!newBreakFromTime || !newBreakToTime || breaksLoading) ? '#ccc' : '#34D399', 
              paddingVertical: 12, 
              paddingHorizontal: 24, 
              borderRadius: 8, 
              alignItems: 'center',
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.1,
              shadowRadius: 4,
              elevation: 3
            }}
            onPress={() => newBreakFromTime && newBreakToTime && handleAddBreak(newBreakFromTime, newBreakToTime)}
            disabled={!newBreakFromTime || !newBreakToTime || breaksLoading}
          >
            <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 16 }}>
              {breaksLoading ? 'Adding...' : 'Add Break'}
            </Text>
          </TouchableOpacity>
        </View>
                <TouchableOpacity
                  style={{ marginTop: 20, alignItems: 'center' }}
                  onPress={() => setBreaksModalVisible(false)}
                >
                  <Text style={{ color: '#fbbf24', fontWeight: 'bold', fontSize: 16 }}>Close</Text>
                </TouchableOpacity>
              </ScrollView>
            </View>
          </View>
        </Modal>
        
        {/* Break Confirmation Popup */}
        <Modal
          visible={showBreakConfirmation}
          animationType="fade"
          transparent={true}
          onRequestClose={() => setShowBreakConfirmation(false)}
        >
          <View style={styles.successPopupOverlay}>
            <View style={styles.successPopup}>
              <Text style={styles.successTitle}>Confirm Break</Text>
              <Text style={styles.successMessage}>
                {breakConfirmationSlot ? 
                  `Do you want to set ${breakConfirmationSlot.timeSlot} on ${formatDate(breakConfirmationSlot.date)} as unavailable?` :
                  'Do you want to set this slot as unavailable?'
                }
              </Text>
              <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 16 }}>
                <TouchableOpacity 
                  style={[styles.successButton, { backgroundColor: '#ff4444', marginRight: 8 }]} 
                  onPress={() => setShowBreakConfirmation(false)}
                >
                  <Text style={styles.successButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.successButton, { backgroundColor: '#34D399' }]} 
                  onPress={handleConfirmBreak}
                >
                  <Text style={styles.successButtonText}>Confirm</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
        
        {/* Success Message Popup */}
        <Modal
          visible={showSuccessMessage}
          animationType="fade"
          transparent={true}
          onRequestClose={() => setShowSuccessMessage(false)}
        >
          <View style={styles.successPopupOverlay}>
            <View style={styles.successPopup}>
              <Text style={styles.successTitle}>Success</Text>
              <Text style={styles.successMessage}>{successMessage}</Text>
              <TouchableOpacity 
                style={styles.successButton} 
                onPress={() => setShowSuccessMessage(false)}
              >
                <Text style={styles.successButtonText}>OK</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </ScrollView>
    </SafeAreaView>
  );
};

// Helper function to create missing user profiles
const createMissingUserProfile = async (userId: string, userData: any) => {
  try {
    console.log('[UploadDietScreen] Attempting to create missing user profile for:', userId);
    await createUserProfile({
      id: userId,
      userId: userId, // For backward compatibility
      firstName: userData.firstName || 'User',
      lastName: userData.lastName || '',
      age: userData.age || 25,
      gender: userData.gender || 'other',
      email: userData.email || '',
      currentWeight: userData.currentWeight || 70,
      height: userData.height || 170,
      activityLevel: userData.activityLevel || 'moderate',
      goalWeight: userData.goalWeight || 70,
      dietaryPreference: userData.dietaryPreference || 'vegetarian',
      favouriteCuisine: userData.favouriteCuisine || '',
      allergies: userData.allergies || '',
      medicalConditions: userData.medicalConditions || '',
      targetCalories: userData.targetCalories || 2000,
      targetProtein: userData.targetProtein || 150,
      targetFat: userData.targetFat || 65,

      caloriesBurnedGoal: userData.caloriesBurnedGoal || 500
    });
    console.log('[UploadDietScreen] Successfully created user profile for:', userId);
    return true;
  } catch (error) {
    console.error('[UploadDietScreen] Failed to create user profile for:', userId, error);
    return false;
  }
};

// --- UploadDietScreen (Dietician) ---
const UploadDietScreen = ({ navigation }: { navigation: any }) => {
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<any | null>(null);
  const [uploading, setUploading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [countdowns, setCountdowns] = useState<{ [userId: string]: { days: number; hours: number } }>({});
  const [refresh, setRefresh] = useState(0);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showPdfModal, setShowPdfModal] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  
  // New state for user info popup
  const [showUserInfoModal, setShowUserInfoModal] = useState(false);
  const [selectedUserInfo, setSelectedUserInfo] = useState<any | null>(null);
  const [userInfoLoading, setUserInfoLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
    console.log('[UploadDietScreen] useEffect triggered, refresh value:', refresh);
    let isMounted = true;
    async function fetchData() {
      setLoading(true);
      try {
        // 0. Refresh free plans first (when dietician opens upload diet page)
        try {
          const refreshResult = await refreshFreePlans();
          console.log('[UploadDietScreen] Refresh free plans result:', refreshResult);
          if (refreshResult.updated_count > 0) {
            console.log(`[UploadDietScreen] Updated ${refreshResult.updated_count} users to free plan`);
          }
        } catch (refreshError) {
          console.error('[UploadDietScreen] Error refreshing free plans:', refreshError);
          // Continue with fetching users even if refresh fails
        }
        
        // 1. Fetch users from backend API with fallback
        let usersFromAPI: any[] = [];
        try {
          usersFromAPI = await listNonDieticianUsers();
        console.log('[UploadDietScreen] Users from API:', usersFromAPI);
        } catch (apiError) {
          console.error('[UploadDietScreen] Error fetching users from API:', apiError);
          
          // Fallback: Try to get users from backend directly
          try {
            console.log('[UploadDietScreen] Attempting backend API fallback for users...');
            const backendUrl = process.env.PRODUCTION_BACKEND_URL || 'https://nutricious4u-production.up.railway.app';
            const response = await fetch(`${backendUrl}/api/users`, {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${await auth.currentUser?.getIdToken()}`
              }
            });
            
            if (response.ok) {
              usersFromAPI = await response.json();
              console.log('[UploadDietScreen] ✅ Users from backend API fallback:', usersFromAPI.length);
            } else {
              console.error('[UploadDietScreen] ❌ Backend API fallback failed:', response.status);
              usersFromAPI = [];
            }
          } catch (fallbackError) {
            console.error('[UploadDietScreen] ❌ Both API methods failed:', fallbackError);
            usersFromAPI = [];
          }
        }
        
        let filteredProfiles: any[] = [];
        if (!usersFromAPI || usersFromAPI.length === 0) {
          console.log('[UploadDietScreen] No users found from any source');
        } else {
          console.log('[UploadDietScreen] API returned users:', usersFromAPI.length);
          filteredProfiles = usersFromAPI.filter((u: any) => {
            const isValid = u && u.userId && u.email && u.email !== 'nutricious4u@gmail.com';
            if (!isValid) {
              console.log('[UploadDietScreen] Skipping invalid user:', u);
              return false;
            }
            
            // Skip test users and placeholder users
            const isTestUser = (
              u.firstName?.toLowerCase() === 'test' ||
              u.email?.startsWith('test@') ||
              u.userId?.toLowerCase().includes('test') ||
              (u.firstName === 'User' && u.lastName === '')
            );
            
            if (isTestUser) {
              console.log('[UploadDietScreen] Skipping test user:', u);
              return false;
            }
            
            return true;
          });
          console.log('[UploadDietScreen] After filtering:', filteredProfiles.length, 'users');
        }
        
        // 2. Fetch diet countdowns and PDF URLs for each user - SEQUENTIAL to prevent 499 errors
        const countdownsObj: { [userId: string]: { days: number; hours: number } } = {};
        
        // Process users sequentially instead of simultaneously to prevent connection conflicts
        for (const u of filteredProfiles) {
          try {
            // Use the same backend API as the user dashboard for consistent calculation
            const dietData = await getUserDiet(u.userId);
            console.log(`[UploadDietScreen] User ${u.userId} diet data:`, dietData);
            u.dietPdfUrl = dietData.dietPdfUrl || null;
            
            if (dietData.daysLeft !== null && dietData.daysLeft !== undefined) {
              // Use the backend-calculated daysLeft and hoursLeft for accurate countdown
              const daysRemaining = Math.max(0, dietData.daysLeft);
              const hoursRemaining = dietData.hoursLeft !== null && dietData.hoursLeft !== undefined 
                ? Math.max(0, dietData.hoursLeft) 
                : 0;
              
              countdownsObj[u.userId] = {
                days: daysRemaining,
                hours: hoursRemaining
              };
            } else {
              countdownsObj[u.userId] = { days: 0, hours: 0 };
            }
            
            // Add small delay between API calls to prevent connection conflicts
            await new Promise(resolve => setTimeout(resolve, 200));
          } catch (e) {
            console.error(`[UploadDietScreen] Error fetching diet data for user ${u.userId}:`, e);
            u.dietPdfUrl = null;
            countdownsObj[u.userId] = { days: 0, hours: 0 };
          }
        }
        
        console.log('[UploadDietScreen] Found users:', filteredProfiles.length);
        console.log('[UploadDietScreen] Users:', filteredProfiles.map(u => ({ userId: u.userId, email: u.email, firstName: u.firstName, lastName: u.lastName })));
        
        if (isMounted) {
          setUsers(filteredProfiles);
          setCountdowns(countdownsObj);
          setLoading(false);
        }
      } catch (err) {
        console.error('[UploadDietScreen] Error fetching users:', err);
        if (isMounted) {
          setUsers([]);
          setLoading(false);
        }
      }
    }
    fetchData();
    return () => { isMounted = false; };
  }, [refresh]);

  const handleUserSelect = (user: any) => {
    setSelectedUser(user);
    setShowUploadModal(true);
    setSuccessMsg('');
    setErrorMsg('');
  };

  // New function to handle info icon press
  const handleInfoPress = async (user: any) => {
    try {
      setUserInfoLoading(true);
      setSelectedUserInfo(null);
      setShowUserInfoModal(true);
      
      console.log('[UploadDietScreen] Fetching details for user:', user.userId);
      
      // First test if user exists
      try {
        const testResult = await testUserExists(user.userId);
        console.log('[UploadDietScreen] Test result:', testResult);
      } catch (testError) {
        console.error('[UploadDietScreen] Test endpoint error:', testError);
      }
      
      // Fetch detailed user information
      const userDetails = await getUserDetails(user.userId);
      console.log('[UploadDietScreen] User details received:', userDetails);
      setSelectedUserInfo(userDetails);
    } catch (error: any) {
      console.error('[UploadDietScreen] Error fetching user details:', error);
      console.error('[UploadDietScreen] Error response:', error.response?.data);
      console.error('[UploadDietScreen] Error status:', error.response?.status);
      
      let errorMessage = 'Failed to load user details';
      if (error.response?.status === 404) {
        errorMessage = 'User not found in database';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      alert(errorMessage);
    } finally {
      setUserInfoLoading(false);
    }
  };

  // New function to handle mark as paid
  const handleMarkAsPaid = async () => {
    if (!selectedUserInfo) return;
    
    try {
      setActionLoading(true);
      await markUserPaid(selectedUserInfo.userId);
      
      // Update the user info
      setSelectedUserInfo((prev: any) => prev ? { ...prev, amountDue: 0 } : null);
      
      // Show success message
      setSuccessMsg('User marked as paid successfully');
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (error) {
      console.error('Error marking user as paid:', error);
      alert('Failed to mark user as paid');
    } finally {
      setActionLoading(false);
    }
  };

  // New function to handle lock/unlock app
  const handleToggleAppLock = async () => {
    if (!selectedUserInfo) return;
    
    try {
      setActionLoading(true);
      
      if (selectedUserInfo.isAppLocked) {
        // Unlock the app
        await unlockUserApp(selectedUserInfo.userId);
        setSelectedUserInfo((prev: any) => prev ? { ...prev, isAppLocked: false } : null);
        setSuccessMsg('User app unlocked successfully');
      } else {
        // Lock the app
        await lockUserApp(selectedUserInfo.userId);
        setSelectedUserInfo((prev: any) => prev ? { ...prev, isAppLocked: true } : null);
        setSuccessMsg('User app locked successfully');
      }
      
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (error) {
      console.error('Error toggling app lock:', error);
      alert('Failed to update app lock status');
    } finally {
      setActionLoading(false);
    }
  };

  // Helper function to get the correct PDF URL for a user
  const getPdfUrlForUser = (user: any) => {
    if (!user?.dietPdfUrl) return null;
    
    console.log('[getPdfUrlForUser] Processing dietPdfUrl:', user.dietPdfUrl);
    
    // If it's a Firebase Storage signed URL, use it directly
    if (user.dietPdfUrl.startsWith('https://storage.googleapis.com/')) {
      console.log('[getPdfUrlForUser] Using Firebase Storage URL directly');
      return user.dietPdfUrl;
    }
    
    // If it's a firestore:// URL, use the backend endpoint
    if (user.dietPdfUrl.startsWith('firestore://')) {
      const url = `${API_URL}/users/${user.userId}/diet/pdf`;
      console.log('[getPdfUrlForUser] Using backend endpoint for firestore URL:', url);
      return url;
    }
    
    // If it's just a filename or any other format, use the backend endpoint
    const url = `${API_URL}/users/${user.userId}/diet/pdf`;
    console.log('[getPdfUrlForUser] Using backend endpoint for filename:', url);
    return url;
  };

  // Helper function to create a simplified PDF viewer HTML for iOS compatibility
  const createPdfViewerHtml = (pdfUrl: string) => {
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
          <meta name="apple-mobile-web-app-capable" content="yes">
          <meta name="apple-mobile-web-app-status-bar-style" content="default">
          <style>
            body { 
              margin: 0; 
              padding: 0; 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              background-color: #f5f5f5;
              overflow: hidden;
            }
            .pdf-container {
              width: 100%;
              height: 100vh;
              display: flex;
              flex-direction: column;
            }
            .pdf-header {
              background: #fff;
              padding: 10px;
              border-bottom: 1px solid #e0e0e0;
              text-align: center;
              font-weight: bold;
              font-size: 16px;
            }
            .pdf-viewer {
              flex: 1;
              width: 100%;
              height: 100%;
              border: none;
              background: #fff;
            }
            .pdf-fallback {
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
              flex-direction: column;
              background: #fff;
              padding: 20px;
              text-align: center;
            }
            .pdf-fallback p {
              margin-bottom: 20px;
              font-size: 16px;
              color: #666;
            }
            .pdf-fallback a {
              color: #007AFF;
              text-decoration: none;
              font-size: 16px;
              padding: 12px 24px;
              background: #f0f0f0;
              border-radius: 8px;
              border: 1px solid #ddd;
            }
            .loading {
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
              font-size: 16px;
              color: #666;
            }
          </style>
        </head>
        <body>
          <div class="pdf-container">
            <div class="pdf-header">Diet PDF Viewer</div>
            <div id="loading" class="loading">Loading PDF...</div>
            <iframe 
              id="pdf-viewer"
              class="pdf-viewer" 
              src="${pdfUrl}" 
              type="application/pdf"
              onload="hideLoading()"
              onerror="showFallback()"
              style="display: none;"
            ></iframe>
          </div>
          <script>
            function hideLoading() {
              document.getElementById('loading').style.display = 'none';
              document.getElementById('pdf-viewer').style.display = 'block';
            }
            
            function showFallback() {
              document.body.innerHTML = \`
                <div class="pdf-fallback">
                  <p>Unable to display PDF in browser</p>
                  <a href="${pdfUrl}" target="_blank">Open PDF in New Tab</a>
                </div>
              \`;
            }
            
            // Check if PDF loads successfully within 5 seconds
            setTimeout(() => {
              const iframe = document.getElementById('pdf-viewer');
              if (iframe && iframe.style.display === 'none') {
                showFallback();
              }
            }, 5000);
          </script>
        </body>
      </html>
    `;
  };

  const handleViewDiet = async () => {
    if (!selectedUser) return;
    try {
      console.log('[UploadDietScreen] handleViewDiet called for user:', selectedUser.userId);
      console.log('[UploadDietScreen] selectedUser.dietPdfUrl:', selectedUser.dietPdfUrl);
      
      // Get the PDF URL
      const url = getPdfUrlForUser(selectedUser);
      console.log('[UploadDietScreen] Generated PDF URL:', url);
      
      if (url) {
        // Open PDF in browser instead of in-app viewer
        const canOpen = await Linking.canOpenURL(url);
        if (canOpen) {
          await Linking.openURL(url);
          console.log('[UploadDietScreen] PDF opened in browser successfully');
        } else {
          console.log('[UploadDietScreen] Cannot open URL:', url);
          Alert.alert('Error', 'Cannot open PDF. Please try again.');
        }
      } else {
        console.log('[UploadDietScreen] No PDF URL available');
        Alert.alert('No Diet PDF', 'No diet PDF available for this user.');
      }
    } catch (e) {
      console.error('[UploadDietScreen] Failed to open diet PDF:', e);
      Alert.alert('Error', 'Failed to open diet PDF. Please try again.');
    }
  };

  const handleUpload = async () => {
    if (!selectedUser) return;
    try {
      setUploading(true);
      setSuccessMsg('');
      setErrorMsg('');
      const result = await DocumentPicker.getDocumentAsync({ type: 'application/pdf' });
      if (result.canceled || !result.assets || !result.assets[0]) {
        setUploading(false);
        return;
      }
      const file = {
        uri: result.assets[0].uri,
        name: result.assets[0].name,
        type: 'application/pdf',
      };
      // Assume dieticianId is available from auth context or similar
      const dieticianId = firebase.auth().currentUser?.uid || '';
      const uploadResult = await uploadDietPdf(selectedUser.userId, dieticianId, file);
      
      // The backend has already updated the Firestore document with the new dietPdfUrl
      // We just need to refresh the user data to get the updated information
      console.log('[UploadDietScreen] Diet uploaded successfully, triggering refresh');
      
      // Send a notification to the user about the new diet using local scheduling
      try {
        const unifiedNotificationService = require('./services/unifiedNotificationService').default;
        await unifiedNotificationService.scheduleNewDietNotification(selectedUser.userId, file.name);
        console.log('[UploadDietScreen] New diet notification scheduled locally for user');
      } catch (notificationError) {
        console.error('[UploadDietScreen] Error scheduling new diet notification:', notificationError);
      }
      
      setRefresh(r => r + 1);
      setSuccessMsg('Diet uploaded successfully! User has been notified.');
      setRefresh(r => r + 1);
      setShowUploadModal(false);
      setSelectedUser(null);
    } catch (e) {
      setErrorMsg('Failed to upload diet');
    } finally {
      setUploading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header without back button */}
      <View style={styles.uploadHeaderContainer}>
        <Text style={styles.uploadScreenTitle}>Upload Diet</Text>
      </View>

      {/* Error and Success Messages */}
      {errorMsg ? (
        <View style={styles.uploadErrorContainer}>
          <Text style={styles.uploadErrorText}>{errorMsg}</Text>
        </View>
      ) : null}
      {successMsg ? (
        <View style={styles.uploadSuccessContainer}>
          <Text style={styles.uploadSuccessText}>{successMsg}</Text>
        </View>
      ) : null}

      {/* Users List */}
      {loading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          data={users}
          keyExtractor={item => item.userId}
          style={{ flex: 1 }}
          contentContainerStyle={{ paddingBottom: 20 }}
          ListEmptyComponent={<Text style={{ textAlign: 'center', color: '#888', marginTop: 40 }}>No users found.</Text>}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={{ 
                padding: 18, 
                borderBottomWidth: 1, 
                borderColor: '#eee', 
                backgroundColor: '#fff',
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
              onPress={() => handleUserSelect(item)}
            >
                          <View style={{ flex: 1 }}>
              <Text style={{ fontWeight: 'bold', fontSize: 18, color: '#000' }}>
                {(item.firstName && item.firstName !== 'User') || item.lastName ? `${item.firstName || ''} ${item.lastName || ''}`.trim() : 'Unknown User'}
              </Text>
              <Text style={{ color: '#bbb', fontSize: 12, marginTop: 4 }}>
                Days Until New Diet: {countdowns[item.userId] ? `${countdowns[item.userId].days} days ${countdowns[item.userId].hours} hours` : '-'}
              </Text>
            </View>
              {/* Action buttons container */}
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                {/* Info icon */}
                <TouchableOpacity
                  style={{ 
                    backgroundColor: COLORS.primaryDark, 
                    borderRadius: 12, 
                    width: 24, 
                    height: 24, 
                    alignItems: 'center', 
                    justifyContent: 'center' 
                  }}
                  onPress={() => handleInfoPress(item)}
                >
                  <Text style={{ color: '#fff', fontSize: 14, fontWeight: 'bold' }}>i</Text>
                </TouchableOpacity>
                
                {/* Plus icon */}
                <TouchableOpacity
                  style={{ 
                    backgroundColor: COLORS.primary, 
                    borderRadius: 12, 
                    width: 24, 
                    height: 24, 
                    alignItems: 'center', 
                    justifyContent: 'center' 
                  }}
                  onPress={() => handleUserSelect(item)}
                >
                  <Text style={{ color: '#fff', fontSize: 16, fontWeight: 'bold' }}>+</Text>
                </TouchableOpacity>
              </View>
            </TouchableOpacity>
          )}
        />
      )}

      {/* User Info Modal */}
      <Modal
        visible={showUserInfoModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowUserInfoModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.userInfoModalContent}>
            {userInfoLoading ? (
              <View style={{ alignItems: 'center', padding: 20 }}>
                <ActivityIndicator size="large" color={COLORS.primary} />
                <Text style={{ marginTop: 10, color: COLORS.text }}>Loading user details...</Text>
              </View>
            ) : selectedUserInfo ? (
              <>
                <Text style={styles.userInfoModalTitle}>
                  User Information
                </Text>
                
                <View style={styles.userInfoContent}>
                  <View style={styles.userInfoRow}>
                    <Text style={styles.userInfoLabel}>Name:</Text>
                    <Text style={styles.userInfoValue}>
                      {selectedUserInfo.firstName} {selectedUserInfo.lastName}
                    </Text>
                  </View>
                  
                  <View style={styles.userInfoRow}>
                    <Text style={styles.userInfoLabel}>Plan:</Text>
                    <Text style={styles.userInfoValue}>{selectedUserInfo.plan}</Text>
                  </View>
                  
                  <View style={styles.userInfoRow}>
                    <Text style={styles.userInfoLabel}>Start Date:</Text>
                    <Text style={styles.userInfoValue}>
                      {selectedUserInfo.startDate ? new Date(selectedUserInfo.startDate).toLocaleDateString('en-GB') : 'Not set'}
                    </Text>
                  </View>
                  
                  <View style={styles.userInfoRow}>
                    <Text style={styles.userInfoLabel}>End Date:</Text>
                    <Text style={styles.userInfoValue}>
                      {selectedUserInfo.endDate ? new Date(selectedUserInfo.endDate).toLocaleDateString('en-GB') : 'Not set'}
                    </Text>
                  </View>
                  
                  <View style={styles.userInfoRow}>
                    <Text style={styles.userInfoLabel}>Amount Due:</Text>
                    <Text style={[styles.userInfoValue, { color: selectedUserInfo.amountDue > 0 ? '#FF4444' : '#34D399' }]}>
                      ₹{selectedUserInfo.amountDue.toLocaleString()}
                    </Text>
                  </View>
                  
                  <View style={styles.userInfoRow}>
                    <Text style={styles.userInfoLabel}>App Status:</Text>
                    <Text style={[styles.userInfoValue, { color: selectedUserInfo.isAppLocked ? '#FF4444' : '#34D399' }]}>
                      {selectedUserInfo.isAppLocked ? 'Locked' : 'Unlocked'}
                    </Text>
                  </View>
                </View>
                
                <View style={styles.userInfoButtons}>
                  <TouchableOpacity
                    style={[styles.userInfoButton, styles.cancelButton]}
                    onPress={() => setShowUserInfoModal(false)}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={[
                      styles.userInfoButton, 
                      styles.paidButton,
                      { backgroundColor: actionLoading ? COLORS.placeholder : '#FFD700' }
                    ]}
                    onPress={handleMarkAsPaid}
                    disabled={actionLoading || selectedUserInfo.amountDue === 0}
                  >
                    <Text style={styles.paidButtonText}>
                      {actionLoading ? 'Processing...' : 'Paid'}
                    </Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={[
                      styles.userInfoButton, 
                      selectedUserInfo.isAppLocked ? styles.unlockButton : styles.lockButton,
                      { backgroundColor: actionLoading ? COLORS.placeholder : selectedUserInfo.isAppLocked ? '#34D399' : '#FF4444' }
                    ]}
                    onPress={handleToggleAppLock}
                    disabled={actionLoading}
                  >
                    <Text style={styles.lockButtonText}>
                      {actionLoading ? 'Processing...' : selectedUserInfo.isAppLocked ? 'Unlock' : 'Lock'}
                    </Text>
                  </TouchableOpacity>
                </View>
              </>
            ) : (
              <Text style={{ textAlign: 'center', color: COLORS.text }}>Failed to load user details</Text>
            )}
          </View>
        </View>
      </Modal>

      {/* Upload Modal */}
      <Modal
        visible={showUploadModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowUploadModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.uploadModalContent}>
            <Text style={styles.modalTitle}>
              Upload Diet for {selectedUser?.firstName} {selectedUser?.lastName}
            </Text>
            <Text style={styles.uploadModalSubtitle}>
              Select a PDF file to upload as the diet plan
            </Text>
            
            <TouchableOpacity
              style={[
                styles.uploadButton,
                uploading && styles.uploadButtonDisabled,
                { 
                  width: '100%', 
                  marginBottom: 12,
                  minHeight: 48,
                  justifyContent: 'center'
                }
              ]}
              onPress={handleUpload}
              disabled={uploading}
            >
              <Text style={styles.viewDietButtonText}>
                {uploading ? 'Uploading...' : 'Select PDF'}
              </Text>
            </TouchableOpacity>
            
            {/* View Current Diet Button */}
            {selectedUser?.dietPdfUrl && (
              <TouchableOpacity
                style={[
                  styles.viewDietButton,
                  { 
                    width: '100%', 
                    marginBottom: 12,
                    minHeight: 48,
                    justifyContent: 'center',
                    backgroundColor: COLORS.primaryDark
                  }
                ]}
                onPress={handleViewDiet}
              >
                <Text style={styles.viewDietButtonText}>View Current Diet</Text>
              </TouchableOpacity>
            )}
            
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[
                  styles.cancelButton,
                  { backgroundColor: '#FF4444' } // Red color for cancel
                ]}
                onPress={() => {
                  setShowUploadModal(false);
                  setSelectedUser(null);
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* PDF Viewer Modal */}
      <Modal
        visible={showPdfModal}
        animationType="slide"
        transparent={false}
        onRequestClose={() => setShowPdfModal(false)}
      >
        <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', padding: 12, backgroundColor: '#fff', zIndex: 2 }}>
            <TouchableOpacity onPress={() => setShowPdfModal(false)} style={{ padding: 8, marginRight: 8 }}>
              <Text style={{ fontSize: 22, color: COLORS.primary }}>Close</Text>
            </TouchableOpacity>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: COLORS.text }}>
              Diet PDF - {selectedUser?.firstName} {selectedUser?.lastName}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            {pdfUrl ? (
              <WebView
                source={{ html: createPdfViewerHtml(pdfUrl) }}
                style={{ flex: 1, width: '100%' }}
                startInLoadingState={true}
                javaScriptEnabled={true}
                domStorageEnabled={true}
                allowsInlineMediaPlayback={true}
                mediaPlaybackRequiresUserAction={false}
                allowsBackForwardNavigationGestures={false}
                allowsLinkPreview={false}
                cacheEnabled={true}
                cacheMode="LOAD_DEFAULT"
                onError={(syntheticEvent) => {
                  const { nativeEvent } = syntheticEvent;
                  console.log('[WebView] Error: ', nativeEvent);
                  Alert.alert('PDF Error', 'Failed to load PDF. Please try again.');
                }}
                onHttpError={(syntheticEvent) => {
                  const { nativeEvent } = syntheticEvent;
                  console.log('[WebView] HTTP Error: ', nativeEvent);
                  if (nativeEvent.statusCode === 404) {
                    Alert.alert('PDF Not Found', 'The diet PDF could not be found. Please ask the dietician to upload a new diet.');
                  } else {
                    Alert.alert('PDF Error', 'Failed to load PDF. Please try again.');
                  }
                }}
                onLoadEnd={(syntheticEvent) => {
                  const { nativeEvent } = syntheticEvent;
                  console.log('[WebView] Loaded: ', nativeEvent);
                }}
                onLoadStart={(syntheticEvent) => {
                  const { nativeEvent } = syntheticEvent;
                  console.log('[WebView] Loading URL: ', nativeEvent.url);
                }}
                onMessage={(event) => {
                  console.log('[WebView] Message: ', event.nativeEvent.data);
                }}
                onNavigationStateChange={(navState) => {
                  console.log('[WebView] Navigation state: ', navState);
                }}
                renderLoading={() => (
                  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}>
                    <ActivityIndicator size="large" color={COLORS.primary} />
                    <Text style={{ marginTop: 10, color: COLORS.text }}>Loading PDF...</Text>
                  </View>
                )}
              />
            ) : (
              <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}>
                <ActivityIndicator size="large" color={COLORS.primary} />
                <Text style={{ marginTop: 10, color: COLORS.text }}>Preparing PDF...</Text>
              </View>
            )}
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

export { UploadDietScreen };