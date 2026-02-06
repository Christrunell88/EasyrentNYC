# NoFeesApts.com - Product Requirements Document

## Original Problem Statement
Build a web application called "NoFeesApts.com" that functions similarly to nofeeplaces.com. The primary feature is to crawl publicly available real estate websites for no-fee apartment listings in NYC, Northern New Jersey, and PA, and display them.

## Core Requirements
- **Web Crawler:** Automatically crawl websites every 48 hours with manual trigger in admin panel
- **Database:** MongoDB for all crawled data (Address, unit number, rent, bedrooms, baths, images, amenities)
- **Authentication:** JWT-based custom sign-up/login + Google social login (Emergent OAuth)
- **Frontend:** Search, filters, interactive map, favorites, "sign up for full details" with blurred addresses
- **Design:** Luxury Dark Theme, smart/intuitive/sleek/modern
- **SEO:** Dynamic sitemap, optimized meta tags
- **Admin Panel:** View listings, analytics, trigger crawls, manage users
- **Notifications:** Email for contact forms, welcome emails for new users
- **Appointment Scheduling:** Tour date/time requests with Google Calendar integration

## User Personas
1. **Apartment Seekers:** Looking for no-fee apartments in NYC/NJ area
2. **Admin/Owner:** Managing listings, viewing analytics, posting to social media

## Tech Stack
- **Frontend:** React + Tailwind CSS + Shadcn/UI
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Auth:** JWT + Emergent Google OAuth
- **Email:** SMTP
- **Social:** Facebook Graph API integration

---

## What's Been Implemented

### Core Features ✅
- Full apartment listing system with search and filters
- User authentication (JWT + Google OAuth)
- Favorites system for logged-in users
- Contact/inquiry system with email notifications
- Admin panel with full CRUD operations
- Automated crawler with 48-hour schedule
- Dynamic sitemap generation at `/api/sitemap.xml`
- SEO optimization with meta tags
- Email subscription ("Get Updates") feature
- Share listing via email feature
- Blog section with SEO-focused content
- FAQ page
- Location-based pages

### Design ✅
- Luxury Dark Theme implemented
- Hero section with custom user-provided image
- Responsive design throughout

### Integrations ✅
- Google Maps for interactive map view
- Google Cloud Storage for images
- Google Analytics 4
- SMTP for transactional emails
- Facebook Graph API (currently blocked - token expired)

---

## Changelog

### 2025-01-15
- **Created:** MongoDB Index Management System
  - 35+ indexes across all collections for query optimization
  - Compound indexes for common query patterns
  - Geospatial (2dsphere) index for map-based searches
  - Unique indexes for data integrity
  - Auto-created on server startup
- **Created:** `/app/backend/create_indexes.py` - Comprehensive index management script
- **Indexes by collection:**
  - `units`: 12 indexes (building_id+unit_number, lifecycle_status, rent, updated_at, featured)
  - `units_staging`: 8 indexes (review_status, duplicate_score DESC, normalized_unit)
  - `buildings`: 7 indexes (normalized_address, location 2dsphere, city+state)
  - `buildings_staging`: 5 indexes (review_status, duplicate_score, address_hash)
  - `price_changes`: 3 indexes (unit_id+changed_at compound)
  - `status_changes`: 4 indexes (unit_id+changed_at, new_status)
- **Implemented:** Unit Lifecycle Management System
  - Automatic stale detection (units not updated in 14 days → status = "stale")
  - Rented status tracking with history
  - Price change history tracking in `price_changes` collection
  - Status change history in `status_changes` collection
  - NO auto-deletion (units are never automatically deleted)
  - Daily scheduler job checks for stale units
- **Created:** `/app/backend/lifecycle_service.py`
- **Created:** Test suite at `/app/backend/tests/test_lifecycle_management.py` (7 tests passed)
- **New API Endpoints:**
  - `GET /api/admin/lifecycle/stats` - Lifecycle statistics
  - `GET /api/admin/lifecycle/stale-units` - List stale units
  - `GET /api/admin/lifecycle/rented-units` - List rented units
  - `PUT /api/admin/lifecycle/unit/{id}/status` - Update unit status
  - `PUT /api/admin/lifecycle/unit/{id}/price` - Update price with history
  - `GET /api/admin/lifecycle/unit/{id}/history` - Full history
  - `POST /api/admin/lifecycle/check-stale` - Manual stale check
  - `POST /api/admin/lifecycle/bulk-refresh` - Bulk refresh stale
  - `POST /api/admin/lifecycle/bulk-mark-rented` - Bulk mark rented
- **Tested:** Database Access Control Layer - All 9 tests passed
  - Crawler role BLOCKED from writing to production collections (units, buildings)
  - Admin role CAN write to production collections via authorized_production_write
  - Crawler CAN write to staging collections (units_staging, buildings_staging)
  - E2E Promotion Flow (staging → production) works correctly
- **Created:** Test suite at `/app/backend/tests/test_db_access_control.py`

### 2025-01-14
- **Added:** 20 Park Avenue building with 2 units (012G: 3BR/3BA $11,595/mo, 017B: 1BR/1BA $6,695/mo)
- **Added:** TFC Buildings from tfc.com crawl:
  - **95 Horatio** (West Village): 3 new units ($6,745 - $7,895/mo)
  - **4540 Center Blvd** (Long Island City): 8 units ($3,117 - $6,795/mo)
  - **595 Dean** (Prospect Heights, Brooklyn): 10 units ($3,094 - $8,105/mo)
- **Added:** 505 W 37th St (Hudson Yards): 1 unit (2BR/2BA $6,775/mo with balcony & river views)
- **Added:** AI Search Agent powered by Gemini 3 Flash
  - Floating chat bubble on all pages
  - Searches 180 units in database
  - Directs users to contact Chris for off-site searches
  - Saves all searches for admin analytics
- **Database:** Total now at 34 buildings, 180 units

### 2025-01-02
- **Fixed:** Sitemap 404 error - moved route from `/sitemap.xml` to `/api/sitemap.xml`
- **Updated:** robots.txt to point to new sitemap URL

### Previous Session
- **Fixed:** Auth issue on custom domain (made API URL dynamic)
- **Fixed:** Dynamic sitemap to use production domain
- **Redesigned:** Hero section with user-provided image
- **Added:** Multiple new buildings and listings (The Anagram, Harrison Yards updates, CD 280, The Habitat)

---

## Prioritized Backlog

### P0 - Critical (Completed)
- [x] **Database Access Control Layer** - Tested & Verified
  - All 9 tests passed confirming proper access restrictions
  - Crawler blocked from production writes
  - Admin can write to production via promotion service

### P0 - Critical (Pending User Verification)
- [ ] Login/Signup fix verification on `nofeesapts.com` (requires redeployment)
- [ ] Stats display fix (63 units/24 buildings -> correct 180 units/34 buildings)

### P0 - High Priority
- [ ] Wire up "Edit before approval" functionality in Admin Staging Review
- [ ] Complete `#FeeFreeFinds` branding strategy
  - Add badges to listings
  - Update social sharing text

### P1 - Important
- [ ] SEO Optimization
  - Enhance location-specific pages with rich content
  - Add more blog content
- [ ] Image re-ordering for listings in admin panel
- [ ] Add "Admin" link back to UI (e.g., footer)

### P2 - Nice to Have
- [ ] Advanced Filters (move-in date, pet-friendly, etc.)
- [ ] Backlink-building strategy

### P3 - Future
- [ ] Google Business Profile for NoFeesApts
- [ ] User-facing apartment comparison feature
- [ ] Google/Facebook Ad campaigns

---

## Blocked Items
- **Facebook Posting:** Blocked due to expired/invalid access token. User must provide new token.

---

## Key API Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/signup` - User registration
- `GET /api/units` - List apartments with filters
- `GET /api/units/{id}` - Unit details
- `POST /api/contact` - Submit inquiry
- `POST /api/subscribe` - Email subscription
- `GET /api/sitemap.xml` - Dynamic sitemap
- `GET /api/admin/stats` - Admin dashboard stats
- `GET /api/stats` - Public stats (with cache busting)

### Staging & Promotion API
- `GET /api/admin/staging/units` - Get staged units for review
- `POST /api/staging/approve/{staging_unit_id}` - Approve staged unit
- `POST /api/staging/reject/{staging_unit_id}` - Reject staged unit
- `POST /api/promote/unit/{staging_unit_id}` - Promote to production

## Test Credentials
- **Admin:** `placesfirm@gmail.com` / `Checkers080/?`
- **User:** `chris.trunell@gmail.com` / `TestPass123!`
