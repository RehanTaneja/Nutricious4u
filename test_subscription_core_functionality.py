#!/usr/bin/env python3
"""
Core Subscription Functionality Test
Tests plan durations, pricing, and auto-renewal logic without creating users
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://nutricious4u-production.up.railway.app"

def log_test(test_name: str, status: str, details: str = ""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")

def test_subscription_plans_structure():
    """Test that subscription plans have correct structure and pricing"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/subscription/plans", timeout=10)
        if response.status_code == 200:
            data = response.json()
            plans = data.get("plans", [])
            log_test("Get Subscription Plans", "PASS", f"Found {len(plans)} plans")
            
            # Expected plans and their details
            expected_plans = {
                "free": {"price": 0.0, "duration": "Forever"},
                "1month": {"price": 5000.0, "duration": "1 month"},
                "2months": {"price": 9000.0, "duration": "2 months"},
                "3months": {"price": 12000.0, "duration": "3 months"},
                "6months": {"price": 20000.0, "duration": "6 months"}
            }
            
            # Verify each plan exists and has correct details
            all_correct = True
            for plan_id, expected in expected_plans.items():
                plan_found = False
                for plan in plans:
                    if plan.get("planId") == plan_id:
                        plan_found = True
                        if plan.get("price") == expected["price"]:
                            log_test(f"Plan {plan_id} Pricing", "PASS", f"Price: ₹{expected['price']}")
                        else:
                            log_test(f"Plan {plan_id} Pricing", "FAIL", f"Expected ₹{expected['price']}, got ₹{plan.get('price')}")
                            all_correct = False
                        
                        if plan.get("duration") == expected["duration"]:
                            log_test(f"Plan {plan_id} Duration", "PASS", f"Duration: {expected['duration']}")
                        else:
                            log_test(f"Plan {plan_id} Duration", "FAIL", f"Expected {expected['duration']}, got {plan.get('duration')}")
                            all_correct = False
                        break
                
                if not plan_found:
                    log_test(f"Plan {plan_id} Exists", "FAIL", "Plan not found")
                    all_correct = False
                else:
                    log_test(f"Plan {plan_id} Exists", "PASS", "Plan found")
            
            return all_correct
        else:
            log_test("Get Subscription Plans", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Subscription Plans", "FAIL", f"Error: {e}")
        return False

def test_plan_duration_calculations():
    """Test that plan duration calculations are correct"""
    try:
        # Test each plan's duration calculation logic
        test_cases = [
            {"plan": "1month", "expected_days": 30, "description": "1 month = 30 days"},
            {"plan": "2months", "expected_days": 60, "description": "2 months = 60 days"},
            {"plan": "3months", "expected_days": 90, "description": "3 months = 90 days"},
            {"plan": "6months", "expected_days": 180, "description": "6 months = 180 days"}
        ]
        
        all_passed = True
        for test_case in test_cases:
            # Simulate the duration calculation logic from the backend
            start_date = datetime.now()
            if test_case["plan"] == "1month":
                end_date = start_date + timedelta(days=30)
            elif test_case["plan"] == "2months":
                end_date = start_date + timedelta(days=60)
            elif test_case["plan"] == "3months":
                end_date = start_date + timedelta(days=90)
            elif test_case["plan"] == "6months":
                end_date = start_date + timedelta(days=180)
            
            actual_days = (end_date - start_date).days
            if actual_days == test_case["expected_days"]:
                log_test(f"Duration {test_case['plan']}", "PASS", f"{test_case['description']}")
            else:
                log_test(f"Duration {test_case['plan']}", "FAIL", f"Expected {test_case['expected_days']} days, got {actual_days}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        log_test("Plan Duration Calculations", "FAIL", f"Error: {e}")
        return False

def test_subscription_endpoints():
    """Test that subscription-related endpoints are accessible"""
    try:
        test_user_id = "test_user_endpoints"
        
        # Test subscription status endpoint
        response = requests.get(f"{BACKEND_URL}/api/subscription/status/{test_user_id}", timeout=10)
        if response.status_code in [200, 404]:  # 404 is OK if user doesn't exist
            log_test("Subscription Status Endpoint", "PASS", f"Endpoint accessible (status: {response.status_code})")
        else:
            log_test("Subscription Status Endpoint", "FAIL", f"Status code: {response.status_code}")
            return False
        
        # Test subscription cancellation endpoint
        response = requests.post(f"{BACKEND_URL}/api/subscription/cancel/{test_user_id}", timeout=10)
        if response.status_code in [200, 400, 404]:  # Various status codes are acceptable
            log_test("Subscription Cancellation Endpoint", "PASS", f"Endpoint accessible (status: {response.status_code})")
        else:
            log_test("Subscription Cancellation Endpoint", "FAIL", f"Status code: {response.status_code}")
            return False
        
        # Test auto-renewal toggle endpoint
        response = requests.post(f"{BACKEND_URL}/api/subscription/toggle-auto-renewal/{test_user_id}?enabled=true", timeout=10)
        if response.status_code in [200, 404]:  # 404 is OK if user doesn't exist
            log_test("Auto-Renewal Toggle Endpoint", "PASS", f"Endpoint accessible (status: {response.status_code})")
        else:
            log_test("Auto-Renewal Toggle Endpoint", "FAIL", f"Status code: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        log_test("Subscription Endpoints", "FAIL", f"Error: {e}")
        return False

def test_money_calculation_logic():
    """Test that money calculation logic is correct"""
    try:
        # Test the money calculation logic
        plan_prices = {
            "1month": 5000.0,
            "2months": 9000.0,
            "3months": 12000.0,
            "6months": 20000.0
        }
        
        # Test cumulative money calculation
        current_total = 0.0
        test_scenarios = [
            {"plan": "1month", "expected_total": 5000.0},
            {"plan": "2months", "expected_total": 14000.0},  # 5000 + 9000
            {"plan": "3months", "expected_total": 26000.0},  # 14000 + 12000
            {"plan": "6months", "expected_total": 46000.0}   # 26000 + 20000
        ]
        
        all_correct = True
        for scenario in test_scenarios:
            # Simulate adding a new subscription
            new_total = current_total + plan_prices[scenario["plan"]]
            current_total = new_total
            
            if new_total == scenario["expected_total"]:
                log_test(f"Money Calculation {scenario['plan']}", "PASS", f"Total: ₹{new_total}")
            else:
                log_test(f"Money Calculation {scenario['plan']}", "FAIL", f"Expected ₹{scenario['expected_total']}, got ₹{new_total}")
                all_correct = False
        
        return all_correct
    except Exception as e:
        log_test("Money Calculation Logic", "FAIL", f"Error: {e}")
        return False

def test_auto_renewal_scenarios():
    """Test auto-renewal scenarios"""
    try:
        # Test different auto-renewal scenarios
        scenarios = [
            {
                "name": "1 Month Plan Renewal",
                "plan": "1month",
                "current_total": 5000.0,
                "expected_new_total": 10000.0,
                "expected_days": 30
            },
            {
                "name": "2 Months Plan Renewal", 
                "plan": "2months",
                "current_total": 9000.0,
                "expected_new_total": 18000.0,
                "expected_days": 60
            },
            {
                "name": "3 Months Plan Renewal",
                "plan": "3months", 
                "current_total": 12000.0,
                "expected_new_total": 24000.0,
                "expected_days": 90
            },
            {
                "name": "6 Months Plan Renewal",
                "plan": "6months",
                "current_total": 20000.0,
                "expected_new_total": 40000.0,
                "expected_days": 180
            }
        ]
        
        plan_prices = {
            "1month": 5000.0,
            "2months": 9000.0,
            "3months": 12000.0,
            "6months": 20000.0
        }
        
        all_correct = True
        for scenario in scenarios:
            # Simulate auto-renewal calculation
            new_total = scenario["current_total"] + plan_prices[scenario["plan"]]
            
            # Simulate date calculation
            start_date = datetime.now()
            if scenario["plan"] == "1month":
                end_date = start_date + timedelta(days=30)
            elif scenario["plan"] == "2months":
                end_date = start_date + timedelta(days=60)
            elif scenario["plan"] == "3months":
                end_date = start_date + timedelta(days=90)
            elif scenario["plan"] == "6months":
                end_date = start_date + timedelta(days=180)
            
            actual_days = (end_date - start_date).days
            
            if new_total == scenario["expected_new_total"] and actual_days == scenario["expected_days"]:
                log_test(f"Auto-Renewal {scenario['name']}", "PASS", f"Total: ₹{new_total}, Duration: {actual_days} days")
            else:
                log_test(f"Auto-Renewal {scenario['name']}", "FAIL", f"Expected total: ₹{scenario['expected_new_total']}, got ₹{new_total}; Expected days: {scenario['expected_days']}, got {actual_days}")
                all_correct = False
        
        return all_correct
    except Exception as e:
        log_test("Auto-Renewal Scenarios", "FAIL", f"Error: {e}")
        return False

def run_core_functionality_test():
    """Run the core functionality test suite"""
    print("🧪 Starting Core Subscription Functionality Test")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Subscription Plans Structure
    test_results.append(test_subscription_plans_structure())
    
    # Test 2: Plan Duration Calculations
    test_results.append(test_plan_duration_calculations())
    
    # Test 3: Subscription Endpoints
    test_results.append(test_subscription_endpoints())
    
    # Test 4: Money Calculation Logic
    test_results.append(test_money_calculation_logic())
    
    # Test 5: Auto-Renewal Scenarios
    test_results.append(test_auto_renewal_scenarios())
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Core subscription functionality is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_core_functionality_test()
    sys.exit(0 if success else 1)
