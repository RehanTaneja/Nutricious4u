#!/usr/bin/env python3
"""
Script to fix the dietPdfUrl in Firestore
"""

import os
import sys

# Add the current directory to the path so we can import services
sys.path.append('.')

from services.firebase_client import db as firestore_db

def fix_diet_pdf_url():
    """Fix the dietPdfUrl in the user's profile"""
    
    print("Fixing dietPdfUrl in Firestore...")
    print("=" * 50)
    
    user_id = "EMoXb6rFuwN3xKsotq54K0kVArf1"
    correct_filename = "MS%20SANDHYA%20GOEL-17%20TH%20JULY%20%2C%20%20%2025%20(1).pdf"
    
    try:
        # Get current user profile
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            current_diet_pdf_url = user_data.get('dietPdfUrl')
            print(f"Current dietPdfUrl: {current_diet_pdf_url}")
            print(f"Correct filename: {correct_filename}")
            
            if current_diet_pdf_url != correct_filename:
                print("Updating dietPdfUrl...")
                
                # Update the document
                firestore_db.collection("user_profiles").document(user_id).update({
                    "dietPdfUrl": correct_filename
                })
                
                print("✓ dietPdfUrl updated successfully")
                
                # Verify the update
                updated_doc = firestore_db.collection("user_profiles").document(user_id).get()
                updated_data = updated_doc.to_dict()
                print(f"New dietPdfUrl: {updated_data.get('dietPdfUrl')}")
            else:
                print("✓ dietPdfUrl is already correct")
        else:
            print(f"User profile not found for ID: {user_id}")
            
    except Exception as e:
        print(f"Error fixing dietPdfUrl: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_diet_pdf_url() 