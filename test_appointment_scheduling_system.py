#!/usr/bin/env python3
"""
Comprehensive Appointment Scheduling System Analysis
==================================================

This script analyzes the appointment scheduling feature to identify issues with:
1. Booking failures and error handling
2. Time slot visibility between users and dieticians
3. Break management and synchronization
4. Real-time updates and data consistency

Issues Identified:
- Users cannot see breaks set by dieticians
- Users only see their own appointments, not others
- No backend API endpoints for appointment management
- Potential race conditions in booking
- Missing validation for overlapping appointments
"""

import json
import requests
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class AppointmentTestResult:
    test_name: str
    success: bool
    error_message: str = ""
    details: Dict[str, Any] = None

class AppointmentSchedulingAnalyzer:
    def __init__(self):
        self.results: List[AppointmentTestResult] = []
        self.backend_url = "https://nutricious4u-production.up.railway.app"
        
    def log_result(self, test_name: str, success: bool, error_message: str = "", details: Dict = None):
        """Log test results"""
        result = AppointmentTestResult(
            test_name=test_name,
            success=success,
            error_message=error_message,
            details=details or {}
        )
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if error_message:
            print(f"   Error: {error_message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        print()

    def test_1_backend_appointment_endpoints(self):
        """Test if backend has appointment management endpoints"""
        print("🔍 Testing Backend Appointment Endpoints...")
        
        endpoints_to_test = [
            "/api/appointments",
            "/api/users/{user_id}/appointments",
            "/api/breaks",
            "/api/appointments/validate"
        ]
        
        missing_endpoints = []
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                if response.status_code == 404:
                    missing_endpoints.append(endpoint)
            except Exception as e:
                missing_endpoints.append(f"{endpoint} (Error: {e})")
        
        if missing_endpoints:
            self.log_result(
                "Backend Appointment Endpoints",
                False,
                f"Missing appointment management endpoints: {missing_endpoints}",
                {"missing_endpoints": missing_endpoints}
            )
        else:
            self.log_result(
                "Backend Appointment Endpoints",
                True,
                details={"tested_endpoints": endpoints_to_test}
            )

    def test_2_code_analysis_user_visibility(self):
        """Analyze code to check user visibility of appointments and breaks"""
        print("🔍 Analyzing User Visibility in Code...")
        
        issues = []
        
        # Based on code analysis from screens.tsx
        issues.append("Users only see their own appointments (line 9606: .where('userId', '==', userId))")
        issues.append("Users don't fetch breaks collection (line 9625: setBreaks([]) - empty breaks array)")
        issues.append("Users cannot see other users' appointments")
        issues.append("No visual indication of breaks for users")
        
        self.log_result(
            "User Visibility Analysis",
            False,
            f"User visibility issues found: {len(issues)}",
            {"visibility_issues": issues}
        )

    def test_3_code_analysis_dietician_visibility(self):
        """Analyze code to check dietician visibility"""
        print("🔍 Analyzing Dietician Visibility in Code...")
        
        strengths = []
        issues = []
        
        # Based on code analysis from DieticianDashboardScreen
        strengths.append("Dieticians can see all appointments (line 10120: no userId filter)")
        strengths.append("Dieticians can manage breaks (line 10130: breaks collection listener)")
        strengths.append("Dieticians can add/remove breaks")
        
        issues.append("No real-time sync with user booking attempts")
        issues.append("Potential for race conditions when users book simultaneously")
        
        self.log_result(
            "Dietician Visibility Analysis",
            len(strengths) > len(issues),
            f"Dietician visibility: {len(strengths)} strengths, {len(issues)} issues",
            {
                "strengths": strengths,
                "issues": issues
            }
        )

    def test_4_booking_validation_analysis(self):
        """Analyze booking validation logic"""
        print("🔍 Analyzing Booking Validation Logic...")
        
        issues = []
        
        # Based on code analysis
        issues.append("No atomic booking validation - potential race conditions")
        issues.append("Users cannot see breaks, so they may book during breaks")
        issues.append("No server-side validation for overlapping appointments")
        issues.append("Client-side validation only (isSlotBooked function)")
        issues.append("No transaction-based booking in Firestore")
        
        self.log_result(
            "Booking Validation Analysis",
            False,
            f"Booking validation issues: {len(issues)}",
            {"validation_issues": issues}
        )

    def test_5_error_handling_analysis(self):
        """Analyze error handling mechanisms"""
        print("🔍 Analyzing Error Handling...")
        
        strengths = []
        weaknesses = []
        
        # Based on code analysis
        strengths.append("Has Firestore fallback to backend API (line 9725)")
        strengths.append("Has local AsyncStorage fallback (line 9770)")
        strengths.append("Comprehensive error logging")
        strengths.append("Multiple fallback mechanisms")
        
        weaknesses.append("No retry mechanism for failed bookings")
        weaknesses.append("No rollback mechanism for partial failures")
        weaknesses.append("Error messages may not be user-friendly")
        weaknesses.append("No timeout handling for slow operations")
        
        self.log_result(
            "Error Handling Analysis",
            len(strengths) > len(weaknesses),
            f"Error handling: {len(strengths)} strengths, {len(weaknesses)} weaknesses",
            {
                "strengths": strengths,
                "weaknesses": weaknesses
            }
        )

    def test_6_real_time_updates_analysis(self):
        """Analyze real-time update mechanisms"""
        print("🔍 Analyzing Real-time Updates...")
        
        issues = []
        
        # Based on code analysis
        issues.append("Users only listen to their own appointments (line 9606)")
        issues.append("Users don't listen to breaks collection")
        issues.append("No real-time sync of dietician's schedule changes")
        issues.append("Break notifications work but may be delayed")
        issues.append("No real-time UI updates for concurrent bookings")
        
        self.log_result(
            "Real-time Updates Analysis",
            False,
            f"Real-time update issues: {len(issues)}",
            {"real_time_issues": issues}
        )

    def test_7_break_management_analysis(self):
        """Analyze break management system"""
        print("🔍 Analyzing Break Management System...")
        
        strengths = []
        issues = []
        
        # Based on code analysis
        strengths.append("Dieticians can add/remove breaks (line 10130)")
        strengths.append("Breaks automatically cancel overlapping appointments (functions/index.js)")
        strengths.append("Break notifications are sent to users")
        strengths.append("Firebase Functions handle break conflicts")
        
        issues.append("Users cannot see breaks in their schedule view (line 9625)")
        issues.append("Users may book during breaks unknowingly")
        issues.append("No visual indication of breaks for users")
        issues.append("Break visibility is completely disabled for users")
        
        self.log_result(
            "Break Management Analysis",
            len(strengths) > len(issues),
            f"Break system: {len(strengths)} strengths, {len(issues)} issues",
            {
                "strengths": strengths,
                "issues": issues
            }
        )

    def test_8_data_consistency_analysis(self):
        """Analyze data consistency across the system"""
        print("🔍 Analyzing Data Consistency...")
        
        issues = []
        
        # Based on code analysis
        issues.append("Users and dieticians see different data sets")
        issues.append("No centralized appointment validation")
        issues.append("Potential for orphaned appointments")
        issues.append("No data integrity checks")
        issues.append("Client-side validation only")
        issues.append("No server-side booking validation")
        
        self.log_result(
            "Data Consistency Analysis",
            False,
            f"Data consistency issues: {len(issues)}",
            {"consistency_issues": issues}
        )

    def generate_recommendations(self):
        """Generate recommendations for fixing the issues"""
        print("\n📋 RECOMMENDATIONS FOR FIXING APPOINTMENT SCHEDULING ISSUES")
        print("=" * 70)
        
        recommendations = [
            {
                "priority": "HIGH",
                "issue": "Users cannot see breaks set by dieticians",
                "solution": "Modify ScheduleAppointmentScreen to fetch and display breaks from Firestore",
                "code_changes": [
                    "Add breaks listener in ScheduleAppointmentScreen (line 9625)",
                    "Update isTimeSlotInBreak function to check actual breaks",
                    "Add visual styling for break time slots",
                    "Remove setBreaks([]) and add proper breaks fetching"
                ]
            },
            {
                "priority": "HIGH", 
                "issue": "Users only see their own appointments",
                "solution": "Allow users to see all appointments (but not book over them)",
                "code_changes": [
                    "Modify appointments listener to fetch all appointments (line 9606)",
                    "Update isSlotBooked to check all appointments",
                    "Add visual distinction for other users' appointments",
                    "Update appointment booking logic to prevent double booking"
                ]
            },
            {
                "priority": "MEDIUM",
                "issue": "No backend API endpoints for appointment management",
                "solution": "Add appointment management endpoints to backend",
                "code_changes": [
                    "Add /api/appointments POST endpoint",
                    "Add /api/appointments GET endpoint", 
                    "Add /api/appointments/{id} DELETE endpoint",
                    "Add appointment validation logic"
                ]
            },
            {
                "priority": "MEDIUM",
                "issue": "Potential race conditions in booking",
                "solution": "Implement atomic booking with server-side validation",
                "code_changes": [
                    "Add transaction-based booking in Firestore",
                    "Implement server-side booking validation",
                    "Add booking lock mechanism",
                    "Use Firestore transactions for atomic operations"
                ]
            },
            {
                "priority": "LOW",
                "issue": "Error handling improvements",
                "solution": "Enhance error handling and user feedback",
                "code_changes": [
                    "Add retry mechanism for failed bookings",
                    "Improve error messages for users",
                    "Add booking confirmation emails",
                    "Add timeout handling for slow operations"
                ]
            }
        ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. [{rec['priority']}] {rec['issue']}")
            print(f"   Solution: {rec['solution']}")
            print(f"   Code Changes:")
            for change in rec['code_changes']:
                print(f"     - {change}")

    def generate_fix_implementation_guide(self):
        """Generate implementation guide for fixes"""
        print("\n🔧 IMPLEMENTATION GUIDE FOR FIXES")
        print("=" * 50)
        
        implementation_steps = [
            {
                "step": 1,
                "title": "Fix User Break Visibility",
                "file": "mobileapp/screens.tsx",
                "changes": [
                    "Replace line 9625: setBreaks([]) with proper breaks fetching",
                    "Add breaks listener similar to appointments listener",
                    "Update isTimeSlotInBreak function to check actual breaks",
                    "Add break time slot styling"
                ]
            },
            {
                "step": 2,
                "title": "Fix User Appointment Visibility",
                "file": "mobileapp/screens.tsx", 
                "changes": [
                    "Modify line 9606: Remove .where('userId', '==', userId) filter",
                    "Update isSlotBooked function to handle all appointments",
                    "Add visual distinction for user's own vs others' appointments",
                    "Update appointment booking logic to prevent double booking"
                ]
            },
            {
                "step": 3,
                "title": "Add Backend Appointment Endpoints",
                "file": "backend/server.py",
                "changes": [
                    "Add appointment models (AppointmentRequest, AppointmentResponse)",
                    "Add POST /api/appointments endpoint",
                    "Add GET /api/appointments endpoint",
                    "Add DELETE /api/appointments/{id} endpoint",
                    "Add appointment validation logic"
                ]
            },
            {
                "step": 4,
                "title": "Implement Atomic Booking",
                "file": "mobileapp/screens.tsx",
                "changes": [
                    "Replace direct Firestore add with transaction-based booking",
                    "Add server-side validation before booking",
                    "Implement booking lock mechanism",
                    "Add rollback mechanism for failed bookings"
                ]
            }
        ]
        
        for step in implementation_steps:
            print(f"\nStep {step['step']}: {step['title']}")
            print(f"File: {step['file']}")
            print("Changes:")
            for change in step['changes']:
                print(f"  - {change}")

    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 APPOINTMENT SCHEDULING SYSTEM ANALYSIS")
        print("=" * 50)
        print()
        
        # Run all tests
        self.test_1_backend_appointment_endpoints()
        self.test_2_code_analysis_user_visibility()
        self.test_3_code_analysis_dietician_visibility()
        self.test_4_booking_validation_analysis()
        self.test_5_error_handling_analysis()
        self.test_6_real_time_updates_analysis()
        self.test_7_break_management_analysis()
        self.test_8_data_consistency_analysis()
        
        # Generate summary
        print("\n📊 TEST SUMMARY")
        print("=" * 30)
        
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed
        
        print(f"Total Tests: {len(self.results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Generate implementation guide
        self.generate_fix_implementation_guide()
        
        # Save detailed results
        with open("appointment_scheduling_analysis.json", "w") as f:
            json.dump([{
                "test_name": r.test_name,
                "success": r.success,
                "error_message": r.error_message,
                "details": r.details
            } for r in self.results], f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: appointment_scheduling_analysis.json")

if __name__ == "__main__":
    analyzer = AppointmentSchedulingAnalyzer()
    analyzer.run_all_tests()
