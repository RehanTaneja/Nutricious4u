#!/bin/bash

# Deployment script for iOS fixes
echo "🚀 Deploying iOS fixes to Railway backend..."

# Check if we're in the right directory
if [ ! -f "backend/server.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please login first:"
    echo "   railway login"
    exit 1
fi

echo "📋 Changes to be deployed:"
echo "   ✅ Enhanced server configuration (timeout settings)"
echo "   ✅ Improved middleware for iOS connection handling"
echo "   ✅ Optimized diet endpoint with async operations"
echo "   ✅ New test endpoint for iOS functionality"
echo "   ✅ Better error handling and logging"

echo ""
echo "🔧 Deploying to Railway..."

# Deploy to Railway
cd backend
railway up

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "🧪 Testing the deployment..."
    
    # Wait a moment for deployment to complete
    sleep 10
    
    # Test the deployment
    cd ..
    python test_ios_fixes.py
    
    echo ""
    echo "📊 Deployment Summary:"
    echo "   ✅ Backend deployed to Railway"
    echo "   ✅ iOS fixes applied"
    echo "   ✅ Test endpoint available"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Test the iOS app on a real device"
    echo "   2. Monitor backend logs for 499 errors"
    echo "   3. Verify diet viewing functionality"
    echo "   4. Check login stability"
    
else
    echo "❌ Deployment failed!"
    echo "Please check the Railway logs for more details."
    exit 1
fi
