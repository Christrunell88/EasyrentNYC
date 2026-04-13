"""Admin general routes - stats, users, crawl, neighborhoods, subscribers, featured, seed."""
from fastapi import APIRouter, HTTPException, Depends, Query, Response, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timezone
import logging

from database import db
from models import User
from auth_utils import require_admin
from services import SEED_MODULE_AVAILABLE, seed_functions

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/admin/users")
async def get_users(user: User = Depends(require_admin)):
    """Get all users (admin only) - includes plain text passwords"""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@router.post("/admin/crawl/{building_id}")
async def trigger_crawl(building_id: str, user: User = Depends(require_admin)):
    """Manually trigger crawl for a building (admin only)"""
    building = await db.buildings.find_one({'id': building_id})
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Import crawler here to avoid circular imports
    from crawler import crawl_building
    
    try:
        await crawl_building(building_id)
        return {'message': 'Crawl started'}
    except Exception as e:
        logger.error(f"Crawl error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/crawl-all")
async def trigger_crawl_all(background_tasks: BackgroundTasks, user: User = Depends(require_admin)):
    """Manually trigger crawl for all buildings (admin only)"""
    from crawler import crawl_all_buildings
    
    try:
        # Run crawl in background to avoid timeout
        background_tasks.add_task(crawl_all_buildings)
        return {'message': 'Crawl started for all buildings', 'status': 'running'}
    except Exception as e:
        logger.error(f"Crawl all error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_public_stats(response: Response):
    """Get public platform statistics"""
    # Prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    total_buildings = await db.buildings.count_documents({})
    total_units = await db.units.count_documents({})
    available_units = await db.units.count_documents({'is_available': True})
    
    return {
        'total_buildings': total_buildings,
        'total_units': total_units,
        'available_units': available_units
    }

@router.get("/admin/stats")
async def get_stats(user: User = Depends(require_admin)):
    """Get platform statistics (admin only)"""
    total_buildings = await db.buildings.count_documents({})
    total_units = await db.units.count_documents({})
    available_units = await db.units.count_documents({'is_available': True})
    total_users = await db.users.count_documents({})
    total_contacts = await db.contact_requests.count_documents({})
    total_subscribers = await db.email_subscribers.count_documents({'active': True})
    
    return {
        'total_buildings': total_buildings,
        'total_units': total_units,
        'available_units': available_units,
        'total_users': total_users,
        'total_contacts': total_contacts,
        'total_subscribers': total_subscribers
    }

# ============== NEIGHBORHOOD SEO ENDPOINTS ==============

@router.get("/neighborhoods")
async def get_all_neighborhoods():
    """Get all neighborhoods with stats for SEO pages"""
    pipeline = [
        {"$lookup": {
            "from": "buildings",
            "localField": "building_id",
            "foreignField": "id",
            "as": "building"
        }},
        {"$unwind": "$building"},
        {"$match": {"is_available": True}},
        {"$group": {
            "_id": "$building.neighborhood",
            "count": {"$sum": 1},
            "avg_rent": {"$avg": "$rent"},
            "min_rent": {"$min": "$rent"},
            "max_rent": {"$max": "$rent"},
            "city": {"$first": "$building.city"},
            "state": {"$first": "$building.state"},
            "studios": {"$sum": {"$cond": [{"$eq": ["$bedrooms", 0]}, 1, 0]}},
            "one_beds": {"$sum": {"$cond": [{"$eq": ["$bedrooms", 1]}, 1, 0]}},
            "two_plus_beds": {"$sum": {"$cond": [{"$gte": ["$bedrooms", 2]}, 1, 0]}}
        }},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"count": -1}}
    ]
    
    neighborhoods = await db.units.aggregate(pipeline).to_list(100)
    
    # Add slug for each neighborhood
    result = []
    for n in neighborhoods:
        slug = n['_id'].lower().replace(' ', '-').replace("'", "")
        result.append({
            "name": n['_id'],
            "slug": slug,
            "count": n['count'],
            "avg_rent": round(n['avg_rent']),
            "min_rent": round(n['min_rent']),
            "max_rent": round(n['max_rent']),
            "city": n['city'],
            "state": n['state'],
            "studios": n['studios'],
            "one_beds": n['one_beds'],
            "two_plus_beds": n['two_plus_beds']
        })
    
    return result

@router.get("/neighborhoods/{slug}")
async def get_neighborhood_detail(slug: str):
    """Get detailed neighborhood data including units"""
    # Convert slug back to neighborhood name
    # Try to find matching neighborhood
    all_buildings = await db.buildings.find({}, {"_id": 0, "neighborhood": 1}).to_list(1000)
    neighborhood_name = None
    
    for b in all_buildings:
        if b.get('neighborhood'):
            test_slug = b['neighborhood'].lower().replace(' ', '-').replace("'", "")
            if test_slug == slug:
                neighborhood_name = b['neighborhood']
                break
    
    if not neighborhood_name:
        raise HTTPException(status_code=404, detail="Neighborhood not found")
    
    # Get buildings in this neighborhood
    buildings = await db.buildings.find(
        {"neighborhood": neighborhood_name},
        {"_id": 0}
    ).to_list(100)
    
    building_ids = [b['id'] for b in buildings]
    
    # Get units
    units = await db.units.find(
        {"building_id": {"$in": building_ids}, "is_available": True},
        {"_id": 0}
    ).sort("rent", 1).to_list(500)
    
    # Add building info to units
    building_map = {b['id']: b for b in buildings}
    for unit in units:
        unit['building'] = building_map.get(unit['building_id'], {})
    
    # Calculate stats
    rents = [u['rent'] for u in units if u.get('rent')]
    studios = len([u for u in units if u.get('bedrooms') == 0])
    one_beds = len([u for u in units if u.get('bedrooms') == 1])
    two_plus = len([u for u in units if u.get('bedrooms', 0) >= 2])
    
    # Price breakdown by bedroom type and amenities (doorman/elevator)
    doorman_keywords = {'Doorman', 'Full-Time Doorman', '24 Hour Concierge', 'Concierge'}
    
    def calc_avg(unit_list):
        rents_list = [u['rent'] for u in unit_list if u.get('rent')]
        return round(sum(rents_list) / len(rents_list)) if rents_list else 0
    
    def has_doorman(u):
        return bool(set(u.get('amenities') or []) & doorman_keywords)
    
    def has_elevator(u):
        return 'Elevator' in (u.get('amenities') or [])
    
    price_breakdown = {}
    for br_val, br_key in [(0, 'studio'), (1, 'one_bed'), (2, 'two_bed')]:
        br_units = [u for u in units if u.get('bedrooms') == br_val and u.get('rent')]
        br_doorman = [u for u in br_units if has_doorman(u)]
        br_no_doorman = [u for u in br_units if not has_doorman(u)]
        br_elevator = [u for u in br_units if has_elevator(u)]
        br_no_elevator = [u for u in br_units if not has_elevator(u)]
        
        price_breakdown[br_key] = {
            'count': len(br_units),
            'avg_rent': calc_avg(br_units),
            'min_rent': min((u['rent'] for u in br_units), default=0),
            'max_rent': max((u['rent'] for u in br_units), default=0),
            'doorman': {'count': len(br_doorman), 'avg_rent': calc_avg(br_doorman)},
            'no_doorman': {'count': len(br_no_doorman), 'avg_rent': calc_avg(br_no_doorman)},
            'elevator': {'count': len(br_elevator), 'avg_rent': calc_avg(br_elevator)},
            'no_elevator': {'count': len(br_no_elevator), 'avg_rent': calc_avg(br_no_elevator)},
        }
    
    # Overall doorman/elevator counts
    total_doorman = len([u for u in units if has_doorman(u)])
    total_elevator = len([u for u in units if has_elevator(u)])
    
    return {
        "name": neighborhood_name,
        "slug": slug,
        "city": buildings[0].get('city') if buildings else None,
        "state": buildings[0].get('state') if buildings else None,
        "stats": {
            "total_units": len(units),
            "total_buildings": len(buildings),
            "avg_rent": round(sum(rents) / len(rents)) if rents else 0,
            "min_rent": min(rents) if rents else 0,
            "max_rent": max(rents) if rents else 0,
            "studios": studios,
            "one_beds": one_beds,
            "two_plus_beds": two_plus,
            "total_doorman": total_doorman,
            "total_elevator": total_elevator
        },
        "price_breakdown": price_breakdown,
        "units": units,
        "buildings": buildings
    }

# ============== END NEIGHBORHOOD ENDPOINTS ==============

@router.get("/admin/subscribers")
async def get_subscribers(user: User = Depends(require_admin)):
    """Get all email subscribers (admin only)"""
    subscribers = await db.email_subscribers.find({}, {"_id": 0}).sort('subscribed_at', -1).to_list(1000)
    return subscribers

@router.post("/admin/units/{unit_id}/toggle-featured")
async def toggle_unit_featured(unit_id: str, user: User = Depends(require_admin)):
    """Toggle featured status for a unit (admin only)"""
    existing = await db.units.find_one({'id': unit_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    current_featured = existing.get('is_featured', False)
    new_featured = not current_featured
    
    await db.units.update_one(
        {'id': unit_id}, 
        {'$set': {'is_featured': new_featured, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        'message': f"Unit {'featured' if new_featured else 'unfeatured'} successfully",
        'unit_id': unit_id,
        'is_featured': new_featured
    }

@router.post("/admin/set-featured-units")
async def set_featured_units(unit_ids: List[str], user: User = Depends(require_admin)):
    """Set specific units as featured and unfeature all others (admin only)"""
    # First, unfeature all units
    await db.units.update_many({}, {'$set': {'is_featured': False}})
    
    # Then feature the specified units
    if unit_ids:
        result = await db.units.update_many(
            {'id': {'$in': unit_ids}},
            {'$set': {'is_featured': True, 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        featured_count = result.modified_count
    else:
        featured_count = 0
    

# ============ AI SEARCH AGENT ============
@router.post("/admin/seed-database")
async def admin_seed_database(
    force: bool = Query(False, description="Force re-seed even if data exists"),
    is_admin: bool = Depends(require_admin)
):
    """
    Admin endpoint to seed the database with buildings and units data.
    Use force=true to overwrite existing data.
    """
    if not SEED_MODULE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database seeding module not available"
        )
    
    try:
        result = await seed_functions['seed_database'](force=force)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Database seeding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/seed-status")
async def admin_seed_status(is_admin: bool = Depends(require_admin)):
    """Check the current database status and available seed data."""
    try:
        current_buildings = await db.buildings.count_documents({})
        current_units = await db.units.count_documents({})
        
        seed_info = {"available": False, "buildings": 0, "units": 0}
        if SEED_MODULE_AVAILABLE:
            try:
                buildings_data, units_data = await seed_functions['load_seed_data']()
                seed_info = {
                    "available": True,
                    "buildings": len(buildings_data),
                    "units": len(units_data)
                }
            except:
                pass
        
        return {
            "current_database": {
                "buildings": current_buildings,
                "units": current_units
            },
            "seed_data": seed_info,
            "needs_seeding": current_buildings < seed_info.get("buildings", 0) or current_units < seed_info.get("units", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

