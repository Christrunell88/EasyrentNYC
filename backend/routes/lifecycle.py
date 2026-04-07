"""Unit lifecycle management routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
import logging

from database import db
from models import User, LifecycleStatusInput, BulkLifecycleInput
from auth_utils import require_admin
from services import LIFECYCLE_SERVICE_AVAILABLE, lifecycle_functions

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ UNIT LIFECYCLE MANAGEMENT ROUTES ============

@router.get("/admin/lifecycle/stats")
async def get_lifecycle_stats(user: User = Depends(require_admin)):
    """Get lifecycle statistics for all units"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = lifecycle_functions['get_lifecycle_service'](db)
    return await service.get_lifecycle_stats()

@router.post("/admin/lifecycle/check-stale")
async def trigger_stale_check(user: User = Depends(require_admin)):
    """Manually trigger stale units check"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = lifecycle_functions['get_lifecycle_service'](db)
    result = await service.check_and_mark_stale_units()
    
    logger.info(f"Manual stale check triggered by {user.email}: {result['units_marked_stale']} units marked")
    return result

@router.get("/admin/lifecycle/stale-units")
async def get_stale_units(
    limit: int = Query(100, le=500),
    user: User = Depends(require_admin)
):
    """Get all units currently marked as stale"""
    stale_units = await db.units.find(
        {'lifecycle_status': 'stale'},
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    # Get building info for context
    if stale_units:
        building_ids = list(set(u.get('building_id') for u in stale_units if u.get('building_id')))
        buildings = await db.buildings.find({'id': {'$in': building_ids}}, {"_id": 0}).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
        
        for unit in stale_units:
            unit['building'] = buildings_map.get(unit.get('building_id'))
    
    return {
        'count': len(stale_units),
        'units': stale_units
    }

@router.get("/admin/lifecycle/rented-units")
async def get_rented_units(
    limit: int = Query(100, le=500),
    user: User = Depends(require_admin)
):
    """Get all units currently marked as rented"""
    rented_units = await db.units.find(
        {'lifecycle_status': 'rented'},
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    return {
        'count': len(rented_units),
        'units': rented_units
    }

@router.put("/admin/lifecycle/unit/{unit_id}/status")
async def update_unit_lifecycle_status(
    unit_id: str,
    input: LifecycleStatusInput,
    user: User = Depends(require_admin)
):
    """Update a unit's lifecycle status"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = lifecycle_functions['get_lifecycle_service'](db)
    
    if input.status == 'rented':
        result = await service.mark_unit_as_rented(
            unit_id=unit_id,
            notes=input.notes,
            changed_by=user.id
        )
    elif input.status == 'available':
        result = await service.mark_unit_as_available(
            unit_id=unit_id,
            rent=input.rent,
            available_date=input.available_date,
            notes=input.notes,
            changed_by=user.id
        )
    elif input.status == 'unavailable':
        # Mark as unavailable
        await service._record_status_change(
            unit_id=unit_id,
            old_status=(await db.units.find_one({'id': unit_id}, {"_id": 0, "lifecycle_status": 1})).get('lifecycle_status', 'available'),
            new_status='unavailable',
            source='manual',
            changed_by=user.id,
            reason=input.notes
        )
        await db.units.update_one(
            {'id': unit_id},
            {
                '$set': {
                    'is_available': False,
                    'lifecycle_status': 'unavailable',
                    'lifecycle_updated_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        result = {'success': True, 'unit_id': unit_id, 'new_status': 'unavailable'}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid status: {input.status}. Use: available, rented, unavailable")
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Operation failed'))
    
    logger.info(f"Unit {unit_id} lifecycle status updated to {input.status} by {user.email}")
    return result

@router.put("/admin/lifecycle/unit/{unit_id}/price")
async def update_unit_price(
    unit_id: str,
    new_price: float = Query(..., gt=0),
    reason: Optional[str] = None,
    user: User = Depends(require_admin)
):
    """Update a unit's rent price (with history tracking)"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = lifecycle_functions['get_lifecycle_service'](db)
    result = await service.update_unit_price(
        unit_id=unit_id,
        new_price=new_price,
        source='manual',
        changed_by=user.id,
        reason=reason
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Operation failed'))
    
    logger.info(f"Unit {unit_id} price updated to ${new_price} by {user.email}")
    return result

@router.get("/admin/lifecycle/unit/{unit_id}/history")
async def get_unit_history(unit_id: str, user: User = Depends(require_admin)):
    """Get full history for a unit (price changes + status changes)"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = lifecycle_functions['get_lifecycle_service'](db)
    return await service.get_unit_full_history(unit_id)

@router.post("/admin/lifecycle/bulk-refresh")
async def bulk_refresh_stale_units(
    input: BulkLifecycleInput,
    user: User = Depends(require_admin)
):
    """Refresh multiple stale units (mark as available again)"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = lifecycle_functions['get_lifecycle_service'](db)
    result = await service.refresh_stale_units(
        unit_ids=input.unit_ids,
        changed_by=user.id
    )
    
    logger.info(f"Bulk refresh: {result['refreshed_count']} units refreshed by {user.email}")
    return result

@router.post("/admin/lifecycle/bulk-mark-rented")
async def bulk_mark_units_rented(
    input: BulkLifecycleInput,
    user: User = Depends(require_admin)
):
    """Mark multiple units as rented"""
    if not LIFECYCLE_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Lifecycle service not available")
    
    service = lifecycle_functions['get_lifecycle_service'](db)
    result = await service.bulk_mark_rented(
        unit_ids=input.unit_ids,
        changed_by=user.id,
        notes=input.notes
    )
    
    logger.info(f"Bulk mark rented: {result['marked_rented_count']} units by {user.email}")
    return result
