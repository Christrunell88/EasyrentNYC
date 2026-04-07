"""Social media routes - Facebook posting."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import logging

from database import db
from models import User
from auth_utils import require_admin
from services import FACEBOOK_SERVICE_AVAILABLE, facebook_service

logger = logging.getLogger(__name__)
router = APIRouter()

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

@router.post("/facebook/post-listing")
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

@router.post("/facebook/post-listings-batch")
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

@router.delete("/facebook/post/{post_id}")
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
