"""
External service availability flags for NoFeesApts.
Centralized service imports and availability checks.
"""
import logging

logger = logging.getLogger(__name__)

# SMTP Email Service
EMAIL_SERVICE_AVAILABLE = False
smtp_service = None
try:
    from smtp_email_service import smtp_service as _smtp_service
    smtp_service = _smtp_service
    EMAIL_SERVICE_AVAILABLE = True
    logger.info("SMTP email service loaded successfully")
except Exception as e:
    logger.warning(f"Email service not available: {str(e)}")

# Twilio SMS Service
SMS_SERVICE_AVAILABLE = False
sms_functions = {}
try:
    from twilio_sms_service import (
        send_sms, send_saved_search_alert_sms,
        send_viewing_confirmation_sms, is_sms_enabled
    )
    SMS_SERVICE_AVAILABLE = is_sms_enabled()
    sms_functions = {
        'send_sms': send_sms,
        'send_saved_search_alert_sms': send_saved_search_alert_sms,
        'send_viewing_confirmation_sms': send_viewing_confirmation_sms,
    }
    if SMS_SERVICE_AVAILABLE:
        logger.info("Twilio SMS service loaded successfully")
    else:
        logger.warning("Twilio SMS service loaded but not configured")
except Exception as e:
    logger.warning(f"SMS service not available: {str(e)}")

# Google Calendar Service
CALENDAR_SERVICE_AVAILABLE = False
calendar_functions = {}
try:
    from google_calendar_service import (
        get_oauth_authorization_url, exchange_code_for_tokens,
        get_user_email_from_token, create_viewing_event,
        delete_viewing_event, is_calendar_enabled
    )
    CALENDAR_SERVICE_AVAILABLE = is_calendar_enabled()
    calendar_functions = {
        'get_oauth_authorization_url': get_oauth_authorization_url,
        'exchange_code_for_tokens': exchange_code_for_tokens,
        'get_user_email_from_token': get_user_email_from_token,
        'create_viewing_event': create_viewing_event,
        'delete_viewing_event': delete_viewing_event,
    }
    if CALENDAR_SERVICE_AVAILABLE:
        logger.info("Google Calendar service loaded successfully")
    else:
        logger.warning("Google Calendar service loaded but not configured")
except Exception as e:
    logger.warning(f"Calendar service not available: {str(e)}")

# Database Seeding Module
SEED_MODULE_AVAILABLE = False
seed_functions = {}
try:
    from seed_database import seed_database, check_database_status, load_seed_data
    seed_functions = {
        'seed_database': seed_database,
        'check_database_status': check_database_status,
        'load_seed_data': load_seed_data,
    }
    SEED_MODULE_AVAILABLE = True
    logger.info("Database seeding module loaded successfully")
except Exception as e:
    logger.warning(f"Database seeding module not available: {str(e)}")

# Promotion Service
PROMOTION_SERVICE_AVAILABLE = False
promotion_service_functions = {}
try:
    from promotion_service import PromotionService, get_promotion_service
    promotion_service_functions = {
        'PromotionService': PromotionService,
        'get_promotion_service': get_promotion_service,
    }
    PROMOTION_SERVICE_AVAILABLE = True
    logger.info("Promotion service loaded successfully")
except Exception as e:
    logger.warning(f"Promotion service not available: {str(e)}")

# Lifecycle Management Service
LIFECYCLE_SERVICE_AVAILABLE = False
lifecycle_functions = {}
try:
    from lifecycle_service import UnitLifecycleService, get_lifecycle_service, run_stale_check
    lifecycle_functions = {
        'UnitLifecycleService': UnitLifecycleService,
        'get_lifecycle_service': get_lifecycle_service,
        'run_stale_check': run_stale_check,
    }
    LIFECYCLE_SERVICE_AVAILABLE = True
    logger.info("Lifecycle service loaded successfully")
except Exception as e:
    logger.warning(f"Lifecycle service not available: {str(e)}")

# Facebook Service
FACEBOOK_SERVICE_AVAILABLE = False
facebook_service = None
try:
    from facebook_service import FacebookService
    facebook_service = FacebookService()
    FACEBOOK_SERVICE_AVAILABLE = True
    logger.info("Facebook service initialized successfully")
except Exception as e:
    logger.warning(f"Facebook service not available: {e}")
