"""Auth routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Request, Response, Depends, BackgroundTasks
from datetime import datetime, timezone, timedelta
import uuid
import os
import requests
import logging

from database import db
from models import (
    User, UserSession, SignupInput, LoginInput,
    ForgotPasswordInput, ResetPasswordInput, AdminResetPasswordInput
)
from auth_utils import (
    get_current_user, require_auth, require_admin,
    hash_password, verify_password
)
from services import EMAIL_SERVICE_AVAILABLE, smtp_service

logger = logging.getLogger(__name__)
router = APIRouter()

JWT_EXPIRATION_DAYS = 7


@router.post("/auth/signup")
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

    response.set_cookie(
        key='session_token',
        value=session_token,
        httponly=True,
        secure=False,
        samesite='lax',
        max_age=JWT_EXPIRATION_DAYS * 24 * 60 * 60,
        path='/'
    )

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


@router.post("/auth/login")
async def login(input: LoginInput, response: Response, request: Request):
    """JWT-based login with email/password"""
    user_doc = await db.users.find_one({'email': input.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = User(**user_doc)

    if not user.password_hash or not verify_password(input.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

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

    response.set_cookie(
        key='session_token',
        value=session_token,
        httponly=True,
        secure=False,
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


@router.post("/auth/forgot-password")
async def forgot_password(input: ForgotPasswordInput):
    """Send password reset email to user"""
    user_doc = await db.users.find_one({'email': input.email})

    if not user_doc:
        logger.info(f"Password reset requested for non-existent email: {input.email}")
        return {'message': 'If the email exists, a password reset link has been sent'}

    user = User(**user_doc)

    reset_token = str(uuid.uuid4())
    reset_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    await db.password_resets.insert_one({
        'user_id': user.id,
        'token': reset_token,
        'expires_at': reset_expiry.isoformat(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'used': False
    })

    try:
        if EMAIL_SERVICE_AVAILABLE:
            from email_service import get_gmail_service
            import base64
            from email.mime.text import MIMEText

            service = get_gmail_service()
            base_url = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')
            reset_url = f"{base_url}/reset-password?token={reset_token}"

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


@router.post("/auth/reset-password")
async def reset_password(input: ResetPasswordInput):
    """Reset password using token"""
    reset_doc = await db.password_resets.find_one({
        'token': input.token,
        'used': False
    })

    if not reset_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires_at = datetime.fromisoformat(reset_doc['expires_at'])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    new_password_hash = hash_password(input.new_password)
    await db.users.update_one(
        {'id': reset_doc['user_id']},
        {'$set': {'password_hash': new_password_hash}}
    )

    await db.password_resets.update_one(
        {'token': input.token},
        {'$set': {'used': True}}
    )

    logger.info(f"Password reset successful for user {reset_doc['user_id']}")
    return {'message': 'Password reset successful'}


@router.post("/admin/reset-password")
async def admin_reset_password(input: AdminResetPasswordInput, admin: User = Depends(require_admin)):
    """Admin endpoint to reset any user's password"""
    user_doc = await db.users.find_one({'id': input.user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    user = User(**user_doc)

    new_password_hash = hash_password(input.new_password)
    await db.users.update_one(
        {'id': input.user_id},
        {'$set': {'password_hash': new_password_hash}}
    )

    logger.info(f"Admin {admin.email} reset password for user {user.email}")

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


@router.post("/auth/session")
async def create_session_from_oauth(request: Request, response: Response):
    """Process Emergent OAuth session_id"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")

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

    user_doc = await db.users.find_one({'email': oauth_data['email']})

    if not user_doc:
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

    response.set_cookie(
        key='session_token',
        value=session_token,
        httponly=True,
        secure=False,
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


@router.get("/auth/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current user"""
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'picture': user.picture,
        'is_admin': user.is_admin
    }


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get('session_token')
    if session_token:
        await db.user_sessions.delete_many({'session_token': session_token})

    response.delete_cookie(key='session_token', path='/')
    return {'message': 'Logged out'}
