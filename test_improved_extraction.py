#!/usr/bin/env python3
"""
Test script for improved diet extraction logic
"""

import re
from datetime import datetime

def extract_structured_diet_activities(diet_text: str):
    """
    Extract timed activities from structured diet format with day headers.
    This handles formats like:
    THURSDAY- 14th AUG
    5:30 AM- 1 glass JEERA water
    6 AM- 5 almonds, 2 walnuts, 5 black raisins {soaked}
    """
    if not diet_text:
        return []
    
    activities = []
    lines = diet_text.split('\n')
    current_day = None
    
    # Day mapping for structured diets
    day_mapping = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a day header (improved pattern)
        day_match = re.search(r'^([A-Z]+)\s*-\s*\d+', line, re.IGNORECASE)
        if day_match:
            day_name = day_match.group(1).lower()
            if day_name in day_mapping:
                current_day = day_mapping[day_name]
                print(f"  📅 Found day: {day_name.upper()} (day {current_day})")
                continue
        
        # Skip lines that don't contain time patterns
        if not re.search(r'\d{1,2}([:.]?\d{2})?\s*(AM|PM|am|pm)?', line):
            print(f"  ⏭️  Skipping line (no time pattern): {line}")
            continue
        
        # Look for time patterns in the line (improved patterns)
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?',  # 5:30 AM, 6:00 PM
            r'(\d{1,2})\s*(AM|PM|am|pm)',  # 6 AM, 8 PM
            r'(\d{1,2})AM',  # 8AM
            r'(\d{1,2})PM',  # 8PM
            r'(\d{1,2})AM-',  # 8AM-
            r'(\d{1,2})PM-',  # 8PM-
        ]
        
        time_match = None
        for pattern in time_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                time_match = match
                break
        
        if time_match and current_day is not None:
            print(f"  🔍 Processing line: {line}")
            print(f"  ⏰ Time match: {time_match.group(0)}")
            try:
                # Extract time components
                if ':' in time_match.group(0):
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    period = time_match.group(3) if len(time_match.groups()) > 2 else None
                else:
                    hour = int(time_match.group(1))
                    minute = 0
                    # Check if the pattern ends with AM/PM
                    if time_match.group(0).upper().endswith('AM'):
                        period = 'AM'
                    elif time_match.group(0).upper().endswith('PM'):
                        period = 'PM'
                    else:
                        period = time_match.group(2) if len(time_match.groups()) > 1 else None
                
                # Convert to 24-hour format
                if period:
                    period = period.upper()
                    if period == 'PM':
                        if hour != 12:
                            hour += 12
                    elif period == 'AM':
                        if hour == 12:
                            hour = 0
                
                # Extract activity text (everything after the time)
                activity_text = line[time_match.end():].strip()
                
                # Clean up the activity text more thoroughly
                if activity_text:
                    # Remove leading dashes, colons, or other separators
                    activity_text = re.sub(r'^[-:\s]+', '', activity_text)
                    
                    # Remove any remaining time patterns to prevent merging
                    activity_text = re.sub(r'\d{1,2}[:.]?\d{2}\s*(AM|PM|am|pm)?', '', activity_text)
                    
                    # Remove day abbreviations that might be left over
                    activity_text = re.sub(r'\b(MON|TUE|WED|THU|FRI|SAT|SUN)\b', '', activity_text, flags=re.IGNORECASE)
                    
                    # Remove any remaining artifacts
                    activity_text = re.sub(r'^[)\s]+', '', activity_text)  # Remove leading ) and spaces
                    activity_text = re.sub(r'[)\s]+$', '', activity_text)  # Remove trailing ) and spaces
                    
                    # Clean up extra whitespace
                    activity_text = re.sub(r'\s+', ' ', activity_text).strip()
                    
                    # Only add if we have meaningful activity text
                    if len(activity_text) > 3 and not activity_text.lower().startswith(('am', 'pm')):
                        # Create activity object
                        activity = {
                            'time': {'hour': hour, 'minute': minute, 'type': 'numeric'},
                            'activity': activity_text,
                            'original_text': line,
                            'hour': hour,
                            'minute': minute,
                            'day': current_day,  # Include day information
                            'unique_id': f"{hour:02d}:{minute:02d}_{hash(activity_text.lower().strip()) % 1000000}"
                        }
                        
                        activities.append(activity)
                        print(f"  ✅ {hour:02d}:{minute:02d} - {activity_text} (Day {current_day})")
                    
            except (ValueError, IndexError) as e:
                print(f"  ❌ Error parsing time in line: {line}, error: {e}")
                continue
    
    # Remove duplicates and sort by time (improved for day-specific activities)
    unique_activities = []
    seen_combinations = set()
    
    for activity in activities:
        # Include day in the combination key to allow same activities on different days
        time_key = f"{activity['hour']:02d}:{activity['minute']:02d}"
        activity_key = activity['activity'].lower().strip()
        day_key = f"day_{activity.get('day', 0)}"
        combination = f"{time_key}_{activity_key}_{day_key}"
        
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            unique_activities.append(activity)
    
    # Sort by day first, then by time
    unique_activities.sort(key=lambda x: (x.get('day', 0), x['hour'], x['minute']))
    
    return unique_activities

def test_extraction():
    """Test the improved extraction with the sample diet"""
    
    sample_diet = """MR. SNJEEV TANEJA DATED-14 th AUG, 25
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
6:30AM- 1 glass water
7AM- 1 glass water
7:30AM- 1glass water
8AM- 2 egg whites & veggies omelette with 2 sour dough toasts\\ pumpkin missi roti
9AM- 1 glass water
10AM- 1 fruit with roasted pumpkin seeds
11AM-1 glass water
12PM- 1 quarter plate roasted chana salad
1PM- 2 pumpkin missi rotis, 1 bowl veg, 1 bowl beetroot\\ ghiya raita with soaked chia seeds"""
    
    print("🧪 Testing Improved Diet Extraction")
    print("=" * 50)
    
    activities = extract_structured_diet_activities(sample_diet)
    
    print("\n📋 Extracted Activities Summary:")
    print("=" * 50)
    
    # Group by day
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day_num in range(7):
        day_activities = [a for a in activities if a.get('day') == day_num]
        if day_activities:
            print(f"\n📅 {day_names[day_num]}:")
            for activity in day_activities:
                time_str = f"{activity['hour']:02d}:{activity['minute']:02d}"
                print(f"  ⏰ {time_str} - {activity['activity']}")
    
    print(f"\n✅ Total activities extracted: {len(activities)}")
    
    return activities

if __name__ == "__main__":
    test_extraction()
