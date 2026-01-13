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
 * Formula: Safe Area Top Only (no additional padding)
 * 
 * @param preset - Spacing preset (kept for compatibility, but not used)
 * @returns Safe area top inset only
 */
export const useStandardTopSpacing = (preset: number = SPACING_PRESETS.PRIMARY): number => {
  const insets = useSafeAreaInsets();
  // Return only safe area top - no additional padding
  return insets.top;
};
