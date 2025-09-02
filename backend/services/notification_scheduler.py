#!/usr/bin/env python3
"""
Notification Scheduler Service
Handles day-based notification scheduling and sending
"""

import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from typing import List, Dict
import firebase_admin
from firebase_admin import firestore

from services.firebase_client import send_push_notification, get_user_notification_token

logger = logging.getLogger(__name__)

class NotificationScheduler:
    def __init__(self, db):
        self.db = db
        self.days_of_week = {
            0: "Monday",
            1: "Tuesday", 
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday"
        }
    
    async def cancel_user_notifications(self, user_id: str) -> int:
        """
        Cancel all scheduled notifications for a user.
        Returns the number of notifications cancelled.
        """
        try:
            logger.info(f"Cancelling all scheduled notifications for user {user_id}")
            
            # Get all scheduled notifications for this user
            scheduled_ref = self.db.collection("scheduled_notifications")
            user_notifications = scheduled_ref.where("user_id", "==", user_id).where("status", "==", "scheduled").stream()
            
            cancelled_count = 0
            
            for doc in user_notifications:
                try:
                    # Update status to cancelled
                    doc.reference.update({
                        'status': 'cancelled',
                        'cancelled_at': datetime.now(pytz.UTC).isoformat()
                    })
                    cancelled_count += 1
                    logger.info(f"Cancelled scheduled notification: {doc.id}")
                except Exception as e:
                    logger.error(f"Error cancelling notification {doc.id}: {e}")
            
            logger.info(f"Cancelled {cancelled_count} scheduled notifications for user {user_id}")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"Error cancelling notifications for user {user_id}: {e}")
            return 0

    async def schedule_user_notifications(self, user_id: str) -> int:
        """
        Schedule all active notifications for a user based on their day preferences.
        Returns the number of notifications scheduled.
        """
        try:
            # First, cancel all existing scheduled notifications for this user
            cancelled_count = await self.cancel_user_notifications(user_id)
            logger.info(f"Cancelled {cancelled_count} existing notifications before scheduling new ones")
            
            # Get user's notifications
            user_notifications_ref = self.db.collection("user_notifications").document(user_id)
            doc = user_notifications_ref.get()
            
            if not doc.exists:
                return 0
            
            data = doc.to_dict()
            notifications = data.get("diet_notifications", [])
            
            if not notifications:
                return 0
            
            # Get user's notification token
            user_token = get_user_notification_token(user_id)
            if not user_token:
                logger.warning(f"No notification token found for user {user_id}")
                return 0
            
            # Prepare batch operations for better performance
            batch = self.db.batch()
            scheduled_count = 0
            
            for notification in notifications:
                if not notification.get('isActive', True):
                    continue
                    
                selected_days = notification.get('selectedDays', [0, 1, 2, 3, 4, 5, 6])
                if not selected_days:
                    continue
                
                # Schedule notification for each selected day
                for day in selected_days:
                    scheduled_notification = self._prepare_scheduled_notification(
                        user_token, notification, day, user_id
                    )
                    if scheduled_notification:
                        # Add to batch instead of individual operations
                        doc_ref = self.db.collection("scheduled_notifications").document()
                        batch.set(doc_ref, scheduled_notification)
                        scheduled_count += 1
            
            # Commit all operations in a single batch
            if scheduled_count > 0:
                batch.commit()
            
            logger.info(f"Scheduled {scheduled_count} notifications for user {user_id}")
            return scheduled_count
            
        except Exception as e:
            logger.error(f"Error scheduling notifications for user {user_id}: {e}")
            return 0
    
    def _prepare_scheduled_notification(self, user_token: str, notification: dict, day: int, user_id: str) -> dict:
        """
        Prepare a scheduled notification document for a specific day of the week.
        Returns the notification data to be stored in Firestore.
        """
        try:
            # Get current time in UTC
            now = datetime.now(pytz.UTC)
            
            # Parse the notification time
            target_time = datetime.strptime(notification['time'], '%H:%M').time()
            
            # Use UTC for consistent timezone handling across all environments
            # This ensures notifications work correctly in both Expo Go and EAS builds
            days_ahead = (day - now.weekday()) % 7
            
            # If it's the same day and the time has already passed, go to next week
            if days_ahead == 0 and now.time() >= target_time:
                days_ahead = 7
            
            # Calculate the next occurrence in UTC
            next_occurrence = now + timedelta(days=days_ahead)
            next_occurrence = next_occurrence.replace(
                hour=target_time.hour, 
                minute=target_time.minute, 
                second=0, 
                microsecond=0
            )
            
            # Prepare the scheduled notification document
            scheduled_notification = {
                'user_id': user_id,
                'notification_id': notification['id'],
                'message': notification['message'],
                'time': notification['time'],
                'day': day,
                'scheduled_for': next_occurrence.isoformat(),
                'status': 'scheduled',
                'created_at': datetime.now(pytz.UTC).isoformat()
            }
            
            logger.info(f"Prepared notification for user {user_id} on {self.days_of_week[day]} at {notification['time']}")
            logger.info(f"  Current UTC: {now.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {now.weekday()})")
            logger.info(f"  Target day: {self.days_of_week[day]} (day {day})")
            logger.info(f"  Days ahead: {days_ahead}")
            logger.info(f"  Next occurrence UTC: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S %Z')} (weekday: {next_occurrence.weekday()})")
            return scheduled_notification
            
        except Exception as e:
            logger.error(f"Error preparing notification for day {day}: {e}")
            return None

    async def _schedule_notification_for_day(self, user_token: str, notification: dict, day: int, user_id: str) -> bool:
        """
        Schedule a notification for a specific day of the week.
        This method is kept for backward compatibility but uses the new batch approach.
        """
        try:
            scheduled_notification = self._prepare_scheduled_notification(user_token, notification, day, user_id)
            if scheduled_notification:
                # Store in scheduled_notifications collection
                self.db.collection("scheduled_notifications").add(scheduled_notification)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error scheduling notification for day {day}: {e}")
            return False
    
    async def send_due_notifications(self):
        """
        Send notifications that are due to be sent.
        This should be called periodically (e.g., every minute).
        """
        try:
            now = datetime.now(pytz.UTC)
            logger.info(f"[Notification Scheduler] Checking for due notifications at {now.isoformat()}")
            
            # Get all scheduled notifications that are due
            scheduled_ref = self.db.collection("scheduled_notifications")
            due_notifications = scheduled_ref.where("status", "==", "scheduled").stream()
            
            sent_count = 0
            checked_count = 0
            
            for doc in due_notifications:
                checked_count += 1
                scheduled_data = doc.to_dict()
                scheduled_for = datetime.fromisoformat(scheduled_data['scheduled_for'].replace('Z', '+00:00'))
                
                logger.info(f"[Notification Scheduler] Checking notification: {scheduled_data.get('message', 'N/A')} scheduled for {scheduled_for.isoformat()}")
                
                # Check if notification is due (within the last minute)
                if now >= scheduled_for and (now - scheduled_for).total_seconds() <= 60:
                    logger.info(f"[Notification Scheduler] Notification is due! Sending...")
                    success = await self._send_notification(scheduled_data, doc.id)
                    if success:
                        sent_count += 1
                        logger.info(f"[Notification Scheduler] Successfully sent notification")
                    else:
                        logger.error(f"[Notification Scheduler] Failed to send notification")
                else:
                    time_diff = (scheduled_for - now).total_seconds()
                    logger.info(f"[Notification Scheduler] Notification not due yet. Time remaining: {time_diff:.0f} seconds")
            
            if checked_count > 0:
                logger.info(f"[Notification Scheduler] Checked {checked_count} notifications, sent {sent_count}")
            else:
                logger.info(f"[Notification Scheduler] No scheduled notifications found")
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending due notifications: {e}")
            return 0
    
    async def _send_notification(self, scheduled_data: dict, doc_id: str) -> bool:
        """
        Send a scheduled notification and update its status.
        """
        try:
            user_token = get_user_notification_token(scheduled_data['user_id'])
            if not user_token:
                logger.warning(f"No notification token found for user {scheduled_data['user_id']}")
                return False
            
            # Send the notification
            success = send_push_notification(
                token=user_token,
                title="Diet Reminder",
                body=scheduled_data['message'],
                data={
                    'type': 'diet_reminder',
                    'source': 'diet_pdf',
                    'time': scheduled_data['time'],
                    'day': scheduled_data['day'],
                    'notification_id': scheduled_data['notification_id'],
                    'scheduled_for': scheduled_data['scheduled_for']
                }
            )
            
            if success:
                # Update status to sent
                self.db.collection("scheduled_notifications").document(doc_id).update({
                    'status': 'sent',
                    'sent_at': datetime.now(pytz.UTC).isoformat()
                })
                
                # Schedule next occurrence for next week
                await self._schedule_next_occurrence(scheduled_data)
                
                logger.info(f"Sent notification to user {scheduled_data['user_id']}: {scheduled_data['message']}")
                return True
            else:
                # Update status to failed
                self.db.collection("scheduled_notifications").document(doc_id).update({
                    'status': 'failed',
                    'failed_at': datetime.now(pytz.UTC).isoformat()
                })
                return False
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    async def _schedule_next_occurrence(self, scheduled_data: dict):
        """
        Schedule the next occurrence of this notification for next week.
        """
        try:
            scheduled_for = datetime.fromisoformat(scheduled_data['scheduled_for'].replace('Z', '+00:00'))
            next_occurrence = scheduled_for + timedelta(days=7)
            
            next_scheduled = {
                'user_id': scheduled_data['user_id'],
                'notification_id': scheduled_data['notification_id'],
                'message': scheduled_data['message'],
                'time': scheduled_data['time'],
                'day': scheduled_data['day'],
                'scheduled_for': next_occurrence.isoformat(),
                'status': 'scheduled',
                'created_at': datetime.now(pytz.UTC).isoformat()
            }
            
            self.db.collection("scheduled_notifications").add(next_scheduled)
            
        except Exception as e:
            logger.error(f"Error scheduling next occurrence: {e}")
    
    async def cleanup_old_notifications(self):
        """
        Clean up old sent/failed notifications (older than 30 days).
        """
        try:
            cutoff_date = datetime.now(pytz.UTC) - timedelta(days=30)
            
            # Get old notifications
            scheduled_ref = self.db.collection("scheduled_notifications")
            old_notifications = scheduled_ref.where("created_at", "<", cutoff_date.isoformat()).stream()
            
            deleted_count = 0
            for doc in old_notifications:
                doc.reference.delete()
                deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old notifications")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {e}")
            return 0

# Global instance
notification_scheduler = None

def get_notification_scheduler(db):
    global notification_scheduler
    if notification_scheduler is None:
        notification_scheduler = NotificationScheduler(db)
    return notification_scheduler
