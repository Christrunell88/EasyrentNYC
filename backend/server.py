from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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

class StagingBulkReviewInput(BaseModel):
    """Input model for bulk reviewing staging items"""
    ids: List[str]
    review_status: str  # "approved" or "rejected"
    reviewer_notes: Optional[str] = None

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
    
    # Create production unit (exclude staging-specific fields)
    production_unit = {
        "id": str(uuid.uuid4()),
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
    
    # Mark staging as promoted
    await db.units_staging.update_one(
        {"id": unit_id},
        {"$set": {"review_status": "promoted", "matched_production_id": production_unit["id"]}}
    )
    
    return {
        "message": "Unit promoted to production",
        "staging_id": unit_id,
        "production_id": production_unit["id"]
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
        "recent_batch_ids": recent_batches[-10:] if recent_batches else []
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
    
    # Step 2: Check for duplicates in production (prevent double insertion)
    # Use normalized unit number if available
    normalized_unit = staged_unit.get("normalized_unit_number", staged_unit["unit_number"])
    
    existing_unit = await db.units.find_one({
        "building_id": production_building_id,
        "$or": [
            {"unit_number": staged_unit["unit_number"]},
            {"unit_number": normalized_unit}
        ]
    }, {"_id": 0, "id": 1, "unit_number": 1})
    
    if existing_unit:
        # Update staging status to rejected with duplicate info
        await db.units_staging.update_one(
            {"id": unit_id},
            {
                "$set": {
                    "review_status": "rejected",
                    "reviewer_notes": f"Duplicate of production unit {existing_unit['id']} (unit {existing_unit['unit_number']})",
                    "matched_production_id": existing_unit["id"],
                    "reviewed_by": user.id,
                    "reviewed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        raise HTTPException(
            status_code=409,
            detail=f"Unit already exists in production: {existing_unit['unit_number']} (ID: {existing_unit['id']})"
        )
    
    # Step 3: Create production unit
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
        "message": "Unit approved and moved to production",
        "staging_id": unit_id,
        "production_id": production_unit_id,
        "building_id": production_building_id,
        "unit_number": staged_unit["unit_number"],
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

# ============ PROMOTION SERVICE ENDPOINTS ============

@api_router.post("/staging/promote/{unit_id}")
async def promote_staging_unit(
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
    """AI-powered apartment search agent"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import re
    import json
    
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
        
        # Create system prompt
        system_prompt = f"""You are the NoFeesApts.com AI Search Assistant - a friendly, knowledgeable apartment search expert for NYC, Northern NJ, and PA no-fee apartments.

CURRENT INVENTORY:
- {total_units} no-fee apartments available across {total_buildings} buildings
- Price range: ${min_rent:,.0f} - ${max_rent:,.0f}/month
- Neighborhoods: {', '.join(neighborhoods[:15])}

YOUR CAPABILITIES:
1. Search our database of {total_units} verified no-fee listings
2. Answer questions about NYC neighborhoods, apartment hunting tips, and the rental market
3. Help users find apartments that match their criteria (budget, bedrooms, location, amenities)
4. For requests outside our current inventory, mention that Chris can help find additional options

CONTACT INFORMATION (Always provide when relevant):
- Phone: (646) 408-8048
- Email: placesfirm@gmail.com
- Name: Chris

RESPONSE STYLE:
- Be conversational, helpful, and enthusiastic
- When showing results, be specific about unit details
- If no exact matches, suggest alternatives or mention contacting Chris
- For off-site searches or special requests, always direct to Chris
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
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.ai_searches.insert_one(search_record)
        
        return {
            'response': response,
            'session_id': session_id,
            'units_found': units_found
        }
        
    except Exception as e:
        logger.error(f"AI Search error: {e}")
        # Fallback response
        return {
            'response': f"I apologize, but I'm having trouble processing your request right now. Please contact Chris directly at (646) 408-8048 or placesfirm@gmail.com for personalized apartment search assistance!",
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
    return {
        'message': f"Successfully set {featured_count} units as featured",
        'featured_unit_ids': unit_ids
    }

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
        # Units collection indexes
        await db.units.create_index([("building_id", 1)])
        await db.units.create_index([("is_available", 1)])
        await db.units.create_index([("bedrooms", 1)])
        await db.units.create_index([("rent", 1)])
        
        # Favorites collection indexes
        await db.favorites.create_index([("user_id", 1)])
        await db.favorites.create_index([("unit_id", 1)])
        await db.favorites.create_index([("user_id", 1), ("unit_id", 1)], unique=True)
        
        # Buildings collection indexes
        await db.buildings.create_index([("neighborhood", 1)])
        await db.buildings.create_index([("city", 1)])
        
        # User sessions indexes
        await db.user_sessions.create_index([("session_token", 1)], unique=True)
        await db.user_sessions.create_index([("expires_at", 1)])
        
        # Password resets indexes
        await db.password_resets.create_index([("token", 1)], unique=True)
        await db.password_resets.create_index([("expires_at", 1)])
        
        # Staging collections indexes
        await db.buildings_staging.create_index([("id", 1)], unique=True)
        await db.buildings_staging.create_index([("review_status", 1)])
        await db.buildings_staging.create_index([("crawler_batch_id", 1)])
        await db.buildings_staging.create_index([("crawler_source", 1)])
        await db.buildings_staging.create_index([("duplicate_score", -1)])
        
        await db.units_staging.create_index([("id", 1)], unique=True)
        await db.units_staging.create_index([("building_id", 1)])
        await db.units_staging.create_index([("review_status", 1)])
        await db.units_staging.create_index([("crawler_batch_id", 1)])
        await db.units_staging.create_index([("crawler_source", 1)])
        await db.units_staging.create_index([("duplicate_score", -1)])
        
        # Price and status change history indexes
        await db.price_changes.create_index([("unit_id", 1)])
        await db.price_changes.create_index([("changed_at", -1)])
        await db.price_changes.create_index([("unit_id", 1), ("changed_at", -1)])
        
        await db.status_changes.create_index([("unit_id", 1)])
        await db.status_changes.create_index([("changed_at", -1)])
        await db.status_changes.create_index([("unit_id", 1), ("changed_at", -1)])
        
        logger.info("Database indexes created successfully (including staging and history collections)")
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

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    logger.info("Scheduler started - crawling every 48 hours, stale check daily")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
