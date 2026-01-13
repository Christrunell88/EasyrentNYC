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

### 2026-01-13
- **New Building Added: 20 Broad Street (Financial District)**
  - Building ID: `9a7632e7-8e2b-4be2-90a0-6cd04eb639ad`
  - Historic building at Wall Street/NYSE with mid-century modern design by Cetra Ruddy
  - 1 unit added (Studio, 524 sq ft)
  - Rent: $4,202/month
  - Data script saved: `/app/backend/Buildings/20_broad_street.py`
  - Features: Sky Lounge, rooftop terrace, outdoor theater, Technogym fitness center

- **New Building Added: 8 Spruce Street - New York by Gehry (Financial District)**
  - Building ID: `b1ba3309-a200-411b-8df7-6b530551cb90`
  - Iconic 76-story Frank Gehry-designed tower (870 ft tall)
  - 7 units added (2 studios, 3 one-bedrooms, 1 two-bedroom, 1 three-bedroom)
  - Rents: $4,151 - $17,198/month
  - Source: Brookfield Properties
  - Data script saved: `/app/backend/Buildings/8_spruce_street.py`
  - Features: 50ft pool, 22,000 sq ft amenities, Brooklyn Bridge views, Steinway Grand Piano

- **New Building Added: 33 Bond Street (Downtown Brooklyn)**
  - Building ID: `cc25c23a-ec06-419c-b3fd-90dc8fe94257`
  - 7 units added (1 studio, 5 one-bedrooms, 1 two-bedroom)
  - Rents: $2,998 - $5,530/month
  - Source: TF Cornerstone
  - Data script saved: `/app/backend/Buildings/33_bond_street.py`
  - Features: Chelsea Piers Fitness, 18,500 sq ft roof deck, pet spa (Throw Me a Bone)

- **New Listing Added: 101 West 15th Street, Unit 519 (Chelsea)**
  - Building ID: `f787816c-4475-4d13-a082-a33f4b1a2b9b`
  - Unit ID: `28ce94fb-703a-43ff-9c66-24e17dcbe7d8`
  - 1BR/1BA, $6,850/month, 2 months free on 16-month lease
  - Source: Stonehenge NYC
  - Data script saved: `/app/backend/Buildings/101_west_15th_street.py`

### 2025-01-13 (Session 2)
- **P1: SEO Optimization - Location Pages Enhanced:**
  - Added rich neighborhood descriptions with local tips
  - Added commute info cards (subway lines, avg commute, walk score)
  - Added lifestyle cards (dining, nightlife, outdoors)
  - Added collapsible FAQ sections with JSON-LD schema for Google rich results
  - Added "Compare Other Locations" internal linking
  - Added comprehensive footer with location links
  - Implemented for all 10 locations: Manhattan, Brooklyn, Queens, Bronx, LIC, Williamsburg, Jersey City, Hoboken, Harrison, Weehawken

- **P1: Blog Content - New Article Published:**
  - "Why NYC Renters Pay Broker Fees When No One Else Does" (`/blog/why-nyc-renters-pay-broker-fees`)
  - Comparison table: NYC vs 6 other cities
  - Explains unique NYC broker fee market
  - Highlights NJ as no-fee alternative
  - 5 actionable tips for finding no-fee apartments

- **P2: Page Speed Optimization:**
  - Added `loading="lazy"` and `decoding="async"` to all images
  - Added `fetchPriority="high"` to hero/critical images
  - Added preconnect hints for external domains (fonts, images)
  - Added preload for hero image
  - Added `font-display: swap` for fonts
  - Added GZip compression middleware to backend (responses >500 bytes)
  - Added Web Vitals monitoring (LCP, INP, CLS, FCP, TTFB) integrated with GA4

### 2025-01-13 (Session 1)
- **Verified:** JSON-LD RealEstateListing schema implemented on unit detail pages (UnitDetails.jsx)
- **Created:** Comprehensive SEO Strategy document (`/app/memory/SEO_STRATEGY.md`)
  - Expanded negative keyword list (budget, government housing, sales, jobs, roommates, geographic exclusions)
  - Target keyword strategy
  - Brand positioning guidelines
- **Updated:** robots.txt with enhanced documentation and additional bot rules
- **Created:** Google Ads Negative Keywords reference (`/app/memory/GOOGLE_ADS_NEGATIVE_KEYWORDS.md`)
  - Copy-paste ready lists for campaign setup
  - Match type recommendations
  - Maintenance schedule

### 2025-01-02
- **Fixed:** Sitemap 404 error - moved route from `/sitemap.xml` to `/api/sitemap.xml`
- **Updated:** robots.txt to point to new sitemap URL

### Previous Sessions
- **Fixed:** Auth issue on custom domain (made API URL dynamic)
- **Fixed:** Dynamic sitemap to use production domain
- **Redesigned:** Hero section with user-provided image
- **Added:** Multiple new buildings and listings (The Anagram, Harrison Yards updates, CD 280, The Habitat)
- **Added:** JSON-LD schemas (RealEstateListing, Product, Apartment) for Google rich results
- **Added:** Dynamic alt text for all images
- **Added:** Comprehensive SEO footer

---

## Prioritized Backlog

### P0 - Verified ✅
- [x] Login working on custom domain (user confirmed)
- [x] JSON-LD RealEstateListing schema implemented
- [x] SEO Optimization - Location pages enhanced with rich content, FAQs, JSON-LD
- [x] Page Speed Optimization - Lazy loading, preloading, GZip compression, Web Vitals

### P0 - High Priority
- [ ] Complete `#FeeFreeFinds` branding strategy
  - Add badges to listings
  - Update social sharing text

### P1 - Important
- [ ] Image re-ordering for listings in admin panel
- [ ] Add "Admin" link back to UI (e.g., footer)

### P2 - Nice to Have
- [ ] Advanced Filters (move-in date, pet-friendly, etc.)
- [ ] Backlink-building strategy

### P3 - Future
- [ ] Google Business Profile for NoFeesApts
- [ ] User-facing apartment comparison feature
- [ ] Google/Facebook Ad campaigns (negative keyword lists ready)

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

## Test Credentials
- **Admin:** `placesfirm@gmail.com` / `Checkers080/?`
- **User:** `chris.trunell@gmail.com` / `TestPass123!`

---

## SEO Documentation Files
- `/app/memory/SEO_STRATEGY.md` - Full SEO strategy with target keywords, negative keywords, brand positioning
- `/app/memory/GOOGLE_ADS_NEGATIVE_KEYWORDS.md` - Copy-paste ready lists for Google Ads campaigns
- `/app/frontend/public/robots.txt` - Crawler directives with documentation
