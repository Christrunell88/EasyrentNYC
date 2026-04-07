"""
Authentication utilities for NoFeesApts.
Provides auth dependencies and password hashing.
"""
from fastapi import Request, HTTPException
from typing import Optional
from datetime import datetime, timezone
import bcrypt

from database import db
from models import User


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
