# NoFeesApts.com - Product Requirements Document

## Original Problem Statement
Build a web application called "NoFeesApts.com" to crawl publicly available real estate websites for no-fee apartment listings in NYC, Northern New Jersey, and PA.

## Core Requirements
- Crawl websites for apartment data using Playwright for JS-heavy sites
- MongoDB data storage
- JWT and Google Auth
- Admin staging and review pipeline
- AI Search Agent ("Kiri") and Discovery features with real-time web search
- Robust SEO structure (Dynamic landing pages for Neighborhoods/Boroughs)
- Immersive frontend UI with curated Hero Carousel
- Email alerts and saved searches for users
- Google Calendar integration for scheduling viewings

## Architecture

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py              # Slim app entry (~282 lines) - CORS, router includes, scheduler
├── database.py            # MongoDB connection module
├── models.py              # All Pydantic models (~425 lines)
├── auth_utils.py          # Auth dependencies
├── services.py            # External service availability flags
├── alert_tasks.py         # Scheduled alert task functions
├── routes/
│   ├── auth.py            # Auth routes - signup, login, logout, OAuth
│   ├── buildings.py       # Buildings CRUD
│   ├── units.py           # Units CRUD + hero/recent/recommendations
│   ├── favorites.py       # Favorites CRUD
│   ├── saved_searches.py  # Saved searches + social proof
│   ├── calendar.py        # Calendar OAuth + viewings
│   ├── contact.py         # Contact + subscribe + share
│   ├── admin_staging.py   # Staging CRUD + bulk operations
│   ├── admin_operations.py # Unavailability + relisting + rejected
│   ├── admin_general.py   # Stats + users + crawl + neighborhoods
│   ├── ai_search.py       # AI search + analytics
│   ├── admin_import.py    # Property search/discovery/crawl/import (multi-building support)
│   ├── lifecycle.py       # Lifecycle management
│   ├── seo.py             # Sitemap
│   └── social.py          # Facebook posting
├── scrapers/
│   ├── base.py            # Playwright browser config
│   ├── generic.py         # Generic Playwright scraper
│   └── trulia.py          # Trulia-specific scraper
├── smtp_email_service.py
├── twilio_sms_service.py
├── google_calendar_service.py
├── sitemap_generator.py
└── uploads/
```

### Frontend (React + Tailwind + Shadcn)
```
/app/frontend/src/
├── components/
│   ├── admin/
│   │   ├── ImportTab.jsx          # Property import with multi-building grouped preview
│   │   ├── StagingTab.jsx         # Staging review tab
│   │   ├── UnavailabilityTab.jsx  # Unavailability review tab
│   │   ├── RentedTab.jsx          # Rented/unavailable units tab
│   │   └── RejectedTab.jsx        # Rejected staging units tab
│   ├── SavedSearchModal.jsx
│   └── AISearchAgent.jsx
├── pages/
│   ├── Landing.jsx
│   ├── Dashboard.jsx
│   ├── AdminPanel.jsx    # Slim parent (~780 lines)
│   ├── UnitDetails.jsx
│   ├── BronxPage.jsx
│   ├── HobokenPage.jsx
│   └── JerseyCityPage.jsx
└── App.js
```

## What's Been Implemented

### Completed Features
- Full CRUD for buildings and units
- JWT authentication + Google Auth
- Admin staging/review pipeline with bulk operations
- AI Search Agent "Kiri" with web search
- SEO landing pages (Bronx, Hoboken, Jersey City)
- Saved Searches with email alerts
- Google Calendar OAuth for scheduling viewings
- Hero Carousel on landing page
- Playwright-based web crawler for management company sites
- Trulia-specific scraper
- Facebook sharing integration
- Email alerts via SMTP
- Google Search Console verification
- **Multi-building crawler support**: Crawler detects per-unit addresses on management company pages with multiple buildings, groups units by address, creates separate staging buildings per unique address (Apr 2026)
- **Modular architecture**: server.py split into route modules, AdminPanel.jsx split into tab components (Apr 2026)
- **Batch Crawl All**: One-click crawl of all 29 management companies with real-time progress tracking, cancel support, and auto-import to staging (Apr 2026)
- **Image upload fix**: Fixed path mismatch between file save directory and static file mount (Apr 2026)
- **Dynamic OG Meta Tags**: Social media crawlers (Facebook, Twitter, LinkedIn, WhatsApp, Discord, Slack, etc.) now receive pre-rendered HTML with dynamic OG tags for unit listings, borough pages, neighborhood pages, and the landing page. Regular users get the normal React SPA. Works in both dev (`setupProxy.js`) and production (`server.js` Express server). Includes admin preview endpoint at `/api/og-preview?path=...`. (Apr 2026)

## Backlog

### P0 (Blocked)
- Twilio SMS Alerts — awaiting user credentials (Account SID, Auth Token, Phone Number)

### P1
- Add 111 Worth Street building and vacant units
- Implement virtual tour support (virtual_tour_url in DB and unit details UI)
- Instagram direct posting (blocked on Facebook Page admin permissions)

### P2
- Create Staten Island SEO landing page
- Blog for long-form SEO content
- Scheduled weekly discovery searches for Admin crawler

### Refactoring Completed (April 2026)
- **Backend**: server.py split from 6315 lines → 282 lines + 16 modular route files + 4 shared modules
- **Frontend**: AdminPanel.jsx split from 3423 lines → 780 lines + 5 extracted tab components
- All 33 backend API tests passing (100%)
- All 15 admin panel tabs verified working

## Pending Issues
1. **Twilio SMS** (P0) - Code complete, awaiting credentials from user
2. **Instagram Posting** (P1) - Blocked on Facebook Page admin permissions
3. **Facebook Sharing Verification** (P1) - Fix deployed, awaiting user test
4. **Dynamic OG Tags** (P2) - CSR limitation, needs SSR/pre-rendering discussion

## Upcoming Tasks
- P1: Virtual tour support (virtual_tour_url field + UI)
- P2: Staten Island SEO landing page
- P2: Blog for long-form SEO content
- P3: Scheduled weekly discovery searches

## 3rd Party Integrations
- Google Search Results (SerpApi) - User API Key required
- Facebook Graph API - Blocked on credentials
- SMTP Gmail - Configured
- Google Calendar API - Configured
- Twilio SMS - Awaiting credentials
- Google Search Console - Verification tag added

## Key API Endpoints
- POST /api/auth/login, /api/auth/signup, /api/auth/logout
- GET /api/buildings, /api/units, /api/hero-units, /api/neighborhoods
- GET /api/admin/stats, /api/admin/users, /api/admin/staging/units
- POST /api/saved-searches, GET /api/saved-searches
- GET /api/oauth/calendar/connect
- POST /api/units/{unit_id}/schedule-viewing
- PUT /api/admin/staging/bulk-approve, DELETE /api/admin/staging/bulk-delete

## Data Models
- `users`: {id, email, name, password_hash, is_admin, created_at}
- `buildings`: {id, name, address, neighborhood, city, state, zip_code, source_url}
- `units`: {id, building_id, unit_number, rent, bedrooms, bathrooms, lifecycle_status}
- `saved_searches`: {id, user_id, filters, alert_frequency, notify_email, notify_sms}
- `units_staging`: {id, building_id, unit_number, rent, review_status, duplicate_score}
