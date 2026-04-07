"""Favorites routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import logging

from database import db
from models import User, Favorite
from auth_utils import require_auth

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/favorites")
async def get_favorites(user: User = Depends(require_auth)):
    """Get user's favorite units"""
    favorites = await db.favorites.find({'user_id': user.id}, {"_id": 0}).to_list(1000)
    
    # Get unit details - optimized to avoid N+1 queries
    result = []
    if favorites:
        # Batch fetch units
        unit_ids = [f['unit_id'] for f in favorites]
        units = await db.units.find({'id': {'$in': unit_ids}}, {"_id": 0}).to_list(len(unit_ids))
        units_map = {u['id']: u for u in units}
        
        # Batch fetch buildings
        building_ids = list(set(u['building_id'] for u in units if u.get('building_id')))
        buildings = await db.buildings.find({'id': {'$in': building_ids}}, {"_id": 0}).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
        
        # Combine results
        for fav in favorites:
            unit = units_map.get(fav['unit_id'])
            if unit:
                unit['building'] = buildings_map.get(unit['building_id'])
                result.append({
                    'favorite_id': fav['id'],
                    'unit': unit
                })
    
    return result

@router.post("/favorites/{unit_id}")
async def add_favorite(unit_id: str, user: User = Depends(require_auth)):
    """Add unit to favorites"""
    # Check unit exists
    unit = await db.units.find_one({'id': unit_id})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Check if already favorited
    existing = await db.favorites.find_one({'user_id': user.id, 'unit_id': unit_id})
    if existing:
        return {'message': 'Already favorited'}
    
    favorite = Favorite(user_id=user.id, unit_id=unit_id)
    fav_dict = favorite.model_dump()
    fav_dict['created_at'] = fav_dict['created_at'].isoformat()
    await db.favorites.insert_one(fav_dict)
    
    return {'message': 'Added to favorites'}

@router.delete("/favorites/{unit_id}")
async def remove_favorite(unit_id: str, user: User = Depends(require_auth)):
    """Remove unit from favorites"""
    result = await db.favorites.delete_one({'user_id': user.id, 'unit_id': unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {'message': 'Removed from favorites'}
