#!/usr/bin/env python3
"""
Quick script to check what environment variables are actually being detected
"""

import os

def check_env_vars():
    print("🔍 Environment Variable Check")
    print("=" * 50)
    
    # Check all Firebase variables
    firebase_vars = {
        'FIREBASE_PROJECT_ID': os.getenv('FIREBASE_PROJECT_ID'),
        'FIREBASE_PRIVATE_KEY_ID': os.getenv('FIREBASE_PRIVATE_KEY_ID'),
        'FIREBASE_PRIVATE_KEY': os.getenv('FIREBASE_PRIVATE_KEY'),
        'FIREBASE_CLIENT_EMAIL': os.getenv('FIREBASE_CLIENT_EMAIL'),
        'FIREBASE_CLIENT_ID': os.getenv('FIREBASE_CLIENT_ID'),
        'FIREBASE_CLIENT_X509_CERT_URL': os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
        'FIREBASE_STORAGE_BUCKET': os.getenv('FIREBASE_STORAGE_BUCKET'),
    }
    
    print("Firebase Environment Variables:")
    for var, value in firebase_vars.items():
        if value:
            if 'PRIVATE_KEY' in var:
                print(f"  ✅ {var}: {'*' * min(len(value), 20)}...")
            else:
                print(f"  ✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
        else:
            print(f"  ❌ {var}: NOT SET")
    
    print()
    
    # Check other critical variables
    other_vars = {
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'PORT': os.getenv('PORT'),
        'HOST': os.getenv('HOST'),
    }
    
    print("Other Environment Variables:")
    for var, value in other_vars.items():
        if value:
            if 'API_KEY' in var:
                print(f"  ✅ {var}: {'*' * min(len(value), 20)}...")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NOT SET")
    
    print()
    print("📊 Summary:")
    firebase_set = sum(1 for v in firebase_vars.values() if v)
    other_set = sum(1 for v in other_vars.values() if v)
    
    print(f"Firebase variables set: {firebase_set}/{len(firebase_vars)}")
    print(f"Other variables set: {other_set}/{len(other_vars)}")
    
    if firebase_set == len(firebase_vars) and other_set == len(other_vars):
        print("🎉 All environment variables are properly set!")
    elif firebase_set > 0:
        print("⚠️  Some environment variables are set, but not all")
    else:
        print("❌ No environment variables are set - using fallbacks")

if __name__ == "__main__":
    check_env_vars() 