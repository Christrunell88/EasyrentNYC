"""Unit routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import logging
import os

from database import db
from models import User, Unit, UnitInput
from auth_utils import require_auth, require_admin
from services import (
    LIFECYCLE_SERVICE_AVAILABLE, lifecycle_functions,
    PROMOTION_SERVICE_AVAILABLE, promotion_service_functions
)

logger = logging.getLogger(__name__)
router = APIRouter()

def _get_lifecycle_service():
    if LIFECYCLE_SERVICE_AVAILABLE:
        return lifecycle_functions['get_lifecycle_service'](db)
    return None

def _get_promotion_service():
    if PROMOTION_SERVICE_AVAILABLE:
        return promotion_service_functions['get_promotion_service'](db)
    return None

@router.get("/units")
async def get_units(
    neighborhood: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
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
    
    # Get units - prioritize featured units
    # First get featured units
    featured_units = await db.units.find(
        {**query, 'is_featured': True}, 
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    # If we need more units to reach the limit, get regular units
    remaining_limit = limit - len(featured_units)
    if remaining_limit > 0:
        regular_units = await db.units.find(
            {**query, 'is_featured': {'$ne': True}}, 
            {"_id": 0}
        ).limit(remaining_limit).to_list(remaining_limit)
        units = featured_units + regular_units
    else:
        units = featured_units
    
    # If neighborhood, city, or state filter, need to join with buildings
    if neighborhood or city or state:
        building_query = {}
        if neighborhood:
            building_query['neighborhood'] = neighborhood
        if city:
            building_query['city'] = city
        if state:
            building_query['state'] = state
        
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


@router.get("/recommendations")
async def get_recommendations():
    """Get smart filter recommendations based on current inventory"""
    try:
        today = datetime.now(timezone.utc)
        week_ago = today - timedelta(days=7)
        
        # 1. Most Popular Buildings - buildings with most available units
        pipeline_popular = [
            {"$match": {"is_available": True}},
            {"$group": {"_id": "$building_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        popular_results = await db.units.aggregate(pipeline_popular).to_list(5)
        popular_building_ids = [r["_id"] for r in popular_results]
        
        # Get building names
        popular_buildings = []
        if popular_building_ids:
            buildings = await db.buildings.find(
                {"id": {"$in": popular_building_ids}}, 
                {"_id": 0, "id": 1, "name": 1}
            ).to_list(5)
            buildings_map = {b["id"]: b["name"] for b in buildings}
            popular_buildings = [
                {"id": r["_id"], "name": buildings_map.get(r["_id"], "Unknown"), "count": r["count"]}
                for r in popular_results if r["_id"] in buildings_map
            ]
        
        # 2. Best Value - lowest price per square foot (only units with sqft data)
        pipeline_value = [
            {"$match": {"is_available": True, "square_feet": {"$gt": 0}}},
            {"$project": {
                "id": 1,
                "building_id": 1,
                "rent": 1,
                "square_feet": 1,
                "bedrooms": 1,
                "price_per_sqft": {"$divide": ["$rent", "$square_feet"]}
            }},
            {"$sort": {"price_per_sqft": 1}},
            {"$limit": 20}
        ]
        value_units = await db.units.aggregate(pipeline_value).to_list(20)
        avg_price_per_sqft = sum(u["price_per_sqft"] for u in value_units) / len(value_units) if value_units else 0
        value_threshold = avg_price_per_sqft * 0.85  # 15% below average
        best_value_count = len([u for u in value_units if u["price_per_sqft"] <= value_threshold])
        
        # 3. New This Week - units created in last 7 days
        new_count = await db.units.count_documents({
            "is_available": True,
            "created_at": {"$gte": week_ago.isoformat()}
        })
        
        # Also check updated_at for recent updates
        if new_count == 0:
            new_count = await db.units.count_documents({
                "is_available": True,
                "updated_at": {"$gte": week_ago.isoformat()}
            })
        
        # 4. Luxury Picks - high-end apartments ($5k+)
        luxury_count = await db.units.count_documents({
            "is_available": True,
            "rent": {"$gte": 5000}
        })
        
        # 5. Studios - always popular for first-time renters
        studio_count = await db.units.count_documents({
            "is_available": True,
            "bedrooms": 0
        })
        
        # 6. Budget Friendly - under $3k
        budget_count = await db.units.count_documents({
            "is_available": True,
            "rent": {"$lte": 3000}
        })
        
        # 7. Family Size - 2+ bedrooms
        family_count = await db.units.count_documents({
            "is_available": True,
            "bedrooms": {"$gte": 2}
        })
        
        # Total available
        total_available = await db.units.count_documents({"is_available": True})
        
        return {
            "recommendations": [
                {
                    "id": "popular_buildings",
                    "label": "Most Popular Buildings",
                    "description": f"Top {len(popular_buildings)} buildings by listings",
                    "count": sum(b["count"] for b in popular_buildings),
                    "filter": {"building_ids": popular_building_ids},
                    "buildings": popular_buildings[:3],
                    "icon": "building"
                },
                {
                    "id": "best_value",
                    "label": "Best Value",
                    "description": "Lowest $/sq ft",
                    "count": best_value_count,
                    "filter": {"sort": "value"},
                    "threshold": round(value_threshold, 2),
                    "icon": "dollar"
                },
                {
                    "id": "new_this_week",
                    "label": "New This Week",
                    "description": "Added in last 7 days",
                    "count": new_count,
                    "filter": {"new": True},
                    "icon": "sparkle"
                },
                {
                    "id": "luxury",
                    "label": "Luxury Picks",
                    "description": "$5,000+/month",
                    "count": luxury_count,
                    "filter": {"min_rent": 5000},
                    "icon": "crown"
                },
                {
                    "id": "studios",
                    "label": "Studios",
                    "description": "Perfect for singles",
                    "count": studio_count,
                    "filter": {"bedrooms": 0},
                    "icon": "bed"
                },
                {
                    "id": "budget",
                    "label": "Budget Friendly",
                    "description": "Under $3,000/month",
                    "count": budget_count,
                    "filter": {"max_rent": 3000},
                    "icon": "piggy"
                },
                {
                    "id": "family",
                    "label": "Family Size",
                    "description": "2+ bedrooms",
                    "count": family_count,
                    "filter": {"min_bedrooms": 2},
                    "icon": "users"
                }
            ],
            "total_available": total_available,
            "generated_at": today.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return {"recommendations": [], "total_available": 0, "error": str(e)}



@router.get("/units/hero-carousel")
async def get_hero_carousel_units(limit: int = Query(5, le=10)):
    """Get 5 best interior units for hero carousel - prioritizes units with quality images"""
    try:
        # Get units with images, sorted by is_featured first then by number of images
        pipeline = [
            {'$match': {'is_available': True, 'images': {'$exists': True, '$ne': []}}},
            {'$addFields': {'image_count': {'$size': '$images'}}},
            {'$sort': {'is_featured': -1, 'image_count': -1, 'created_at': -1}},
            {'$limit': limit * 3},  # Get more to ensure variety
            {'$project': {'_id': 0}}
        ]
        
        all_units = await db.units.aggregate(pipeline).to_list(limit * 3)
        
        # Select units ensuring variety - one per building
        seen_buildings = set()
        selected_units = []
        
        for unit in all_units:
            building_id = unit.get('building_id')
            if building_id in seen_buildings:
                continue
            seen_buildings.add(building_id)
            selected_units.append(unit)
            if len(selected_units) >= limit:
                break
        
        # Enrich with building data
        enriched_units = []
        for unit in selected_units:
            building = await db.buildings.find_one({'id': unit.get('building_id')}, {"_id": 0})
            unit['building'] = building
            enriched_units.append(unit)
        
        return enriched_units
    except Exception as e:
        logger.error(f"Error getting hero carousel units: {e}")
        return []


@router.get("/units/recent")
async def get_recent_units(limit: int = Query(6, le=20)):
    """Get most recently added units with variety - max one unit per building"""
    try:
        # Get more units than needed to ensure variety
        all_units = await db.units.find(
            {'is_available': True},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit * 5).to_list(limit * 5)
        
        # Select units ensuring variety - one per building
        seen_buildings = set()
        selected_units = []
        
        for unit in all_units:
            building_id = unit.get('building_id')
            
            # Skip if we already have a unit from this building
            if building_id in seen_buildings:
                continue
            
            seen_buildings.add(building_id)
            selected_units.append(unit)
            
            # Stop when we have enough
            if len(selected_units) >= limit:
                break
        
        # If we don't have enough unique buildings, fill with remaining units
        if len(selected_units) < limit:
            for unit in all_units:
                if unit not in selected_units:
                    selected_units.append(unit)
                    if len(selected_units) >= limit:
                        break
        
        # Enrich with building data
        enriched_units = []
        for unit in selected_units:
            building = await db.buildings.find_one({'id': unit.get('building_id')}, {"_id": 0})
            unit['building'] = building
            enriched_units.append(unit)
        
        return enriched_units
    except Exception as e:
        logger.error(f"Error getting recent units: {e}")
        return []



@router.get("/units/{unit_id}")
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

@router.get("/share/{unit_id}", response_class=HTMLResponse)
async def get_share_preview(unit_id: str):
    """Generate HTML page with Open Graph meta tags for social sharing.
    Facebook, LinkedIn, and other crawlers will scrape this page to get the preview."""
    unit = await db.units.find_one({'id': unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    building = await db.buildings.find_one({'id': unit['building_id']}, {"_id": 0})
    
    # Generate content
    bedrooms = unit.get('bedrooms', 0)
    bedroom_text = 'Studio' if bedrooms == 0 else f'{bedrooms} Bedroom' if bedrooms == 1 else f'{bedrooms} Bedrooms'
    rent = unit.get('rent', 0)
    neighborhood = building.get('neighborhood', '') if building else ''
    city = building.get('city', 'NYC') if building else 'NYC'
    building_name = building.get('name', '') if building else ''
    
    # Get first image or use default
    images = unit.get('images', [])
    image_url = images[0] if images else 'https://static.prod-images.emergentagent.com/jobs/809a99b2-794a-4bcc-9110-b50857b9c814/images/669505f9b273977a606a8fe480082945aab2c6997e18616eb33fb32a2c5e4eb9.png'
    
    title = f"{bedroom_text} at {building_name or neighborhood} - ${rent:,}/mo | No Fee"
    description = f"No broker fee {bedroom_text.lower()} apartment for rent in {neighborhood}, {city}. ${rent:,}/month. Save thousands on broker fees! View on NoFeesApts.com"
    canonical_url = f"https://nofeesapts.com/unit/{unit_id}"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:site_name" content="NoFeesApts.com">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{canonical_url}">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image_url}">
    
    <!-- Redirect to actual listing -->
    <meta http-equiv="refresh" content="0;url={canonical_url}">
    <link rel="canonical" href="{canonical_url}">
</head>
<body>
    <p>Redirecting to <a href="{canonical_url}">{title}</a>...</p>
</body>
</html>"""
    
    return HTMLResponse(content=html)

@router.post("/units", response_model=Unit)
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

@router.put("/units/{unit_id}", response_model=Unit)
async def update_unit(unit_id: str, input: UnitInput, user: User = Depends(require_admin)):
    """Update unit (admin only) - tracks price changes automatically"""
    existing = await db.units.find_one({'id': unit_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    old_rent = existing.get('rent', 0)
    new_rent = input.rent
    old_available = existing.get('is_available', True)
    new_available = input.is_available
    
    update_data = input.model_dump()
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Track price changes if rent changed
    if old_rent != new_rent and LIFECYCLE_SERVICE_AVAILABLE:
        service = _get_lifecycle_service()
        await service._record_price_change(
            unit_id=unit_id,
            old_price=old_rent,
            new_price=new_rent,
            source='admin_update',
            changed_by=user.id
        )
        # Clear stale status if price was updated
        if existing.get('lifecycle_status') == 'stale':
            update_data['lifecycle_status'] = 'available'
            update_data['stale_since'] = None
    
    # Track availability/status changes
    if old_available != new_available and LIFECYCLE_SERVICE_AVAILABLE:
        service = _get_lifecycle_service()
        old_status = existing.get('lifecycle_status', 'available')
        # If marked as not available, it could be rented or unavailable
        if not new_available:
            new_status = 'rented' if 'rented' in (input.description or '').lower() else 'unavailable'
        else:
            new_status = 'available'
        
        await service._record_status_change(
            unit_id=unit_id,
            old_status=old_status,
            new_status=new_status,
            source='admin_update',
            changed_by=user.id
        )
        update_data['lifecycle_status'] = new_status
        update_data['lifecycle_updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.units.update_one({'id': unit_id}, {'$set': update_data})
    
    updated = await db.units.find_one({'id': unit_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return updated

@router.patch("/units/{unit_id}/images")
async def update_unit_images(unit_id: str, images: List[str], user: User = Depends(require_admin)):
    """Update unit images only (admin only)"""
    existing = await db.units.find_one({'id': unit_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    await db.units.update_one(
        {'id': unit_id}, 
        {'$set': {'images': images, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'message': 'Images updated', 'unit_id': unit_id, 'image_count': len(images)}

@router.delete("/units/{unit_id}")
async def delete_unit(unit_id: str, user: User = Depends(require_admin)):
    """Delete unit (admin only)"""
    result = await db.units.delete_one({'id': unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {'message': 'Unit deleted'}

@router.get("/units/{unit_id}/price-history")
async def get_unit_price_history(
    unit_id: str,
    limit: int = Query(50, le=200),
    user: User = Depends(require_admin)
):
    """
    Get price change history for a production unit.
    """
    if not PROMOTION_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Promotion service not available")
    
    # Verify unit exists
    unit = await db.units.find_one({"id": unit_id}, {"_id": 0, "id": 1, "unit_number": 1, "rent": 1})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    promotion_service = _get_promotion_service()
    history = await promotion_service.get_unit_price_history(unit_id, limit)
    
    return {
        "unit_id": unit_id,
        "unit_number": unit.get("unit_number"),
        "current_rent": unit.get("rent"),
        "price_history": history,
        "total_changes": len(history)
    }


@router.get("/units/{unit_id}/status-history")
async def get_unit_status_history(
    unit_id: str,
    limit: int = Query(50, le=200),
    user: User = Depends(require_admin)
):
    """
    Get status change history for a production unit.
    """
    if not PROMOTION_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Promotion service not available")
    
    # Verify unit exists
    unit = await db.units.find_one({"id": unit_id}, {"_id": 0, "id": 1, "unit_number": 1, "is_available": 1})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    promotion_service = _get_promotion_service()
    history = await promotion_service.get_unit_status_history(unit_id, limit)
    
    return {
        "unit_id": unit_id,
        "unit_number": unit.get("unit_number"),
        "current_status": "available" if unit.get("is_available", True) else "unavailable",
        "status_history": history,
        "total_changes": len(history)
    }


@router.get("/admin/price-changes")
async def get_all_price_changes(
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    unit_id: Optional[str] = Query(None),
    user: User = Depends(require_admin)
):
    """
    Get all price changes across all units.
    """
    query = {}
    if unit_id:
        query["unit_id"] = unit_id
    
    changes = await db.price_changes.find(query, {"_id": 0}).sort("changed_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.price_changes.count_documents(query)
    
    return {
        "items": changes,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/admin/status-changes")
async def get_all_status_changes(
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    unit_id: Optional[str] = Query(None),
    user: User = Depends(require_admin)
):
    """
    Get all status changes across all units.
    """
    query = {}
    if unit_id:
        query["unit_id"] = unit_id
    
    changes = await db.status_changes.find(query, {"_id": 0}).sort("changed_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.status_changes.count_documents(query)
    
    return {
        "items": changes,
        "total": total,
        "skip": skip,
        "limit": limit
    }
