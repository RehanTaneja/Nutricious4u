import firebase_admin
from firebase_admin import credentials, firestore
import os

# Build a robust path to the service account file
# This starts from the location of the current file (__file__)
# and navigates to the 'backend' directory to find the JSON file.
try:
    current_dir = os.path.dirname(__file__)
    cred_path = os.path.abspath(os.path.join(current_dir, 'firebase_service_account.json'))

    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Service account key not found at the expected path: {cred_path}")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"!!!!!!!!!! FIREBASE INITIALIZATION FAILED !!!!!!!!!!")
    print(f"Failed to initialize Firebase: {e}")
    db = None