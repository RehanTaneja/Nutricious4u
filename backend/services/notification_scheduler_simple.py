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
        DISABLED: Backend diet notification scheduling is disabled to prevent conflicts.
        All diet notifications are now handled by the frontend for reliability.
        """
        logger.info(f"[SimpleNotificationScheduler] DISABLED - Diet notifications for user {user_id} handled by frontend only")
        return 0

    def _calculate_next_occurrence(self, hour: int, minute: int, selected_days: List[int]) -> str:
        """
        Calculate the next occurrence of a notification based on time and selected days.
        Returns ISO timestamp string in UTC.
        """
        now = datetime.now(timezone.utc)
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
        DISABLED: Backend diet notification sending is disabled to prevent conflicts.
        All diet notifications are now handled by the frontend for reliability.
        """
        logger.info("[SimpleNotificationScheduler] DISABLED - Diet notifications handled by frontend only")
        return 0

    def _schedule_next_occurrence(self, notification_data: Dict[str, Any]):
        """
        Schedule the next occurrence of a recurring notification.
        """
        try:
            hour = notification_data.get("hour")
            minute = notification_data.get("minute")
            selected_days = notification_data.get("selectedDays", [])
            
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
