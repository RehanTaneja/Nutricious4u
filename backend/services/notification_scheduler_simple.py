#!/usr/bin/env python3
"""
Enhanced Notification Scheduler Service
Automatically schedules diet notifications when dietician uploads new diet
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SimpleNotificationScheduler:
    """
    Enhanced notification scheduler that automatically schedules diet notifications
    """
    def __init__(self, db):
        self.db = db
        logger.info("SimpleNotificationScheduler initialized - will schedule diet notifications automatically")
    
    async def cancel_user_notifications(self, user_id: str) -> int:
        """
        Cancel all scheduled notifications for a user by removing them from the database.
        This prevents old diet notifications from continuing to be sent.
        """
        try:
            logger.info(f"[SimpleNotificationScheduler] Cancelling all notifications for user {user_id}")
            
            # Get all scheduled notifications for this user
            scheduled_ref = self.db.collection("scheduled_notifications")
            user_notifications = scheduled_ref.where("user_id", "==", user_id).stream()
            
            cancelled_count = 0
            for notification_doc in user_notifications:
                try:
                    # Delete the scheduled notification document
                    notification_doc.reference.delete()
                    cancelled_count += 1
                    logger.info(f"[SimpleNotificationScheduler] Cancelled notification {notification_doc.id}")
                except Exception as delete_error:
                    logger.error(f"[SimpleNotificationScheduler] Error deleting notification {notification_doc.id}: {delete_error}")
            
            logger.info(f"[SimpleNotificationScheduler] Successfully cancelled {cancelled_count} notifications for user {user_id}")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"[SimpleNotificationScheduler] Error cancelling notifications for user {user_id}: {e}")
            return 0

    async def schedule_user_notifications(self, user_id: str) -> int:
        """
        Schedule all active diet notifications for a user automatically.
        This is called when dietician uploads a new diet.
        """
        try:
            logger.info(f"[SimpleNotificationScheduler] Scheduling notifications for user {user_id}")
            
            # Get user's diet notifications from Firestore
            user_notifications_ref = self.db.collection("user_notifications").document(user_id)
            notifications_doc = user_notifications_ref.get()
            
            if not notifications_doc.exists:
                logger.info(f"[SimpleNotificationScheduler] No notifications found for user {user_id}")
                return 0
            
            notifications_data = notifications_doc.to_dict()
            diet_notifications = notifications_data.get("diet_notifications", [])
            
            if not diet_notifications:
                logger.info(f"[SimpleNotificationScheduler] No diet notifications found for user {user_id}")
                return 0
            
            logger.info(f"[SimpleNotificationScheduler] Found {len(diet_notifications)} diet notifications for user {user_id}")
            
            # Schedule each notification
            scheduled_count = 0
            for notification in diet_notifications:
                try:
                    # Check if notification is active
                    if not notification.get("isActive", True):
                        logger.info(f"[SimpleNotificationScheduler] Skipping inactive notification: {notification.get('message', 'Unknown')}")
                        continue
                    
                    # Get notification details
                    message = notification.get("message", "")
                    time_str = notification.get("time", "")
                    selected_days = notification.get("selectedDays", [])  # CRITICAL FIX: No default to all days
                    
                    # Skip notifications without proper day selection to prevent random reminders
                    if not selected_days:
                        logger.warning(f"[SimpleNotificationScheduler] Skipping notification without selectedDays: {message}")
                        continue
                    
                    if not message or not time_str:
                        logger.warning(f"[SimpleNotificationScheduler] Invalid notification data: {notification}")
                        continue
                    
                    # Parse time (format: "HH:MM")
                    try:
                        hour, minute = map(int, time_str.split(":"))
                    except ValueError:
                        logger.warning(f"[SimpleNotificationScheduler] Invalid time format: {time_str}")
                        continue
                    
                    # Create scheduled notification record
                    scheduled_notification = {
                        "user_id": user_id,
                        "notification_id": notification.get("id", f"diet_{datetime.now().timestamp()}"),
                        "message": message,
                        "time": time_str,
                        "hour": hour,
                        "minute": minute,
                        "selectedDays": selected_days,
                        "scheduled_for": self._calculate_next_occurrence(hour, minute, selected_days),
                        "status": "scheduled",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "source": "diet_pdf",
                        "isActive": True
                    }
                    
                    # Store in scheduled_notifications collection
                    scheduled_ref = self.db.collection("scheduled_notifications").document(f"{user_id}_{notification.get('id', datetime.now().timestamp())}")
                    scheduled_ref.set(scheduled_notification)
                    
                    scheduled_count += 1
                    logger.info(f"[SimpleNotificationScheduler] Scheduled notification: {message} at {time_str}")
                    
                except Exception as notification_error:
                    logger.error(f"[SimpleNotificationScheduler] Error scheduling notification {notification}: {notification_error}")
                    continue
            
            logger.info(f"[SimpleNotificationScheduler] Successfully scheduled {scheduled_count} notifications for user {user_id}")
            return scheduled_count
            
        except Exception as e:
            logger.error(f"[SimpleNotificationScheduler] Error scheduling notifications for user {user_id}: {e}")
            return 0

    def _calculate_next_occurrence(self, hour: int, minute: int, selected_days: List[int]) -> str:
        """
        Calculate the next occurrence of a notification based on time and selected days.
        Returns ISO timestamp string.
        CRITICAL FIX: Improved logic to prevent notifications on wrong days.
        """
        now = datetime.now()
        current_day = now.weekday()  # 0=Monday, 1=Tuesday, etc.
        
        # CRITICAL FIX: Validate selected_days
        if not selected_days:
            logger.error("No selected days provided for notification scheduling")
            return (now + timedelta(days=1)).isoformat()
        
        logger.info(f"Calculating next occurrence for {hour:02d}:{minute:02d} on days {selected_days}")
        logger.info(f"Current day: {current_day} ({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][current_day]})")
        
        # Check if we can schedule for today
        today_target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if current_day in selected_days and today_target > now:
            logger.info(f"Scheduling for today: {today_target.isoformat()}")
            return today_target.isoformat()
        
        # Find next valid day
        for days_ahead in range(1, 8):  # Check next 7 days
            check_date = now + timedelta(days=days_ahead)
            check_day = check_date.weekday()
            
            if check_day in selected_days:
                target_time = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                logger.info(f"Scheduling for {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][check_day]} ({check_day}): {target_time.isoformat()}")
                return target_time.isoformat()
        
        # Fallback (should never happen if selected_days is valid)
        logger.error(f"Could not find valid day in selected_days {selected_days}")
        return (now + timedelta(days=1)).isoformat()

    async def send_due_notifications(self):
        """
        Send notifications that are due to be sent.
        Now actually sends scheduled diet notifications.
        """
        try:
            logger.info("[SimpleNotificationScheduler] Checking for due notifications...")
            
            # Get all scheduled notifications that are due
            now = datetime.now(timezone.utc)
            scheduled_ref = self.db.collection("scheduled_notifications")
            
            # Query for notifications that are due (scheduled_for <= now and status = "scheduled")
            due_notifications = scheduled_ref.where("status", "==", "scheduled").where("scheduled_for", "<=", now.isoformat()).stream()
            
            sent_count = 0
            for notification_doc in due_notifications:
                try:
                    notification_data = notification_doc.to_dict()
                    user_id = notification_data.get("user_id")
                    notification_id = notification_data.get("notification_id")
                    message = notification_data.get("message", "")
                    
                    if not user_id or not message:
                        logger.warning(f"[SimpleNotificationScheduler] Invalid notification data: {notification_data}")
                        continue
                    
                    # Get user's notification token
                    user_profile_ref = self.db.collection("user_profiles").document(user_id)
                    user_profile = user_profile_ref.get()
                    
                    if not user_profile.exists:
                        logger.warning(f"[SimpleNotificationScheduler] User profile not found: {user_id}")
                        continue
                    
                    user_data = user_profile.to_dict()
                    user_token = user_data.get("expoPushToken") or user_data.get("notificationToken")
                    
                    if not user_token:
                        logger.warning(f"[SimpleNotificationScheduler] No notification token for user: {user_id}")
                        continue
                    
                    # Send push notification
                    from server import send_push_notification  # Import here to avoid circular imports
                    
                    try:
                        send_push_notification(
                            user_token,
                            "Diet Reminder",
                            message,
                            {
                                "type": "diet_reminder",
                                "userId": user_id,
                                "notificationId": notification_id,
                                "timestamp": now.isoformat()
                            }
                        )
                        
                        # Update notification status to sent
                        notification_doc.reference.update({
                            "status": "sent",
                            "sent_at": now.isoformat()
                        })
                        
                        # CRITICAL FIX: Backend handles all recurring scheduling
                        # Schedule next occurrence for recurring notifications
                        self._schedule_next_occurrence(notification_data)
                        logger.info(f"Notification sent successfully - scheduled next occurrence")
                        
                        sent_count += 1
                        logger.info(f"[SimpleNotificationScheduler] Sent notification to user {user_id}: {message}")
                        
                    except Exception as send_error:
                        logger.error(f"[SimpleNotificationScheduler] Error sending notification: {send_error}")
                        # Mark as failed
                        notification_doc.reference.update({
                            "status": "failed",
                            "failed_at": now.isoformat()
                        })
                        
                except Exception as notification_error:
                    logger.error(f"[SimpleNotificationScheduler] Error processing notification {notification_doc.id}: {notification_error}")
                    continue
            
            logger.info(f"[SimpleNotificationScheduler] Sent {sent_count} due notifications")
            return sent_count
            
        except Exception as e:
            logger.error(f"[SimpleNotificationScheduler] Error sending due notifications: {e}")
            return 0

    def _schedule_next_occurrence(self, notification_data: Dict[str, Any]):
        """
        Schedule the next occurrence of a recurring notification.
        """
        try:
            hour = notification_data.get("hour")
            minute = notification_data.get("minute")
            selected_days = notification_data.get("selectedDays", [0, 1, 2, 3, 4, 5, 6])
            
            if hour is None or minute is None:
                return
            
            # Calculate next occurrence
            next_occurrence = self._calculate_next_occurrence(hour, minute, selected_days)
            
            # Update the scheduled notification with next occurrence
            notification_data["scheduled_for"] = next_occurrence
            notification_data["status"] = "scheduled"
            notification_data["created_at"] = datetime.now(timezone.utc).isoformat()
            
            # Store updated notification
            scheduled_ref = self.db.collection("scheduled_notifications").document(notification_data["notification_id"])
            scheduled_ref.set(notification_data, merge=True)
            
            logger.info(f"[SimpleNotificationScheduler] Scheduled next occurrence for notification {notification_data['notification_id']} at {next_occurrence}")
            
        except Exception as e:
            logger.error(f"[SimpleNotificationScheduler] Error scheduling next occurrence: {e}")

    async def cleanup_old_notifications(self):
        """
        Clean up old sent/failed notifications.
        Returns 0 since all notifications are handled locally.
        """
        logger.info("[SimpleNotificationScheduler] Cleanup handled locally")
        return 0

# Global instance
simple_notification_scheduler = None

def get_simple_notification_scheduler(db):
    global simple_notification_scheduler
    if simple_notification_scheduler is None:
        simple_notification_scheduler = SimpleNotificationScheduler(db)
    return simple_notification_scheduler
