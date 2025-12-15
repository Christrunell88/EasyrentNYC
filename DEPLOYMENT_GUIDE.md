# NoFeesApts.com - Firebase Deployment Guide

## Your Firebase URL
Your site is hosted at: **https://nofeesapts-2b5c9.web.app/**

## Overview
This guide will help you deploy the NoFeesApts.com full-stack application to your Firebase hosting while keeping the backend on Emergent servers.

---

## Architecture

### Frontend (Firebase Hosting)
- **Domain**: https://nofeesapts-2b5c9.web.app/
- **Tech**: React + Tailwind CSS
- **Hosted on**: Firebase Hosting

### Backend (Emergent/Your Server)
- **Current URL**: https://freefeeapts.preview.emergentagent.com/api
- **Tech**: FastAPI + MongoDB + Web Crawler
- **Hosted on**: Emergent platform (or your own server)

---

## Step 1: Build the Frontend for Production

### From this Emergent environment:

```bash
# Navigate to frontend
cd /app/frontend

# Install dependencies (if needed)
yarn install

# Build production bundle
yarn build

# The build folder will be created at /app/frontend/build
```

---

## Step 2: Update Backend URL for Production

Before building, update the backend URL to point to your production backend:

```bash
# Edit /app/frontend/.env
REACT_APP_BACKEND_URL=https://your-backend-domain.com

# Or if keeping on Emergent preview:
REACT_APP_BACKEND_URL=https://freefeeapts.preview.emergentagent.com
```

**Important**: After changing .env, rebuild:
```bash
yarn build
```

---

## Step 3: Deploy to Firebase

### Option A: Deploy from Local Machine

1. **Download the build folder** from this environment:
   ```bash
   # Compress the build folder
   cd /app/frontend
   tar -czf build.tar.gz build/
   
   # Download this file to your local machine
   ```

2. **On your local machine**, with Firebase CLI installed:
   ```bash
   # Login to Firebase
   firebase login
   
   # Initialize (if not done)
   firebase init hosting
   
   # Select your project: nofeesapts-2b5c9
   # Set public directory: build
   # Configure as single-page app: Yes
   # Don't overwrite index.html: No
   
   # Extract build folder
   tar -xzf build.tar.gz
   
   # Deploy
   firebase deploy --only hosting
   ```

### Option B: Direct Upload via Firebase Console

1. Go to Firebase Console: https://console.firebase.google.com/
2. Select project: nofeesapts-2b5c9
3. Go to Hosting
4. Upload the contents of `/app/frontend/build` folder

---

## Step 4: Configure CORS on Backend

Your backend needs to allow requests from your Firebase domain:

```python
# In /app/backend/.env
CORS_ORIGINS="https://nofeesapts-2b5c9.web.app,https://nofeesapts-2b5c9.firebaseapp.com"
```

Then restart backend:
```bash
sudo supervisorctl restart backend
```

---

## Step 5: Custom Domain (Optional)

### Connect nofeesapts.com to Firebase:

1. **In Firebase Console**:
   - Go to Hosting → Add custom domain
   - Enter: nofeesapts.com
   - Follow DNS configuration instructions

2. **Add DNS Records** (at your domain registrar):
   ```
   Type: A
   Name: @
   Value: [Firebase IP from console]
   
   Type: A  
   Name: www
   Value: [Firebase IP from console]
   ```

3. **Update Backend CORS**:
   ```
   CORS_ORIGINS="https://nofeesapts.com,https://www.nofeesapts.com,https://nofeesapts-2b5c9.web.app"
   ```

---

## Step 6: Environment Variables Summary

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://your-backend-domain.com
```

### Backend (.env)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="https://nofeesapts-2b5c9.web.app,https://nofeesapts.com"
JWT_SECRET="your-secret-key-change-in-production-12345"
PLAYWRIGHT_BROWSERS_PATH="/usr/local/share/playwright"
```

---

## Step 7: Backend Deployment Options

### Option A: Keep on Emergent (Current Setup)
- Backend URL: https://freefeeapts.preview.emergentagent.com
- No changes needed
- Limited to Emergent environment

### Option B: Deploy Backend Separately

**Recommended Hosts**:
- **Railway.app** (Easy Python + MongoDB)
- **Render.com** (Free tier available)
- **DigitalOcean App Platform**
- **AWS EC2 + MongoDB Atlas**

**Requirements**:
- Python 3.11+
- MongoDB database
- Playwright browsers installed
- All Python dependencies from requirements.txt

---

## Files to Deploy

### Frontend (to Firebase):
```
/app/frontend/build/
├── index.html
├── static/
│   ├── css/
│   ├── js/
│   └── media/
└── asset-manifest.json
```

### Backend (if deploying separately):
```
/app/backend/
├── server.py
├── crawler.py
├── requirements.txt
└── .env
```

---

## Testing After Deployment

1. **Test Frontend**:
   ```
   Visit: https://nofeesapts-2b5c9.web.app/
   - Should see landing page
   - Should be able to sign up/login
   ```

2. **Test Backend Connection**:
   ```bash
   # From browser console on your site:
   fetch('https://your-backend-url.com/api/units?limit=5')
     .then(r => r.json())
     .then(d => console.log(d))
   ```

3. **Test Auth Flow**:
   - Sign up with email
   - Check if dashboard loads with apartments
   - Test filters

---

## Maintenance

### Update Apartment Listings:
1. Crawler runs automatically every 48 hours
2. Manual trigger from Admin Panel → Buildings → Crawl button
3. Or via API: `POST /api/admin/crawl/{building_id}`

### Add New Buildings:
1. Login as admin (admin@nofeesapts.com)
2. Go to Admin Panel
3. Add building with source URL
4. Trigger crawl

---

## Quick Deployment Commands

```bash
# From this Emergent environment:

# 1. Update backend URL in frontend
echo 'REACT_APP_BACKEND_URL=https://your-backend-url.com' > /app/frontend/.env

# 2. Build frontend
cd /app/frontend && yarn build

# 3. Package for download
tar -czf /tmp/nofeesapts-frontend.tar.gz -C /app/frontend/build .

# 4. Download /tmp/nofeesapts-frontend.tar.gz to your local machine

# 5. On local machine with Firebase CLI:
# Extract and deploy
tar -xzf nofeesapts-frontend.tar.gz -C ./public
firebase deploy --only hosting

# 6. Update backend CORS
# Add your Firebase URL to backend/.env CORS_ORIGINS
# Then: sudo supervisorctl restart backend
```

---

## Support

- **Backend Issues**: Check `/var/log/supervisor/backend.err.log`
- **Frontend Issues**: Check browser console (F12)
- **Database Issues**: `mongosh test_database`
- **Crawler Issues**: Check backend logs for "crawler" entries

---

## Current Status

✅ Frontend: Updated to NoFeesApts.com branding
✅ Backend: 206 apartments from 5 buildings
✅ Crawler: Running every 48 hours
✅ Database: No duplicates, properly indexed
✅ Admin Panel: Fully functional

Ready to deploy to: https://nofeesapts-2b5c9.web.app/
