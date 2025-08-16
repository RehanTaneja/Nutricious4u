import axios from 'axios';
import { Platform } from 'react-native';
import { PRODUCTION_BACKEND_URL } from '@env';
import { logger } from '../utils/logger';

// Debug environment variables
console.log('=== API CONFIG DEBUG ===');
console.log('PRODUCTION_BACKEND_URL:', PRODUCTION_BACKEND_URL || 'MISSING');
console.log('__DEV__:', __DEV__);
console.log('Platform:', Platform.OS);
console.log('==========================');

// Environment-based API URL configuration
let apiHost = 'nutricious4u-production.up.railway.app';
let port = '';
let protocol = 'https';

// Always use production backend URL for now (since localhost backend is not running)
if (__DEV__) {
  // Development: Use Railway URL for Expo Go testing
  apiHost = PRODUCTION_BACKEND_URL || 'nutricious4u-production.up.railway.app';
  port = '';
  protocol = 'https';
  logger.log('[API] Using Railway backend for development:', apiHost);
} else {
  // Production: Use Railway URL
  apiHost = PRODUCTION_BACKEND_URL || 'nutricious4u-production.up.railway.app';
  port = '';
  protocol = 'https';
  logger.log('[API] Using production backend:', apiHost);
}

export const API_URL = `${protocol}://${apiHost}${port}/api`;
logger.log('[API] Final API_URL:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000, // Increased timeout to 30 seconds for Gemini API calls
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    logger.log('[API] Axios error:', error);
    if (error.message === 'Network Error' || error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      logger.error('Network Error - Backend server is not available');
      // In production, throw the error to help with debugging
      if (!__DEV__) {
        return Promise.reject(error);
      }
      // In development, return a mock response to prevent app crashes
      return Promise.resolve({ 
        data: { 
          error: 'Backend not available',
          message: 'The backend server is not currently available. Please ensure your backend is deployed and accessible.',
          isBackendError: true
        }, 
        status: 503 
      });
    }
    return Promise.reject(error);
  }
);

// Add request interceptor for better error handling
api.interceptors.request.use(
  config => {
    logger.log('[API] Making request to:', config.url);
    return config;
  },
  error => {
    logger.log('[API] Request error:', error);
    return Promise.reject(error);
  }
);

export interface FoodItem {
  id: string;
  name: string;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  servingSize: number;
  per_100g?: boolean;
}

export interface DailyNutrition {
  day: string;
  calories: number;
  protein: number;
  fat: number;
  carbs?: number;
}

export interface LogSummaryResponse {
  history: DailyNutrition[];
}

export interface UserProfile {
  id: string;
  userId?: string; // For backward compatibility
  firstName: string;
  lastName: string;
  age: number;
  gender: string;
  currentWeight: number;
  goalWeight: number;
  height: number;
  dietaryPreference: string;
  favouriteCuisine: string;
  allergies: string;
  medicalConditions: string;
  targetCalories: number;
  targetProtein: number;
  targetFat: number;
  activityLevel: string;
  stepGoal: number;
  caloriesBurnedGoal: number;
  email: string;
  dietPdfUrl?: string; // URL to the user's diet PDF
  lastDietUpload?: string; // Timestamp of last diet upload
  dieticianId?: string; // ID of the dietician who uploaded the diet
  // Subscription fields
  subscriptionPlan?: string; // '1month', '3months', '6months'
  subscriptionStartDate?: string;
  subscriptionEndDate?: string;
  totalAmountPaid?: number;
  isSubscriptionActive?: boolean;
  // Plan queuing fields
  queuedPlans?: QueuedPlan[];
  totalDueAmount?: number;
}

export interface QueuedPlan {
  planId: string;
  startDate: string;
  endDate: string;
  amount: number;
}

export interface UpdateUserProfile {
  firstName?: string;
  lastName?: string;
  age?: number;
  gender?: string;
  currentWeight?: number;
  goalWeight?: number;
  height?: number;
  dietaryPreference?: string;
  favouriteCuisine?: string;
  allergies?: string;
  medicalConditions?: string;
  targetCalories?: number;
  targetProtein?: number;
  targetFat?: number;
  activityLevel?: string;
  stepGoal?: number;
  caloriesBurnedGoal?: number;
  email?: string;
  // Subscription fields
  subscriptionPlan?: string;
  subscriptionStartDate?: string;
  subscriptionEndDate?: string;
  totalAmountPaid?: number;
  isSubscriptionActive?: boolean;
}

export interface SubscriptionPlan {
  planId: string;
  name: string;
  duration: string;
  price: number;
  description: string;
  features?: string[]; // List of features included in this plan
  isFree?: boolean; // Indicates if this is the free plan
}

export interface SubscriptionStatus {
  subscriptionPlan?: string;
  subscriptionStartDate?: string;
  subscriptionEndDate?: string;
  currentSubscriptionAmount: number;
  totalAmountPaid: number;
  isSubscriptionActive: boolean;
  isFreeUser?: boolean; // Indicates if user is on free plan
  autoRenewalEnabled?: boolean; // Indicates if auto-renewal is enabled
}

export interface Notification {
  id: string;
  userId: string;
  title: string;
  body: string;
  type: string;
  timestamp: string;
  read: boolean;
}





export interface SubscriptionResponse {
  success: boolean;
  message: string;
  subscription?: {
    planId: string;
    startDate: string;
    endDate: string;
    amountPaid: number;
    totalAmountPaid: number;
  };
}

export async function searchFood(query: string): Promise<FoodItem[]> {
  const response = await api.get('/food/search', { params: { query } });
  return response.data.foods;
}

export const logFood = async (userId: string, foodName: string, servingSize: string = "100") => {
  try {
    logger.log('[logFood] Request payload:', { userId, foodName, servingSize });
    const response = await api.post('/food/log', { userId, foodName, servingSize });
    logger.log('[logFood] Response:', response.data);
    return response.data;
  } catch (error) {
    logger.error('[logFood] Error:', error);
    throw error;
  }
};

export const logWorkout = async (workoutData: { 
  userId: string; 
  exerciseId: string; 
  exerciseName: string; 
  type: string; 
  duration: string; 
  sets: any; 
  reps: any; 
  date: any; 
}) => {
  const maxRetries = 3;
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      logger.log(`[logWorkout] Attempt ${attempt}/${maxRetries} - Request payload:`, workoutData);
      const response = await api.post('/workout/log', workoutData);
      logger.log('[logWorkout] Response:', response.data);
      return response.data;
    } catch (error: any) {
      lastError = error;
      logger.error(`[logWorkout] Attempt ${attempt} failed:`, error);
      
      // If it's a timeout or network error, retry
      if (error.code === 'ECONNABORTED' || error.message === 'Network Error') {
        if (attempt < maxRetries) {
          logger.log(`[logWorkout] Retrying in ${attempt * 1000}ms...`);
          await new Promise(resolve => setTimeout(resolve, attempt * 1000));
          continue;
        }
      }
      
      // For other errors, don't retry
      break;
    }
  }
  
  // If all attempts failed, try a fallback approach
  logger.log('[logWorkout] All attempts failed, trying fallback...');
  try {
    // Try with a simpler endpoint or different approach
    const fallbackResponse = await api.post('/api/workouts/log', {
      workout_id: workoutData.exerciseId,
      duration: workoutData.duration
    });
    logger.log('[logWorkout] Fallback response:', fallbackResponse.data);
    return {
      ...workoutData,
      calories: fallbackResponse.data.calories_burned || 100
    };
  } catch (fallbackError) {
    logger.error('[logWorkout] Fallback also failed:', fallbackError);
    throw lastError; // Throw the original error
  }
};

export interface DailySummary {
  calories: number;
  protein: number;
  fat: number;
}

export interface HistoryItem {
  day: string;
  calories: number;
}

export interface LogSummaryResponse {
  daily_summary: DailySummary;
  seven_day_history: HistoryItem[];
}

export const getLogSummary = async (userId: string): Promise<LogSummaryResponse> => {
  try {
    logger.log('[getLogSummary] Request for userId:', userId);
    const response = await api.get(`/food/log/summary/${userId}`);
    logger.log('[getLogSummary] Response:', response.data);
    return response.data;
  } catch (error) {
    logger.error('[getLogSummary] Error:', error);
    throw error;
  }
}

// User Profile API calls
export const createUserProfile = async (profile: UserProfile): Promise<UserProfile> => {
  try {
    const response = await axios.post(`${API_URL}/users/profile`, profile);
    return response.data;
  } catch (error) {
    logger.error('Error creating user profile:', error);
    throw error;
  }
};

export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  try {
    const response = await api.get(`/users/${userId}/profile`);
    return response.data;
  } catch (error: any) {
    if (error.response && error.response.status === 404) {
      // No profile exists for this user
      return null;
    }
    logger.error('Error getting user profile:', error);
    throw error;
  }
}

export const updateUserProfile = async (userId: string, profileUpdate: UpdateUserProfile): Promise<UserProfile> => {
  try {
    const response = await axios.patch(`${API_URL}/users/${userId}/profile`, profileUpdate);
    return response.data;
  } catch (error) {
    logger.error('Error updating user profile:', error);
    throw error;
  }
};

export interface ChatMessageRequest {
  userId: string;
  chat_history: Array<{ sender: string; text: string }>;
  user_profile: UserProfile | null;
  user_message: string;
}

export interface ChatMessageResponse {
  bot_message: string;
}

export const sendChatbotMessage = async (
  userId: string,
  chat_history: Array<{ sender: string; text: string }>,
  user_profile: UserProfile | null,
  user_message: string
): Promise<string> => {
  try {
    const response = await api.post<ChatMessageResponse>('/chatbot/message', {
      userId,
      chat_history,
      user_profile,
      user_message,
    });
    return response.data.bot_message;
  } catch (error) {
    logger.error('[sendChatbotMessage] Error:', error);
    throw error;
  }
};

// --- Routine Types ---
export interface RoutineItem {
  type: 'food' | 'workout';
  name: string;
  quantity?: string; // For food: serving size; for workout: duration
}

export interface Routine {
  id: string;
  name: string;
  items: RoutineItem[];
  calories: number;
  protein: number;
  fat: number;
  burned: number;
  created_at: string;
  updated_at: string;
}

export interface RoutineCreateRequest {
  name: string;
  items: RoutineItem[];
}

export interface RoutineUpdateRequest {
  name?: string;
  items?: RoutineItem[];
}

export const listRoutines = async (userId: string): Promise<Routine[]> => {
  const response = await api.get(`/users/${userId}/routines`);
  return response.data;
};

export const createRoutine = async (userId: string, routine: RoutineCreateRequest): Promise<Routine> => {
  const response = await api.post(`/users/${userId}/routines`, routine);
  return response.data;
};

export const updateRoutine = async (userId: string, routineId: string, routine: RoutineUpdateRequest): Promise<Routine> => {
  const response = await api.patch(`/users/${userId}/routines/${routineId}`, routine);
  return response.data;
};

export const deleteRoutine = async (userId: string, routineId: string): Promise<void> => {
  await api.delete(`/users/${userId}/routines/${routineId}`);
};

export const logRoutine = async (userId: string, routineId: string): Promise<void> => {
  await api.post(`/users/${userId}/routines/${routineId}/log`);
};

export interface WorkoutLogSummaryDay {
  day: string;
  calories: number;
}

export interface WorkoutLogSummaryResponse {
  history: WorkoutLogSummaryDay[];
}

export const getWorkoutLogSummary = async (userId: string): Promise<WorkoutLogSummaryResponse> => {
  const response = await api.get(`/workout/log/summary/${userId}`);
  return response.data;
};

export async function scanFoodPhoto(imageUri: string, userId: string) {
  const formData = new FormData();
  formData.append('userId', userId);
  formData.append('photo', {
    uri: imageUri,
    name: 'photo.jpg',
    type: 'image/jpeg',
  } as any);
  const response = await fetch(`${API_URL}/food/scan-photo`, {
    method: 'POST',
    body: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  if (!response.ok) throw new Error('Failed to scan food photo');
  return response.json();
}

// --- Diet PDF Upload (Dietician) ---
export const uploadDietPdf = async (userId: string, dieticianId: string, file: any) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('dietician_id', dieticianId);
  const response = await api.post(`/users/${userId}/diet/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// --- Get User Diet PDF and Countdown ---
export const getUserDiet = async (userId: string) => {
  const response = await api.get(`/users/${userId}/diet`);
  return response.data;
};

// --- Diet Notification Management ---
export const extractDietNotifications = async (userId: string) => {
  const response = await api.post(`/users/${userId}/diet/notifications/extract`);
  return response.data;
};

export const getDietNotifications = async (userId: string) => {
  const response = await api.get(`/users/${userId}/diet/notifications`);
  return response.data;
};

export const deleteDietNotification = async (userId: string, notificationId: string) => {
  const response = await api.delete(`/users/${userId}/diet/notifications/${notificationId}`);
  return response.data;
};

export const updateDietNotification = async (userId: string, notificationId: string, notificationUpdate: any) => {
  const response = await api.put(`/users/${userId}/diet/notifications/${notificationId}`, notificationUpdate);
  return response.data;
};

export const scheduleDietNotifications = async (userId: string) => {
  const response = await api.post(`/users/${userId}/diet/notifications/schedule`);
  return response.data;
};

export const cancelDietNotifications = async (userId: string) => {
  const response = await api.post(`/users/${userId}/diet/notifications/cancel`);
  return response.data;
};

export const testDietNotification = async (userId: string) => {
  const response = await api.post(`/users/${userId}/diet/notifications/test`);
  return response.data;
};

// --- List All Users Except Dietician ---
export const listNonDieticianUsers = async () => {
  const response = await api.get('/users/non-dietician');
  return response.data;
};

// --- Refresh Free Plans (for Dietician) ---
export const refreshFreePlans = async (): Promise<{ success: boolean; message: string; updated_count: number }> => {
  const response = await api.post('/users/refresh-free-plans');
  return response.data;
};

// --- Get All User Profiles (for Messages Screen) ---
export const getAllUserProfiles = async () => {
  const response = await api.get('/users/all-profiles');
  return response.data;
};

// --- Subscription Management ---
export const getSubscriptionPlans = async (): Promise<SubscriptionPlan[]> => {
  const response = await api.get('/subscription/plans');
  return response.data.plans;
};

export const selectSubscription = async (userId: string, planId: string): Promise<SubscriptionResponse> => {
  const response = await api.post('/subscription/select', { userId, planId });
  return response.data;
};

export const getSubscriptionStatus = async (userId: string): Promise<SubscriptionStatus> => {
  const response = await api.get(`/subscription/status/${userId}`);
  return response.data;
};

export const cancelSubscription = async (userId: string): Promise<{ success: boolean; message: string }> => {
  const response = await api.post(`/subscription/cancel/${userId}`);
  return response.data;
};

export const toggleAutoRenewal = async (userId: string, enabled: boolean): Promise<{ success: boolean; message: string }> => {
  const response = await api.post(`/subscription/toggle-auto-renewal/${userId}?enabled=${enabled}`);
  return response.data;
};

export const addSubscriptionAmount = async (userId: string, planId: string): Promise<{ success: boolean; message: string; amountAdded: number; newTotal: number }> => {
  const response = await api.post(`/subscription/add-amount/${userId}?planId=${planId}`);
  return response.data;
};

// --- Notification Management ---
export const getUserNotifications = async (userId: string): Promise<{ notifications: Notification[] }> => {
  const response = await api.get(`/notifications/${userId}`);
  return response.data;
};

export const markNotificationRead = async (notificationId: string): Promise<{ success: boolean; message: string }> => {
  const response = await api.put(`/notifications/${notificationId}/read`);
  return response.data;
};

export const deleteNotification = async (notificationId: string): Promise<{ success: boolean; message: string }> => {
  const response = await api.delete(`/notifications/${notificationId}`);
  return response.data;
};

// --- User Management (Dietician) ---
export const getUserDetails = async (userId: string) => {
  const response = await api.get(`/users/${userId}/details`);
  return response.data;
};

export const markUserPaid = async (userId: string) => {
  const response = await api.post(`/users/${userId}/mark-paid`);
  return response.data;
};

export const lockUserApp = async (userId: string) => {
  const response = await api.post(`/users/${userId}/lock-app`);
  return response.data;
};

export const unlockUserApp = async (userId: string) => {
  const response = await api.post(`/users/${userId}/unlock-app`);
  return response.data;
};

export const getUserLockStatus = async (userId: string) => {
  const response = await api.get(`/users/${userId}/lock-status`);
  return response.data;
};

export const testUserExists = async (userId: string) => {
  const response = await api.get(`/users/${userId}/test`);
  return response.data;
};

export default api; 