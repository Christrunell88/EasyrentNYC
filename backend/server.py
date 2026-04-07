from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import subprocess
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import requests
import shutil
import base64
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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

# Run browser check at module load
ensure_playwright_browsers()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7

# Create the main app
app = FastAPI()

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
# print(":white_tick: CORS Origins:", origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import SMTP email service
EMAIL_SERVICE_AVAILABLE = False
try:
    from smtp_email_service import smtp_service
    EMAIL_SERVICE_AVAILABLE = True
    logger.info("SMTP email service loaded successfully")
except Exception as e:
    EMAIL_SERVICE_AVAILABLE = False
    logger.warning(f"Email service not available: {str(e)}")

# Import Twilio SMS service
SMS_SERVICE_AVAILABLE = False
try:
    from twilio_sms_service import (
        send_sms, send_saved_search_alert_sms, 
        send_viewing_confirmation_sms, is_sms_enabled
    )
    SMS_SERVICE_AVAILABLE = is_sms_enabled()
    if SMS_SERVICE_AVAILABLE:
        logger.info("Twilio SMS service loaded successfully")
    else:
        logger.warning("Twilio SMS service loaded but not configured")
except Exception as e:
    SMS_SERVICE_AVAILABLE = False
    logger.warning(f"SMS service not available: {str(e)}")

# Import Google Calendar service
CALENDAR_SERVICE_AVAILABLE = False
try:
    from google_calendar_service import (
        get_oauth_authorization_url, exchange_code_for_tokens,
        get_user_email_from_token, create_viewing_event,
        delete_viewing_event, is_calendar_enabled
    )
    CALENDAR_SERVICE_AVAILABLE = is_calendar_enabled()
    if CALENDAR_SERVICE_AVAILABLE:
        logger.info("Google Calendar service loaded successfully")
    else:
        logger.warning("Google Calendar service loaded but not configured")
except Exception as e:
    CALENDAR_SERVICE_AVAILABLE = False
    logger.warning(f"Calendar service not available: {str(e)}")

# Import database seeding module
SEED_MODULE_AVAILABLE = False
try:
    from seed_database import seed_database, check_database_status, load_seed_data
    SEED_MODULE_AVAILABLE = True
    logger.info("Database seeding module loaded successfully")
except Exception as e:
    SEED_MODULE_AVAILABLE = False
    logger.warning(f"Database seeding module not available: {str(e)}")

# Import promotion service
PROMOTION_SERVICE_AVAILABLE = False
try:
    from promotion_service import PromotionService, get_promotion_service
    PROMOTION_SERVICE_AVAILABLE = True
    logger.info("Promotion service loaded successfully")
except Exception as e:
    PROMOTION_SERVICE_AVAILABLE = False
    logger.warning(f"Promotion service not available: {str(e)}")

# Import lifecycle management service
LIFECYCLE_SERVICE_AVAILABLE = False
try:
    from lifecycle_service import UnitLifecycleService, get_lifecycle_service, run_stale_check
    LIFECYCLE_SERVICE_AVAILABLE = True
    logger.info("Lifecycle service loaded successfully")
except Exception as e:
    LIFECYCLE_SERVICE_AVAILABLE = False
    logger.warning(f"Lifecycle service not available: {str(e)}")

# ============ MODELS ============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    password_hash: Optional[str] = None  # For JWT auth
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Building(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    source_url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_crawled: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Unit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    building_id: str
    unit_number: str
    rent: float
    bedrooms: int  # 0 for studio
    bathrooms: float
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    description: Optional[str] = None
    is_available: bool = True
    is_featured: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Lifecycle management fields
    lifecycle_status: str = Field(default="available")  # available, stale, rented, unavailable
    stale_since: Optional[datetime] = None
    rented_at: Optional[datetime] = None
    rented_notes: Optional[str] = None
    lifecycle_updated_at: Optional[datetime] = None
    # Verification fields (set when approved from staging)
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    # Source metadata (maintained from staging)
    crawler_source: Optional[str] = None
    crawler_batch_id: Optional[str] = None
    original_staging_id: Optional[str] = None
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============ STAGING MODELS ============
# These collections store crawled/unverified listings before production approval

class ReviewStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class BuildingStaging(BaseModel):
    """Staging collection for crawled buildings awaiting review"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Core building fields (mirror production)
    name: str
    address: str
    normalized_address: Optional[str] = None  # Standardized address format
    neighborhood: str
    city: str
    normalized_city: Optional[str] = None
    state: str
    normalized_state: Optional[str] = None  # 2-letter abbreviation
    zip_code: str
    normalized_zip: Optional[str] = None  # 5-digit format
    address_hash: Optional[str] = None  # For duplicate detection
    source_url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_crawled: Optional[datetime] = None
    # Staging-specific fields
    review_status: str = Field(default="pending")  # pending, approved, rejected
    crawler_source: str = Field(default="")  # e.g., "mercedeshouseny.com", "tfc.com"
    crawler_batch_id: str = Field(default="")  # unique identifier for the crawl batch
    validation_flags: List[str] = Field(default_factory=list)  # e.g., ["missing_zip", "invalid_address"]
    duplicate_score: float = Field(default=0.0)  # 0-1, higher means more likely duplicate
    matched_production_id: Optional[str] = None  # ID of matching production building if duplicate
    raw_data: Optional[dict] = None  # Store original crawled data
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UnitStaging(BaseModel):
    """Staging collection for crawled units awaiting review"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Core unit fields (mirror production)
    building_id: str  # References building_staging.id or buildings.id
    unit_number: str
    normalized_unit_number: Optional[str] = None  # Standardized unit number for duplicate detection
    rent: float
    bedrooms: int  # 0 for studio
    bathrooms: float
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    original_images: List[str] = []  # Store original URLs before GCS upload
    description: Optional[str] = None
    is_available: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Staging-specific fields
    review_status: str = Field(default="pending")  # pending, approved, rejected
    crawler_source: str = Field(default="")  # e.g., "mercedeshouseny.com", "tfc.com"
    crawler_batch_id: str = Field(default="")  # unique identifier for the crawl batch
    validation_flags: List[str] = Field(default_factory=list)  # e.g., ["possible_duplicate", "missing_images", "invalid_rent"]
    duplicate_score: float = Field(default=0.0)  # 0-1, higher means more likely duplicate
    matched_production_id: Optional[str] = None  # ID of matching production unit if duplicate
    raw_data: Optional[str] = None  # Store original crawled HTML/data
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Favorite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    unit_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SavedSearch(BaseModel):
    """Saved search for email alerts"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    user_phone: Optional[str] = None  # For SMS alerts
    name: str  # User-friendly name for the search
    # Search criteria
    bedrooms: Optional[int] = None  # 0 for studio, None for any
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    bathrooms: Optional[float] = None
    state: Optional[str] = None  # NY, NJ, PA
    neighborhood: Optional[str] = None
    # Alert settings
    alert_frequency: str = "daily"  # daily, weekly, instant
    notify_email: bool = True
    notify_sms: bool = False
    is_active: bool = True
    last_alert_sent: Optional[datetime] = None
    # Track what was already sent
    last_checked_at: Optional[datetime] = None
    notified_unit_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    unit_id: str
    message: str
    name: str
    email: str
    phone: Optional[str] = None
    preferred_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AISearchRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class AISearchHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    query: str
    response: str
    units_found: int = 0
    neighborhoods_mentioned: List[str] = []
    price_range: Optional[dict] = None
    bedrooms_requested: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    preferred_time: Optional[str] = None
    alternative_date: Optional[str] = None
    alternative_time: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============ INPUT MODELS ============

class SignupInput(BaseModel):
    email: str
    password: str
    name: str

class LoginInput(BaseModel):
    email: str
    password: str

class ForgotPasswordInput(BaseModel):
    email: str

class ResetPasswordInput(BaseModel):
    token: str
    new_password: str

class AdminResetPasswordInput(BaseModel):
    user_id: str
    new_password: str

class ShareUnitInput(BaseModel):
    unit_id: str
    recipient_email: str
    message: Optional[str] = None

class EmailSubscribeInput(BaseModel):
    email: str

class BuildingInput(BaseModel):
    name: str
    address: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    source_url: str

class UnitInput(BaseModel):
    building_id: str
    unit_number: str
    rent: float
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    description: Optional[str] = None
    is_available: bool = True
    is_featured: bool = False

class ContactInput(BaseModel):
    unit_id: str
    message: str
    name: str
    email: str
    phone: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    alternative_date: Optional[str] = None
    alternative_time: Optional[str] = None

# ============ STAGING INPUT MODELS ============

class BuildingStagingInput(BaseModel):
    """Input model for creating/updating staging buildings"""
    name: str
    address: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    source_url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    crawler_source: str = ""
    crawler_batch_id: str = ""
    validation_flags: List[str] = []
    duplicate_score: float = 0.0

class UnitStagingInput(BaseModel):
    """Input model for creating/updating staging units"""
    building_id: str
    unit_number: str
    rent: float
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    description: Optional[str] = None
    is_available: bool = True
    crawler_source: str = ""
    crawler_batch_id: str = ""
    validation_flags: List[str] = []
    duplicate_score: float = 0.0

class StagingReviewInput(BaseModel):
    """Input model for reviewing staging items"""
    review_status: str  # "approved" or "rejected"
    reviewer_notes: Optional[str] = None

class StagingUnitEditInput(BaseModel):
    """Input model for editing staging unit details before approval"""
    building_id: Optional[str] = None
    unit_number: Optional[str] = None
    rent: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None  # Allow updating images

class StagingBulkReviewInput(BaseModel):
    """Input model for bulk reviewing staging items"""
    ids: List[str]
    review_status: str  # "approved" or "rejected"
    reviewer_notes: Optional[str] = None

class SavedSearchInput(BaseModel):
    """Input model for creating/updating saved searches"""
    name: str
    bedrooms: Optional[int] = None
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    bathrooms: Optional[float] = None
    state: Optional[str] = None
    neighborhood: Optional[str] = None
    alert_frequency: str = "daily"  # daily, weekly, instant
    phone_number: Optional[str] = None  # For SMS alerts
    notify_email: bool = True
    notify_sms: bool = False

class ScheduleViewingInput(BaseModel):
    """Input model for scheduling apartment viewings"""
    unit_id: str
    viewing_date: str  # ISO format date
    viewing_time: str  # HH:MM format
    notes: Optional[str] = None

# ============ AUTH HELPERS ============

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session_token cookie or Authorization header"""
    session_token = request.cookies.get('session_token')
    
    if not session_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header.split(' ')[1]
    
    if not session_token:
        return None
    
    session = await db.user_sessions.find_one({
        'session_token': session_token,
        'expires_at': {'$gt': datetime.now(timezone.utc).isoformat()}
    })
    
    if not session:
        return None
    
    user_doc = await db.users.find_one({'id': session['user_id']})
    if not user_doc:
        return None
    
    return User(**user_doc)

async def require_auth(request: Request) -> User:
    """Require authentication"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

async def require_admin(request: Request) -> User:
    """Require admin privileges"""
    user = await require_auth(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ============ AUTH ROUTES ============

@api_router.post("/auth/signup")
async def signup(input: SignupInput, response: Response, background_tasks: BackgroundTasks):
    """JWT-based signup with email/password"""
    existing = await db.users.find_one({'email': input.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=input.email,
        name=input.name,
        password_hash=hash_password(input.password)
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    await db.users.insert_one(user_dict)
    
    # Create session
    session_token = str(uuid.uuid4())
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    )
    
    session_dict = session.model_dump()
    session_dict['expires_at'] = session_dict['expires_at'].isoformat()
    session_dict['created_at'] = session_dict['created_at'].isoformat()
    await db.user_sessions.insert_one(session_dict)
    
    # Set cookie
    response.set_cookie(
        key='session_token',
        value=session_token,
        httponly=True,
        secure=False,  # Allow HTTP cookies for localhost development
        samesite='lax',
        max_age=JWT_EXPIRATION_DAYS * 24 * 60 * 60,
        path='/'
    )
    
    # Send welcome email in background
    if EMAIL_SERVICE_AVAILABLE:
        background_tasks.add_task(
            smtp_service.send_welcome_email,
            user_email=user.email,
            user_name=user.name
        )
        logger.info(f"Welcome email queued for new user: {user.email}")
    
    return {
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'is_admin': user.is_admin
        },
        'session_token': session_token
    }

@api_router.post("/auth/login")
async def login(input: LoginInput, response: Response, request: Request):
    """JWT-based login with email/password"""
    user_doc = await db.users.find_one({'email': input.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**user_doc)
    
    if not user.password_hash or not verify_password(input.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_token = str(uuid.uuid4())
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    )
    
    session_dict = session.model_dump()
    session_dict['expires_at'] = session_dict['expires_at'].isoformat()
    session_dict['created_at'] = session_dict['created_at'].isoformat()
    await db.user_sessions.insert_one(session_dict)
    
    # Set cookie
    response.set_cookie(
        key='session_token',
        value=session_token,
        httponly=True,
        secure=False,  # Allow HTTP cookies for localhost development
        samesite='lax',
        max_age=JWT_EXPIRATION_DAYS * 24 * 60 * 60,
        path='/'
    )
    
    return {
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'is_admin': user.is_admin
        },
        'session_token': session_token
    }

@api_router.post("/auth/forgot-password")
async def forgot_password(input: ForgotPasswordInput):
    """Send password reset email to user"""
    user_doc = await db.users.find_one({'email': input.email})
    
    # Always return success to prevent email enumeration
    if not user_doc:
        logger.info(f"Password reset requested for non-existent email: {input.email}")
        return {'message': 'If the email exists, a password reset link has been sent'}
    
    user = User(**user_doc)
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    reset_expiry = datetime.now(timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
    
    # Store reset token
    await db.password_resets.insert_one({
        'user_id': user.id,
        'token': reset_token,
        'expires_at': reset_expiry.isoformat(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'used': False
    })
    
    # Send email with reset link
    try:
        if EMAIL_SERVICE_AVAILABLE:
            from email_service import get_gmail_service
            import base64
            from email.mime.text import MIMEText
            
            service = get_gmail_service()
            # Use the actual domain from environment or default to the live domain
            base_url = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')
            reset_url = f"{base_url}/reset-password?token={reset_token}"
            
            # Create email
            message = MIMEText(f"""
Hello {user.name or 'User'},

You requested a password reset for your NoFeesApts.com account.

Click the link below to reset your password (valid for 1 hour):
{reset_url}

If you didn't request this, please ignore this email.

Best regards,
NoFeesApts.com Team
            """)
            
            message['to'] = user.email
            message['subject'] = 'Password Reset - NoFeesApts.com'
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
    
    return {'message': 'If the email exists, a password reset link has been sent'}

@api_router.post("/auth/reset-password")
async def reset_password(input: ResetPasswordInput):
    """Reset password using token"""
    # Find reset token
    reset_doc = await db.password_resets.find_one({
        'token': input.token,
        'used': False
    })
    
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(reset_doc['expires_at'])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Update user password
    new_password_hash = hash_password(input.new_password)
    await db.users.update_one(
        {'id': reset_doc['user_id']},
        {'$set': {'password_hash': new_password_hash}}
    )
    
    # Mark token as used
    await db.password_resets.update_one(
        {'token': input.token},
        {'$set': {'used': True}}
    )
    
    logger.info(f"Password reset successful for user {reset_doc['user_id']}")
    
    return {'message': 'Password reset successful'}

@api_router.post("/admin/reset-password")
async def admin_reset_password(input: AdminResetPasswordInput, admin: User = Depends(require_admin)):
    """Admin endpoint to reset any user's password"""
    # Check if user exists
    user_doc = await db.users.find_one({'id': input.user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = User(**user_doc)
    
    # Update password
    new_password_hash = hash_password(input.new_password)
    await db.users.update_one(
        {'id': input.user_id},
        {'$set': {'password_hash': new_password_hash}}
    )
    
    logger.info(f"Admin {admin.email} reset password for user {user.email}")
    
    # Send email notification to user
    try:
        if EMAIL_SERVICE_AVAILABLE:
            from email_service import get_gmail_service
            import base64
            from email.mime.text import MIMEText
            
            service = get_gmail_service()
            
            message = MIMEText(f"""
Hello {user.name or 'User'},

Your NoFeesApts.com password has been reset by an administrator.

Your new temporary password is: {input.new_password}

Please log in and change your password immediately.

Best regards,
NoFeesApts.com Team
            """)
            
            message['to'] = user.email
            message['subject'] = 'Your Password Has Been Reset - NoFeesApts.com'
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Password reset notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send password reset notification: {e}")
    
    return {'message': f'Password reset successfully for {user.email}'}

@api_router.post("/auth/session")
async def create_session_from_oauth(request: Request, response: Response):
    """Process Emergent OAuth session_id"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    
    # Get user data from Emergent
    try:
        resp = requests.get(
            'https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data',
            headers={'X-Session-ID': session_id},
            timeout=10
        )
        resp.raise_for_status()
        oauth_data = resp.json()
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=400, detail="Invalid session_id")
    
    # Check if user exists
    user_doc = await db.users.find_one({'email': oauth_data['email']})
    
    if not user_doc:
        # Create new user
        user = User(
            email=oauth_data['email'],
            name=oauth_data.get('name', oauth_data['email']),
            picture=oauth_data.get('picture')
        )
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await db.users.insert_one(user_dict)
    else:
        user = User(**user_doc)
    
    # Create session with Emergent's session_token
    session_token = oauth_data['session_token']
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    
    session_dict = session.model_dump()
    session_dict['expires_at'] = session_dict['expires_at'].isoformat()
    session_dict['created_at'] = session_dict['created_at'].isoformat()
    await db.user_sessions.insert_one(session_dict)
    
    # Set cookie
    response.set_cookie(
        key='session_token',
        value=session_token,
        httponly=True,
        secure=False,  # Allow HTTP cookies for localhost development
        samesite='lax',
        max_age=7 * 24 * 60 * 60,
        path='/'
    )
    
    return {
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'picture': user.picture,
            'is_admin': user.is_admin
        },
        'session_token': session_token
    }

@api_router.get("/auth/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current user"""
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'picture': user.picture,
        'is_admin': user.is_admin
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get('session_token')
    if session_token:
        await db.user_sessions.delete_many({'session_token': session_token})
    
    response.delete_cookie(key='session_token', path='/')
    return {'message': 'Logged out'}

# ============ BUILDING ROUTES ============

@api_router.get("/buildings", response_model=List[Building])
async def get_buildings():
    """Get all buildings"""
    buildings = await db.buildings.find({}, {"_id": 0}).to_list(1000)
    for b in buildings:
        if isinstance(b.get('created_at'), str):
            b['created_at'] = datetime.fromisoformat(b['created_at'])
        if b.get('last_crawled') and isinstance(b['last_crawled'], str):
            b['last_crawled'] = datetime.fromisoformat(b['last_crawled'])
    return buildings

@api_router.get("/buildings/{building_id}", response_model=Building)
async def get_building(building_id: str):
    """Get building by ID"""
    building = await db.buildings.find_one({'id': building_id}, {"_id": 0})
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    if isinstance(building.get('created_at'), str):
        building['created_at'] = datetime.fromisoformat(building['created_at'])
    if building.get('last_crawled') and isinstance(building['last_crawled'], str):
        building['last_crawled'] = datetime.fromisoformat(building['last_crawled'])
    
    return building

@api_router.post("/buildings", response_model=Building)
async def create_building(input: BuildingInput, user: User = Depends(require_admin)):
    """Create building (admin only)"""
    building = Building(**input.model_dump())
    building_dict = building.model_dump()
    building_dict['created_at'] = building_dict['created_at'].isoformat()
    await db.buildings.insert_one(building_dict)
    return building

@api_router.put("/buildings/{building_id}", response_model=Building)
async def update_building(building_id: str, input: BuildingInput, user: User = Depends(require_admin)):
    """Update building (admin only)"""
    existing = await db.buildings.find_one({'id': building_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Building not found")
    
    update_data = input.model_dump()
    await db.buildings.update_one({'id': building_id}, {'$set': update_data})
    
    updated = await db.buildings.find_one({'id': building_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if updated.get('last_crawled') and isinstance(updated['last_crawled'], str):
        updated['last_crawled'] = datetime.fromisoformat(updated['last_crawled'])
    
    return updated

@api_router.delete("/buildings/{building_id}")
async def delete_building(building_id: str, user: User = Depends(require_admin)):
    """Delete building and all its units (admin only)"""
    result = await db.buildings.delete_one({'id': building_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Delete all units
    await db.units.delete_many({'building_id': building_id})
    return {'message': 'Building deleted'}

# ============ UNIT ROUTES ============

@api_router.get("/units")
async def get_units(
    neighborhood: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    bedrooms: Optional[int] = None,
    min_rent: Optional[float] = None,
    max_rent: Optional[float] = None,
    bathrooms: Optional[float] = None,
    amenities: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """Search units with filters"""
    query = {'is_available': True}
    
    if bedrooms is not None:
        query['bedrooms'] = bedrooms
    if min_rent is not None:
        query['rent'] = query.get('rent', {})
        query['rent']['$gte'] = min_rent
    if max_rent is not None:
        query['rent'] = query.get('rent', {})
        query['rent']['$lte'] = max_rent
    if bathrooms is not None:
        query['bathrooms'] = bathrooms
    if amenities:
        amenity_list = [a.strip() for a in amenities.split(',')]
        query['amenities'] = {'$in': amenity_list}
    
    # Get units - prioritize featured units
    # First get featured units
    featured_units = await db.units.find(
        {**query, 'is_featured': True}, 
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    # If we need more units to reach the limit, get regular units
    remaining_limit = limit - len(featured_units)
    if remaining_limit > 0:
        regular_units = await db.units.find(
            {**query, 'is_featured': {'$ne': True}}, 
            {"_id": 0}
        ).limit(remaining_limit).to_list(remaining_limit)
        units = featured_units + regular_units
    else:
        units = featured_units
    
    # If neighborhood, city, or state filter, need to join with buildings
    if neighborhood or city or state:
        building_query = {}
        if neighborhood:
            building_query['neighborhood'] = neighborhood
        if city:
            building_query['city'] = city
        if state:
            building_query['state'] = state
        
        buildings = await db.buildings.find(building_query, {"_id": 0}).to_list(1000)
        building_ids = [b['id'] for b in buildings]
        units = [u for u in units if u['building_id'] in building_ids]
    
    # Get building info for each unit - optimized to avoid N+1 queries
    if units:
        # Get all unique building IDs
        building_ids = list(set(u['building_id'] for u in units if u.get('building_id')))
        # Fetch all buildings in one query
        buildings = await db.buildings.find({'id': {'$in': building_ids}}, {"_id": 0}).to_list(len(building_ids))
        # Create a map for quick lookup
        buildings_map = {b['id']: b for b in buildings}
        
        # Attach buildings to units
        for unit in units:
            unit['building'] = buildings_map.get(unit['building_id'])
            
            if isinstance(unit.get('created_at'), str):
                unit['created_at'] = datetime.fromisoformat(unit['created_at'])
            if isinstance(unit.get('updated_at'), str):
                unit['updated_at'] = datetime.fromisoformat(unit['updated_at'])
    
    return units


@api_router.get("/recommendations")
async def get_recommendations():
    """Get smart filter recommendations based on current inventory"""
    try:
        today = datetime.now(timezone.utc)
        week_ago = today - timedelta(days=7)
        
        # 1. Most Popular Buildings - buildings with most available units
        pipeline_popular = [
            {"$match": {"is_available": True}},
            {"$group": {"_id": "$building_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        popular_results = await db.units.aggregate(pipeline_popular).to_list(5)
        popular_building_ids = [r["_id"] for r in popular_results]
        
        # Get building names
        popular_buildings = []
        if popular_building_ids:
            buildings = await db.buildings.find(
                {"id": {"$in": popular_building_ids}}, 
                {"_id": 0, "id": 1, "name": 1}
            ).to_list(5)
            buildings_map = {b["id"]: b["name"] for b in buildings}
            popular_buildings = [
                {"id": r["_id"], "name": buildings_map.get(r["_id"], "Unknown"), "count": r["count"]}
                for r in popular_results if r["_id"] in buildings_map
            ]
        
        # 2. Best Value - lowest price per square foot (only units with sqft data)
        pipeline_value = [
            {"$match": {"is_available": True, "square_feet": {"$gt": 0}}},
            {"$project": {
                "id": 1,
                "building_id": 1,
                "rent": 1,
                "square_feet": 1,
                "bedrooms": 1,
                "price_per_sqft": {"$divide": ["$rent", "$square_feet"]}
            }},
            {"$sort": {"price_per_sqft": 1}},
            {"$limit": 20}
        ]
        value_units = await db.units.aggregate(pipeline_value).to_list(20)
        avg_price_per_sqft = sum(u["price_per_sqft"] for u in value_units) / len(value_units) if value_units else 0
        value_threshold = avg_price_per_sqft * 0.85  # 15% below average
        best_value_count = len([u for u in value_units if u["price_per_sqft"] <= value_threshold])
        
        # 3. New This Week - units created in last 7 days
        new_count = await db.units.count_documents({
            "is_available": True,
            "created_at": {"$gte": week_ago.isoformat()}
        })
        
        # Also check updated_at for recent updates
        if new_count == 0:
            new_count = await db.units.count_documents({
                "is_available": True,
                "updated_at": {"$gte": week_ago.isoformat()}
            })
        
        # 4. Luxury Picks - high-end apartments ($5k+)
        luxury_count = await db.units.count_documents({
            "is_available": True,
            "rent": {"$gte": 5000}
        })
        
        # 5. Studios - always popular for first-time renters
        studio_count = await db.units.count_documents({
            "is_available": True,
            "bedrooms": 0
        })
        
        # 6. Budget Friendly - under $3k
        budget_count = await db.units.count_documents({
            "is_available": True,
            "rent": {"$lte": 3000}
        })
        
        # 7. Family Size - 2+ bedrooms
        family_count = await db.units.count_documents({
            "is_available": True,
            "bedrooms": {"$gte": 2}
        })
        
        # Total available
        total_available = await db.units.count_documents({"is_available": True})
        
        return {
            "recommendations": [
                {
                    "id": "popular_buildings",
                    "label": "Most Popular Buildings",
                    "description": f"Top {len(popular_buildings)} buildings by listings",
                    "count": sum(b["count"] for b in popular_buildings),
                    "filter": {"building_ids": popular_building_ids},
                    "buildings": popular_buildings[:3],
                    "icon": "building"
                },
                {
                    "id": "best_value",
                    "label": "Best Value",
                    "description": "Lowest $/sq ft",
                    "count": best_value_count,
                    "filter": {"sort": "value"},
                    "threshold": round(value_threshold, 2),
                    "icon": "dollar"
                },
                {
                    "id": "new_this_week",
                    "label": "New This Week",
                    "description": "Added in last 7 days",
                    "count": new_count,
                    "filter": {"new": True},
                    "icon": "sparkle"
                },
                {
                    "id": "luxury",
                    "label": "Luxury Picks",
                    "description": "$5,000+/month",
                    "count": luxury_count,
                    "filter": {"min_rent": 5000},
                    "icon": "crown"
                },
                {
                    "id": "studios",
                    "label": "Studios",
                    "description": "Perfect for singles",
                    "count": studio_count,
                    "filter": {"bedrooms": 0},
                    "icon": "bed"
                },
                {
                    "id": "budget",
                    "label": "Budget Friendly",
                    "description": "Under $3,000/month",
                    "count": budget_count,
                    "filter": {"max_rent": 3000},
                    "icon": "piggy"
                },
                {
                    "id": "family",
                    "label": "Family Size",
                    "description": "2+ bedrooms",
                    "count": family_count,
                    "filter": {"min_bedrooms": 2},
                    "icon": "users"
                }
            ],
            "total_available": total_available,
            "generated_at": today.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return {"recommendations": [], "total_available": 0, "error": str(e)}



@api_router.get("/units/hero-carousel")
async def get_hero_carousel_units(limit: int = Query(5, le=10)):
    """Get 5 best interior units for hero carousel - prioritizes units with quality images"""
    try:
        # Get units with images, sorted by is_featured first then by number of images
        pipeline = [
            {'$match': {'is_available': True, 'images': {'$exists': True, '$ne': []}}},
            {'$addFields': {'image_count': {'$size': '$images'}}},
            {'$sort': {'is_featured': -1, 'image_count': -1, 'created_at': -1}},
            {'$limit': limit * 3},  # Get more to ensure variety
            {'$project': {'_id': 0}}
        ]
        
        all_units = await db.units.aggregate(pipeline).to_list(limit * 3)
        
        # Select units ensuring variety - one per building
        seen_buildings = set()
        selected_units = []
        
        for unit in all_units:
            building_id = unit.get('building_id')
            if building_id in seen_buildings:
                continue
            seen_buildings.add(building_id)
            selected_units.append(unit)
            if len(selected_units) >= limit:
                break
        
        # Enrich with building data
        enriched_units = []
        for unit in selected_units:
            building = await db.buildings.find_one({'id': unit.get('building_id')}, {"_id": 0})
            unit['building'] = building
            enriched_units.append(unit)
        
        return enriched_units
    except Exception as e:
        logger.error(f"Error getting hero carousel units: {e}")
        return []


@api_router.get("/units/recent")
async def get_recent_units(limit: int = Query(6, le=20)):
    """Get most recently added units with variety - max one unit per building"""
    try:
        # Get more units than needed to ensure variety
        all_units = await db.units.find(
            {'is_available': True},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit * 5).to_list(limit * 5)
        
        # Select units ensuring variety - one per building
        seen_buildings = set()
        selected_units = []
        
        for unit in all_units:
            building_id = unit.get('building_id')
            
            # Skip if we already have a unit from this building
            if building_id in seen_buildings:
                continue
            
            seen_buildings.add(building_id)
            selected_units.append(unit)
            
            # Stop when we have enough
            if len(selected_units) >= limit:
                break
        
        # If we don't have enough unique buildings, fill with remaining units
        if len(selected_units) < limit:
            for unit in all_units:
                if unit not in selected_units:
                    selected_units.append(unit)
                    if len(selected_units) >= limit:
                        break
        
        # Enrich with building data
        enriched_units = []
        for unit in selected_units:
            building = await db.buildings.find_one({'id': unit.get('building_id')}, {"_id": 0})
            unit['building'] = building
            enriched_units.append(unit)
        
        return enriched_units
    except Exception as e:
        logger.error(f"Error getting recent units: {e}")
        return []



@api_router.get("/units/{unit_id}")
async def get_unit(unit_id: str):
    """Get unit by ID"""
    unit = await db.units.find_one({'id': unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Get building info
    building = await db.buildings.find_one({'id': unit['building_id']}, {"_id": 0})
    unit['building'] = building
    
    if isinstance(unit.get('created_at'), str):
        unit['created_at'] = datetime.fromisoformat(unit['created_at'])
    if isinstance(unit.get('updated_at'), str):
        unit['updated_at'] = datetime.fromisoformat(unit['updated_at'])
    
    return unit

@api_router.get("/share/{unit_id}", response_class=HTMLResponse)
async def get_share_preview(unit_id: str):
    """Generate HTML page with Open Graph meta tags for social sharing.
    Facebook, LinkedIn, and other crawlers will scrape this page to get the preview."""
    unit = await db.units.find_one({'id': unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    building = await db.buildings.find_one({'id': unit['building_id']}, {"_id": 0})
    
    # Generate content
    bedrooms = unit.get('bedrooms', 0)
    bedroom_text = 'Studio' if bedrooms == 0 else f'{bedrooms} Bedroom' if bedrooms == 1 else f'{bedrooms} Bedrooms'
    rent = unit.get('rent', 0)
    neighborhood = building.get('neighborhood', '') if building else ''
    city = building.get('city', 'NYC') if building else 'NYC'
    building_name = building.get('name', '') if building else ''
    
    # Get first image or use default
    images = unit.get('images', [])
    image_url = images[0] if images else 'https://static.prod-images.emergentagent.com/jobs/809a99b2-794a-4bcc-9110-b50857b9c814/images/669505f9b273977a606a8fe480082945aab2c6997e18616eb33fb32a2c5e4eb9.png'
    
    title = f"{bedroom_text} at {building_name or neighborhood} - ${rent:,}/mo | No Fee"
    description = f"No broker fee {bedroom_text.lower()} apartment for rent in {neighborhood}, {city}. ${rent:,}/month. Save thousands on broker fees! View on NoFeesApts.com"
    canonical_url = f"https://nofeesapts.com/unit/{unit_id}"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:site_name" content="NoFeesApts.com">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{canonical_url}">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image_url}">
    
    <!-- Redirect to actual listing -->
    <meta http-equiv="refresh" content="0;url={canonical_url}">
    <link rel="canonical" href="{canonical_url}">
</head>
<body>
    <p>Redirecting to <a href="{canonical_url}">{title}</a>...</p>
</body>
</html>"""
    
    return HTMLResponse(content=html)

@api_router.post("/units", response_model=Unit)
async def create_unit(input: UnitInput, user: User = Depends(require_admin)):
    """Create unit (admin only)"""
    # Check building exists
    building = await db.buildings.find_one({'id': input.building_id})
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    unit = Unit(**input.model_dump())
    unit_dict = unit.model_dump()
    unit_dict['created_at'] = unit_dict['created_at'].isoformat()
    unit_dict['updated_at'] = unit_dict['updated_at'].isoformat()
    await db.units.insert_one(unit_dict)
    return unit

@api_router.put("/units/{unit_id}", response_model=Unit)
async def update_unit(unit_id: str, input: UnitInput, user: User = Depends(require_admin)):
    """Update unit (admin only) - tracks price changes automatically"""
    existing = await db.units.find_one({'id': unit_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    old_rent = existing.get('rent', 0)
    new_rent = input.rent
    old_available = existing.get('is_available', True)
    new_available = input.is_available
    
    update_data = input.model_dump()
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Track price changes if rent changed
    if old_rent != new_rent and LIFECYCLE_SERVICE_AVAILABLE:
        service = get_lifecycle_service(db)
        await service._record_price_change(
            unit_id=unit_id,
            old_price=old_rent,
            new_price=new_rent,
            source='admin_update',
            changed_by=user.id
        )
        # Clear stale status if price was updated
        if existing.get('lifecycle_status') == 'stale':
            update_data['lifecycle_status'] = 'available'
            update_data['stale_since'] = None
    
    # Track availability/status changes
    if old_available != new_available and LIFECYCLE_SERVICE_AVAILABLE:
        service = get_lifecycle_service(db)
        old_status = existing.get('lifecycle_status', 'available')
        # If marked as not available, it could be rented or unavailable
        if not new_available:
            new_status = 'rented' if 'rented' in (input.description or '').lower() else 'unavailable'
        else:
            new_status = 'available'
        
        await service._record_status_change(
            unit_id=unit_id,
            old_status=old_status,
            new_status=new_status,
            source='admin_update',
            changed_by=user.id
        )
        update_data['lifecycle_status'] = new_status
        update_data['lifecycle_updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.units.update_one({'id': unit_id}, {'$set': update_data})
    
    updated = await db.units.find_one({'id': unit_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return updated

@api_router.patch("/units/{unit_id}/images")
async def update_unit_images(unit_id: str, images: List[str], user: User = Depends(require_admin)):
    """Update unit images only (admin only)"""
    existing = await db.units.find_one({'id': unit_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    await db.units.update_one(
        {'id': unit_id}, 
        {'$set': {'images': images, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'message': 'Images updated', 'unit_id': unit_id, 'image_count': len(images)}

@api_router.delete("/units/{unit_id}")
async def delete_unit(unit_id: str, user: User = Depends(require_admin)):
    """Delete unit (admin only)"""
    result = await db.units.delete_one({'id': unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {'message': 'Unit deleted'}

# ============ FAVORITES ROUTES ============

@api_router.get("/favorites")
async def get_favorites(user: User = Depends(require_auth)):
    """Get user's favorite units"""
    favorites = await db.favorites.find({'user_id': user.id}, {"_id": 0}).to_list(1000)
    
    # Get unit details - optimized to avoid N+1 queries
    result = []
    if favorites:
        # Batch fetch units
        unit_ids = [f['unit_id'] for f in favorites]
        units = await db.units.find({'id': {'$in': unit_ids}}, {"_id": 0}).to_list(len(unit_ids))
        units_map = {u['id']: u for u in units}
        
        # Batch fetch buildings
        building_ids = list(set(u['building_id'] for u in units if u.get('building_id')))
        buildings = await db.buildings.find({'id': {'$in': building_ids}}, {"_id": 0}).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
        
        # Combine results
        for fav in favorites:
            unit = units_map.get(fav['unit_id'])
            if unit:
                unit['building'] = buildings_map.get(unit['building_id'])
                result.append({
                    'favorite_id': fav['id'],
                    'unit': unit
                })
    
    return result

@api_router.post("/favorites/{unit_id}")
async def add_favorite(unit_id: str, user: User = Depends(require_auth)):
    """Add unit to favorites"""
    # Check unit exists
    unit = await db.units.find_one({'id': unit_id})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Check if already favorited
    existing = await db.favorites.find_one({'user_id': user.id, 'unit_id': unit_id})
    if existing:
        return {'message': 'Already favorited'}
    
    favorite = Favorite(user_id=user.id, unit_id=unit_id)
    fav_dict = favorite.model_dump()
    fav_dict['created_at'] = fav_dict['created_at'].isoformat()
    await db.favorites.insert_one(fav_dict)
    
    return {'message': 'Added to favorites'}

@api_router.delete("/favorites/{unit_id}")
async def remove_favorite(unit_id: str, user: User = Depends(require_auth)):
    """Remove unit from favorites"""
    result = await db.favorites.delete_one({'user_id': user.id, 'unit_id': unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {'message': 'Removed from favorites'}

# ============ SAVED SEARCHES ROUTES ============

@api_router.get("/saved-searches")
async def get_saved_searches(user: User = Depends(require_auth)):
    """Get user's saved searches"""
    searches = await db.saved_searches.find(
        {'user_id': user.id},
        {"_id": 0}
    ).sort('created_at', -1).to_list(100)
    return searches

@api_router.post("/saved-searches")
async def create_saved_search(input: SavedSearchInput, user: User = Depends(require_auth)):
    """Create a new saved search for email/SMS alerts"""
    # Check if user already has a similar search
    existing_count = await db.saved_searches.count_documents({'user_id': user.id})
    if existing_count >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 saved searches allowed")
    
    # Validate SMS request
    if input.notify_sms and not input.phone_number:
        raise HTTPException(status_code=400, detail="Phone number required for SMS alerts")
    
    if input.notify_sms and not SMS_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="SMS service not available")
    
    saved_search = SavedSearch(
        user_id=user.id,
        user_email=user.email,
        user_phone=input.phone_number,
        name=input.name,
        bedrooms=input.bedrooms,
        min_rent=input.min_rent,
        max_rent=input.max_rent,
        bathrooms=input.bathrooms,
        state=input.state,
        neighborhood=input.neighborhood,
        alert_frequency=input.alert_frequency,
        notify_email=input.notify_email,
        notify_sms=input.notify_sms
    )
    
    search_dict = saved_search.model_dump()
    search_dict['created_at'] = search_dict['created_at'].isoformat()
    search_dict['updated_at'] = search_dict['updated_at'].isoformat()
    await db.saved_searches.insert_one(search_dict)
    
    # Update user's phone if provided and not already set
    if input.phone_number:
        await db.users.update_one(
            {'id': user.id, 'phone_number': {'$exists': False}},
            {'$set': {'phone_number': input.phone_number}}
        )
    
    logger.info(f"Saved search created for user {user.email}: {input.name} (email={input.notify_email}, sms={input.notify_sms})")
    
    alert_types = []
    if input.notify_email:
        alert_types.append("email")
    if input.notify_sms:
        alert_types.append("SMS")
    alert_text = " and ".join(alert_types) if alert_types else "email"
    
    return {
        'message': f'Search saved! You will receive {alert_text} alerts for matching listings.',
        'search': {
            'id': saved_search.id,
            'name': saved_search.name,
            'alert_frequency': saved_search.alert_frequency,
            'notify_email': saved_search.notify_email,
            'notify_sms': saved_search.notify_sms
        }
    }

@api_router.put("/saved-searches/{search_id}")
async def update_saved_search(search_id: str, input: SavedSearchInput, user: User = Depends(require_auth)):
    """Update a saved search"""
    existing = await db.saved_searches.find_one({'id': search_id, 'user_id': user.id})
    if not existing:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    update_data = input.model_dump()
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.saved_searches.update_one(
        {'id': search_id},
        {'$set': update_data}
    )
    
    return {'message': 'Saved search updated'}

@api_router.delete("/saved-searches/{search_id}")
async def delete_saved_search(search_id: str, user: User = Depends(require_auth)):
    """Delete a saved search"""
    result = await db.saved_searches.delete_one({'id': search_id, 'user_id': user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saved search not found")
    return {'message': 'Saved search deleted'}

@api_router.put("/saved-searches/{search_id}/toggle")
async def toggle_saved_search(search_id: str, user: User = Depends(require_auth)):
    """Toggle saved search active/inactive"""
    existing = await db.saved_searches.find_one({'id': search_id, 'user_id': user.id})
    if not existing:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    new_active = not existing.get('is_active', True)
    await db.saved_searches.update_one(
        {'id': search_id},
        {'$set': {'is_active': new_active, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'message': f'Search alerts {"enabled" if new_active else "disabled"}', 'is_active': new_active}

@api_router.post("/admin/trigger-search-alerts")
async def trigger_search_alerts(user: User = Depends(require_admin)):
    """Manually trigger saved search alerts (admin only)"""
    try:
        alerts_sent = await process_saved_search_alerts()
        return {
            'message': f'Saved search alerts processed. {alerts_sent} alerts sent.',
            'alerts_sent': alerts_sent
        }
    except Exception as e:
        logger.error(f"Error triggering search alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ SOCIAL PROOF ROUTES ============

@api_router.get("/social-proof")
async def get_social_proof():
    """Get social proof data for landing page"""
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        
        # Count users who signed up today
        signups_today = await db.users.count_documents({
            'created_at': {'$gte': today_start.isoformat()}
        })
        
        # Count users who signed up this week
        signups_this_week = await db.users.count_documents({
            'created_at': {'$gte': week_ago.isoformat()}
        })
        
        # Total users
        total_users = await db.users.count_documents({})
        
        # Recent inquiries (contact requests)
        inquiries_today = await db.contact_requests.count_documents({
            'created_at': {'$gte': today_start.isoformat()}
        })
        
        # Active saved searches
        active_searches = await db.saved_searches.count_documents({'is_active': True})
        
        # Total units
        total_units = await db.units.count_documents({'is_available': True})
        
        # Total subscribers
        total_subscribers = await db.email_subscribers.count_documents({'active': True})
        
        return {
            'signups_today': signups_today,
            'signups_this_week': signups_this_week,
            'total_users': total_users,
            'inquiries_today': inquiries_today,
            'active_searches': active_searches,
            'total_units': total_units,
            'total_subscribers': total_subscribers,
            'generated_at': now.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting social proof data: {e}")
        return {
            'signups_today': 0,
            'signups_this_week': 0,
            'total_users': 0,
            'inquiries_today': 0,
            'active_searches': 0,
            'total_units': 180,
            'total_subscribers': 0
        }

# ============ CALENDAR & VIEWING ROUTES ============

@api_router.get("/calendar/status")
async def get_calendar_status(user: User = Depends(require_auth)):
    """Check if user has connected Google Calendar"""
    user_doc = await db.users.find_one({'id': user.id})
    has_calendar = bool(user_doc and user_doc.get('google_calendar_tokens'))
    
    return {
        'connected': has_calendar,
        'calendar_enabled': CALENDAR_SERVICE_AVAILABLE
    }

@api_router.get("/calendar/connect")
async def connect_calendar(request: Request, user: User = Depends(require_auth)):
    """Initiate Google Calendar OAuth flow"""
    if not CALENDAR_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Calendar service not configured")
    
    # Get the base URL from request
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/oauth/calendar/callback"
    
    auth_url = get_oauth_authorization_url(
        redirect_uri=redirect_uri,
        state=user.id  # Pass user ID as state for callback
    )
    
    if not auth_url:
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")
    
    return {'authorization_url': auth_url}

@api_router.get("/oauth/calendar/callback")
async def calendar_oauth_callback(code: str, state: str, request: Request):
    """Handle Google Calendar OAuth callback"""
    if not CALENDAR_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Calendar service not configured")
    
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/oauth/calendar/callback"
    
    # Exchange code for tokens
    tokens = exchange_code_for_tokens(code, redirect_uri)
    if not tokens:
        # Redirect to frontend with error
        frontend_url = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')
        return RedirectResponse(f"{frontend_url}/dashboard?calendar_error=auth_failed")
    
    # Get user email from token to verify
    token_email = get_user_email_from_token(tokens.get('access_token'))
    
    # State contains user ID
    user_id = state
    
    # Store tokens in user document
    await db.users.update_one(
        {'id': user_id},
        {
            '$set': {
                'google_calendar_tokens': tokens,
                'google_calendar_email': token_email,
                'google_calendar_connected_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    logger.info(f"Google Calendar connected for user {user_id}")
    
    # Redirect to frontend with success
    frontend_url = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')
    return RedirectResponse(f"{frontend_url}/dashboard?calendar_connected=true")

@api_router.delete("/calendar/disconnect")
async def disconnect_calendar(user: User = Depends(require_auth)):
    """Disconnect Google Calendar"""
    await db.users.update_one(
        {'id': user.id},
        {
            '$unset': {
                'google_calendar_tokens': '',
                'google_calendar_email': '',
                'google_calendar_connected_at': ''
            }
        }
    )
    
    return {'message': 'Calendar disconnected'}

@api_router.post("/viewings/schedule")
async def schedule_viewing(
    input: ScheduleViewingInput,
    user: User = Depends(require_auth)
):
    """Schedule an apartment viewing and add to calendar"""
    # Get unit and building info
    unit = await db.units.find_one({'id': input.unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    building = await db.buildings.find_one({'id': unit.get('building_id')}, {"_id": 0})
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Parse viewing datetime
    try:
        viewing_datetime = datetime.fromisoformat(f"{input.viewing_date}T{input.viewing_time}:00")
        viewing_datetime = viewing_datetime.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date/time format")
    
    # Create viewing record
    viewing = {
        'id': str(uuid.uuid4()),
        'user_id': user.id,
        'user_email': user.email,
        'unit_id': input.unit_id,
        'building_id': building.get('id'),
        'building_name': building.get('name'),
        'unit_number': unit.get('unit_number'),
        'address': building.get('address'),
        'viewing_datetime': viewing_datetime.isoformat(),
        'notes': input.notes,
        'status': 'scheduled',
        'calendar_event_id': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Try to add to Google Calendar if connected
    user_doc = await db.users.find_one({'id': user.id})
    calendar_tokens = user_doc.get('google_calendar_tokens') if user_doc else None
    
    if calendar_tokens and CALENDAR_SERVICE_AVAILABLE:
        event_result = create_viewing_event(
            tokens=calendar_tokens,
            building_name=building.get('name'),
            unit_number=unit.get('unit_number', 'N/A'),
            address=building.get('address', ''),
            viewing_datetime=viewing_datetime,
            notes=input.notes
        )
        
        if event_result:
            viewing['calendar_event_id'] = event_result.get('id')
            viewing['calendar_event_link'] = event_result.get('htmlLink')
            
            # Update tokens if refreshed
            if event_result.get('updated_tokens'):
                await db.users.update_one(
                    {'id': user.id},
                    {'$set': {'google_calendar_tokens': event_result['updated_tokens']}}
                )
    
    # Save viewing to database
    await db.viewings.insert_one(viewing)
    
    # Send SMS confirmation if user has phone
    if SMS_SERVICE_AVAILABLE and user_doc.get('phone_number'):
        send_viewing_confirmation_sms(
            phone_number=user_doc['phone_number'],
            building_name=building.get('name'),
            unit_number=unit.get('unit_number', 'N/A'),
            viewing_date=input.viewing_date,
            viewing_time=input.viewing_time
        )
    
    logger.info(f"Viewing scheduled for user {user.email}: {building.get('name')} on {input.viewing_date}")
    
    return {
        'message': 'Viewing scheduled successfully',
        'viewing': {
            'id': viewing['id'],
            'building_name': viewing['building_name'],
            'unit_number': viewing['unit_number'],
            'viewing_datetime': viewing['viewing_datetime'],
            'calendar_added': bool(viewing.get('calendar_event_id')),
            'calendar_link': viewing.get('calendar_event_link')
        }
    }

@api_router.get("/viewings")
async def get_user_viewings(user: User = Depends(require_auth)):
    """Get user's scheduled viewings"""
    viewings = await db.viewings.find(
        {'user_id': user.id},
        {"_id": 0}
    ).sort('viewing_datetime', 1).to_list(100)
    
    return viewings

@api_router.delete("/viewings/{viewing_id}")
async def cancel_viewing(viewing_id: str, user: User = Depends(require_auth)):
    """Cancel a scheduled viewing"""
    viewing = await db.viewings.find_one({'id': viewing_id, 'user_id': user.id})
    if not viewing:
        raise HTTPException(status_code=404, detail="Viewing not found")
    
    # Delete from Google Calendar if connected
    if viewing.get('calendar_event_id'):
        user_doc = await db.users.find_one({'id': user.id})
        calendar_tokens = user_doc.get('google_calendar_tokens') if user_doc else None
        
        if calendar_tokens and CALENDAR_SERVICE_AVAILABLE:
            delete_viewing_event(calendar_tokens, viewing['calendar_event_id'])
    
    # Delete viewing record
    await db.viewings.delete_one({'id': viewing_id})
    
    return {'message': 'Viewing cancelled'}

@api_router.get("/services/status")
async def get_services_status():
    """Get status of external services"""
    return {
        'email_service': EMAIL_SERVICE_AVAILABLE,
        'sms_service': SMS_SERVICE_AVAILABLE,
        'calendar_service': CALENDAR_SERVICE_AVAILABLE
    }

# ============ CONTACT ROUTES ============

@api_router.post("/contact")
async def contact_about_unit(
    input: ContactInput, 
    background_tasks: BackgroundTasks,
    user: User = Depends(require_auth)
):
    """Submit contact request for a unit and send email notification"""
    # Check unit exists
    unit = await db.units.find_one({'id': input.unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Get building info for better email context
    building = None
    if unit.get('building_id'):
        building = await db.buildings.find_one(
            {'id': unit['building_id']}, 
            {"_id": 0}
        )
    
    # Create contact request record
    contact = ContactRequest(
        user_id=user.id,
        **input.model_dump()
    )
    contact_dict = contact.model_dump()
    contact_dict['created_at'] = contact_dict['created_at'].isoformat()
    await db.contact_requests.insert_one(contact_dict)
    
    # Send email notifications in background
    if EMAIL_SERVICE_AVAILABLE:
        building_name = building.get('name', 'Unknown Building') if building else 'Unknown Building'
        building_address = building.get('address', 'N/A') if building else 'N/A'
        unit_number = unit.get('unit_number', 'N/A')
        rent = unit.get('rent', 0)
        bedrooms = unit.get('bedrooms', 0)
        bathrooms = unit.get('bathrooms', 0)
        
        # Send notification to admin
        background_tasks.add_task(
            smtp_service.send_inquiry_notification,
            admin_email='placesfirm@gmail.com',
            user_name=input.name,
            user_email=input.email,
            user_phone=input.phone,
            message=input.message,
            building_name=building_name,
            building_address=building_address,
            unit_number=unit_number,
            rent=rent,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            preferred_date=input.preferred_date,
            preferred_time=input.preferred_time,
            alternative_date=input.alternative_date,
            alternative_time=input.alternative_time
        )
        
        # Send confirmation to user
        background_tasks.add_task(
            smtp_service.send_inquiry_confirmation,
            user_email=input.email,
            user_name=input.name,
            message=input.message,
            building_name=building_name,
            building_address=building_address,
            unit_number=unit_number,
            rent=rent,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            preferred_date=input.preferred_date,
            preferred_time=input.preferred_time,
            alternative_date=input.alternative_date,
            alternative_time=input.alternative_time
        )
        
        logger.info(f"Email notifications queued for contact request from {input.email}")
    else:
        logger.warning("Email service not available - notification not sent")
    
    return {
        'message': 'Contact request submitted',
        'email_sent': EMAIL_SERVICE_AVAILABLE
    }

@api_router.get("/contact")
async def get_contact_requests(user: User = Depends(require_admin)):
    """Get all contact requests (admin only)"""
    contacts = await db.contact_requests.find({}, {"_id": 0}).sort('created_at', -1).to_list(1000)
    return contacts

@api_router.post("/subscribe")
async def subscribe_email(input: EmailSubscribeInput):
    """Subscribe email for apartment alerts"""
    try:
        # Check if email already exists
        existing = await db.email_subscribers.find_one({'email': input.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already subscribed")
        
        # Add new subscriber
        subscriber = {
            'id': str(uuid.uuid4()),
            'email': input.email,
            'subscribed_at': datetime.now(timezone.utc).isoformat(),
            'active': True,
            'source': 'landing_page'
        }
        
        await db.email_subscribers.insert_one(subscriber)
        
        logger.info(f"New email subscriber: {input.email}")
        
        # Send welcome email
        try:
            from smtp_email_service import send_welcome_subscriber_email
            await send_welcome_subscriber_email(input.email)
            logger.info(f"Welcome email sent to: {input.email}")
        except Exception as email_error:
            logger.error(f"Failed to send welcome email: {str(email_error)}")
            # Don't fail the subscription if email fails
        
        return {'success': True, 'message': 'Successfully subscribed!'}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")

@api_router.post("/share-unit")
async def share_unit(input: ShareUnitInput, user: User = Depends(require_auth)):
    """Share apartment unit via email using SMTP"""
    # Get unit details
    unit = await db.units.find_one({'id': input.unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Get building info
    building = None
    if unit.get('building_id'):
        building = await db.buildings.find_one({'id': unit['building_id']}, {"_id": 0})
    
    # Send share email using SMTP
    try:
        # Prepare unit details
        building_name = building.get('name', 'NYC Apartment') if building else 'NYC Apartment'
        address = building.get('address', '') if building else ''
        neighborhood = building.get('neighborhood', '') if building else ''
        unit_number = unit.get('unit_number', '')
        bedrooms = 'Studio' if unit.get('bedrooms', 0) == 0 else f"{unit.get('bedrooms')} Bedroom"
        bathrooms = unit.get('bathrooms', 0)
        rent = unit.get('rent', 0)
        # Use environment variable for frontend URL
        frontend_url = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')
        unit_url = f"{frontend_url}/unit/{unit['id']}"
        
        # Get first image
        image_url = unit.get('images', [])[0] if unit.get('images') else None
        
        # Create HTML email
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 30px; border: 1px solid #e0e0e0; }}
        .apartment-card {{ background: white; border-radius: 10px; overflow: hidden; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .apartment-image {{ width: 100%; height: 300px; object-fit: cover; }}
        .apartment-details {{ padding: 20px; }}
        .price {{ font-size: 32px; font-weight: bold; color: #f59e0b; margin: 10px 0; }}
        .badge {{ display: inline-block; background: #ef4444; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .details {{ display: flex; gap: 20px; margin: 15px 0; }}
        .detail-item {{ font-size: 16px; color: #666; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }}
        .message {{ background: #fff3cd; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">🏢 NoFeesApts.com</h1>
            <p style="margin: 10px 0 0 0;">Your friend shared an apartment with you!</p>
        </div>
        
        <div class="content">
            <p>Hi there!</p>
            <p><strong>{user.name or user.email}</strong> thought you might be interested in this no-fee apartment:</p>
            
            {f'<div class="message"><p>{input.message}</p></div>' if input.message else ''}
            
            <div class="apartment-card">
                {f'<img src="{image_url}" alt="Apartment" class="apartment-image" />' if image_url else ''}
                <div class="apartment-details">
                    <span class="badge">NO FEE</span>
                    <h2 style="margin: 10px 0; color: #1f2937;">{building_name}</h2>
                    <p style="color: #666; margin: 5px 0;">{address}</p>
                    {f'<p style="color: #666; margin: 5px 0;">{neighborhood}</p>' if neighborhood else ''}
                    
                    <div class="price">${rent:,}/month</div>
                    
                    <div class="details">
                        <span class="detail-item">🛏️ {bedrooms}</span>
                        <span class="detail-item">🚿 {bathrooms} Bath</span>
                        {f'<span class="detail-item">📍 Unit {unit_number}</span>' if unit_number else ''}
                    </div>
                    
                    <p style="margin: 20px 0 10px 0; font-weight: bold;">Why This is Special:</p>
                    <ul style="color: #666; margin: 0; padding-left: 20px;">
                        <li>✨ NO BROKER FEES - Save thousands!</li>
                        <li>🏙️ Prime {neighborhood if neighborhood else 'NYC'} location</li>
                        <li>📸 Real photos, not stock images</li>
                        <li>⚡ Move-in ready</li>
                    </ul>
                </div>
            </div>
            
            <div style="text-align: center;">
                <a href="{unit_url}" class="cta-button">View Full Details →</a>
            </div>
            
            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                Browse more no-fee apartments in NYC and Northern New Jersey at <a href="{frontend_url}" style="color: #f59e0b;">NoFeesApts.com</a>
            </p>
        </div>
        
        <div class="footer">
            This email was sent because {user.name or user.email} shared an apartment with you from NoFeesApts.com<br>
            © 2025 NoFeesApts.com • No Broker Fees Ever
        </div>
    </div>
</body>
</html>
        """
        
        # Use SMTP service to send email
        subject = f"Check out this {bedrooms} apartment at {building_name} - No Broker Fees!"
        email_sent = smtp_service.send_email(
            to_email=input.recipient_email,
            subject=subject,
            body_html=html_content,
            reply_to=user.email
        )
        
        if email_sent:
            logger.info(f"Unit {unit['id']} shared by {user.email} to {input.recipient_email}")
            return {'message': 'Apartment shared successfully!'}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share unit: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

# ============ ADMIN ROUTES ============

# ============ STAGING COLLECTIONS ROUTES ============

@api_router.get("/admin/staging/buildings")
async def get_staging_buildings(
    status: Optional[str] = Query(None, description="Filter by review_status: pending, approved, rejected"),
    batch_id: Optional[str] = Query(None, description="Filter by crawler_batch_id"),
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """Get all buildings in staging collection"""
    query = {}
    if status:
        query["review_status"] = status
    if batch_id:
        query["crawler_batch_id"] = batch_id
    
    buildings = await db.buildings_staging.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.buildings_staging.count_documents(query)
    
    return {
        "items": buildings,
        "total": total,
        "pending": await db.buildings_staging.count_documents({"review_status": "pending"}),
        "approved": await db.buildings_staging.count_documents({"review_status": "approved"}),
        "rejected": await db.buildings_staging.count_documents({"review_status": "rejected"})
    }

@api_router.get("/admin/staging/buildings/{building_id}")
async def get_staging_building(building_id: str, user: User = Depends(require_admin)):
    """Get a specific staging building by ID"""
    building = await db.buildings_staging.find_one({"id": building_id}, {"_id": 0})
    if not building:
        raise HTTPException(status_code=404, detail="Staging building not found")
    return building

@api_router.post("/admin/staging/buildings")
async def create_staging_building(
    building_input: BuildingStagingInput,
    user: User = Depends(require_admin)
):
    """Create a new building in staging"""
    building = BuildingStaging(
        name=building_input.name,
        address=building_input.address,
        neighborhood=building_input.neighborhood,
        city=building_input.city,
        state=building_input.state,
        zip_code=building_input.zip_code,
        source_url=building_input.source_url,
        latitude=building_input.latitude,
        longitude=building_input.longitude,
        crawler_source=building_input.crawler_source,
        crawler_batch_id=building_input.crawler_batch_id,
        validation_flags=building_input.validation_flags,
        duplicate_score=building_input.duplicate_score
    )
    
    await db.buildings_staging.insert_one(building.model_dump())
    return {"id": building.id, "message": "Staging building created"}

@api_router.put("/admin/staging/buildings/{building_id}/review")
async def review_staging_building(
    building_id: str,
    review: StagingReviewInput,
    user: User = Depends(require_admin)
):
    """Review a staging building (approve/reject)"""
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="review_status must be 'approved' or 'rejected'")
    
    result = await db.buildings_staging.update_one(
        {"id": building_id},
        {
            "$set": {
                "review_status": review.review_status,
                "reviewer_notes": review.reviewer_notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staging building not found")
    
    return {"message": f"Building {review.review_status}", "id": building_id}

@api_router.post("/admin/staging/buildings/{building_id}/promote")
async def promote_staging_building(
    building_id: str,
    user: User = Depends(require_admin)
):
    """Promote an approved staging building to production"""
    staging_building = await db.buildings_staging.find_one({"id": building_id}, {"_id": 0})
    if not staging_building:
        raise HTTPException(status_code=404, detail="Staging building not found")
    
    if staging_building.get("review_status") != "approved":
        raise HTTPException(status_code=400, detail="Building must be approved before promotion")
    
    # Create production building (exclude staging-specific fields)
    production_building = {
        "id": str(uuid.uuid4()),
        "name": staging_building["name"],
        "address": staging_building["address"],
        "neighborhood": staging_building["neighborhood"],
        "city": staging_building["city"],
        "state": staging_building["state"],
        "zip_code": staging_building["zip_code"],
        "source_url": staging_building["source_url"],
        "latitude": staging_building.get("latitude"),
        "longitude": staging_building.get("longitude"),
        "last_crawled": staging_building.get("last_crawled"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.buildings.insert_one(production_building)
    
    # Mark staging as promoted
    await db.buildings_staging.update_one(
        {"id": building_id},
        {"$set": {"review_status": "promoted", "matched_production_id": production_building["id"]}}
    )
    
    return {
        "message": "Building promoted to production",
        "staging_id": building_id,
        "production_id": production_building["id"]
    }

@api_router.delete("/admin/staging/buildings/{building_id}")
async def delete_staging_building(building_id: str, user: User = Depends(require_admin)):
    """Delete a staging building"""
    result = await db.buildings_staging.delete_one({"id": building_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staging building not found")
    return {"message": "Staging building deleted"}

# Units Staging Routes

@api_router.get("/admin/staging/units")
async def get_staging_units(
    status: Optional[str] = Query(None, description="Filter by review_status: pending, approved, rejected"),
    batch_id: Optional[str] = Query(None, description="Filter by crawler_batch_id"),
    building_id: Optional[str] = Query(None, description="Filter by building_id"),
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """Get all units in staging collection"""
    query = {}
    if status:
        query["review_status"] = status
    if batch_id:
        query["crawler_batch_id"] = batch_id
    if building_id:
        query["building_id"] = building_id
    
    units = await db.units_staging.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.units_staging.count_documents(query)
    
    return {
        "items": units,
        "total": total,
        "pending": await db.units_staging.count_documents({"review_status": "pending"}),
        "approved": await db.units_staging.count_documents({"review_status": "approved"}),
        "rejected": await db.units_staging.count_documents({"review_status": "rejected"})
    }

@api_router.get("/admin/staging/units/{unit_id}")
async def get_staging_unit(unit_id: str, user: User = Depends(require_admin)):
    """Get a specific staging unit by ID"""
    unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    return unit

@api_router.post("/admin/staging/units")
async def create_staging_unit(
    unit_input: UnitStagingInput,
    user: User = Depends(require_admin)
):
    """Create a new unit in staging"""
    unit = UnitStaging(
        building_id=unit_input.building_id,
        unit_number=unit_input.unit_number,
        rent=unit_input.rent,
        bedrooms=unit_input.bedrooms,
        bathrooms=unit_input.bathrooms,
        square_feet=unit_input.square_feet,
        available_date=unit_input.available_date,
        amenities=unit_input.amenities,
        images=unit_input.images,
        description=unit_input.description,
        is_available=unit_input.is_available,
        crawler_source=unit_input.crawler_source,
        crawler_batch_id=unit_input.crawler_batch_id,
        validation_flags=unit_input.validation_flags,
        duplicate_score=unit_input.duplicate_score
    )
    
    await db.units_staging.insert_one(unit.model_dump())
    return {"id": unit.id, "message": "Staging unit created"}

@api_router.put("/admin/staging/units/{unit_id}/review")
async def review_staging_unit(
    unit_id: str,
    review: StagingReviewInput,
    user: User = Depends(require_admin)
):
    """Review a staging unit (approve/reject)"""
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="review_status must be 'approved' or 'rejected'")
    
    result = await db.units_staging.update_one(
        {"id": unit_id},
        {
            "$set": {
                "review_status": review.review_status,
                "reviewer_notes": review.reviewer_notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    return {"message": f"Unit {review.review_status}", "id": unit_id}

@api_router.put("/admin/staging/units/{unit_id}/edit")
async def edit_staging_unit(
    unit_id: str,
    edit_data: StagingUnitEditInput,
    user: User = Depends(require_admin)
):
    """Edit staging unit details before approval (building, rent, etc.)"""
    # Verify the staging unit exists
    staging_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    # Build update dict with only provided fields
    update_data = {}
    
    if edit_data.building_id is not None:
        # Verify building exists
        building = await db.buildings.find_one({"id": edit_data.building_id}, {"_id": 0})
        if not building:
            raise HTTPException(status_code=400, detail="Invalid building_id - building not found")
        update_data["building_id"] = edit_data.building_id
        update_data["building_name"] = building.get("name")
        update_data["building_address"] = building.get("address")
    
    if edit_data.unit_number is not None:
        update_data["unit_number"] = edit_data.unit_number
        update_data["normalized_unit_number"] = edit_data.unit_number.strip().upper()
    
    if edit_data.rent is not None:
        update_data["rent"] = edit_data.rent
    
    if edit_data.bedrooms is not None:
        update_data["bedrooms"] = edit_data.bedrooms
    
    if edit_data.bathrooms is not None:
        update_data["bathrooms"] = edit_data.bathrooms
    
    if edit_data.square_feet is not None:
        update_data["square_feet"] = edit_data.square_feet
    
    if edit_data.available_date is not None:
        update_data["available_date"] = edit_data.available_date
    
    if edit_data.description is not None:
        update_data["description"] = edit_data.description
    
    if edit_data.images is not None:
        update_data["images"] = edit_data.images
        # Remove no_images flag if images are being added
        if edit_data.images and len(edit_data.images) > 0:
            await db.units_staging.update_one(
                {"id": unit_id},
                {"$pull": {"validation_flags": "no_images"}}
            )
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Add metadata
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["edited_by"] = user.id
    update_data["edited_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.units_staging.update_one(
        {"id": unit_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        return {"message": "No changes made", "id": unit_id}
    
    # Return updated unit
    updated_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    return {"message": "Unit updated", "id": unit_id, "unit": updated_unit}

@api_router.post("/admin/staging/units/{unit_id}/upload-images")
async def upload_staging_unit_images(
    unit_id: str,
    files: List[UploadFile] = File(...),
    user: User = Depends(require_admin)
):
    """Upload images for a staging unit"""
    # Verify unit exists
    staging_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    uploaded_urls = []
    upload_dir = Path(__file__).parent / "uploads" / unit_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        if not file.content_type.startswith("image/"):
            continue
        
        # Generate unique filename
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4().hex[:12]}.{ext}"
        file_path = upload_dir / filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create URL path (relative to backend)
        image_url = f"/api/uploads/{unit_id}/{filename}"
        uploaded_urls.append(image_url)
    
    if not uploaded_urls:
        raise HTTPException(status_code=400, detail="No valid images uploaded")
    
    # Update the staging unit with new images (append to existing)
    existing_images = staging_unit.get("images", []) or []
    all_images = existing_images + uploaded_urls
    
    await db.units_staging.update_one(
        {"id": unit_id},
        {
            "$set": {
                "images": all_images,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$pull": {"validation_flags": "no_images"}
        }
    )
    
    return {
        "message": f"Uploaded {len(uploaded_urls)} images",
        "uploaded_urls": uploaded_urls,
        "total_images": len(all_images)
    }

@api_router.delete("/admin/staging/units/{unit_id}/images")
async def delete_staging_unit_image(
    unit_id: str,
    image_url: str = Query(...),
    user: User = Depends(require_admin)
):
    """Delete a specific image from a staging unit"""
    staging_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    existing_images = staging_unit.get("images", []) or []
    
    if image_url not in existing_images:
        raise HTTPException(status_code=404, detail="Image not found in unit")
    
    # Remove from list
    updated_images = [img for img in existing_images if img != image_url]
    
    # Delete file if it's a local upload
    if image_url.startswith("/api/uploads/"):
        file_path = Path(__file__).parent / "uploads" / image_url.replace("/api/uploads/", "")
        if file_path.exists():
            file_path.unlink()
    
    # Update staging unit
    update_data = {
        "images": updated_images,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Re-add no_images flag if no images left
    if len(updated_images) == 0:
        await db.units_staging.update_one(
            {"id": unit_id},
            {"$addToSet": {"validation_flags": "no_images"}}
        )
    
    await db.units_staging.update_one(
        {"id": unit_id},
        {"$set": update_data}
    )
    
    return {"message": "Image deleted", "remaining_images": len(updated_images)}

@api_router.post("/admin/staging/units/{unit_id}/promote")
async def promote_staging_unit(
    unit_id: str,
    user: User = Depends(require_admin)
):
    """Promote an approved staging unit to production"""
    staging_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    if staging_unit.get("review_status") != "approved":
        raise HTTPException(status_code=400, detail="Unit must be approved before promotion")
    
    # Check if unit already exists in production (same building + unit number)
    existing_unit = await db.units.find_one({
        "building_id": staging_unit["building_id"],
        "unit_number": staging_unit["unit_number"]
    }, {"_id": 0})
    
    if existing_unit:
        # Update existing production unit
        production_id = existing_unit["id"]
        update_data = {
            "rent": staging_unit["rent"],
            "bedrooms": staging_unit["bedrooms"],
            "bathrooms": staging_unit["bathrooms"],
            "square_feet": staging_unit.get("square_feet"),
            "available_date": staging_unit.get("available_date"),
            "amenities": staging_unit.get("amenities", []),
            "images": staging_unit.get("images", []) if staging_unit.get("images") else existing_unit.get("images", []),
            "description": staging_unit.get("description") or existing_unit.get("description"),
            "is_available": staging_unit.get("is_available", True),
            "latitude": staging_unit.get("latitude"),
            "longitude": staging_unit.get("longitude"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.units.update_one({"id": production_id}, {"$set": update_data})
        message = "Unit updated in production (existing unit found)"
    else:
        # Create new production unit
        production_id = str(uuid.uuid4())
        production_unit = {
            "id": production_id,
            "building_id": staging_unit["building_id"],
            "unit_number": staging_unit["unit_number"],
            "rent": staging_unit["rent"],
            "bedrooms": staging_unit["bedrooms"],
            "bathrooms": staging_unit["bathrooms"],
            "square_feet": staging_unit.get("square_feet"),
            "available_date": staging_unit.get("available_date"),
            "amenities": staging_unit.get("amenities", []),
            "images": staging_unit.get("images", []),
            "description": staging_unit.get("description"),
            "is_available": staging_unit.get("is_available", True),
            "is_featured": False,
            "latitude": staging_unit.get("latitude"),
            "longitude": staging_unit.get("longitude"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(production_unit)
        message = "Unit promoted to production (new unit created)"
    
    # Mark staging as promoted
    await db.units_staging.update_one(
        {"id": unit_id},
        {"$set": {"review_status": "promoted", "matched_production_id": production_id}}
    )
    
    return {
        "message": message,
        "staging_id": unit_id,
        "production_id": production_id
    }

@api_router.delete("/admin/staging/units/{unit_id}")
async def delete_staging_unit(unit_id: str, user: User = Depends(require_admin)):
    """Delete a staging unit"""
    result = await db.units_staging.delete_one({"id": unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    return {"message": "Staging unit deleted"}

# Bulk Operations for Staging

@api_router.post("/admin/staging/buildings/bulk-review")
async def bulk_review_staging_buildings(
    review: StagingBulkReviewInput,
    user: User = Depends(require_admin)
):
    """Bulk review multiple staging buildings"""
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="review_status must be 'approved' or 'rejected'")
    
    result = await db.buildings_staging.update_many(
        {"id": {"$in": review.ids}},
        {
            "$set": {
                "review_status": review.review_status,
                "reviewer_notes": review.reviewer_notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": f"{result.modified_count} buildings {review.review_status}",
        "modified_count": result.modified_count
    }

@api_router.post("/admin/staging/units/bulk-review")
async def bulk_review_staging_units(
    review: StagingBulkReviewInput,
    user: User = Depends(require_admin)
):
    """Bulk review multiple staging units"""
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="review_status must be 'approved' or 'rejected'")
    
    result = await db.units_staging.update_many(
        {"id": {"$in": review.ids}},
        {
            "$set": {
                "review_status": review.review_status,
                "reviewer_notes": review.reviewer_notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": f"{result.modified_count} units {review.review_status}",
        "modified_count": result.modified_count
    }

@api_router.get("/admin/staging/stats")
async def get_staging_stats(user: User = Depends(require_admin)):
    """Get staging collections statistics"""
    buildings_pending = await db.buildings_staging.count_documents({"review_status": "pending"})
    buildings_approved = await db.buildings_staging.count_documents({"review_status": "approved"})
    buildings_rejected = await db.buildings_staging.count_documents({"review_status": "rejected"})
    
    units_pending = await db.units_staging.count_documents({"review_status": "pending"})
    units_approved = await db.units_staging.count_documents({"review_status": "approved"})
    units_rejected = await db.units_staging.count_documents({"review_status": "rejected"})
    
    # Get unavailability review stats
    unavail_pending = await db.unavailability_reviews.count_documents({"review_status": "pending"})
    unavail_confirmed = await db.unavailability_reviews.count_documents({"review_status": "confirmed_unavailable"})
    unavail_false_positive = await db.unavailability_reviews.count_documents({"review_status": "false_positive"})
    
    # Get recent batch IDs
    recent_batches = await db.units_staging.distinct("crawler_batch_id")
    
    return {
        "buildings_staging": {
            "total": buildings_pending + buildings_approved + buildings_rejected,
            "pending": buildings_pending,
            "approved": buildings_approved,
            "rejected": buildings_rejected
        },
        "units_staging": {
            "total": units_pending + units_approved + units_rejected,
            "pending": units_pending,
            "approved": units_approved,
            "rejected": units_rejected
        },
        "unavailability_reviews": {
            "total": unavail_pending + unavail_confirmed + unavail_false_positive,
            "pending": unavail_pending,
            "confirmed_unavailable": unavail_confirmed,
            "false_positive": unavail_false_positive
        },
        "recent_batch_ids": recent_batches[-10:] if recent_batches else []
    }


# ============ UNAVAILABILITY REVIEW ROUTES ============

class UnavailabilityReviewInput(BaseModel):
    """Input for reviewing unavailability flags"""
    review_status: str  # confirmed_unavailable, false_positive
    reviewer_notes: Optional[str] = None


@api_router.get("/admin/unavailability-reviews")
async def get_unavailability_reviews(
    status: str = Query("pending", description="Filter by status: pending, confirmed_unavailable, false_positive"),
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    min_misses: int = Query(1, description="Minimum consecutive misses to show"),
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """
    Get units flagged as potentially unavailable for admin review.
    
    These are production units that were NOT found in recent crawls.
    Units with higher consecutive_misses are more likely to be actually unavailable.
    """
    query = {"review_status": status}
    
    if building_id:
        query["building_id"] = building_id
    if min_misses > 1:
        query["consecutive_misses"] = {"$gte": min_misses}
    
    reviews = await db.unavailability_reviews.find(
        query, {"_id": 0}
    ).sort([("consecutive_misses", -1), ("last_checked_at", -1)]).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with building names
    building_ids = list(set(r.get('building_id') for r in reviews if r.get('building_id')))
    buildings_map = {}
    if building_ids:
        buildings = await db.buildings.find(
            {"id": {"$in": building_ids}}, 
            {"_id": 0, "id": 1, "name": 1, "address": 1}
        ).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
    
    for review in reviews:
        building = buildings_map.get(review.get('building_id'), {})
        review['building_name'] = building.get('name', 'Unknown')
        review['building_address'] = building.get('address', 'Unknown')
    
    total = await db.unavailability_reviews.count_documents(query)
    
    return {
        "items": reviews,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@api_router.put("/admin/unavailability-reviews/{review_id}")
async def review_unavailability_flag(
    review_id: str,
    input: UnavailabilityReviewInput,
    user: User = Depends(require_admin)
):
    """
    Review an unavailability flag - confirm unit is unavailable or mark as false positive.
    
    Actions:
    - confirmed_unavailable: Marks the production unit as unavailable (is_available=false, lifecycle_status='rented')
    - false_positive: Keeps the unit available, dismisses the flag
    """
    review = await db.unavailability_reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update the review record
    await db.unavailability_reviews.update_one(
        {"id": review_id},
        {
            "$set": {
                "review_status": input.review_status,
                "reviewed_by": user.id,
                "reviewed_at": now,
                "reviewer_notes": input.reviewer_notes
            }
        }
    )
    
    # If confirmed unavailable, update the production unit
    if input.review_status == "confirmed_unavailable":
        unit_id = review.get('unit_id')
        
        # Update production unit
        result = await db.units.update_one(
            {"id": unit_id},
            {
                "$set": {
                    "is_available": False,
                    "lifecycle_status": "rented",
                    "unavailable_reason": "not_found_in_crawl",
                    "unavailable_confirmed_by": user.id,
                    "unavailable_confirmed_at": now,
                    "updated_at": now
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Marked unit {review.get('unit_number')} as unavailable (confirmed by admin)")
            
            # Record status change in history
            status_change = {
                "id": str(uuid.uuid4()),
                "unit_id": unit_id,
                "old_status": "available",
                "new_status": "rented",
                "source": "unavailability_review",
                "changed_by": user.id,
                "reason": f"Not found in crawl ({review.get('consecutive_misses', 1)} consecutive misses). {input.reviewer_notes or ''}",
                "created_at": now
            }
            await db.status_changes.insert_one(status_change)
        
        return {
            "message": f"Unit {review.get('unit_number')} marked as unavailable",
            "unit_id": unit_id,
            "review_status": input.review_status
        }
    else:
        # False positive - unit is still available, just dismiss the flag
        logger.info(f"Unavailability flag for unit {review.get('unit_number')} marked as false positive")
        return {
            "message": f"Flag dismissed for unit {review.get('unit_number')}",
            "unit_id": review.get('unit_id'),
            "review_status": input.review_status
        }


class BulkUnavailabilityReviewInput(BaseModel):
    """Input for bulk reviewing unavailability flags"""
    review_ids: List[str]
    review_status: str  # confirmed_unavailable, false_positive
    reviewer_notes: Optional[str] = None


@api_router.post("/admin/unavailability-reviews/bulk-review")
async def bulk_review_unavailability(
    input: BulkUnavailabilityReviewInput,
    user: User = Depends(require_admin)
):
    """
    Bulk review multiple unavailability flags at once.
    """
    if input.review_status not in ["confirmed_unavailable", "false_positive"]:
        raise HTTPException(status_code=400, detail="Invalid review_status")
    
    now = datetime.now(timezone.utc).isoformat()
    processed = 0
    units_marked_unavailable = []
    
    for review_id in input.review_ids:
        review = await db.unavailability_reviews.find_one({"id": review_id})
        if not review:
            continue
        
        # Update review record
        await db.unavailability_reviews.update_one(
            {"id": review_id},
            {
                "$set": {
                    "review_status": input.review_status,
                    "reviewed_by": user.id,
                    "reviewed_at": now,
                    "reviewer_notes": input.reviewer_notes
                }
            }
        )
        
        # If confirmed unavailable, update production unit
        if input.review_status == "confirmed_unavailable":
            unit_id = review.get('unit_id')
            await db.units.update_one(
                {"id": unit_id},
                {
                    "$set": {
                        "is_available": False,
                        "lifecycle_status": "rented",
                        "unavailable_reason": "not_found_in_crawl",
                        "unavailable_confirmed_by": user.id,
                        "unavailable_confirmed_at": now,
                        "updated_at": now
                    }
                }
            )
            units_marked_unavailable.append(review.get('unit_number'))
        
        processed += 1
    
    return {
        "message": f"Processed {processed} reviews",
        "review_status": input.review_status,
        "units_marked_unavailable": units_marked_unavailable if input.review_status == "confirmed_unavailable" else []
    }


@api_router.get("/admin/unavailability-reviews/stats")
async def get_unavailability_stats(user: User = Depends(require_admin)):
    """Get summary statistics for unavailability reviews"""
    pending = await db.unavailability_reviews.count_documents({"review_status": "pending"})
    confirmed = await db.unavailability_reviews.count_documents({"review_status": "confirmed_unavailable"})
    false_positive = await db.unavailability_reviews.count_documents({"review_status": "false_positive"})
    
    # Get high-priority items (3+ consecutive misses)
    high_priority = await db.unavailability_reviews.count_documents({
        "review_status": "pending",
        "consecutive_misses": {"$gte": 3}
    })
    
    # Get by building breakdown
    pipeline = [
        {"$match": {"review_status": "pending"}},
        {"$group": {"_id": "$building_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    by_building = await db.unavailability_reviews.aggregate(pipeline).to_list(10)
    
    # Enrich with building names
    building_ids = [b['_id'] for b in by_building]
    if building_ids:
        buildings = await db.buildings.find(
            {"id": {"$in": building_ids}},
            {"_id": 0, "id": 1, "name": 1}
        ).to_list(len(building_ids))
        buildings_map = {b['id']: b['name'] for b in buildings}
        for b in by_building:
            b['building_name'] = buildings_map.get(b['_id'], 'Unknown')
    
    return {
        "total_pending": pending,
        "total_confirmed": confirmed,
        "total_false_positive": false_positive,
        "high_priority_count": high_priority,
        "pending_by_building": by_building
    }


# ============ UNAVAILABLE UNITS MANAGEMENT ============

@api_router.get("/admin/units/unavailable")
async def get_unavailable_units(
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    building_id: Optional[str] = Query(None),
    user: User = Depends(require_admin)
):
    """
    Get units that are marked as unavailable/rented.
    These units can be re-listed if they become available again.
    """
    query = {
        "$or": [
            {"is_available": False},
            {"lifecycle_status": {"$in": ["rented", "unavailable"]}}
        ]
    }
    
    if building_id:
        query["building_id"] = building_id
    
    units = await db.units.find(
        query, {"_id": 0}
    ).sort("updated_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with building info
    building_ids = list(set(u.get('building_id') for u in units if u.get('building_id')))
    buildings_map = {}
    if building_ids:
        buildings = await db.buildings.find(
            {"id": {"$in": building_ids}},
            {"_id": 0, "id": 1, "name": 1, "address": 1}
        ).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
    
    for unit in units:
        building = buildings_map.get(unit.get('building_id'), {})
        unit['building_name'] = building.get('name', 'Unknown')
        unit['building_address'] = building.get('address', 'Unknown')
    
    total = await db.units.count_documents(query)
    
    return {
        "items": units,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@api_router.put("/admin/units/{unit_id}/relist")
async def relist_unavailable_unit(
    unit_id: str,
    rent: Optional[int] = None,
    notes: Optional[str] = None,
    user: User = Depends(require_admin)
):
    """
    Re-list an unavailable unit, making it available again.
    Optionally update the rent price.
    """
    unit = await db.units.find_one({"id": unit_id})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    update_data = {
        "is_available": True,
        "lifecycle_status": "available",
        "relisted_at": now,
        "relisted_by": user.id,
        "relist_notes": notes,
        "updated_at": now
    }
    
    # Update rent if provided
    if rent is not None:
        update_data["rent"] = rent
        update_data["rent_updated_at"] = now
    
    # Clear unavailability fields
    update_data["unavailable_reason"] = None
    update_data["unavailable_confirmed_by"] = None
    update_data["unavailable_confirmed_at"] = None
    
    result = await db.units.update_one(
        {"id": unit_id},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        # Record status change
        status_change = {
            "id": str(uuid.uuid4()),
            "unit_id": unit_id,
            "old_status": unit.get('lifecycle_status', 'unavailable'),
            "new_status": "available",
            "source": "admin_relist",
            "changed_by": user.id,
            "reason": notes or "Re-listed by admin",
            "created_at": now
        }
        await db.status_changes.insert_one(status_change)
        
        # Clear any pending unavailability review for this unit
        await db.unavailability_reviews.update_many(
            {"unit_id": unit_id, "review_status": "pending"},
            {"$set": {"review_status": "relisted", "reviewed_at": now, "reviewed_by": user.id}}
        )
        
        logger.info(f"Unit {unit.get('unit_number')} re-listed by admin {user.email}")
        
        return {
            "message": f"Unit {unit.get('unit_number')} has been re-listed",
            "unit_id": unit_id,
            "new_rent": rent if rent else unit.get('rent')
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to update unit")


class BulkRelistInput(BaseModel):
    unit_ids: List[str]
    notes: Optional[str] = None


@api_router.post("/admin/units/bulk-relist")
async def bulk_relist_units(
    input: BulkRelistInput,
    user: User = Depends(require_admin)
):
    """
    Re-list multiple unavailable units at once.
    """
    now = datetime.now(timezone.utc).isoformat()
    relisted = []
    
    for unit_id in input.unit_ids:
        unit = await db.units.find_one({"id": unit_id})
        if not unit:
            continue
        
        result = await db.units.update_one(
            {"id": unit_id},
            {
                "$set": {
                    "is_available": True,
                    "lifecycle_status": "available",
                    "relisted_at": now,
                    "relisted_by": user.id,
                    "relist_notes": input.notes,
                    "updated_at": now,
                    "unavailable_reason": None,
                    "unavailable_confirmed_by": None,
                    "unavailable_confirmed_at": None
                }
            }
        )
        
        if result.modified_count > 0:
            relisted.append(unit.get('unit_number'))
            
            # Clear pending unavailability reviews
            await db.unavailability_reviews.update_many(
                {"unit_id": unit_id, "review_status": "pending"},
                {"$set": {"review_status": "relisted", "reviewed_at": now, "reviewed_by": user.id}}
            )
    
    return {
        "message": f"Re-listed {len(relisted)} units",
        "relisted_units": relisted
    }


# ============ REJECTED STAGING UNITS MANAGEMENT ============

@api_router.get("/admin/staging/rejected")
async def get_rejected_staging_units(
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """
    Get rejected staging units that can be reconsidered for listing.
    """
    units = await db.units_staging.find(
        {"review_status": "rejected"}, {"_id": 0}
    ).sort("reviewed_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with building info
    building_ids = list(set(u.get('building_id') for u in units if u.get('building_id')))
    buildings_map = {}
    if building_ids:
        buildings = await db.buildings.find(
            {"id": {"$in": building_ids}},
            {"_id": 0, "id": 1, "name": 1, "address": 1}
        ).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
    
    for unit in units:
        building = buildings_map.get(unit.get('building_id'), {})
        unit['building_name'] = building.get('name', 'Unknown')
        unit['building_address'] = building.get('address', 'Unknown')
    
    total = await db.units_staging.count_documents({"review_status": "rejected"})
    
    return {
        "items": units,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@api_router.put("/admin/staging/rejected/{staging_id}/reconsider")
async def reconsider_rejected_staging(
    staging_id: str,
    user: User = Depends(require_admin)
):
    """
    Move a rejected staging unit back to pending for reconsideration.
    """
    unit = await db.units_staging.find_one({"id": staging_id})
    if not unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    if unit.get('review_status') != 'rejected':
        raise HTTPException(status_code=400, detail="Unit is not in rejected status")
    
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db.units_staging.update_one(
        {"id": staging_id},
        {
            "$set": {
                "review_status": "pending",
                "reconsidered_at": now,
                "reconsidered_by": user.id,
                "updated_at": now
            },
            "$unset": {
                "rejection_reason": "",
                "rejected_by": "",
                "rejected_at": ""
            }
        }
    )
    
    if result.modified_count > 0:
        return {
            "message": f"Unit {unit.get('unit_number')} moved back to pending review",
            "staging_id": staging_id
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to update unit")


class ApproveRejectedInput(BaseModel):
    rent: Optional[int] = None


@api_router.put("/admin/staging/rejected/{staging_id}/approve-direct")
async def approve_rejected_directly(
    staging_id: str,
    input: ApproveRejectedInput = ApproveRejectedInput(),
    user: User = Depends(require_admin)
):
    """
    Directly approve a previously rejected staging unit to production.
    """
    staging_unit = await db.units_staging.find_one({"id": staging_id})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Prepare production unit data
    production_unit = {
        "id": str(uuid.uuid4()),
        "building_id": staging_unit.get('building_id'),
        "unit_number": staging_unit.get('unit_number'),
        "rent": input.rent if input.rent else staging_unit.get('rent'),
        "bedrooms": staging_unit.get('bedrooms'),
        "bathrooms": staging_unit.get('bathrooms'),
        "sqft": staging_unit.get('sqft'),
        "amenities": staging_unit.get('amenities', []),
        "images": staging_unit.get('images', []),
        "floor_plan_url": staging_unit.get('floor_plan_url'),
        "is_available": True,
        "lifecycle_status": "available",
        "source_url": staging_unit.get('source_url'),
        "crawler_source": staging_unit.get('crawler_source'),
        "created_at": now,
        "updated_at": now,
        "approved_from_rejected": True,
        "approved_by": user.id,
        "approved_at": now
    }
    
    # Insert to production
    await db.units.insert_one(production_unit)
    
    # Update staging record
    await db.units_staging.update_one(
        {"id": staging_id},
        {
            "$set": {
                "review_status": "approved",
                "approved_at": now,
                "approved_by": user.id,
                "production_unit_id": production_unit['id']
            }
        }
    )
    
    return {
        "message": f"Unit {staging_unit.get('unit_number')} approved and added to production",
        "production_unit_id": production_unit['id']
    }


# ============ STAGING APPROVAL SYSTEM ============

@api_router.get("/staging/units")
async def get_staging_units_for_approval(
    status: str = Query("pending", description="Filter by status: pending, approved, rejected"),
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    batch_id: Optional[str] = Query(None, description="Filter by crawler batch ID"),
    has_duplicates: Optional[bool] = Query(None, description="Filter by duplicate flag"),
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """
    Get staged units for approval review.
    
    Query params:
    - status: pending | approved | rejected
    - building_id: Filter by building
    - batch_id: Filter by crawl batch
    - has_duplicates: true to show only flagged duplicates
    """
    query = {"review_status": status}
    
    if building_id:
        query["building_id"] = building_id
    if batch_id:
        query["crawler_batch_id"] = batch_id
    if has_duplicates is True:
        query["validation_flags"] = {"$in": ["likely_duplicate", "possible_duplicate", "potential_duplicate"]}
    elif has_duplicates is False:
        query["validation_flags"] = {"$nin": ["likely_duplicate", "possible_duplicate", "potential_duplicate"]}
    
    # Get units with building info
    units = await db.units_staging.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with building names
    for unit in units:
        # Try production building first
        building = await db.buildings.find_one({"id": unit["building_id"]}, {"_id": 0, "name": 1, "address": 1})
        if not building:
            # Try staging building
            building = await db.buildings_staging.find_one({"id": unit["building_id"]}, {"_id": 0, "name": 1, "address": 1})
        
        unit["building_name"] = building.get("name", "Unknown") if building else "Unknown"
        unit["building_address"] = building.get("address", "") if building else ""
    
    total = await db.units_staging.count_documents(query)
    pending_count = await db.units_staging.count_documents({"review_status": "pending"})
    
    return {
        "items": units,
        "total": total,
        "pending_total": pending_count,
        "skip": skip,
        "limit": limit
    }


@api_router.post("/staging/approve/{unit_id}")
async def approve_staging_unit(
    unit_id: str,
    notes: Optional[str] = Query(None, description="Optional approval notes"),
    user: User = Depends(require_admin)
):
    """
    Approve a staged unit and move it to production.
    
    Process:
    1. Validate building exists in production (create if missing from staging)
    2. Check for duplicates in production (prevent double insertion)
    3. Move unit from staging to production
    4. Set is_verified = true
    5. Maintain source metadata
    6. Record approval timestamp
    """
    # Get the staged unit
    staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staged_unit:
        raise HTTPException(status_code=404, detail="Staged unit not found")
    
    if staged_unit.get("review_status") == "approved":
        raise HTTPException(status_code=400, detail="Unit already approved")
    
    building_id = staged_unit["building_id"]
    production_building_id = building_id
    
    # Step 1: Validate building exists in production
    production_building = await db.buildings.find_one({"id": building_id}, {"_id": 0})
    
    if not production_building:
        # Check if building exists in staging
        staged_building = await db.buildings_staging.find_one({"id": building_id}, {"_id": 0})
        
        if staged_building:
            # Create building in production from staging data
            production_building_id = str(uuid.uuid4())
            new_production_building = {
                "id": production_building_id,
                "name": staged_building["name"],
                "address": staged_building["address"],
                "neighborhood": staged_building["neighborhood"],
                "city": staged_building["city"],
                "state": staged_building["state"],
                "zip_code": staged_building["zip_code"],
                "source_url": staged_building["source_url"],
                "latitude": staged_building.get("latitude"),
                "longitude": staged_building.get("longitude"),
                "last_crawled": staged_building.get("last_crawled"),
                # Source metadata
                "crawler_source": staged_building.get("crawler_source", ""),
                "original_staging_id": building_id,
                "is_verified": True,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "verified_by": user.id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.buildings.insert_one(new_production_building)
            
            # Mark staging building as promoted
            await db.buildings_staging.update_one(
                {"id": building_id},
                {
                    "$set": {
                        "review_status": "promoted",
                        "matched_production_id": production_building_id,
                        "reviewed_by": user.id,
                        "reviewed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Auto-created production building {production_building_id} from staging {building_id}")
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Building {building_id} not found in production or staging. Cannot approve unit."
            )
    
    # Step 2: Check for duplicates in production
    # Use normalized unit number if available
    normalized_unit = staged_unit.get("normalized_unit_number", staged_unit["unit_number"])
    
    existing_unit = await db.units.find_one({
        "building_id": production_building_id,
        "$or": [
            {"unit_number": staged_unit["unit_number"]},
            {"unit_number": normalized_unit}
        ]
    }, {"_id": 0})
    
    action = "created"
    
    if existing_unit:
        # UPDATE existing production unit instead of rejecting
        production_unit_id = existing_unit["id"]
        update_data = {
            "rent": staged_unit["rent"],
            "bedrooms": staged_unit["bedrooms"],
            "bathrooms": staged_unit["bathrooms"],
            "square_feet": staged_unit.get("square_feet"),
            "available_date": staged_unit.get("available_date", existing_unit.get("available_date", "Immediate")),
            "amenities": staged_unit.get("amenities", existing_unit.get("amenities", [])),
            "images": staged_unit.get("images") if staged_unit.get("images") else existing_unit.get("images", []),
            "description": staged_unit.get("description") or existing_unit.get("description", ""),
            "is_available": staged_unit.get("is_available", True),
            "latitude": staged_unit.get("latitude") or existing_unit.get("latitude"),
            "longitude": staged_unit.get("longitude") or existing_unit.get("longitude"),
            # Update verification
            "is_verified": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verified_by": user.id,
            # Update source metadata
            "crawler_source": staged_unit.get("crawler_source", existing_unit.get("crawler_source", "")),
            "crawler_batch_id": staged_unit.get("crawler_batch_id", existing_unit.get("crawler_batch_id", "")),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.units.update_one({"id": production_unit_id}, {"$set": update_data})
        action = "updated"
        
        logger.info(f"Updated existing production unit {production_unit_id} from staging {unit_id}")
    else:
        # Step 3: Create NEW production unit
        production_unit_id = str(uuid.uuid4())
        production_unit = {
            "id": production_unit_id,
            "building_id": production_building_id,
            "unit_number": staged_unit["unit_number"],
            "rent": staged_unit["rent"],
            "bedrooms": staged_unit["bedrooms"],
            "bathrooms": staged_unit["bathrooms"],
            "square_feet": staged_unit.get("square_feet"),
            "available_date": staged_unit.get("available_date", "Immediate"),
            "amenities": staged_unit.get("amenities", []),
            "images": staged_unit.get("images", []),
            "description": staged_unit.get("description", ""),
            "is_available": staged_unit.get("is_available", True),
            "is_featured": False,
            "latitude": staged_unit.get("latitude"),
            "longitude": staged_unit.get("longitude"),
            # Verification flags
            "is_verified": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verified_by": user.id,
            # Source metadata
            "crawler_source": staged_unit.get("crawler_source", ""),
            "crawler_batch_id": staged_unit.get("crawler_batch_id", ""),
            "original_staging_id": unit_id,
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.units.insert_one(production_unit)
    
    # Step 4: Update staging unit status
    await db.units_staging.update_one(
        {"id": unit_id},
        {
            "$set": {
                "review_status": "approved",
                "matched_production_id": production_unit_id,
                "reviewer_notes": notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    logger.info(f"Approved staging unit {unit_id} -> production unit {production_unit_id}")
    
    return {
        "message": f"Unit approved and {'updated in' if action == 'updated' else 'moved to'} production",
        "staging_id": unit_id,
        "production_id": production_unit_id,
        "building_id": production_building_id,
        "unit_number": staged_unit["unit_number"],
        "action": action,
        "approved_at": datetime.now(timezone.utc).isoformat()
    }


@api_router.post("/staging/reject/{unit_id}")
async def reject_staging_unit(
    unit_id: str,
    reason: str = Query(..., description="Reason for rejection"),
    user: User = Depends(require_admin)
):
    """
    Reject a staged unit.
    
    The unit remains in staging with status='rejected' for audit purposes.
    """
    # Get the staged unit
    staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staged_unit:
        raise HTTPException(status_code=404, detail="Staged unit not found")
    
    if staged_unit.get("review_status") == "rejected":
        raise HTTPException(status_code=400, detail="Unit already rejected")
    
    if staged_unit.get("review_status") == "approved":
        raise HTTPException(status_code=400, detail="Cannot reject an already approved unit")
    
    # Update staging unit status
    await db.units_staging.update_one(
        {"id": unit_id},
        {
            "$set": {
                "review_status": "rejected",
                "reviewer_notes": reason,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    logger.info(f"Rejected staging unit {unit_id}: {reason}")
    
    return {
        "message": "Unit rejected",
        "staging_id": unit_id,
        "reason": reason,
        "rejected_at": datetime.now(timezone.utc).isoformat()
    }


@api_router.post("/staging/approve-batch")
async def approve_batch_staging_units(
    unit_ids: List[str] = Query(..., description="List of unit IDs to approve"),
    notes: Optional[str] = Query(None, description="Optional batch approval notes"),
    user: User = Depends(require_admin)
):
    """
    Approve multiple staged units in batch.
    
    Returns results for each unit (success or failure reason).
    """
    results = []
    approved_count = 0
    failed_count = 0
    
    for unit_id in unit_ids:
        try:
            # Get the staged unit
            staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
            if not staged_unit:
                results.append({"unit_id": unit_id, "status": "failed", "reason": "Not found"})
                failed_count += 1
                continue
            
            if staged_unit.get("review_status") == "approved":
                results.append({"unit_id": unit_id, "status": "skipped", "reason": "Already approved"})
                continue
            
            # Use the single approve endpoint logic
            building_id = staged_unit["building_id"]
            production_building_id = building_id
            
            # Check building
            production_building = await db.buildings.find_one({"id": building_id}, {"_id": 0})
            
            if not production_building:
                staged_building = await db.buildings_staging.find_one({"id": building_id}, {"_id": 0})
                if staged_building:
                    # Auto-create building
                    production_building_id = str(uuid.uuid4())
                    new_building = {
                        "id": production_building_id,
                        "name": staged_building["name"],
                        "address": staged_building["address"],
                        "neighborhood": staged_building["neighborhood"],
                        "city": staged_building["city"],
                        "state": staged_building["state"],
                        "zip_code": staged_building["zip_code"],
                        "source_url": staged_building["source_url"],
                        "latitude": staged_building.get("latitude"),
                        "longitude": staged_building.get("longitude"),
                        "crawler_source": staged_building.get("crawler_source", ""),
                        "original_staging_id": building_id,
                        "is_verified": True,
                        "verified_at": datetime.now(timezone.utc).isoformat(),
                        "verified_by": user.id,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.buildings.insert_one(new_building)
                    await db.buildings_staging.update_one(
                        {"id": building_id},
                        {"$set": {"review_status": "promoted", "matched_production_id": production_building_id}}
                    )
                else:
                    results.append({"unit_id": unit_id, "status": "failed", "reason": "Building not found"})
                    failed_count += 1
                    continue
            
            # Check for duplicates
            normalized_unit = staged_unit.get("normalized_unit_number", staged_unit["unit_number"])
            existing = await db.units.find_one({
                "building_id": production_building_id,
                "$or": [{"unit_number": staged_unit["unit_number"]}, {"unit_number": normalized_unit}]
            })
            
            if existing:
                await db.units_staging.update_one(
                    {"id": unit_id},
                    {"$set": {"review_status": "rejected", "reviewer_notes": f"Duplicate of {existing['id']}"}}
                )
                results.append({"unit_id": unit_id, "status": "rejected", "reason": f"Duplicate of {existing['id']}"})
                failed_count += 1
                continue
            
            # Create production unit
            production_unit_id = str(uuid.uuid4())
            production_unit = {
                "id": production_unit_id,
                "building_id": production_building_id,
                "unit_number": staged_unit["unit_number"],
                "rent": staged_unit["rent"],
                "bedrooms": staged_unit["bedrooms"],
                "bathrooms": staged_unit["bathrooms"],
                "square_feet": staged_unit.get("square_feet"),
                "available_date": staged_unit.get("available_date", "Immediate"),
                "amenities": staged_unit.get("amenities", []),
                "images": staged_unit.get("images", []),
                "description": staged_unit.get("description", ""),
                "is_available": True,
                "is_featured": False,
                "is_verified": True,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "verified_by": user.id,
                "crawler_source": staged_unit.get("crawler_source", ""),
                "crawler_batch_id": staged_unit.get("crawler_batch_id", ""),
                "original_staging_id": unit_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.units.insert_one(production_unit)
            await db.units_staging.update_one(
                {"id": unit_id},
                {
                    "$set": {
                        "review_status": "approved",
                        "matched_production_id": production_unit_id,
                        "reviewer_notes": notes,
                        "reviewed_by": user.id,
                        "reviewed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            results.append({
                "unit_id": unit_id,
                "status": "approved",
                "production_id": production_unit_id
            })
            approved_count += 1
            
        except Exception as e:
            results.append({"unit_id": unit_id, "status": "failed", "reason": str(e)})
            failed_count += 1
    
    return {
        "message": f"Batch approval complete: {approved_count} approved, {failed_count} failed",
        "approved_count": approved_count,
        "failed_count": failed_count,
        "results": results
    }


@api_router.post("/staging/reject-batch")
async def reject_batch_staging_units(
    unit_ids: List[str] = Query(..., description="List of unit IDs to reject"),
    reason: str = Query(..., description="Rejection reason"),
    user: User = Depends(require_admin)
):
    """
    Reject multiple staged units in batch.
    """
    result = await db.units_staging.update_many(
        {"id": {"$in": unit_ids}, "review_status": "pending"},
        {
            "$set": {
                "review_status": "rejected",
                "reviewer_notes": reason,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": f"{result.modified_count} units rejected",
        "rejected_count": result.modified_count,
        "reason": reason
    }


class BulkDeleteInput(BaseModel):
    """Input model for bulk delete operations"""
    ids: List[str]


@api_router.post("/admin/staging/units/bulk-delete")
async def bulk_delete_staging_units(
    input: BulkDeleteInput,
    user: User = Depends(require_admin)
):
    """
    Bulk delete staging units.
    """
    if not input.ids:
        raise HTTPException(status_code=400, detail="No unit IDs provided")
    
    result = await db.units_staging.delete_many({"id": {"$in": input.ids}})
    
    logger.info(f"Admin {user.email} bulk deleted {result.deleted_count} staging units")
    
    return {
        "message": f"{result.deleted_count} staging unit(s) deleted",
        "deleted_count": result.deleted_count
    }


@api_router.post("/admin/units/bulk-delete")
async def bulk_delete_production_units(
    input: BulkDeleteInput,
    user: User = Depends(require_admin)
):
    """
    Bulk delete production units.
    """
    if not input.ids:
        raise HTTPException(status_code=400, detail="No unit IDs provided")
    
    # Delete units
    result = await db.units.delete_many({"id": {"$in": input.ids}})
    
    # Also delete any associated favorites
    await db.favorites.delete_many({"unit_id": {"$in": input.ids}})
    
    logger.info(f"Admin {user.email} bulk deleted {result.deleted_count} production units")
    
    return {
        "message": f"{result.deleted_count} unit(s) deleted from production",
        "deleted_count": result.deleted_count
    }


@api_router.post("/admin/staging/units/bulk-approve")
async def bulk_approve_staging_units(
    input: BulkDeleteInput,  # Reusing the same input model (just needs ids)
    user: User = Depends(require_admin)
):
    """
    Bulk approve staging units and promote them to production.
    """
    if not input.ids:
        raise HTTPException(status_code=400, detail="No unit IDs provided")
    
    approved_count = 0
    errors = []
    
    for unit_id in input.ids:
        try:
            # Get the staged unit
            staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
            if not staged_unit:
                errors.append(f"Unit {unit_id} not found")
                continue
            
            if staged_unit.get("review_status") == "approved":
                errors.append(f"Unit {unit_id} already approved")
                continue
            
            # Get or create building
            building_id = staged_unit.get('building_id')
            if not building_id:
                # Try to find or create building from staging data
                building_name = staged_unit.get('building_name', 'Unknown Building')
                building_address = staged_unit.get('building_address', '')
                
                existing_building = await db.buildings.find_one({
                    '$or': [
                        {'name': building_name},
                        {'address': building_address}
                    ]
                }, {"_id": 0})
                
                if existing_building:
                    building_id = existing_building['id']
                else:
                    # Create new building
                    import uuid
                    building_id = str(uuid.uuid4())
                    new_building = {
                        'id': building_id,
                        'name': building_name,
                        'address': building_address,
                        'neighborhood': staged_unit.get('neighborhood', ''),
                        'city': staged_unit.get('city', 'New York'),
                        'state': staged_unit.get('state', 'NY'),
                        'images': staged_unit.get('building_images', []),
                        'amenities': staged_unit.get('amenities', []),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    await db.buildings.insert_one(new_building)
                    logger.info(f"Created new building: {building_name} ({building_id})")
            
            # Create production unit
            import uuid
            production_unit = {
                'id': str(uuid.uuid4()),
                'building_id': building_id,
                'unit_number': staged_unit.get('unit_number', 'N/A'),
                'rent': staged_unit.get('rent', 0),
                'bedrooms': staged_unit.get('bedrooms', 0),
                'bathrooms': staged_unit.get('bathrooms', 1),
                'sqft': staged_unit.get('sqft'),
                'images': staged_unit.get('images', []),
                'amenities': staged_unit.get('amenities', []),
                'is_available': True,
                'available_date': staged_unit.get('available_date'),
                'description': staged_unit.get('description', ''),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'promoted_from_staging': unit_id,
                'promoted_by': user.email,
                'promoted_at': datetime.now(timezone.utc).isoformat()
            }
            
            await db.units.insert_one(production_unit)
            
            # Mark staging unit as approved
            await db.units_staging.update_one(
                {"id": unit_id},
                {
                    "$set": {
                        "review_status": "approved",
                        "reviewed_by": user.email,
                        "reviewed_at": datetime.now(timezone.utc).isoformat(),
                        "production_unit_id": production_unit['id']
                    }
                }
            )
            
            approved_count += 1
            logger.info(f"Bulk approved unit {unit_id} -> production {production_unit['id']}")
            
        except Exception as e:
            logger.error(f"Error approving unit {unit_id}: {e}")
            errors.append(f"Unit {unit_id}: {str(e)}")
            continue
    
    logger.info(f"Admin {user.email} bulk approved {approved_count} staging units")
    
    return {
        "message": f"{approved_count} unit(s) approved and added to production",
        "approved_count": approved_count,
        "errors": errors if errors else None
    }

# ============ PROMOTION SERVICE ENDPOINTS ============

@api_router.post("/staging/promote/{unit_id}")
async def promote_staging_unit_via_service(
    unit_id: str,
    notes: Optional[str] = Query(None, description="Optional promotion notes"),
    user: User = Depends(require_admin)
):
    """
    Promote a staged unit to production using the promotion service.
    
    Promotion rules:
    - If production unit exists → update price/status only
    - If not → create new production unit
    - Preserves history: price_changes, status_changes
    """
    if not PROMOTION_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Promotion service not available")
    
    # Get the staged unit
    staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staged_unit:
        raise HTTPException(status_code=404, detail="Staged unit not found")
    
    if staged_unit.get("review_status") == "approved":
        raise HTTPException(status_code=400, detail="Unit already approved/promoted")
    
    # Get promotion service
    promotion_service = get_promotion_service(db)
    
    try:
        result = await promotion_service.promote_unit(
            staged_unit=staged_unit,
            approved_by=user.id,
            notes=notes
        )
        
        return {
            "message": f"Unit {result['action']} successfully",
            "staging_id": result["staging_id"],
            "production_id": result["production_id"],
            "action": result["action"],
            "changes": result["changes"],
            "building_created": result["building_created"],
            "promoted_at": result["promoted_at"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Promotion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/staging/promote-batch")
async def promote_batch_staging_units(
    unit_ids: List[str] = Query(..., description="List of unit IDs to promote"),
    notes: Optional[str] = Query(None, description="Optional batch promotion notes"),
    user: User = Depends(require_admin)
):
    """
    Promote multiple staged units to production in batch.
    
    Returns results for each unit showing whether it was created or updated.
    """
    if not PROMOTION_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Promotion service not available")
    
    promotion_service = get_promotion_service(db)
    
    results = await promotion_service.promote_batch(
        staging_ids=unit_ids,
        approved_by=user.id,
        notes=notes
    )
    
    return {
        "message": f"Batch promotion complete: {results['created']} created, {results['updated']} updated, {results['failed']} failed",
        "total": results["total"],
        "created": results["created"],
        "updated": results["updated"],
        "failed": results["failed"],
        "details": results["details"]
    }


@api_router.get("/units/{unit_id}/price-history")
async def get_unit_price_history(
    unit_id: str,
    limit: int = Query(50, le=200),
    user: User = Depends(require_admin)
):
    """
    Get price change history for a production unit.
    """
    if not PROMOTION_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Promotion service not available")
    
    # Verify unit exists
    unit = await db.units.find_one({"id": unit_id}, {"_id": 0, "id": 1, "unit_number": 1, "rent": 1})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    promotion_service = get_promotion_service(db)
    history = await promotion_service.get_unit_price_history(unit_id, limit)
    
    return {
        "unit_id": unit_id,
        "unit_number": unit.get("unit_number"),
        "current_rent": unit.get("rent"),
        "price_history": history,
        "total_changes": len(history)
    }


@api_router.get("/units/{unit_id}/status-history")
async def get_unit_status_history(
    unit_id: str,
    limit: int = Query(50, le=200),
    user: User = Depends(require_admin)
):
    """
    Get status change history for a production unit.
    """
    if not PROMOTION_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Promotion service not available")
    
    # Verify unit exists
    unit = await db.units.find_one({"id": unit_id}, {"_id": 0, "id": 1, "unit_number": 1, "is_available": 1})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    promotion_service = get_promotion_service(db)
    history = await promotion_service.get_unit_status_history(unit_id, limit)
    
    return {
        "unit_id": unit_id,
        "unit_number": unit.get("unit_number"),
        "current_status": "available" if unit.get("is_available", True) else "unavailable",
        "status_history": history,
        "total_changes": len(history)
    }


@api_router.get("/admin/price-changes")
async def get_all_price_changes(
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    unit_id: Optional[str] = Query(None),
    user: User = Depends(require_admin)
):
    """
    Get all price changes across all units.
    """
    query = {}
    if unit_id:
        query["unit_id"] = unit_id
    
    changes = await db.price_changes.find(query, {"_id": 0}).sort("changed_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.price_changes.count_documents(query)
    
    return {
        "items": changes,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@api_router.get("/admin/status-changes")
async def get_all_status_changes(
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    unit_id: Optional[str] = Query(None),
    user: User = Depends(require_admin)
):
    """
    Get all status changes across all units.
    """
    query = {}
    if unit_id:
        query["unit_id"] = unit_id
    
    changes = await db.status_changes.find(query, {"_id": 0}).sort("changed_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.status_changes.count_documents(query)
    
    return {
        "items": changes,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.get("/admin/users")
async def get_users(user: User = Depends(require_admin)):
    """Get all users (admin only) - includes plain text passwords"""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.post("/admin/crawl/{building_id}")
async def trigger_crawl(building_id: str, user: User = Depends(require_admin)):
    """Manually trigger crawl for a building (admin only)"""
    building = await db.buildings.find_one({'id': building_id})
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Import crawler here to avoid circular imports
    from crawler import crawl_building
    
    try:
        await crawl_building(building_id)
        return {'message': 'Crawl started'}
    except Exception as e:
        logger.error(f"Crawl error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/admin/crawl-all")
async def trigger_crawl_all(background_tasks: BackgroundTasks, user: User = Depends(require_admin)):
    """Manually trigger crawl for all buildings (admin only)"""
    from crawler import crawl_all_buildings
    
    try:
        # Run crawl in background to avoid timeout
        background_tasks.add_task(crawl_all_buildings)
        return {'message': 'Crawl started for all buildings', 'status': 'running'}
    except Exception as e:
        logger.error(f"Crawl all error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/stats")
async def get_public_stats(response: Response):
    """Get public platform statistics"""
    # Prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    total_buildings = await db.buildings.count_documents({})
    total_units = await db.units.count_documents({})
    available_units = await db.units.count_documents({'is_available': True})
    
    return {
        'total_buildings': total_buildings,
        'total_units': total_units,
        'available_units': available_units
    }

@api_router.get("/admin/stats")
async def get_stats(user: User = Depends(require_admin)):
    """Get platform statistics (admin only)"""
    total_buildings = await db.buildings.count_documents({})
    total_units = await db.units.count_documents({})
    available_units = await db.units.count_documents({'is_available': True})
    total_users = await db.users.count_documents({})
    total_contacts = await db.contact_requests.count_documents({})
    total_subscribers = await db.email_subscribers.count_documents({'active': True})
    
    return {
        'total_buildings': total_buildings,
        'total_units': total_units,
        'available_units': available_units,
        'total_users': total_users,
        'total_contacts': total_contacts,
        'total_subscribers': total_subscribers
    }

# ============== NEIGHBORHOOD SEO ENDPOINTS ==============

@api_router.get("/neighborhoods")
async def get_all_neighborhoods():
    """Get all neighborhoods with stats for SEO pages"""
    pipeline = [
        {"$lookup": {
            "from": "buildings",
            "localField": "building_id",
            "foreignField": "id",
            "as": "building"
        }},
        {"$unwind": "$building"},
        {"$match": {"is_available": True}},
        {"$group": {
            "_id": "$building.neighborhood",
            "count": {"$sum": 1},
            "avg_rent": {"$avg": "$rent"},
            "min_rent": {"$min": "$rent"},
            "max_rent": {"$max": "$rent"},
            "city": {"$first": "$building.city"},
            "state": {"$first": "$building.state"},
            "studios": {"$sum": {"$cond": [{"$eq": ["$bedrooms", 0]}, 1, 0]}},
            "one_beds": {"$sum": {"$cond": [{"$eq": ["$bedrooms", 1]}, 1, 0]}},
            "two_plus_beds": {"$sum": {"$cond": [{"$gte": ["$bedrooms", 2]}, 1, 0]}}
        }},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"count": -1}}
    ]
    
    neighborhoods = await db.units.aggregate(pipeline).to_list(100)
    
    # Add slug for each neighborhood
    result = []
    for n in neighborhoods:
        slug = n['_id'].lower().replace(' ', '-').replace("'", "")
        result.append({
            "name": n['_id'],
            "slug": slug,
            "count": n['count'],
            "avg_rent": round(n['avg_rent']),
            "min_rent": round(n['min_rent']),
            "max_rent": round(n['max_rent']),
            "city": n['city'],
            "state": n['state'],
            "studios": n['studios'],
            "one_beds": n['one_beds'],
            "two_plus_beds": n['two_plus_beds']
        })
    
    return result

@api_router.get("/neighborhoods/{slug}")
async def get_neighborhood_detail(slug: str):
    """Get detailed neighborhood data including units"""
    # Convert slug back to neighborhood name
    # Try to find matching neighborhood
    all_buildings = await db.buildings.find({}, {"_id": 0, "neighborhood": 1}).to_list(1000)
    neighborhood_name = None
    
    for b in all_buildings:
        if b.get('neighborhood'):
            test_slug = b['neighborhood'].lower().replace(' ', '-').replace("'", "")
            if test_slug == slug:
                neighborhood_name = b['neighborhood']
                break
    
    if not neighborhood_name:
        raise HTTPException(status_code=404, detail="Neighborhood not found")
    
    # Get buildings in this neighborhood
    buildings = await db.buildings.find(
        {"neighborhood": neighborhood_name},
        {"_id": 0}
    ).to_list(100)
    
    building_ids = [b['id'] for b in buildings]
    
    # Get units
    units = await db.units.find(
        {"building_id": {"$in": building_ids}, "is_available": True},
        {"_id": 0}
    ).sort("rent", 1).to_list(500)
    
    # Add building info to units
    building_map = {b['id']: b for b in buildings}
    for unit in units:
        unit['building'] = building_map.get(unit['building_id'], {})
    
    # Calculate stats
    rents = [u['rent'] for u in units if u.get('rent')]
    studios = len([u for u in units if u.get('bedrooms') == 0])
    one_beds = len([u for u in units if u.get('bedrooms') == 1])
    two_plus = len([u for u in units if u.get('bedrooms', 0) >= 2])
    
    return {
        "name": neighborhood_name,
        "slug": slug,
        "city": buildings[0].get('city') if buildings else None,
        "state": buildings[0].get('state') if buildings else None,
        "stats": {
            "total_units": len(units),
            "total_buildings": len(buildings),
            "avg_rent": round(sum(rents) / len(rents)) if rents else 0,
            "min_rent": min(rents) if rents else 0,
            "max_rent": max(rents) if rents else 0,
            "studios": studios,
            "one_beds": one_beds,
            "two_plus_beds": two_plus
        },
        "units": units,
        "buildings": buildings
    }

# ============== END NEIGHBORHOOD ENDPOINTS ==============

@api_router.get("/admin/subscribers")
async def get_subscribers(user: User = Depends(require_admin)):
    """Get all email subscribers (admin only)"""
    subscribers = await db.email_subscribers.find({}, {"_id": 0}).sort('subscribed_at', -1).to_list(1000)
    return subscribers

@api_router.post("/admin/units/{unit_id}/toggle-featured")
async def toggle_unit_featured(unit_id: str, user: User = Depends(require_admin)):
    """Toggle featured status for a unit (admin only)"""
    existing = await db.units.find_one({'id': unit_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    current_featured = existing.get('is_featured', False)
    new_featured = not current_featured
    
    await db.units.update_one(
        {'id': unit_id}, 
        {'$set': {'is_featured': new_featured, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        'message': f"Unit {'featured' if new_featured else 'unfeatured'} successfully",
        'unit_id': unit_id,
        'is_featured': new_featured
    }

@api_router.post("/admin/set-featured-units")
async def set_featured_units(unit_ids: List[str], user: User = Depends(require_admin)):
    """Set specific units as featured and unfeature all others (admin only)"""
    # First, unfeature all units
    await db.units.update_many({}, {'$set': {'is_featured': False}})
    
    # Then feature the specified units
    if unit_ids:
        result = await db.units.update_many(
            {'id': {'$in': unit_ids}},
            {'$set': {'is_featured': True, 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        featured_count = result.modified_count
    else:
        featured_count = 0
    

# ============ AI SEARCH AGENT ============

@api_router.post("/ai-search")
async def ai_search(request: Request, search_request: AISearchRequest):
    """AI-powered apartment search agent with Google Search grounding"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from serpapi import GoogleSearch
    import re
    import json
    import asyncio
    
    async def get_google_search_context(query: str) -> dict:
        """Fetch real-time market data from Google Search via SerpApi"""
        serpapi_key = os.environ.get('SERPAPI_KEY')
        if not serpapi_key:
            return {"error": "SerpApi not configured"}
        
        try:
            # Run SerpApi search in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            
            def execute_search():
                search = GoogleSearch({
                    "q": f"{query} NYC apartments rent prices 2025",
                    "api_key": serpapi_key,
                    "num": 5,
                    "gl": "us",
                    "hl": "en"
                })
                return search.get_dict()
            
            results = await loop.run_in_executor(None, execute_search)
            
            # Parse relevant info
            organic_results = results.get("organic_results", [])[:3]
            answer_box = results.get("answer_box", {})
            
            context = {
                "search_performed": True,
                "query": query,
                "snippets": [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "source": r.get("displayed_link", "")
                    }
                    for r in organic_results
                ],
                "answer_box": answer_box.get("snippet") or answer_box.get("answer") if answer_box else None
            }
            return context
            
        except Exception as e:
            return {"error": str(e), "search_performed": False}
    
    try:
        # Get current user if logged in
        user = None
        user_email = None
        try:
            user = await get_current_user(request)
            if user:
                user_email = user.email
        except:
            pass
        
        # Generate session ID if not provided
        session_id = search_request.session_id or str(uuid.uuid4())
        
        # Get database stats for context
        total_units = await db.units.count_documents({'is_available': True})
        total_buildings = await db.buildings.count_documents({})
        
        # Get all units for search context
        units = await db.units.find(
            {'is_available': True},
            {'_id': 0, 'id': 1, 'unit_number': 1, 'rent': 1, 'bedrooms': 1, 'bathrooms': 1, 
             'building_id': 1, 'neighborhood': 1, 'amenities': 1, 'square_feet': 1}
        ).to_list(500)
        
        # Get building info
        buildings = await db.buildings.find({}, {'_id': 0}).to_list(100)
        building_map = {b['id']: b for b in buildings}
        
        # Enrich units with building info
        for unit in units:
            building = building_map.get(unit.get('building_id', ''), {})
            unit['building_name'] = building.get('name', 'Unknown')
            unit['neighborhood'] = building.get('neighborhood', 'Unknown')
            unit['city'] = building.get('city', 'New York')
        
        # Get unique neighborhoods and price ranges
        neighborhoods = list(set(u.get('neighborhood', '') for u in units if u.get('neighborhood')))
        min_rent = min((u.get('rent', 0) for u in units if u.get('rent')), default=0)
        max_rent = max((u.get('rent', 0) for u in units if u.get('rent')), default=0)
        
        # Determine if we should search Google for market context
        query_lower = search_request.message.lower()
        market_keywords = ['average', 'market', 'trend', 'price', 'compare', 'typical', 'worth', 'fair', 'expensive', 'cheap', 'afford', 'neighborhood', 'area', 'best', 'popular', 'safe']
        should_search_google = any(kw in query_lower for kw in market_keywords)
        
        # Get Google search context for market questions
        google_context = {}
        if should_search_google:
            # Extract neighborhood or location from query
            search_term = search_request.message
            for n in neighborhoods:
                if n.lower() in query_lower:
                    search_term = n
                    break
            google_context = await get_google_search_context(search_term)
        
        # Build Google context string for system prompt
        google_context_str = ""
        if google_context.get("search_performed") and google_context.get("snippets"):
            google_context_str = "\n\nREAL-TIME MARKET DATA (from Google Search):\n"
            if google_context.get("answer_box"):
                google_context_str += f"Quick Answer: {google_context['answer_box']}\n\n"
            for snippet in google_context.get("snippets", []):
                google_context_str += f"- {snippet['title']}: {snippet['snippet']} (Source: {snippet['source']})\n"
        
        # Create system prompt with Google context
        system_prompt = f"""You are the NoFeesApts.com AI Search Assistant - a friendly, knowledgeable apartment search expert for NYC, Northern NJ, and PA no-fee apartments.

CURRENT INVENTORY:
- {total_units} no-fee apartments available across {total_buildings} buildings
- Price range: ${min_rent:,.0f} - ${max_rent:,.0f}/month
- Neighborhoods: {', '.join(neighborhoods[:15])}
{google_context_str}
YOUR CAPABILITIES:
1. Search our database of {total_units} verified no-fee listings
2. Answer questions about NYC neighborhoods, apartment hunting tips, and the rental market
3. Help users find apartments that match their criteria (budget, bedrooms, location, amenities)
4. Provide real-time market insights using current data
5. For requests outside our current inventory, mention that you can help find additional options

CONTACT INFORMATION (Always provide when relevant):
- Phone: (646) 408-8048
- Email: placesfirm@gmail.com
- Name: Kiri (AI Expert Leasing Agent)

RESPONSE STYLE:
- You are Kiri, an AI expert leasing agent who helps renters find their perfect no-fee apartment
- Be conversational, helpful, and enthusiastic
- When showing results, be specific about unit details
- When answering market questions, cite the real-time data when available
- If no exact matches, suggest alternatives or offer to help find more options
- For off-site searches or special requests, offer to help directly
- Keep responses concise but informative

AVAILABLE UNITS DATA:
{json.dumps(units[:50], default=str)}

When searching, analyze the user's request and find matching units. Report the count and key details."""

        # Initialize Gemini chat
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        chat = LlmChat(
            api_key=llm_key,
            session_id=session_id,
            system_message=system_prompt
        ).with_model("gemini", "gemini-3-flash-preview")
        
        # Send user message
        user_message = UserMessage(text=search_request.message)
        response = await chat.send_message(user_message)
        
        # Extract analytics from the query
        query_lower = search_request.message.lower()
        
        # Detect neighborhoods mentioned
        neighborhoods_mentioned = [n for n in neighborhoods if n.lower() in query_lower]
        
        # Detect bedrooms
        bedrooms_requested = None
        if 'studio' in query_lower:
            bedrooms_requested = 0
        elif '1 bed' in query_lower or '1br' in query_lower or 'one bed' in query_lower:
            bedrooms_requested = 1
        elif '2 bed' in query_lower or '2br' in query_lower or 'two bed' in query_lower:
            bedrooms_requested = 2
        elif '3 bed' in query_lower or '3br' in query_lower or 'three bed' in query_lower:
            bedrooms_requested = 3
        
        # Detect price range
        price_match = re.findall(r'\$?(\d{1,2}),?(\d{3})', query_lower)
        price_range = None
        if price_match:
            prices = [int(p[0] + p[1]) for p in price_match]
            price_range = {'min': min(prices), 'max': max(prices)} if len(prices) > 1 else {'target': prices[0]}
        
        # Count matching units for analytics
        units_found = 0
        for unit in units:
            matches = True
            if bedrooms_requested is not None and unit.get('bedrooms') != bedrooms_requested:
                matches = False
            if neighborhoods_mentioned and unit.get('neighborhood', '').lower() not in [n.lower() for n in neighborhoods_mentioned]:
                matches = False
            if price_range:
                rent = unit.get('rent', 0)
                if 'min' in price_range and 'max' in price_range:
                    if rent < price_range['min'] or rent > price_range['max']:
                        matches = False
                elif 'target' in price_range:
                    if abs(rent - price_range['target']) > 1000:
                        matches = False
            if matches:
                units_found += 1
        
        # Save search to database
        search_record = {
            'id': str(uuid.uuid4()),
            'session_id': session_id,
            'user_id': user.id if user else None,
            'user_email': user_email,
            'query': search_request.message,
            'response': response,
            'units_found': units_found,
            'neighborhoods_mentioned': neighborhoods_mentioned,
            'price_range': price_range,
            'bedrooms_requested': bedrooms_requested,
            'google_search_used': google_context.get('search_performed', False),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.ai_searches.insert_one(search_record)
        
        return {
            'response': response,
            'session_id': session_id,
            'units_found': units_found,
            'google_grounded': google_context.get('search_performed', False)
        }
        
    except Exception as e:
        logger.error(f"AI Search error: {e}")
        # Fallback response
        return {
            'response': f"I apologize, but I'm having trouble processing your request right now. Please contact me directly at (646) 408-8048 or placesfirm@gmail.com for personalized apartment search assistance!",
            'session_id': search_request.session_id or str(uuid.uuid4()),
            'units_found': 0
        }

@api_router.get("/admin/ai-searches")
async def get_ai_searches(user: User = Depends(require_admin), limit: int = 100):
    """Get AI search history for admin review"""
    searches = await db.ai_searches.find(
        {},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    return searches

@api_router.get("/admin/search-analytics")
async def get_search_analytics(user: User = Depends(require_admin)):
    """Get AI search analytics for admin dashboard"""
    
    # Total searches
    total_searches = await db.ai_searches.count_documents({})
    
    # Searches in last 24 hours
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent_searches = await db.ai_searches.count_documents({
        'created_at': {'$gte': yesterday.isoformat()}
    })
    
    # Get all searches for analytics
    all_searches = await db.ai_searches.find({}, {'_id': 0}).to_list(1000)
    
    # Most searched neighborhoods
    neighborhood_counts = {}
    for search in all_searches:
        for n in search.get('neighborhoods_mentioned', []):
            neighborhood_counts[n] = neighborhood_counts.get(n, 0) + 1
    top_neighborhoods = sorted(neighborhood_counts.items(), key=lambda x: -x[1])[:10]
    
    # Bedroom preferences
    bedroom_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for search in all_searches:
        br = search.get('bedrooms_requested')
        if br is not None and br in bedroom_counts:
            bedroom_counts[br] += 1
    
    # Price range analysis
    price_searches = [s for s in all_searches if s.get('price_range')]
    avg_target_price = 0
    if price_searches:
        prices = []
        for s in price_searches:
            pr = s.get('price_range', {})
            if 'target' in pr:
                prices.append(pr['target'])
            elif 'min' in pr and 'max' in pr:
                prices.append((pr['min'] + pr['max']) / 2)
        avg_target_price = sum(prices) / len(prices) if prices else 0
    
    # Searches with no matches
    no_match_searches = len([s for s in all_searches if s.get('units_found', 0) == 0])
    
    return {
        'total_searches': total_searches,
        'searches_last_24h': recent_searches,
        'top_neighborhoods': [{'name': n, 'count': c} for n, c in top_neighborhoods],
        'bedroom_preferences': {
            'studio': bedroom_counts[0],
            'one_bed': bedroom_counts[1],
            'two_bed': bedroom_counts[2],
            'three_plus': bedroom_counts[3]
        },
        'avg_target_price': round(avg_target_price, 0),
        'no_match_rate': round(no_match_searches / total_searches * 100, 1) if total_searches > 0 else 0
    }

# ============ PROPERTY SEARCH & IMPORT ============

class PropertySearchRequest(BaseModel):
    query: str
    search_type: str = "all"  # "all", "management_companies", "custom"
    
class PropertyCrawlRequest(BaseModel):
    url: str
    building_name: Optional[str] = None

class PropertyImportRequest(BaseModel):
    building: dict
    units: List[dict]

# Known management companies with their property/availability URLs
MANAGEMENT_COMPANIES = [
    # === ORIGINAL 12 ===
    {
        "name": "Two Trees Management",
        "website": "https://www.twotreesny.com",
        "availability_url": "https://www.twotreesny.com/availabilities",
        "neighborhoods": ["DUMBO", "Williamsburg", "Brooklyn"],
        "description": "Major Brooklyn developer with luxury no-fee buildings"
    },
    {
        "name": "Rose Associates",
        "website": "https://www.roseassociates.com",
        "availability_url": "https://www.roseassociates.com/availabilities",
        "neighborhoods": ["Manhattan", "Multiple"],
        "description": "Large NYC property manager with diverse portfolio"
    },
    {
        "name": "TF Cornerstone",
        "website": "https://www.tfcornerstone.com",
        "availability_url": "https://www.tfcornerstone.com/apartments",
        "neighborhoods": ["Long Island City", "Manhattan", "Brooklyn"],
        "description": "Major developer in LIC and Manhattan waterfront"
    },
    {
        "name": "Manhattan Skyline",
        "website": "https://www.manhattanskyline.com",
        "availability_url": "https://www.manhattanskyline.com/availability",
        "neighborhoods": ["Chelsea", "Midtown", "Financial District"],
        "description": "Luxury Manhattan no-fee apartments"
    },
    {
        "name": "Gotham Organization",
        "website": "https://www.gothamorg.com",
        "availability_url": "https://www.gothamorg.com/availabilities",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "NYC developer with multiple luxury buildings"
    },
    {
        "name": "Brookfield Properties",
        "website": "https://www.brookfieldproperties.com",
        "availability_url": "https://www.brookfieldproperties.com/en/properties.html",
        "neighborhoods": ["Manhattan", "Multiple"],
        "description": "Major commercial and residential developer"
    },
    {
        "name": "Related Companies",
        "website": "https://www.related.com",
        "availability_url": "https://www.related.com/rentals",
        "neighborhoods": ["Hudson Yards", "Manhattan"],
        "description": "Hudson Yards developer with luxury rentals"
    },
    {
        "name": "Extell Development",
        "website": "https://www.extelldev.com",
        "availability_url": "https://www.extelldev.com/rentals",
        "neighborhoods": ["Manhattan", "Upper West Side"],
        "description": "Luxury Manhattan high-rise developer"
    },
    {
        "name": "LeFrak",
        "website": "https://www.lefrak.com",
        "availability_url": "https://www.lefrak.com/residential",
        "neighborhoods": ["Jersey City", "Queens"],
        "description": "Major developer in Jersey City and Queens"
    },
    {
        "name": "Avalon Bay",
        "website": "https://www.avaloncommunities.com",
        "availability_url": "https://www.avaloncommunities.com/new-york",
        "neighborhoods": ["Multiple NYC Areas"],
        "description": "National apartment developer with NYC presence"
    },
    {
        "name": "Equity Residential",
        "website": "https://www.equityapartments.com",
        "availability_url": "https://www.equityapartments.com/new-york-city",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "Large national REIT with NYC properties"
    },
    {
        "name": "The Durst Organization",
        "website": "https://www.durst.org",
        "availability_url": "https://www.durst.org/residential",
        "neighborhoods": ["Midtown", "Financial District"],
        "description": "Historic NYC developer and property manager"
    },
    # === NEW ADDITIONS ===
    {
        "name": "Silverstein Properties",
        "website": "https://www.silversteinproperties.com",
        "availability_url": "https://www.silversteinproperties.com/residential",
        "neighborhoods": ["Financial District", "WTC", "Manhattan"],
        "description": "World Trade Center developer with luxury residential"
    },
    {
        "name": "SL Green",
        "website": "https://www.slgreen.com",
        "availability_url": "https://www.slgreen.com/properties/residential",
        "neighborhoods": ["Midtown", "Manhattan"],
        "description": "NYC's largest office landlord with residential portfolio"
    },
    {
        "name": "Rockrose Development",
        "website": "https://www.rockrose.com",
        "availability_url": "https://www.rockrose.com/residences",
        "neighborhoods": ["Long Island City", "Manhattan"],
        "description": "Major LIC developer with waterfront properties"
    },
    {
        "name": "Moinian Group",
        "website": "https://www.moinian.com",
        "availability_url": "https://www.moinian.com/residential",
        "neighborhoods": ["Hudson Yards", "Midtown", "Manhattan"],
        "description": "Sky and other luxury Manhattan developments"
    },
    {
        "name": "L+M Development",
        "website": "https://www.lmdevpartners.com",
        "availability_url": "https://www.lmdevpartners.com/portfolio",
        "neighborhoods": ["Harlem", "Brooklyn", "Bronx"],
        "description": "Affordable and market-rate housing developer"
    },
    {
        "name": "Toll Brothers City Living",
        "website": "https://www.tollbrothers.com/city-living",
        "availability_url": "https://www.tollbrothers.com/city-living/new-york",
        "neighborhoods": ["Manhattan", "Brooklyn", "Jersey City"],
        "description": "Luxury condo and rental developer"
    },
    {
        "name": "Property Markets Group (PMG)",
        "website": "https://www.propertymg.com",
        "availability_url": "https://www.propertymg.com/properties",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "Boutique luxury developer in NYC"
    },
    {
        "name": "Hines",
        "website": "https://www.hines.com",
        "availability_url": "https://www.hines.com/properties?region=new-york",
        "neighborhoods": ["Manhattan", "Multiple"],
        "description": "Global real estate firm with NYC residential"
    },
    {
        "name": "Tishman Speyer",
        "website": "https://www.tishmanspeyer.com",
        "availability_url": "https://www.tishmanspeyer.com/rentals",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "Major developer - Rockefeller Center owners"
    },
    {
        "name": "Stonehenge NYC",
        "website": "https://www.stonehengenyc.com",
        "availability_url": "https://www.stonehengenyc.com/apartments",
        "neighborhoods": ["Midtown", "Upper East Side", "Manhattan"],
        "description": "Boutique Manhattan apartment operator"
    },
    {
        "name": "Glenwood Management",
        "website": "https://www.glenwoodnyc.com",
        "availability_url": "https://www.glenwoodnyc.com/available-apartments",
        "neighborhoods": ["Upper East Side", "Midtown", "FiDi"],
        "description": "Luxury Manhattan high-rise apartments"
    },
    {
        "name": "Brodsky Organization",
        "website": "https://www.brodsky.com",
        "availability_url": "https://www.brodsky.com/rentals",
        "neighborhoods": ["Upper West Side", "Manhattan"],
        "description": "Family-owned Manhattan apartment operator"
    },
    {
        "name": "UDR",
        "website": "https://www.udr.com",
        "availability_url": "https://www.udr.com/new-york-city-apartments",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "National REIT with luxury NYC apartments"
    },
    {
        "name": "Bozzuto",
        "website": "https://www.bozzuto.com",
        "availability_url": "https://www.bozzuto.com/apartments/region/new-york",
        "neighborhoods": ["Jersey City", "Hoboken", "NYC Area"],
        "description": "Property manager with NJ and NYC presence"
    },
    {
        "name": "Ironstate Development",
        "website": "https://www.ironstate.com",
        "availability_url": "https://www.ironstate.com/portfolio",
        "neighborhoods": ["Jersey City", "Hoboken"],
        "description": "Major Jersey City waterfront developer"
    },
    {
        "name": "Mack-Cali (Veris Residential)",
        "website": "https://www.verisresidential.com",
        "availability_url": "https://www.verisresidential.com/apartments",
        "neighborhoods": ["Jersey City", "Weehawken", "NJ Waterfront"],
        "description": "NJ waterfront luxury apartment developer"
    },
    {
        "name": "Applied Companies",
        "website": "https://www.appliedcompanies.com",
        "availability_url": "https://www.appliedcompanies.com/communities",
        "neighborhoods": ["Hoboken", "Jersey City"],
        "description": "NJ luxury apartment communities"
    }
]

# Pattern recognition keywords for no-fee buildings
NO_FEE_PATTERNS = [
    "no fee", "no broker fee", "no broker", "owner pays fee", 
    "net effective", "free rent", "lease-up", "new construction",
    "luxury rental", "luxury apartments", "direct from owner",
    "in-house leasing", "on-site leasing", "management company"
]

# Areas to focus discovery searches
DISCOVERY_AREAS = [
    {"area": "Manhattan", "neighborhoods": ["Chelsea", "Tribeca", "FiDi", "Midtown", "UWS", "UES", "Hudson Yards", "Harlem"]},
    {"area": "Brooklyn", "neighborhoods": ["DUMBO", "Williamsburg", "Brooklyn Heights", "Fort Greene", "Greenpoint", "Downtown Brooklyn"]},
    {"area": "Queens", "neighborhoods": ["Long Island City", "Astoria", "Flushing"]},
    {"area": "New Jersey", "neighborhoods": ["Jersey City", "Hoboken", "Weehawken", "Harrison", "Newark"]},
    {"area": "Pennsylvania", "neighborhoods": ["Philadelphia"]}
]

@api_router.get("/admin/management-companies")
async def get_management_companies(user: User = Depends(require_admin)):
    """Get list of known management companies for quick search."""
    return {
        "companies": MANAGEMENT_COMPANIES,
        "total": len(MANAGEMENT_COMPANIES)
    }

@api_router.post("/admin/property-search")
async def property_search(request: PropertySearchRequest, user: User = Depends(require_admin)):
    """
    AI-powered property search that finds building websites using SerpApi.
    Prioritizes known management companies and filters aggregators.
    """
    from serpapi import GoogleSearch
    import asyncio
    
    serpapi_key = os.environ.get('SERPAPI_KEY')
    if not serpapi_key:
        raise HTTPException(status_code=500, detail="SerpApi not configured. Add SERPAPI_KEY to environment.")
    
    try:
        buildings = []
        
        # If searching management companies, return the curated list
        if request.search_type == "management_companies":
            for company in MANAGEMENT_COMPANIES:
                buildings.append({
                    "name": company["name"],
                    "url": company["availability_url"],
                    "domain": company["website"].replace("https://", "").replace("http://", ""),
                    "snippet": f"{company['description']}. Areas: {', '.join(company['neighborhoods'])}",
                    "source": "curated_management_company",
                    "is_management_company": True
                })
            return {
                "query": request.query,
                "results": buildings,
                "total_found": len(buildings),
                "search_type": "management_companies"
            }
        
        loop = asyncio.get_event_loop()
        
        # Enhanced search query with management company patterns
        management_terms = "Two Trees OR Rose Associates OR TF Cornerstone OR Manhattan Skyline OR Gotham OR Related OR Extell OR LeFrak"
        search_query = f"{request.query} ({management_terms}) apartments availability -streeteasy -zillow"
        
        def execute_search():
            search = GoogleSearch({
                "q": search_query,
                "api_key": serpapi_key,
                "num": 20,
                "gl": "us",
                "hl": "en"
            })
            return search.get_dict()
        
        results = await loop.run_in_executor(None, execute_search)
        
        organic_results = results.get("organic_results", [])
        
        # Filter and structure results
        seen_domains = set()
        
        # Skip aggregators and non-building sites (Trulia removed - we now have a dedicated scraper)
        skip_domains = ['streeteasy', 'zillow', 'apartments.com', 'realtor', 
                      'apartmentguide', 'rent.com', 'hotpads', 'facebook', 'instagram',
                      'youtube', 'twitter', 'linkedin', 'yelp', 'wikipedia', 'craigslist',
                      'reddit', 'pinterest', 'glassdoor', 'indeed', 'nytimes', 'curbed']
        
        # Priority domains from management companies
        priority_domains = ['twotreesny.com', 'roseassociates.com', 'tfcornerstone.com', 
                          'manhattanskyline.com', 'gothamorg.com', 'related.com',
                          'extelldev.com', 'lefrak.com', 'durst.org', 'brookfieldproperties.com']
        
        priority_results = []
        other_results = []
        
        for result in organic_results:
            link = result.get("link", "")
            domain = result.get("displayed_link", "").split("/")[0] if result.get("displayed_link") else ""
            
            if any(skip in domain.lower() for skip in skip_domains):
                continue
            
            if domain in seen_domains:
                continue
            seen_domains.add(domain)
            
            # Check if it looks like a building/property website
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            
            property_terms = ['apartment', 'rental', 'residence', 'living', 'lease', 'rent', 
                            'bedroom', 'studio', 'availability', 'no fee', 'no broker']
            
            if any(term in title or term in snippet for term in property_terms):
                building_data = {
                    "name": result.get("title", "Unknown Building"),
                    "url": link,
                    "domain": domain,
                    "snippet": result.get("snippet", ""),
                    "source": "google_search",
                    "is_management_company": any(pd in domain.lower() for pd in priority_domains)
                }
                
                # Prioritize management company results
                if building_data["is_management_company"]:
                    priority_results.append(building_data)
                else:
                    other_results.append(building_data)
        
        # Combine with priority results first
        buildings = priority_results + other_results
        
        return {
            "query": request.query,
            "results": buildings[:15],
            "total_found": len(buildings),
            "search_type": "web_search",
            "priority_count": len(priority_results)
        }
        
    except Exception as e:
        logger.error(f"Property search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

class DiscoverySearchRequest(BaseModel):
    area: str = "all"  # "Manhattan", "Brooklyn", "Queens", "New Jersey", "all"
    search_new_construction: bool = True
    search_net_effective: bool = True
    
@api_router.post("/admin/property-discovery")
async def property_discovery(request: DiscoverySearchRequest, user: User = Depends(require_admin)):
    """
    AI-powered discovery search to find NEW no-fee buildings and management companies.
    Uses pattern recognition to identify potential no-fee sources.
    """
    from serpapi import GoogleSearch
    import asyncio
    
    serpapi_key = os.environ.get('SERPAPI_KEY')
    if not serpapi_key:
        raise HTTPException(status_code=500, detail="SerpApi not configured.")
    
    try:
        all_results = []
        loop = asyncio.get_event_loop()
        
        # Build discovery queries based on area
        discovery_queries = []
        
        if request.area == "all":
            areas = ["Manhattan NYC", "Brooklyn NYC", "Queens NYC", "Jersey City NJ", "Hoboken NJ"]
        else:
            areas = [request.area]
        
        for area in areas:
            # Query 1: New construction
            if request.search_new_construction:
                discovery_queries.append(f"new luxury rental building {area} 2024 2025 no fee apartments")
            
            # Query 2: Net effective / lease-up specials
            if request.search_net_effective:
                discovery_queries.append(f"no broker fee luxury apartments {area} net effective rent")
            
            # Query 3: Management company search
            discovery_queries.append(f"luxury apartment management company {area} availability rentals")
        
        # Skip aggregators (Trulia removed - we now have a dedicated scraper)
        skip_domains = ['streeteasy', 'zillow', 'apartments.com', 'realtor', 
                      'apartmentguide', 'rent.com', 'hotpads', 'facebook', 'instagram',
                      'youtube', 'twitter', 'linkedin', 'yelp', 'wikipedia', 'craigslist',
                      'reddit', 'pinterest', 'nytimes', 'curbed', 'timeout', 'thrillist']
        
        # Known management domains for priority
        known_domains = [c['website'].replace('https://', '').replace('http://', '').replace('www.', '') 
                        for c in MANAGEMENT_COMPANIES]
        
        seen_domains = set()
        priority_results = []
        new_discoveries = []
        
        # Execute searches (limit to avoid rate limits)
        for query in discovery_queries[:6]:
            def execute_search(q=query):
                search = GoogleSearch({
                    "q": q,
                    "api_key": serpapi_key,
                    "num": 10,
                    "gl": "us",
                    "hl": "en"
                })
                return search.get_dict()
            
            try:
                results = await loop.run_in_executor(None, execute_search)
                organic_results = results.get("organic_results", [])
                
                for result in organic_results:
                    link = result.get("link", "")
                    domain = result.get("displayed_link", "").split("/")[0] if result.get("displayed_link") else ""
                    domain_clean = domain.replace("www.", "").lower()
                    
                    # Skip aggregators
                    if any(skip in domain_clean for skip in skip_domains):
                        continue
                    
                    if domain_clean in seen_domains:
                        continue
                    seen_domains.add(domain_clean)
                    
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    combined_text = (title + " " + snippet).lower()
                    
                    # Pattern recognition score
                    pattern_score = 0
                    matched_patterns = []
                    
                    for pattern in NO_FEE_PATTERNS:
                        if pattern in combined_text:
                            pattern_score += 1
                            matched_patterns.append(pattern)
                    
                    # Check for property-related terms
                    property_terms = ['apartment', 'rental', 'residence', 'living', 'bedroom', 'studio', 'availability']
                    if any(term in combined_text for term in property_terms):
                        pattern_score += 1
                    
                    # Must have some relevance
                    if pattern_score == 0:
                        continue
                    
                    building_data = {
                        "name": title,
                        "url": link,
                        "domain": domain,
                        "snippet": snippet,
                        "pattern_score": pattern_score,
                        "matched_patterns": matched_patterns,
                        "is_known_company": domain_clean in known_domains,
                        "source": "discovery"
                    }
                    
                    if building_data["is_known_company"]:
                        priority_results.append(building_data)
                    else:
                        new_discoveries.append(building_data)
                        
            except Exception as search_error:
                logger.warning(f"Discovery search error for query '{query}': {search_error}")
                continue
        
        # Sort new discoveries by pattern score
        new_discoveries.sort(key=lambda x: x["pattern_score"], reverse=True)
        
        # Combine: known companies first, then new discoveries
        all_results = priority_results + new_discoveries
        
        return {
            "area": request.area,
            "results": all_results[:20],
            "total_found": len(all_results),
            "known_company_count": len(priority_results),
            "new_discovery_count": len(new_discoveries),
            "queries_executed": len(discovery_queries[:6])
        }
        
    except Exception as e:
        logger.error(f"Discovery search error: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

@api_router.get("/admin/discovery-areas")
async def get_discovery_areas(user: User = Depends(require_admin)):
    """Get available discovery areas and their neighborhoods."""
    return {
        "areas": DISCOVERY_AREAS,
        "patterns": NO_FEE_PATTERNS
    }

@api_router.post("/admin/property-crawl")
async def property_crawl(request: PropertyCrawlRequest, user: User = Depends(require_admin)):
    """
    Crawl a building website to extract property data.
    Returns structured building and unit information for preview.
    """
    import httpx
    from bs4 import BeautifulSoup
    import re
    
    try:
        # Fetch the page
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = await client.get(request.url, headers=headers)
            response.raise_for_status()
            html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract building info
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Look for address patterns
        address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Place|Pl|Drive|Dr|Lane|Ln|Way)[\w\s,]*(?:NY|NJ|PA|New York|New Jersey|Pennsylvania)?[\s,]*\d{5}?'
        address_matches = re.findall(address_pattern, soup.get_text(), re.IGNORECASE)
        address = address_matches[0] if address_matches else ""
        
        # Extract neighborhood from common patterns
        neighborhood = ""
        neighborhood_patterns = ['Chelsea', 'Tribeca', 'DUMBO', 'Williamsburg', 'Long Island City', 
                                'Financial District', 'Midtown', 'Upper West Side', 'Upper East Side',
                                'Brooklyn Heights', 'Fort Greene', 'Astoria', 'Jersey City', 'Hoboken',
                                'Harrison', 'SoHo', 'West Village', 'East Village', 'Harlem', 'Murray Hill']
        page_text = soup.get_text().lower()
        for n in neighborhood_patterns:
            if n.lower() in page_text:
                neighborhood = n
                break
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '') or img.get('data-src', '')
            if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'button', 'arrow', 'sprite']):
                # Make absolute URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(request.url)
                    src = f"{parsed.scheme}://{parsed.netloc}{src}"
                elif not src.startswith('http'):
                    from urllib.parse import urljoin
                    src = urljoin(request.url, src)
                
                if src not in images:
                    images.append(src)
        
        # Extract units/apartments info
        units = []
        
        # Look for pricing patterns
        price_pattern = r'\$[\d,]+(?:\s*[-–]\s*\$[\d,]+)?(?:/mo|/month)?'
        prices = re.findall(price_pattern, soup.get_text())
        
        # Look for bedroom patterns
        bed_pattern = r'(\d+)\s*(?:bed|bedroom|br)|studio'
        beds = re.findall(bed_pattern, soup.get_text(), re.IGNORECASE)
        
        # Look for unit numbers
        unit_pattern = r'(?:unit|apt|apartment|#)\s*([A-Za-z0-9-]+)'
        unit_nums = re.findall(unit_pattern, soup.get_text(), re.IGNORECASE)
        
        # Try to find availability tables or listings
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join(cell.get_text() for cell in cells)
                
                # Check if row contains apartment info
                if any(term in row_text.lower() for term in ['bed', 'studio', 'rent', '$']):
                    price_match = re.search(r'\$[\d,]+', row_text)
                    bed_match = re.search(r'(\d+)\s*(?:bed|br)|studio', row_text, re.IGNORECASE)
                    unit_match = re.search(r'(?:unit|apt|#)?\s*([A-Za-z0-9-]+)', row_text, re.IGNORECASE)
                    
                    if price_match:
                        unit_data = {
                            'unit_number': unit_match.group(1) if unit_match else f"Unit-{len(units)+1}",
                            'rent': int(price_match.group().replace('$', '').replace(',', '')),
                            'bedrooms': int(bed_match.group(1)) if bed_match and bed_match.group(1) else 0,
                            'bathrooms': 1,
                            'images': images[:5] if images else []
                        }
                        units.append(unit_data)
        
        # If no units found from tables, create sample units from extracted prices
        if not units and prices:
            for i, price in enumerate(prices[:5]):
                price_clean = int(re.sub(r'[^\d]', '', price.split('-')[0].split('/')[0]))
                if 1000 < price_clean < 50000:  # Reasonable rent range
                    units.append({
                        'unit_number': f"Unit-{i+1}",
                        'rent': price_clean,
                        'bedrooms': int(beds[i]) if i < len(beds) and beds[i].isdigit() else 1,
                        'bathrooms': 1,
                        'images': images[i*2:(i+1)*2] if images else []
                    })
        
        building_data = {
            'name': request.building_name or title_text.split('|')[0].split('-')[0].strip(),
            'address': address,
            'neighborhood': neighborhood,
            'city': 'New York' if 'NY' in address.upper() else 'Unknown',
            'state': 'NY' if 'NY' in address.upper() else ('NJ' if 'NJ' in address.upper() else 'Unknown'),
            'source_url': request.url,
            'images': images[:10]
        }
        
        return {
            'building': building_data,
            'units': units,
            'raw_images': images[:20],
            'crawl_status': 'success',
            'units_found': len(units)
        }
        
    except Exception as e:
        logger.error(f"Property crawl error: {e}")
        return {
            'building': {
                'name': request.building_name or 'Unknown Building',
                'source_url': request.url
            },
            'units': [],
            'crawl_status': 'partial',
            'error': str(e),
            'message': 'Could not automatically extract data. Please enter manually.'
        }

@api_router.post("/admin/property-import")
async def property_import(request: PropertyImportRequest, user: User = Depends(require_admin)):
    """
    Import crawled property data to staging for review.
    """
    try:
        batch_id = f"import-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        
        # Create staging building
        building_data = {
            'id': str(uuid.uuid4()),
            'name': request.building['name'],
            'address': request.building.get('address', ''),
            'neighborhood': request.building.get('neighborhood', ''),
            'city': request.building.get('city', 'New York'),
            'state': request.building.get('state', 'NY'),
            'zip_code': request.building.get('zip_code', ''),
            'source_url': request.building.get('source_url', ''),
            'images': request.building.get('images', []),
            'crawler_source': request.building.get('source_url', ''),
            'crawler_batch_id': batch_id,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.buildings_staging.insert_one(building_data)
        
        # Create staging units
        units_created = 0
        for unit in request.units:
            unit_data = {
                'id': str(uuid.uuid4()),
                'building_id': building_data['id'],
                'unit_number': unit.get('unit_number', f"Unit-{units_created+1}"),
                'rent': unit.get('rent', 0),
                'bedrooms': unit.get('bedrooms', 0),
                'bathrooms': unit.get('bathrooms', 1),
                'square_feet': unit.get('square_feet'),
                'amenities': unit.get('amenities', []),
                'images': unit.get('images', []),
                'description': unit.get('description', ''),
                'is_available': True,
                'crawler_source': request.building.get('source_url', ''),
                'crawler_batch_id': batch_id,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            await db.units_staging.insert_one(unit_data)
            units_created += 1
        
        return {
            'success': True,
            'building_id': building_data['id'],
            'units_created': units_created,
            'batch_id': batch_id,
            'message': f"Successfully imported {building_data['name']} with {units_created} units to staging."
        }
        
    except Exception as e:
        logger.error(f"Property import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# Note: Router is included after all routes are defined (see below)

# ============ DATABASE SEEDING ENDPOINT ============

@api_router.post("/admin/seed-database")
async def admin_seed_database(
    force: bool = Query(False, description="Force re-seed even if data exists"),
    is_admin: bool = Depends(require_admin)
):
    """
    Admin endpoint to seed the database with buildings and units data.
    Use force=true to overwrite existing data.
    """
    if not SEED_MODULE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database seeding module not available"
        )
    
    try:
        result = await seed_database(force=force)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Database seeding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/seed-status")
async def admin_seed_status(is_admin: bool = Depends(require_admin)):
    """Check the current database status and available seed data."""
    try:
        current_buildings = await db.buildings.count_documents({})
        current_units = await db.units.count_documents({})
        
        seed_info = {"available": False, "buildings": 0, "units": 0}
        if SEED_MODULE_AVAILABLE:
            try:
                buildings_data, units_data = await load_seed_data()
                seed_info = {
                    "available": True,
                    "buildings": len(buildings_data),
                    "units": len(units_data)
                }
            except:
                pass
        
        return {
            "current_database": {
                "buildings": current_buildings,
                "units": current_units
            },
            "seed_data": seed_info,
            "needs_seeding": current_buildings < seed_info.get("buildings", 0) or current_units < seed_info.get("units", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def create_indexes():
    """Create database indexes for query optimization"""
    try:
        # Use comprehensive index creation script
        try:
            from create_indexes import create_indexes as create_all_indexes, ensure_geospatial_field
            
            # Ensure geospatial fields are set
            await ensure_geospatial_field(db)
            
            # Create all indexes
            results = await create_all_indexes(db)
            logger.info(f"Database indexes: {len(results['created'])} created, {len(results['already_exists'])} already existed")
            
            if results['errors']:
                for err in results['errors'][:3]:  # Log first 3 errors
                    logger.warning(f"Index creation warning: {err}")
        except ImportError:
            # Fallback to basic indexes if script not available
            logger.warning("Index creation script not available, using basic indexes")
            
            # Units collection indexes
            await db.units.create_index([("building_id", 1)])
            await db.units.create_index([("is_available", 1)])
            await db.units.create_index([("bedrooms", 1)])
            await db.units.create_index([("rent", 1)])
            await db.units.create_index([("lifecycle_status", 1)])
            
            # Buildings collection indexes
            await db.buildings.create_index([("neighborhood", 1)])
            await db.buildings.create_index([("city", 1)])
            await db.buildings.create_index([("normalized_address", 1)], sparse=True)
            
            # User sessions indexes
            await db.user_sessions.create_index([("session_token", 1)], unique=True)
            await db.user_sessions.create_index([("expires_at", 1)])
            
            # Staging collections indexes
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
        
        buildings_data, units_data = await load_seed_data()
        
        # Only auto-seed if database has significantly fewer records
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

# ============ UNIT LIFECYCLE MANAGEMENT ROUTES ============

class LifecycleStatusInput(BaseModel):
    """Input model for updating unit lifecycle status"""
    status: str  # available, rented, unavailable
    rent: Optional[float] = None
    available_date: Optional[str] = None
    notes: Optional[str] = None

class BulkLifecycleInput(BaseModel):
    """Input model for bulk lifecycle operations"""
    unit_ids: List[str]
    notes: Optional[str] = None

@api_router.get("/admin/lifecycle/stats")
async def get_lifecycle_stats(user: User = Depends(require_admin)):
    """Get lifecycle statistics for all units"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = get_lifecycle_service(db)
    return await service.get_lifecycle_stats()

@api_router.post("/admin/lifecycle/check-stale")
async def trigger_stale_check(user: User = Depends(require_admin)):
    """Manually trigger stale units check"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = get_lifecycle_service(db)
    result = await service.check_and_mark_stale_units()
    
    logger.info(f"Manual stale check triggered by {user.email}: {result['units_marked_stale']} units marked")
    return result

@api_router.get("/admin/lifecycle/stale-units")
async def get_stale_units(
    limit: int = Query(100, le=500),
    user: User = Depends(require_admin)
):
    """Get all units currently marked as stale"""
    stale_units = await db.units.find(
        {'lifecycle_status': 'stale'},
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    # Get building info for context
    if stale_units:
        building_ids = list(set(u.get('building_id') for u in stale_units if u.get('building_id')))
        buildings = await db.buildings.find({'id': {'$in': building_ids}}, {"_id": 0}).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
        
        for unit in stale_units:
            unit['building'] = buildings_map.get(unit.get('building_id'))
    
    return {
        'count': len(stale_units),
        'units': stale_units
    }

@api_router.get("/admin/lifecycle/rented-units")
async def get_rented_units(
    limit: int = Query(100, le=500),
    user: User = Depends(require_admin)
):
    """Get all units currently marked as rented"""
    rented_units = await db.units.find(
        {'lifecycle_status': 'rented'},
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    return {
        'count': len(rented_units),
        'units': rented_units
    }

@api_router.put("/admin/lifecycle/unit/{unit_id}/status")
async def update_unit_lifecycle_status(
    unit_id: str,
    input: LifecycleStatusInput,
    user: User = Depends(require_admin)
):
    """Update a unit's lifecycle status"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = get_lifecycle_service(db)
    
    if input.status == 'rented':
        result = await service.mark_unit_as_rented(
            unit_id=unit_id,
            notes=input.notes,
            changed_by=user.id
        )
    elif input.status == 'available':
        result = await service.mark_unit_as_available(
            unit_id=unit_id,
            rent=input.rent,
            available_date=input.available_date,
            notes=input.notes,
            changed_by=user.id
        )
    elif input.status == 'unavailable':
        # Mark as unavailable
        await service._record_status_change(
            unit_id=unit_id,
            old_status=(await db.units.find_one({'id': unit_id}, {"_id": 0, "lifecycle_status": 1})).get('lifecycle_status', 'available'),
            new_status='unavailable',
            source='manual',
            changed_by=user.id,
            reason=input.notes
        )
        await db.units.update_one(
            {'id': unit_id},
            {
                '$set': {
                    'is_available': False,
                    'lifecycle_status': 'unavailable',
                    'lifecycle_updated_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        result = {'success': True, 'unit_id': unit_id, 'new_status': 'unavailable'}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid status: {input.status}. Use: available, rented, unavailable")
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Operation failed'))
    
    logger.info(f"Unit {unit_id} lifecycle status updated to {input.status} by {user.email}")
    return result

@api_router.put("/admin/lifecycle/unit/{unit_id}/price")
async def update_unit_price(
    unit_id: str,
    new_price: float = Query(..., gt=0),
    reason: Optional[str] = None,
    user: User = Depends(require_admin)
):
    """Update a unit's rent price (with history tracking)"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = get_lifecycle_service(db)
    result = await service.update_unit_price(
        unit_id=unit_id,
        new_price=new_price,
        source='manual',
        changed_by=user.id,
        reason=reason
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Operation failed'))
    
    logger.info(f"Unit {unit_id} price updated to ${new_price} by {user.email}")
    return result

@api_router.get("/admin/lifecycle/unit/{unit_id}/history")
async def get_unit_history(unit_id: str, user: User = Depends(require_admin)):
    """Get full history for a unit (price changes + status changes)"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = get_lifecycle_service(db)
    return await service.get_unit_full_history(unit_id)

@api_router.post("/admin/lifecycle/bulk-refresh")
async def bulk_refresh_stale_units(
    input: BulkLifecycleInput,
    user: User = Depends(require_admin)
):
    """Refresh multiple stale units (mark as available again)"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = get_lifecycle_service(db)
    result = await service.refresh_stale_units(
        unit_ids=input.unit_ids,
        changed_by=user.id
    )
    
    logger.info(f"Bulk refresh: {result['refreshed_count']} units refreshed by {user.email}")
    return result

@api_router.post("/admin/lifecycle/bulk-mark-rented")
async def bulk_mark_units_rented(
    input: BulkLifecycleInput,
    user: User = Depends(require_admin)
):
    """Mark multiple units as rented"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = get_lifecycle_service(db)
    result = await service.bulk_mark_rented(
        unit_ids=input.unit_ids,
        changed_by=user.id,
        notes=input.notes
    )
    
    logger.info(f"Bulk mark rented: {result['marked_rented_count']} units by {user.email}")
    return result

# ============ SITEMAP ROUTE ============

@api_router.get("/sitemap.xml", response_class=PlainTextResponse)
async def get_sitemap():
    """Generate and serve dynamic sitemap.xml for SEO"""
    try:
        from sitemap_generator import generate_sitemap
        
        # Get all available units
        units = await db.units.find(
            {'is_available': True},
            {"_id": 0, "id": 1, "updated_at": 1, "created_at": 1}
        ).to_list(1000)
        
        # Get all buildings for location pages
        buildings = await db.buildings.find(
            {},
            {"_id": 0, "neighborhood": 1, "city": 1}
        ).to_list(1000)
        
        # Always use production URL for sitemap (SEO purposes)
        base_url = 'https://www.nofeesapts.com'
        
        # Generate sitemap
        sitemap_xml = generate_sitemap(units, buildings, base_url)
        
        logger.info(f"Sitemap generated with {len(units)} units and {len(buildings)} buildings")
        
        return PlainTextResponse(
            content=sitemap_xml,
            media_type="application/xml"
        )
    except Exception as e:
        logger.error(f"Error generating sitemap: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate sitemap")

@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots():
    """Serve robots.txt for search engines"""
    # Always use production URL for robots.txt (with www to match Google Search Console)
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

# ============ FACEBOOK INTEGRATION ============

# Import Facebook service
FACEBOOK_SERVICE_AVAILABLE = False
try:
    from facebook_service import FacebookService
    facebook_service = FacebookService()
    FACEBOOK_SERVICE_AVAILABLE = True
    logger.info("Facebook service initialized successfully")
except Exception as e:
    FACEBOOK_SERVICE_AVAILABLE = False
    logger.warning(f"Facebook service not available: {e}")

def format_listing_for_facebook(unit: dict) -> tuple:
    """Format apartment listing data for Facebook post."""
    # Build the main message
    message = f"{unit.get('unit_number', 'Apartment')} at {unit.get('address', 'Address')}\n\n"
    message += f"📍 {unit.get('city', '')}, {unit.get('state', '')} {unit.get('zip_code', '')}\n"
    message += f"💰 ${unit.get('rent', 0):,.0f}/month\n"
    message += f"🛏️ {unit.get('bedrooms', 0)} bed • 🛁 {unit.get('bathrooms', 0)} bath"
    
    if unit.get('square_feet'):
        message += f" • {unit['square_feet']} sq ft"
    
    message += "\n\n"
    
    if unit.get('amenities'):
        amenities_list = unit['amenities'][:5]
        message += "✨ Amenities: " + ", ".join(amenities_list) + "\n\n"
    
    if unit.get('description'):
        description = unit['description'][:200] + "..." if len(unit['description']) > 200 else unit['description']
        message += f"{description}\n\n"
    
    message += "✅ NO FEE APARTMENT\n\n"
    message += "🔗 View full listing and apply: "
    
    # Extract photo URLs
    photo_urls = unit.get('images', [])
    
    # Build listing URL
    listing_url = f"https://nofeesapts.com/unit/{unit['id']}"
    
    return message, photo_urls, listing_url

@api_router.post("/facebook/post-listing")
async def post_listing_to_facebook(
    unit_id: str,
    is_admin: bool = Depends(require_admin)
):
    """Post a single apartment listing to Facebook Business Page."""
    if not FACEBOOK_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Facebook service not configured"
        )
    
    try:
        # Get the unit
        unit = await db.units.find_one({"id": unit_id}, {"_id": 0})
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        
        # Format for Facebook
        message, photo_urls, listing_url = format_listing_for_facebook(unit)
        
        # Post to Facebook
        if not photo_urls:
            # Use placeholder if no photos
            result = await facebook_service.post_with_single_photo(
                message=message + listing_url,
                photo_url="https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80",
                link=listing_url
            )
        elif len(photo_urls) == 1:
            # Single photo post
            result = await facebook_service.post_with_single_photo(
                message=message + listing_url,
                photo_url=photo_urls[0],
                link=listing_url
            )
        else:
            # Multi-photo post
            result = await facebook_service.post_with_multiple_photos(
                message=message + listing_url,
                photo_urls=photo_urls,
                link=listing_url
            )
        
        # Extract post ID
        post_id = result.get("id") or result.get("post_id")
        
        # Mark as posted
        await db.units.update_one(
            {"id": unit_id},
            {
                "$set": {
                    "posted_to_facebook": True,
                    "facebook_post_id": post_id,
                    "facebook_posted_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "post_id": post_id,
            "unit_id": unit_id,
            "message": "Posted successfully to Facebook"
        }
        
    except Exception as e:
        logger.error(f"Error posting to Facebook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error posting to Facebook: {str(e)}"
        )

@api_router.post("/facebook/post-listings-batch")
async def post_multiple_listings_to_facebook(
    unit_ids: List[str],
    is_admin: bool = Depends(require_admin)
):
    """Post multiple apartment listings to Facebook in batch."""
    if not FACEBOOK_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Facebook service not configured"
        )
    
    results = []
    errors = []
    
    for unit_id in unit_ids:
        try:
            unit = await db.units.find_one({"id": unit_id}, {"_id": 0})
            if not unit:
                errors.append({"unit_id": unit_id, "error": "Unit not found"})
                continue
            
            message, photo_urls, listing_url = format_listing_for_facebook(unit)
            
            # Post based on photo count
            if len(photo_urls) <= 1:
                photo_url = photo_urls[0] if photo_urls else "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80"
                result = await facebook_service.post_with_single_photo(
                    message=message + listing_url,
                    photo_url=photo_url,
                    link=listing_url
                )
            else:
                result = await facebook_service.post_with_multiple_photos(
                    message=message + listing_url,
                    photo_urls=photo_urls,
                    link=listing_url
                )
            
            post_id = result.get("id") or result.get("post_id")
            
            # Mark as posted
            await db.units.update_one(
                {"id": unit_id},
                {
                    "$set": {
                        "posted_to_facebook": True,
                        "facebook_post_id": post_id,
                        "facebook_posted_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            results.append({
                "unit_id": unit_id,
                "post_id": post_id,
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Error posting unit {unit_id}: {str(e)}")
            errors.append({"unit_id": unit_id, "error": str(e)})
    
    return {
        "total": len(unit_ids),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }

@api_router.delete("/facebook/post/{post_id}")
async def delete_facebook_post(
    post_id: str,
    is_admin: bool = Depends(require_admin)
):
    """Delete a Facebook post."""
    if not FACEBOOK_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Facebook service not configured"
        )
    
    try:
        success = await facebook_service.delete_post(post_id)
        if success:
            return {"success": True, "message": "Post deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete post")
    except Exception as e:
        logger.error(f"Error deleting post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ INCLUDE ROUTER AND MIDDLEWARE ============
# Note: This MUST be after all routes are defined
app.include_router(api_router)

# Mount static files for uploaded images
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# app.add_middleware(
#     CORSMiddleware,
#     allow_credentials=True,
#     allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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
            asyncio.run(run_stale_check(db))
            logger.info("Scheduled stale check completed")
        else:
            logger.warning("Lifecycle service not available, skipping stale check")
    except Exception as e:
        logger.error(f"Scheduled stale check error: {e}")

async def process_saved_search_alerts():
    """Process saved search alerts and send email notifications"""
    from smtp_email_service import send_saved_search_alert_email
    
    logger.info("Processing saved search alerts...")
    
    try:
        # Get all active saved searches
        searches = await db.saved_searches.find({
            'is_active': True
        }).to_list(1000)
        
        alerts_sent = 0
        
        for search in searches:
            try:
                # Build query for matching units
                query = {'is_available': True}
                
                if search.get('bedrooms') is not None:
                    query['bedrooms'] = search['bedrooms']
                if search.get('min_rent'):
                    query['rent'] = query.get('rent', {})
                    query['rent']['$gte'] = search['min_rent']
                if search.get('max_rent'):
                    query['rent'] = query.get('rent', {})
                    query['rent']['$lte'] = search['max_rent']
                if search.get('bathrooms'):
                    query['bathrooms'] = search['bathrooms']
                
                # Get units created since last check
                last_checked = search.get('last_checked_at')
                if last_checked:
                    if isinstance(last_checked, str):
                        last_checked_dt = datetime.fromisoformat(last_checked)
                    else:
                        last_checked_dt = last_checked
                    query['created_at'] = {'$gt': last_checked_dt.isoformat()}
                else:
                    # First time - only get units from last 24 hours
                    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
                    query['created_at'] = {'$gt': yesterday.isoformat()}
                
                # Get matching units excluding already notified
                notified_ids = search.get('notified_unit_ids', [])
                if notified_ids:
                    query['id'] = {'$nin': notified_ids}
                
                units = await db.units.find(query, {"_id": 0}).limit(20).to_list(20)
                
                # Filter by state/neighborhood if specified (requires building lookup)
                if search.get('state') or search.get('neighborhood'):
                    building_query = {}
                    if search.get('state'):
                        building_query['state'] = search['state']
                    if search.get('neighborhood'):
                        building_query['neighborhood'] = {'$regex': search['neighborhood'], '$options': 'i'}
                    
                    if building_query:
                        buildings = await db.buildings.find(building_query, {"_id": 0}).to_list(1000)
                        building_ids = {b['id'] for b in buildings}
                        units = [u for u in units if u.get('building_id') in building_ids]
                
                if units:
                    # Enrich units with building data
                    for unit in units:
                        building = await db.buildings.find_one(
                            {'id': unit.get('building_id')}, 
                            {"_id": 0}
                        )
                        unit['building'] = building
                    
                    # Get user info
                    user = await db.users.find_one({'id': search['user_id']})
                    user_name = user.get('name', 'Apartment Hunter') if user else 'Apartment Hunter'
                    
                    # Send email
                    search_criteria = {
                        'bedrooms': search.get('bedrooms'),
                        'min_rent': search.get('min_rent'),
                        'max_rent': search.get('max_rent'),
                        'state': search.get('state'),
                        'neighborhood': search.get('neighborhood')
                    }
                    
                    # Send notifications based on user preferences
                    notification_sent = False
                    
                    # Send email if enabled
                    if search.get('notify_email', True):
                        email_sent = send_saved_search_alert_email(
                            user_email=search['user_email'],
                            user_name=user_name,
                            search_name=search['name'],
                            matching_units=units,
                            search_criteria=search_criteria
                        )
                        if email_sent:
                            notification_sent = True
                            logger.info(f"Email alert sent to {search['user_email']} for search '{search['name']}'")
                    
                    # Send SMS if enabled and phone number available
                    if search.get('notify_sms') and search.get('user_phone') and SMS_SERVICE_AVAILABLE:
                        sms_sent = send_saved_search_alert_sms(
                            phone_number=search['user_phone'],
                            search_name=search['name'],
                            matching_units=units
                        )
                        if sms_sent:
                            notification_sent = True
                            logger.info(f"SMS alert sent to {search['user_phone']} for search '{search['name']}'")
                    
                    if notification_sent:
                        alerts_sent += 1
                        # Update search with notified units
                        new_notified_ids = notified_ids + [u['id'] for u in units]
                        await db.saved_searches.update_one(
                            {'id': search['id']},
                            {
                                '$set': {
                                    'last_checked_at': datetime.now(timezone.utc).isoformat(),
                                    'last_alert_sent': datetime.now(timezone.utc).isoformat(),
                                    'notified_unit_ids': new_notified_ids[-100]  # Keep last 100
                                }
                            }
                        )
                        logger.info(f"Alerts sent for search '{search['name']}' with {len(units)} units")
                else:
                    # No new matches, just update last_checked
                    await db.saved_searches.update_one(
                        {'id': search['id']},
                        {'$set': {'last_checked_at': datetime.now(timezone.utc).isoformat()}}
                    )
            
            except Exception as e:
                logger.error(f"Error processing search {search.get('id')}: {e}")
                continue
        
        logger.info(f"Saved search alerts completed: {alerts_sent} alerts sent")
        return alerts_sent
    
    except Exception as e:
        logger.error(f"Error in saved search alerts job: {e}")
        return 0

def scheduled_saved_search_alerts_job():
    """Run saved search alerts daily"""
    import asyncio
    
    logger.info("Starting scheduled saved search alerts...")
    try:
        alerts_sent = asyncio.run(process_saved_search_alerts())
        logger.info(f"Scheduled saved search alerts completed: {alerts_sent} alerts sent")
    except Exception as e:
        logger.error(f"Scheduled saved search alerts error: {e}")

# Schedule crawl every 48 hours
scheduler.add_job(
    scheduled_crawl_job,
    trigger=IntervalTrigger(hours=48),
    id='crawl_job',
    replace_existing=True
)

# Schedule stale check daily at 6 AM
scheduler.add_job(
    scheduled_stale_check_job,
    trigger=IntervalTrigger(hours=24),
    id='stale_check_job',
    replace_existing=True
)

# Schedule saved search alerts every 6 hours
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
