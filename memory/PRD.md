# NoFeesApts.com - Product Requirements Document

## Original Problem Statement
Build a web application called "NoFeesApts.com" that functions similarly to nofeeplaces.com. The primary feature is to crawl publicly available real estate websites for no-fee apartment listings in NYC, Northern New Jersey, and PA, and display them.

## Core Features
- **Web Crawler:** Automatically crawl websites every 48 hours with manual trigger option
- **Database:** MongoDB for storing crawled apartment data
- **Authentication:** JWT-based custom sign-up/login + Google social login
- **Frontend:** Dark landing page (pre-login), light theme for logged-in users, search, filters, interactive map, favorites
- **Admin Panel:** View listings, analytics, trigger crawls, staging/approval pipeline
- **SEO:** Dynamic sitemap, structured data (Schema.org)
- **Notifications:** Email for contact forms and welcome emails
- **AI Search Agent:** Gemini 3 Flash powered apartment search

## Tech Stack
- **Frontend:** React (port 3000)
- **Backend:** FastAPI (port 8001)
- **Database:** MongoDB
- **AI:** Gemini 3 Flash
- **Crawler:** Playwright

## Architecture
```
/app/
├── backend/
│   ├── server.py              # Main FastAPI app with all routes
│   ├── crawler.py             # Web scraping with Playwright
│   ├── lifecycle_service.py   # Unit staleness management
│   ├── create_indexes.py      # MongoDB index optimization
│   ├── start.sh               # Server startup script
│   └── tests/
│       ├── test_db_access_control.py
│       └── test_lifecycle_management.py
└── frontend/
    └── src/
        └── pages/
            └── AdminPanel.jsx  # Admin dashboard with staging
```

## Database Schema
### Collections
- `units` - Production apartment listings
- `units_staging` - Pending listings for review
- `buildings` - Production building data
- `buildings_staging` - Pending building data
- `users` - User accounts
- `favorites` - User saved listings
- `price_history` - Price tracking
- `status_history` - Availability tracking

### Key Fields (units)
- `building_id`, `unit_number`, `rent`, `bedrooms`, `bathrooms`
- `images[]`, `amenities[]`, `description`
- `is_available`, `review_status`, `lifecycle_status`
- `crawler_source`, `crawler_batch_id`

## Credentials
- **Admin:** placesfirm@gmail.com / Checkers080/?
- **Test User:** chris.trunell@gmail.com / TestPass123!

---

## Implementation Status

### ✅ Completed (as of 2026-02-19)
- [x] Full-stack app with React frontend + FastAPI backend
- [x] MongoDB database with optimized indexes
- [x] JWT authentication + Google social login
- [x] Web crawler with Playwright (fixed browser installation)
- [x] Staging/approval pipeline for listings
- [x] Admin panel with staging management
- [x] "Edit Staging Unit" feature
- [x] Unit lifecycle management (stale detection)
- [x] 37 buildings, 183+ units in production
- [x] **7W21 stock images assigned** (3 units with living room + bedroom images)
- [x] AI Search Agent (Gemini 3 Flash)
- [x] Google Analytics integration
- [x] Facebook Graph API connection
- [x] **Image Carousel on ListingCard** - Desktop (hover with arrows, thumbnails, auto-advance) + Mobile (swipe)
- [x] **End-to-End Renter Path** - Verified: Landing → Auth → Dashboard → Unit Detail

### Recent Work (2026-02-19)
- **Image Carousel on Listing Cards**: 
  - Desktop: Navigation arrows + thumbnail strip on hover, auto-advance every 2 seconds
  - Mobile: Swipe gesture support with visual "< Swipe >" hint
  - Photo count badge and dot indicators
- **E2E Testing Completed**: Full renter path verified (94% backend, 100% frontend pass rate)
- **Pytest tests created**: `/app/backend/tests/test_nofeesapts.py`
- **Backlink-building Technical Implementation**:
  - Added LocalBusiness schema markup (RealEstateAgent type) to SEO.jsx
  - Created `/app/frontend/src/components/Footer.jsx` with internal linking (Locations, Neighborhoods, Resources, Company)
  - Created `/app/frontend/src/components/RelatedListings.jsx` for similar apartments on unit detail pages
  - ShareDialog already had embed code for backlinks
- **Google Business Profile Technical Integration**:
  - Added comprehensive LocalBusiness schema to SEO.jsx with geo coordinates, hours, aggregate rating
  - Created `/app/frontend/src/components/GoogleMapEmbed.jsx` with static map + interactive buttons
  - Created `/app/frontend/src/pages/Neighborhoods.jsx` as location index page with FAQ schema
  - Added Google Maps embed to unit detail pages with "View on Google Maps" and "Get Directions" buttons

### 🟠 Pending User Verification (Requires Redeployment)
- [x] ~~Stats display on live site~~ - Fixed in preview
- [x] ~~Login/Signup on custom domain~~ - **FIXED** in preview

### Previous Fixes (2026-02-10)
- **Fixed login on custom domain**: Changed API URL logic to use `window.location.origin` in production
- **Added /login and /signup routes**: Now redirect to /auth page
- **Fixed CORS configuration**: Changed from `*` to explicit origins list (required for withCredentials)

### 🟡 Upcoming Tasks (P1-P2)
- [ ] Complete #FeeFreeFinds branding (badges, social sharing)
- [ ] SEO Optimization (location pages, blog content)
- [ ] Add "Admin" link back to UI
- [ ] Lifecycle Dashboard UI

### 🔵 Future/Backlog (P3)
- [ ] Advanced Filters (move-in date, pet-friendly)
- [ ] Backlink-building strategy
- [ ] Google Business Profile
- [ ] Apartment comparison feature
- [ ] Google/Facebook Ad campaigns

## Known Issues
1. **BACKEND_URL duplication** - Constant duplicated in App.js and authStore.js
2. **crawler.py size** - Consider modularizing into /scrapers/ directory

## 3rd Party Integrations
| Service | Status | Purpose |
|---------|--------|---------|
| Gemini 3 Flash | Active | AI Search Agent |
| Facebook Graph API | Active | Social integration |
| Google Analytics | Active | Event tracking |
| Playwright | Active | Web crawler |

## API Endpoints (Key)
- `POST /api/auth/login` - User login
- `GET /api/units` - List apartments
- `GET /api/admin/staging/units` - Get staging units
- `PUT /api/admin/staging/units/{id}` - Edit staging unit
- `POST /api/admin/crawl-all` - Trigger crawler
- `POST /api/lifecycle/stale-check` - Check stale units
- `GET /api/lifecycle/report` - Lifecycle status report
