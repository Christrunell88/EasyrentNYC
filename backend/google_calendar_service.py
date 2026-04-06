"""
Google Calendar Service for NoFeesApts.com
Handles OAuth flow and calendar event creation for apartment viewings
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Google OAuth Configuration
GOOGLE_CALENDAR_CLIENT_ID = os.environ.get('GOOGLE_CALENDAR_CLIENT_ID')
GOOGLE_CALENDAR_CLIENT_SECRET = os.environ.get('GOOGLE_CALENDAR_CLIENT_SECRET')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://nofeesapts.com')

# Scopes for Calendar API
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.email'
]

GOOGLE_CALENDAR_ENABLED = bool(GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET)

if GOOGLE_CALENDAR_ENABLED:
    logger.info("Google Calendar service initialized")
else:
    logger.warning("Google Calendar credentials not configured. Calendar integration disabled.")


def get_oauth_authorization_url(redirect_uri: str, state: str = None) -> Optional[str]:
    """
    Generate Google OAuth authorization URL
    
    Args:
        redirect_uri: Callback URL after authorization
        state: Optional state parameter for CSRF protection
    
    Returns:
        Authorization URL or None if not configured
    """
    if not GOOGLE_CALENDAR_ENABLED:
        return None
    
    params = {
        'client_id': GOOGLE_CALENDAR_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(CALENDAR_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    if state:
        params['state'] = state
    
    query_string = '&'.join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/auth?{query_string}"


def exchange_code_for_tokens(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    """
    Exchange authorization code for access and refresh tokens
    
    Args:
        code: Authorization code from OAuth callback
        redirect_uri: Same redirect URI used in authorization
    
    Returns:
        Token response dict or None on error
    """
    if not GOOGLE_CALENDAR_ENABLED:
        return None
    
    try:
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': GOOGLE_CALENDAR_CLIENT_ID,
                'client_secret': GOOGLE_CALENDAR_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {e}")
        return None


def get_user_email_from_token(access_token: str) -> Optional[str]:
    """
    Get user's email from access token
    
    Args:
        access_token: Google OAuth access token
    
    Returns:
        User's email or None
    """
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code == 200:
            return response.json().get('email')
        return None
        
    except Exception as e:
        logger.error(f"Error getting user email: {e}")
        return None


def get_credentials_from_tokens(tokens: Dict[str, Any]) -> Optional[Credentials]:
    """
    Create Credentials object from stored tokens
    
    Args:
        tokens: Token dict containing access_token and optionally refresh_token
    
    Returns:
        Credentials object or None
    """
    if not tokens or not tokens.get('access_token'):
        return None
    
    try:
        creds = Credentials(
            token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=GOOGLE_CALENDAR_CLIENT_ID,
            client_secret=GOOGLE_CALENDAR_CLIENT_SECRET
        )
        return creds
        
    except Exception as e:
        logger.error(f"Error creating credentials: {e}")
        return None


def refresh_tokens_if_needed(creds: Credentials) -> Optional[Dict[str, Any]]:
    """
    Refresh tokens if expired
    
    Args:
        creds: Credentials object
    
    Returns:
        Updated tokens dict if refreshed, None otherwise
    """
    try:
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            return {
                'access_token': creds.token,
                'refresh_token': creds.refresh_token
            }
        return None
        
    except Exception as e:
        logger.error(f"Error refreshing tokens: {e}")
        return None


def create_viewing_event(
    tokens: Dict[str, Any],
    building_name: str,
    unit_number: str,
    address: str,
    viewing_datetime: datetime,
    duration_minutes: int = 30,
    notes: str = None
) -> Optional[Dict[str, Any]]:
    """
    Create a calendar event for apartment viewing
    
    Args:
        tokens: User's Google OAuth tokens
        building_name: Name of the building
        unit_number: Unit number
        address: Building address
        viewing_datetime: Datetime of the viewing (should be timezone-aware)
        duration_minutes: Duration of viewing in minutes
        notes: Additional notes for the event
    
    Returns:
        Created event data or None on error
    """
    creds = get_credentials_from_tokens(tokens)
    if not creds:
        logger.error("Invalid credentials for calendar event creation")
        return None
    
    try:
        # Refresh if needed
        updated_tokens = refresh_tokens_if_needed(creds)
        if updated_tokens:
            creds = get_credentials_from_tokens(updated_tokens)
        
        service = build('calendar', 'v3', credentials=creds)
        
        # Ensure datetime is timezone-aware
        if viewing_datetime.tzinfo is None:
            viewing_datetime = viewing_datetime.replace(tzinfo=timezone.utc)
        
        end_datetime = viewing_datetime + timedelta(minutes=duration_minutes)
        
        event_body = {
            'summary': f'🏠 Apartment Viewing: {building_name} - Unit {unit_number}',
            'location': address,
            'description': (
                f"Apartment viewing at {building_name}\n"
                f"Unit: {unit_number}\n"
                f"Address: {address}\n\n"
                f"This is a no-fee apartment found on NoFeesApts.com\n"
                f"{f'Notes: {notes}' if notes else ''}"
            ),
            'start': {
                'dateTime': viewing_datetime.isoformat(),
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/New_York'
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},       # 1 hour before
                ]
            }
        }
        
        event = service.events().insert(
            calendarId='primary',
            body=event_body
        ).execute()
        
        logger.info(f"Calendar event created: {event.get('id')}")
        
        return {
            'id': event.get('id'),
            'htmlLink': event.get('htmlLink'),
            'summary': event.get('summary'),
            'start': event.get('start'),
            'end': event.get('end'),
            'updated_tokens': updated_tokens
        }
        
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        return None


def delete_viewing_event(tokens: Dict[str, Any], event_id: str) -> bool:
    """
    Delete a calendar event
    
    Args:
        tokens: User's Google OAuth tokens
        event_id: Google Calendar event ID
    
    Returns:
        True if deleted successfully
    """
    creds = get_credentials_from_tokens(tokens)
    if not creds:
        return False
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        logger.info(f"Calendar event deleted: {event_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}")
        return False


def is_calendar_enabled() -> bool:
    """Check if Google Calendar service is available"""
    return GOOGLE_CALENDAR_ENABLED
