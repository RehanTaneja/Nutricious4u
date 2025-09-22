/**
 * Gemini Nutrition Service
 * Handles nutrition data extraction using Gemini API with prompt engineering
 * Returns three comma-separated values: calories, protein, fat
 */

const GEMINI_API_KEY = 'AIzaSyBqJqJqJqJqJqJqJqJqJqJqJqJqJqJqJqJ'; // Replace with actual API key

interface NutritionResponse {
  calories: number;
  protein: number;
  fat: number;
  success: boolean;
  error?: string;
}

class GeminiNutritionService {
  private static instance: GeminiNutritionService;

  private constructor() {}

  public static getInstance(): GeminiNutritionService {
    if (!GeminiNutritionService.instance) {
      GeminiNutritionService.instance = new GeminiNutritionService();
    }
    return GeminiNutritionService.instance;
  }

  /**
   * Get nutrition data from Gemini API
   * @param foodName - Name of the food item
   * @param quantity - Quantity/serving size
   * @returns Promise with calories, protein, fat
   */
  public async getNutritionData(foodName: string, quantity: string): Promise<NutritionResponse> {
    try {
      console.log(`[GeminiNutrition] Getting nutrition for: ${foodName}, ${quantity}`);
      
      // Create the prompt for Gemini
      const prompt = this.createNutritionPrompt(foodName, quantity);
      
      // Call Gemini API
      const response = await this.callGeminiAPI(prompt);
      
      // Parse the response
      const nutrition = this.parseGeminiResponse(response);
      
      console.log(`[GeminiNutrition] Success: ${nutrition.calories} cal, ${nutrition.protein}g protein, ${nutrition.fat}g fat`);
      
      return nutrition;
    } catch (error) {
      console.error('[GeminiNutrition] Error:', error);
      return {
        calories: 0,
        protein: 0,
        fat: 0,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Create the prompt for Gemini API
   */
  private createNutritionPrompt(foodName: string, quantity: string): string {
    return `You are a nutrition expert. For the food item "${foodName}" with quantity "${quantity}", provide exactly 3 comma-separated numbers representing:
1. Total calories
2. Total protein in grams
3. Total fat in grams

Format: calories,protein,fat
Example: 150,12,8

Only return the 3 numbers separated by commas. No other text, explanations, or formatting.`;
  }

  /**
   * Call Gemini API
   */
  private async callGeminiAPI(prompt: string): Promise<string> {
    try {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: prompt
            }]
          }]
        })
      });

      if (!response.ok) {
        throw new Error(`Gemini API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
        throw new Error('Invalid response from Gemini API');
      }

      return data.candidates[0].content.parts[0].text.trim();
    } catch (error) {
      console.error('[GeminiNutrition] API call failed:', error);
      throw error;
    }
  }

  /**
   * Parse Gemini response to extract nutrition values
   */
  private parseGeminiResponse(response: string): NutritionResponse {
    try {
      // Clean the response
      const cleanResponse = response.replace(/[^\d,.-]/g, '').trim();
      
      // Split by comma
      const parts = cleanResponse.split(',');
      
      if (parts.length !== 3) {
        throw new Error(`Expected 3 values, got ${parts.length}: ${response}`);
      }
      
      // Parse each value
      const calories = parseFloat(parts[0].trim());
      const protein = parseFloat(parts[1].trim());
      const fat = parseFloat(parts[2].trim());
      
      // Validate values
      if (isNaN(calories) || isNaN(protein) || isNaN(fat)) {
        throw new Error(`Invalid numeric values: ${response}`);
      }
      
      if (calories < 0 || protein < 0 || fat < 0) {
        throw new Error(`Negative values not allowed: ${response}`);
      }
      
      return {
        calories: Math.round(calories * 100) / 100, // Round to 2 decimal places
        protein: Math.round(protein * 100) / 100,
        fat: Math.round(fat * 100) / 100,
        success: true
      };
    } catch (error) {
      console.error('[GeminiNutrition] Parse error:', error);
      return {
        calories: 0,
        protein: 0,
        fat: 0,
        success: false,
        error: `Failed to parse response: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Get workout calories from Gemini API
   */
  public async getWorkoutCalories(workoutName: string, duration: string): Promise<{ calories: number; success: boolean; error?: string }> {
    try {
      console.log(`[GeminiNutrition] Getting workout calories for: ${workoutName}, ${duration} minutes`);
      
      const prompt = `You are a fitness expert. For the workout "${workoutName}" with duration "${duration} minutes", provide exactly 1 number representing the total calories burned.

Only return the number. No other text, explanations, or formatting.`;
      
      const response = await this.callGeminiAPI(prompt);
      const calories = parseFloat(response.replace(/[^\d.-]/g, ''));
      
      if (isNaN(calories) || calories < 0) {
        throw new Error(`Invalid calories value: ${response}`);
      }
      
      console.log(`[GeminiNutrition] Workout calories: ${calories}`);
      
      return {
        calories: Math.round(calories),
        success: true
      };
    } catch (error) {
      console.error('[GeminiNutrition] Workout calories error:', error);
      return {
        calories: 0,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

export default GeminiNutritionService;
