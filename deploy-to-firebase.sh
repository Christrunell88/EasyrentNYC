#!/bin/bash

# NoFeesApts.com - Firebase Deployment Script
# This script prepares your frontend for Firebase deployment

echo "========================================="
echo "NoFeesApts.com - Firebase Deployment"
echo "========================================="
echo ""

# Step 1: Build Frontend
echo "Step 1: Building React frontend..."
cd /app/frontend
yarn build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ Build successful!"
echo ""

# Step 2: Create deployment package
echo "Step 2: Creating deployment package..."
tar -czf /tmp/nofeesapts-firebase-deploy.tar.gz \
    build/ \
    firebase.json \
    .firebaserc

echo "✅ Package created: /tmp/nofeesapts-firebase-deploy.tar.gz"
echo ""

# Step 3: Show file size
SIZE=$(du -h /tmp/nofeesapts-firebase-deploy.tar.gz | cut -f1)
echo "📦 Package size: $SIZE"
echo ""

# Step 4: Instructions
echo "========================================="
echo "Next Steps:"
echo "========================================="
echo ""
echo "1. Download the package:"
echo "   /tmp/nofeesapts-firebase-deploy.tar.gz"
echo ""
echo "2. On your local machine with Firebase CLI:"
echo "   tar -xzf nofeesapts-firebase-deploy.tar.gz"
echo "   firebase deploy --only hosting"
echo ""
echo "3. Your site will be live at:"
echo "   https://nofeesapts-2b5c9.web.app/"
echo ""
echo "========================================="
echo "Backend Configuration"
echo "========================================="
echo ""
echo "Make sure your backend allows Firebase domain:"
echo ""
echo "Backend .env should have:"
echo "CORS_ORIGINS=\"https://nofeesapts-2b5c9.web.app,https://nofeesapts-2b5c9.firebaseapp.com\""
echo ""
echo "Current backend URL in frontend:"
grep REACT_APP_BACKEND_URL /app/frontend/.env
echo ""
echo "✅ Deployment package ready!"
