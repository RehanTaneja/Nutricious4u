#!/usr/bin/env python3
"""
Isolated Diet Issues Analysis

Tests the core logic without external dependencies to identify the exact problems.
"""

import re
from typing import List, Dict, Optional

class SimpleDietAnalyzer:
    """Simplified version of diet analyzer to isolate the core issues"""
    
    def __init__(self):
        # Time patterns from the actual service
        self.time_patterns = [
            r'(\d{1,2})\s*:\s*(\d{2})\s*(AM|PM|am|pm)',  # 5:30 AM, 8:00 PM
            r'(\d{1,2})\s*(AM|PM|am|pm)',  # 6 AM, 8AM, 12PM
            r'(\d{1,2})\s*:\s*(\d{2})',  # 8:00, 14:30
        ]
        
        # Day patterns
        self.day_patterns = [
            (r'MONDAY|Monday', 0),
            (r'TUESDAY|Tuesday', 1), 
            (r'WEDNESDAY|Wednesday', 2),
            (r'THURSDAY|Thursday', 3),
            (r'FRIDAY|Friday', 4),
            (r'SATURDAY|Saturday', 5),
            (r'SUNDAY|Sunday', 6),
        ]
    
    def extract_times_from_line(self, line: str) -> Optional[Dict]:
        """Extract time from a line"""
        for pattern in self.time_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 1:
                    try:
                        hour = int(groups[0])
                        minute = 0  # Default minute
                        
                        # Check if we have minutes
                        if len(groups) >= 2 and groups[1] and groups[1].isdigit():
                            minute = int(groups[1])
                        
                        # Handle AM/PM
                        period_idx = 2 if len(groups) >= 3 else 1
                        if len(groups) > period_idx and groups[period_idx]:
                            period = groups[period_idx].upper()
                            if period in ['PM', 'P.M.'] and hour != 12:
                                hour += 12
                            elif period in ['AM', 'A.M.'] and hour == 12:
                                hour = 0
                        
                        # Get activity text (everything after the time)
                        activity = line[match.end():].strip(' -')
                        
                        return {
                            'hour': hour,
                            'minute': minute,
                            'time': f"{hour:02d}:{minute:02d}",
                            'activity': activity,
                            'original_line': line
                        }
                    except ValueError:
                        continue
        return None
    
    def detect_day_from_line(self, line: str) -> Optional[int]:
        """Detect day from a line"""
        for pattern, day_num in self.day_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return day_num
        return None
    
    def extract_activities(self, diet_text: str) -> List[Dict]:
        """Extract all timed activities from diet text"""
        lines = diet_text.strip().split('\n')
        activities = []
        current_day = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line defines a new day
            detected_day = self.detect_day_from_line(line)
            if detected_day is not None:
                current_day = detected_day
                print(f"📅 Detected day: {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][detected_day]}")
                continue
            
            # Try to extract time from this line
            time_data = self.extract_times_from_line(line)
            if time_data:
                time_data['day'] = current_day
                activities.append(time_data)
                print(f"    ⏰ {time_data['time']} (Day: {current_day}): {time_data['activity'][:40]}...")
        
        return activities
    
    def determine_diet_days(self, activities: List[Dict]) -> List[int]:
        """Determine which days the diet covers"""
        detected_days = set()
        for activity in activities:
            if activity.get('day') is not None:
                detected_days.add(activity['day'])
        
        return sorted(list(detected_days))
    
    def create_notifications(self, activities: List[Dict], diet_days: List[int]) -> List[Dict]:
        """Create notifications from activities"""
        notifications = []
        
        for activity in activities:
            # If activity has specific day, use it; otherwise use diet_days
            if activity.get('day') is not None:
                selected_days = [activity['day']]
            else:
                selected_days = diet_days  # This is the problematic line!
            
            notification = {
                'time': activity['time'],
                'message': activity['activity'],
                'selectedDays': selected_days,
                'hour': activity['hour'],
                'minute': activity['minute']
            }
            notifications.append(notification)
        
        return notifications

def test_real_diet_issues():
    """Test with real diet that causes issues"""
    
    # Real diet text - note it only covers Thursday and Friday
    real_diet = """MR. SNJEEV TANEJA DATED-14 th AUG, 25
WT-97 KGS, HT-5'10", AGE-56 YRS
THURSDAY- 14 th AUG
5:30 AM- 1 glass JEERA water
6 AM- 5 almonds, 2 walnuts, 5 black raisins {soaked}
8AM- 2 green moong dal cheela with mint chutney, 1 bowl ghiya raita
10AM- 1 fruit with roasted pumpkin seeds- 1 apple\\ pear\\ 2 plums\\ kiwi\\ 1 bowl papaya\\ 3-4 slices pineapple
12PM- 1 bowl sprouts salad
1PM- 1 bowl veg, 2 pumpkin missi roti, 1 bowl beetroot\\ ghiya raita with soaked chia seeds
4PM- 1 cup tea with roasted makhana namkeen
6PM- 1 fruit with flaxseeds powder
8PM-1 bowl veg soup, 1 quarter plate green moong , veg masala khichdi
10PM- 1 cup cinnamon water
FRIDAY- 15 th AUG
5:30AM- 1glass jeera water
6 AM- 5 almonds, 2 walnuts, 5 black raisins (soaked)
8AM- 2 egg whites & veggies omelette with 2 sour dough toasts\\ pumpkin missi roti
10AM- 1 fruit with roasted pumpkin seeds
12PM- 1 quarter plate roasted chana salad
1PM- 2 pumpkin missi rotis, 1 bowl veg, 1 bowl beetroot\\ ghiya raita with soaked chia seeds
4PM- 1 cup tea
6PM- 1 fruit with flaxseeds powder
8PM- 1 bowl veg soup
10PM- 1 cup turmeric milk"""

    print("🔍 DIET NOTIFICATION ISSUE ANALYSIS")
    print("=" * 60)
    print("📋 Diet covers: THURSDAY-FRIDAY only")
    print("❌ Problem: User gets notifications on all other days too")
    print()
    
    analyzer = SimpleDietAnalyzer()
    
    # Extract activities
    activities = analyzer.extract_activities(real_diet)
    print(f"📊 Total activities extracted: {len(activities)}")
    
    # Determine diet days
    diet_days = analyzer.determine_diet_days(activities)
    day_names = [['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][d] for d in diet_days]
    print(f"📅 Diet days determined: {diet_days} ({', '.join(day_names)})")
    
    # Expected days (Thursday=3, Friday=4)
    expected_days = [3, 4]
    if set(diet_days) == set(expected_days):
        print("✅ Diet days correctly detected!")
    else:
        print(f"❌ Wrong diet days! Expected: {expected_days} (Thu-Fri), Got: {diet_days}")
    
    print()
    
    # Create notifications
    notifications = analyzer.create_notifications(activities, diet_days)
    
    # Analyze notifications by day
    day_count = {}
    problematic_notifications = []
    
    for notification in notifications:
        selected_days = notification['selectedDays']
        for day in selected_days:
            if day not in day_count:
                day_count[day] = 0
            day_count[day] += 1
        
        # Check for wrong days
        if set(selected_days) != set(expected_days):
            problematic_notifications.append(notification)
    
    print("📱 NOTIFICATIONS BY DAY:")
    print("-" * 30)
    for day in sorted(day_count.keys()):
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
        count = day_count[day]
        is_correct = day in expected_days
        status = "✅" if is_correct else "❌"
        print(f"  {status} {day_name}: {count} notifications")
    
    print()
    
    if problematic_notifications:
        print(f"⚠️ PROBLEMATIC NOTIFICATIONS: {len(problematic_notifications)}")
        print("-" * 30)
        for notif in problematic_notifications[:5]:  # Show first 5
            print(f"  {notif['time']}: {notif['message'][:40]}...")
            print(f"    selectedDays: {notif['selectedDays']} (should be {expected_days})")
    
    print()
    print("🔥 ROOT CAUSE ANALYSIS:")
    print("-" * 30)
    
    # Count activities by day
    thu_activities = [a for a in activities if a.get('day') == 3]
    fri_activities = [a for a in activities if a.get('day') == 4]
    no_day_activities = [a for a in activities if a.get('day') is None]
    
    print(f"  Thursday activities: {len(thu_activities)}")
    print(f"  Friday activities: {len(fri_activities)}")
    print(f"  Activities without day: {len(no_day_activities)}")
    
    if no_day_activities:
        print(f"  🔥 ISSUE: {len(no_day_activities)} activities have no specific day!")
        print(f"     These get assigned diet_days: {diet_days}")
        print(f"     This causes notifications on wrong days!")
        
        print("\n  Sample activities without day:")
        for activity in no_day_activities[:3]:
            print(f"    - {activity['time']}: {activity['activity'][:40]}...")
    
    return activities, notifications, diet_days

if __name__ == "__main__":
    activities, notifications, diet_days = test_real_diet_issues()
    
    print("\n" + "=" * 60)
    print("🎯 EXACT ISSUES IDENTIFIED:")
    print("-" * 30)
    print("1. Some activities are not being assigned to specific days")
    print("2. These activities get assigned to ALL diet days")
    print("3. This causes notifications on days when diet doesn't exist")
    print("4. Need to fix day detection in extraction logic")
    print("5. Need to ensure automatic extraction works on upload")
