#!/usr/bin/env python3
"""
Check Railway environment variables for Nutricious4u deployment
"""

import os
import sys
from datetime import datetime

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking Railway Environment Variables...")
    print(f"Timestamp: {datetime.utcnow()}")
    print(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'production')}")
    print()
    
    # Required variables
    required_vars = {
        'FIREBASE_PROJECT_ID': 'Firebase Project ID',
        'FIREBASE_PRIVATE_KEY_ID': 'Firebase Private Key ID',
        'FIREBASE_CLIENT_EMAIL': 'Firebase Client Email',
        'FIREBASE_CLIENT_ID': 'Firebase Client ID',
        'FIREBASE_CLIENT_X509_CERT_URL': 'Firebase Client X509 Cert URL',
        'FIREBASE_STORAGE_BUCKET': 'Firebase Storage Bucket',
        'FIREBASE_PRIVATE_KEY': 'Firebase Private Key',
        'GEMINI_API_KEY': 'Gemini API Key'
    }
    
    missing_vars = []
    present_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PRIVATE' in var:
                display_value = f"{'*' * min(len(value), 20)}..."
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            
            print(f"✅ {var}: {display_value}")
            present_vars.append(var)
        else:
            print(f"❌ {var}: MISSING")
            missing_vars.append(var)
    
    print()
    print("=" * 50)
    print("📊 Summary:")
    print(f"Present: {len(present_vars)}/{len(required_vars)}")
    print(f"Missing: {len(missing_vars)}/{len(required_vars)}")
    
    if missing_vars:
        print(f"\n❌ Missing variables: {', '.join(missing_vars)}")
        print("\nTo fix this:")
        print("1. Go to Railway Dashboard")
        print("2. Select your project")
        print("3. Go to Variables tab")
        print("4. Add the missing environment variables")
        print("5. Redeploy your application")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

def check_private_key_format():
    """Check if the Firebase private key is properly formatted"""
    print("\n🔐 Checking Firebase Private Key Format...")
    
    private_key = os.getenv('FIREBASE_PRIVATE_KEY')
    if not private_key:
        print("❌ FIREBASE_PRIVATE_KEY is not set")
        return False
    
    # Check for proper formatting
    issues = []
    
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
        issues.append("Missing or incorrect header")
    
    if not private_key.endswith('-----END PRIVATE KEY-----'):
        issues.append("Missing or incorrect footer")
    
    if '\\n' in private_key:
        issues.append("Contains escaped newlines (\\n) - should be actual newlines")
    
    if not any(char.isdigit() for char in private_key):
        issues.append("No digits found - may be empty or malformed")
    
    if issues:
        print("❌ Private key formatting issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nTo fix:")
        print("1. Copy the private key from your Firebase service account JSON")
        print("2. Make sure it includes the header and footer")
        print("3. Replace \\n with actual newlines")
        print("4. Add it exactly as shown in the deployment guide")
        return False
    else:
        print("✅ Private key appears to be properly formatted")
        return True

def check_railway_specific():
    """Check Railway-specific environment variables"""
    print("\n🚂 Checking Railway-specific variables...")
    
    railway_vars = {
        'RAILWAY_ENVIRONMENT': 'Railway Environment',
        'PORT': 'Port (should be set by Railway)',
        'RAILWAY_STATIC_URL': 'Railway Static URL'
    }
    
    for var, description in railway_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (may be normal)")

def main():
    """Run all checks"""
    print("🚀 Railway Environment Check for Nutricious4u")
    print("=" * 60)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Check private key format
    key_ok = check_private_key_format()
    
    # Check Railway-specific variables
    check_railway_specific()
    
    print("\n" + "=" * 60)
    print("📋 Final Status:")
    
    if env_ok and key_ok:
        print("🎉 All checks passed! Your Railway deployment should work correctly.")
        print("\nNext steps:")
        print("1. Deploy to Railway")
        print("2. Check the /health endpoint")
        print("3. Monitor the deployment logs")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above before deploying.")
        print("\nCommon fixes:")
        print("- Add missing environment variables in Railway dashboard")
        print("- Fix private key formatting")
        print("- Redeploy after making changes")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 