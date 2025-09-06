import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { auth } from './firebase';
import { logger } from '../utils/logger';

// Note: Notification handler is already configured in firebase.ts
// This prevents conflicts and ensures iOS compatibility

export interface UnifiedNotification {
  id: string;
  title: string;
  body: string;
  type: 'custom' | 'diet' | 'new_diet' | 'message' | 'diet_reminder' | 'subscription';
  data?: any;
  scheduledFor?: Date;
  repeats?: boolean;
  repeatInterval?: number; // in seconds
}

export class UnifiedNotificationService {
  private static instance: UnifiedNotificationService;
  private isInitialized = false;
  private notificationDeduplication: Set<string> = new Set(); // Track processed notifications
  private lastNotificationTime: Map<string, number> = new Map(); // Track last notification time per message

  private constructor() {
    // No dependencies to prevent circular imports and EAS build issues
  }

  public static getInstance(): UnifiedNotificationService {
    if (!UnifiedNotificationService.instance) {
      UnifiedNotificationService.instance = new UnifiedNotificationService();
    }
    return UnifiedNotificationService.instance;
  }

  // CRITICAL FIX: Initialize permissions for EAS builds
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Request permissions - CRITICAL for EAS builds
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        throw new Error('Notification permissions not granted');
      }

      this.isInitialized = true;
      logger.log('[UnifiedNotificationService] Initialized successfully with permissions');
    } catch (error) {
      logger.error('[UnifiedNotificationService] Initialization failed:', error);
      throw error;
    }
  }

  // CRITICAL FIX: Add deduplication to prevent random repeats
  private isDuplicateNotification(notification: UnifiedNotification): boolean {
    const notificationKey = `${notification.data?.message}_${notification.data?.time}_${notification.data?.userId}`;
    const now = Date.now();
    const lastTime = this.lastNotificationTime.get(notificationKey) || 0;
    
    // If same notification was processed within last 5 minutes, consider it duplicate
    if (now - lastTime < 5 * 60 * 1000) {
      console.log('[NOTIFICATION DEBUG] Duplicate notification detected:', notificationKey);
      return true;
    }
    
    this.lastNotificationTime.set(notificationKey, now);
    return false;
  }

  // Schedule a notification locally (works in EAS builds)
  async scheduleNotification(notification: UnifiedNotification): Promise<string> {
    try {
      // CRITICAL FIX: Check for duplicates before scheduling
      if (this.isDuplicateNotification(notification)) {
        console.log('[NOTIFICATION DEBUG] Skipping duplicate notification');
        return 'duplicate_skipped';
      }
      
      // CRITICAL FIX: Ensure permissions are initialized
      if (!this.isInitialized) {
        await this.initialize();
      }

      const { title, body, type, data, scheduledFor, repeats, repeatInterval } = notification;

      // iOS-specific notification content optimization
      const notificationContent = {
        title,
        body,
        sound: Platform.OS === 'ios' ? 'default' : 'default',
        priority: 'high' as const,
        autoDismiss: false,
        sticky: false,
        // iOS-specific data structure for better compatibility
        data: {
          ...data,
          type,
          userId: auth.currentUser?.uid,
          platform: Platform.OS,
          timestamp: new Date().toISOString(),
          // iOS-specific fields for better notification handling
          ...(Platform.OS === 'ios' && {
            categoryId: 'general',
            threadId: type
          })
        }
      };

      // Log notification configuration for debugging
      logger.log('[UnifiedNotificationService] Scheduling notification with logo:', {
        title,
        body,
        type,
        platform: Platform.OS,
        scheduledFor: scheduledFor?.toISOString()
      });

      let trigger: any;

      if (scheduledFor) {
        // Schedule for specific date/time
        const secondsUntilTrigger = Math.floor((scheduledFor.getTime() - Date.now()) / 1000);
        
        // CRITICAL FIX: Prevent immediate triggers and ensure minimum delay
        if (secondsUntilTrigger <= 0) {
          logger.warn(`[UnifiedNotificationService] Attempted to schedule notification for past time: ${scheduledFor.toISOString()}, scheduling for 1 minute from now`);
          trigger = {
            type: 'timeInterval',
            seconds: 60, // Minimum 1 minute delay
            repeats: repeats || false
          };
        } else if (secondsUntilTrigger < 60) {
          // If less than 1 minute, add buffer
          trigger = {
            type: 'timeInterval',
            seconds: 60,
            repeats: repeats || false
          };
        } else {
          trigger = {
            type: 'timeInterval',
            seconds: secondsUntilTrigger,
            repeats: repeats || false
          };
        }
      } else {
        // Schedule immediately with minimum delay
        trigger = {
          type: 'timeInterval',
          seconds: 60, // Minimum 1 minute delay instead of 1 second
          repeats: false
        };
      }

      const scheduledId = await Notifications.scheduleNotificationAsync({
        content: notificationContent,
        trigger
      });

      logger.log('[UnifiedNotificationService] Notification scheduled:', {
        id: notification.id,
        type,
        title,
        scheduledId,
        scheduledFor: scheduledFor?.toISOString(),
        platform: Platform.OS
      });

      // iOS-specific success logging
      if (Platform.OS === 'ios') {
        console.log(`[iOS] Notification scheduled successfully: ${type} - ${title}`);
      }

      return scheduledId;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to schedule notification:', error);
      
      // iOS-specific error handling
      if (Platform.OS === 'ios') {
        console.error(`[iOS] Notification scheduling failed: ${error.message}`);
      }
      
      throw error;
    }
  }

  // CRITICAL FIX: Add custom notification scheduling to unified service
  async scheduleCustomNotification(notification: {
    message: string;
    time: string; // HH:MM format
    selectedDays: number[]; // 0=Monday, 1=Tuesday, etc.
    type: 'custom';
  }): Promise<string> {
    try {
      // CRITICAL FIX: Ensure permissions are initialized
      if (!this.isInitialized) {
        await this.initialize();
      }

      const { message, time, selectedDays } = notification;
      const [hours, minutes] = time.split(':').map(Number);
      
      // Calculate next occurrence based on selected days
      const nextOccurrence = this.calculateNextOccurrence(hours, minutes, selectedDays);
      
      const unifiedNotification: UnifiedNotification = {
        id: `custom_${Date.now()}_${Math.random()}`,
        title: 'Custom Reminder',
        body: message,
        type: 'custom',
        data: {
          message,
          time,
          selectedDays,
          userId: auth.currentUser?.uid,
          scheduledFor: nextOccurrence.toISOString(),
          platform: Platform.OS
        },
        scheduledFor: nextOccurrence,
        repeats: false
      };

      const scheduledId = await this.scheduleNotification(unifiedNotification);
      logger.log('[UnifiedNotificationService] Custom notification scheduled:', {
        message,
        time,
        selectedDays,
        scheduledId,
        nextOccurrence: nextOccurrence.toISOString()
      });

      return scheduledId;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to schedule custom notification:', error);
      throw error;
    }
  }

  // Calculate next occurrence for custom notifications
  private calculateNextOccurrence(hours: number, minutes: number, selectedDays: number[]): Date {
    const now = new Date();
    const currentDay = now.getDay(); // 0=Sunday, 1=Monday, etc.
    const targetTime = new Date(now);
    targetTime.setHours(hours, minutes, 0, 0);

    // Convert selectedDays to match JavaScript day format (0=Sunday)
    const jsSelectedDays = selectedDays.map(day => (day + 1) % 7); // Convert Monday=0 to Sunday=0

    // Find next occurrence
    for (let dayOffset = 0; dayOffset <= 7; dayOffset++) {
      const checkDate = new Date(now);
      checkDate.setDate(now.getDate() + dayOffset);
      const checkDay = checkDate.getDay();

      if (jsSelectedDays.includes(checkDay)) {
        const occurrence = new Date(checkDate);
        occurrence.setHours(hours, minutes, 0, 0);

        // If this is today and time hasn't passed, use today
        if (dayOffset === 0 && occurrence > now) {
          return occurrence;
        }
        // If this is today but time has passed, or it's a future day
        if (dayOffset > 0) {
          return occurrence;
        }
      }
    }

    // Fallback: schedule for next week
    const fallback = new Date(now);
    fallback.setDate(now.getDate() + 7);
    fallback.setHours(hours, minutes, 0, 0);
    return fallback;
  }

  // Schedule diet notifications locally with improved day-wise scheduling
  async scheduleDietNotifications(notifications: any[]): Promise<string[]> {
    try {
      const scheduledIds: string[] = [];
      
      for (const notification of notifications) {
        const { message, time, selectedDays } = notification;
        const [hours, minutes] = time.split(':').map(Number);
        
        // CRITICAL FIX: Group notifications by activity and time, not by day
        if (selectedDays && selectedDays.length > 0) {
          // Create one notification per activity with proper day filtering
          const notificationId = `diet_${Date.now()}_${Math.random()}_${hours}_${minutes}`;
          
          // Calculate the next occurrence for the first selected day
          const firstDay = selectedDays[0];
          const nextOccurrence = this.calculateDietNextOccurrence(hours, minutes, firstDay);
          
          const unifiedNotification: UnifiedNotification = {
            id: notificationId,
            title: 'Diet Reminder',
            body: message,
            type: 'diet',
            data: {
              message,
              time,
              selectedDays, // Store all selected days in data
              extractedFrom: notification.extractedFrom,
              notificationId: notificationId,
              // Add activity identifier to prevent duplicates
              activityId: `${message}_${time}`
            },
            scheduledFor: nextOccurrence,
            repeats: true, // Enable weekly repeats for diet notifications
            repeatInterval: 7 * 24 * 60 * 60 // 7 days in seconds
          };

          const scheduledId = await this.scheduleNotification(unifiedNotification);
          scheduledIds.push(scheduledId);
          
          logger.log(`[UnifiedNotificationService] Scheduled grouped diet notification:`, {
            message,
            time,
            selectedDays,
            scheduledFor: nextOccurrence.toISOString(),
            scheduledId,
            activityId: `${message}_${time}`
          });
        } else {
          // Fallback: schedule daily if no specific days selected
          const nextOccurrence = this.calculateDietNextOccurrence(hours, minutes);
          
          const notificationId = `diet_${Date.now()}_${Math.random()}_daily`;
          const unifiedNotification: UnifiedNotification = {
            id: notificationId,
            title: 'Diet Reminder',
            body: message,
            type: 'diet',
            data: {
              message,
              time,
              selectedDays: [],
              extractedFrom: notification.extractedFrom,
              notificationId: notificationId,
              activityId: `${message}_${time}`
            },
            scheduledFor: nextOccurrence,
            repeats: true, // Enable daily repeats for diet notifications
            repeatInterval: 24 * 60 * 60 // Daily in seconds
          };

          const scheduledId = await this.scheduleNotification(unifiedNotification);
          scheduledIds.push(scheduledId);
          
          logger.log('[UnifiedNotificationService] Scheduled daily diet notification:', {
            message,
            time,
            scheduledFor: nextOccurrence.toISOString(),
            scheduledId
          });
        }
      }

      logger.log('[UnifiedNotificationService] Scheduled diet notifications:', scheduledIds);
      return scheduledIds;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to schedule diet notifications:', error);
      throw error;
    }
  }

  // Schedule "New Diet" notification locally
  async scheduleNewDietNotification(userId: string, dietPdfUrl: string): Promise<string> {
    try {
      const unifiedNotification: UnifiedNotification = {
        id: `new_diet_${Date.now()}`,
        title: 'New Diet Has Arrived!',
        body: 'Your dietician has uploaded a new diet plan for you.',
        type: 'new_diet',
        data: {
          userId,
          dietPdfUrl,
          cacheVersion: Date.now()
        }
      };

      const scheduledId = await this.scheduleNotification(unifiedNotification);
      logger.log('[UnifiedNotificationService] New diet notification scheduled:', scheduledId);
      return scheduledId;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to schedule new diet notification:', error);
      throw error;
    }
  }

  // Schedule message notification locally
  async scheduleMessageNotification(
    recipientId: string, 
    senderName: string, 
    message: string, 
    isFromDietician: boolean = false
  ): Promise<string> {
    try {
      const title = isFromDietician ? 'New message from dietician' : `New message from ${senderName}`;
      
      const unifiedNotification: UnifiedNotification = {
        id: `message_${Date.now()}_${Math.random()}`,
        title,
        body: message,
        type: 'message',
        data: {
          recipientId,
          senderName,
          message,
          isFromDietician
        }
      };

      const scheduledId = await this.scheduleNotification(unifiedNotification);
      logger.log('[UnifiedNotificationService] Message notification scheduled:', scheduledId);
      return scheduledId;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to schedule message notification:', error);
      throw error;
    }
  }

  // Schedule diet reminder notification locally
  // REMOVED: scheduleDietReminderNotification method
  // This was causing users to receive "1 day left" notifications meant for dieticians
  // "1 day left" notifications should only be sent to dieticians from the backend

  // Cancel a notification by scheduled ID (for backward compatibility)
  async cancelNotification(scheduledId: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(scheduledId);
      logger.log('[UnifiedNotificationService] Cancelled notification by scheduled ID:', scheduledId);
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to cancel notification by scheduled ID:', error);
      throw error;
    }
  }

  // Cancel a specific notification by ID
  async cancelNotificationById(notificationId: string): Promise<boolean> {
    try {
      const scheduledNotifications = await Notifications.getAllScheduledNotificationsAsync();
      
      for (const notification of scheduledNotifications) {
        if (notification.content.data?.notificationId === notificationId) {
          await Notifications.cancelScheduledNotificationAsync(notification.identifier);
          logger.log('[UnifiedNotificationService] Cancelled specific notification:', notificationId);
          return true;
        }
      }
      
      logger.log('[UnifiedNotificationService] Notification not found for cancellation:', notificationId);
      return false;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to cancel specific notification:', error);
      return false;
    }
  }

  // Cancel all notifications of a specific type
  async cancelNotificationsByType(type: string): Promise<number> {
    try {
      const scheduledNotifications = await Notifications.getAllScheduledNotificationsAsync();
      let cancelledCount = 0;
      
      for (const notification of scheduledNotifications) {
        if (notification.content.data?.type === type) {
          await Notifications.cancelScheduledNotificationAsync(notification.identifier);
          logger.log('[UnifiedNotificationService] Cancelled notification:', notification.identifier);
          cancelledCount++;
        }
      }
      
      logger.log(`[UnifiedNotificationService] Cancelled ${cancelledCount} ${type} notifications`);
      return cancelledCount;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to cancel notifications:', error);
      throw error;
    }
  }

  // Cancel all notifications
  async cancelAllNotifications(): Promise<void> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
      logger.log('[UnifiedNotificationService] Cancelled all notifications');
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to cancel all notifications:', error);
      throw error;
    }
  }

  // Get all scheduled notifications
  async getScheduledNotifications(): Promise<any[]> {
    try {
      const notifications = await Notifications.getAllScheduledNotificationsAsync();
      return notifications;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to get scheduled notifications:', error);
      return [];
    }
  }

  // Calculate next occurrence for diet notifications - using same method as custom reminders
  private calculateDietNextOccurrence(hours: number, minutes: number, dayOfWeek?: number): Date {
    const now = new Date();
    const currentDay = now.getDay(); // 0=Sunday, 1=Monday, etc.
    const targetTime = new Date(now);
    targetTime.setHours(hours, minutes, 0, 0);

    if (dayOfWeek !== undefined) {
      // Convert selectedDays to match JavaScript day format (0=Sunday)
      const jsSelectedDay = (dayOfWeek + 1) % 7; // Convert Monday=0 to Sunday=0
      
      // Find next occurrence for the specific day
      for (let dayOffset = 0; dayOffset <= 7; dayOffset++) {
        const checkDate = new Date(now);
        checkDate.setDate(now.getDate() + dayOffset);
        const checkDay = checkDate.getDay();

        if (checkDay === jsSelectedDay) {
          const occurrence = new Date(checkDate);
          occurrence.setHours(hours, minutes, 0, 0);

          // If this is today and time hasn't passed, use today
          if (dayOffset === 0 && occurrence > now) {
            return occurrence;
          }
          // If this is today but time has passed, or it's a future day
          if (dayOffset > 0) {
            return occurrence;
          }
        }
      }

      // Fallback: schedule for next week
      const fallback = new Date(now);
      fallback.setDate(now.getDate() + 7);
      fallback.setHours(hours, minutes, 0, 0);
      return fallback;
    } else {
      // Daily occurrence - same logic as custom reminders
      if (targetTime > now) {
        return targetTime; // Today if time hasn't passed
      } else {
        const tomorrow = new Date(now);
        tomorrow.setDate(now.getDate() + 1);
        tomorrow.setHours(hours, minutes, 0, 0);
        return tomorrow;
      }
    }
  }

  // Handle notification received
  async handleNotificationReceived(notification: any): Promise<void> {
    try {
      const { type, data } = notification.content.data;
      
      logger.log('[UnifiedNotificationService] Notification received:', { type, data });

      // Handle different notification types
      switch (type) {
        case 'new_diet':
          // Trigger diet refresh in the app
          this.handleNewDietNotification(data);
          break;
        case 'message':
          // Handle message notification
          this.handleMessageNotification(data);
          break;
        case 'diet_reminder':
          // Handle diet reminder notification
          this.handleDietReminderNotification(data);
          break;
        default:
          logger.log('[UnifiedNotificationService] Unknown notification type:', type);
      }
    } catch (error) {
      logger.error('[UnifiedNotificationService] Error handling notification:', error);
    }
  }

  private handleNewDietNotification(data: any): void {
    // This will be handled by the app's notification listener
    logger.log('[UnifiedNotificationService] New diet notification handled:', data);
  }

  private handleMessageNotification(data: any): void {
    // This will be handled by the app's notification listener
    logger.log('[UnifiedNotificationService] Message notification handled:', data);
  }

  private handleDietReminderNotification(data: any): void {
    // This will be handled by the app's notification listener
    logger.log('[UnifiedNotificationService] Diet reminder notification handled:', data);
  }
}

export default UnifiedNotificationService.getInstance();
