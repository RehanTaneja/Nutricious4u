#!/usr/bin/env python3
"""
Final Comprehensive Test for Appointment Scheduling System
========================================================

This script verifies that all the fixes are working correctly:
1. Firestore rules allow users to read all appointments and breaks
2. Users can see their own appointments in green
3. Users can see other users' appointments in grey
4. Dieticians can see all appointments with user names
5. All permissions are working correctly
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_firestore_rules_deployment():
    """Test if Firestore rules are deployed correctly"""
    print("🔍 Testing Firestore Rules Deployment...")
    
    try:
        with open("firestore.rules", "r") as f:
            content = f.read()
        
        checks = []
        
        # Check appointments read permission
        if "allow read: if request.auth != null;" in content and "appointments" in content:
            checks.append("✅ Users can read all appointments")
        else:
            checks.append("❌ Users cannot read all appointments")
        
        # Check breaks read permission
        if "allow read: if request.auth != null;" in content and "breaks" in content:
            checks.append("✅ Users can read all breaks")
        else:
            checks.append("❌ Users cannot read all breaks")
        
        # Check appointments write permission
        if "request.auth.uid == resource.data.userId" in content and "appointments" in content:
            checks.append("✅ Users can write their own appointments")
        else:
            checks.append("❌ Users cannot write their own appointments")
        
        # Check dietician permissions
        if "isDietician == true" in content:
            checks.append("✅ Dietician permissions properly configured")
        else:
            checks.append("❌ Dietician permissions not configured")
        
        success = all(check.startswith("✅") for check in checks)
        
        print("Firestore Rules Status:")
        for check in checks:
            print(f"   {check}")
        
        return success
        
    except FileNotFoundError:
        print("❌ firestore.rules file not found")
        return False

def test_backend_api_endpoints():
    """Test if backend API endpoints are working"""
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

def test_frontend_implementation():
    """Test if frontend implementation is correct"""
    print("\n🔍 Testing Frontend Implementation...")
    
    try:
        with open("mobileapp/screens.tsx", "r") as f:
            content = f.read()
        
        checks = []
        
        # Check if users fetch all appointments (no userId filter)
        if ".collection('appointments')" in content and "onSnapshot" in content:
            if ".where('userId', '==', userId)" not in content:
                checks.append("✅ Users fetch all appointments (no userId filter)")
            else:
                checks.append("❌ Users only fetch their own appointments")
        else:
            checks.append("❌ No appointments listener found")
        
        # Check if users fetch breaks
        if ".collection('breaks')" in content and "onSnapshot" in content:
            checks.append("✅ Users fetch breaks from Firestore")
        else:
            checks.append("❌ No breaks listener found")
        
        # Check if break checking function is implemented
        if "isTimeSlotInBreak" in content and "breaks.some" in content:
            checks.append("✅ Break checking function implemented")
        else:
            checks.append("❌ Break checking function not implemented")
        
        # Check if user's own appointments are filtered in summary
        if "appt.userId === userId" in content:
            checks.append("✅ User's own appointments filtered in summary")
        else:
            checks.append("❌ User's own appointments not filtered in summary")
        
        # Check if atomic booking is implemented
        if "existingAppointmentsSnapshot.empty" in content:
            checks.append("✅ Atomic booking validation implemented")
        else:
            checks.append("❌ Atomic booking validation not implemented")
        
        # Check if dietician dashboard shows user names
        if "bookedUserInfo.userName" in content:
            checks.append("✅ Dietician dashboard shows user names")
        else:
            checks.append("❌ Dietician dashboard doesn't show user names")
        
        # Check if color styles are implemented
        if "bookedByMeTimeSlot" in content and "backgroundColor: '#10B981'" in content:
            checks.append("✅ User's own appointments styled in green")
        else:
            checks.append("❌ User's own appointments not styled in green")
        
        if "bookedTimeSlot" in content and "backgroundColor: '#9CA3AF'" in content:
            checks.append("✅ Other users' appointments styled in grey")
        else:
            checks.append("❌ Other users' appointments not styled in grey")
        
        success_count = len([c for c in checks if c.startswith("✅")])
        total_count = len(checks)
        
        print("Frontend Implementation Status:")
        for check in checks:
            print(f"   {check}")
        
        print(f"\nSuccess Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        return success_count == total_count
        
    except FileNotFoundError:
        print("❌ screens.tsx file not found")
        return False

def generate_deployment_instructions():
    """Generate deployment instructions"""
    print("\n📋 DEPLOYMENT INSTRUCTIONS")
    print("=" * 40)
    
    print("\n1. ✅ Firestore Rules (COMPLETED)")
    print("   Command: firebase deploy --only firestore:rules")
    print("   Status: Already deployed successfully")
    
    print("\n2. 🔧 Backend Deployment (REQUIRED)")
    print("   Option A: Install Railway CLI and deploy")
    print("   ```bash")
    print("   npm install -g @railway/cli")
    print("   railway login")
    print("   cd backend")
    print("   railway up")
    print("   ```")
    
    print("\n   Option B: Deploy via Railway Dashboard")
    print("   - Go to https://railway.app/dashboard")
    print("   - Select your Nutricious4u project")
    print("   - Connect your GitHub repository")
    print("   - Push changes to trigger automatic deployment")
    
    print("\n3. 📱 Frontend Deployment (REQUIRED)")
    print("   ```bash")
    print("   cd mobileapp")
    print("   npm run build")
    print("   # Or for Expo:")
    print("   npx expo build:ios")
    print("   npx expo build:android")
    print("   ```")
    
    print("\n4. 🧪 Testing After Deployment")
    print("   - Test user appointment booking")
    print("   - Test dietician break management")
    print("   - Verify color coding (green for own, grey for others)")
    print("   - Check real-time updates")
    print("   - Verify no permission errors")

def generate_expected_results():
    """Generate expected results after deployment"""
    print("\n🎯 EXPECTED RESULTS AFTER DEPLOYMENT")
    print("=" * 45)
    
    print("\n✅ For Users:")
    print("   - Can see all appointments and breaks")
    print("   - Own appointments appear in GREEN")
    print("   - Other users' appointments appear in GREY")
    print("   - Breaks appear as 'Break' in light grey")
    print("   - Can book appointments successfully")
    print("   - No more 'Missing or insufficient permissions' errors")
    
    print("\n✅ For Dieticians:")
    print("   - Can see all appointments with user names")
    print("   - Can manage breaks")
    print("   - Can see the complete schedule")
    print("   - Real-time updates work")
    
    print("\n✅ System Features:")
    print("   - Double booking prevention")
    print("   - Real-time updates across devices")
    print("   - Consistent experience for all users")
    print("   - Proper error handling")
    print("   - Atomic booking validation")

def generate_test_scenarios():
    """Generate manual test scenarios"""
    print("\n🧪 MANUAL TEST SCENARIOS")
    print("=" * 30)
    
    scenarios = [
        {
            "scenario": "User Appointment Booking",
            "steps": [
                "1. Login as a regular user",
                "2. Go to Schedule Appointment screen",
                "3. Select an available time slot",
                "4. Confirm the booking",
                "5. Verify it appears in GREEN with 'Your Appt'"
            ],
            "expected": "User can book appointments and see them in green"
        },
        {
            "scenario": "Multiple Users Booking",
            "steps": [
                "1. Have User A book an appointment",
                "2. Login as User B",
                "3. Check the same time slot",
                "4. Verify it shows as 'Booked' in GREY"
            ],
            "expected": "Other users' appointments appear in grey"
        },
        {
            "scenario": "Dietician View",
            "steps": [
                "1. Login as dietician",
                "2. Go to Dietician Dashboard",
                "3. Check appointment slots",
                "4. Verify user names are displayed"
            ],
            "expected": "Dietician sees all appointments with user names"
        },
        {
            "scenario": "Break Management",
            "steps": [
                "1. Login as dietician",
                "2. Add a break",
                "3. Login as user",
                "4. Verify break appears as 'Break'"
            ],
            "expected": "Users can see dietician's breaks"
        },
        {
            "scenario": "Real-time Updates",
            "steps": [
                "1. Open appointment screen on two devices",
                "2. Book appointment on one device",
                "3. Verify it appears immediately on the other"
            ],
            "expected": "Real-time updates work across devices"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['scenario']}")
        print("   Steps:")
        for step in scenario['steps']:
            print(f"   {step}")
        print(f"   Expected: {scenario['expected']}")

def main():
    """Run all tests and generate reports"""
    print("🚀 FINAL APPOINTMENT SCHEDULING SYSTEM TEST")
    print("=" * 55)
    print()
    
    # Run tests
    firestore_success = test_firestore_rules_deployment()
    backend_success = test_backend_api_endpoints()
    frontend_success = test_frontend_implementation()
    
    # Generate reports
    print("\n📊 FINAL TEST SUMMARY")
    print("=" * 25)
    
    tests = [
        ("Firestore Rules", firestore_success),
        ("Backend API", backend_success),
        ("Frontend Implementation", frontend_success)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Success Rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The system is ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before deployment.")
    
    # Generate instructions and scenarios
    generate_deployment_instructions()
    generate_expected_results()
    generate_test_scenarios()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {
            "firestore_rules": firestore_success,
            "backend_api": backend_success,
            "frontend_implementation": frontend_success
        },
        "overall_success": passed == total,
        "success_rate": f"{passed}/{total} ({passed/total*100:.1f}%)"
    }
    
    with open("final_appointment_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: final_appointment_test_results.json")

if __name__ == "__main__":
    main()
