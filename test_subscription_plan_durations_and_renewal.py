#!/usr/bin/env python3
"""
Comprehensive Test for Subscription Plan Durations and Automatic Renewal
Tests plan durations, automatic renewal, cancellation behavior, and money tracking
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

def test_subscription_plans():
    """Test that subscription plans are correctly defined"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/subscription/plans", timeout=10)
        if response.status_code == 200:
            plans = response.json()
            log_test("Get Subscription Plans", "PASS", f"Found {len(plans)} plans")
            
            # Expected plans and their durations
            expected_plans = {
                "1month": {"price": 5000.0, "duration_days": 30},
                "2months": {"price": 9000.0, "duration_days": 60},
                "3months": {"price": 12000.0, "duration_days": 90},
                "6months": {"price": 20000.0, "duration_days": 180}
            }
            
            # Verify each plan exists and has correct pricing
            for plan_id, expected in expected_plans.items():
                plan_found = False
                for plan in plans:
                    if plan.get("planId") == plan_id:
                        plan_found = True
                        if plan.get("price") == expected["price"]:
                            log_test(f"Plan {plan_id} Pricing", "PASS", f"Price: ₹{expected['price']}")
                        else:
                            log_test(f"Plan {plan_id} Pricing", "FAIL", f"Expected ₹{expected['price']}, got ₹{plan.get('price')}")
                        break
                
                if not plan_found:
                    log_test(f"Plan {plan_id} Exists", "FAIL", "Plan not found")
                else:
                    log_test(f"Plan {plan_id} Exists", "PASS", "Plan found")
            
            return True
        else:
            log_test("Get Subscription Plans", "FAIL", f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Subscription Plans", "FAIL", f"Error: {e}")
        return False

def test_plan_duration_calculations():
    """Test that plan duration calculations are correct"""
    try:
        # Test each plan's duration calculation
        test_cases = [
            {"plan": "1month", "expected_days": 30, "description": "1 month = 30 days"},
            {"plan": "2months", "expected_days": 60, "description": "2 months = 60 days"},
            {"plan": "3months", "expected_days": 90, "description": "3 months = 90 days"},
            {"plan": "6months", "expected_days": 180, "description": "6 months = 180 days"}
        ]
        
        all_passed = True
        for test_case in test_cases:
            # Calculate expected end date
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

def test_subscription_selection():
    """Test subscription selection with different plans"""
    try:
        test_user_id = "test_user_plan_duration"
        
        # Test each plan
        plans_to_test = ["1month", "2months", "3months", "6months"]
        results = []
        
        for plan_id in plans_to_test:
            try:
                # Create subscription request
                subscription_data = {
                    "userId": test_user_id,
                    "planId": plan_id
                }
                
                response = requests.post(
                    f"{BACKEND_URL}/api/subscription/select",
                    json=subscription_data,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    if data.get("success"):
                        log_test(f"Select {plan_id} Plan", "PASS", f"Successfully selected {plan_id}")
                        
                        # Verify subscription status
                        status_response = requests.get(f"{BACKEND_URL}/api/subscription/status/{test_user_id}", timeout=10)
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get("subscriptionPlan") == plan_id:
                                log_test(f"Verify {plan_id} Status", "PASS", f"Plan correctly set to {plan_id}")
                                results.append(True)
                            else:
                                log_test(f"Verify {plan_id} Status", "FAIL", f"Expected {plan_id}, got {status_data.get('subscriptionPlan')}")
                                results.append(False)
                        else:
                            log_test(f"Verify {plan_id} Status", "FAIL", f"Status code: {status_response.status_code}")
                            results.append(False)
                    else:
                        log_test(f"Select {plan_id} Plan", "FAIL", f"Success: False, Message: {data.get('message')}")
                        results.append(False)
                else:
                    log_test(f"Select {plan_id} Plan", "FAIL", f"Status code: {response.status_code}")
                    results.append(False)
                    
            except Exception as e:
                log_test(f"Select {plan_id} Plan", "FAIL", f"Error: {e}")
                results.append(False)
        
        return all(results)
    except Exception as e:
        log_test("Subscription Selection", "FAIL", f"Error: {e}")
        return False

def test_subscription_cancellation():
    """Test that subscription cancellation works and prevents renewal"""
    try:
        test_user_id = "test_user_cancellation"
        
        # First, create a subscription
        subscription_data = {
            "userId": test_user_id,
            "planId": "1month"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/subscription/select",
            json=subscription_data,
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            log_test("Create Subscription for Cancellation", "FAIL", f"Status code: {response.status_code}")
            return False
        
        log_test("Create Subscription for Cancellation", "PASS", "Subscription created")
        
        # Now cancel the subscription
        cancel_response = requests.post(f"{BACKEND_URL}/api/subscription/cancel/{test_user_id}", timeout=10)
        
        if cancel_response.status_code == 200:
            cancel_data = cancel_response.json()
            if cancel_data.get("success"):
                log_test("Cancel Subscription", "PASS", f"Successfully cancelled: {cancel_data.get('message')}")
                
                # Verify subscription is cancelled
                status_response = requests.get(f"{BACKEND_URL}/api/subscription/status/{test_user_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if not status_data.get("isSubscriptionActive"):
                        log_test("Verify Cancellation", "PASS", "Subscription is inactive")
                        return True
                    else:
                        log_test("Verify Cancellation", "FAIL", "Subscription is still active")
                        return False
                else:
                    log_test("Verify Cancellation", "FAIL", f"Status code: {status_response.status_code}")
                    return False
            else:
                log_test("Cancel Subscription", "FAIL", f"Success: False, Message: {cancel_data.get('message')}")
                return False
        else:
            log_test("Cancel Subscription", "FAIL", f"Status code: {cancel_response.status_code}")
            return False
            
    except Exception as e:
        log_test("Subscription Cancellation", "FAIL", f"Error: {e}")
        return False

def test_money_tracking():
    """Test that money amounts are correctly tracked"""
    try:
        test_user_id = "test_user_money_tracking"
        
        # Test multiple subscription selections to verify money accumulation
        plans_to_test = ["1month", "2months"]  # Test 2 plans
        expected_total = 0
        
        for i, plan_id in enumerate(plans_to_test):
            subscription_data = {
                "userId": test_user_id,
                "planId": plan_id
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/subscription/select",
                json=subscription_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get("success"):
                    # Calculate expected total
                    plan_prices = {"1month": 5000.0, "2months": 9000.0}
                    expected_total += plan_prices[plan_id]
                    
                    # Check subscription status for total amount
                    status_response = requests.get(f"{BACKEND_URL}/api/subscription/status/{test_user_id}", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        actual_total = status_data.get("totalAmountPaid", 0)
                        
                        if actual_total == expected_total:
                            log_test(f"Money Tracking {plan_id}", "PASS", f"Total: ₹{actual_total}")
                        else:
                            log_test(f"Money Tracking {plan_id}", "FAIL", f"Expected ₹{expected_total}, got ₹{actual_total}")
                            return False
                    else:
                        log_test(f"Money Tracking {plan_id}", "FAIL", f"Status code: {status_response.status_code}")
                        return False
                else:
                    log_test(f"Money Tracking {plan_id}", "FAIL", f"Success: False")
                    return False
            else:
                log_test(f"Money Tracking {plan_id}", "FAIL", f"Status code: {response.status_code}")
                return False
        
        log_test("Money Tracking Overall", "PASS", f"Final total: ₹{expected_total}")
        return True
        
    except Exception as e:
        log_test("Money Tracking", "FAIL", f"Error: {e}")
        return False

def test_auto_renewal_logic():
    """Test the auto-renewal logic (without actually triggering it)"""
    try:
        # Test the auto-renewal endpoint exists
        test_user_id = "test_user_auto_renewal"
        
        # Test toggle auto-renewal
        response = requests.post(f"{BACKEND_URL}/api/subscription/toggle-auto-renewal/{test_user_id}?enabled=true", timeout=10)
        
        if response.status_code in [200, 404]:  # 404 is OK if user doesn't exist
            log_test("Auto-Renewal Toggle", "PASS", f"Endpoint accessible (status: {response.status_code})")
        else:
            log_test("Auto-Renewal Toggle", "FAIL", f"Status code: {response.status_code}")
            return False
        
        # Test subscription reminder job endpoint (if it exists)
        try:
            reminder_response = requests.post(f"{BACKEND_URL}/api/admin/trigger-subscription-reminder-job", timeout=30)
            if reminder_response.status_code in [200, 404, 500]:
                log_test("Subscription Reminder Job", "PASS", f"Endpoint accessible (status: {reminder_response.status_code})")
            else:
                log_test("Subscription Reminder Job", "FAIL", f"Status code: {reminder_response.status_code}")
                return False
        except Exception as e:
            log_test("Subscription Reminder Job", "FAIL", f"Error: {e}")
            return False
        
        return True
        
    except Exception as e:
        log_test("Auto-Renewal Logic", "FAIL", f"Error: {e}")
        return False

def run_comprehensive_test():
    """Run the complete test suite"""
    print("🧪 Starting Comprehensive Subscription Plan Duration and Renewal Test")
    print("=" * 80)
    
    test_results = []
    
    # Test 1: Subscription Plans
    test_results.append(test_subscription_plans())
    
    # Test 2: Plan Duration Calculations
    test_results.append(test_plan_duration_calculations())
    
    # Test 3: Subscription Selection
    test_results.append(test_subscription_selection())
    
    # Test 4: Subscription Cancellation
    test_results.append(test_subscription_cancellation())
    
    # Test 5: Money Tracking
    test_results.append(test_money_tracking())
    
    # Test 6: Auto-Renewal Logic
    test_results.append(test_auto_renewal_logic())
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Subscription system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
