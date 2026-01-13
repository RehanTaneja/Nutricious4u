import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Dimensions } from 'react-native';

/**
 * Screen-specific spacing presets
 * REDUCED values to provide less padding than original (50px, 60px, 32px)
 */
export const SPACING_PRESETS = {
  PRIMARY: 4,       // Dashboard, Recipes, etc. (reduced - was 50px, now ~48px on iPhone X)
  SECONDARY: 4,     // Settings, Details (reduced - was 32px, now ~36px on iPhone X)
  FULLSCREEN: 2,    // Chatbot, Messages (reduced - was 60px, now ~46px on iPhone X)
  MODAL: 8,         // Modals, Overlays
} as const;

/**
 * Get base padding based on screen size
 */
const getBasePadding = (preset: number = SPACING_PRESETS.PRIMARY): number => {
  const screenHeight = Dimensions.get('window').height;
  
  // Use minimal padding for all screen sizes
  if (screenHeight < 700) return preset; // Small phones
  if (screenHeight < 900) return preset; // Standard phones
  if (screenHeight < 1100) return preset + 1; // Large phones: slightly more
  return preset + 1; // Tablets: slightly more
};

/**
 * Get standardized top spacing for screens
 * Formula: Safe Area Top + Base Padding (REDUCED)
 * 
 * @param preset - Spacing preset (PRIMARY, SECONDARY, FULLSCREEN, MODAL)
 * @returns Total top spacing value (reduced compared to original)
 */
export const useStandardTopSpacing = (preset: number = SPACING_PRESETS.PRIMARY): number => {
  const insets = useSafeAreaInsets();
  const basePadding = getBasePadding(preset);
  return insets.top + basePadding;
};
