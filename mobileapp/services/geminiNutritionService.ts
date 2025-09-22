/**
 * Gemini Nutrition Service
 * Uses Gemini API to get nutrition data for food items
 */

import { API_URL } from './api';

export interface NutritionResponse {
  success: boolean;
  calories: number;
  protein: number;
  fat: number;
  error?: string;
}

class GeminiNutritionService {
  private static instance: GeminiNutritionService;

  private constructor() {}

  static getInstance(): GeminiNutritionService {
    if (!GeminiNutritionService.instance) {
      GeminiNutritionService.instance = new GeminiNutritionService();
    }
    return GeminiNutritionService.instance;
  }

  /**
   * Get nutrition data from Gemini API
   */
  async getNutritionData(foodName: string, quantity: string): Promise<NutritionResponse> {
    try {
      console.log('[GeminiNutrition] Getting nutrition data for:', { foodName, quantity });
      
      const response = await fetch(`${API_URL}/gemini/nutrition`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          foodName: foodName.trim(),
          servingSize: quantity.trim()
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[GeminiNutrition] API response:', data);

      // Extract nutrition values from response
      const nutrition = data.food || data;
      
      return {
        success: true,
        calories: parseFloat(nutrition.calories) || 0,
        protein: parseFloat(nutrition.protein) || 0,
        fat: parseFloat(nutrition.fat) || 0
      };
    } catch (error) {
      console.error('[GeminiNutrition] Error getting nutrition data:', error);
      return {
        success: false,
        calories: 0,
        protein: 0,
        fat: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get workout calories from Gemini API
   */
  async getWorkoutCalories(exerciseName: string, duration: string): Promise<{success: boolean, calories: number, error?: string}> {
    try {
      console.log('[GeminiNutrition] Getting workout calories for:', { exerciseName, duration });
      
      const response = await fetch(`${API_URL}/gemini/workout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          exerciseName: exerciseName.trim(),
          duration: duration.trim()
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[GeminiNutrition] Workout API response:', data);

      return {
        success: true,
        calories: parseFloat(data.calories) || 0
      };
    } catch (error) {
      console.error('[GeminiNutrition] Error getting workout calories:', error);
      return {
        success: false,
        calories: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

export default GeminiNutritionService;
