import requests
import unittest
import json
import sys

class CalorieTrackerAPITest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CalorieTrackerAPITest, self).__init__(*args, **kwargs)
        self.base_url = "https://848b3fac-d341-4039-baa0-3a59cfdf4897.preview.emergentagent.com/api"
        self.tests_run = 0
        self.tests_passed = 0

    def setUp(self):
        self.tests_run += 1

    def tearDown(self):
        pass

    def test_01_root_endpoint(self):
        """Test the root API endpoint"""
        print("\n🔍 Testing root endpoint...")
        response = requests.get(f"{self.base_url}/")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Hello World")
        
        print("✅ Root endpoint test passed")
        self.tests_passed += 1

    def test_02_food_search_endpoint(self):
        """Test the food search API endpoint"""
        print("\n🔍 Testing food search endpoint...")
        
        # Test with valid query
        response = requests.get(f"{self.base_url}/food/search", params={"query": "apple"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("foods", data)
        self.assertIsInstance(data["foods"], list)
        
        # Verify at least one food item is returned for "apple"
        self.assertGreater(len(data["foods"]), 0)
        
        # Verify food item structure
        food = data["foods"][0]
        self.assertIn("id", food)
        self.assertIn("name", food)
        self.assertIn("calories", food)
        self.assertIn("protein", food)
        self.assertIn("fat", food)
        
        print(f"✅ Food search returned {len(data['foods'])} items for 'apple'")
        
        # Test with another query
        response = requests.get(f"{self.base_url}/food/search", params={"query": "chicken"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify chicken results
        self.assertIn("foods", data)
        chicken_items = [food for food in data["foods"] if "chicken" in food["name"].lower()]
        self.assertGreater(len(chicken_items), 0)
        
        print(f"✅ Food search returned {len(data['foods'])} items for 'chicken'")
        
        # Test with empty query (should return 422 Unprocessable Entity)
        response = requests.get(f"{self.base_url}/food/search", params={"query": ""})
        self.assertEqual(response.status_code, 422)
        
        print("✅ Food search endpoint test passed")
        self.tests_passed += 1

    def test_03_workout_search_endpoint(self):
        """Test the workout search API endpoint"""
        print("\n🔍 Testing workout search endpoint...")
        
        # Test with valid query
        response = requests.get(f"{self.base_url}/workout/search", params={"query": "running"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("exercises", data)
        self.assertIsInstance(data["exercises"], list)
        
        # Verify at least one workout is returned for "running"
        self.assertGreater(len(data["exercises"]), 0)
        
        # Verify workout item structure
        workout = data["exercises"][0]
        self.assertIn("id", workout)
        self.assertIn("name", workout)
        self.assertIn("calories_per_minute", workout)
        self.assertIn("type", workout)
        
        print(f"✅ Workout search returned {len(data['exercises'])} items for 'running'")
        
        # Test with another query
        response = requests.get(f"{self.base_url}/workout/search", params={"query": "yoga"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify yoga results
        self.assertIn("exercises", data)
        yoga_items = [workout for workout in data["exercises"] if "yoga" in workout["name"].lower()]
        self.assertGreater(len(yoga_items), 0)
        
        print(f"✅ Workout search returned {len(data['exercises'])} items for 'yoga'")
        
        # Test with empty query (should return 422 Unprocessable Entity)
        response = requests.get(f"{self.base_url}/workout/search", params={"query": ""})
        self.assertEqual(response.status_code, 422)
        
        print("✅ Workout search endpoint test passed")
        self.tests_passed += 1

    def test_04_status_endpoints(self):
        """Test the status check endpoints"""
        print("\n🔍 Testing status endpoints...")
        
        # Test POST status endpoint
        status_data = {"client_name": "test_client"}
        response = requests.post(f"{self.base_url}/status", json=status_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["client_name"], "test_client")
        self.assertIn("id", data)
        self.assertIn("timestamp", data)
        
        print("✅ POST status endpoint test passed")
        
        # Test GET status endpoint
        response = requests.get(f"{self.base_url}/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        # At least our test entry should be there
        self.assertGreater(len(data), 0)
        
        print(f"✅ GET status endpoint returned {len(data)} entries")
        self.tests_passed += 1

    def run_tests(self):
        """Run all tests and print summary"""
        test_methods = [method for method in dir(self) if method.startswith('test_')]
        test_methods.sort()  # Ensure tests run in order
        
        print("\n🧪 Starting API Tests for Calorie Tracker App")
        print("=" * 50)
        
        for method in test_methods:
            getattr(self, method)()
        
        print("\n" + "=" * 50)
        print(f"📊 Tests Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = CalorieTrackerAPITest()
    success = tester.run_tests()
    sys.exit(0 if success else 1)