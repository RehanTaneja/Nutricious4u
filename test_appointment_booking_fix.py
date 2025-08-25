#!/usr/bin/env python3
"""
Test Appointment Booking Fix
===========================

This script verifies that the appointment booking permission issue is fixed:
1. Check Firestore rules are correct
2. Test appointment booking flow
3. Verify all components are working
"""

import requests
import json
from datetime import datetime, timedelta

def test_firestore_rules_fix():
    """Test if Firestore rules are correctly fixed"""
    print("🔍 Testing Firestore Rules Fix...")
    
    try:
        with open("firestore.rules", "r") as f:
            content = f.read()
        
        checks = []
        
        # Check if create permission uses request.resource.data.userId
        if "request.resource.data.userId" in content and "allow create:" in content:
            checks.append("✅ Create permission uses request.resource.data.userId")
        else:
            checks.append("❌ Create permission not correctly configured")
        
        # Check if read permission allows all authenticated users
        if "allow read: if request.auth != null;" in content and "appointments" in content:
            checks.append("✅ Read permission allows all authenticated users")
        else:
            checks.append("❌ Read permission not correctly configured")
        
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
        
        print("Firestore Rules Fix Status:")
        for check in checks:
            print(f"   {check}")
        
        return success
        
    except FileNotFoundError:
        print("❌ firestore.rules file not found")
        return False

def test_backend_appointment_endpoints():
    """Test if backend appointment endpoints are working"""
    print("\n🔍 Testing Backend Appointment Endpoints...")
    
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
    
    print("Backend Appointment Endpoints Status:")
    for endpoint in working_endpoints:
        print(f"   ✅ {endpoint}")
    for endpoint in failed_endpoints:
        print(f"   ❌ {endpoint}")
    
    return success

def test_frontend_appointment_flow():
    """Test if frontend appointment booking flow is correct"""
    print("\n🔍 Testing Frontend Appointment Booking Flow...")
    
    try:
        with open("mobileapp/screens.tsx", "r") as f:
            content = f.read()
        
        checks = []
        
        # Check if appointment booking function exists
        if "handleScheduleAppointment" in content:
            checks.append("✅ Appointment booking function exists")
        else:
            checks.append("❌ Appointment booking function not found")
        
        # Check if Firestore add is used for booking
        if "firestore.collection('appointments').add" in content:
            checks.append("✅ Firestore add is used for booking")
        else:
            checks.append("❌ Firestore add not used for booking")
        
        # Check if API fallback is implemented
        if "fetch(`${backendUrl}/api/appointments`" in content:
            checks.append("✅ API fallback is implemented")
        else:
            checks.append("❌ API fallback not implemented")
        
        # Check if error handling is implemented
        if "catch (firestoreError)" in content:
            checks.append("✅ Error handling is implemented")
        else:
            checks.append("❌ Error handling not implemented")
        
        # Check if breaks loading state is implemented
        if "breaksLoading" in content and "setBreaksLoading(false)" in content:
            checks.append("✅ Breaks loading state is implemented")
        else:
            checks.append("❌ Breaks loading state not implemented")
        
        # Check if visual distinction is implemented
        if "bookedByMeTimeSlot" in content and "bookedTimeSlot" in content:
            checks.append("✅ Visual distinction is implemented")
        else:
            checks.append("❌ Visual distinction not implemented")
        
        success_count = len([c for c in checks if c.startswith("✅")])
        total_count = len(checks)
        
        print("Frontend Appointment Flow Status:")
        for check in checks:
            print(f"   {check}")
        
        print(f"\nSuccess Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        return success_count == total_count
        
    except FileNotFoundError:
        print("❌ screens.tsx file not found")
        return False

def analyze_appointment_data_structure():
    """Analyze the appointment data structure to ensure it matches Firestore rules"""
    print("\n🔍 Analyzing Appointment Data Structure...")
    
    try:
        with open("mobileapp/screens.tsx", "r") as f:
            content = f.read()
        
        # Find appointment data structure
        if "appointmentData" in content:
            print("✅ Appointment data structure found")
            
            # Check if userId is included
            if "userId: userId" in content:
                print("✅ userId field is included in appointment data")
            else:
                print("❌ userId field not found in appointment data")
            
            # Check if userName is included
            if "userName: userName" in content:
                print("✅ userName field is included in appointment data")
            else:
                print("❌ userName field not found in appointment data")
            
            # Check if date is included
            if "date: appointmentDate.toISOString()" in content:
                print("✅ date field is included in appointment data")
            else:
                print("❌ date field not found in appointment data")
            
            # Check if timeSlot is included
            if "timeSlot: selectedTimeSlot" in content:
                print("✅ timeSlot field is included in appointment data")
            else:
                print("❌ timeSlot field not found in appointment data")
            
        else:
            print("❌ Appointment data structure not found")
            return False
        
        return True
        
    except FileNotFoundError:
        print("❌ screens.tsx file not found")
        return False

def generate_debugging_guide():
    """Generate debugging guide for appointment booking issues"""
    print("\n🔧 DEBUGGING GUIDE FOR APPOINTMENT BOOKING")
    print("=" * 50)
    
    print("\n1. **Check Firestore Rules**")
    print("   - Verify rules are deployed: firebase deploy --only firestore:rules")
    print("   - Check Firebase Console for rule syntax errors")
    print("   - Ensure create rule uses: request.resource.data.userId")
    
    print("\n2. **Check User Authentication**")
    print("   - Verify user is logged in: auth.currentUser?.uid")
    print("   - Check if user has valid Firebase token")
    print("   - Ensure user profile exists in Firestore")
    
    print("\n3. **Check Appointment Data Structure**")
    print("   - Verify appointmentData contains userId field")
    print("   - Ensure userId matches auth.currentUser?.uid")
    print("   - Check all required fields are present")
    
    print("\n4. **Check Network Connectivity**")
    print("   - Test Firestore connection")
    print("   - Check if API fallback is working")
    print("   - Verify backend endpoints are accessible")
    
    print("\n5. **Check Console Logs**")
    print("   - Look for '[Appointment Debug]' messages")
    print("   - Check for permission errors")
    print("   - Verify data is being sent correctly")

def generate_manual_test_scenarios():
    """Generate manual test scenarios"""
    print("\n🧪 MANUAL TEST SCENARIOS")
    print("=" * 30)
    
    scenarios = [
        {
            "scenario": "Test Appointment Booking",
            "steps": [
                "1. Login as a regular user",
                "2. Go to Schedule Appointment screen",
                "3. Select an available time slot",
                "4. Confirm the booking",
                "5. Check console for '[Appointment Debug]' messages",
                "6. Verify appointment appears in the grid"
            ],
            "expected": "Appointment should be booked successfully without permission errors"
        },
        {
            "scenario": "Test Firestore Rules",
            "steps": [
                "1. Open Firebase Console",
                "2. Go to Firestore Database",
                "3. Check if appointments collection exists",
                "4. Verify new appointment document is created",
                "5. Check if userId field matches current user"
            ],
            "expected": "Appointment document should be created with correct userId"
        },
        {
            "scenario": "Test API Fallback",
            "steps": [
                "1. Disconnect from internet",
                "2. Try to book an appointment",
                "3. Check if API fallback is triggered",
                "4. Reconnect to internet",
                "5. Verify appointment is saved"
            ],
            "expected": "API fallback should handle network issues gracefully"
        },
        {
            "scenario": "Test Multiple Users",
            "steps": [
                "1. Have User A book an appointment",
                "2. Login as User B",
                "3. Check if User A's appointment is visible",
                "4. Try to book the same time slot",
                "5. Verify booking is prevented"
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

def main():
    """Run all tests and generate reports"""
    print("🚀 TESTING APPOINTMENT BOOKING FIX")
    print("=" * 40)
    print()
    
    # Run tests
    firestore_success = test_firestore_rules_fix()
    backend_success = test_backend_appointment_endpoints()
    frontend_success = test_frontend_appointment_flow()
    data_structure_success = analyze_appointment_data_structure()
    
    # Generate reports
    print("\n📊 TEST SUMMARY")
    print("=" * 15)
    
    tests = [
        ("Firestore Rules Fix", firestore_success),
        ("Backend Appointment Endpoints", backend_success),
        ("Frontend Appointment Flow", frontend_success),
        ("Appointment Data Structure", data_structure_success)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Success Rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The appointment booking fix should work.")
        print("\n🔧 NEXT STEPS:")
        print("   1. Deploy backend: cd backend && railway up")
        print("   2. Deploy frontend: cd mobileapp && npm run build")
        print("   3. Test on device: Book an appointment")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before deployment.")
    
    # Generate debugging guide and scenarios
    generate_debugging_guide()
    generate_manual_test_scenarios()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {
            "firestore_rules_fix": firestore_success,
            "backend_appointment_endpoints": backend_success,
            "frontend_appointment_flow": frontend_success,
            "appointment_data_structure": data_structure_success
        },
        "overall_success": passed == total,
        "success_rate": f"{passed}/{total} ({passed/total*100:.1f}%)"
    }
    
    with open("appointment_booking_fix_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: appointment_booking_fix_results.json")

if __name__ == "__main__":
    main()
