/**
 * Unified Nutrition Data Manager
 * Manages 7-day rolling window of nutrition data with automatic midnight reset
 * Replaces complex backend system with simple, reliable local storage
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

// Data structure for each day's nutrition
export interface DayNutrition {
  date: string; // YYYY-MM-DD format
  calories: number;
  protein: number;
  fat: number;
  burned: number; // calories burned from workouts
}

// 7-day rolling window data structure
export interface WeeklyNutritionData {
  days: DayNutrition[];
  lastResetDate: string;
}

const NUTRITION_DATA_KEY = 'weekly_nutrition_data';
const WORKOUT_DATA_KEY = 'weekly_workout_data';

class NutritionDataManager {
  private static instance: NutritionDataManager;
  private weeklyData: WeeklyNutritionData | null = null;

  private constructor() {}

  public static getInstance(): NutritionDataManager {
    if (!NutritionDataManager.instance) {
      NutritionDataManager.instance = new NutritionDataManager();
    }
    return NutritionDataManager.instance;
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
   * Generate 7 days of data (6 days ago to today)
   */
  private generate7Days(): DayNutrition[] {
    const days: DayNutrition[] = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const dateStr = `${year}-${month}-${day}`;
      
      days.push({
        date: dateStr,
        calories: 0,
        protein: 0,
        fat: 0,
        burned: 0
      });
    }
    
    return days;
  }

  /**
   * Initialize or load weekly data
   */
  private async initializeData(): Promise<WeeklyNutritionData> {
    try {
      const stored = await AsyncStorage.getItem(NUTRITION_DATA_KEY);
      if (stored) {
        const data: WeeklyNutritionData = JSON.parse(stored);
        const today = this.getTodayDate();
        
        // Check if we need to reset (new day)
        if (data.lastResetDate !== today) {
          console.log('[NutritionDataManager] New day detected, resetting data');
          return this.resetForNewDay(data, today);
        }
        
        // Ensure we have exactly 7 days
        if (data.days.length !== 7) {
          console.log('[NutritionDataManager] Invalid data length, regenerating');
          return this.resetForNewDay(data, today);
        }
        
        return data;
      } else {
        console.log('[NutritionDataManager] No stored data, initializing new');
        return this.createNewData();
      }
    } catch (error) {
      console.error('[NutritionDataManager] Error loading data:', error);
      return this.createNewData();
    }
  }

  /**
   * Create new weekly data
   */
  private createNewData(): WeeklyNutritionData {
    const today = this.getTodayDate();
    return {
      days: this.generate7Days(),
      lastResetDate: today
    };
  }

  /**
   * Reset data for new day (shift left, add new day)
   */
  private resetForNewDay(oldData: WeeklyNutritionData, today: string): WeeklyNutritionData {
    const newDays = [...oldData.days];
    
    // Remove leftmost day (oldest)
    newDays.shift();
    
    // Add new day at the end (today)
    newDays.push({
      date: today,
      calories: 0,
      protein: 0,
      fat: 0,
      burned: 0
    });
    
    return {
      days: newDays,
      lastResetDate: today
    };
  }

  /**
   * Save data to storage
   */
  private async saveData(data: WeeklyNutritionData): Promise<void> {
    try {
      await AsyncStorage.setItem(NUTRITION_DATA_KEY, JSON.stringify(data));
      this.weeklyData = data;
      console.log('[NutritionDataManager] Data saved successfully');
    } catch (error) {
      console.error('[NutritionDataManager] Error saving data:', error);
    }
  }

  /**
   * Get current weekly data
   */
  public async getWeeklyData(): Promise<WeeklyNutritionData> {
    if (!this.weeklyData) {
      this.weeklyData = await this.initializeData();
    }
    return this.weeklyData;
  }

  /**
   * Get today's nutrition data
   */
  public async getTodayData(): Promise<DayNutrition> {
    const data = await this.getWeeklyData();
    const today = this.getTodayDate();
    
    const todayData = data.days.find(day => day.date === today);
    if (todayData) {
      return todayData;
    }
    
    // Fallback - should not happen
    return {
      date: today,
      calories: 0,
      protein: 0,
      fat: 0,
      burned: 0
    };
  }

  /**
   * Add food nutrition to today's data
   */
  public async addFoodNutrition(calories: number, protein: number, fat: number): Promise<void> {
    const data = await this.getWeeklyData();
    const today = this.getTodayDate();
    
    const todayIndex = data.days.findIndex(day => day.date === today);
    if (todayIndex !== -1) {
      data.days[todayIndex].calories += calories;
      data.days[todayIndex].protein += protein;
      data.days[todayIndex].fat += fat;
      
      await this.saveData(data);
      console.log(`[NutritionDataManager] Added food: ${calories} cal, ${protein}g protein, ${fat}g fat`);
    }
  }

  /**
   * Add workout calories to today's data
   */
  public async addWorkoutCalories(calories: number): Promise<void> {
    const data = await this.getWeeklyData();
    const today = this.getTodayDate();
    
    const todayIndex = data.days.findIndex(day => day.date === today);
    if (todayIndex !== -1) {
      data.days[todayIndex].burned += calories;
      
      await this.saveData(data);
      console.log(`[NutritionDataManager] Added workout: ${calories} calories burned`);
    }
  }

  /**
   * Get data for bar graph (7 days in chronological order)
   */
  public async getBarGraphData(): Promise<DayNutrition[]> {
    const data = await this.getWeeklyData();
    return data.days; // Already in chronological order
  }

  /**
   * Get data for trackers (today's data)
   */
  public async getTrackerData(): Promise<DayNutrition> {
    return await this.getTodayData();
  }

  /**
   * Reset all data (for testing or manual reset)
   */
  public async resetAllData(): Promise<void> {
    const newData = this.createNewData();
    await this.saveData(newData);
    console.log('[NutritionDataManager] All data reset');
  }

  /**
   * Get summary data for display
   */
  public async getSummaryData(): Promise<{
    today: DayNutrition;
    weekly: DayNutrition[];
    totalCalories: number;
    totalProtein: number;
    totalFat: number;
    totalBurned: number;
  }> {
    const data = await this.getWeeklyData();
    const today = await this.getTodayData();
    
    const totalCalories = data.days.reduce((sum, day) => sum + day.calories, 0);
    const totalProtein = data.days.reduce((sum, day) => sum + day.protein, 0);
    const totalFat = data.days.reduce((sum, day) => sum + day.fat, 0);
    const totalBurned = data.days.reduce((sum, day) => sum + day.burned, 0);
    
    return {
      today,
      weekly: data.days,
      totalCalories,
      totalProtein,
      totalFat,
      totalBurned
    };
  }

  /**
   * Check if it's a new day and reset if needed
   */
  public async checkAndResetIfNewDay(): Promise<boolean> {
    const data = await this.getWeeklyData();
    const today = this.getTodayDate();
    
    if (data.lastResetDate !== today) {
      console.log('[NutritionDataManager] New day detected, performing reset');
      const newData = this.resetForNewDay(data, today);
      await this.saveData(newData);
      return true; // Reset occurred
    }
    
    return false; // No reset needed
  }
}

export default NutritionDataManager;
