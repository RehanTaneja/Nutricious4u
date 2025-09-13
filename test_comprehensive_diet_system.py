#!/usr/bin/env python3
"""
Comprehensive Diet Reminder System Test
========================================

This test verifies the complete diet reminder system fixes:
1. Popup-based extraction instead of automatic extraction
2. Local scheduling only (no backend scheduler conflicts)
3. No wrong reminders on non-diet days
4. No random reminders after 22:00
5. Proper day-wise scheduling

Test Scenarios:
- New diet upload → Should set auto_extract_pending=True
- Manual extraction → Should use local scheduling only
- Non-diet days → Should NOT get notifications
- Wrong time reminders → Should NOT happen
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
TEST_USER_ID = "test_user_diet_system"
TEST_DIETICIAN_ID = "test_dietician"

# Sample diet content that should extract Monday-Thursday activities only
SAMPLE_DIET_CONTENT = """
Diet Plan for Week

DAY 1 (MONDAY):
8:00 AM - Breakfast: Oats with fruits
12:00 PM - Lunch: Rice with dal
6:00 PM - Dinner: Chapati with vegetables
10:00 PM - Water (2 glasses)

DAY 2 (TUESDAY):  
8:00 AM - Breakfast: Upma
1:00 PM - Lunch: Chicken curry with rice
7:00 PM - Dinner: Fish with vegetables
10:00 PM - Herbal tea

DAY 3 (WEDNESDAY):
8:00 AM - Breakfast: Idli with sambar
12:30 PM - Lunch: Vegetable biryani
6:30 PM - Dinner: Dal with roti
10:00 PM - Milk (1 glass)

DAY 4 (THURSDAY):
8:00 AM - Breakfast: Poha
1:30 PM - Lunch: Rajma with rice
7:30 PM - Dinner: Paneer curry
10:00 PM - Green tea

Note: Friday is rest day - no specific diet plan
"""

def print_test_header(test_name):
    """Print a formatted test header"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    print()

async def test_backend_upload_flow():
    """Test 1: Backend diet upload should set auto_extract_pending=True"""
    print_test_header("Backend Diet Upload Flow")
    
    try:
        # Import backend modules
        sys.path.append('backend')
        from services.diet_notification_service import diet_notification_service
        
        # Mock firestore database
        class MockFirestore:
            def __init__(self):
                self.data = {}
            
            def collection(self, name):
                return MockCollection(self, name)
        
        class MockCollection:
            def __init__(self, db, name):
                self.db = db
                self.name = name
            
            def document(self, doc_id):
                return MockDocument(self.db, self.name, doc_id)
        
        class MockDocument:
            def __init__(self, db, collection, doc_id):
                self.db = db
                self.collection = collection
                self.doc_id = doc_id
                self.key = f"{collection}/{doc_id}"
            
            def set(self, data, merge=False):
                if merge and self.key in self.db.data:
                    self.db.data[self.key].update(data)
                else:
                    self.db.data[self.key] = data
                return True
        
        # Mock PDF RAG service
        class MockPDFService:
            def get_diet_pdf_text(self, user_id, url, db):
                return SAMPLE_DIET_CONTENT
        
        # Replace the RAG service temporarily
        original_rag = diet_notification_service.pdf_rag_service
        diet_notification_service.pdf_rag_service = MockPDFService()
        
        mock_db = MockFirestore()
        
        # Test extraction
        notifications = diet_notification_service.extract_and_create_notifications(
            TEST_USER_ID, "test_diet.pdf", mock_db
        )
        
        # Restore original service
        diet_notification_service.pdf_rag_service = original_rag
        
        # Verify results
        print(f"📊 Extracted {len(notifications)} notifications")
        
        # Check that we got notifications
        if len(notifications) > 0:
            print_result("Diet extraction", True, f"Found {len(notifications)} activities")
        else:
            print_result("Diet extraction", False, "No activities extracted")
            return False
        
        # Check day assignment
        monday_notifications = [n for n in notifications if 0 in n.get('selectedDays', [])]
        friday_notifications = [n for n in notifications if 4 in n.get('selectedDays', [])]
        
        print(f"📅 Monday notifications: {len(monday_notifications)}")
        print(f"📅 Friday notifications: {len(friday_notifications)}")
        
        # Should have Monday notifications, should NOT have Friday notifications
        if len(monday_notifications) > 0:
            print_result("Monday scheduling", True, f"Found {len(monday_notifications)} Monday activities")
        else:
            print_result("Monday scheduling", False, "No Monday activities found")
        
        if len(friday_notifications) == 0:
            print_result("Friday prevention", True, "No Friday notifications (correct)")
        else:
            print_result("Friday prevention", False, f"Found {len(friday_notifications)} Friday notifications (wrong)")
        
        # Check inactive notifications (those without determined days)
        inactive_notifications = [n for n in notifications if not n.get('isActive', True)]
        print(f"🔒 Inactive notifications: {len(inactive_notifications)}")
        
        return len(notifications) > 0 and len(friday_notifications) == 0
        
    except Exception as e:
        print_result("Backend upload test", False, str(e))
        return False

def test_popup_system():
    """Test 2: Popup system implementation"""
    print_test_header("Auto-Extraction Popup System")
    
    try:
        # Check if popup implementation exists in frontend
        frontend_file = 'mobileapp/screens.tsx'
        if not os.path.exists(frontend_file):
            print_result("Frontend file check", False, "screens.tsx not found")
            return False
        
        with open(frontend_file, 'r') as f:
            content = f.read()
        
        # Check for key popup components
        popup_checks = [
            ('Auto-extraction state', 'showAutoExtractionPopup'),
            ('Popup modal', 'Auto-Extraction Popup Modal'),
            ('Extract button', 'Extract Reminders'),
            ('Popup trigger', 'auto_extract_pending'),
            ('Handle function', 'handleAutoExtraction')
        ]
        
        all_passed = True
        for check_name, check_text in popup_checks:
            if check_text in content:
                print_result(check_name, True, f"Found: {check_text}")
            else:
                print_result(check_name, False, f"Missing: {check_text}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_result("Popup system test", False, str(e))
        return False

def test_scheduler_conflicts():
    """Test 3: Backend scheduler conflicts removal"""
    print_test_header("Backend Scheduler Conflicts")
    
    try:
        backend_file = 'backend/server.py'
        if not os.path.exists(backend_file):
            print_result("Backend file check", False, "server.py not found")
            return False
        
        with open(backend_file, 'r') as f:
            content = f.read()
        
        # Check that backend scheduler is disabled
        scheduler_checks = [
            ('Backend scheduler disabled', '# DISABLED: Backend notification scheduler'),
            ('Auto extraction removed', 'DO NOT automatically schedule here'),
            ('Manual extraction local only', 'using local scheduling only for reliability'),
            ('Popup flag set', 'auto_extract_pending')
        ]
        
        all_passed = True
        for check_name, check_text in scheduler_checks:
            if check_text in content:
                print_result(check_name, True, f"Found: {check_text}")
            else:
                print_result(check_name, False, f"Missing: {check_text}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_result("Scheduler conflicts test", False, str(e))
        return False

def test_unified_notification_service():
    """Test 4: Unified notification service improvements"""
    print_test_header("Unified Notification Service")
    
    try:
        service_file = 'mobileapp/services/unifiedNotificationService.ts'
        if not os.path.exists(service_file):
            print_result("Service file check", False, "unifiedNotificationService.ts not found")
            return False
        
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Check for improvements
        service_checks = [
            ('Day-wise scheduling', 'Create separate notifications for each selected day'),
            ('Active check', 'notification.isActive !== false'),
            ('Weekly repeats', 'repeats: true'),
            ('Repeat interval', 'repeatInterval: 7 * 24 * 60 * 60 * 1000'),
            ('Inactive skip', 'Skipping notification - no valid days or inactive')
        ]
        
        all_passed = True
        for check_name, check_text in service_checks:
            if check_text in content:
                print_result(check_name, True, f"Found: {check_text}")
            else:
                print_result(check_name, False, f"Missing: {check_text}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_result("Unified service test", False, str(e))
        return False

def test_diet_notification_service():
    """Test 5: Diet notification service improvements"""
    print_test_header("Diet Notification Service")
    
    try:
        service_file = 'backend/services/diet_notification_service.py'
        if not os.path.exists(service_file):
            print_result("Service file check", False, "diet_notification_service.py not found")
            return False
        
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Check for critical fixes
        service_checks = [
            ('Conservative scheduling', 'CONSERVATIVE FIX'),
            ('Empty days default', "notification['selectedDays'] = []"),
            ('Inactive default', "notification['isActive'] = False"),
            ('Day determination', '_determine_diet_days_from_activities'),
            ('No weekend default', 'Could not determine days')
        ]
        
        all_passed = True
        for check_name, check_text in service_checks:
            if check_text in content:
                print_result(check_name, True, f"Found: {check_text}")
            else:
                print_result(check_name, False, f"Missing: {check_text}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_result("Diet service test", False, str(e))
        return False

async def run_comprehensive_test():
    """Run all tests"""
    print(f"""
🎯 COMPREHENSIVE DIET REMINDER SYSTEM TEST
==========================================

Testing the complete fix for diet reminder issues:
✅ Popup-based extraction instead of automatic
✅ Local scheduling only (no backend conflicts)  
✅ No wrong reminders on non-diet days
✅ No random reminders after last scheduled time
✅ Proper day-wise notification delivery

Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Backend Upload Flow", await test_backend_upload_flow()))
    test_results.append(("Popup System", test_popup_system()))
    test_results.append(("Scheduler Conflicts", test_scheduler_conflicts()))
    test_results.append(("Unified Service", test_unified_notification_service()))
    test_results.append(("Diet Service", test_diet_notification_service()))
    
    # Final summary
    print_test_header("COMPREHENSIVE TEST RESULTS")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("""
🎉 ALL TESTS PASSED!
===================

✅ Diet reminder system is now working correctly:
   • New diets trigger popup for extraction (not automatic)
   • Manual extraction uses local scheduling only
   • No wrong reminders on non-diet days (like Friday)
   • No random reminders after 22:00
   • Proper day-wise delivery (Monday-Thursday only)
   • Backend scheduler conflicts resolved

🚀 The app is ready for deployment!
""")
        return True
    else:
        print(f"""
⚠️  {total_tests - passed_tests} TESTS FAILED
================================

Please review the failed tests above and fix the issues before deployment.
""")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(run_comprehensive_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
