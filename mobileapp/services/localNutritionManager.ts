/**
 * Local Nutrition Data Manager
 * Manages 7-day rolling nutrition data using AsyncStorage
 * Automatically resets at midnight and maintains data consistency
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export interface DayNutrition {
  date: string; // YYYY-MM-DD format
  calories: number;
  protein: number;
  fat: number;
  burned: number;
}

export interface NutritionData {
  days: DayNutrition[];
  lastResetDate: string;
}

class LocalNutritionManager {
  private static instance: LocalNutritionManager;
  private readonly STORAGE_KEY = 'nutrition_data';
  private readonly RESET_KEY = 'last_reset_date';
  private readonly BURNED_KEY_PREFIX = 'burned_today_';

  private constructor() {}

  static getInstance(): LocalNutritionManager {
    if (!LocalNutritionManager.instance) {
      LocalNutritionManager.instance = new LocalNutritionManager();
    }
    return LocalNutritionManager.instance;
  }

  /**
   * Get today's date in YYYY-MM-DD format
   */
  private getTodayDate(): string {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  /**
   * Get yesterday's date in YYYY-MM-DD format
   */
  private getYesterdayDate(): string {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const year = yesterday.getFullYear();
    const month = String(yesterday.getMonth() + 1).padStart(2, '0');
    const day = String(yesterday.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  /**
   * Generate 7-day date range (6 days ago to today)
   */
  private generate7DayRange(): string[] {
    const dates: string[] = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      dates.push(`${year}-${month}-${day}`);
    }
    
    return dates;
  }

  /**
   * Check if it's a new day and reset if needed
   */
  async checkAndResetIfNewDay(): Promise<boolean> {
    try {
      const today = this.getTodayDate();
      const lastReset = await AsyncStorage.getItem(this.RESET_KEY);
      
      console.log('[LocalNutrition] Checking for new day reset...');
      console.log('[LocalNutrition] Today:', today);
      console.log('[LocalNutrition] Last reset:', lastReset);
      
      if (lastReset !== today) {
        console.log('[LocalNutrition] New day detected, resetting data...');
        await this.resetForNewDay();
        await AsyncStorage.setItem(this.RESET_KEY, today);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('[LocalNutrition] Error checking new day:', error);
      return false;
    }
  }

  /**
   * Reset data for new day (shift left, add new day at right)
   */
  private async resetForNewDay(): Promise<void> {
    try {
      const currentData = await this.getNutritionData();
      const today = this.getTodayDate();
      
      // Remove oldest day (leftmost) and add new day (rightmost)
      const newDays = currentData.days.slice(1); // Remove first element
      newDays.push({
        date: today,
        calories: 0,
        protein: 0,
        fat: 0,
        burned: 0
      });
      
      const newData: NutritionData = {
        days: newDays,
        lastResetDate: today
      };
      
      await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(newData));
      console.log('[LocalNutrition] Data reset for new day:', newData);
    } catch (error) {
      console.error('[LocalNutrition] Error resetting for new day:', error);
    }
  }

  /**
   * Initialize with 7 days of empty data if not exists
   */
  async initializeIfNeeded(): Promise<void> {
    try {
      const existing = await AsyncStorage.getItem(this.STORAGE_KEY);
      if (!existing) {
        console.log('[LocalNutrition] Initializing with 7 days of empty data...');
        const dates = this.generate7DayRange();
        const days: DayNutrition[] = dates.map(date => ({
          date,
          calories: 0,
          protein: 0,
          fat: 0,
          burned: 0
        }));
        
        const initialData: NutritionData = {
          days,
          lastResetDate: this.getTodayDate()
        };
        
        await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(initialData));
        console.log('[LocalNutrition] Initialized with:', initialData);
      }
    } catch (error) {
      console.error('[LocalNutrition] Error initializing:', error);
    }
  }

  /**
   * Get all nutrition data
   */
  async getNutritionData(): Promise<NutritionData> {
    try {
      const data = await AsyncStorage.getItem(this.STORAGE_KEY);
      if (data) {
        return JSON.parse(data);
      }
      
      // Initialize if not exists
      await this.initializeIfNeeded();
      const newData = await AsyncStorage.getItem(this.STORAGE_KEY);
      return newData ? JSON.parse(newData) : { days: [], lastResetDate: this.getTodayDate() };
    } catch (error) {
      console.error('[LocalNutrition] Error getting nutrition data:', error);
      return { days: [], lastResetDate: this.getTodayDate() };
    }
  }

  /**
   * Get today's nutrition data
   */
  async getTodayData(): Promise<DayNutrition> {
    try {
      const data = await this.getNutritionData();
      const today = this.getTodayDate();
      const todayData = data.days.find(day => day.date === today);
      
      if (todayData) {
        return todayData;
      }
      
      // If today's data doesn't exist, create it
      const newTodayData: DayNutrition = {
        date: today,
        calories: 0,
        protein: 0,
        fat: 0,
        burned: 0
      };
      
      // Add to data and save
      data.days.push(newTodayData);
      await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
      
      return newTodayData;
    } catch (error) {
      console.error('[LocalNutrition] Error getting today data:', error);
      return {
        date: this.getTodayDate(),
        calories: 0,
        protein: 0,
        fat: 0,
        burned: 0
      };
    }
  }

  /**
   * Add food nutrition to today's data
   */
  async addFoodNutrition(calories: number, protein: number, fat: number): Promise<void> {
    try {
      console.log('[LocalNutrition] Adding food nutrition:', { calories, protein, fat });
      
      const data = await this.getNutritionData();
      const today = this.getTodayDate();
      
      // Find today's data or create it
      let todayData = data.days.find(day => day.date === today);
      if (!todayData) {
        todayData = {
          date: today,
          calories: 0,
          protein: 0,
          fat: 0,
          burned: 0
        };
        data.days.push(todayData);
      }
      
      // Add nutrition values
      todayData.calories += calories;
      todayData.protein += protein;
      todayData.fat += fat;
      
      // Ensure we don't exceed 7 days
      if (data.days.length > 7) {
        data.days = data.days.slice(-7);
      }
      
      // Save updated data
      await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
      
      console.log('[LocalNutrition] Updated today data:', todayData);
    } catch (error) {
      console.error('[LocalNutrition] Error adding food nutrition:', error);
    }
  }

  /**
   * Add workout calories to today's data
   */
  async addWorkoutCalories(calories: number): Promise<void> {
    try {
      console.log('[LocalNutrition] Adding workout calories:', calories);
      
      const data = await this.getNutritionData();
      const today = this.getTodayDate();
      
      // Find today's data or create it
      let todayData = data.days.find(day => day.date === today);
      if (!todayData) {
        todayData = {
          date: today,
          calories: 0,
          protein: 0,
          fat: 0,
          burned: 0
        };
        data.days.push(todayData);
      }
      
      // Add burned calories
      todayData.burned += calories;
      
      // Ensure we don't exceed 7 days
      if (data.days.length > 7) {
        data.days = data.days.slice(-7);
      }
      
      // Save updated data
      await AsyncStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
      
      console.log('[LocalNutrition] Updated today burned calories:', todayData.burned);
    } catch (error) {
      console.error('[LocalNutrition] Error adding workout calories:', error);
    }
  }

  /**
   * Get 7-day data for bar graph (chronological order)
   */
  async getBarGraphData(): Promise<DayNutrition[]> {
    try {
      const data = await this.getNutritionData();
      const dates = this.generate7DayRange();
      
      // Ensure we have data for all 7 days
      const barGraphData: DayNutrition[] = dates.map(date => {
        const dayData = data.days.find(day => day.date === date);
        return dayData || {
          date,
          calories: 0,
          protein: 0,
          fat: 0,
          burned: 0
        };
      });
      
      console.log('[LocalNutrition] Bar graph data:', barGraphData);
      return barGraphData;
    } catch (error) {
      console.error('[LocalNutrition] Error getting bar graph data:', error);
      return [];
    }
  }

  /**
   * Get summary data in the format expected by the frontend
   */
  async getSummaryData(): Promise<{
    history: Array<{day: string, calories: number, protein: number, fat: number}>;
    daily_summary: {calories: number, protein: number, fat: number};
  }> {
    try {
      const data = await this.getNutritionData();
      const today = this.getTodayData();
      
      // Convert to frontend format
      const history = data.days.map(day => ({
        day: day.date,
        calories: day.calories,
        protein: day.protein,
        fat: day.fat
      }));
      
      const daily_summary = {
        calories: today.calories,
        protein: today.protein,
        fat: today.fat
      };
      
      return { history, daily_summary };
    } catch (error) {
      console.error('[LocalNutrition] Error getting summary data:', error);
      return {
        history: [],
        daily_summary: { calories: 0, protein: 0, fat: 0 }
      };
    }
  }

  /**
   * Clear all data (for testing)
   */
  async clearAllData(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.STORAGE_KEY);
      await AsyncStorage.removeItem(this.RESET_KEY);
      console.log('[LocalNutrition] All data cleared');
    } catch (error) {
      console.error('[LocalNutrition] Error clearing data:', error);
    }
  }
}

export default LocalNutritionManager;
