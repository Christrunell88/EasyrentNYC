"""Saved searches and social proof routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import logging

from database import db
from models import User, SavedSearch, SavedSearchInput
from auth_utils import require_auth, require_admin
from services import SMS_SERVICE_AVAILABLE
from alert_tasks import process_saved_search_alerts

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/saved-searches")
async def get_saved_searches(user: User = Depends(require_auth)):
    """Get user's saved searches"""
    searches = await db.saved_searches.find(
        {'user_id': user.id},
        {"_id": 0}
    ).sort('created_at', -1).to_list(100)
    return searches

@router.post("/saved-searches")
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

@router.put("/saved-searches/{search_id}")
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

@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(search_id: str, user: User = Depends(require_auth)):
    """Delete a saved search"""
    result = await db.saved_searches.delete_one({'id': search_id, 'user_id': user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saved search not found")
    return {'message': 'Saved search deleted'}

@router.put("/saved-searches/{search_id}/toggle")
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

@router.post("/admin/trigger-search-alerts")
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

@router.get("/social-proof")
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
