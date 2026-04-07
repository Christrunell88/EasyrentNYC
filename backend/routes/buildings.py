"""Building routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
import logging

from database import db
from models import User, Building, BuildingInput
from auth_utils import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/buildings", response_model=List[Building])
async def get_buildings():
    """Get all buildings"""
    buildings = await db.buildings.find({}, {"_id": 0}).to_list(1000)
    for b in buildings:
        if isinstance(b.get('created_at'), str):
            b['created_at'] = datetime.fromisoformat(b['created_at'])
        if b.get('last_crawled') and isinstance(b['last_crawled'], str):
            b['last_crawled'] = datetime.fromisoformat(b['last_crawled'])
    return buildings

@router.get("/buildings/{building_id}", response_model=Building)
async def get_building(building_id: str):
    """Get building by ID"""
    building = await db.buildings.find_one({'id': building_id}, {"_id": 0})
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    if isinstance(building.get('created_at'), str):
        building['created_at'] = datetime.fromisoformat(building['created_at'])
    if building.get('last_crawled') and isinstance(building['last_crawled'], str):
        building['last_crawled'] = datetime.fromisoformat(building['last_crawled'])
    
    return building

@router.post("/buildings", response_model=Building)
async def create_building(input: BuildingInput, user: User = Depends(require_admin)):
    """Create building (admin only)"""
    building = Building(**input.model_dump())
    building_dict = building.model_dump()
    building_dict['created_at'] = building_dict['created_at'].isoformat()
    await db.buildings.insert_one(building_dict)
    return building

@router.put("/buildings/{building_id}", response_model=Building)
async def update_building(building_id: str, input: BuildingInput, user: User = Depends(require_admin)):
    """Update building (admin only)"""
    existing = await db.buildings.find_one({'id': building_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Building not found")
    
    update_data = input.model_dump()
    await db.buildings.update_one({'id': building_id}, {'$set': update_data})
    
    updated = await db.buildings.find_one({'id': building_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if updated.get('last_crawled') and isinstance(updated['last_crawled'], str):
        updated['last_crawled'] = datetime.fromisoformat(updated['last_crawled'])
    
    return updated

@router.delete("/buildings/{building_id}")
async def delete_building(building_id: str, user: User = Depends(require_admin)):
    """Delete building and all its units (admin only)"""
    result = await db.buildings.delete_one({'id': building_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Delete all units
    await db.units.delete_many({'building_id': building_id})
    return {'message': 'Building deleted'}
