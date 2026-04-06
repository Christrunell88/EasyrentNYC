"""
Twilio SMS Service for NoFeesApts.com
Handles SMS notifications for apartment listing alerts
"""

import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

twilio_client = None
TWILIO_ENABLED = False

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        TWILIO_ENABLED = True
        logger.info("Twilio SMS service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")
else:
    logger.warning("Twilio credentials not configured. SMS notifications disabled.")


def format_phone_number(phone: str) -> str:
    """Ensure phone number is in E.164 format"""
    # Remove any spaces, dashes, or parentheses
    phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Add + if not present and assume US number
    if not phone.startswith('+'):
        if phone.startswith('1') and len(phone) == 11:
            phone = '+' + phone
        elif len(phone) == 10:
            phone = '+1' + phone
        else:
            phone = '+' + phone
    
    return phone


def send_sms(to_phone: str, message: str) -> bool:
    """
    Send an SMS message
    
    Args:
        to_phone: Phone number in E.164 format (e.g., +14155552671)
        message: Message body (max 1600 characters)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not TWILIO_ENABLED:
        logger.warning("SMS not sent - Twilio not configured")
        return False
    
    try:
        formatted_phone = format_phone_number(to_phone)
        
        # Truncate message if too long
        if len(message) > 1600:
            message = message[:1597] + "..."
        
        result = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_phone
        )
        
        logger.info(f"SMS sent to {formatted_phone}: SID={result.sid}")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio error sending SMS to {to_phone}: {e.code} - {e.msg}")
        return False
    except Exception as e:
        logger.error(f"Error sending SMS to {to_phone}: {e}")
        return False


def send_saved_search_alert_sms(
    phone_number: str,
    search_name: str,
    matching_units: list,
    frontend_url: str = "https://nofeesapts.com"
) -> bool:
    """
    Send SMS alert for new matching apartments
    
    Args:
        phone_number: User's phone number
        search_name: Name of the saved search
        matching_units: List of matching unit objects
        frontend_url: Frontend URL for links
    
    Returns:
        bool: True if sent successfully
    """
    if not matching_units:
        return False
    
    count = len(matching_units)
    
    # Build concise message (SMS has char limits)
    if count == 1:
        unit = matching_units[0]
        building_name = unit.get('building', {}).get('name', 'New Building')
        rent = unit.get('rent', 0)
        beds = "Studio" if unit.get('bedrooms', 0) == 0 else f"{unit.get('bedrooms')}BR"
        
        message = (
            f"🏠 NoFeesApts Alert!\n"
            f"New match for '{search_name}':\n"
            f"{building_name}\n"
            f"{beds} • ${rent:,.0f}/mo\n"
            f"View: {frontend_url}/unit/{unit.get('id')}"
        )
    else:
        # Multiple units - summarize
        min_rent = min(u.get('rent', 0) for u in matching_units)
        max_rent = max(u.get('rent', 0) for u in matching_units)
        
        message = (
            f"🏠 NoFeesApts Alert!\n"
            f"{count} new apartments match '{search_name}'!\n"
            f"Rent range: ${min_rent:,.0f}-${max_rent:,.0f}/mo\n"
            f"View all: {frontend_url}/dashboard"
        )
    
    return send_sms(phone_number, message)


def send_viewing_confirmation_sms(
    phone_number: str,
    building_name: str,
    unit_number: str,
    viewing_date: str,
    viewing_time: str
) -> bool:
    """
    Send SMS confirmation for scheduled viewing
    
    Args:
        phone_number: User's phone number
        building_name: Name of the building
        unit_number: Unit number
        viewing_date: Date of viewing
        viewing_time: Time of viewing
    
    Returns:
        bool: True if sent successfully
    """
    message = (
        f"✅ Viewing Confirmed!\n"
        f"📍 {building_name}\n"
        f"Unit: {unit_number}\n"
        f"📅 {viewing_date} at {viewing_time}\n"
        f"We'll send a reminder 1 hour before."
    )
    
    return send_sms(phone_number, message)


def send_viewing_reminder_sms(
    phone_number: str,
    building_name: str,
    unit_number: str,
    viewing_time: str,
    address: str
) -> bool:
    """
    Send SMS reminder before viewing
    
    Args:
        phone_number: User's phone number
        building_name: Name of the building
        unit_number: Unit number
        viewing_time: Time of viewing
        address: Building address
    
    Returns:
        bool: True if sent successfully
    """
    message = (
        f"⏰ Viewing Reminder!\n"
        f"Your viewing at {building_name} (Unit {unit_number}) is in 1 hour.\n"
        f"📍 {address}\n"
        f"Time: {viewing_time}"
    )
    
    return send_sms(phone_number, message)


def is_sms_enabled() -> bool:
    """Check if SMS service is available"""
    return TWILIO_ENABLED
