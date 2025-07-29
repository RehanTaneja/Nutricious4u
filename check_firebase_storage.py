#!/usr/bin/env python3
"""
Script to check Firebase Storage for diet PDFs
"""

import os
import sys

# Add the current directory to the path so we can import services
sys.path.append('.')

from services.firebase_client import bucket, db as firestore_db

def check_firebase_storage():
    """Check Firebase Storage for diet PDFs"""
    
    print("Checking Firebase Storage for diet PDFs...")
    print("=" * 50)
    
    # Check user profile in Firestore
    user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    
    try:
        # Get user profile from Firestore
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            print(f"User profile found:")
            print(f"  dietPdfUrl: {user_data.get('dietPdfUrl', 'Not found')}")
            print(f"  lastDietUpload: {user_data.get('lastDietUpload', 'Not found')}")
            
            diet_pdf_url = user_data.get('dietPdfUrl')
            if diet_pdf_url:
                print(f"\nChecking Firebase Storage for: {diet_pdf_url}")
                
                # If it's a filename, check in Storage
                if diet_pdf_url.endswith('.pdf'):
                    blob_path = f"diets/{user_id}/{diet_pdf_url}"
                    blob = bucket.blob(blob_path)
                    
                    if blob.exists():
                        print(f"✓ PDF found in Storage at: {blob_path}")
                        print(f"  Size: {blob.size} bytes")
                        print(f"  Created: {blob.time_created}")
                        
                        # Generate a signed URL
                        from datetime import timedelta
                        signed_url = blob.generate_signed_url(
                            version="v4",
                            expiration=timedelta(hours=1),
                            method="GET"
                        )
                        print(f"  Signed URL: {signed_url[:100]}...")
                    else:
                        print(f"✗ PDF not found in Storage at: {blob_path}")
                        
                        # List all blobs in the user's diet folder
                        print(f"\nListing all files in diets/{user_id}/:")
                        blobs = bucket.list_blobs(prefix=f"diets/{user_id}/")
                        for blob in blobs:
                            print(f"  - {blob.name} ({blob.size} bytes)")
                
                elif diet_pdf_url.startswith('https://storage.googleapis.com/'):
                    print(f"✓ Firebase Storage signed URL found: {diet_pdf_url[:100]}...")
                
                else:
                    print(f"Unknown URL format: {diet_pdf_url}")
            else:
                print("No dietPdfUrl found in user profile")
        else:
            print(f"User profile not found for ID: {user_id}")
            
    except Exception as e:
        print(f"Error checking Firebase: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_firebase_storage() 