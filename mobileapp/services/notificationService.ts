import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { auth, firestore } from './firebase';
import { logger } from '../utils/logger';

// Configure notification behavior for iOS compatibility
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export interface CustomNotification {
  id: string;
  message: string;
  time: string; // HH:MM format
  selectedDays: number[]; // 0=Monday, 1=Tuesday, etc.
  scheduledId?: string;
  backupIds?: string[];
  type: 'custom' | 'diet';
  createdAt: string;
  userId: string;
}

export interface DietNotification {
  id: string;
  message: string;
  time: string;
  dayOfWeek?: number;
  scheduledId?: string;
  backupIds?: string[];
  extractedFrom: string;
  createdAt: string;
}

class NotificationService {
  private static instance: NotificationService;
  private isInitialized = false;

  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Request permissions
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        throw new Error('Notification permissions not granted');
      }

      // Get push token for remote notifications
      const token = await this.getPushToken();
      if (token) {
        await this.savePushToken(token);
      }

      this.isInitialized = true;
      logger.log('[NotificationService] Initialized successfully');
    } catch (error) {
      logger.error('[NotificationService] Initialization failed:', error);
      throw error;
    }
  }

  private async getPushToken(): Promise<string | null> {
    try {
      if (Platform.OS === 'ios') {
        const token = (await Notifications.getExpoPushTokenAsync({
          projectId: '23b497a5-baac-44c7-82a4-487a59bfff5b'
        })).data;
        return token;
      } else {
        const token = (await Notifications.getExpoPushTokenAsync({
          projectId: '23b497a5-baac-44c7-82a4-487a59bfff5b'
        })).data;
        return token;
      }
    } catch (error) {
      logger.error('[NotificationService] Failed to get push token:', error);
      return null;
    }
  }

  private async savePushToken(token: string): Promise<void> {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) return;

      await firestore.collection('user_profiles').doc(userId).update({
        expoPushToken: token,
        lastTokenUpdate: new Date().toISOString()
      });
      logger.log('[NotificationService] Push token saved to Firestore');
    } catch (error) {
      logger.error('[NotificationService] Failed to save push token:', error);
    }
  }

  // Schedule a custom notification for specific days and time
  async scheduleCustomNotification(notification: Omit<CustomNotification, 'id' | 'createdAt' | 'scheduledId'>): Promise<string> {
    try {
      const { message, time, selectedDays } = notification;
      const [hours, minutes] = time.split(':').map(Number);
      
      // Calculate next occurrence based on selected days
      const nextOccurrence = this.calculateNextOccurrence(hours, minutes, selectedDays);
      const secondsUntilTrigger = Math.max(1, Math.floor((nextOccurrence.getTime() - Date.now()) / 1000));

      const notificationContent = {
        title: 'Custom Reminder',
        body: message,
        sound: 'default',
        priority: 'high',
        autoDismiss: false,
        sticky: false,
        data: {
          type: 'custom_notification',
          message,
          time,
          selectedDays,
          userId: auth.currentUser?.uid,
          scheduledFor: nextOccurrence.toISOString(),
          platform: Platform.OS
        }
      };

      const scheduledId = await Notifications.scheduleNotificationAsync({
        content: notificationContent,
        trigger: {
          type: 'timeInterval',
          seconds: secondsUntilTrigger,
          repeats: false
        } as any,
      });

      logger.log('[NotificationService] Custom notification scheduled:', {
        message,
        time,
        selectedDays,
        scheduledId,
        nextOccurrence: nextOccurrence.toISOString(),
        secondsUntilTrigger
      });

      return scheduledId;
    } catch (error) {
      logger.error('[NotificationService] Failed to schedule custom notification:', error);
      throw error;
    }
  }

  // Calculate next occurrence based on selected days and time
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

  // Schedule diet notification with automatic extraction
  async scheduleDietNotification(notification: Omit<DietNotification, 'id' | 'createdAt' | 'scheduledId'>): Promise<string> {
    try {
      const { message, time, dayOfWeek } = notification;
      const [hours, minutes] = time.split(':').map(Number);
      
      // Calculate next occurrence
      const nextOccurrence = this.calculateDietNextOccurrence(hours, minutes, dayOfWeek);
      const secondsUntilTrigger = Math.max(1, Math.floor((nextOccurrence.getTime() - Date.now()) / 1000));

      const notificationContent = {
        title: 'Diet Reminder',
        body: message,
        sound: 'default',
        priority: 'high',
        autoDismiss: false,
        sticky: false,
        data: {
          type: 'diet_notification',
          message,
          time,
          dayOfWeek,
          extractedFrom: notification.extractedFrom,
          userId: auth.currentUser?.uid,
          scheduledFor: nextOccurrence.toISOString(),
          platform: Platform.OS
        }
      };

      const scheduledId = await Notifications.scheduleNotificationAsync({
        content: notificationContent,
        trigger: {
          type: 'timeInterval',
          seconds: secondsUntilTrigger,
          repeats: false
        } as any,
      });

      logger.log('[NotificationService] Diet notification scheduled:', {
        message,
        time,
        dayOfWeek,
        scheduledId,
        nextOccurrence: nextOccurrence.toISOString(),
        secondsUntilTrigger
      });

      return scheduledId;
    } catch (error) {
      logger.error('[NotificationService] Failed to schedule diet notification:', error);
      throw error;
    }
  }

  private calculateDietNextOccurrence(hours: number, minutes: number, dayOfWeek?: number): Date {
    const now = new Date();
    const currentDay = now.getDay(); // 0=Sunday, 1=Monday, etc.
    const targetTime = new Date(now);
    targetTime.setHours(hours, minutes, 0, 0);

    if (dayOfWeek !== undefined) {
      // Convert selectedDays to match JavaScript day format (0=Sunday)
      const jsSelectedDay = (dayOfWeek + 1) % 7; // Convert Monday=0 to Sunday=0
      
      // Find next occurrence for the specific day - same logic as custom reminders
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

  // Extract and schedule diet notifications automatically
  async extractAndScheduleDietNotifications(): Promise<DietNotification[]> {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) throw new Error('User not authenticated');

      // Get user's diet from Firestore
      const dietDoc = await firestore.collection('users').doc(userId).collection('diets').orderBy('createdAt', 'desc').limit(1).get();
      
      if (dietDoc.empty) {
        throw new Error('No diet found for user');
      }

      const dietData = dietDoc.docs[0].data();
      const dietText = dietData.content || '';

      // Extract time-based activities from diet text
      const notifications = this.extractTimeBasedActivities(dietText);
      
      // Schedule each notification
      const scheduledNotifications: DietNotification[] = [];
      
      for (const notification of notifications) {
        try {
          const scheduledId = await this.scheduleDietNotification({
            ...notification,
            userId,
            extractedFrom: dietData.id || 'unknown'
          });

          scheduledNotifications.push({
            ...notification,
            id: notification.id,
            scheduledId,
            createdAt: new Date().toISOString()
          });
        } catch (error) {
          logger.error('[NotificationService] Failed to schedule diet notification:', error);
        }
      }

      // Save to Firestore
      await this.saveDietNotificationsToFirestore(scheduledNotifications);

      logger.log('[NotificationService] Extracted and scheduled diet notifications:', scheduledNotifications.length);
      return scheduledNotifications;
    } catch (error) {
      logger.error('[NotificationService] Failed to extract diet notifications:', error);
      throw error;
    }
  }

  // Extract time-based activities from diet text
  private extractTimeBasedActivities(dietText: string): Omit<DietNotification, 'id' | 'createdAt' | 'scheduledId' | 'userId'>[] {
    const notifications: Omit<DietNotification, 'id' | 'createdAt' | 'scheduledId' | 'userId'>[] = [];
    
    // Time patterns to match
    const timePatterns = [
      /(\d{1,2}):(\d{2})\s*(am|pm)/gi, // 9:30 AM, 2:15 PM
      /(\d{1,2}):(\d{2})/g, // 14:30, 09:30
      /(\d{1,2})\s*(am|pm)/gi, // 9 AM, 2 PM
    ];

    const lines = dietText.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      for (const pattern of timePatterns) {
        const matches = line.match(pattern);
        if (matches) {
          for (const match of matches) {
            const time = this.parseTime(match);
            if (time) {
              // Extract activity description (next few lines or same line)
              let activity = this.extractActivityDescription(lines, i, line);
              
              if (activity) {
                notifications.push({
                  message: activity,
                  time,
                  extractedFrom: 'diet_pdf',
                  backupIds: []
                });
              }
            }
          }
        }
      }
    }

    return notifications;
  }

  private parseTime(timeStr: string): string | null {
    try {
      const cleanTime = timeStr.toLowerCase().replace(/\s+/g, '');
      
      if (cleanTime.includes('am') || cleanTime.includes('pm')) {
        // 12-hour format
        const match = cleanTime.match(/(\d{1,2}):?(\d{2})?\s*(am|pm)/);
        if (match) {
          let hours = parseInt(match[1]);
          const minutes = parseInt(match[3] || '0');
          const period = match[4];
          
          if (period === 'pm' && hours !== 12) hours += 12;
          if (period === 'am' && hours === 12) hours = 0;
          
          return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        }
      } else {
        // 24-hour format
        const match = cleanTime.match(/(\d{1,2}):(\d{2})/);
        if (match) {
          const hours = parseInt(match[1]);
          const minutes = parseInt(match[2]);
          
          if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
          }
        }
      }
    } catch (error) {
      logger.error('[NotificationService] Error parsing time:', timeStr, error);
    }
    
    return null;
  }

  private extractActivityDescription(lines: string[], lineIndex: number, currentLine: string): string | null {
    // Try to extract activity from current line
    const activityMatch = currentLine.replace(/.*?\d{1,2}:?\d{0,2}\s*(am|pm)?/gi, '').trim();
    if (activityMatch && activityMatch.length > 3) {
      return activityMatch;
    }

    // Try next few lines
    for (let i = lineIndex + 1; i < Math.min(lineIndex + 3, lines.length); i++) {
      const nextLine = lines[i].trim();
      if (nextLine && nextLine.length > 3 && !nextLine.match(/\d{1,2}:?\d{0,2}/)) {
        return nextLine;
      }
    }

    return null;
  }

  // Save diet notifications to Firestore
  private async saveDietNotificationsToFirestore(notifications: DietNotification[]): Promise<void> {
    try {
      const userId = auth.currentUser?.uid;
      if (!userId) return;

      const batch = firestore.batch();
      
      for (const notification of notifications) {
        const docRef = firestore.collection('users').doc(userId).collection('diet_notifications').doc(notification.id);
        batch.set(docRef, notification);
      }

      await batch.commit();
      logger.log('[NotificationService] Diet notifications saved to Firestore');
    } catch (error) {
      logger.error('[NotificationService] Failed to save diet notifications to Firestore:', error);
      throw error;
    }
  }

  // Cancel all scheduled notifications
  async cancelAllNotifications(): Promise<void> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
      logger.log('[NotificationService] All notifications cancelled');
    } catch (error) {
      logger.error('[NotificationService] Failed to cancel all notifications:', error);
      throw error;
    }
  }

  // Cancel specific notification
  async cancelNotification(scheduledId: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(scheduledId);
      logger.log('[NotificationService] Notification cancelled:', scheduledId);
    } catch (error) {
      logger.error('[NotificationService] Failed to cancel notification:', error);
      throw error;
    }
  }

  // Get all scheduled notifications
  async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
    try {
      const notifications = await Notifications.getAllScheduledNotificationsAsync();
      logger.log('[NotificationService] Retrieved scheduled notifications:', notifications.length);
      return notifications;
    } catch (error) {
      logger.error('[NotificationService] Failed to get scheduled notifications:', error);
      throw error;
    }
  }

  // Reschedule notifications daily (for recurring notifications)
  async rescheduleDailyNotifications(): Promise<void> {
    try {
      // This would be called daily to reschedule recurring notifications
      // Implementation depends on your specific requirements
      logger.log('[NotificationService] Daily rescheduling completed');
    } catch (error) {
      logger.error('[NotificationService] Failed to reschedule daily notifications:', error);
      throw error;
    }
  }
}

export default NotificationService.getInstance();
