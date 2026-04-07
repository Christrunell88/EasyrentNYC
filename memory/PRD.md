# NoFeesApts.com - Product Requirements Document

## Original Problem Statement
Build a web application called "NoFeesApts.com" to crawl publicly available real estate websites for no-fee apartment listings in NYC, Northern New Jersey, and PA.

## Core Requirements
- Crawl websites for apartment data
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
├── server.py              # Slim app entry (282 lines) - CORS, router includes, scheduler
├── database.py            # MongoDB connection module
├── models.py              # All Pydantic models (424 lines)
├── auth_utils.py          # Auth dependencies (62 lines)
├── services.py            # External service availability flags (118 lines)
├── alert_tasks.py         # Scheduled alert task functions (145 lines)
├── routes/
│   ├── auth.py            # Auth routes - signup, login, logout, OAuth (362 lines)
│   ├── buildings.py       # Buildings CRUD (75 lines)
│   ├── units.py           # Units CRUD + hero/recent/recommendations (644 lines)
│   ├── favorites.py       # Favorites CRUD (69 lines)
│   ├── saved_searches.py  # Saved searches + social proof (197 lines)
│   ├── calendar.py        # Calendar OAuth + viewings (226 lines)
│   ├── contact.py         # Contact + subscribe + share (285 lines)
│   ├── admin_staging.py   # Staging CRUD + bulk operations (1312 lines)
│   ├── admin_operations.py # Unavailability + relisting + rejected (568 lines)
│   ├── admin_general.py   # Stats + users + crawl + neighborhoods (303 lines)
│   ├── ai_search.py       # AI search + analytics (324 lines)
│   ├── admin_import.py    # Property search/discovery/crawl/import (731 lines)
│   ├── lifecycle.py       # Lifecycle management (206 lines)
│   ├── seo.py             # Sitemap (43 lines)
│   └── social.py          # Facebook posting (224 lines)
├── scrapers/
│   ├── generic.py
│   └── trulia.py
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
│   │   ├── ImportTab.jsx          # Property import tab (311 lines)
│   │   ├── StagingTab.jsx         # Staging review tab (477 lines)
│   │   ├── UnavailabilityTab.jsx  # Unavailability review tab (214 lines)
│   │   ├── RentedTab.jsx          # Rented/unavailable units tab (175 lines)
│   │   └── RejectedTab.jsx        # Rejected staging units tab (112 lines)
│   ├── SavedSearchModal.jsx
│   └── AISearchAgent.jsx
├── pages/
│   ├── Landing.jsx
│   ├── Dashboard.jsx
│   ├── AdminPanel.jsx    # Slim parent (780 lines, down from 3423)
│   ├── UnitDetails.jsx
│   ├── BronxPage.jsx
│   ├── HobokenPage.jsx
│   └── JerseyCityPage.jsx
└── App.js
```

## What's Been Implemented

### Completed Features
- Full CRUD for buildings and units
- JWT + Google OAuth authentication
- Admin staging/approval pipeline with bulk operations
- AI Search Agent "Kiri" with real-time web search (SerpApi)
- Saved searches with email/SMS alerts
- Google Calendar OAuth for scheduling viewings
- SEO landing pages (Bronx, Hoboken, Jersey City)
- Sitemap generation
- Hero carousel with featured units
- Email subscribers
- Social proof metrics
- Trulia-specific scraper
- Unit lifecycle management (available → stale → rented)
- Facebook sharing integration
- CSV export for admin inventory
- Password reset (admin + user-initiated)

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
