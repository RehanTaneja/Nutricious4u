#!/usr/bin/env python3
"""
Simple Notification Scheduler Service
Temporary replacement for complex scheduler - all notifications handled locally
"""

import logging

logger = logging.getLogger(__name__)

class SimpleNotificationScheduler:
    """
    Simple notification scheduler that delegates all scheduling to local device
    """
    def __init__(self, db):
        self.db = db
        logger.info("SimpleNotificationScheduler initialized - all notifications handled locally")
    
    async def cancel_user_notifications(self, user_id: str) -> int:
        """
        Cancel all scheduled notifications for a user.
        Returns 0 since all notifications are handled locally.
        """
        logger.info(f"[SimpleNotificationScheduler] Notifications for user {user_id} handled locally")
        return 0

    async def schedule_user_notifications(self, user_id: str) -> int:
        """
        Schedule all active notifications for a user.
        Returns 0 since all notifications are handled locally.
        """
        logger.info(f"[SimpleNotificationScheduler] Notifications for user {user_id} handled locally")
        return 0

    async def send_due_notifications(self):
        """
        Send notifications that are due to be sent.
        Returns 0 since all notifications are handled locally.
        """
        logger.info("[SimpleNotificationScheduler] All notifications handled locally")
        return 0

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
