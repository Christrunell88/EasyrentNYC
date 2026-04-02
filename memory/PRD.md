# NoFeesApts.com - Product Requirements Document

## Original Problem Statement
Build a web application called "NoFeesApts.com" that functions similarly to nofeeplaces.com. The primary feature is to crawl publicly available real estate websites for no-fee apartment listings in NYC, Northern New Jersey, and PA, and display them.

## Core Features
- **Web Crawler:** Automatically crawl websites every 48 hours with manual trigger option
- **Database:** MongoDB for storing crawled apartment data
- **Authentication:** JWT-based custom sign-up/login + Google social login
- **Frontend:** White landing page (pre-login), light theme for logged-in users, search, filters, interactive map, favorites
- **Admin Panel:** View listings, analytics, trigger crawls, staging/approval pipeline
- **SEO:** Dynamic sitemap, structured data (Schema.org), neighborhood landing pages
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
│   ├── crawler.py             # Web scraping orchestration
│   ├── lifecycle_service.py   # Unit staleness management
│   ├── sitemap_generator.py   # Dynamic sitemap with neighborhood pages
│   ├── create_indexes.py      # MongoDB index optimization
│   ├── start.sh               # Server startup script
│   ├── scrapers/              # Modular site-specific scrapers
│   │   ├── __init__.py        # Scraper registry & unified interface
│   │   ├── base.py            # Shared utilities (browser, parsing)
│   │   ├── rosenyc_base.py    # Rose NYC iframe base scraper
│   │   ├── fortysixfifty.py   # 4650 Center Blvd
│   │   ├── mercedes_house.py  # Mercedes House
│   │   ├── harrison_yards.py  # Harrison Yards (RealPage)
│   │   ├── seven_w21.py       # 7 West 21st Street
│   │   ├── rivercourt.py      # Rivercourt LIC
│   │   ├── melar.py           # The Melar
│   │   └── generic.py         # Fallback scraper
│   └── tests/
│       ├── test_db_access_control.py
│       └── test_lifecycle_management.py
└── frontend/
    └── src/
        ├── config/
        │   └── api.js         # Centralized API configuration
        └── pages/
            ├── NeighborhoodsIndex.jsx  # SEO index of all neighborhoods
            ├── NeighborhoodPage.jsx    # Individual neighborhood SEO page
            ├── Landing.jsx             # Landing page with hero & listings
            └── AdminPanel.jsx          # Admin dashboard with staging
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

### Recent Work (2026-04-02)
- **Property Import Feature - COMPLETED** (Admin Panel):
  - Added "Import" tab to Admin Panel (first position, green highlight)
  - AI-powered property search using SerpApi that finds building management websites
  - Automatically filters out aggregators (StreetEasy, Zillow, Apartments.com, etc.)
  - "Crawl & Import" button extracts building data (name, address, neighborhood, images)
  - Attempts to extract unit information (unit numbers, rent, bedrooms, bathrooms)
  - Editable preview modal to review/modify data before import
  - Imports directly to staging for admin approval
  - Backend endpoints: `/api/admin/property-search`, `/api/admin/property-crawl`, `/api/admin/property-import`

### Recent Work (2026-03-09)
- **Hero Carousel Redesign - COMPLETED**:
  - Replaced busy multi-image hero with clean, full-width immersive carousel
  - Curated 5 best interior living room images from: 507 West Chelsea, 20 Broad, 60 Water DUMBO, Aro (NEW), 7W21 (NEW)
  - Slow 5.5-second transitions with pause-on-hover
  - Removed navigation arrows for cleaner aesthetic
  - Added alluring centered CTA: "EXPLORE 222+ No-Fee Apartments" with gold accent
  - "BROWSE FREE" button with elegant hover effect
  - "No credit card required" trust signal
  - Transparent navbar over carousel for immersive feel
  - Slide indicators moved to bottom-left
  - All SEO preserved (hidden h1, schema markup, meta tags)
  - Mobile responsive

- **New Buildings Added**:
  - **Aro** (242 West 53rd Street, Midtown West) - Added building + Unit 37B with 5 luxury interior images
  - **7W21** (7 W 21st St, Flatiron District) - Added building + Unit 1905 with 5 interior images

- **Brooklyn SEO Landing Page - COMPLETED** (`/brooklyn`):
  - Created dedicated high-value SEO page targeting "Best No Fee Apartments in Brooklyn"
  - Hero with dynamic stats (15+ listings, $5,181 avg rent, $0 broker fees)
  - "Why Choose No-Fee Apartments?" benefits card
  - Brooklyn Neighborhoods grid (DUMBO, Williamsburg, Brooklyn Heights, Fort Greene, Prospect Heights, Carroll Gardens, Park Slope, Cobble Hill)
  - Featured Brooklyn Apartments section with 6 listing cards
  - FAQ section with 5 SEO-optimized Q&As and Schema.org FAQPage markup
  - Rich SEO content section about Brooklyn apartments
  - Author/trust signal with update timestamp
  - Full Schema.org structured data (CollectionPage, BreadcrumbList, ItemList)
  - Added to sitemap with 0.95 priority

- **Manhattan SEO Landing Page - COMPLETED** (`/manhattan`):
  - Created dedicated high-value SEO page targeting "Best No Fee Apartments in Manhattan"
  - Hero with dynamic stats (68+ listings, $5,828 avg rent, $0 broker fees)
  - Manhattan Neighborhoods grid (Chelsea, Tribeca, Financial District, Midtown West, Upper West Side, Upper East Side, West Village, SoHo)
  - Featured Manhattan Apartments section with 6 listing cards
  - FAQ section with 5 SEO-optimized Q&As and Schema.org FAQPage markup
  - Full Schema.org structured data
  - Added to sitemap with 0.95 priority

- **New Jersey SEO Landing Page - COMPLETED** (`/new-jersey`):
  - Created dedicated high-value SEO page targeting "Best No Fee Apartments in New Jersey"
  - Hero with dynamic stats (37+ listings, $2,893 avg rent, $0 broker fees)
  - Transit highlight: "10-20 min PATH train to Manhattan"
  - "Why Choose NJ Over NYC?" benefits card
  - NJ Towns grid (Jersey City, Hoboken, Weehawken, Harrison, Newark, Edgewater, Fort Lee, Union City)
  - Commute time section (Exchange Place→WTC: 10min, Hoboken→33rd: 15min, Harrison→WTC: 20min)
  - FAQ section with 5 SEO-optimized Q&As and Schema.org FAQPage markup
  - Full Schema.org structured data
  - Added to sitemap with 0.95 priority

- **Queens SEO Landing Page - COMPLETED** (`/queens`):
  - Created dedicated high-value SEO page targeting "Best No Fee Apartments in Queens"
  - Hero with dynamic stats (21+ listings, $4,460 avg rent, $0 broker fees)
  - Queens Neighborhoods grid (Long Island City, Astoria, Flushing, Jamaica, Forest Hills, Sunnyside, Jackson Heights, Rego Park)
  - Featured Queens Apartments section with 6 listing cards
  - FAQ section with 5 SEO-optimized Q&As and Schema.org FAQPage markup
  - Full Schema.org structured data
  - Added to sitemap with 0.95 priority

### Recent Work (2026-03-03)
- **SerpApi Google Search Integration - COMPLETED**:
  - Enhanced AI Search Agent with real-time Google search grounding
  - Agent now fetches live market data for price/trend questions
  - Keywords trigger search: "average", "market", "trend", "price", "compare", "affordable", etc.
  - Tracks `google_search_used` in ai_searches collection for analytics
  - Free tier: 250 searches/month (no credit card required)
  - API Key stored securely in backend/.env

- **Neighborhood SEO Pages - COMPLETED**:
  - Created `/apartments` index page showing all 28 neighborhoods grouped by region (NYC, NJ, PA)
  - Created `/apartments/:slug` dynamic pages for each neighborhood (e.g., `/apartments/chelsea`)
  - Each neighborhood page includes:
    - Hero with neighborhood name, description, and highlights
    - Stats: unit count, avg rent, starting price, $0 broker fee
    - Listing grid with prices, bed/bath, blurred addresses
    - SEO content section with rich text about the neighborhood
    - Schema.org structured data for search engines
    - Full footer with links to other neighborhoods
  - Added neighborhood descriptions for 13+ key areas (Chelsea, Tribeca, DUMBO, etc.)
  - New API endpoints: `GET /api/neighborhoods`, `GET /api/neighborhoods/:slug`
  - Updated sitemap to include all neighborhood pages with high priority
  - Updated landing page "Popular Locations" to link to new pages
  - Added "View All 28 Neighborhoods →" link
  - Files created: `NeighborhoodsIndex.jsx`, `NeighborhoodPage.jsx`

- **Landing Page Enhancements - COMPLETED**:
  - Hero images now show prices with blurred addresses
  - Studio image updated to use 507 West Chelsea interior
  - 1 Bedroom image updated to use Chelsea Centro (TFC) interior
  - Contact info removed from box, now subtle text below CTA

- **Chelsea Centro Unit Added**:
  - Added unit 16J to TFC Chelsea (200 W 26th St)
  - $5,815/mo, 1 Bed, 1 Bath
  - 11 high-quality images from TFC website

### Recent Work (2026-03-02)
- **ListingCard UI Cleanup - COMPLETED**:
  - Moved thumbnail images from hover overlay to below the main image
  - Simplified card layout with minimal text (price, bed/bath, address only)
  - Removed rental type labels, building name sections, and photo count badges
  - Reduced text sizes throughout for cleaner look
  - Contact buttons (Email/Call) moved to bottom of card
  - Removed "Welcome back" message from Dashboard
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
  - **Admin Panel UI - COMPLETED**:
    - New "Unavailable" tab with orange badge showing pending count
    - Stats display: Pending, Confirmed, False Positives, High Priority (3+ misses)
    - Table showing: Unit, Building, Rent, Beds, Misses (badge), First Detected
    - Quick action buttons: Green checkmark (dismiss), Red X (confirm unavailable)
    - Checkboxes for bulk selection with bulk action buttons
    - Confirmation dialog with unit details, notes field, and action buttons
    - Refresh button to reload data
  - **Re-listing System - COMPLETED** (2026-03-02):
    - New "Rented/Off" tab showing all unavailable/rented units
    - New "Rejected" tab showing rejected staging units
    - Re-list button opens dialog with rent update option and notes
    - Bulk re-list functionality for multiple units
    - "Reconsider" button moves rejected units back to pending
    - "Approve" button directly approves rejected units to production
    - API Endpoints:
      - `GET /api/admin/units/unavailable` - List unavailable units
      - `PUT /api/admin/units/{id}/relist` - Re-list a single unit
      - `POST /api/admin/units/bulk-relist` - Bulk re-list units
      - `GET /api/admin/staging/rejected` - List rejected staging units
      - `PUT /api/admin/staging/rejected/{id}/reconsider` - Move to pending
      - `PUT /api/admin/staging/rejected/{id}/approve-direct` - Approve directly
  - Status: ✅ TESTED AND WORKING

- **Code Cleanup - COMPLETED** (2026-03-02):
  - **Centralized API Configuration**:
    - Created `/app/frontend/src/config/api.js` with single source of truth for API URL
    - Migrated `App.js` and `authStore.js` to use centralized config
    - Removed duplicate `BACKEND_URL` / `API` definitions
    - Consistent URL handling for custom domains and CORS
  - **Modular Scrapers - FULLY MIGRATED**:
    - Created `/app/backend/scrapers/` directory with complete scraper suite
    - **Base utilities** (`base.py`): Browser management, parsing helpers
    - **Rose NYC base** (`rosenyc_base.py`): Shared logic for Rose NYC iframe sites
    - **Site-specific scrapers**:
      - `fortysixfifty.py` - 4650 Center Blvd (iframe table)
      - `mercedes_house.py` - Mercedes House (regex patterns)
      - `harrison_yards.py` - Harrison Yards (RealPage widget)
      - `seven_w21.py` - 7 West 21st Street (Rose NYC iframe)
      - `rivercourt.py` - Rivercourt LIC (Rose NYC iframe)
      - `melar.py` - The Melar (Rose NYC iframe)
      - `generic.py` - Fallback scraper for unknown sites
    - **Registry** (`__init__.py`): Maps URL patterns to scrapers
    - Updated `crawler.py` to use modular scrapers exclusively
  - Status: ✅ COMPLETED

- **Landing Page Update - COMPLETED** (2026-03-02):
  - Saved original layout to `Landing_OriginalLayout.jsx.bak`
  - Added contact information box with:
    - "Free Sign Up for Full Access" header
    - "Get full access and new listings alerts" messaging
    - Office phone: 646-408-8048 (clickable)
    - Email: Placesfirm@gmail.com (clickable)
  - Changed button text: "EXPLORE COLLECTION" → "FREE SIGN UP"
  - Changed nav button: "GET STARTED" → "FREE SIGN UP"
  - Changed "View All Properties" → "Sign Up to View All Properties"
  - **White Theme Update**:
    - Changed entire landing page from dark to clean white background
    - White navigation bar with shadow
    - Hero section replaced with three interior images gallery (Studio, 1BR, 2BR)
    - Stats displayed below images (horizontally)
    - Light gray (#f8f8f8) sections for visual separation
    - Dark text for contrast on white backgrounds
    - Removed "FEATURED" badge from all listing cards
    - Updated footer and all sections to match white theme
  - **Listing Card Updates**:
    - Added smart image selector to prioritize interior images over exterior shots
    - Changed bedroom display from "X Rooms" to "Studio", "1 Bed", "2 Bed"
    - Capitalized "Bath" text
  - **New Arrivals Variety**:
    - Updated `/api/units/recent` to show max one unit per building
    - Ensures 6 different buildings displayed, not duplicates from same building
    - Each listing now has unique imagery
  - Status: ✅ COMPLETED

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
