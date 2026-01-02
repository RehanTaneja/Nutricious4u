/**
 * Push Token Manager
 * Orchestrates push token registration and Firestore save
 * Maintains all existing logging and error handling
 */

import { Platform } from 'react-native';
import { requestPushToken } from './pushNotificationService';
import { auth, firestore } from './firebase';
import firebase from './firebase';
import { logger } from '../utils/logger';

/**
 * Register push token and save to Firestore
 * Maintains exact same logging and behavior as original implementation
 */
export async function registerAndSavePushToken(userId?: string): Promise<string | null> {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('🔔 [PUSH TOKEN MANAGER] START');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`[PUSH TOKEN MANAGER] Time: ${new Date().toISOString()}`);
  console.log(`[PUSH TOKEN MANAGER] Platform: ${Platform.OS}`);
  console.log(`[PUSH TOKEN MANAGER] User ID provided: ${userId || 'None'}`);
  console.log(`[PUSH TOKEN MANAGER] Current user: ${auth.currentUser?.uid || 'None'}`);
  console.log(`[PUSH TOKEN MANAGER] Current user email: ${auth.currentUser?.email || 'None'}`);
  
  // Get user ID for logging
  const currentUserId = userId || auth.currentUser?.uid || 'unknown';
  
  // Step 1: Request push token
  const tokenResult = await requestPushToken(currentUserId);
  
  if (tokenResult.error || !tokenResult.token) {
    console.log('[PUSH TOKEN MANAGER] ❌ FAILED: Could not retrieve push token');
    console.log(`[PUSH TOKEN MANAGER] Error: ${tokenResult.error?.message || 'Unknown error'}`);
    console.log('═══════════════════════════════════════════════════════════════');
    logger.log('Failed to get push token:', tokenResult.error);
    return null;
  }
  
  const token = tokenResult.token;
  console.log('[PUSH TOKEN MANAGER] ✓ Token retrieved successfully');
  
  // Step 2: Save token to Firestore
  console.log('[PUSH TOKEN MANAGER] Step 4: Saving token to Firestore...');
  try {
    // Use provided userId or get from auth
    const user = userId ? { uid: userId } : auth.currentUser;
    console.log(`[PUSH TOKEN MANAGER] User for saving: ${user?.uid || 'None'}`);
    
    // CRITICAL FIX: Force refresh ID token to ensure Firestore has valid auth
    // This resolves the timing issue where Firestore's auth context may not be
    // synchronized with Firebase Auth immediately after onAuthStateChanged fires
    if (auth.currentUser) {
      console.log('[PUSH TOKEN MANAGER] Refreshing ID token for Firestore auth...');
      try {
        await auth.currentUser.getIdToken(true);
        console.log('[PUSH TOKEN MANAGER] ✓ ID token refreshed successfully');
      } catch (tokenRefreshError) {
        console.error('[PUSH TOKEN MANAGER] ⚠️ ID token refresh failed:', tokenRefreshError);
        // Continue anyway - the existing token might still work
      }
    }
    
    if (!user) {
      console.log('[PUSH TOKEN MANAGER] ❌ FAILED: No user available for saving token');
      console.log('═══════════════════════════════════════════════════════════════');
      return null; // Return null to signal failure - token wasn't saved!
    }
    
    if (!token) {
      console.log('[PUSH TOKEN MANAGER] ❌ FAILED: No token available for saving');
      console.log('═══════════════════════════════════════════════════════════════');
      return null;
    }
    
    const saveData = { 
      expoPushToken: token,
      platform: Platform.OS,
      lastTokenUpdate: new Date().toISOString()
    };
    
    console.log(`[PUSH TOKEN MANAGER] Saving to: user_profiles/${user.uid}`);
    console.log(`[PUSH TOKEN MANAGER] Save data:`, JSON.stringify(saveData, null, 2));
    
    await firebase.firestore().collection('user_profiles').doc(user.uid).set(saveData, { merge: true });
    
    console.log('[PUSH TOKEN MANAGER] ✓ Token saved successfully to Firestore');
    console.log(`[PUSH TOKEN MANAGER] ✓ Token saved for user: ${user.uid}`);
    
    // Verify save was successful
    console.log('[PUSH TOKEN MANAGER] Step 5: Verifying token was saved...');
    const doc = await firebase.firestore().collection('user_profiles').doc(user.uid).get();
    const savedData = doc.data();
    const savedToken = savedData?.expoPushToken;
    
    if (savedToken === token) {
      console.log('[PUSH TOKEN MANAGER] ✓✓✓ VERIFICATION SUCCESS: Token matches saved token');
      console.log(`[PUSH TOKEN MANAGER] Saved token preview: ${savedToken.substring(0, 30)}...`);
    } else {
      console.log('[PUSH TOKEN MANAGER] ❌ VERIFICATION FAILED: Saved token does not match');
      console.log(`[PUSH TOKEN MANAGER] Expected: ${token.substring(0, 30)}...`);
      console.log(`[PUSH TOKEN MANAGER] Got: ${savedToken ? savedToken.substring(0, 30) + '...' : 'None'}`);
    }
    
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('🔔 [PUSH TOKEN MANAGER] SUCCESS');
    console.log('═══════════════════════════════════════════════════════════════');
    
    logger.log('Saved expoPushToken to Firestore with platform info');
    logger.log(`Token saved for user: ${user.uid}`);
    
    return token;
  } catch (error: any) {
    console.log('[PUSH TOKEN MANAGER] ❌ FAILED to save push token to Firestore');
    console.error('[PUSH TOKEN MANAGER] Save error code:', error?.code);
    console.error('[PUSH TOKEN MANAGER] Save error message:', error?.message);
    console.error('[PUSH TOKEN MANAGER] Full error:', error);
    console.log('═══════════════════════════════════════════════════════════════');
    logger.log('Failed to save push token to Firestore:', error);
    logger.log('Error code:', error?.code, 'Error message:', error?.message);
    return null; // Return null so caller knows save failed and retry can happen
  }
}

