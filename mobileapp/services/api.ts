import axios from 'axios';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

let apiHost = 'localhost';

if (Constants.manifest?.debuggerHost) {
  apiHost = Constants.manifest.debuggerHost.split(':')[0];
  console.log('[API] Using debuggerHost IP:', apiHost);
} else if (Constants.expoConfig?.hostUri) {
  apiHost = Constants.expoConfig.hostUri.split(':')[0];
  console.log('[API] Using expoConfig.hostUri IP:', apiHost);
}

// Fallback: If still localhost or 127.0.0.1, use a common LAN IP
if (apiHost === 'localhost' || apiHost === '127.0.0.1') {
  // Try to get the actual IP from the logs or use a common one
  apiHost = '172.16.0.28'; // Based on the logs showing this IP
  console.log('[API] Fallback to LAN IP:', apiHost);
}

export const API_URL = `http://${apiHost}:8000/api`;
console.log('[API] Final API_URL:', API_URL);

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
    console.log('[API] Axios error:', error);
    if (error.message === 'Network Error') {
      console.error('Network Error - Please check your connection or the server status');
    }
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
  userId: string;
  firstName: string;
  lastName: string;
  age: number;
  gender: string;
  email: string;
  currentWeight?: number;
  goalWeight?: number;
  height?: number;
  dietaryPreference?: string; // veg, non-veg, vegan
  favouriteCuisine?: string;
  allergies?: string;
  medicalConditions?: string;
  streakCount?: number;
  lastFoodLogDate?: string;
  targetCalories?: number;
  targetProtein?: number;
  targetFat?: number;
  activityLevel?: string;
  stepGoal?: number;
  caloriesBurnedGoal?: number;
  dietPdfUrl?: string; // URL to the user's diet PDF
  lastDietUpload?: string; // Timestamp of last diet upload
  dieticianId?: string; // ID of the dietician who uploaded the diet
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
}

export async function searchFood(query: string): Promise<FoodItem[]> {
  const response = await api.get('/food/search', { params: { query } });
  return response.data.foods;
}

export const logFood = async (userId: string, foodName: string, servingSize: string = "100") => {
  try {
    console.log('[logFood] Request payload:', { userId, foodName, servingSize });
    const response = await api.post('/food/log', { userId, foodName, servingSize });
    console.log('[logFood] Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('[logFood] Error:', error);
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
      console.log(`[logWorkout] Attempt ${attempt}/${maxRetries} - Request payload:`, workoutData);
      const response = await api.post('/workout/log', workoutData);
      console.log('[logWorkout] Response:', response.data);
      return response.data;
    } catch (error: any) {
      lastError = error;
      console.error(`[logWorkout] Attempt ${attempt} failed:`, error);
      
      // If it's a timeout or network error, retry
      if (error.code === 'ECONNABORTED' || error.message === 'Network Error') {
        if (attempt < maxRetries) {
          console.log(`[logWorkout] Retrying in ${attempt * 1000}ms...`);
          await new Promise(resolve => setTimeout(resolve, attempt * 1000));
          continue;
        }
      }
      
      // For other errors, don't retry
      break;
    }
  }
  
  // If all attempts failed, try a fallback approach
  console.log('[logWorkout] All attempts failed, trying fallback...');
  try {
    // Try with a simpler endpoint or different approach
    const fallbackResponse = await api.post('/api/workouts/log', {
      workout_id: workoutData.exerciseId,
      duration: workoutData.duration
    });
    console.log('[logWorkout] Fallback response:', fallbackResponse.data);
    return {
      ...workoutData,
      calories: fallbackResponse.data.calories_burned || 100
    };
  } catch (fallbackError) {
    console.error('[logWorkout] Fallback also failed:', fallbackError);
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
    console.log('[getLogSummary] Request for userId:', userId);
    const response = await api.get(`/food/log/summary/${userId}`);
    console.log('[getLogSummary] Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('[getLogSummary] Error:', error);
    throw error;
  }
}

// User Profile API calls
export const createUserProfile = async (profile: UserProfile): Promise<UserProfile> => {
  try {
    const response = await axios.post(`${API_URL}/users/profile`, profile);
    return response.data;
  } catch (error) {
    console.error('Error creating user profile:', error);
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
    console.error('Error getting user profile:', error);
    throw error;
  }
}

export const updateUserProfile = async (userId: string, profileUpdate: UpdateUserProfile): Promise<UserProfile> => {
  try {
    const response = await axios.patch(`${API_URL}/users/${userId}/profile`, profileUpdate);
    return response.data;
  } catch (error) {
    console.error('Error updating user profile:', error);
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
    console.error('[sendChatbotMessage] Error:', error);
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

export const testDietNotification = async (userId: string) => {
  const response = await api.post(`/users/${userId}/diet/notifications/test`);
  return response.data;
};

// --- List All Users Except Dietician ---
export const listNonDieticianUsers = async () => {
  const response = await api.get('/users/non-dietician');
  return response.data;
};

export default api; 