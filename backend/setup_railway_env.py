#!/usr/bin/env python3
"""
Setup Railway Environment Variables for Nutricious4u
This script helps you set up the correct environment variables in Railway
"""

import os
import sys
from datetime import datetime

def print_railway_setup_instructions():
    """Print step-by-step instructions for setting up Railway environment variables"""
    print("🚀 Railway Environment Variables Setup Guide")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow()}")
    print()
    
    print("📋 Step-by-Step Instructions:")
    print("1. Go to your Railway dashboard: https://railway.app/dashboard")
    print("2. Click on your Nutricious4u project")
    print("3. Go to the 'Variables' tab")
    print("4. Add the following environment variables:")
    print()
    
    print("🔧 Required Environment Variables:")
    print("-" * 40)
    
    # Define all required variables with their values
    env_vars = {
        'FIREBASE_PROJECT_ID': 'nutricious4u-63158',
        'FIREBASE_PRIVATE_KEY_ID': '12ef6bab2ae0ca218c25477e6702e412626c10ff',
        'FIREBASE_CLIENT_EMAIL': 'firebase-adminsdk-fbsvc@nutricious4u-63158.iam.gserviceaccount.com',
        'FIREBASE_CLIENT_ID': '110249587534948017563',
        'FIREBASE_CLIENT_X509_CERT_URL': 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40nutricious4u-63158.iam.gserviceaccount.com',
        'FIREBASE_STORAGE_BUCKET': 'nutricious4u-diet-storage',
        'GEMINI_API_KEY': 'AIzaSyDNSOV8CO_IV15t1dxokhfZShHccGF5lB0'
    }
    
    for var, value in env_vars.items():
        if 'PRIVATE_KEY' in var:
            print(f"❌ {var}: [SEE SPECIAL INSTRUCTIONS BELOW]")
        else:
            print(f"✅ {var}: {value}")
    
    print()
    print("🔐 SPECIAL INSTRUCTIONS FOR FIREBASE_PRIVATE_KEY:")
    print("-" * 50)
    print("The FIREBASE_PRIVATE_KEY must be formatted exactly as follows:")
    print()
    print("FIREBASE_PRIVATE_KEY=")
    print("-----BEGIN PRIVATE KEY-----")
    print("MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDUnYDUWCWA7eTc")
    print("m6LNim/X7eXcwfCmK6+Ki3G08iBsysfMkUsPlIK2Yo6LtzWGaSpca8DBypR+bO6G")
    print("ODlFiekRlQUERBLlSuxiOUhrf9nLlTKx1tcVRg/4iy0Y4Gl0QZ4AxLaun2DH9yh0")
    print("F6QJKv/G+/nhAeOmHj4Jye+JCeKfRmqulUwdEXqc5tQPSxAFF1r1BhNQYKdd4Zq8")
    print("PD/ytqpeF5FB2o+6oqAdRzA4EnrnLzI5E+95tLk/sbh5U6j0bHACsLqxlarSfDeR")
    print("fJDL10O6SppK9VcPRDZrWQPDJNhSjb157t+ZqJX/Cp5H0hJbAtIpoU68t02GW/P5")
    print("JUS9ooGdAgMBAAECggEAGJKIdmImmXdFFUsGfo9SnEfSIlimvam8XLx/fHxkS3aH")
    print("L2kWXftZvQb4dwTKUpm6a9qHOU52qYLg8VGzqsoEzgOlRAgzD92AIt0Ade4dh4Yb")
    print("iQqtqneBtoWtRVwATA+eWXPish1Y49t4iSxHSMj3rTFngH4Fp6gEnwB/5txl3Obi")
    print("HvCsuC0X0E/1ZFn7pJf/fG63q6+wSTSeFku2mE3PXFAy8/Q7H8dpefVtS9DuWp8z")
    print("K6D4oyd07ynyf2jlhudfoEpYQYpspY4p1ava0p8NjNXfhrxxx9rdauljQvpc2i7t")
    print("m2Kw1qB+EL77l8Z1UIRvLOasLlNdVnwk4kRSHL95kQKBgQD/BZkNEStQ9xLE3ALv")
    print("BiME8dJ00CYOsAWSWzRYf+aT+oE/P4ERYGP1dEWGV1UwH3R+9ev9MUU9GeGqhByu")
    print("riva/eQ50uW4VWxd5f+PSjBiNBYizgCI1lwP+xwgf2NwpwHT/c9WgXKQvFPFAJ5k")
    print("E+y+l68aMjw2FuPYiIGQF2KaMQKBgQDVbkRXjju5eRYngg3NCYuqxgterN1n4sQn")
    print("CZMxPS1vGRnqRpU/P/2LdbqItGVxh1UbuRvauJOUOagVAn4mxMxOFin2uLEBa3e3")
    print("rIeX8gUbI0/99gqLx+EEkjqiYCrlgni623wTyzb8WuMdFih/sgaDmf7PNDdrxLF5")
    print("/IrZzOMXLQKBgAtgyI9YsMIQA/pchpT7hRx3XZhwoQIOwHDjONap/jOj/ZhA0RVh")
    print("Y5RT97Yit15KSPxRJJJLXHd5bCQbeNwiUTqYEVKzIiSzSv51gI14FeiLwmETJ9rz")
    print("FXBxF7QrethP2zkGHfYSGHZ0sJgdivOUH//w7JMSorUXGFtU29L9+BxBAoGAIpu9")
    print("w0DSGHI1EHT7TeslVazFfTWktUrFKdtYndxguKomVKHbY6U5tNqDQ9WUuYMLXvJ2")
    print("PNI/RALRaY687AZvZp4bceFi+mr1v7ffSNk60Lq6JuE1tpLTvw0DKv9TFWJBt3MN")
    print("vJvwL52BRF8qdAJnIgHfmrPJ5NTBPpmf3k9l54UCgYB+E4KDfo9Z5BEd/oZ39R/s")
    print("oCdhnZdXpeCgQDSQH+wBwXDHnk1VqyDS2UtD6xcQLVEiXY8uKFvhSft04TMRBxAs")
    print("9MMKKpoOHZV3v3uTPMDegjF5Wj1dnWbKuZ+O+mJpzs4LynNTzCxOnS8gYyFEjw6H")
    print("10CkLfJA/OYvZPAoBhJyZw==")
    print("-----END PRIVATE KEY-----")
    print()
    print("⚠️  IMPORTANT NOTES:")
    print("- Copy the entire private key including the BEGIN and END lines")
    print("- Make sure there are no extra spaces or characters")
    print("- The key should be on multiple lines, not all on one line")
    print("- After adding all variables, redeploy your application")
    print()
    print("🔄 After Setting Variables:")
    print("1. Save all the environment variables")
    print("2. Go to the 'Deployments' tab")
    print("3. Click 'Redeploy' to apply the new environment variables")
    print("4. Check the logs to see if Firebase initializes successfully")
    print()
    print("🧪 Testing:")
    print("Visit your Railway URL + /health to check if Firebase is connected")
    print("Example: https://your-app.railway.app/health")

def main():
    """Main function"""
    print_railway_setup_instructions()
    
    print("\n" + "=" * 60)
    print("📊 Current Status Check:")
    
    # Check current environment variables
    current_vars = {
        'FIREBASE_PROJECT_ID': os.getenv('FIREBASE_PROJECT_ID'),
        'FIREBASE_PRIVATE_KEY_ID': os.getenv('FIREBASE_PRIVATE_KEY_ID'),
        'FIREBASE_CLIENT_EMAIL': os.getenv('FIREBASE_CLIENT_EMAIL'),
        'FIREBASE_CLIENT_ID': os.getenv('FIREBASE_CLIENT_ID'),
        'FIREBASE_CLIENT_X509_CERT_URL': os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
        'FIREBASE_STORAGE_BUCKET': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'FIREBASE_PRIVATE_KEY': os.getenv('FIREBASE_PRIVATE_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
    }
    
    print("Current Environment Variables:")
    for var, value in current_vars.items():
        if value:
            if 'PRIVATE_KEY' in var or 'API_KEY' in var:
                print(f"  ✅ {var}: {'*' * min(len(value), 20)}...")
            else:
                print(f"  ✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
        else:
            print(f"  ❌ {var}: NOT SET")
    
    print()
    print("🎯 Next Steps:")
    print("1. Follow the instructions above to set up Railway environment variables")
    print("2. Redeploy your application")
    print("3. Test the /health endpoint")
    print("4. Monitor the deployment logs for Firebase initialization")

if __name__ == "__main__":
    main() 