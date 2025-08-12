#!/usr/bin/env python3
"""
Migration script to fix existing user profiles by adding isDietician field.
Run this script to update all existing user profiles.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

try:
    from services.firebase_client import db
    print("✅ Firebase client imported successfully")
except Exception as e:
    print(f"❌ Firebase client import failed: {e}")
    sys.exit(1)

def fix_user_profiles():
    """Fix existing user profiles by adding isDietician field."""
    if db is None:
        print("❌ Firebase is not initialized")
        return
    
    try:
        print("🔍 Fetching all user profiles...")
        users_ref = db.collection("user_profiles")
        all_users = users_ref.stream()
        
        fixed_count = 0
        total_count = 0
        
        for user in all_users:
            total_count += 1
            user_data = user.to_dict()
            user_id = user.id
            
            # Check if isDietician field exists
            if "isDietician" not in user_data:
                # Set isDietician based on email
                if user_data.get("email") == "nutricious4u@gmail.com":
                    user_data["isDietician"] = True
                    print(f"✅ Set isDietician=True for dietician: {user_data.get('firstName', 'Unknown')} ({user_data.get('email', 'No email')})")
                else:
                    user_data["isDietician"] = False
                    print(f"✅ Set isDietician=False for user: {user_data.get('firstName', 'Unknown')} ({user_data.get('email', 'No email')})")
                
                # Update the document
                users_ref.document(user_id).update({"isDietician": user_data["isDietician"]})
                fixed_count += 1
            else:
                print(f"ℹ️  User already has isDietician field: {user_data.get('firstName', 'Unknown')} (isDietician={user_data.get('isDietician')})")
        
        print(f"\n🎉 Migration completed!")
        print(f"📊 Total users processed: {total_count}")
        print(f"🔧 Users fixed: {fixed_count}")
        print(f"✅ Users already correct: {total_count - fixed_count}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting user profile migration...")
    fix_user_profiles()
    print("🏁 Migration script completed!")
