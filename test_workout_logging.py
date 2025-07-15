#!/usr/bin/env python3
"""
Test script to verify workout logging functionality with non-numeric duration values.
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8002"  # Adjust if your server runs on a different port

def test_workout_logging_with_non_numeric_duration():
    """Test workout logging with non-numeric duration values."""
    
    print("Testing workout logging with non-numeric duration values...")
    
    # Test cases with different duration types
    test_cases = [
        {"duration": "30", "description": "Numeric string"},
        {"duration": 30, "description": "Numeric integer"},
        {"duration": "thirty", "description": "Non-numeric string"},
        {"duration": "30 minutes", "description": "String with text"},
        {"duration": "half hour", "description": "Text duration"},
        {"duration": "45 mins", "description": "Abbreviated duration"},
        {"duration": "", "description": "Empty string"},
        {"duration": None, "description": "None value"},
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['description']} ---")
        
        # Test the workout logging endpoint
        workout_data = {
            "workout_id": "1",  # Running workout
            "duration": test_case["duration"]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/workouts/log", json=workout_data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: {result}")
                print(f"   Duration: {result.get('duration')}")
                print(f"   Calories Burned: {result.get('calories_burned')}")
            else:
                print(f"❌ Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def test_gemini_workout_nutrition():
    """Test the Gemini workout nutrition function with non-numeric durations."""
    
    print("\n\nTesting Gemini workout nutrition with non-numeric durations...")
    
    # Test cases for the Gemini function
    test_cases = [
        {"workout_name": "Running", "duration": "30", "description": "Numeric duration"},
        {"workout_name": "Walking", "duration": "twenty", "description": "Non-numeric duration"},
        {"workout_name": "Cycling", "duration": "45 minutes", "description": "Duration with text"},
        {"workout_name": "Yoga", "duration": "", "description": "Empty duration"},
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing Gemini: {test_case['description']} ---")
        
        # Test the workout log endpoint that uses Gemini
        workout_data = {
            "userId": "test_user",
            "exerciseId": "1",
            "exerciseName": test_case["workout_name"],
            "type": "cardio",
            "duration": test_case["duration"],
            "sets": None,
            "reps": None,
            "date": None
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/workout/log", json=workout_data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: {result}")
                print(f"   Duration: {result.get('duration')}")
                print(f"   Calories: {result.get('calories')}")
            else:
                print(f"❌ Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Starting workout logging tests...")
    print("Make sure the backend server is running on localhost:8002")
    
    try:
        # Test basic workout logging
        test_workout_logging_with_non_numeric_duration()
        
        # Test Gemini workout nutrition
        test_gemini_workout_nutrition()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}") 