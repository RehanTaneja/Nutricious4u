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
        Cancel all scheduled notifications for a user.
        Returns 0 since all notifications are handled locally.
        """
        logger.info(f"[SimpleNotificationScheduler] Notifications for user {user_id} handled locally")
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
                    selected_days = notification.get("selectedDays", [0, 1, 2, 3, 4, 5, 6])  # Default to all days
                    
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
        """
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, find next occurrence
        if target_time <= now:
            # Find next selected day
            current_day = now.weekday()
            next_day = None
            
            # Check remaining days this week
            for day in range(current_day + 1, 7):
                if day in selected_days:
                    next_day = day
                    break
            
            # If no remaining days this week, find first selected day next week
            if next_day is None:
                for day in range(7):
                    if day in selected_days:
                        next_day = day
                        break
            
            if next_day is not None:
                days_ahead = (next_day - current_day) % 7
                if days_ahead == 0:  # Same day, next week
                    days_ahead = 7
                target_time = now + timedelta(days=days_ahead)
                target_time = target_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return target_time.isoformat()

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
                        
                        # CRITICAL FIX: Remove duplicate scheduling
                        # The mobile app handles recurring notifications with repeats: true
                        # We should NOT schedule next occurrence here to prevent duplicates
                        # This fixes the issue of late notifications appearing after 22:00
                        logger.info(f"Notification sent successfully - mobile app will handle next occurrence")
                        
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
