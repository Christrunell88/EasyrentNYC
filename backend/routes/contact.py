"""Contact, subscribe, share, and services routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timezone
import uuid
import os
import logging

from database import db
from models import User, ContactRequest, ContactInput, EmailSubscribeInput, ShareUnitInput
from auth_utils import require_auth, require_admin
from services import EMAIL_SERVICE_AVAILABLE, smtp_service, SMS_SERVICE_AVAILABLE, CALENDAR_SERVICE_AVAILABLE

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/services/status")
async def get_services_status():
    """Get status of external services"""
    return {
        'email_service': EMAIL_SERVICE_AVAILABLE,
        'sms_service': SMS_SERVICE_AVAILABLE,
        'calendar_service': CALENDAR_SERVICE_AVAILABLE
    }

# ============ CONTACT ROUTES ============

@router.post("/contact")
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

@router.get("/contact")
async def get_contact_requests(user: User = Depends(require_admin)):
    """Get all contact requests (admin only)"""
    contacts = await db.contact_requests.find({}, {"_id": 0}).sort('created_at', -1).to_list(1000)
    return contacts

@router.get("/contact-requests")
async def get_contact_requests_alias(user: User = Depends(require_admin)):
    """Get all contact requests (admin only) - alias for /contact"""
    contacts = await db.contact_requests.find({}, {"_id": 0}).sort('created_at', -1).to_list(1000)
    return contacts

@router.post("/subscribe")
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

@router.post("/share-unit")
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
