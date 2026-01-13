import { useSafeAreaInsets } from 'react-native-safe-area-context';

/**
 * Screen-specific spacing presets (kept for compatibility, but not used)
 */
export const SPACING_PRESETS = {
  PRIMARY: 0,       // Dashboard, Recipes, etc.
  SECONDARY: 0,     // Settings, Details
  FULLSCREEN: 0,    // Chatbot, Messages
  MODAL: 0,         // Modals, Overlays
} as const;

/**
 * Get standardized top spacing for screens
 * Formula: Half of Safe Area Top (reduced padding)
 * 
 * @param preset - Spacing preset (kept for compatibility, but not used)
 * @returns Half of safe area top inset
 */
export const useStandardTopSpacing = (preset: number = SPACING_PRESETS.PRIMARY): number => {
  const insets = useSafeAreaInsets();
  // Return half of safe area top - reduced padding
  return Math.round(insets.top / 2);
};
