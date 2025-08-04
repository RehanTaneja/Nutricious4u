#!/bin/bash

echo "🚀 Nutricious4u Production Deployment Script"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Check if backend URL is set
echo ""
echo "Step 1: Checking backend configuration..."
if grep -q "your-actual-production-backend-url.com" .env; then
    print_error "Backend URL is still set to placeholder!"
    echo "Please update .env file with your deployed backend URL"
    echo "Example: PRODUCTION_BACKEND_URL=https://your-app.railway.app"
    exit 1
else
    print_status "Backend URL is configured"
fi

# Step 2: Check Firebase configuration
echo ""
echo "Step 2: Checking Firebase configuration..."
if [ -f "google-services.json" ] && [ -f "GoogleService-Info.plist" ]; then
    print_status "Firebase configuration files found"
else
    print_warning "Firebase configuration files may be outdated"
    echo "Please download fresh config files from Firebase Console"
fi

# Step 3: Check environment variables
echo ""
echo "Step 3: Checking environment variables..."
required_vars=("API_KEY" "AUTH_DOMAIN" "PROJECT_ID" "STORAGE_BUCKET" "MESSAGING_SENDER_ID" "APP_ID" "PRODUCTION_BACKEND_URL")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -eq 0 ]; then
    print_status "All required environment variables are set"
else
    print_error "Missing environment variables: ${missing_vars[*]}"
    exit 1
fi

# Step 4: TypeScript compilation check
echo ""
echo "Step 4: Checking TypeScript compilation..."
if npx tsc --noEmit; then
    print_status "TypeScript compilation successful"
else
    print_error "TypeScript compilation failed"
    exit 1
fi

# Step 5: Build preview
echo ""
echo "Step 5: Building preview version..."
echo "This will create a test build to verify everything works"
echo "Press Enter to continue or Ctrl+C to cancel..."
read

print_status "Starting EAS preview build..."
eas build --profile preview --platform android

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Test the preview build thoroughly"
echo "2. If everything works, run: eas build --profile production --platform android"
echo "3. For app store submission: eas submit --profile production --platform android"
echo ""
echo "📚 Documentation:"
echo "- Firebase Setup: FIREBASE_PRODUCTION_SETUP.md"
echo "- Production Guide: PRODUCTION_DEPLOYMENT.md" 