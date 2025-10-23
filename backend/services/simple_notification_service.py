#!/usr/bin/env python3
"""
Simple Notification Service
A clean, reliable notification system based on how popular apps handle notifications.
"""

import json
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleNotificationService:
    """
    Simple notification service that handles all notification types uniformly.
    Based on how popular apps like WhatsApp and Instagram handle notifications.
    """
    
    def __init__(self, firestore_db):
        self.db = firestore_db
        logger.info("SimpleNotificationService initialized")
    
    def get_user_token(self, user_id: str) -> Optional[str]:
        """
        Get notification token for a user.
        Handles special case for 'dietician' recipient.
        Returns None if user doesn't exist or has no token.
        """
        try:
            logger.info(f"[SimpleNotification] Getting token for user: {user_id}")
            
            if not self.db:
                logger.error("[SimpleNotification] Firestore not initialized")
                return None
            
            # CRITICAL FIX: Handle 'dietician' as special recipient
            if user_id == "dietician":
                logger.info(f"[SimpleNotification] Getting dietician token (special case)")
                from services.firebase_client import get_dietician_notification_token
                dietician_token = get_dietician_notification_token()
                if dietician_token:
                    logger.info(f"[SimpleNotification] ✅ Dietician token found: {dietician_token[:20]}...")
                else:
                    logger.error(f"[SimpleNotification] ❌ No dietician token found")
                return dietician_token
            
            # Get user document
            doc = self.db.collection("user_profiles").document(user_id).get()
            
            if not doc.exists:
                logger.warning(f"[SimpleNotification] User {user_id} not found")
                return None
            
            data = doc.to_dict()
            
            # Get token (prefer expoPushToken, fallback to notificationToken)
            token = data.get("expoPushToken") or data.get("notificationToken")
            
            if not token:
                logger.warning(f"[SimpleNotification] No token found for user {user_id}")
                return None
            
            # Validate token format
            if not token.startswith("ExponentPushToken"):
                logger.warning(f"[SimpleNotification] Invalid token format for user {user_id}: {token[:20]}...")
                return None
            
            logger.info(f"[SimpleNotification] ✅ Token found for user {user_id}: {token[:20]}...")
            return token
            
        except Exception as e:
            logger.error(f"[SimpleNotification] Error getting token for user {user_id}: {e}")
            return None
    
    def send_notification(self, recipient_id: str, title: str, body: str, data: Dict[str, Any] = None) -> bool:
        """
        Send a notification to a user.
        
        Args:
            recipient_id: User ID to send notification to
            title: Notification title
            body: Notification body
            data: Additional data payload
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            logger.info(f"[SimpleNotification] ===== SENDING NOTIFICATION =====")
            logger.info(f"[SimpleNotification] Recipient: {recipient_id}")
            logger.info(f"[SimpleNotification] Title: {title}")
            logger.info(f"[SimpleNotification] Body: {body}")
            logger.info(f"[SimpleNotification] Data: {data}")
            
            # Get user's notification token
            token = self.get_user_token(recipient_id)
            if not token:
                logger.error(f"[SimpleNotification] ❌ No token found for user {recipient_id}")
                return False
            
            # Prepare notification payload
            notification_data = {
                "to": token,
                "sound": "default",
                "title": title,
                "body": body,
                "data": data or {}
            }
            
            logger.info(f"[SimpleNotification] Payload: {json.dumps(notification_data, indent=2)}")
            
            # Send to Expo Push Service
            logger.info(f"[SimpleNotification] Sending to Expo Push Service...")
            response = requests.post(
                "https://exp.host/--/api/v2/push/send",
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
                data=json.dumps(notification_data),
                timeout=10
            )
            
            logger.info(f"[SimpleNotification] Expo response status: {response.status_code}")
            logger.info(f"[SimpleNotification] Expo response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("data", {}).get("status") == "ok":
                    logger.info(f"[SimpleNotification] ✅ Notification sent successfully to {recipient_id}")
                    return True
                else:
                    logger.error(f"[SimpleNotification] ❌ Expo push error: {result}")
                    return False
            else:
                logger.error(f"[SimpleNotification] ❌ Failed to send notification. Status: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"[SimpleNotification] ❌ Timeout sending notification to {recipient_id}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"[SimpleNotification] ❌ Request error sending notification to {recipient_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"[SimpleNotification] ❌ Error sending notification to {recipient_id}: {e}")
            return False
    
    def send_new_diet_notification(self, user_id: str, dietician_name: str = "Your dietician") -> bool:
        """
        Send notification when new diet is uploaded.
        """
        logger.info(f"[SimpleNotification] Sending new diet notification to user {user_id}")
        
        return self.send_notification(
            recipient_id=user_id,
            title="New Diet Has Arrived! 🥗",
            body=f"{dietician_name} has uploaded a new diet plan for you.",
            data={
                "type": "new_diet",
                "userId": user_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def send_message_notification(self, recipient_id: str, sender_name: str, message: str, is_dietician: bool = False, sender_user_id: str = None) -> bool:
        """
        Send notification for new message.
        
        Args:
            recipient_id: User ID or 'dietician' to send notification to
            sender_name: Name of the message sender
            message: Message content
            is_dietician: True if sender is dietician, False if sender is user
            sender_user_id: User ID of sender (for tracking)
        """
        logger.info(f"[SimpleNotification] ===== MESSAGE NOTIFICATION =====")
        logger.info(f"[SimpleNotification] Recipient: {recipient_id}")
        logger.info(f"[SimpleNotification] Sender: {sender_name}")
        logger.info(f"[SimpleNotification] Is Dietician: {is_dietician}")
        logger.info(f"[SimpleNotification] Sender User ID: {sender_user_id}")
        
        if is_dietician:
            title = f"Message from {sender_name}"
            body = message[:100] + "..." if len(message) > 100 else message
        else:
            title = f"New message from {sender_name}"
            body = message[:100] + "..." if len(message) > 100 else message
        
        # Prepare notification data with proper flags for frontend handlers
        notification_data = {
            "type": "message_notification",
            "senderName": sender_name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # CRITICAL: Add fromDietician or fromUser flag based on sender
        if is_dietician:
            notification_data["fromDietician"] = True
            logger.info(f"[SimpleNotification] Setting fromDietician=True (dietician -> user)")
        else:
            notification_data["fromUser"] = sender_user_id or True
            logger.info(f"[SimpleNotification] Setting fromUser={sender_user_id or True} (user -> dietician)")
        
        return self.send_notification(
            recipient_id=recipient_id,
            title=title,
            body=body,
            data=notification_data
        )
    
    def send_appointment_notification(self, recipient_id: str, appointment_type: str, appointment_date: str, time_slot: str) -> bool:
        """
        Send notification for appointment scheduling/cancelling.
        """
        logger.info(f"[SimpleNotification] Sending appointment notification to {recipient_id}")
        
        if appointment_type == "scheduled":
            title = "Appointment Confirmed ✅"
            body = f"Your appointment has been confirmed for {appointment_date} at {time_slot}"
        elif appointment_type == "cancelled":
            title = "Appointment Cancelled ❌"
            body = f"Your appointment for {appointment_date} at {time_slot} has been cancelled"
        else:
            title = "Appointment Update"
            body = f"Your appointment for {appointment_date} at {time_slot} has been updated"
        
        return self.send_notification(
            recipient_id=recipient_id,
            title=title,
            body=body,
            data={
                "type": "appointment",
                "appointmentType": appointment_type,
                "appointmentDate": appointment_date,
                "timeSlot": time_slot,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def send_diet_reminder_notification(self, user_id: str, user_name: str) -> bool:
        """
        Send notification when user needs new diet (1 day left).
        """
        logger.info(f"[SimpleNotification] Sending diet reminder notification to {user_id}")
        
        return self.send_notification(
            recipient_id=user_id,
            title="Diet Reminder ⏰",
            body=f"Hi {user_name}, your current diet plan expires in 1 day. Please contact your dietician for a new plan.",
            data={
                "type": "diet_reminder",
                "userId": user_id,
                "userName": user_name,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def send_dietician_diet_reminder_notification(self, user_id: str, user_name: str) -> bool:
        """
        Send notification to dietician when user needs new diet (1 day left).
        """
        logger.info(f"[SimpleNotification] Sending diet reminder notification to dietician for user {user_id}")
        
        # Get dietician token
        from services.firebase_client import get_dietician_notification_token
        dietician_token = get_dietician_notification_token()
        if not dietician_token:
            logger.error("[SimpleNotification] No dietician token found")
            return False
        
        # Send to dietician using direct token
        return self.send_notification_to_token(
            token=dietician_token,
            title="Diet Reminder ⏰",
            body=f"{user_name} has 1 day left in their diet",
            data={
                "type": "dietician_diet_reminder",
                "userId": user_id,
                "userName": user_name,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def send_notification_to_token(self, token: str, title: str, body: str, data: Dict[str, Any] = None) -> bool:
        """
        Send a notification directly to a specific token.
        
        Args:
            token: Expo push token to send notification to
            title: Notification title
            body: Notification body
            data: Additional data payload
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            logger.info(f"[SimpleNotification] ===== SENDING NOTIFICATION TO TOKEN =====")
            logger.info(f"[SimpleNotification] Token: {token[:20]}...")
            logger.info(f"[SimpleNotification] Title: {title}")
            logger.info(f"[SimpleNotification] Body: {body}")
            logger.info(f"[SimpleNotification] Data: {data}")
            
            if not token:
                logger.error(f"[SimpleNotification] ❌ No token provided")
                return False
            
            # Prepare notification payload
            notification_data = {
                "to": token,
                "sound": "default",
                "title": title,
                "body": body,
                "data": data or {}
            }
            
            logger.info(f"[SimpleNotification] Payload: {json.dumps(notification_data, indent=2)}")
            
            # Send to Expo Push Service
            logger.info(f"[SimpleNotification] Sending to Expo Push Service...")
            response = requests.post(
                "https://exp.host/--/api/v2/push/send",
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
                data=json.dumps(notification_data),
                timeout=10
            )
            
            logger.info(f"[SimpleNotification] Response status: {response.status_code}")
            logger.info(f"[SimpleNotification] Response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("data", {}).get("status") == "error":
                    logger.error(f"[SimpleNotification] ❌ Expo push error: {result}")
                    return False
                
                logger.info(f"[SimpleNotification] ✅ Notification sent successfully")
                return True
            else:
                logger.error(f"[SimpleNotification] ❌ Failed to send notification: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"[SimpleNotification] ❌ Error sending notification to token: {e}")
            return False


# Global instance
_notification_service = None

def get_notification_service(firestore_db) -> SimpleNotificationService:
    """
    Get the global notification service instance.
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = SimpleNotificationService(firestore_db)
    return _notification_service
