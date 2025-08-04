# Railway Deployment Guide for Nutricious4u

## Overview
This guide will help you deploy the Nutricious4u backend to Railway with proper Firebase configuration.

## Prerequisites
- Railway account
- Firebase project with Firestore and Storage enabled
- Firebase service account key

## Step 1: Firebase Setup

### 1.1 Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing project
3. Enable Firestore Database
4. Enable Storage
5. Create a service account key

### 1.2 Get Service Account Key
1. In Firebase Console, go to Project Settings
2. Go to Service Accounts tab
3. Click "Generate new private key"
4. Download the JSON file
5. Keep this file secure - it contains sensitive credentials

## Step 2: Railway Deployment

### 2.1 Connect to Railway
1. Go to [Railway Dashboard](https://railway.app/)
2. Create a new project
3. Connect your GitHub repository
4. Select the `backend` directory as the source

### 2.2 Set Environment Variables
Add these environment variables in Railway:

#### Required Firebase Variables:
```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_CLIENT_EMAIL=your-service-account-email
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_X509_CERT_URL=your-cert-url
FIREBASE_STORAGE_BUCKET=your-storage-bucket
```

#### Firebase Private Key (Important!):
```
FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDUnYDUWCWA7eTc
m6LNim/X7eXcwfCmK6+Ki3G08iBsysfMkUsPlIK2Yo6LtzWGaSpca8DBypR+bO6G
ODlFiekRlQUERBLlSuxiOUhrf9nLlTKx1tcVRg/4iy0Y4Gl0QZ4AxLaun2DH9yh0
F6QJKv/G+/nhAeOmHj4Jye+JCeKfRmqulUwdEXqc5tQPSxAFF1r1BhNQYKdd4Zq8
PD/ytqpeF5FB2o+6oqAdRzA4EnrnLzI5E+95tLk/sbh5U6j0bHACsLqxlarSfDeR
fJDL10O6SppK9VcPRDZrWQPDJNhSjb157t+ZqJX/Cp5H0hJbAtIpoU68t02GW/P5
JUS9ooGdAgMBAAECggEAGJKIdmImmXdFFUsGfo9SnEfSIlimvam8XLx/fHxkS3aH
L2kWXftZvQb4dwTKUpm6a9qHOU52qYLg8VGzqsoEzgOlRAgzD92AIt0Ade4dh4Yb
iQqtqneBtoWtRVwATA+eWXPish1Y49t4iSxHSMj3rTFngH4Fp6gEnwB/5txl3Obi
HvCsuC0X0E/1ZFn7pJf/fG63q6+wSTSeFku2mE3PXFAy8/Q7H8dpefVtS9DuWp8z
K6D4oyd07ynyf2jlhudfoEpYQYpspY4p1ava0p8NjNXfhrxxx9rdauljQvpc2i7t
m2Kw1qB+EL77l8Z1UIRvLOasLlNdVnwk4kRSHL95kQKBgQD/BZkNEStQ9xLE3ALv
BiME8dJ00CYOsAWSWzRYf+aT+oE/P4ERYGP1dEWGV1UwH3R+9ev9MUU9GeGqhByu
riva/eQ50uW4VWxd5f+PSjBiNBYizgCI1lwP+xwgf2NwpwHT/c9WgXKQvFPFAJ5k
E+y+l68aMjw2FuPYiIGQF2KaMQKBgQDVbkRXjju5eRYngg3NCYuqxgterN1n4sQn
CZMxPS1vGRnqRpU/P/2LdbqItGVxh1UbuRvauJOUOagVAn4mxMxOFin2uLEBa3e3
rIeX8gUbI0/99gqLx+EEkjqiYCrlgni623wTyzb8WuMdFih/sgaDmf7PNDdrxLF5
/IrZzOMXLQKBgAtgyI9YsMIQA/pchpT7hRx3XZhwoQIOwHDjONap/jOj/ZhA0RVh
Y5RT97Yit15KSPxRJJJLXHd5bCQbeNwiUTqYEVKzIiSzSv51gI14FeiLwmETJ9rz
FXBxF7QrethP2zkGHfYSGHZ0sJgdivOUH//w7JMSorUXGFtU29L9+BxBAoGAIpu9
w0DSGHI1EHT7TeslVazFfTWktUrFKdtYndxguKomVKHbY6U5tNqDQ9WUuYMLXvJ2
PNI/RALRaY687AZvZp4bceFi+mr1v7ffSNk60Lq6JuE1tpLTvw0DKv9TFWJBt3MN
vJvwL52BRF8qdAJnIgHfmrPJ5NTBPpmf3k9l54UCgYB+E4KDfo9Z5BEd/oZ39R/s
oCdhnZdXpeCgQDSQH+wBwXDHnk1VqyDS2UtD6xcQLVEiXY8uKFvhSft04TMRBxAs
9MMKKpoOHZV3v3uTPMDegjF5Wj1dnWbKuZ+O+mJpzs4LynNTzCxOnS8gYyFEjw6H
10CkLfJA/OYvZPAoBhJyZw==
-----END PRIVATE KEY-----
```

#### Other Required Variables:
```
GEMINI_API_KEY=your-gemini-api-key
```

### 2.3 Important Notes for Private Key

**CRITICAL**: The private key must be formatted exactly as shown above with:
- Proper line breaks (`\n` characters)
- `-----BEGIN PRIVATE KEY-----` header
- `-----END PRIVATE KEY-----` footer
- All the key content in between

**Common Issues:**
- If the key is missing the header/footer, add them
- If the key has escaped newlines (`\\n`), replace with actual newlines (`\n`)
- Make sure there are no extra spaces or characters

## Step 3: Deploy

### 3.1 Automatic Deployment
1. Railway will automatically detect the Python project
2. It will use the `railway.json` configuration
3. The app will start with `uvicorn server:app --host 0.0.0.0 --port $PORT`

### 3.2 Manual Deployment
If automatic deployment fails:
1. Go to Railway project settings
2. Set the build command: `pip install -r requirements.txt`
3. Set the start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

## Step 4: Verify Deployment

### 4.1 Health Check
Visit your Railway URL + `/health` to check if the service is running:
```
https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "firebase": "connected",
  "gemini": "configured",
  "services": {
    "firebase": "connected",
    "gemini": "configured",
    "pdf_rag": "available",
    "diet_notifications": "available"
  }
}
```

### 4.2 Test Firebase Connection
Run the test script locally to verify Firebase configuration:
```bash
cd backend
python test_firebase_connection.py
```

## Troubleshooting

### Firebase Connection Issues

#### Error: "MalformedFraming"
This means the private key is not properly formatted.

**Solution:**
1. Copy the private key from your Firebase service account JSON
2. Make sure it includes the header and footer
3. Replace `\\n` with `\n` if present
4. Add the key exactly as shown in the example above

#### Error: "Failed to initialize a certificate credential"
This usually means missing or incorrect environment variables.

**Solution:**
1. Check all required environment variables are set
2. Verify the private key format
3. Ensure no extra spaces or characters in the values

#### Error: "Firebase service is currently unavailable"
This means Firebase failed to initialize but the app is still running.

**Solution:**
1. Check the deployment logs for Firebase initialization errors
2. Verify environment variables are correct
3. The app will use file-based credentials as fallback

### Deployment Issues

#### Build Fails
1. Check that `requirements.txt` exists and is valid
2. Verify Python version compatibility
3. Check Railway logs for specific error messages

#### App Won't Start
1. Check the start command in `railway.json`
2. Verify the `server.py` file exists
3. Check for import errors in the logs

### Environment Variables Not Working
1. Make sure variables are set in Railway dashboard
2. Redeploy after changing environment variables
3. Check that variable names match exactly (case-sensitive)

## Support

If you continue to have issues:
1. Check Railway deployment logs
2. Run the Firebase test script locally
3. Verify all environment variables are set correctly
4. Ensure the private key is properly formatted

## Security Notes

- Never commit the Firebase service account JSON to version control
- Use environment variables for all sensitive data
- Regularly rotate Firebase service account keys
- Monitor Railway logs for any security issues 