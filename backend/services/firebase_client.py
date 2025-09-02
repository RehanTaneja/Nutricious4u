import firebase_admin
from firebase_admin import credentials, firestore
import os
from fastapi import HTTPException
# Add storage import
from firebase_admin import storage
import requests
import json
from datetime import datetime, timedelta

# Initialize Firebase using environment variables
def initialize_firebase():
    """Initialize Firebase with proper error handling and fallback mechanisms"""
    try:
        print("🔥 Initializing Firebase...")
        
        # Check if Firebase is already initialized
        try:
            # Try to get the default app
            default_app = firebase_admin.get_app()
            print("✅ Firebase already initialized, using existing app")
            db = firestore.client()
            bucket = storage.bucket()
            return db, bucket
        except ValueError:
            # Firebase not initialized yet, continue with initialization
            pass
        
        # Get basic project info
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET', 'nutricious4u-diet-storage')
        
        if not project_id:
            print("❌ FIREBASE_PROJECT_ID is required")
            raise ValueError("FIREBASE_PROJECT_ID is required")
        
        # Try to get environment variables first
        private_key = os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
        client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        private_key_id = os.getenv('FIREBASE_PRIVATE_KEY_ID')
        client_id = os.getenv('FIREBASE_CLIENT_ID')
        client_x509_cert_url = os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
        
        # If we have the private key from environment, use it
        if private_key and client_email:
            print("✅ Using environment variables for Firebase")
            
            # Ensure private key is properly formatted
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                print("⚠️  Private key doesn't start with proper header, attempting to fix...")
                if '-----BEGIN PRIVATE KEY-----' in private_key:
                    start = private_key.find('-----BEGIN PRIVATE KEY-----')
                    end = private_key.find('-----END PRIVATE KEY-----') + len('-----END PRIVATE KEY-----')
                    private_key = private_key[start:end]
                else:
                    private_key = f"-----BEGIN PRIVATE KEY-----\n{private_key}\n-----END PRIVATE KEY-----"
            
            # Build service account info
            service_account_info = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": private_key_id or "placeholder",
                "private_key": private_key,
                "client_email": client_email,
                "client_id": client_id or "placeholder",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": client_x509_cert_url or f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email}",
                "universe_domain": "googleapis.com"
            }
            
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket})
            
            db = firestore.client()
            bucket = storage.bucket()
            print("✅ Firebase initialized successfully with environment variables.")
            return db, bucket
        
        # If environment variables are missing, try file-based approach
        print("📄 Using file-based Firebase credentials...")
        
        # Try to find the service account file
        possible_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'firebase_service_account.json')),
            os.path.abspath(os.path.join(os.getcwd(), 'services', 'firebase_service_account.json')),
            os.path.abspath(os.path.join(os.getcwd(), 'firebase_service_account.json')),
            '/app/services/firebase_service_account.json',
            '/app/firebase_service_account.json'
        ]
        
        for cred_path in possible_paths:
            if os.path.exists(cred_path):
                print(f"📄 Found service account file at: {cred_path}")
                try:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket})
                    db = firestore.client()
                    bucket = storage.bucket()
                    print("✅ Firebase initialized successfully with file-based credentials.")
                    return db, bucket
                except Exception as e:
                    print(f"❌ Failed to initialize with file {cred_path}: {e}")
                    continue
        
        # If no file found, create a minimal service account with default values
        print("🔄 Creating minimal Firebase configuration...")
        
        # Use default values for missing environment variables
        default_client_email = f"firebase-adminsdk-fbsvc@{project_id}.iam.gserviceaccount.com"
        default_private_key = os.getenv('FIREBASE_PRIVATE_KEY', '')
        
        service_account_info = {
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
            "private_key": default_private_key,
            "client_email": default_client_email,
            "client_id": os.getenv('FIREBASE_CLIENT_ID', ''),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{default_client_email}",
            "universe_domain": "googleapis.com"
        }
        
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket})
        
        db = firestore.client()
        bucket = storage.bucket()
        print("✅ Firebase initialized successfully with default configuration.")
        return db, bucket
        
    except Exception as e:
        print(f"!!!!!!!!!! FIREBASE INITIALIZATION FAILED !!!!!!!!!!")
        print(f"Failed to initialize Firebase: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# Initialize Firebase at module level
db, bucket = initialize_firebase()

# Check if initialization was successful
if db is None or bucket is None:
    print("❌ Firebase initialization failed completely")
    # Don't raise exception here, let the application start but handle errors in endpoints
    db = None
    bucket = None

# Export the initialize function for reinitialization
__all__ = ['db', 'bucket', 'initialize_firebase', 'upload_diet_pdf', 'list_non_dietician_users', 
           'get_user_notification_token', 'send_push_notification', 'check_users_with_one_day_remaining']

# --- Diet PDF Upload Helper ---
def upload_diet_pdf(user_id: str, file_data: bytes, filename: str) -> str:
    """
    Uploads a diet PDF to Firebase Storage for a user and returns the download URL.
    """
    if db is None or bucket is None:
        raise HTTPException(status_code=500, detail="Firebase is not initialized. Please check server configuration.")
    
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
    Only includes users with paid plans (not free plan).
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Firebase is not initialized. Please check server configuration.")
    
    try:
        users_ref = db.collection("user_profiles")
        # Get all users and filter in Python instead of Firestore query
        all_users = users_ref.stream()
        non_dietician_users = []
        
        for user in all_users:
            user_data = user.to_dict()
            # Skip users with isDietician = True, include all others
            if user_data.get("isDietician") != True:
                # Skip placeholder users and test users
                is_placeholder = (
                    user_data.get("firstName", "User") == "User" and
                    user_data.get("lastName", "") == "" and
                    (not user_data.get("email") or user_data.get("email", "").endswith("@example.com"))
                )
                
                # Skip test users
                is_test_user = (
                    user_data.get("firstName", "").lower() == "test" or
                    user_data.get("email", "").startswith("test@") or
                    user_data.get("userId", "").startswith("test_") or
                    "test" in user_data.get("userId", "").lower()
                )
                
                # Skip users without proper names
                has_proper_name = (
                    user_data.get("firstName") and 
                    user_data.get("firstName") != "User" and
                    user_data.get("firstName") != "Test" and
                    user_data.get("firstName").strip() != ""
                )
                
                # Only include users with paid plans (not free plan)
                subscription_plan = user_data.get("subscriptionPlan")
                has_paid_plan = (
                    subscription_plan and 
                    subscription_plan != "free" and 
                    subscription_plan != "Not set" and 
                    subscription_plan != ""
                )
                
                if not is_placeholder and not is_test_user and has_proper_name and has_paid_plan:
                    # Add the document ID as userId
                    user_data["userId"] = user.id
                    non_dietician_users.append(user_data)
        
        print(f"Found {len(non_dietician_users)} non-dietician users with paid plans")
        return non_dietician_users
    except Exception as e:
        print(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users.")

# --- Get User Notification Token ---
def get_user_notification_token(user_id: str) -> str:
    if db is None:
        print("Firebase not initialized, cannot get notification token")
        return None
    
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
    if db is None:
        print("Firebase not initialized, cannot get dietician notification token")
        return None
    
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
    if db is None:
        print("Firebase not initialized, cannot check users with one day remaining")
        return []
    
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
                
                # Calculate days remaining using same logic as main API
                from datetime import timezone
                now = datetime.now(timezone.utc)
                
                # Ensure last_upload is timezone-aware for comparison
                if last_upload.tzinfo is None:
                    last_upload = last_upload.replace(tzinfo=timezone.utc)
                
                time_diff = now - last_upload
                total_hours_remaining = max(0, 168 - int(time_diff.total_seconds() / 3600))
                days_remaining = total_hours_remaining // 24
                
                if days_remaining == 1:
                    # Get proper user name (first name + last name)
                    first_name = data.get('firstName', '').strip()
                    last_name = data.get('lastName', '').strip()
                    
                    # Create proper name format
                    if first_name and last_name:
                        full_name = f"{first_name} {last_name}"
                    elif first_name:
                        full_name = first_name
                    elif last_name:
                        full_name = last_name
                    else:
                        full_name = "User"  # Fallback
                    
                    one_day_users.append({
                        "userId": user.id,
                        "name": full_name,
                        "firstName": first_name,
                        "lastName": last_name,
                        "email": data.get('email', '')
                    })
        
        # Send notification to dietician if any users have 1 day remaining
        if one_day_users:
            dietician_token = get_dietician_notification_token()
            if dietician_token:
                # Create proper message with user names
                if len(one_day_users) == 1:
                    user_name = one_day_users[0]["name"]
                    message = f"{user_name} has 1 day left in their diet"
                else:
                    user_names = [user["name"] for user in one_day_users]
                    message = f"{', '.join(user_names)} have 1 day left in their diets"
                
                send_push_notification(
                    dietician_token,
                    "Diet Reminder",
                    message,
                    {"type": "diet_reminder", "users": one_day_users}
                )
                print(f"Sent diet reminder notification to dietician: {message}")
            else:
                print("No dietician notification token found")
        
        return one_day_users
        
    except Exception as e:
        print(f"Error checking users with one day remaining: {e}")
        return []