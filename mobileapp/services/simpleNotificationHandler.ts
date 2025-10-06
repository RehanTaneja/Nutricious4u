/**
 * Simple Notification Handler
 * Handles all notification types uniformly based on how popular apps work.
 */

import { Notifications } from 'expo';
import { Platform, Alert } from 'react-native';

// Simple logger for notifications
const logger = {
  log: (message: string, ...args: any[]) => console.log(`[SimpleNotificationHandler] ${message}`, ...args),
  error: (message: string, ...args: any[]) => console.error(`[SimpleNotificationHandler] ${message}`, ...args),
  warn: (message: string, ...args: any[]) => console.warn(`[SimpleNotificationHandler] ${message}`, ...args)
};

export class SimpleNotificationHandler {
  private static instance: SimpleNotificationHandler;
  
  public static getInstance(): SimpleNotificationHandler {
    if (!SimpleNotificationHandler.instance) {
      SimpleNotificationHandler.instance = new SimpleNotificationHandler();
    }
    return SimpleNotificationHandler.instance;
  }
  
  /**
   * Initialize notification handling
   */
  public initialize(): void {
    try {
      logger.log('[SimpleNotificationHandler] Initializing notification handler');
      
      // Set up notification received listener
      Notifications.addNotificationReceivedListener(this.handleNotificationReceived.bind(this));
      
      logger.log('[SimpleNotificationHandler] ✅ Notification handler initialized');
    } catch (error) {
      logger.error('[SimpleNotificationHandler] Failed to initialize:', error);
    }
  }
  
  /**
   * Handle incoming notifications
   */
  private handleNotificationReceived(notification: any): void {
    try {
      logger.log('[SimpleNotificationHandler] ===== NOTIFICATION RECEIVED =====');
      logger.log('[SimpleNotificationHandler] Notification:', JSON.stringify(notification, null, 2));
      
      const data = notification.request.content.data;
      const title = notification.request.content.title;
      const body = notification.request.content.body;
      
      logger.log('[SimpleNotificationHandler] Title:', title);
      logger.log('[SimpleNotificationHandler] Body:', body);
      logger.log('[SimpleNotificationHandler] Data:', JSON.stringify(data, null, 2));
      
      // Handle different notification types
      if (data?.type) {
        this.handleNotificationByType(data.type, data, title, body);
      } else {
        logger.log('[SimpleNotificationHandler] Generic notification received');
        this.showGenericNotification(title, body);
      }
      
    } catch (error) {
      logger.error('[SimpleNotificationHandler] Error handling notification:', error);
    }
  }
  
  /**
   * Handle notifications by type
   */
  private handleNotificationByType(type: string, data: any, title: string, body: string): void {
    logger.log(`[SimpleNotificationHandler] Handling ${type} notification`);
    
    switch (type) {
      case 'new_diet':
        this.handleNewDietNotification(data, title, body);
        break;
        
      case 'message':
        this.handleMessageNotification(data, title, body);
        break;
        
      case 'appointment':
        this.handleAppointmentNotification(data, title, body);
        break;
        
      case 'diet_reminder':
        this.handleDietReminderNotification(data, title, body);
        break;
        
      case 'test':
        this.handleTestNotification(data, title, body);
        break;
        
      default:
        logger.log(`[SimpleNotificationHandler] Unknown notification type: ${type}`);
        this.showGenericNotification(title, body);
    }
  }
  
  /**
   * Handle new diet notifications
   */
  private handleNewDietNotification(data: any, title: string, body: string): void {
    logger.log('[SimpleNotificationHandler] New diet notification received');
    
    // Show alert for new diet
    Alert.alert(
      title,
      body,
      [
        { text: 'OK', style: 'default' },
        { text: 'View Diet', style: 'default', onPress: () => {
          // Navigate to diet screen if needed
          logger.log('[SimpleNotificationHandler] User wants to view diet');
        }}
      ]
    );
  }
  
  /**
   * Handle message notifications
   */
  private handleMessageNotification(data: any, title: string, body: string): void {
    logger.log('[SimpleNotificationHandler] Message notification received');
    
    // Show alert for message
    Alert.alert(
      title,
      body,
      [
        { text: 'OK', style: 'default' },
        { text: 'Reply', style: 'default', onPress: () => {
          // Navigate to messages if needed
          logger.log('[SimpleNotificationHandler] User wants to reply');
        }}
      ]
    );
  }
  
  /**
   * Handle appointment notifications
   */
  private handleAppointmentNotification(data: any, title: string, body: string): void {
    logger.log('[SimpleNotificationHandler] Appointment notification received');
    
    // Show alert for appointment
    Alert.alert(
      title,
      body,
      [
        { text: 'OK', style: 'default' },
        { text: 'View Appointments', style: 'default', onPress: () => {
          // Navigate to appointments if needed
          logger.log('[SimpleNotificationHandler] User wants to view appointments');
        }}
      ]
    );
  }
  
  /**
   * Handle diet reminder notifications
   */
  private handleDietReminderNotification(data: any, title: string, body: string): void {
    logger.log('[SimpleNotificationHandler] Diet reminder notification received');
    
    // Show alert for diet reminder
    Alert.alert(
      title,
      body,
      [
        { text: 'OK', style: 'default' },
        { text: 'Contact Dietician', style: 'default', onPress: () => {
          // Navigate to contact dietician if needed
          logger.log('[SimpleNotificationHandler] User wants to contact dietician');
        }}
      ]
    );
  }
  
  /**
   * Handle test notifications
   */
  private handleTestNotification(data: any, title: string, body: string): void {
    logger.log('[SimpleNotificationHandler] Test notification received');
    
    // Show simple alert for test
    Alert.alert(
      title,
      body,
      [{ text: 'OK', style: 'default' }]
    );
  }
  
  /**
   * Show generic notification
   */
  private showGenericNotification(title: string, body: string): void {
    logger.log('[SimpleNotificationHandler] Showing generic notification');
    
    Alert.alert(
      title,
      body,
      [{ text: 'OK', style: 'default' }]
    );
  }
}

// Export singleton instance
export const simpleNotificationHandler = SimpleNotificationHandler.getInstance();
