#!/bin/bash

# This script tests the Gmail API integration once credentials are added
# Run this AFTER you've placed gmail_credentials.json in /app/backend/

echo "🧪 Testing Gmail API Email Service"
echo "====================================="
echo ""

# Check if credentials file exists
if [ ! -f "/app/backend/gmail_credentials.json" ]; then
    echo "❌ Error: gmail_credentials.json not found!"
    echo ""
    echo "Please add your OAuth credentials file at:"
    echo "  /app/backend/gmail_credentials.json"
    echo ""
    echo "See GMAIL_SETUP.md for instructions."
    exit 1
fi

echo "✅ Credentials file found"
echo ""

# Test the email service directly
echo "📧 Sending test email..."
echo ""
cd /app/backend
python3 email_service.py

echo ""
echo "====================================="
echo "If successful, check placesfirm@gmail.com for the test email!"
