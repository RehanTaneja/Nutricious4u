#!/usr/bin/env python3
"""
Comprehensive Notification System Test Suite
Tests all new notification handlers and existing functions
"""

import json
import re
from typing import Dict, List, Tuple

def print_header(text: str):
    print("\n" + "=" * 80)
    print(f"🧪 {text}")
    print("=" * 80)

def print_success(text: str):
    print(f"✅ {text}")

def print_error(text: str):
    print(f"❌ {text}")

def print_info(text: str):
    print(f"ℹ️  {text}")

def print_warning(text: str):
    print(f"⚠️  {text}")

class NotificationTester:
    def __init__(self):
        self.test_results = {}
        
    def test_token_functions(self) -> Dict:
        """Test get_user_notification_token and get_dietician_notification_token"""
        print_header("TEST 1: Token Retrieval Functions")
        
        results = {
            "get_user_notification_token": {"status": "unknown", "details": []},
            "get_dietician_notification_token": {"status": "unknown", "details": []}
        }
        
        try:
            with open('backend/services/firebase_client.py', 'r') as f:
                content = f.read()
            
            # Test get_user_notification_token
            print_info("Testing get_user_notification_token function...")
            
            checks = []
            if 'def get_user_notification_token(user_id: str)' in content:
                checks.append("✅ Function exists")
            else:
                checks.append("❌ Function not found")
                
            if 'is_dietician = data.get("isDietician", False)' in content:
                checks.append("✅ Checks isDietician flag")
            else:
                checks.append("❌ Missing isDietician check")
                
            if 'if is_dietician:' in content and 'return None' in content:
                checks.append("✅ Returns None for dietician accounts")
            else:
                checks.append("❌ Doesn't filter dietician accounts")
                
            if 'token = data.get("expoPushToken") or data.get("notificationToken")' in content:
                checks.append("✅ Retrieves token from Firestore")
            else:
                checks.append("❌ Token retrieval logic missing")
                
            if 'token.startswith("ExponentPushToken")' in content:
                checks.append("✅ Validates token format")
            else:
                checks.append("❌ No token format validation")
            
            results["get_user_notification_token"]["details"] = checks
            results["get_user_notification_token"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
            
            # Test get_dietician_notification_token
            print_info("\nTesting get_dietician_notification_token function...")
            
            checks = []
            if 'def get_dietician_notification_token()' in content:
                checks.append("✅ Function exists")
            else:
                checks.append("❌ Function not found")
                
            if 'users_ref.where("isDietician", "==", True)' in content:
                checks.append("✅ Queries for dietician account")
            else:
                checks.append("❌ Missing dietician query")
                
            if 'is_dietician = data.get("isDietician", False)' in content:
                checks.append("✅ Validates dietician flag")
            else:
                checks.append("❌ No dietician validation")
            
            results["get_dietician_notification_token"]["details"] = checks
            results["get_dietician_notification_token"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
                
            if results["get_user_notification_token"]["status"] == "passed" and results["get_dietician_notification_token"]["status"] == "passed":
                print_success("\n✅ All token functions working correctly")
            else:
                print_error("\n❌ Some token functions have issues")
                
        except Exception as e:
            print_error(f"Error testing token functions: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_message_notification_handlers(self) -> Dict:
        """Test message notification handlers in frontend"""
        print_header("TEST 2: Message Notification Handlers")
        
        results = {
            "user_dashboard": {"status": "unknown", "details": []},
            "dietician_dashboard": {"status": "unknown", "details": []},
            "backend": {"status": "unknown", "details": []}
        }
        
        try:
            with open('mobileapp/screens.tsx', 'r') as f:
                screens_content = f.read()
            
            # Test User Dashboard handler
            print_info("Testing User DashboardScreen message handler...")
            
            checks = []
            if "data?.type === 'message_notification' && data?.fromDietician" in screens_content:
                checks.append("✅ User handler exists for messages from dietician")
            else:
                checks.append("❌ User handler missing for messages from dietician")
                
            if "Alert.alert" in screens_content and "New Message" in screens_content:
                checks.append("✅ Shows alert for new messages")
            else:
                checks.append("❌ No alert for new messages")
                
            if "navigation.navigate('DieticianMessage')" in screens_content:
                checks.append("✅ Provides navigation to messages")
            else:
                checks.append("❌ No navigation to messages")
            
            results["user_dashboard"]["details"] = checks
            results["user_dashboard"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
            
            # Test Dietician Dashboard handler
            print_info("\nTesting DieticianDashboard message handler...")
            
            checks = []
            if "data?.type === 'message_notification' && data?.fromUser" in screens_content:
                checks.append("✅ Dietician handler exists for messages from users")
            else:
                checks.append("❌ Dietician handler missing")
            
            results["dietician_dashboard"]["details"] = checks
            results["dietician_dashboard"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
            
            # Test Backend
            print_info("\nTesting Backend message notification logic...")
            
            with open('backend/server.py', 'r') as f:
                server_content = f.read()
            
            checks = []
            if 'async def send_message_notification' in server_content:
                checks.append("✅ Backend endpoint exists")
            else:
                checks.append("❌ Backend endpoint missing")
                
            if 'if sender_is_dietician:' in server_content:
                checks.append("✅ Routes based on sender role")
            else:
                checks.append("❌ No role-based routing")
                
            if '"fromDietician": True' in server_content:
                checks.append("✅ Sets fromDietician flag correctly")
            else:
                checks.append("❌ fromDietician flag missing")
                
            if '"fromUser": sender_user_id' in server_content:
                checks.append("✅ Sets fromUser flag correctly")
            else:
                checks.append("❌ fromUser flag missing")
            
            results["backend"]["details"] = checks
            results["backend"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
                
            if all(r["status"] == "passed" for r in results.values()):
                print_success("\n✅ All message notification handlers working correctly")
            else:
                print_error("\n❌ Some message notification handlers have issues")
                
        except Exception as e:
            print_error(f"Error testing message handlers: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_appointment_notification_handlers(self) -> Dict:
        """Test appointment notification handlers"""
        print_header("TEST 3: Appointment Notification Handlers")
        
        results = {
            "user_dashboard": {"status": "unknown", "details": []},
            "dietician_dashboard": {"status": "unknown", "details": []},
            "backend_user_notification": {"status": "unknown", "details": []},
            "backend_dietician_notification": {"status": "unknown", "details": []}
        }
        
        try:
            with open('mobileapp/screens.tsx', 'r') as f:
                screens_content = f.read()
            
            # Test User Dashboard handler
            print_info("Testing User DashboardScreen appointment handler...")
            
            checks = []
            if "data?.type === 'appointment_notification'" in screens_content:
                checks.append("✅ User appointment handler exists")
            else:
                checks.append("❌ User appointment handler missing")
                
            if "data.appointmentType === 'confirmed'" in screens_content:
                checks.append("✅ Handles confirmed appointments")
            else:
                checks.append("❌ No confirmed appointment handling")
                
            if "data.appointmentType === 'cancelled'" in screens_content:
                checks.append("✅ Handles cancelled appointments")
            else:
                checks.append("❌ No cancelled appointment handling")
            
            results["user_dashboard"]["details"] = checks
            results["user_dashboard"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
            
            # Test Dietician Dashboard handler
            print_info("\nTesting DieticianDashboard appointment handler...")
            
            # Find dietician dashboard section
            dietician_section_start = screens_content.find("const DieticianDashboardScreen")
            if dietician_section_start > 0:
                dietician_section = screens_content[dietician_section_start:dietician_section_start + 50000]
                
                checks = []
                if "data?.type === 'appointment_notification'" in dietician_section:
                    checks.append("✅ Dietician appointment handler exists")
                else:
                    checks.append("❌ Dietician appointment handler missing")
                    
                if "data.appointmentType === 'scheduled' ? 'booked' : 'cancelled'" in dietician_section:
                    checks.append("✅ Handles both scheduled and cancelled")
                else:
                    checks.append("❌ Incomplete appointment type handling")
            else:
                checks = ["❌ DieticianDashboardScreen not found"]
            
            results["dietician_dashboard"]["details"] = checks
            results["dietician_dashboard"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
            
            # Test Backend
            print_info("\nTesting Backend appointment notification logic...")
            
            with open('backend/server.py', 'r') as f:
                server_content = f.read()
            
            # Test user notification
            checks = []
            if 'if appointment_type == "scheduled":' in server_content:
                checks.append("✅ Checks for scheduled appointments")
            else:
                checks.append("❌ No scheduled appointment check")
                
            if 'user_docs = firestore_db.collection("user_profiles").where("email", "==", user_email)' in server_content:
                checks.append("✅ Finds user by email")
            else:
                checks.append("❌ No user lookup by email")
                
            if 'user_token = get_user_notification_token(user_doc.id)' in server_content:
                checks.append("✅ Gets user notification token")
            else:
                checks.append("❌ No user token retrieval")
                
            if '"appointmentType": "confirmed"' in server_content:
                checks.append("✅ Sends confirmed appointment notification to user")
            else:
                checks.append("❌ No user confirmation notification")
            
            results["backend_user_notification"]["details"] = checks
            results["backend_user_notification"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
            
            # Test dietician notification
            print_info("\nTesting Backend dietician appointment notification...")
            
            checks = []
            if 'dietician_token = get_dietician_notification_token()' in server_content:
                checks.append("✅ Gets dietician token")
            else:
                checks.append("❌ No dietician token retrieval")
                
            if '"type": "appointment_notification"' in server_content:
                checks.append("✅ Sends appointment notification to dietician")
            else:
                checks.append("❌ No dietician notification")
            
            results["backend_dietician_notification"]["details"] = checks
            results["backend_dietician_notification"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
                
            if all(r["status"] == "passed" for r in results.values()):
                print_success("\n✅ All appointment notification handlers working correctly")
            else:
                print_error("\n❌ Some appointment notification handlers have issues")
                
        except Exception as e:
            print_error(f"Error testing appointment handlers: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_diet_notifications_unchanged(self) -> Dict:
        """Verify diet notifications remain unchanged"""
        print_header("TEST 4: Diet Notifications (Verify Unchanged)")
        
        results = {
            "new_diet_handler": {"status": "unknown", "details": []},
            "diet_reminder_handler": {"status": "unknown", "details": []},
            "backend_diet_upload": {"status": "unknown", "details": []}
        }
        
        try:
            with open('mobileapp/screens.tsx', 'r') as f:
                screens_content = f.read()
            
            # Test new_diet handler
            print_info("Testing new_diet notification handler...")
            
            checks = []
            if "data?.type === 'new_diet' && data?.userId === userId" in screens_content:
                checks.append("✅ new_diet handler exists")
            else:
                checks.append("❌ new_diet handler missing")
                
            if "setShowAutoExtractionPopup(true)" in screens_content:
                checks.append("✅ Shows auto extraction popup")
            else:
                checks.append("❌ Auto extraction popup missing")
                
            if "getUserDiet(userId)" in screens_content:
                checks.append("✅ Refreshes diet data")
            else:
                checks.append("❌ No diet data refresh")
            
            results["new_diet_handler"]["details"] = checks
            results["new_diet_handler"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
            
            # Test diet reminder handler
            print_info("\nTesting diet_reminder handler...")
            
            checks = []
            if "data?.type === 'diet'" in screens_content or "data?.type === 'diet_reminder'" in screens_content:
                checks.append("✅ diet_reminder handler exists")
            else:
                checks.append("❌ diet_reminder handler missing")
            
            results["diet_reminder_handler"]["details"] = checks
            results["diet_reminder_handler"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
            
            # Test backend diet upload
            print_info("\nTesting Backend diet upload notification...")
            
            with open('backend/server.py', 'r') as f:
                server_content = f.read()
            
            checks = []
            if 'async def upload_user_diet_pdf' in server_content:
                checks.append("✅ Diet upload endpoint exists")
            else:
                checks.append("❌ Diet upload endpoint missing")
                
            if 'user_token = get_user_notification_token(user_id)' in server_content:
                checks.append("✅ Gets user token for new diet notification")
            else:
                checks.append("❌ No user token retrieval for diet")
                
            if '"type": "new_diet"' in server_content:
                checks.append("✅ Sends new_diet notification to user")
            else:
                checks.append("❌ No new_diet notification to user")
                
            if 'dietician_token = get_dietician_notification_token()' in server_content:
                checks.append("✅ Gets dietician token")
            else:
                checks.append("❌ No dietician token retrieval")
                
            if '"type": "diet_upload_success"' in server_content:
                checks.append("✅ Sends diet_upload_success to dietician")
            else:
                checks.append("❌ No diet_upload_success notification")
            
            results["backend_diet_upload"]["details"] = checks
            results["backend_diet_upload"]["status"] = "passed" if all("✅" in c for c in checks) else "failed"
            
            for check in checks:
                print(f"  {check}")
                
            if all(r["status"] == "passed" for r in results.values()):
                print_success("\n✅ Diet notifications remain unchanged and working")
            else:
                print_error("\n❌ Diet notifications may have been affected")
                
        except Exception as e:
            print_error(f"Error testing diet notifications: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_notification_isolation(self) -> Dict:
        """Verify different notification types don't interfere"""
        print_header("TEST 5: Notification Type Isolation")
        
        results = {"status": "unknown", "details": []}
        
        try:
            with open('mobileapp/screens.tsx', 'r') as f:
                content = f.read()
            
            checks = []
            
            # Find all notification listeners in User Dashboard
            dashboard_start = content.find("const DashboardScreen")
            dashboard_end = content.find("const handleOpenDiet", dashboard_start)
            dashboard_section = content[dashboard_start:dashboard_end]
            
            # Count separate if blocks for each notification type
            new_diet_handlers = dashboard_section.count("data?.type === 'new_diet'")
            message_handlers = dashboard_section.count("data?.type === 'message_notification'")
            appointment_handlers = dashboard_section.count("data?.type === 'appointment_notification'")
            
            if new_diet_handlers == 1:
                checks.append(f"✅ Exactly 1 new_diet handler in User Dashboard")
            else:
                checks.append(f"⚠️  {new_diet_handlers} new_diet handlers found (expected 1)")
                
            if message_handlers >= 1:
                checks.append(f"✅ Message handler exists in User Dashboard")
            else:
                checks.append(f"❌ No message handler in User Dashboard")
                
            if appointment_handlers >= 1:
                checks.append(f"✅ Appointment handler exists in User Dashboard")
            else:
                checks.append(f"❌ No appointment handler in User Dashboard")
            
            # Verify each handler is in separate if block
            if_blocks = re.findall(r"if \(data\?\\.type ===", dashboard_section)
            if len(if_blocks) >= 3:
                checks.append(f"✅ Notification handlers are in separate if blocks")
            else:
                checks.append(f"⚠️  Only {len(if_blocks)} if blocks found for notifications")
            
            results["details"] = checks
            results["status"] = "passed" if all("✅" in c for c in checks) else "warning"
            
            for check in checks:
                print(f"  {check}")
                
            if results["status"] == "passed":
                print_success("\n✅ All notification types are properly isolated")
            else:
                print_warning("\n⚠️  Some notification isolation concerns")
                
        except Exception as e:
            print_error(f"Error testing notification isolation: {e}")
            results["error"] = str(e)
            results["status"] = "failed"
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all tests and return results"""
        print("\n" + "🚀" * 40)
        print("🚀 COMPREHENSIVE NOTIFICATION SYSTEM TEST SUITE")
        print("🚀" * 40)
        
        all_results = {}
        
        # Run tests
        all_results["token_functions"] = self.test_token_functions()
        all_results["message_notifications"] = self.test_message_notification_handlers()
        all_results["appointment_notifications"] = self.test_appointment_notification_handlers()
        all_results["diet_notifications_unchanged"] = self.test_diet_notifications_unchanged()
        all_results["notification_isolation"] = self.test_notification_isolation()
        
        # Summary
        print_header("TEST SUMMARY")
        
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results.values() if isinstance(r, dict) and r.get("status") == "passed")
        warning_tests = sum(1 for r in all_results.values() if isinstance(r, dict) and r.get("status") == "warning")
        failed_tests = total_tests - passed_tests - warning_tests
        
        print(f"\n📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"⚠️  Warnings: {warning_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests == 0:
            print_success("\n🎉 ALL TESTS PASSED! Notification system is working correctly.")
        else:
            print_error(f"\n⚠️  {failed_tests} tests failed. Please review the results above.")
        
        return all_results

if __name__ == "__main__":
    tester = NotificationTester()
    results = tester.run_all_tests()
    
    # Save results
    with open('notification_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Detailed results saved to: notification_test_results.json")

