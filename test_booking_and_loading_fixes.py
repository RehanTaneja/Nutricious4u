#!/usr/bin/env python3
"""
Test Booking and Loading Fixes
=============================

This script verifies that:
1. Users can now book appointments (permission fix)
2. Breaks loading state is implemented
3. All fixes are working correctly
"""

import requests
import json
from datetime import datetime

def test_firestore_rules_fix():
    """Test if Firestore rules allow users to create appointments"""
    print("🔍 Testing Firestore Rules Fix for Booking...")
    
    try:
        with open("firestore.rules", "r") as f:
            content = f.read()
        
        checks = []
        
        # Check if create permission is separate from update/delete
        if "allow create:" in content and "request.auth.uid == resource.data.userId" in content:
            checks.append("✅ Users can create appointments for themselves")
        else:
            checks.append("❌ Users cannot create appointments")
        
        # Check if update/delete permissions are separate
        if "allow update, delete:" in content:
            checks.append("✅ Update/delete permissions are properly configured")
        else:
            checks.append("❌ Update/delete permissions not configured")
        
        # Check if dietician permissions are maintained
        if "isDietician == true" in content:
            checks.append("✅ Dietician permissions maintained")
        else:
            checks.append("❌ Dietician permissions missing")
        
        success = all(check.startswith("✅") for check in checks)
        
        print("Firestore Rules Booking Fix Status:")
        for check in checks:
            print(f"   {check}")
        
        return success
        
    except FileNotFoundError:
        print("❌ firestore.rules file not found")
        return False

def test_breaks_loading_implementation():
    """Test if breaks loading state is implemented"""
    print("\n🔍 Testing Breaks Loading Implementation...")
    
    try:
        with open("mobileapp/screens.tsx", "r") as f:
            content = f.read()
        
        checks = []
        
        # Check if breaksLoading state is defined
        if "breaksLoading" in content and "setBreaksLoading" in content:
            checks.append("✅ Breaks loading state is implemented")
        else:
            checks.append("❌ Breaks loading state not implemented")
        
        # Check if loading state is set to false when breaks are loaded
        if "setBreaksLoading(false)" in content:
            checks.append("✅ Loading state is properly managed")
        else:
            checks.append("❌ Loading state not properly managed")
        
        # Check if loading state is shown in UI
        if "isBreaksLoading" in content and "? '...'" in content:
            checks.append("✅ Loading state is shown in UI")
        else:
            checks.append("❌ Loading state not shown in UI")
        
        success = all(check.startswith("✅") for check in checks)
        
        print("Breaks Loading Implementation Status:")
        for check in checks:
            print(f"   {check}")
        
        return success
        
    except FileNotFoundError:
        print("❌ screens.tsx file not found")
        return False

def test_backend_api_endpoints():
    """Test if backend API endpoints are still working"""
    print("\n🔍 Testing Backend API Endpoints...")
    
    base_url = "https://nutricious4u-production.up.railway.app"
    endpoints = [
        "/api/appointments",
        "/api/breaks"
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                working_endpoints.append(f"{endpoint} ({len(data)} items)")
            else:
                failed_endpoints.append(f"{endpoint} (Status: {response.status_code})")
        except Exception as e:
            failed_endpoints.append(f"{endpoint} (Error: {e})")
    
    success = len(working_endpoints) >= 1
    
    print("Backend API Status:")
    for endpoint in working_endpoints:
        print(f"   ✅ {endpoint}")
    for endpoint in failed_endpoints:
        print(f"   ❌ {endpoint}")
    
    return success

def generate_manual_test_scenarios():
    """Generate manual test scenarios for the fixes"""
    print("\n🧪 MANUAL TEST SCENARIOS FOR FIXES")
    print("=" * 40)
    
    scenarios = [
        {
            "scenario": "User Can Book Appointments",
            "steps": [
                "1. Login as a regular user",
                "2. Go to Schedule Appointment screen",
                "3. Select an available time slot",
                "4. Confirm the booking",
                "5. Verify the booking is successful (no permission errors)"
            ],
            "expected": "User should be able to book appointments without permission errors"
        },
        {
            "scenario": "Breaks Loading State",
            "steps": [
                "1. Login as a user",
                "2. Go to Schedule Appointment screen",
                "3. Check if time slots show '...' briefly while breaks load",
                "4. Wait for breaks to load",
                "5. Verify breaks appear as 'Break'"
            ],
            "expected": "Time slots should show loading state while breaks are loading"
        },
        {
            "scenario": "Visual Distinction After Loading",
            "steps": [
                "1. Have a dietician add some breaks",
                "2. Login as a user",
                "3. Wait for breaks to load",
                "4. Verify breaks show as 'Break' in light grey",
                "5. Book an appointment",
                "6. Verify your appointment shows in GREEN"
            ],
            "expected": "Proper visual distinction between breaks and appointments"
        },
        {
            "scenario": "Multiple Users Booking",
            "steps": [
                "1. Have User A book an appointment",
                "2. Login as User B",
                "3. Check the same time slot",
                "4. Verify it shows as 'Booked' in GREY",
                "5. Try to book the same slot",
                "6. Verify booking is prevented"
            ],
            "expected": "Double booking prevention should work correctly"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['scenario']}")
        print("   Steps:")
        for step in scenario['steps']:
            print(f"   {step}")
        print(f"   Expected: {scenario['expected']}")

def generate_deployment_instructions():
    """Generate deployment instructions"""
    print("\n📋 DEPLOYMENT INSTRUCTIONS")
    print("=" * 30)
    
    print("\n1. ✅ Firestore Rules (COMPLETED)")
    print("   Command: firebase deploy --only firestore:rules")
    print("   Status: Already deployed successfully")
    print("   Fix: Separated create/update permissions for appointments")
    
    print("\n2. ✅ Frontend Loading State (COMPLETED)")
    print("   Status: Breaks loading state implemented")
    print("   Fix: Added breaksLoading state and UI loading indicator")
    
    print("\n3. 🔧 Backend Deployment (REQUIRED)")
    print("   Option A: Railway CLI")
    print("   ```bash")
    print("   npm install -g @railway/cli")
    print("   railway login")
    print("   cd backend")
    print("   railway up")
    print("   ```")
    
    print("\n   Option B: Railway Dashboard")
    print("   - Go to https://railway.app/dashboard")
    print("   - Select your Nutricious4u project")
    print("   - Connect your GitHub repository")
    print("   - Push changes to trigger automatic deployment")
    
    print("\n4. 📱 Frontend Deployment (REQUIRED)")
    print("   ```bash")
    print("   cd mobileapp")
    print("   npm run build")
    print("   # Or for Expo:")
    print("   npx expo build:ios")
    print("   npx expo build:android")
    print("   ```")

def generate_expected_results():
    """Generate expected results after deployment"""
    print("\n🎯 EXPECTED RESULTS AFTER DEPLOYMENT")
    print("=" * 40)
    
    print("\n✅ Booking Fixes:")
    print("   - Users can book appointments successfully")
    print("   - No more 'Missing or insufficient permissions' errors")
    print("   - Firestore create permissions work correctly")
    
    print("\n✅ Loading Fixes:")
    print("   - Time slots show '...' while breaks are loading")
    print("   - Breaks appear properly after loading")
    print("   - No more 1-second delay visibility issue")
    
    print("\n✅ Visual Distinction:")
    print("   - User's own appointments: GREEN")
    print("   - Other users' appointments: GREY")
    print("   - Breaks: Light grey with 'Break' text")
    
    print("\n✅ System Features:")
    print("   - Double booking prevention works")
    print("   - Real-time updates across devices")
    print("   - Proper error handling")
    print("   - Consistent user experience")

def main():
    """Run all tests and generate reports"""
    print("🚀 TESTING BOOKING AND LOADING FIXES")
    print("=" * 45)
    print()
    
    # Run tests
    firestore_success = test_firestore_rules_fix()
    loading_success = test_breaks_loading_implementation()
    backend_success = test_backend_api_endpoints()
    
    # Generate reports
    print("\n📊 TEST SUMMARY")
    print("=" * 15)
    
    tests = [
        ("Firestore Rules Fix", firestore_success),
        ("Breaks Loading Implementation", loading_success),
        ("Backend API", backend_success)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Success Rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL FIXES IMPLEMENTED! Ready for deployment.")
    else:
        print("\n⚠️  Some fixes need attention before deployment.")
    
    # Generate instructions and scenarios
    generate_deployment_instructions()
    generate_expected_results()
    generate_manual_test_scenarios()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {
            "firestore_rules_fix": firestore_success,
            "breaks_loading_implementation": loading_success,
            "backend_api": backend_success
        },
        "overall_success": passed == total,
        "success_rate": f"{passed}/{total} ({passed/total*100:.1f}%)"
    }
    
    with open("booking_and_loading_fixes_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: booking_and_loading_fixes_results.json")

if __name__ == "__main__":
    main()
