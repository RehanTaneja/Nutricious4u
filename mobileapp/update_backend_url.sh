#!/bin/bash

echo "🔧 Backend URL Update Script"
echo "============================"

echo ""
echo "Enter your Railway backend URL (e.g., https://nutricious4u-backend.railway.app):"
read backend_url

if [ -z "$backend_url" ]; then
    echo "❌ No URL provided. Exiting."
    exit 1
fi

# Update the .env file
sed -i '' "s|PRODUCTION_BACKEND_URL=.*|PRODUCTION_BACKEND_URL=$backend_url|" .env

echo ""
echo "✅ Backend URL updated to: $backend_url"
echo ""
echo "Testing configuration..."
./DEPLOYMENT_SCRIPT.sh

echo ""
echo "🎉 Ready to build!"
echo "Run: eas build --profile production --platform android" 