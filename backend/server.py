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

# Cookie security settings - secure=True for HTTPS (production), False for HTTP (localhost)
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
IS_PRODUCTION = FRONTEND_URL.startswith('https://')
COOKIE_SECURE = IS_PRODUCTION

# Create the main app
app = FastAPI()
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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
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
        secure=COOKIE_SECURE,  # True for HTTPS, False for HTTP
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
    
    # Get units
    units = await db.units.find(query, {"_id": 0}).limit(limit).to_list(limit)
    
    # If neighborhood or city filter, need to join with buildings
    if neighborhood or city:
        building_query = {}
        if neighborhood:
            building_query['neighborhood'] = neighborhood
        if city:
            building_query['city'] = city
        
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
    """Update unit (admin only)"""
    existing = await db.units.find_one({'id': unit_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    update_data = input.model_dump()
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.units.update_one({'id': unit_id}, {'$set': update_data})
    
    updated = await db.units.find_one({'id': unit_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return updated

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
            'active': True
        }
        
        await db.email_subscribers.insert_one(subscriber)
        
        logger.info(f"New email subscriber: {input.email}")
        
        return {'success': True, 'message': 'Successfully subscribed!'}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")

@api_router.post("/share-unit")
async def share_unit(input: ShareUnitInput, user: User = Depends(require_auth)):
    """Share apartment unit via email"""
    # Get unit details
    unit = await db.units.find_one({'id': input.unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Get building info
    building = None
    if unit.get('building_id'):
        building = await db.buildings.find_one({'id': unit['building_id']}, {"_id": 0})
    
    # Send share email
    try:
        if EMAIL_SERVICE_AVAILABLE:
            from email_service import get_gmail_service
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            service = get_gmail_service()
            
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
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Check out this {bedrooms} apartment at {building_name} - No Broker Fees!"
            msg['From'] = os.getenv("GMAIL_SENDER_EMAIL", "placesfirm@gmail.com")
            msg['To'] = input.recipient_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Unit {unit['id']} shared by {user.email} to {input.recipient_email}")
            
            return {'message': 'Apartment shared successfully!'}
        else:
            raise HTTPException(status_code=503, detail="Email service unavailable")
    except Exception as e:
        logger.error(f"Failed to share unit: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

# ============ ADMIN ROUTES ============

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

@api_router.get("/admin/stats")
async def get_stats(user: User = Depends(require_admin)):
    """Get platform statistics (admin only)"""
    total_buildings = await db.buildings.count_documents({})
    total_units = await db.units.count_documents({})
    available_units = await db.units.count_documents({'is_available': True})
    total_users = await db.users.count_documents({})
    total_contacts = await db.contact_requests.count_documents({})
    
    return {
        'total_buildings': total_buildings,
        'total_units': total_units,
        'available_units': available_units,
        'total_users': total_users,
        'total_contacts': total_contacts
    }

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# ============ SITEMAP ROUTE ============

@app.get("/sitemap.xml", response_class=PlainTextResponse)
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
        
        # Get base URL from environment or use production URL
        base_url = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')
        
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
    base_url = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')
    
    robots_content = f"""User-agent: *
Allow: /

# Sitemap
Sitemap: {base_url}/sitemap.xml

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

# Schedule crawl every 48 hours
scheduler.add_job(
    scheduled_crawl_job,
    trigger=IntervalTrigger(hours=48),
    id='crawl_job',
    replace_existing=True
)

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    logger.info("Scheduler started - crawling every 48 hours")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
