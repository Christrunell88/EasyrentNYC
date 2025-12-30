# Gmail API Setup Instructions

## ✅ Status
- ✅ Gmail API Python libraries installed
- ✅ Email service module created (`email_service.py`)
- ✅ Contact endpoint updated to send emails
- ⏳ **WAITING: OAuth credentials file**

## 📋 Steps to Complete Setup

### 1. Get OAuth Credentials from Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. **Enable Gmail API:**
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure OAuth consent screen:
     - User Type: External
     - App name: NoFeesApts.com
     - User support email: placesfirm@gmail.com
     - Developer contact: placesfirm@gmail.com
     - Scopes: Add `https://www.googleapis.com/auth/gmail.send`
     - Test users: Add placesfirm@gmail.com
   - Application type: **Desktop app**
   - Name: "NoFeesApts Email Service"
   - Click "Create"

5. **Download Credentials:**
   - Click the download button (⬇) next to your OAuth client
   - Save the JSON file

### 2. Add Credentials to Backend

Once you have the downloaded JSON file:

1. **Rename it to:** `gmail_credentials.json`
2. **Upload/paste it to:** `/app/backend/gmail_credentials.json`
3. The system is configured to look for this exact file path

### 3. First-Time Authorization

The first time the email service runs, it will:
1. Open a browser window asking you to authorize the app
2. Sign in with placesfirm@gmail.com
3. Grant permission to send emails
4. Save the authorization token for future use

After this one-time setup, emails will send automatically without requiring authorization again.

### 4. Test the Email Service

After adding credentials, test with:

```bash
cd /app/backend
python email_service.py
```

This will send a test email to placesfirm@gmail.com to verify everything is working.

## 🔒 Security Notes

- ✅ `gmail_credentials.json` is in `.gitignore` (never committed to version control)
- ✅ `token.pickle` (cached auth) is also ignored
- ✅ All sensitive config in environment variables
- ✅ OAuth credentials are encrypted and stored securely

## 📧 What Happens When Users Submit Contact Form

1. User fills out contact form on the website
2. Form data is saved to MongoDB database
3. Email notification is sent **in background** to placesfirm@gmail.com
4. User sees immediate success message
5. You receive a professionally formatted HTML email with:
   - User's name, email, phone
   - Apartment unit they're inquiring about
   - Their message
   - Direct reply-to link

## 🧪 Testing the Integration

Once credentials are added, you can test the contact form:

```bash
# Test the backend API directly
curl -X POST "https://nofeesapts.preview.emergentagent.com/api/contact" \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -d '{
    "unit_id": "SOME_UNIT_ID",
    "name": "Test User",
    "email": "test@example.com",
    "phone": "+12125551234",
    "message": "This is a test inquiry about the apartment."
  }'
```

## 🔧 Troubleshooting

### Error: "Gmail credentials file not found"
- Make sure `gmail_credentials.json` is in `/app/backend/`
- Check the filename is exactly `gmail_credentials.json`

### Error: "Failed to refresh credentials"
- Delete `token.pickle` and re-authorize
- Make sure the OAuth consent screen is configured correctly

### Emails not sending
- Check backend logs: `tail -f /var/log/supervisor/backend.*.log`
- Verify Gmail API is enabled in Google Cloud Console
- Ensure test users include placesfirm@gmail.com

## 📌 Current Configuration

- **Sender Email:** placesfirm@gmail.com (from `.env`)
- **Recipient Email:** placesfirm@gmail.com (from `.env`)
- **OAuth Scope:** `https://www.googleapis.com/auth/gmail.send`
- **Credentials Path:** `/app/backend/gmail_credentials.json`
- **Token Cache:** `/app/backend/token.pickle`

## ✨ Ready to Proceed

Once you paste the OAuth credentials JSON file at `/app/backend/gmail_credentials.json`, the email service will be ready to use!
