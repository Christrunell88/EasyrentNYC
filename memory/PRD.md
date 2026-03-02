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

### ✅ Completed (as of 2026-02-25)
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
- [x] **The Larstrand Building** - Added to staging (3 units with images)
- [x] **The Greenpoint Building** - Added to staging (10 units with images)
- [x] **Theme Switch (Dark→Light)** - Landing page has dark theme, all logged-in pages (Dashboard, Favorites, Unit Details, FeeFreeFinds) now use clean white/light theme with amber accents

### Recent Work (2026-03-02)
- **Contact Modal Implementation - COMPLETED**:
  - Created on-page contact form modal in `ListingCard.jsx`
  - Users can now email the agent without leaving the page (no more `mailto:` redirect)
  - Modal pre-fills user name, email, and unit-specific message
  - Sends email to `placesfirm@gmail.com` via `/api/contact` endpoint
  - Contact requests stored in database for admin tracking
  - Emails sent via Gmail SMTP (configured with app password)
  - Fixed API endpoint path from `/contact` to `/api/contact`
  - Status: ✅ TESTED AND WORKING

- **Unavailability Detection System - COMPLETED**:
  - Added automatic detection of potentially unavailable units when crawling
  - Compares crawled results against production units for each building
  - Units in production but NOT in crawl → flagged for admin review
  - New `unavailability_reviews` collection stores flags
  - Tracks `consecutive_misses` to prioritize high-confidence cases
  - New API Endpoints:
    - `GET /api/admin/unavailability-reviews` - List flagged units
    - `GET /api/admin/unavailability-reviews/stats` - Summary stats
    - `PUT /api/admin/unavailability-reviews/{id}` - Review single flag
    - `POST /api/admin/unavailability-reviews/bulk-review` - Bulk review
  - Review Actions:
    - `confirmed_unavailable` → Marks unit as rented, removes from listings
    - `false_positive` → Dismisses flag, keeps unit available
  - Status: ✅ TESTED AND WORKING (21 units detected on first test crawl)

### Recent Work (2026-02-27)
- **Malt Drive Building - PROMOTED TO PRODUCTION**:
  - **Malt Drive** (2-21 Malt Drive, Jersey City, NJ 07305)
    - 3 units: Studio 312 ($2,150), 1BR 101 ($2,450), 2BR 205 ($2,850)
    - All 3 units have 8 professional images attached (user-provided AVIF images)
    - Amenities: No Fee, Doorman, Fitness Center, Rooftop, In-Unit Laundry, Pet Friendly
    - Status: ✅ LIVE IN PRODUCTION

- **The Smile Building - PROMOTED TO PRODUCTION**:
  - **The Smile** (158 East 126th Street, Harlem, NY 10035)
    - Designer: BIG (Bjarke Ingels Group)
    - 4 units: 3 Studios + 1 Two-Bedroom
      - Unit 929 (Studio) - $2,940/mo - 494 sq ft - 10 images
      - Unit 1108 (Studio) - $2,964/mo - 477 sq ft - 10 images
      - Unit 1123 (Studio) - $3,061/mo - 493 sq ft - 10 images
      - Unit 1129 (2BR/2BA) - $5,652/mo - 1,008 sq ft - 11 images
    - Amenities: No Fee, Rooftop Pool, Fitness Center, Doorman, Spa, Sauna, Steam Room, Co-Working Space, Game Room, Screening Room, Pet Friendly, Loft-Style
    - Status: ✅ LIVE IN PRODUCTION

### Previous Work (2026-02-25)
- **Theme Switch Implementation**:
  - Landing page: Dark luxury theme (unchanged)
  - Dashboard: White background, gray header, amber accents
  - ListingCard: Theme-aware with `theme="light"` prop
  - Favorites: Light theme with amber gradient title
  - Unit Details: Light theme with clean professional look
  - FeeFreeFinds: Light theme consistent with dashboard
  - All logged-in pages now use clean, professional white background

- **New Buildings Added to Staging**:
  - **The Larstrand** (227 W 77th St, Upper West Side)
    - 3 units: Studio 05C ($4,850), Studio 16J ($4,897), 1BR 17H ($7,100)
    - All with images from building gallery
  - **The Greenpoint** (21 India Street, Brooklyn)
    - 10 units: 4 Studios, 5 One-Bedrooms, 1 Two-Bedroom
    - Rent range: $4,074 - $7,148
    - Square footage included (492-972 sq ft)

### Previous Work (2026-02-19)
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
