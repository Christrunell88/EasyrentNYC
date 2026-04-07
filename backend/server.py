"""
NoFeesApts.com - Main FastAPI Application
Slim server that imports modular route files.
"""
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pathlib import Path
import os
import logging
import subprocess

from database import db, client
from services import (
    SEED_MODULE_AVAILABLE, seed_functions,
    LIFECYCLE_SERVICE_AVAILABLE, lifecycle_functions
)

# Route imports
from routes.auth import router as auth_router
from routes.buildings import router as buildings_router
from routes.units import router as units_router
from routes.favorites import router as favorites_router
from routes.saved_searches import router as saved_searches_router
from routes.calendar import router as calendar_router
from routes.contact import router as contact_router
from routes.admin_staging import router as admin_staging_router
from routes.admin_operations import router as admin_operations_router
from routes.admin_general import router as admin_general_router
from routes.ai_search import router as ai_search_router
from routes.admin_import import router as admin_import_router
from routes.lifecycle import router as lifecycle_router
from routes.seo import router as seo_router
from routes.social import router as social_router

ROOT_DIR = Path(__file__).parent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Ensure Playwright browsers are installed
def ensure_playwright_browsers():
    """Install Playwright browsers if not present"""
    browsers_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '/pw-browsers')
    chromium_path = Path(browsers_path) / 'chromium_headless_shell-1194'

    if not chromium_path.exists():
        logging.info("Installing Playwright Chromium browser...")
        try:
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
            result = subprocess.run(
                ['playwright', 'install', 'chromium'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logging.info("Playwright browser installed successfully")
            else:
                logging.warning(f"Playwright install warning: {result.stderr}")
        except Exception as e:
            logging.warning(f"Could not install Playwright browser: {e}")
    else:
        logging.info("Playwright browser already installed")

ensure_playwright_browsers()


# Create the main app
app = FastAPI()

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router with /api prefix
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(buildings_router)
api_router.include_router(units_router)
api_router.include_router(favorites_router)
api_router.include_router(saved_searches_router)
api_router.include_router(calendar_router)
api_router.include_router(contact_router)
api_router.include_router(admin_staging_router)
api_router.include_router(admin_operations_router)
api_router.include_router(admin_general_router)
api_router.include_router(ai_search_router)
api_router.include_router(admin_import_router)
api_router.include_router(lifecycle_router)
api_router.include_router(seo_router)
api_router.include_router(social_router)

# Include API router in app
app.include_router(api_router)

# Mount static files for uploaded images
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# ============ ROOT-LEVEL ROUTES ============
from fastapi.responses import PlainTextResponse

@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots():
    """Serve robots.txt for search engines"""
    base_url = 'https://www.nofeesapts.com'
    robots_content = f"""User-agent: *
Allow: /

# Sitemap
Sitemap: {base_url}/api/sitemap.xml

# Disallow admin and auth pages from indexing
Disallow: /admin
Disallow: /api/
"""
    return PlainTextResponse(content=robots_content, media_type="text/plain")


# ============ STARTUP / SHUTDOWN EVENTS ============

@app.on_event("startup")
async def create_indexes():
    """Create database indexes for query optimization"""
    try:
        try:
            from create_indexes import create_indexes as create_all_indexes, ensure_geospatial_field

            await ensure_geospatial_field(db)
            results = await create_all_indexes(db)
            logger.info(f"Database indexes: {len(results['created'])} created, {len(results['already_exists'])} already existed")

            if results['errors']:
                for err in results['errors'][:3]:
                    logger.warning(f"Index creation warning: {err}")
        except ImportError:
            logger.warning("Index creation script not available, using basic indexes")

            await db.units.create_index([("building_id", 1)])
            await db.units.create_index([("is_available", 1)])
            await db.units.create_index([("bedrooms", 1)])
            await db.units.create_index([("rent", 1)])
            await db.units.create_index([("lifecycle_status", 1)])

            await db.buildings.create_index([("neighborhood", 1)])
            await db.buildings.create_index([("city", 1)])
            await db.buildings.create_index([("normalized_address", 1)], sparse=True)

            await db.user_sessions.create_index([("session_token", 1)], unique=True)
            await db.user_sessions.create_index([("expires_at", 1)])

            await db.units_staging.create_index([("review_status", 1)])
            await db.units_staging.create_index([("duplicate_score", -1)])
            await db.buildings_staging.create_index([("review_status", 1)])

            logger.info("Basic database indexes created successfully")

    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")


@app.on_event("startup")
async def auto_seed_database():
    """Auto-seed database on startup if it's empty or has fewer records than seed data"""
    if not SEED_MODULE_AVAILABLE:
        logger.info("Skipping auto-seed: seeding module not available")
        return

    try:
        current_buildings = await db.buildings.count_documents({})
        current_units = await db.units.count_documents({})

        load_seed_data = seed_functions['load_seed_data']
        seed_database = seed_functions['seed_database']
        buildings_data, units_data = await load_seed_data()

        if current_buildings < len(buildings_data) or current_units < len(units_data):
            logger.info(f"Auto-seeding database: current has {current_buildings} buildings, {current_units} units; seed has {len(buildings_data)} buildings, {len(units_data)} units")
            result = await seed_database(force=False)
            logger.info(f"Auto-seed complete: {result.get('message', 'done')}")
        else:
            logger.info(f"Database already has sufficient data ({current_buildings} buildings, {current_units} units), skipping auto-seed")
    except Exception as e:
        logger.warning(f"Auto-seed warning: {str(e)}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# ============ SCHEDULER ============

scheduler = BackgroundScheduler()


def scheduled_crawl_job():
    """Run crawl for all buildings every 48 hours"""
    import asyncio
    from crawler import crawl_all_buildings

    logger.info("Starting scheduled crawl...")
    try:
        asyncio.run(crawl_all_buildings())
        logger.info("Scheduled crawl completed")
    except Exception as e:
        logger.error(f"Scheduled crawl error: {e}")


def scheduled_stale_check_job():
    """Check for stale units daily"""
    import asyncio

    logger.info("Starting scheduled stale check...")
    try:
        if LIFECYCLE_SERVICE_AVAILABLE:
            run_stale_check = lifecycle_functions['run_stale_check']
            asyncio.run(run_stale_check(db))
            logger.info("Scheduled stale check completed")
        else:
            logger.warning("Lifecycle service not available, skipping stale check")
    except Exception as e:
        logger.error(f"Scheduled stale check error: {e}")


def scheduled_saved_search_alerts_job():
    """Run saved search alerts daily"""
    import asyncio
    from alert_tasks import process_saved_search_alerts

    logger.info("Starting scheduled saved search alerts...")
    try:
        alerts_sent = asyncio.run(process_saved_search_alerts())
        logger.info(f"Scheduled saved search alerts completed: {alerts_sent} alerts sent")
    except Exception as e:
        logger.error(f"Scheduled saved search alerts error: {e}")


scheduler.add_job(
    scheduled_crawl_job,
    trigger=IntervalTrigger(hours=48),
    id='crawl_job',
    replace_existing=True
)

scheduler.add_job(
    scheduled_stale_check_job,
    trigger=IntervalTrigger(hours=24),
    id='stale_check_job',
    replace_existing=True
)

scheduler.add_job(
    scheduled_saved_search_alerts_job,
    trigger=IntervalTrigger(hours=6),
    id='saved_search_alerts_job',
    replace_existing=True
)


@app.on_event("startup")
async def startup_event():
    scheduler.start()
    logger.info("Scheduler started - crawling every 48 hours, stale check daily, saved search alerts every 6 hours")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
