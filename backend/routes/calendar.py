"""Calendar and viewings routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone
import uuid
import os
import logging

from database import db
from models import User, ScheduleViewingInput
from auth_utils import require_auth
from services import (
    CALENDAR_SERVICE_AVAILABLE, calendar_functions,
    SMS_SERVICE_AVAILABLE, sms_functions
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/calendar/status")
async def get_calendar_status(user: User = Depends(require_auth)):
    """Check if user has connected Google Calendar"""
    user_doc = await db.users.find_one({'id': user.id})
    has_calendar = bool(user_doc and user_doc.get('google_calendar_tokens'))
    
    return {
        'connected': has_calendar,
        'calendar_enabled': CALENDAR_SERVICE_AVAILABLE
    }

@router.get("/calendar/connect")
async def connect_calendar(request: Request, user: User = Depends(require_auth)):
    """Initiate Google Calendar OAuth flow"""
    if not CALENDAR_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Calendar service not configured")
    
    # Get the base URL from request
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/oauth/calendar/callback"
    
    auth_url = calendar_functions['get_oauth_authorization_url'](
        redirect_uri=redirect_uri,
        state=user.id  # Pass user ID as state for callback
    )
    
    if not auth_url:
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")
    
    return {'authorization_url': auth_url}

@router.get("/oauth/calendar/callback")
async def calendar_oauth_callback(code: str, state: str, request: Request):
    """Handle Google Calendar OAuth callback"""
    if not CALENDAR_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Calendar service not configured")
    
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/oauth/calendar/callback"
    
    # Exchange code for tokens
    tokens = calendar_functions['exchange_code_for_tokens'](code, redirect_uri)
    if not tokens:
        # Redirect to frontend with error
        frontend_url = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')
        return RedirectResponse(f"{frontend_url}/dashboard?calendar_error=auth_failed")
    
    # Get user email from token to verify
    token_email = calendar_functions['get_user_email_from_token'](tokens.get('access_token'))
    
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

@router.delete("/calendar/disconnect")
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

@router.post("/viewings/schedule")
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
        event_result = calendar_functions['create_viewing_event'](
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
        sms_functions['send_viewing_confirmation_sms'](
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

@router.get("/viewings")
async def get_user_viewings(user: User = Depends(require_auth)):
    """Get user's scheduled viewings"""
    viewings = await db.viewings.find(
        {'user_id': user.id},
        {"_id": 0}
    ).sort('viewing_datetime', 1).to_list(100)
    
    return viewings

@router.delete("/viewings/{viewing_id}")
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
            calendar_functions['delete_viewing_event'](calendar_tokens, viewing['calendar_event_id'])
    
    # Delete viewing record
    await db.viewings.delete_one({'id': viewing_id})
    
    return {'message': 'Viewing cancelled'}
