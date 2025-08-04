#!/usr/bin/env python3
"""
Test environment variables in Railway deployment
"""

import os
import sys
from datetime import datetime

def main():
    print("🔍 Testing Environment Variables in Railway")
    print("=" * 50)
    print(f"Timestamp: {datetime.utcnow()}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Test all Firebase variables
    firebase_vars = {
        'FIREBASE_PROJECT_ID': 'Firebase Project ID',
        'FIREBASE_PRIVATE_KEY_ID': 'Firebase Private Key ID',
        'FIREBASE_CLIENT_EMAIL': 'Firebase Client Email',
        'FIREBASE_CLIENT_ID': 'Firebase Client ID',
        'FIREBASE_CLIENT_X509_CERT_URL': 'Firebase Client X509 Cert URL',
        'FIREBASE_STORAGE_BUCKET': 'Firebase Storage Bucket',
        'FIREBASE_PRIVATE_KEY': 'Firebase Private Key',
        'GEMINI_API_KEY': 'Gemini API Key'
    }
    
    print("📋 Environment Variables Status:")
    print("-" * 40)
    
    all_set = True
    for var, description in firebase_vars.items():
        value = os.getenv(var)
        if value:
            if 'PRIVATE_KEY' in var or 'API_KEY' in var:
                print(f"✅ {var}: {'*' * min(len(value), 20)}...")
            else:
                print(f"✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    print()
    print("=" * 50)
    print("📊 Summary:")
    
    if all_set:
        print("🎉 All environment variables are set!")
        print("✅ Firebase should work correctly")
        return 0
    else:
        print("❌ Some environment variables are missing")
        print("⚠️  Firebase may not work correctly")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 