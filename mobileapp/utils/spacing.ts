import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Dimensions } from 'react-native';

/**
 * Screen-specific spacing presets
 */
export const SPACING_PRESETS = {
  PRIMARY: 20,      // Dashboard, Recipes, etc.
  SECONDARY: 20,    // Settings, Details
  FULLSCREEN: 16,   // Chatbot, Messages (more content)
  MODAL: 24,        // Modals, Overlays (more generous)
} as const;

/**
 * Get base padding based on screen size
 */
const getBasePadding = (preset: number = SPACING_PRESETS.PRIMARY): number => {
  const screenHeight = Dimensions.get('window').height;
  
  // Adjust base padding slightly for different screen sizes
  if (screenHeight < 700) return preset - 4; // Small phones: slightly less
  if (screenHeight < 900) return preset; // Standard phones: use preset
  if (screenHeight < 1100) return preset + 4; // Large phones: slightly more
  return preset + 4; // Tablets: slightly more
};

/**
 * Get standardized top spacing for screens
 * Formula: Safe Area Top + Base Padding
 * 
 * @param preset - Spacing preset (PRIMARY, SECONDARY, FULLSCREEN, MODAL)
 * @returns Total top spacing value
 */
export const useStandardTopSpacing = (preset: number = SPACING_PRESETS.PRIMARY): number => {
  const insets = useSafeAreaInsets();
  const basePadding = getBasePadding(preset);
  return insets.top + basePadding;
};
