#!/usr/bin/env python3
"""
Test Appointment Permission Debug
================================

This script helps debug the appointment permission issue by analyzing
the code and providing specific debugging steps.
"""

import json
from datetime import datetime

def analyze_appointment_booking_flow():
    """Analyze the appointment booking flow for potential issues"""
    print("🔍 Analyzing Appointment Booking Flow...")
    
    try:
        with open("mobileapp/screens.tsx", "r") as f:
            content = f.read()
        
        issues = []
        checks = []
        
        # Check appointment data structure
        if "appointmentData = {" in content:
            checks.append("✅ Appointment data structure found")
            
            # Check if userId is correctly set
            if "userId: userId" in content:
                checks.append("✅ userId field is set correctly")
            else:
                issues.append("❌ userId field may not be set correctly")
            
            # Check if userName is set
            if "userName: userName" in content:
                checks.append("✅ userName field is set")
            else:
                issues.append("❌ userName field may be missing")
            
            # Check if date is in ISO format
            if "appointmentDate.toISOString()" in content:
                checks.append("✅ Date is in ISO format")
            else:
                issues.append("❌ Date may not be in ISO format")
        else:
            issues.append("❌ Appointment data structure not found")
        
        # Check Firestore add call
        if "firestore.collection('appointments').add" in content:
            checks.append("✅ Firestore add call is present")
        else:
            issues.append("❌ Firestore add call not found")
        
        # Check error handling
        if "catch (firestoreError)" in content:
            checks.append("✅ Error handling is implemented")
        else:
            issues.append("❌ Error handling may be missing")
        
        # Check API fallback
        if "fetch(`${backendUrl}/api/appointments`" in content:
            checks.append("✅ API fallback is implemented")
        else:
            issues.append("❌ API fallback may be missing")
        
        # Check user authentication
        if "auth.currentUser?.uid" in content:
            checks.append("✅ User authentication check is present")
        else:
            issues.append("❌ User authentication check may be missing")
        
        print("Appointment Booking Flow Analysis:")
        for check in checks:
            print(f"   {check}")
        for issue in issues:
            print(f"   {issue}")
        
        return len(issues) == 0
        
    except FileNotFoundError:
        print("❌ screens.tsx file not found")
        return False

def analyze_firestore_rules():
    """Analyze Firestore rules for potential issues"""
    print("\n🔍 Analyzing Firestore Rules...")
    
    try:
        with open("firestore.rules", "r") as f:
            content = f.read()
        
        issues = []
        checks = []
        
        # Check if create permission uses request.resource.data.userId
        if "request.resource.data.userId" in content:
            checks.append("✅ Create permission uses request.resource.data.userId")
        else:
            issues.append("❌ Create permission may not use request.resource.data.userId")
        
        # Check if read permission allows authenticated users
        if "allow read: if request.auth != null;" in content:
            checks.append("✅ Read permission allows authenticated users")
        else:
            issues.append("❌ Read permission may not allow authenticated users")
        
        # Check if update/delete permissions are separate
        if "allow update, delete:" in content:
            checks.append("✅ Update/delete permissions are separate")
        else:
            issues.append("❌ Update/delete permissions may not be separate")
        
        # Check if dietician permissions are maintained
        if "isDietician == true" in content:
            checks.append("✅ Dietician permissions are maintained")
        else:
            issues.append("❌ Dietician permissions may be missing")
        
        print("Firestore Rules Analysis:")
        for check in checks:
            print(f"   {check}")
        for issue in issues:
            print(f"   {issue}")
        
        return len(issues) == 0
        
    except FileNotFoundError:
        print("❌ firestore.rules file not found")
        return False

def generate_specific_debugging_steps():
    """Generate specific debugging steps for the permission issue"""
    print("\n🔧 SPECIFIC DEBUGGING STEPS FOR PERMISSION ISSUE")
    print("=" * 55)
    
    print("\n1. **Immediate Checks**")
    print("   - Check if user is logged in: console.log(auth.currentUser?.uid)")
    print("   - Verify appointmentData structure: console.log(appointmentData)")
    print("   - Check if userId matches: console.log('userId:', userId, 'auth.uid:', auth.currentUser?.uid)")
    
    print("\n2. **Firestore Rules Verification**")
    print("   - Open Firebase Console > Firestore > Rules")
    print("   - Verify the deployed rules match firestore.rules file")
    print("   - Check if rules contain: request.resource.data.userId")
    print("   - Rules may take 1-2 minutes to propagate")
    
    print("\n3. **Network and Authentication**")
    print("   - Check if user has valid Firebase token")
    print("   - Verify user profile exists in Firestore")
    print("   - Test Firestore connection in console")
    
    print("\n4. **Data Structure Validation**")
    print("   - Ensure appointmentData contains all required fields:")
    print("     * userId (string)")
    print("     * userName (string)")
    print("     * userEmail (string)")
    print("     * date (ISO string)")
    print("     * timeSlot (string)")
    print("     * status (string)")
    print("     * createdAt (ISO string)")
    
    print("\n5. **Console Debugging**")
    print("   - Add these console.log statements to handleScheduleAppointment:")
    print("     console.log('[DEBUG] User ID:', userId)")
    print("     console.log('[DEBUG] Auth UID:', auth.currentUser?.uid)")
    print("     console.log('[DEBUG] Appointment Data:', appointmentData)")
    print("     console.log('[DEBUG] User authenticated:', !!auth.currentUser)")

def generate_test_scenarios():
    """Generate test scenarios to verify the fix"""
    print("\n🧪 TEST SCENARIOS TO VERIFY FIX")
    print("=" * 35)
    
    scenarios = [
        {
            "name": "Test 1: Basic Appointment Booking",
            "steps": [
                "1. Login as a regular user",
                "2. Go to Schedule Appointment screen",
                "3. Select an available time slot",
                "4. Click 'Schedule Appointment'",
                "5. Check console for '[Appointment Debug]' messages",
                "6. Verify no permission errors"
            ],
            "expected": "Appointment should be booked successfully"
        },
        {
            "name": "Test 2: Verify Data Structure",
            "steps": [
                "1. Before clicking 'Schedule Appointment'",
                "2. Add console.log(appointmentData) in handleScheduleAppointment",
                "3. Check that userId matches auth.currentUser?.uid",
                "4. Verify all required fields are present"
            ],
            "expected": "appointmentData should have correct structure"
        },
        {
            "name": "Test 3: Check Firestore Rules",
            "steps": [
                "1. Open Firebase Console",
                "2. Go to Firestore > Rules",
                "3. Verify rules are deployed",
                "4. Check if create rule uses request.resource.data.userId"
            ],
            "expected": "Rules should allow user to create their own appointments"
        },
        {
            "name": "Test 4: API Fallback Test",
            "steps": [
                "1. Temporarily break Firestore connection",
                "2. Try to book an appointment",
                "3. Check if API fallback is triggered",
                "4. Verify appointment is saved via API"
            ],
            "expected": "API fallback should work when Firestore fails"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("   Steps:")
        for step in scenario['steps']:
            print(f"   {step}")
        print(f"   Expected: {scenario['expected']}")

def generate_console_debug_code():
    """Generate console debug code to add to the app"""
    print("\n💻 CONSOLE DEBUG CODE TO ADD")
    print("=" * 30)
    
    debug_code = """
// Add this to handleScheduleAppointment function for debugging:

console.log('[DEBUG] === APPOINTMENT DEBUGGING ===');
console.log('[DEBUG] User authenticated:', !!auth.currentUser);
console.log('[DEBUG] User ID:', userId);
console.log('[DEBUG] Auth UID:', auth.currentUser?.uid);
console.log('[DEBUG] User email:', auth.currentUser?.email);
console.log('[DEBUG] Selected time slot:', selectedTimeSlot);
console.log('[DEBUG] Selected date:', selectedDate);

// Before creating appointmentData
console.log('[DEBUG] User profile data:', userData);
console.log('[DEBUG] User name to use:', userName);

// After creating appointmentData
console.log('[DEBUG] Full appointment data:', appointmentData);
console.log('[DEBUG] Data types:', {
  userId: typeof appointmentData.userId,
  userName: typeof appointmentData.userName,
  date: typeof appointmentData.date,
  timeSlot: typeof appointmentData.timeSlot
});

// Before Firestore add
console.log('[DEBUG] About to save to Firestore...');
console.log('[DEBUG] Collection path: appointments');
console.log('[DEBUG] Data to save:', JSON.stringify(appointmentData, null, 2));
"""
    
    print(debug_code)

def main():
    """Run the permission debug analysis"""
    print("🚀 APPOINTMENT PERMISSION DEBUG ANALYSIS")
    print("=" * 45)
    print()
    
    # Run analyses
    booking_flow_ok = analyze_appointment_booking_flow()
    firestore_rules_ok = analyze_firestore_rules()
    
    # Generate debugging information
    print("\n📊 ANALYSIS SUMMARY")
    print("=" * 20)
    
    print(f"Booking Flow Analysis: {'✅ PASS' if booking_flow_ok else '❌ FAIL'}")
    print(f"Firestore Rules Analysis: {'✅ PASS' if firestore_rules_ok else '❌ FAIL'}")
    
    if booking_flow_ok and firestore_rules_ok:
        print("\n🎉 Code analysis looks good!")
        print("The permission issue might be due to:")
        print("1. Rules not fully propagated (wait 1-2 minutes)")
        print("2. User authentication issues")
        print("3. Network connectivity problems")
        print("4. Data structure mismatch")
    else:
        print("\n⚠️  Issues found in code analysis.")
        print("Please fix the identified issues first.")
    
    # Generate debugging guides
    generate_specific_debugging_steps()
    generate_test_scenarios()
    generate_console_debug_code()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "analysis": {
            "booking_flow_ok": booking_flow_ok,
            "firestore_rules_ok": firestore_rules_ok
        },
        "recommendations": [
            "Add console debug code to identify exact issue",
            "Check if rules are fully propagated",
            "Verify user authentication",
            "Test with simple appointment data"
        ]
    }
    
    with open("appointment_permission_debug_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: appointment_permission_debug_results.json")

if __name__ == "__main__":
    main()
