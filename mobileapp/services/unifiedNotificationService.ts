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
  private notificationService: any;

  private constructor() {
    // Import the existing notification service
    this.notificationService = require('./notificationService').default;
  }

  public static getInstance(): UnifiedNotificationService {
    if (!UnifiedNotificationService.instance) {
      UnifiedNotificationService.instance = new UnifiedNotificationService();
    }
    return UnifiedNotificationService.instance;
  }

  // Schedule a notification locally (works in EAS builds)
  async scheduleNotification(notification: UnifiedNotification): Promise<string> {
    try {
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
        const secondsUntilTrigger = Math.max(1, Math.floor((scheduledFor.getTime() - Date.now()) / 1000));
        trigger = {
          type: 'timeInterval',
          seconds: secondsUntilTrigger,
          repeats: repeats || false
        };
      } else {
        // Schedule immediately
        trigger = {
          type: 'timeInterval',
          seconds: 1,
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

  // Schedule diet notifications locally with day-wise scheduling
  async scheduleDietNotifications(notifications: any[]): Promise<string[]> {
    try {
      const scheduledIds: string[] = [];
      
      for (const notification of notifications) {
        const { message, time, selectedDays } = notification;
        const [hours, minutes] = time.split(':').map(Number);
        
        // Schedule for each selected day
        if (selectedDays && selectedDays.length > 0) {
          for (const dayOfWeek of selectedDays) {
            // Calculate next occurrence for this specific day
            const nextOccurrence = this.calculateDietNextOccurrence(hours, minutes, dayOfWeek);
            
            const notificationId = `diet_${Date.now()}_${Math.random()}_day_${dayOfWeek}`;
            const unifiedNotification: UnifiedNotification = {
              id: notificationId,
              title: 'Diet Reminder',
              body: message,
              type: 'diet',
              data: {
                message,
                time,
                dayOfWeek,
                selectedDays,
                extractedFrom: notification.extractedFrom,
                notificationId: notificationId // Add this for specific cancellation
              },
              scheduledFor: nextOccurrence,
              repeats: true,
              repeatInterval: 7 * 24 * 60 * 60 // 7 days in seconds
            };

            const scheduledId = await this.scheduleNotification(unifiedNotification);
            scheduledIds.push(scheduledId);
            
            logger.log(`[UnifiedNotificationService] Scheduled diet notification for day ${dayOfWeek}:`, {
              message,
              time,
              scheduledFor: nextOccurrence.toISOString(),
              scheduledId
            });
          }
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
              dayOfWeek: null,
              selectedDays: [],
              extractedFrom: notification.extractedFrom,
              notificationId: notificationId
            },
            scheduledFor: nextOccurrence,
            repeats: true,
            repeatInterval: 24 * 60 * 60 // Daily
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
  async scheduleDietReminderNotification(userId: string, userName: string): Promise<string> {
    try {
      const unifiedNotification: UnifiedNotification = {
        id: `diet_reminder_${Date.now()}`,
        title: 'Diet Reminder Alert',
        body: `User ${userName} has 1 day remaining on their diet plan.`,
        type: 'diet_reminder',
        data: {
          userId,
          userName
        }
      };

      const scheduledId = await this.scheduleNotification(unifiedNotification);
      logger.log('[UnifiedNotificationService] Diet reminder notification scheduled:', scheduledId);
      return scheduledId;
    } catch (error) {
      logger.error('[UnifiedNotificationService] Failed to schedule diet reminder notification:', error);
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

  // Calculate next occurrence for diet notifications
  private calculateDietNextOccurrence(hours: number, minutes: number, dayOfWeek?: number): Date {
    const now = new Date();
    const targetTime = new Date(now);
    targetTime.setHours(hours, minutes, 0, 0);

    if (dayOfWeek !== undefined) {
      // Specific day of week
      const currentDay = now.getDay();
      const targetDay = (dayOfWeek + 1) % 7; // Convert Monday=0 to Sunday=0
      
      let daysToAdd = targetDay - currentDay;
      if (daysToAdd <= 0) daysToAdd += 7; // Next week if today or past

      const occurrence = new Date(now);
      occurrence.setDate(now.getDate() + daysToAdd);
      occurrence.setHours(hours, minutes, 0, 0);

      // If it's today and time hasn't passed, use today
      if (daysToAdd === 7 && targetTime > now) {
        return targetTime;
      }

      return occurrence;
    } else {
      // Daily occurrence
      if (targetTime > now) {
        return targetTime; // Today
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
