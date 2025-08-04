#!/usr/bin/env python3
"""
Test Firebase connection and configuration
"""

import os
import sys
import json
from datetime import datetime

def test_environment_variables():
    """Test if all required Firebase environment variables are set"""
    print("🔍 Testing Firebase Environment Variables...")
    
    required_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_PRIVATE_KEY_ID', 
        'FIREBASE_CLIENT_EMAIL',
        'FIREBASE_CLIENT_ID',
        'FIREBASE_CLIENT_X509_CERT_URL',
        'FIREBASE_STORAGE_BUCKET'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * min(len(value), 10)}...")
    
    # Special handling for private key
    private_key = os.getenv('FIREBASE_PRIVATE_KEY')
    if private_key:
        print(f"✅ FIREBASE_PRIVATE_KEY: {'*' * min(len(private_key), 20)}...")
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("⚠️  WARNING: Private key doesn't start with proper header")
    else:
        missing_vars.append('FIREBASE_PRIVATE_KEY')
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_firebase_import():
    """Test if Firebase can be imported and initialized"""
    print("\n🔥 Testing Firebase Import...")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage
        print("✅ Firebase Admin SDK imported successfully")
        
        # Test credentials creation
        service_account_info = {
            "type": "service_account",
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.getenv('FIREBASE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
            "universe_domain": "googleapis.com"
        }
        
        # Fix private key format if needed
        private_key = service_account_info['private_key']
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            if '-----BEGIN PRIVATE KEY-----' in private_key:
                start = private_key.find('-----BEGIN PRIVATE KEY-----')
                end = private_key.find('-----END PRIVATE KEY-----') + len('-----END PRIVATE KEY-----')
                private_key = private_key[start:end]
            else:
                private_key = f"-----BEGIN PRIVATE KEY-----\n{private_key}\n-----END PRIVATE KEY-----"
        
        service_account_info['private_key'] = private_key
        
        cred = credentials.Certificate(service_account_info)
        print("✅ Firebase credentials created successfully")
        
        # Test app initialization
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'nutricious4u-diet-storage')
        })
        print("✅ Firebase app initialized successfully")
        
        # Test Firestore connection
        db = firestore.client()
        print("✅ Firestore client created successfully")
        
        # Test Storage connection
        bucket = storage.bucket()
        print("✅ Storage bucket created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase import/initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_based_credentials():
    """Test if file-based credentials work as fallback"""
    print("\n📄 Testing File-based Credentials...")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage
        
        # Check if service account file exists
        current_dir = os.path.dirname(__file__)
        cred_path = os.path.abspath(os.path.join(current_dir, 'services', 'firebase_service_account.json'))
        
        if os.path.exists(cred_path):
            print(f"✅ Service account file found at: {cred_path}")
            
            cred = credentials.Certificate(cred_path)
            print("✅ File-based credentials created successfully")
            
            # Test app initialization with file credentials
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'nutricious4u-diet-storage')
            })
            print("✅ Firebase app initialized with file credentials")
            
            return True
        else:
            print(f"❌ Service account file not found at: {cred_path}")
            return False
            
    except Exception as e:
        print(f"❌ File-based credentials failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Firebase Connection Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.utcnow()}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Test 1: Environment variables
    env_ok = test_environment_variables()
    
    # Test 2: Firebase import and initialization
    import_ok = test_firebase_import()
    
    # Test 3: File-based credentials
    file_ok = test_file_based_credentials()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Firebase Import: {'✅ PASS' if import_ok else '❌ FAIL'}")
    print(f"File-based Credentials: {'✅ PASS' if file_ok else '❌ FAIL'}")
    
    if env_ok and import_ok:
        print("\n🎉 All tests passed! Firebase should work correctly.")
        return 0
    elif file_ok:
        print("\n⚠️  Environment variables failed, but file-based credentials work.")
        print("   The app should still function using the service account file.")
        return 0
    else:
        print("\n❌ Firebase configuration has issues. Please check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 