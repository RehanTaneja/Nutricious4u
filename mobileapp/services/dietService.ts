import { Alert, Linking } from 'react-native';
import { getUserDiet } from './api';
import { auth } from '../services/firebase';
import { API_URL } from '@env';

/**
 * Shared Diet Service
 * Provides consistent diet opening functionality for both My Diet button and notifications
 */
export class DietService {
  /**
   * Opens the user's diet PDF using the same logic as the My Diet button
   * @param isFreeUser - Whether the user is on a free plan
   * @param setShowUpgradeModal - Function to show upgrade modal (optional)
   * @param setDietPdfUrl - Function to update diet PDF URL state (optional)
   */
  static async openDiet(
    isFreeUser: boolean = false,
    setShowUpgradeModal?: (show: boolean) => void,
    setDietPdfUrl?: (url: string | null) => void
  ): Promise<void> {
    console.log('[DietService] openDiet called, isFreeUser:', isFreeUser);
    
    // Check if user is on free plan
    if (isFreeUser) {
      console.log('[DietService] Showing upgrade modal for free user');
      if (setShowUpgradeModal) {
        setShowUpgradeModal(true);
      } else {
        Alert.alert('Upgrade Required', 'Please upgrade to access your diet plan.');
      }
      return;
    }
    
    try {
      // Get current user
      const userId = auth.currentUser?.uid;
      if (!userId) {
        Alert.alert('Error', 'User not authenticated. Please log in again.');
        return;
      }
      
      // Force refresh diet data before opening
      console.log('[DietService] Refreshing diet data before opening PDF...');
      const dietData = await getUserDiet(userId);
      console.log('[DietService] Refreshed diet data:', dietData);
      
      // Update local state if setter provided
      if (setDietPdfUrl) {
        setDietPdfUrl(dietData.dietPdfUrl || null);
      }
      
      if (dietData.dietPdfUrl) {
        console.log('[DietService] Opening diet PDF with URL:', dietData.dietPdfUrl);
        
        // Generate PDF URL with cache busting
        const pdfUrl = DietService.getPdfUrlWithCacheBusting(dietData.dietPdfUrl);
        console.log('[DietService] Final PDF URL for browser:', pdfUrl);
        
        if (pdfUrl) {
          // Open PDF in browser
          const canOpen = await Linking.canOpenURL(pdfUrl);
          if (canOpen) {
            await Linking.openURL(pdfUrl);
            console.log('[DietService] PDF opened in browser successfully');
          } else {
            console.log('[DietService] Cannot open URL:', pdfUrl);
            Alert.alert('Error', 'Cannot open PDF. Please try again.');
          }
        } else {
          Alert.alert('Error', 'No PDF URL available.');
        }
      } else {
        Alert.alert('No Diet Available', 'You don\'t have a diet plan yet. Please contact your dietician.');
      }
    } catch (e) {
      console.error('[DietService] Failed to open diet PDF:', e);
      Alert.alert('Error', 'Failed to open diet PDF. Please try again.');
    }
  }

  /**
   * Helper function to get the correct PDF URL with cache busting
   * @param pdfUrl - The original PDF URL
   * @returns Processed PDF URL with cache busting
   */
  static getPdfUrlWithCacheBusting(pdfUrl: string): string | null {
    if (!pdfUrl) return null;
    
    console.log('[DietService] getPdfUrlWithCacheBusting called with pdfUrl:', pdfUrl);
    
    // If it's a Firebase Storage signed URL, use it directly
    if (pdfUrl.startsWith('https://storage.googleapis.com/')) {
      console.log('[DietService] Using Firebase Storage URL directly:', pdfUrl);
      return pdfUrl;
    }
    
    // If it's a firestore:// URL, use the backend endpoint
    if (pdfUrl.startsWith('firestore://')) {
      const userId = auth.currentUser?.uid;
      const url = `${API_URL}/users/${userId}/diet/pdf`;
      console.log('[DietService] Using backend endpoint for firestore URL:', url);
      return url;
    }
    
    // If it's just a filename or any other format, use the backend endpoint with cache busting
    const userId = auth.currentUser?.uid;
    const timestamp = Date.now(); // Add cache busting parameter
    const url = `${API_URL}/users/${userId}/diet/pdf?t=${timestamp}`;
    console.log('[DietService] Using backend endpoint for filename with cache busting:', url);
    return url;
  }
}
