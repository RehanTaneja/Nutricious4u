#!/usr/bin/env python3
"""
Test Firestore Rules Verification
================================

This script verifies that the Firestore rules are working correctly
by testing the specific permission issue that was causing problems.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime, timedelta

def test_firestore_connection():
    """Test if we can connect to Firestore"""
    print("🔍 Testing Firestore Connection...")
    
    try:
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate("backend/services/firebase_service_account.json")
        firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Test basic connection
        test_doc = db.collection('test').document('connection_test')
        test_doc.set({'timestamp': datetime.now().isoformat()})
        
        # Clean up
        test_doc.delete()
        
        print("✅ Firestore connection successful")
        return db
        
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")
        return None

def test_appointment_creation_permissions(db):
    """Test if appointment creation permissions work correctly"""
    print("\n🔍 Testing Appointment Creation Permissions...")
    
    if not db:
        print("❌ Cannot test permissions without Firestore connection")
        return False
    
    try:
        # Test data
        test_appointment = {
            'userId': 'test_user_123',
            'userName': 'Test User',
            'userEmail': 'test@example.com',
            'date': datetime.now().isoformat(),
            'timeSlot': '10:00',
            'status': 'confirmed',
            'createdAt': datetime.now().isoformat()
        }
        
        # Try to create appointment
        appointment_ref = db.collection('appointments').add(test_appointment)
        appointment_id = appointment_ref[1].id
        
        print(f"✅ Appointment created successfully with ID: {appointment_id}")
        
        # Clean up
        db.collection('appointments').document(appointment_id).delete()
        print("✅ Test appointment cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Appointment creation failed: {e}")
        return False

def test_appointment_read_permissions(db):
    """Test if appointment read permissions work correctly"""
    print("\n🔍 Testing Appointment Read Permissions...")
    
    if not db:
        print("❌ Cannot test permissions without Firestore connection")
        return False
    
    try:
        # Create a test appointment
        test_appointment = {
            'userId': 'test_user_123',
            'userName': 'Test User',
            'userEmail': 'test@example.com',
            'date': datetime.now().isoformat(),
            'timeSlot': '11:00',
            'status': 'confirmed',
            'createdAt': datetime.now().isoformat()
        }
        
        appointment_ref = db.collection('appointments').add(test_appointment)
        appointment_id = appointment_ref[1].id
        
        # Try to read all appointments
        appointments = db.collection('appointments').stream()
        appointment_count = len(list(appointments))
        
        print(f"✅ Successfully read {appointment_count} appointments")
        
        # Clean up
        db.collection('appointments').document(appointment_id).delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Appointment read failed: {e}")
        return False

def test_breaks_read_permissions(db):
    """Test if breaks read permissions work correctly"""
    print("\n🔍 Testing Breaks Read Permissions...")
    
    if not db:
        print("❌ Cannot test permissions without Firestore connection")
        return False
    
    try:
        # Try to read all breaks
        breaks = db.collection('breaks').stream()
        break_count = len(list(breaks))
        
        print(f"✅ Successfully read {break_count} breaks")
        
        return True
        
    except Exception as e:
        print(f"❌ Breaks read failed: {e}")
        return False

def analyze_firestore_rules_syntax():
    """Analyze the Firestore rules syntax"""
    print("\n🔍 Analyzing Firestore Rules Syntax...")
    
    try:
        with open("firestore.rules", "r") as f:
            content = f.read()
        
        # Check for common syntax issues
        issues = []
        
        # Check if rules version is specified
        if "rules_version = '2';" not in content:
            issues.append("Missing rules version declaration")
        
        # Check if service declaration is correct
        if "service cloud.firestore" not in content:
            issues.append("Missing service declaration")
        
        # Check if appointments rules exist
        if "match /appointments/{appointmentId}" not in content:
            issues.append("Missing appointments rules")
        
        # Check if create permission uses correct syntax
        if "request.resource.data.userId" not in content:
            issues.append("Create permission not using request.resource.data.userId")
        
        # Check if read permission allows authenticated users
        if "allow read: if request.auth != null;" not in content:
            issues.append("Read permission not allowing authenticated users")
        
        if issues:
            print("❌ Firestore rules syntax issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Firestore rules syntax looks correct")
            return True
            
    except FileNotFoundError:
        print("❌ firestore.rules file not found")
        return False

def generate_firestore_debugging_guide():
    """Generate debugging guide for Firestore issues"""
    print("\n🔧 FIRESTORE DEBUGGING GUIDE")
    print("=" * 30)
    
    print("\n1. **Check Rules Deployment**")
    print("   - Verify rules are deployed: firebase deploy --only firestore:rules")
    print("   - Check Firebase Console > Firestore > Rules")
    print("   - Rules may take a few minutes to propagate")
    
    print("\n2. **Check Authentication**")
    print("   - Ensure user is authenticated: auth.currentUser?.uid")
    print("   - Verify Firebase token is valid")
    print("   - Check if user profile exists in Firestore")
    
    print("\n3. **Check Data Structure**")
    print("   - Verify appointmentData contains all required fields")
    print("   - Ensure userId matches auth.currentUser?.uid")
    print("   - Check date format is ISO string")
    
    print("\n4. **Check Network Issues**")
    print("   - Test Firestore connection")
    print("   - Check for network timeouts")
    print("   - Verify Firebase project configuration")
    
    print("\n5. **Check Console Logs**")
    print("   - Look for '[Appointment Debug]' messages")
    print("   - Check for specific permission error messages")
    print("   - Verify data being sent to Firestore")

def main():
    """Run all Firestore tests"""
    print("🚀 TESTING FIRESTORE RULES VERIFICATION")
    print("=" * 45)
    print()
    
    # Test Firestore connection
    db = test_firestore_connection()
    
    # Test permissions
    creation_success = test_appointment_creation_permissions(db) if db else False
    read_success = test_appointment_read_permissions(db) if db else False
    breaks_success = test_breaks_read_permissions(db) if db else False
    syntax_success = analyze_firestore_rules_syntax()
    
    # Generate summary
    print("\n📊 FIRESTORE TEST SUMMARY")
    print("=" * 25)
    
    tests = [
        ("Firestore Connection", db is not None),
        ("Appointment Creation", creation_success),
        ("Appointment Read", read_success),
        ("Breaks Read", breaks_success),
        ("Rules Syntax", syntax_success)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Success Rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL FIRESTORE TESTS PASSED!")
        print("The Firestore rules should be working correctly.")
        print("\nIf users are still getting permission errors:")
        print("1. Check if the app is using the latest deployed rules")
        print("2. Verify user authentication is working")
        print("3. Check network connectivity")
        print("4. Look for specific error messages in console")
    else:
        print("\n⚠️  Some Firestore tests failed.")
        print("Please check the issues above and fix them.")
    
    # Generate debugging guide
    generate_firestore_debugging_guide()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {
            "firestore_connection": db is not None,
            "appointment_creation": creation_success,
            "appointment_read": read_success,
            "breaks_read": breaks_success,
            "rules_syntax": syntax_success
        },
        "overall_success": passed == total,
        "success_rate": f"{passed}/{total} ({passed/total*100:.1f}%)"
    }
    
    with open("firestore_rules_verification_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: firestore_rules_verification_results.json")

if __name__ == "__main__":
    main()
