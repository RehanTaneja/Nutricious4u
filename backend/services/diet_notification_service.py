import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, time
import requests
from services.pdf_rag_service import pdf_rag_service
from services.firebase_client import send_push_notification, get_user_notification_token

logger = logging.getLogger(__name__)

class DietNotificationService:
    """
    Service for extracting timed activities from diet PDFs and converting them
    into scheduled notifications.
    """
    
    def __init__(self):
        # Common time patterns in diet PDFs (ordered by specificity)
        self.time_patterns = [
            # Most specific patterns first (with exact PM format)
            r'(\d{1,2})\s*:\s*(\d{2})\s*P\.M\.',  # 4 : 30 P.M., 5 : 30 P.M.
            r'●\s*(\d{1,2})\s*:\s*(\d{2})\s*P\.M\.',  # ● 4 : 30 P.M., ● 5 : 30 P.M.
            
            # Other specific patterns
            r'(\d{1,2})\s*:\s*(\d{2})\s*(PM|pm)',  # 5 : 30 PM, 4 : 30 PM
            r'(\d{1,2})\s*:\s*(\d{2})\s*(AM|PM|am|pm)',  # 8:00 AM, 12 :00A.M.
            r'(\d{1,2})\s*\.\s*(\d{2})\s*(AM|PM|am|pm)',  # 8.00 AM, 6:30AM.
            r'(\d{1,2})\s*(\d{2})\s*(AM|PM|am|pm)',  # 8 00 AM, 2 30 PM
            
            # Less specific patterns (without AM/PM)
            r'(\d{1,2})\s*:\s*(\d{2})\s*(?:AM|PM|am|pm)?',  # 8:00, 8:00 AM
            r'(\d{1,2})\s*\.\s*(\d{2})\s*(?:AM|PM|am|pm)?',  # 8.00, 8.00 AM
            r'(\d{1,2})\s*(\d{2})\s*(?:AM|PM|am|pm)?',  # 8 00, 8 00 AM
            
            # 24-hour format
            r'(\d{1,2}):(\d{2})\s*(?:AM|PM|am|pm)?',  # 14:30
            r'(\d{1,2})\.(\d{2})\s*(?:AM|PM|am|pm)?',  # 14.30
            r'(\d{1,2})\s*(\d{2})\s*(?:AM|PM|am|pm)?',  # 14 30
            
            # Text-based times
            r'(morning|breakfast|dawn|sunrise)',  # morning, breakfast
            r'(noon|midday|lunch)',  # noon, lunch
            r'(afternoon|evening|dinner|sunset)',  # afternoon, dinner
            r'(night|bedtime|sleep)',  # night, bedtime
        ]
        
        # Common activity keywords
        self.activity_keywords = [
            'water', 'drink', 'eat', 'meal', 'breakfast', 'lunch', 'dinner', 'snack',
            'supplement', 'vitamin', 'medicine', 'medication', 'exercise', 'workout',
            'walk', 'run', 'yoga', 'meditation', 'sleep', 'rest', 'wake', 'wake up',
            'take', 'consume', 'have', 'drink', 'sip', 'gulp', 'swallow',
            'tea', 'cup', 'glass', 'almonds', 'walnut', 'brazilnut', 'raisins', 'fig',
            'coconut', 'fruit', 'pumpkin', 'seeds', 'coriander', 'soaked', 'piece',
            'medicine', 'medication', 'pill', 'tablet', 'capsule', 'raita', 'bowl',
            'cinnamon', 'chia', 'moringa', 'beetroot', 'cucumber', 'jeera', 'ajwain',
            'salt', 'thin', 'regularize', 'regularise'
        ]
        
        # Time mappings for text-based times
        self.text_time_mappings = {
            'morning': (8, 0),
            'breakfast': (8, 0),
            'dawn': (6, 0),
            'sunrise': (6, 0),
            'noon': (12, 0),
            'midday': (12, 0),
            'lunch': (13, 0),
            'afternoon': (15, 0),
            'evening': (18, 0),
            'dinner': (19, 0),
            'sunset': (18, 0),
            'night': (22, 0),
            'bedtime': (22, 0),
            'sleep': (22, 0)
        }
    
    def extract_timed_activities(self, diet_text: str) -> List[Dict]:
        """
        Extract timed activities from diet text.
        Returns a list of dictionaries with time and activity information.
        """
        if not diet_text:
            return []
        
        activities = []
        lines = diet_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Find all time patterns in the line with deduplication at regex level
            time_matches = []
            seen_positions = set()  # Track positions to avoid duplicate matches
            
            for pattern in self.time_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Check if this position has already been matched by a higher priority pattern
                    position_key = (match.start(), match.end())
                    if position_key in seen_positions:
                        continue
                    
                    if len(match.groups()) >= 2:
                        try:
                            hour = int(match.group(1))
                            minute = int(match.group(2))
                            

                            

                            
                            # Handle 12-hour format
                            if len(match.groups()) > 2 and match.group(3):
                                period = match.group(3).upper()
                                if period == 'PM':
                                    if hour == 12:
                                        hour = 12  # 12 PM stays 12
                                    else:
                                        hour += 12  # Other PM times add 12
                                elif period == 'AM':
                                    if hour == 12:
                                        hour = 0  # 12 AM becomes 0
                            else:
                                # If no AM/PM specified, assume AM for early hours (1-11), PM for later (12-23)
                                if 1 <= hour <= 11:
                                    pass  # Keep as AM
                                elif hour == 12:
                                    hour += 12  # 12 without AM/PM is typically PM
                                elif 13 <= hour <= 23:
                                    pass  # Already in 24-hour format
                                else:
                                    continue  # Invalid hour
                            
                            # Special handling for "4 : 30 P.M." and "5 : 30 P.M." format
                            if match.group(0).endswith('P.M.'):
                                if hour in [4, 5]:  # These should be PM times
                                    hour += 12
                            
                            # Validate time
                            if 0 <= hour <= 23 and 0 <= minute <= 59:
                                # Mark this position as seen to prevent duplicate matches
                                seen_positions.add(position_key)
                                
                                time_matches.append({
                                    'start': match.start(),
                                    'end': match.end(),
                                    'hour': hour,
                                    'minute': minute,
                                    'match_text': match.group(0)
                                })
                        except (ValueError, IndexError):
                            continue
            
            # Sort time matches by position and remove duplicates
            time_matches.sort(key=lambda x: x['start'])
            unique_time_matches = []
            seen_times = set()
            
            for time_match in time_matches:
                time_key = f"{time_match['hour']:02d}:{time_match['minute']:02d}"
                if time_key not in seen_times:
                    seen_times.add(time_key)
                    unique_time_matches.append(time_match)
            
            # Process each unique time match
            for time_match in unique_time_matches:
                
                # Extract the text after this time match
                after_time = line[time_match['end']:].strip()
                
                # Look for continuation in next lines if the current line ends with incomplete text
                full_activity = after_time
                if after_time and (after_time.endswith('with') or len(after_time.split()) <= 3):
                    # Check next few lines for continuation
                    line_index = lines.index(line)
                    for i in range(1, min(4, len(lines) - line_index)):
                        if line_index + i < len(lines):
                            next_line = lines[line_index + i].strip()
                            if next_line and not any(time_pattern in next_line for time_pattern in self.time_patterns):
                                # This line might be a continuation
                                full_activity += " " + next_line
                                break
                
                # Clean up the activity text
                activity = self._clean_activity_text(full_activity, line)
                if activity:
                    # Check if we already have an activity for this time
                    existing_activity = None
                    for existing in activities:
                        if (existing['hour'] == time_match['hour'] and 
                            existing['minute'] == time_match['minute']):
                            existing_activity = existing
                            break
                    
                    if existing_activity:
                        # If we already have an activity for this time, choose the more specific one
                        if len(activity) > len(existing_activity['activity']):
                            # Replace with the more detailed activity
                            existing_activity['activity'] = activity
                            existing_activity['original_text'] = line
                    else:
                        # Add new activity
                        activities.append({
                            'time': {'hour': time_match['hour'], 'minute': time_match['minute'], 'type': 'numeric'},
                            'activity': activity,
                            'original_text': line,
                            'hour': time_match['hour'],
                            'minute': time_match['minute']
                        })
        
        # Remove duplicates based on time and activity with better prioritization
        unique_activities = []
        seen_combinations = set()
        time_groups = {}  # Group activities by time to handle AM/PM conflicts
        
        for activity in activities:
            time_key = f"{activity['hour']:02d}:{activity['minute']:02d}"
            activity_key = activity['activity'].lower().strip()
            combination = f"{time_key}_{activity_key}"
            
            # Group by time to handle AM/PM conflicts
            if time_key not in time_groups:
                time_groups[time_key] = []
            time_groups[time_key].append(activity)
        
        # Process each time group to resolve AM/PM conflicts
        for time_key, activities_for_time in time_groups.items():
            if len(activities_for_time) == 1:
                # No conflict, add as is
                activity = activities_for_time[0]
                activity['unique_id'] = f"{time_key}_{hash(activity['activity'].lower().strip()) % 1000000}"
                unique_activities.append(activity)
            else:
                # Multiple activities for the same time - resolve AM/PM conflict
                # Prioritize PM times (later hours) over AM times (earlier hours)
                # For the same hour, prefer the one with more detailed activity
                best_activity = max(activities_for_time, key=lambda x: (
                    x['hour'],  # Prefer later hours (PM over AM)
                    len(x['activity'])  # Prefer more detailed activities
                ))
                
                # Only add if we haven't seen this combination before
                activity_key = best_activity['activity'].lower().strip()
                combination = f"{time_key}_{activity_key}"
                
                if combination not in seen_combinations:
                    seen_combinations.add(combination)
                    best_activity['unique_id'] = f"{time_key}_{hash(activity_key) % 1000000}"
                    unique_activities.append(best_activity)
        
        # Final pass: Remove AM duplicates when we have PM versions
        final_activities = []
        pm_times = set()
        
        # First, identify all PM times
        for activity in unique_activities:
            if activity['hour'] >= 12:  # PM times
                pm_times.add(f"{activity['hour'] - 12:02d}:{activity['minute']:02d}")
        
        # Then filter out AM duplicates
        for activity in unique_activities:
            time_key = f"{activity['hour']:02d}:{activity['minute']:02d}"
            
            # If this is an AM time and we have a corresponding PM time, skip it
            if activity['hour'] < 12:
                am_time_key = f"{activity['hour']:02d}:{activity['minute']:02d}"
                if am_time_key in pm_times:
                    continue
            
            final_activities.append(activity)
        
        return final_activities
    
    def _extract_time_from_line(self, line: str) -> Optional[Dict]:
        """
        Extract time information from a line of text.
        """
        line_lower = line.lower()
        
        # Check for text-based times first
        for text_time, (hour, minute) in self.text_time_mappings.items():
            if text_time in line_lower:
                return {'hour': hour, 'minute': minute, 'type': 'text'}
        
        # Check for numeric time patterns
        for pattern in self.time_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                for match in matches:
                    if len(match) >= 2:
                        try:
                            hour = int(match[0])
                            minute = int(match[1])
                            
                            # Handle 12-hour format
                            if len(match) > 2 and match[2]:
                                period = match[2].upper()
                                if period == 'PM' and hour != 12:
                                    hour += 12
                                elif period == 'AM' and hour == 12:
                                    hour = 0
                            else:
                                # If no AM/PM specified, assume AM for early hours (1-11), PM for later (12-23)
                                if 1 <= hour <= 11:
                                    # Keep as AM
                                    pass
                                elif hour == 12:
                                    # 12 without AM/PM is typically PM
                                    hour += 12
                                elif 13 <= hour <= 23:
                                    # Already in 24-hour format
                                    pass
                                else:
                                    # Invalid hour
                                    continue
                            
                            # Validate time
                            if 0 <= hour <= 23 and 0 <= minute <= 59:
                                return {'hour': hour, 'minute': minute, 'type': 'numeric'}
                        except (ValueError, IndexError):
                            continue
        
                return None

    def _clean_activity_text(self, text: str, original_line: str = "") -> Optional[str]:
        """
        Clean up activity text by removing bullet points and other artifacts.
        """
        if not text:
            return None
        
        # Remove bullet point characters and other artifacts
        cleaned = re.sub(r'^[●•·\-\*\.\s]+', '', text)  # Remove leading bullet points and dots
        cleaned = re.sub(r'[●•·\-\*\.\s]+$', '', cleaned)  # Remove trailing bullet points and dots
        
        # Remove time patterns that might be left over
        cleaned = re.sub(r'\d{1,2}\s*[:\.]\s*\d{2}\s*(?:AM|PM|am|pm)?', '', cleaned)
        cleaned = re.sub(r'\d{1,2}\s*\d{2}\s*(?:AM|PM|am|pm)?', '', cleaned)
        
        # Remove common time words and patterns
        time_words = ['morning', 'breakfast', 'dawn', 'sunrise', 'noon', 'midday', 
                     'lunch', 'dinner', 'afternoon', 'evening', 'sunset', 'night', 
                     'bedtime', 'sleep', 'am', 'pm', 'a.m.', 'p.m.', 'o\'clock', 'oclock']
        
        for word in time_words:
            cleaned = re.sub(r'\b' + word + r'\b', '', cleaned, flags=re.IGNORECASE)
        
        # Remove specific problematic patterns
        cleaned = re.sub(r'\bP\.M\.\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bA\.M\.\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bPM\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bAM\s*', '', cleaned, flags=re.IGNORECASE)
        
        # Remove any remaining bullet point patterns
        cleaned = re.sub(r'●\s*', '', cleaned)
        cleaned = re.sub(r'•\s*', '', cleaned)
        cleaned = re.sub(r'·\s*', '', cleaned)
        cleaned = re.sub(r'\-\s*', '', cleaned)
        cleaned = re.sub(r'\*\s*', '', cleaned)
        
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Check if the cleaned text contains activity keywords
        has_activity = any(keyword in cleaned.lower() for keyword in self.activity_keywords)
        
        if cleaned and has_activity:
            # If the message ends with "with", try to find more context
            if cleaned.strip().endswith('with'):
                # Look for common completions in the original line
                completions = ['honey', 'lemon', 'ginger', 'cinnamon', 'milk', 'sugar', 'cardamom', 'tulsi', 'basil', 'jeera', 'ajwain', 'tulsi', 'basil']
                for completion in completions:
                    if completion in original_line.lower():
                        cleaned = cleaned.strip() + ' ' + completion
                        break
                # If no completion found, try to find what comes after "with" in the original line
                if cleaned.strip().endswith('with'):
                    # Look for text after "with" in the original line
                    with_index = original_line.lower().find('with')
                    if with_index != -1:
                        after_with = original_line[with_index + 4:].strip()
                        if after_with:
                            # Take the first word after "with"
                            next_word = after_with.split()[0] if after_with.split() else ""
                            if next_word and len(next_word) > 2:  # Only if it's a meaningful word
                                cleaned = cleaned.strip() + ' ' + next_word
                            else:
                                cleaned = cleaned.strip()[:-4].strip()  # Remove "with"
                        else:
                            cleaned = cleaned.strip()[:-4].strip()  # Remove "with"
                    else:
                        cleaned = cleaned.strip()[:-4].strip()  # Remove "with"
            
            return cleaned
        
        return None

    def _extract_activity_from_segment(self, segment: str) -> Optional[str]:
        """
        Extract activity description from a segment of text (after bullet point splitting).
        """
        # Remove time information from the segment (more comprehensive patterns)
        cleaned_segment = re.sub(r'\d{1,2}\s*[:\.]\s*\d{2}\s*(?:AM|PM|am|pm)?', '', segment)
        cleaned_segment = re.sub(r'\d{1,2}\s*\d{2}\s*(?:AM|PM|am|pm)?', '', cleaned_segment)
        
        # Remove common time words
        time_words = ['morning', 'breakfast', 'dawn', 'sunrise', 'noon', 'midday', 
                     'lunch', 'dinner', 'afternoon', 'evening', 'sunset', 'night', 
                     'bedtime', 'sleep', 'am', 'pm', 'a.m.', 'p.m.', 'o\'clock', 'oclock']
        
        for word in time_words:
            cleaned_segment = re.sub(r'\b' + word + r'\b', '', cleaned_segment, flags=re.IGNORECASE)
        
        # Clean up the segment
        cleaned_segment = re.sub(r'\s+', ' ', cleaned_segment).strip()
        cleaned_segment = re.sub(r'^[:\-\s\.]+', '', cleaned_segment)  # Remove leading punctuation
        cleaned_segment = re.sub(r'[:\-\s\.]+$', '', cleaned_segment)  # Remove trailing punctuation
        
        # Check if the segment contains activity keywords
        has_activity = any(keyword in cleaned_segment.lower() for keyword in self.activity_keywords)
        
        if cleaned_segment and has_activity:
            return cleaned_segment
        
        return None

    def _extract_activity_from_line(self, line: str) -> Optional[str]:
        """
        Extract activity description from a line of text.
        """
        # Remove time information from the line (more comprehensive patterns)
        cleaned_line = re.sub(r'\d{1,2}\s*[:\.]\s*\d{2}\s*(?:AM|PM|am|pm)?', '', line)
        cleaned_line = re.sub(r'\d{1,2}\s*\d{2}\s*(?:AM|PM|am|pm)?', '', cleaned_line)
        
        # Remove common time words
        time_words = ['morning', 'breakfast', 'dawn', 'sunrise', 'noon', 'midday', 
                     'lunch', 'dinner', 'afternoon', 'evening', 'sunset', 'night', 
                     'bedtime', 'sleep', 'am', 'pm', 'a.m.', 'p.m.', 'o\'clock', 'oclock']
        
        for word in time_words:
            cleaned_line = re.sub(r'\b' + word + r'\b', '', cleaned_line, flags=re.IGNORECASE)
        
        # Clean up the line
        cleaned_line = re.sub(r'\s+', ' ', cleaned_line).strip()
        cleaned_line = re.sub(r'^[:\-\s\.]+', '', cleaned_line)  # Remove leading punctuation
        cleaned_line = re.sub(r'[:\-\s\.]+$', '', cleaned_line)  # Remove trailing punctuation
        
        # Check if the line contains activity keywords
        has_activity = any(keyword in cleaned_line.lower() for keyword in self.activity_keywords)
        
        if cleaned_line and has_activity:
            return cleaned_line
        
        return None
    
    def create_notification_from_activity(self, activity: Dict) -> Dict:
        """
        Create a notification object from an activity.
        """
        time_obj = time(activity['hour'], activity['minute'])
        # Use the unique_id if available, otherwise generate one
        unique_id = activity.get('unique_id', f"{activity['hour']:02d}:{activity['minute']:02d}_{hash(activity['activity']) % 1000000}")
        notification_id = f"diet_{activity['hour']}_{activity['minute']}_{hash(unique_id) % 1000000}"
        
        return {
            'id': notification_id,
            'message': activity['activity'],
            'time': time_obj.strftime('%H:%M'),
            'hour': activity['hour'],
            'minute': activity['minute'],
            'scheduledId': None,  # Will be set when scheduled
            'source': 'diet_pdf',
            'original_text': activity['original_text'],
            'selectedDays': [0, 1, 2, 3, 4, 5, 6],  # Default to all days for extracted notifications
            'isActive': True  # Track if notification is active
        }
    
    def extract_and_create_notifications(self, user_id: str, diet_pdf_url: str, db) -> List[Dict]:
        """
        Extract timed activities from a user's diet PDF and create notifications.
        """
        try:
            # Get diet text using the existing RAG service
            diet_text = pdf_rag_service.get_diet_pdf_text(user_id, diet_pdf_url, db)
            
            if not diet_text:
                logger.warning(f"No diet text found for user {user_id}")
                return []
            
            # Extract timed activities
            activities = self.extract_timed_activities(diet_text)
            
            if not activities:
                logger.info(f"No timed activities found in diet PDF for user {user_id}")
                return []
            
            # Create notifications from activities
            notifications = []
            for activity in activities:
                notification = self.create_notification_from_activity(activity)
                notifications.append(notification)
            
            logger.info(f"Extracted {len(notifications)} timed activities from diet PDF for user {user_id}")
            return notifications
            
        except Exception as e:
            logger.error(f"Error extracting notifications from diet PDF for user {user_id}: {e}")
            return []
    
    def send_immediate_notification(self, user_id: str, notification: Dict) -> bool:
        """
        Send an immediate notification to a user.
        """
        try:
            user_token = get_user_notification_token(user_id)
            if not user_token:
                logger.warning(f"No notification token found for user {user_id}")
                return False
            
            success = send_push_notification(
                token=user_token,
                title="Diet Reminder",
                body=notification['message'],
                data={
                    'type': 'diet_reminder',
                    'source': 'diet_pdf',
                    'time': notification['time']
                }
            )
            
            if success:
                logger.info(f"Sent diet notification to user {user_id}: {notification['message']}")
            else:
                logger.error(f"Failed to send diet notification to user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending diet notification to user {user_id}: {e}")
            return False

# Global instance
diet_notification_service = DietNotificationService() 