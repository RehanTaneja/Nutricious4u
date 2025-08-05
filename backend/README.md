# Nutricious4u Backend

## Firebase Setup

### For Local Development:
1. Download your Firebase service account key from Google Cloud Console
2. Replace the placeholder values in `services/firebase_service_account.json` with your real credentials
3. **IMPORTANT**: Never commit the real credentials to git

### For Production (Railway):
The app uses environment variables for Firebase credentials. Set these in Railway:

- `FIREBASE_PROJECT_ID`
- `FIREBASE_PRIVATE_KEY`
- `FIREBASE_CLIENT_EMAIL`
- `FIREBASE_CLIENT_ID`
- `FIREBASE_PRIVATE_KEY_ID`
- `FIREBASE_CLIENT_X509_CERT_URL`
- `GEMINI_API_KEY`

### Security Notes:
- The `firebase_service_account.json` file is for local development only
- Production deployments use environment variables
- Never commit real credentials to version control 