/**
 * Push Notification Service
 * Pure push notification logic - no Firebase dependencies
 * Handles device checks, permissions, and token retrieval
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { logFrontendEvent } from './api';
import { logger } from '../utils/logger';

export interface PushTokenResult {
  token: string | null;
  error: Error | null;
  permissionStatus: string;
  deviceSupported: boolean;
}

/**
 * Check if device supports push notifications
 */
export function isDeviceSupported(): boolean {
  const supported = Device.isDevice;
  console.log(`[PUSH SERVICE] Device check: ${supported ? 'Physical device' : 'Simulator/Emulator'}`);
  return supported;
}

/**
 * Request notification permissions
 */
export async function requestNotificationPermissions(): Promise<{
  status: string;
  granted: boolean;
}> {
  console.log('[PUSH SERVICE] Step 1: Checking existing notification permissions...');
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  console.log(`[PUSH SERVICE] ✓ Existing permission status: ${existingStatus}`);
  
  let finalStatus = existingStatus;
  
  if (existingStatus !== 'granted') {
    console.log('[PUSH SERVICE] Step 2: Permission not granted, requesting...');
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
    console.log(`[PUSH SERVICE] ✓ Permission request result: ${finalStatus}`);
  } else {
    console.log('[PUSH SERVICE] Step 2: Permission already granted, skipping request');
  }
  
  return {
    status: finalStatus,
    granted: finalStatus === 'granted'
  };
}

/**
 * Get Expo push token with comprehensive logging
 */
export async function getExpoPushToken(projectId: string, userId: string): Promise<{
  token: string | null;
  error: Error | null;
}> {
  console.log('[PUSH SERVICE] Step 3: Getting Expo push token...');
  console.log(`[PUSH SERVICE] Platform: ${Platform.OS}`);
  console.log(`[PUSH SERVICE] Project ID: ${projectId}`);
  
  try {
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId: projectId
    });
    
    // Enhanced logging - visible in backend logs
    console.log('[PUSH SERVICE] Raw tokenData:', JSON.stringify(tokenData));
    console.log('[PUSH SERVICE] Type of data:', typeof tokenData.data);
    console.log('[PUSH SERVICE] Data length:', tokenData.data?.length);
    console.log('[PUSH SERVICE] Data value:', tokenData.data);
    
    // Log to backend for visibility
    if (!__DEV__ && userId !== 'unknown') {
      try {
        await logFrontendEvent(userId, 'PUSH_TOKEN_DATA_RECEIVED', {
          platform: Platform.OS,
          projectId: projectId,
          tokenDataType: typeof tokenData.data,
          tokenDataLength: tokenData.data?.length,
          tokenDataValue: tokenData.data ? (tokenData.data.substring(0, 50) + (tokenData.data.length > 50 ? '...' : '')) : null,
          tokenDataIsEmpty: tokenData.data === '' || (typeof tokenData.data === 'string' && tokenData.data.trim() === ''),
          rawTokenData: JSON.stringify(tokenData)
        });
      } catch (logErr) {
        console.warn('[PUSH SERVICE] Failed to log tokenData to backend:', logErr);
      }
    }
    
    const token = tokenData.data;
    
    // Validate token is not empty
    if (!token || (typeof token === 'string' && token.trim() === '')) {
      console.log('[PUSH SERVICE] ❌ Token is empty - tokenData:', JSON.stringify(tokenData));
      console.log('[PUSH SERVICE] ❌ Token validation failed: empty string or null');
      
      // Log to backend for visibility
      if (!__DEV__ && userId !== 'unknown') {
        try {
          await logFrontendEvent(userId, 'PUSH_TOKEN_VALIDATION_FAILED', {
            platform: Platform.OS,
            projectId: projectId,
            reason: 'empty_string_or_null',
            tokenDataType: typeof tokenData.data,
            tokenDataLength: tokenData.data?.length,
            tokenDataValue: tokenData.data,
            rawTokenData: JSON.stringify(tokenData)
          });
        } catch (logErr) {
          console.warn('[PUSH SERVICE] Failed to log validation failure to backend:', logErr);
        }
      }
      
      return { token: null, error: new Error('Token is empty or null') };
    }
    
    console.log(`[PUSH SERVICE] ✓ Token received successfully`);
    console.log(`[PUSH SERVICE] Token preview: ${token.substring(0, 30)}...`);
    console.log(`[PUSH SERVICE] Token length: ${token.length}`);
    console.log(`[PUSH SERVICE] Token type: ${typeof token}`);
    console.log(`[PUSH SERVICE] Token starts with 'ExponentPushToken': ${token.startsWith('ExponentPushToken')}`);
    
    // Log successful token to backend
    if (!__DEV__ && userId !== 'unknown') {
      try {
        await logFrontendEvent(userId, 'PUSH_TOKEN_VALIDATION_SUCCESS', {
          platform: Platform.OS,
          projectId: projectId,
          tokenLength: token.length,
          tokenPreview: token.substring(0, 30) + '...',
          tokenStartsWithExponent: token.startsWith('ExponentPushToken')
        });
      } catch (logErr) {
        console.warn('[PUSH SERVICE] Failed to log success to backend:', logErr);
      }
    }
    
    return { token, error: null };
  } catch (tokenError: any) {
    console.log('[PUSH SERVICE] ❌ FAILED to get Expo push token');
    console.error('[PUSH SERVICE] Token error:', tokenError);
    console.log('═══════════════════════════════════════════════════════════════');
    
    // Log error to backend for visibility
    if (!__DEV__ && userId !== 'unknown') {
      try {
        await logFrontendEvent(userId, 'PUSH_TOKEN_ERROR', {
          platform: Platform.OS,
          projectId: projectId,
          errorMessage: String(tokenError),
          errorType: tokenError?.constructor?.name || 'Unknown'
        });
      } catch (logErr) {
        console.warn('[PUSH SERVICE] Failed to log error to backend:', logErr);
      }
    }
    
    return { token: null, error: tokenError };
  }
}

/**
 * Main function: Request push token with full flow
 * Includes device check, permissions, and token retrieval
 */
export async function requestPushToken(userId: string): Promise<PushTokenResult> {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('🔔 [PUSH TOKEN REGISTRATION] START');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`[PUSH SERVICE] Time: ${new Date().toISOString()}`);
  console.log(`[PUSH SERVICE] Platform: ${Platform.OS}`);
  console.log(`[PUSH SERVICE] User ID: ${userId || 'None'}`);
  
  // Step 1: Check if device is supported
  const deviceSupported = isDeviceSupported();
  if (!deviceSupported) {
    console.log('[PUSH SERVICE] ❌ FAILED: Push notifications require a physical device');
    console.log('═══════════════════════════════════════════════════════════════');
    logger.log('Push notifications are not supported on simulators/emulators');
    return {
      token: null,
      error: new Error('Push notifications require a physical device'),
      permissionStatus: 'unsupported',
      deviceSupported: false
    };
  }
  
  // Step 2: Get project ID
  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  if (!projectId) {
    console.log('[PUSH SERVICE] ❌ Missing Expo project ID, cannot request push token');
    console.log('═══════════════════════════════════════════════════════════════');
    return {
      token: null,
      error: new Error('Missing Expo project ID'),
      permissionStatus: 'unknown',
      deviceSupported: true
    };
  }
  
  console.log(`[PUSH SERVICE] Project ID: ${projectId}`);
  
  // Step 3: Request permissions
  const permissionResult = await requestNotificationPermissions();
  
  if (!permissionResult.granted) {
    console.log('[PUSH SERVICE] ❌ FAILED: Notification permission not granted');
    console.log(`[PUSH SERVICE] Final status: ${permissionResult.status}`);
    console.log('═══════════════════════════════════════════════════════════════');
    logger.log('Failed to get push token for push notification!');
    return {
      token: null,
      error: new Error(`Notification permission not granted: ${permissionResult.status}`),
      permissionStatus: permissionResult.status,
      deviceSupported: true
    };
  }
  
  console.log('[PUSH SERVICE] ✓ Permission granted successfully');
  
  // Step 4: Get Expo push token
  const tokenResult = await getExpoPushToken(projectId, userId);
  
  if (tokenResult.error) {
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('🔔 [PUSH TOKEN REGISTRATION] FAILED');
    console.log('═══════════════════════════════════════════════════════════════');
    return {
      token: null,
      error: tokenResult.error,
      permissionStatus: permissionResult.status,
      deviceSupported: true
    };
  }
  
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('🔔 [PUSH TOKEN REGISTRATION] TOKEN RETRIEVED');
  console.log('═══════════════════════════════════════════════════════════════');
  
  return {
    token: tokenResult.token,
    error: null,
    permissionStatus: permissionResult.status,
    deviceSupported: true
  };
}

