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

// Environment-based API URL configuration with fallbacks
let apiHost = 'nutricious4u-production.up.railway.app';
let port = '';
let protocol = 'https';

// Enhanced environment variable handling for EAS builds
const getBackendUrl = () => {
  // Priority 1: Environment variable
  if (PRODUCTION_BACKEND_URL) {
    return PRODUCTION_BACKEND_URL;
  }
  
  // Priority 2: Hardcoded fallback for EAS builds
  if (!__DEV__) {
    logger.log('[API] Using hardcoded fallback URL for EAS build');
    return 'nutricious4u-production.up.railway.app';
  }
  
  // Priority 3: Development fallback
  logger.log('[API] Using development fallback URL');
  return 'nutricious4u-production.up.railway.app';
};

// Always use production backend URL for now (since localhost backend is not running)
if (__DEV__) {
  // Development: Use Railway URL for Expo Go testing
  apiHost = getBackendUrl();
  port = '';
  protocol = 'https';
  logger.log('[API] Using Railway backend for development:', apiHost);
} else {
  // Production: Use Railway URL
  apiHost = getBackendUrl();
  port = '';
  protocol = 'https';
  logger.log('[API] Using production backend:', apiHost);
}

export const API_URL = `${protocol}://${apiHost}${port}/api`;
logger.log('[API] Final API_URL:', API_URL);

// Request deduplication to prevent simultaneous identical requests
const pendingRequests = new Map<string, Promise<any>>();

// Request queue to prevent concurrent requests on iOS
class RequestQueue {
  private queue: Array<() => Promise<any>> = [];
  private processing = false;
  private maxConcurrent = Platform.OS === 'ios' ? 1 : 3; // Single request at a time for iOS
  private activeRequests = 0;
  private lastRequestTime = 0;
  private minRequestInterval = Platform.OS === 'ios' ? 2000 : 100; // 2 seconds minimum interval for iOS
  private requestTimeout = Platform.OS === 'ios' ? 45000 : 15000; // 45 second timeout for iOS

  async add<T>(requestFn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          // Ensure minimum interval between requests on iOS
          if (Platform.OS === 'ios') {
            const now = Date.now();
            const timeSinceLastRequest = now - this.lastRequestTime;
            if (timeSinceLastRequest < this.minRequestInterval) {
              const delay = this.minRequestInterval - timeSinceLastRequest;
              logger.log(`[RequestQueue] Waiting ${delay}ms before next request`);
              await new Promise(resolve => setTimeout(resolve, delay));
            }
            this.lastRequestTime = Date.now();
          }
          
          this.activeRequests++;
          logger.log(`[RequestQueue] Starting request. Active: ${this.activeRequests}`);
          
          // Add timeout to prevent hanging requests
          const timeoutPromise = new Promise((_, timeoutReject) => {
            setTimeout(() => {
              timeoutReject(new Error(`Request timeout after ${this.requestTimeout}ms`));
            }, this.requestTimeout);
          });
          
          // Race between the actual request and timeout
          const result = await Promise.race([
            requestFn(),
            timeoutPromise
          ]) as T;
          
          resolve(result);
          return result;
        } catch (error) {
          logger.error(`[RequestQueue] Request failed:`, error);
          reject(error);
          throw error;
        } finally {
          this.activeRequests--;
          logger.log(`[RequestQueue] Request completed. Active: ${this.activeRequests}`);
          this.processNext();
        }
      });
      
      this.processNext();
    });
  }

  private async processNext() {
    if (this.processing || this.queue.length === 0 || this.activeRequests >= this.maxConcurrent) {
      return;
    }

    this.processing = true;
    
    while (this.queue.length > 0 && this.activeRequests < this.maxConcurrent) {
      const requestFn = this.queue.shift();
      if (requestFn) {
        // Add longer delay between requests on iOS to prevent connection issues
        if (Platform.OS === 'ios' && this.activeRequests > 0) {
          await new Promise(resolve => setTimeout(resolve, 2500)); // Increased delay to 2.5 seconds
        }
        requestFn();
      }
    }
    
    this.processing = false;
  }

  getQueueLength(): number {
    return this.queue.length;
  }

  getActiveRequests(): number {
    return this.activeRequests;
  }
}

const requestQueue = new RequestQueue();

// iOS-specific axios configuration with connection pooling
const axiosConfig = {
  baseURL: API_URL,
  timeout: Platform.OS === 'ios' ? 60000 : 25000, // Increased to 60 seconds for iOS
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': Platform.OS === 'ios' ? 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0' : 'Nutricious4u/1',
    'Accept': 'application/json',
    'Connection': 'keep-alive',
    'Keep-Alive': 'timeout=300, max=1000', // Increased timeout significantly
  },
  // iOS-specific settings
  ...(Platform.OS === 'ios' && {
    // Prevent connection reuse issues on iOS
    maxRedirects: 0,
    validateStatus: (status: number) => status < 500, // Don't throw on 4xx errors
    // Add connection pooling settings
    httpAgent: undefined, // Let axios handle connection pooling
    httpsAgent: undefined,
    // Add request timeout and retry settings
    timeout: 60000, // 60 seconds for iOS
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
    // Add additional iOS-specific settings
    decompress: true,
  })
};

const api = axios.create(axiosConfig);

// Enhanced retry configuration with circuit breaker pattern
const retryConfig = {
  retries: Platform.OS === 'ios' ? 0 : 1, // No retries for iOS to prevent cascading failures
  retryDelay: 1000, // Reduced delay
  retryCondition: (error: any) => {
    // Only retry on actual network errors, not on client-side issues
    return (
      error.message === 'Network Error' ||
      error.code === 'ECONNABORTED' ||
      error.code === 'ECONNREFUSED' ||
      error.code === 'ENOTFOUND' ||
      error.code === 'ETIMEDOUT' ||
      (error.response && error.response.status >= 500 && error.response.status !== 503) // Don't retry on 503 (service unavailable)
      // Removed 499 from retry condition to prevent retry loops
    );
  }
};

// Circuit breaker pattern to prevent cascading failures
class CircuitBreaker {
  private failures = 0;
  private lastFailureTime = 0;
  private state = 'CLOSED';
  private readonly failureThreshold = Platform.OS === 'ios' ? 3 : 5; // Lower threshold for iOS
  private readonly resetTimeout = Platform.OS === 'ios' ? 60000 : 30000; // 60 seconds for iOS

  async execute(fn: () => Promise<any>) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.resetTimeout) {
        this.state = 'HALF_OPEN';
        logger.log('[CIRCUIT_BREAKER] Moving to HALF_OPEN state');
      } else {
        logger.log('[CIRCUIT_BREAKER] Circuit breaker is OPEN, rejecting request');
        throw new Error('Service temporarily unavailable. Please try again later.');
      }
    }
    
    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = 'CLOSED';
  }

  private onFailure() {
    this.failures += 1;
    this.lastFailureTime = Date.now();
    
    if (this.failures >= this.failureThreshold) {
      this.state = 'OPEN';
      logger.error(`[CIRCUIT_BREAKER] Circuit breaker opened after ${this.failures} failures`);
    }
  }
}

const circuitBreaker = new CircuitBreaker();

// Enhanced retry interceptor with circuit breaker
api.interceptors.response.use(
  response => response,
  async error => {
    const { config } = error;
    
    // Initialize retry count if not set
    if (!config || !config.__retryCount) {
      config.__retryCount = 0;
    }
    
    // Handle 499 errors immediately - don't retry
    if (error.response?.status === 499) {
      logger.error('[API] Client closed connection (499):', error.config?.url);
      logger.error('[API] 499 Error details:', {
        url: error.config?.url,
        method: error.config?.method,
        platform: Platform.OS,
        timestamp: new Date().toISOString()
      });
      
      // For iOS, provide a more specific error message and implement recovery
      const errorMessage = Platform.OS === 'ios' 
        ? 'Connection was interrupted. Please try again.'
        : 'Request was cancelled. Please try again.';
      
      // For iOS, implement a more graceful error handling
      if (Platform.OS === 'ios') {
        // Log additional context for debugging
        logger.error('[API] iOS 499 Error Context:', {
          userAgent: error.config?.headers?.['User-Agent'],
          connection: error.config?.headers?.['Connection'],
          keepAlive: error.config?.headers?.['Keep-Alive']
        });
      }
      
      return Promise.reject({
        ...error,
        message: errorMessage,
        isClientClosedError: true,
        isIOSConnectionError: Platform.OS === 'ios',
        shouldRetry: false // Explicitly mark as non-retryable
      });
    }
    
    // Check if we should retry
    if (retryConfig.retryCondition(error) && config.__retryCount < retryConfig.retries) {
      config.__retryCount += 1;
      
      logger.log(`[API] Retrying request (${config.__retryCount}/${retryConfig.retries}): ${config.url}`);
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, retryConfig.retryDelay * config.__retryCount));
      
      // Retry the request
      return api(config);
    }
    
    // Log the final error
    logger.log('[API] Final error after retries:', error);
    
    // Handle specific iOS connection issues
    if (Platform.OS === 'ios' && (
      error.message === 'Network Error' || 
      error.code === 'ECONNABORTED'
    )) {
      logger.error('[API] iOS connection issue detected:', error.message || error.code);
      
      return Promise.reject({
        ...error,
        message: 'Connection issue detected. Please check your internet connection and try again.',
        isIOSConnectionError: true
      });
    }
    
    return Promise.reject(error);
  }
);

// Enhanced request interceptor with deduplication
api.interceptors.request.use(
  config => {
    logger.log('[API] Making request to:', config.url);
    
    // Add iOS-specific request headers
    if (Platform.OS === 'ios') {
      config.headers = {
        ...config.headers,
        'X-Platform': 'ios',
        'X-App-Version': '1.0.0',
        'X-Request-ID': Date.now().toString() // Add request ID for tracking
      } as any;
    }
    
    return config;
  },
  error => {
    logger.log('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Enhanced API wrapper with request deduplication, circuit breaker, and queuing
const enhancedApi = {
  get: async <T>(url: string, config?: any) => {
    const requestKey = `GET:${url}`;
    
    // Check if there's already a pending request
    if (pendingRequests.has(requestKey)) {
      logger.log('[API] Deduplicating request:', url);
      return pendingRequests.get(requestKey);
    }
    
    // Create new request with queuing
    const requestPromise = requestQueue.add(() => 
      circuitBreaker.execute(() => api.get(url, config))
    );
    pendingRequests.set(requestKey, requestPromise);
    
    try {
      const result = await requestPromise;
      return result;
    } finally {
      // Clean up pending request
      pendingRequests.delete(requestKey);
    }
  },
  
  post: async (url: string, data?: any, config?: any) => {
    return requestQueue.add(() => 
      circuitBreaker.execute(() => api.post(url, data, config))
    );
  },
  
  patch: async (url: string, data?: any, config?: any) => {
    return requestQueue.add(() => 
      circuitBreaker.execute(() => api.patch(url, data, config))
    );
  },
  
  delete: async (url: string, config?: any) => {
    return requestQueue.add(() => 
      circuitBreaker.execute(() => api.delete(url, config))
    );
  },
  
  put: async (url: string, data?: any, config?: any) => {
    return requestQueue.add(() => 
      circuitBreaker.execute(() => api.put(url, data, config))
    );
  }
};

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

  caloriesBurnedGoal: number;
  email: string;
  dietPdfUrl?: string; // URL to the user's diet PDF
  lastDietUpload?: string; // Timestamp of last diet upload
  dieticianId?: string; // ID of the dietician who uploaded the diet
  // Subscription fields
  subscriptionPlan?: string; // '1month', '2months', '3months', '6months'
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

export async function getNutritionData(foodName: string, quantity: string): Promise<{food: FoodItem, success: boolean}> {
  const response = await enhancedApi.get('/food/nutrition', { 
    params: { food_name: foodName, quantity: quantity } 
  });
  return response.data;
}

export const logFood = async (userId: string, foodName: string, servingSize: string = "100", nutrition?: {calories: number, protein: number, fat: number}) => {
  try {
    // CRITICAL FIX: Include user's timezone offset for consistent local time handling
    const timezoneOffset = new Date().getTimezoneOffset(); // Returns offset in minutes
    
    const payload = nutrition 
      ? { userId, foodName, servingSize, calories: nutrition.calories, protein: nutrition.protein, fat: nutrition.fat, timezoneOffset }
      : { userId, foodName, servingSize, timezoneOffset };
    
    logger.log('[logFood] Request payload with timezone:', payload);
    logger.log(`[logFood] User timezone offset: ${timezoneOffset} minutes (${timezoneOffset / 60} hours)`);
    const response = await enhancedApi.post('/food/log', payload);
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
      const response = await enhancedApi.post('/workout/log', workoutData);
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
    const fallbackResponse = await enhancedApi.post('/api/workouts/log', {
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
    const response = await enhancedApi.get(`/food/log/summary/${userId}`);
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
    const response = await enhancedApi.post(`/users/profile`, profile);
    return response.data;
  } catch (error) {
    logger.error('Error creating user profile:', error);
    throw error;
  }
};

// Global profile request lock to prevent multiple simultaneous requests
let profileRequestLock: { [userId: string]: Promise<any> } = {};

// Profile caching to prevent duplicate requests during login
let profileCache: { [userId: string]: { profile: any; timestamp: number } } = {};
const PROFILE_CACHE_DURATION = 30000; // 30 seconds

export const getUserProfile = async (userId: string): Promise<UserProfile> => {
  // Check cache first
  const cached = profileCache[userId];
  if (cached && Date.now() - cached.timestamp < PROFILE_CACHE_DURATION) {
    logger.log(`[getUserProfile] Returning cached profile for ${userId}`);
    return cached.profile;
  }

  // Check if there's already a request in progress for this user
  const existingRequest = profileRequestLock[userId];
  if (existingRequest) {
    logger.log(`[getUserProfile] Request already in progress for ${userId}, waiting...`);
    try {
      const result = await existingRequest;
      return result;
    } catch (error) {
      logger.error(`[getUserProfile] Error waiting for existing request for ${userId}:`, error);
      // If the existing request failed, we'll try again
    }
  }

  logger.log(`[getUserProfile] Fetching fresh profile for ${userId}`);
  
  // Create a new request promise and store it in the lock
  const requestPromise = requestQueue.add(async () => {
    try {
      const response = await api.get(`/users/${userId}/profile`);
      
      // Cache the profile
      profileCache[userId] = {
        profile: response.data,
        timestamp: Date.now()
      };
      
      logger.log(`[getUserProfile] Successfully fetched and cached profile for ${userId}`);
      return response.data;
    } catch (error: any) {
      logger.error(`[getUserProfile] Error fetching profile for ${userId}:`, error);
      throw error;
    } finally {
      // Remove the lock when the request completes (success or failure)
      delete profileRequestLock[userId];
    }
  });

  // Store the promise in the lock
  profileRequestLock[userId] = requestPromise;
  
  return requestPromise;
};

// Function to clear profile cache (useful for logout)
export const clearProfileCache = (userId?: string) => {
  if (userId) {
    delete profileCache[userId];
    delete profileRequestLock[userId]; // Also clear the lock
    logger.log(`[clearProfileCache] Cleared cache and lock for ${userId}`);
  } else {
    profileCache = {};
    profileRequestLock = {}; // Clear all locks
    logger.log(`[clearProfileCache] Cleared all profile cache and locks`);
  }
};

// Function to update profile cache (useful after profile updates)
export const updateProfileCache = (userId: string, profile: UserProfile) => {
  profileCache[userId] = {
    profile,
    timestamp: Date.now()
  };
  logger.log(`[updateProfileCache] Updated cache for ${userId}`);
};

// Function to check if a profile request is in progress
export const isProfileRequestInProgress = (userId: string): boolean => {
  return !!profileRequestLock[userId];
};

// Function to check if login is in progress (imported from App.tsx)
export const isLoginInProgress = (): boolean => {
  // This will be set by App.tsx during login sequence
  return (global as any).isLoginInProgress || false;
};

// Enhanced getUserProfile that respects login state
export const getUserProfileSafe = async (userId: string): Promise<UserProfile> => {
  // Check if login is in progress
  if (isLoginInProgress()) {
    logger.log(`[getUserProfileSafe] Login in progress, deferring profile request for ${userId}`);
    // Wait a bit and try again
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  return getUserProfile(userId);
};

// Recipe API functions using the queue system
export const getRecipes = async (): Promise<any[]> => {
  logger.log('[getRecipes] Fetching recipes through API queue');
  return requestQueue.add(async () => {
    try {
      const response = await api.get('/recipes');
      logger.log('[getRecipes] Successfully fetched recipes');
      return response.data.recipes || [];
    } catch (error: any) {
      logger.error('[getRecipes] Error fetching recipes:', error);
      throw error;
    }
  });
};

export const updateUserProfile = async (userId: string, profileUpdate: UpdateUserProfile): Promise<UserProfile> => {
  try {
    const response = await enhancedApi.patch(`/users/${userId}/profile`, profileUpdate);
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
    const response = await enhancedApi.post('/chatbot/message', {
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
  const response = await enhancedApi.get(`/users/${userId}/routines`);
  return response.data;
};

export const createRoutine = async (userId: string, routine: RoutineCreateRequest): Promise<Routine> => {
  const response = await enhancedApi.post(`/users/${userId}/routines`, routine);
  return response.data;
};

export const updateRoutine = async (userId: string, routineId: string, routine: RoutineUpdateRequest): Promise<Routine> => {
  const response = await enhancedApi.patch(`/users/${userId}/routines/${routineId}`, routine);
  return response.data;
};

export const deleteRoutine = async (userId: string, routineId: string): Promise<void> => {
  await enhancedApi.delete(`/users/${userId}/routines/${routineId}`);
};

export const logRoutine = async (userId: string, routineId: string): Promise<void> => {
  await enhancedApi.post(`/users/${userId}/routines/${routineId}/log`);
};

export interface WorkoutLogSummaryDay {
  day: string;
  calories: number;
}

export interface WorkoutLogSummaryResponse {
  history: WorkoutLogSummaryDay[];
}

export const getWorkoutLogSummary = async (userId: string): Promise<WorkoutLogSummaryResponse> => {
  const response = await enhancedApi.get(`/workout/log/summary/${userId}`);
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
  const response = await enhancedApi.post(`/users/${userId}/diet/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// --- Get User Diet PDF and Countdown ---
export const getUserDiet = async (userId: string) => {
  const response = await enhancedApi.get(`/users/${userId}/diet`);
  return response.data;
};

// --- Diet Notification Management ---
export const extractDietNotifications = async (userId: string) => {
  logger.log('[API] Starting diet extraction through API queue');
  
  try {
    logger.log('[API] Making diet extraction request to:', `${API_URL}/users/${userId}/diet/notifications/extract`);
    const response = await enhancedApi.post(`/users/${userId}/diet/notifications/extract`);
    logger.log('[API] Diet extraction request completed successfully');
    return response.data;
  } catch (error) {
    logger.error('[API] Diet extraction request failed:', error);
    throw error;
  }
};

export const getDietNotifications = async (userId: string) => {
  const response = await enhancedApi.get(`/users/${userId}/diet/notifications`);
  return response.data;
};

export const deleteDietNotification = async (userId: string, notificationId: string) => {
  const response = await enhancedApi.delete(`/users/${userId}/diet/notifications/${notificationId}`);
  return response.data;
};

export const updateDietNotification = async (userId: string, notificationId: string, notificationUpdate: any) => {
  const response = await enhancedApi.put(`/users/${userId}/diet/notifications/${notificationId}`, notificationUpdate);
  return response.data;
};

export const scheduleDietNotifications = async (userId: string) => {
  const response = await enhancedApi.post(`/users/${userId}/diet/notifications/schedule`);
  return response.data;
};

export const cancelDietNotifications = async (userId: string) => {
  const response = await enhancedApi.post(`/users/${userId}/diet/notifications/cancel`);
  return response.data;
};

export const testDietNotification = async (userId: string) => {
  const response = await enhancedApi.post(`/users/${userId}/diet/notifications/test`);
  return response.data;
};

// --- List All Users Except Dietician ---
export const listNonDieticianUsers = async () => {
  const response = await enhancedApi.get('/users/non-dietician');
  return response.data;
};

// --- Refresh Free Plans (for Dietician) ---
export const refreshFreePlans = async (): Promise<{ success: boolean; message: string; updated_count: number }> => {
  const response = await enhancedApi.post('/users/refresh-free-plans');
  return response.data;
};

// --- Get All User Profiles (for Messages Screen) ---
export const getAllUserProfiles = async () => {
  const response = await enhancedApi.get('/users/all-profiles');
  return response.data;
};

// --- Subscription Management ---
export const getSubscriptionPlans = async (): Promise<SubscriptionPlan[]> => {
  const response = await enhancedApi.get('/subscription/plans');
  return response.data.plans;
};

export const selectSubscription = async (userId: string, planId: string): Promise<SubscriptionResponse> => {
  const response = await enhancedApi.post('/subscription/select', { userId, planId });
  return response.data;
};

export const getSubscriptionStatus = async (userId: string): Promise<SubscriptionStatus> => {
  const response = await enhancedApi.get(`/subscription/status/${userId}`);
  return response.data;
};

export const cancelSubscription = async (userId: string): Promise<{ success: boolean; message: string; cancelled_notifications?: number }> => {
  const response = await enhancedApi.post(`/subscription/cancel/${userId}`);
  return response.data;
};

export const toggleAutoRenewal = async (userId: string, enabled: boolean): Promise<{ success: boolean; message: string }> => {
  const response = await enhancedApi.post(`/subscription/toggle-auto-renewal/${userId}?enabled=${enabled}`);
  return response.data;
};

export const addSubscriptionAmount = async (userId: string, planId: string): Promise<{ success: boolean; message: string; amountAdded: number; newTotal: number }> => {
  const response = await enhancedApi.post(`/subscription/add-amount/${userId}?planId=${planId}`);
  return response.data;
};

// --- Notification Management ---
export const getUserNotifications = async (userId: string): Promise<{ notifications: Notification[] }> => {
  const response = await enhancedApi.get(`/notifications/${userId}`);
  return response.data;
};

export const markNotificationRead = async (notificationId: string): Promise<{ success: boolean; message: string }> => {
  const response = await enhancedApi.put(`/notifications/${notificationId}/read`);
  return response.data;
};

export const deleteNotification = async (notificationId: string): Promise<{ success: boolean; message: string }> => {
  const response = await enhancedApi.delete(`/notifications/${notificationId}`);
  return response.data;
};

// --- User Management (Dietician) ---
export const getUserDetails = async (userId: string) => {
  const response = await enhancedApi.get(`/users/${userId}/details`);
  return response.data;
};

export const markUserPaid = async (userId: string) => {
  const response = await enhancedApi.post(`/users/${userId}/mark-paid`);
  return response.data;
};

export const lockUserApp = async (userId: string) => {
  const response = await enhancedApi.post(`/users/${userId}/lock-app`);
  return response.data;
};

export const unlockUserApp = async (userId: string) => {
  const response = await enhancedApi.post(`/users/${userId}/unlock-app`);
  return response.data;
};

export const getUserLockStatus = async (userId: string) => {
  console.log('[API] 🔒 Fetching user lock status for:', userId);
  const response = await enhancedApi.get(`/users/${userId}/lock-status`);
  console.log('[API] 🔒 Lock status response:', response.data);
  console.log('[API] 🔒 Lock status call completed, app should continue to main screen');
  
  // Add additional logging call to backend for EAS builds
  if (!__DEV__) {
    try {
      // Make a logging request with crash detection info
      await enhancedApi.get(`/users/${userId}/profile?debugEvent=LOCK_STATUS_COMPLETED&platform=${Platform.OS}&timestamp=${new Date().toISOString()}&nextStep=NAVIGATE_TO_MAINTABS`);
    } catch (logError) {
      console.warn('Failed to log lock status completion:', logError);
    }
  }
  
  return response.data;
};

export const testUserExists = async (userId: string) => {
  const response = await enhancedApi.get(`/users/${userId}/test`);
  return response.data;
};

// Frontend Event Logging for iOS Debug using existing endpoints
export const logFrontendEvent = async (userId: string, event: string, data?: any) => {
  try {
    // Only log in EAS builds (not Expo Go)
    if (!__DEV__) {
      const logData = {
        userId,
        event,
        data: JSON.stringify(data || {}),
        platform: Platform.OS,
        timestamp: new Date().toISOString(),
        userAgent: Platform.OS === 'ios' ? 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0' : 'Nutricious4u/1'
      };
      
      // Use profile endpoint with special logging data - this will show in backend logs
      // The backend will see this in the logs when the request is made
      const profileLogData = {
        ...logData,
        frontendEvent: event,
        eventData: data,
        debugLog: true
      };
      
      console.log('📱 FRONTEND EVENT LOG:', JSON.stringify(profileLogData, null, 2));
      
      // Make a quick GET request to existing endpoint to trigger backend logging
      // The query params will show in Railway logs
      const logUrl = `/users/${userId}/profile?frontendEvent=${encodeURIComponent(event)}&platform=${Platform.OS}&timestamp=${encodeURIComponent(new Date().toISOString())}&data=${encodeURIComponent(JSON.stringify(data || {}))}`;
      
      // Use a timeout to not hang the app
      const logPromise = enhancedApi.get(logUrl);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Log timeout')), 3000)
      );
      
      await Promise.race([logPromise, timeoutPromise]);
    }
  } catch (error) {
    // Silently fail - don't let logging break the app
    console.warn('Failed to log frontend event:', error);
  }
};

// Check if new diet popup should be shown
export const checkNewDietPopupTrigger = async (userId: string) => {
  try {
    const response = await enhancedApi.get(`/users/${userId}/new-diet-popup-trigger`);
    return response.data;
  } catch (error) {
    console.error('Error checking new diet popup trigger:', error);
    return { showPopup: false };
  }
};

// Function to get queue status for debugging
export const getQueueStatus = () => {
  return {
    queueLength: requestQueue.getQueueLength(),
    activeRequests: requestQueue.getActiveRequests(),
    platform: Platform.OS
  };
};

// --- Missing Functions for iOS Fix ---
export const resetDailyData = async (userId: string) => {
  const response = await enhancedApi.post(`/user/${userId}/reset-daily`, {});
  return response.data;
};

export const sendAppointmentNotification = async (
  type: 'scheduled' | 'cancelled',
  userName: string,
  appointmentDate: string,
  timeSlot: string,
  userEmail: string
) => {
  const response = await enhancedApi.post('/notifications/send', {
    recipientId: 'dietician', // Send to dietician
    type: 'appointment',
    appointmentType: type,
    appointmentDate,
    timeSlot,
    userName,
    userEmail
  });
  return response.data;
};

export const sendMessageNotification = async (
  recipientUserId: string, 
  message: string, 
  senderName: string,
  senderUserId: string,
  senderIsDietician: boolean
) => {
  const response = await enhancedApi.post('/notifications/send', {
    recipientId: recipientUserId,
    type: 'message',
    message,
    senderName,
    isDietician: senderIsDietician
  });
  return response.data;
};

export const searchFood = async (searchQuery: string): Promise<FoodItem[]> => {
  const response = await enhancedApi.get(`/food/search?q=${encodeURIComponent(searchQuery)}`);
  return response.data.foods || [];
};

export default enhancedApi; 