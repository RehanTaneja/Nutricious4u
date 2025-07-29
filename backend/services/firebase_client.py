import firebase_admin
from firebase_admin import credentials, firestore
import os
from fastapi import HTTPException
# Add storage import
from firebase_admin import storage
import requests
import json
from datetime import datetime, timedelta

# Build a robust path to the service account file
# This starts from the location of the current file (__file__)
# and navigates to the 'backend' directory to find the JSON file.
try:
    current_dir = os.path.dirname(__file__)
    cred_path = os.path.abspath(os.path.join(current_dir, 'firebase_service_account.json'))

    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Service account key not found at the expected path: {cred_path}")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'nutricious4u-diet-storage')
    })
    db = firestore.client()
    bucket = storage.bucket()
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"!!!!!!!!!! FIREBASE INITIALIZATION FAILED !!!!!!!!!!")
    print(f"Failed to initialize Firebase: {e}")
    db = None
    bucket = None

if db is None or bucket is None:
    raise HTTPException(status_code=500, detail="Firestore or Storage is not initialized. Check server logs for details.")

# --- Diet PDF Upload Helper ---
def upload_diet_pdf(user_id: str, file_data: bytes, filename: str) -> str:
    """
    Uploads a diet PDF to Firebase Storage for a user and returns the download URL.
    """
    try:
        print(f"Attempting to upload PDF for user {user_id} with filename {filename}")
        blob_path = f"diets/{user_id}/{filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(file_data, content_type='application/pdf')
        
        # For uniform bucket-level access, we need to generate a signed URL instead of making public
        # Generate a signed URL that expires in 7 days (maximum allowed)
        from datetime import timedelta
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(days=7),
            method="GET"
        )
        print(f"Successfully uploaded PDF to Storage. Signed URL: {signed_url}")
        return signed_url
    except Exception as e:
        print(f"Failed to upload diet PDF to Storage: {e}")
        # Fallback: store in Firestore as base64 for now
        try:
            import base64
            pdf_base64 = base64.b64encode(file_data).decode('utf-8')
            doc_ref = db.collection('diet_pdfs').document(user_id)
            doc_ref.set({
                'filename': filename,
                'pdf_data': pdf_base64,
                'uploaded_at': datetime.now().isoformat(),
                'content_type': 'application/pdf'
            })
            print(f"Stored PDF in Firestore as fallback for user {user_id}")
            return f"firestore://diet_pdfs/{user_id}"
        except Exception as fallback_error:
            print(f"Fallback storage also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail="Failed to upload diet PDF.")

# --- List All Users Except Dietician ---
def list_non_dietician_users():
    """
    Returns a list of user profiles where isDietician is not True.
    """
    try:
        users_ref = db.collection("user_profiles")
        users = users_ref.where("isDietician", "!=", True).stream()
        return [u.to_dict() for u in users]
    except Exception as e:
        print(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users.")

# --- Get User Notification Token ---
def get_user_notification_token(user_id: str) -> str:
    try:
        doc = db.collection("user_profiles").document(user_id).get()
        if not doc.exists:
            return None
        # Check for both expoPushToken and notificationToken
        data = doc.to_dict()
        return data.get("expoPushToken") or data.get("notificationToken")
    except Exception as e:
        print(f"Failed to get notification token: {e}")
        return None

# --- Send Push Notification via Expo ---
def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """
    Send push notification using Expo's push service
    """
    if not token:
        print("No notification token provided")
        return False
    
    try:
        # Expo push notification payload
        message = {
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "data": data or {}
        }
        
        # Send to Expo's push service
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            headers={
                "Accept": "application/json",
                "Accept-encoding": "gzip, deflate",
                "Content-Type": "application/json",
            },
            data=json.dumps(message)
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("data", {}).get("status") == "error":
                print(f"Expo push error: {result}")
                return False
            print(f"Push notification sent successfully: {title} - {body}")
            return True
        else:
            print(f"Failed to send push notification: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False

# --- Get Dietician Notification Token ---
def get_dietician_notification_token() -> str:
    """
    Get the notification token for the dietician account
    """
    try:
        # Find the dietician user
        users_ref = db.collection("user_profiles")
        dietician_query = users_ref.where("isDietician", "==", True).limit(1).stream()
        
        for user in dietician_query:
            data = user.to_dict()
            return data.get("expoPushToken") or data.get("notificationToken")
        
        return None
    except Exception as e:
        print(f"Failed to get dietician notification token: {e}")
        return None

# --- Check Users with 1 Day Remaining ---
def check_users_with_one_day_remaining():
    """
    Check all users and notify dietician if any user has 1 day remaining
    """
    try:
        users_ref = db.collection("user_profiles")
        users = users_ref.where("isDietician", "!=", True).stream()
        
        one_day_users = []
        for user in users:
            data = user.to_dict()
            last_upload = data.get("lastDietUpload")
            
            if last_upload:
                # Convert to datetime if it's a string
                if isinstance(last_upload, str):
                    last_upload = datetime.fromisoformat(last_upload.replace('Z', '+00:00'))
                
                # Calculate days remaining
                days_elapsed = (datetime.now() - last_upload).days
                days_remaining = 7 - days_elapsed
                
                if days_remaining == 1:
                    one_day_users.append({
                        "userId": user.id,
                        "name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
                        "email": data.get('email', '')
                    })
        
        # Send notification to dietician if any users have 1 day remaining
        if one_day_users:
            dietician_token = get_dietician_notification_token()
            if dietician_token:
                user_names = ", ".join([user["name"] for user in one_day_users])
                send_push_notification(
                    dietician_token,
                    "Diet Reminder",
                    f"1 day left for {user_names}'s diet",
                    {"type": "diet_reminder", "users": one_day_users}
                )
                print(f"Sent diet reminder notification for {len(one_day_users)} users")
        
        return one_day_users
        
    except Exception as e:
        print(f"Error checking users with one day remaining: {e}")
        return []