"""Admin operations routes - unavailability, relisting, rejected staging."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging

from database import db
from models import (
    User, UnavailabilityReviewInput, BulkUnavailabilityReviewInput,
    BulkRelistInput, ApproveRejectedInput
)
from auth_utils import require_admin
from services import PROMOTION_SERVICE_AVAILABLE, promotion_service_functions

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/admin/unavailability-reviews")
async def get_unavailability_reviews(
    status: str = Query("pending", description="Filter by status: pending, confirmed_unavailable, false_positive"),
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    min_misses: int = Query(1, description="Minimum consecutive misses to show"),
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """
    Get units flagged as potentially unavailable for admin review.
    
    These are production units that were NOT found in recent crawls.
    Units with higher consecutive_misses are more likely to be actually unavailable.
    """
    query = {"review_status": status}
    
    if building_id:
        query["building_id"] = building_id
    if min_misses > 1:
        query["consecutive_misses"] = {"$gte": min_misses}
    
    reviews = await db.unavailability_reviews.find(
        query, {"_id": 0}
    ).sort([("consecutive_misses", -1), ("last_checked_at", -1)]).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with building names
    building_ids = list(set(r.get('building_id') for r in reviews if r.get('building_id')))
    buildings_map = {}
    if building_ids:
        buildings = await db.buildings.find(
            {"id": {"$in": building_ids}}, 
            {"_id": 0, "id": 1, "name": 1, "address": 1}
        ).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
    
    for review in reviews:
        building = buildings_map.get(review.get('building_id'), {})
        review['building_name'] = building.get('name', 'Unknown')
        review['building_address'] = building.get('address', 'Unknown')
    
    total = await db.unavailability_reviews.count_documents(query)
    
    return {
        "items": reviews,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.put("/admin/unavailability-reviews/{review_id}")
async def review_unavailability_flag(
    review_id: str,
    input: UnavailabilityReviewInput,
    user: User = Depends(require_admin)
):
    """
    Review an unavailability flag - confirm unit is unavailable or mark as false positive.
    
    Actions:
    - confirmed_unavailable: Marks the production unit as unavailable (is_available=false, lifecycle_status='rented')
    - false_positive: Keeps the unit available, dismisses the flag
    """
    review = await db.unavailability_reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update the review record
    await db.unavailability_reviews.update_one(
        {"id": review_id},
        {
            "$set": {
                "review_status": input.review_status,
                "reviewed_by": user.id,
                "reviewed_at": now,
                "reviewer_notes": input.reviewer_notes
            }
        }
    )
    
    # If confirmed unavailable, update the production unit
    if input.review_status == "confirmed_unavailable":
        unit_id = review.get('unit_id')
        
        # Update production unit
        result = await db.units.update_one(
            {"id": unit_id},
            {
                "$set": {
                    "is_available": False,
                    "lifecycle_status": "rented",
                    "unavailable_reason": "not_found_in_crawl",
                    "unavailable_confirmed_by": user.id,
                    "unavailable_confirmed_at": now,
                    "updated_at": now
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Marked unit {review.get('unit_number')} as unavailable (confirmed by admin)")
            
            # Record status change in history
            status_change = {
                "id": str(uuid.uuid4()),
                "unit_id": unit_id,
                "old_status": "available",
                "new_status": "rented",
                "source": "unavailability_review",
                "changed_by": user.id,
                "reason": f"Not found in crawl ({review.get('consecutive_misses', 1)} consecutive misses). {input.reviewer_notes or ''}",
                "created_at": now
            }
            await db.status_changes.insert_one(status_change)
        
        return {
            "message": f"Unit {review.get('unit_number')} marked as unavailable",
            "unit_id": unit_id,
            "review_status": input.review_status
        }
    else:
        # False positive - unit is still available, just dismiss the flag
        logger.info(f"Unavailability flag for unit {review.get('unit_number')} marked as false positive")
        return {
            "message": f"Flag dismissed for unit {review.get('unit_number')}",
            "unit_id": review.get('unit_id'),
            "review_status": input.review_status
        }



@router.post("/admin/unavailability-reviews/bulk-review")
async def bulk_review_unavailability(
    input: BulkUnavailabilityReviewInput,
    user: User = Depends(require_admin)
):
    """
    Bulk review multiple unavailability flags at once.
    """
    if input.review_status not in ["confirmed_unavailable", "false_positive"]:
        raise HTTPException(status_code=400, detail="Invalid review_status")
    
    now = datetime.now(timezone.utc).isoformat()
    processed = 0
    units_marked_unavailable = []
    
    for review_id in input.review_ids:
        review = await db.unavailability_reviews.find_one({"id": review_id})
        if not review:
            continue
        
        # Update review record
        await db.unavailability_reviews.update_one(
            {"id": review_id},
            {
                "$set": {
                    "review_status": input.review_status,
                    "reviewed_by": user.id,
                    "reviewed_at": now,
                    "reviewer_notes": input.reviewer_notes
                }
            }
        )
        
        # If confirmed unavailable, update production unit
        if input.review_status == "confirmed_unavailable":
            unit_id = review.get('unit_id')
            await db.units.update_one(
                {"id": unit_id},
                {
                    "$set": {
                        "is_available": False,
                        "lifecycle_status": "rented",
                        "unavailable_reason": "not_found_in_crawl",
                        "unavailable_confirmed_by": user.id,
                        "unavailable_confirmed_at": now,
                        "updated_at": now
                    }
                }
            )
            units_marked_unavailable.append(review.get('unit_number'))
        
        processed += 1
    
    return {
        "message": f"Processed {processed} reviews",
        "review_status": input.review_status,
        "units_marked_unavailable": units_marked_unavailable if input.review_status == "confirmed_unavailable" else []
    }


@router.get("/admin/unavailability-reviews/stats")
async def get_unavailability_stats(user: User = Depends(require_admin)):
    """Get summary statistics for unavailability reviews"""
    pending = await db.unavailability_reviews.count_documents({"review_status": "pending"})
    confirmed = await db.unavailability_reviews.count_documents({"review_status": "confirmed_unavailable"})
    false_positive = await db.unavailability_reviews.count_documents({"review_status": "false_positive"})
    
    # Get high-priority items (3+ consecutive misses)
    high_priority = await db.unavailability_reviews.count_documents({
        "review_status": "pending",
        "consecutive_misses": {"$gte": 3}
    })
    
    # Get by building breakdown
    pipeline = [
        {"$match": {"review_status": "pending"}},
        {"$group": {"_id": "$building_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    by_building = await db.unavailability_reviews.aggregate(pipeline).to_list(10)
    
    # Enrich with building names
    building_ids = [b['_id'] for b in by_building]
    if building_ids:
        buildings = await db.buildings.find(
            {"id": {"$in": building_ids}},
            {"_id": 0, "id": 1, "name": 1}
        ).to_list(len(building_ids))
        buildings_map = {b['id']: b['name'] for b in buildings}
        for b in by_building:
            b['building_name'] = buildings_map.get(b['_id'], 'Unknown')
    
    return {
        "total_pending": pending,
        "total_confirmed": confirmed,
        "total_false_positive": false_positive,
        "high_priority_count": high_priority,
        "pending_by_building": by_building
    }


# ============ UNAVAILABLE UNITS MANAGEMENT ============

@router.get("/admin/units/unavailable")
async def get_unavailable_units(
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    building_id: Optional[str] = Query(None),
    user: User = Depends(require_admin)
):
    """
    Get units that are marked as unavailable/rented.
    These units can be re-listed if they become available again.
    """
    query = {
        "$or": [
            {"is_available": False},
            {"lifecycle_status": {"$in": ["rented", "unavailable"]}}
        ]
    }
    
    if building_id:
        query["building_id"] = building_id
    
    units = await db.units.find(
        query, {"_id": 0}
    ).sort("updated_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with building info
    building_ids = list(set(u.get('building_id') for u in units if u.get('building_id')))
    buildings_map = {}
    if building_ids:
        buildings = await db.buildings.find(
            {"id": {"$in": building_ids}},
            {"_id": 0, "id": 1, "name": 1, "address": 1}
        ).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
    
    for unit in units:
        building = buildings_map.get(unit.get('building_id'), {})
        unit['building_name'] = building.get('name', 'Unknown')
        unit['building_address'] = building.get('address', 'Unknown')
    
    total = await db.units.count_documents(query)
    
    return {
        "items": units,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.put("/admin/units/{unit_id}/relist")
async def relist_unavailable_unit(
    unit_id: str,
    rent: Optional[int] = None,
    notes: Optional[str] = None,
    user: User = Depends(require_admin)
):
    """
    Re-list an unavailable unit, making it available again.
    Optionally update the rent price.
    """
    unit = await db.units.find_one({"id": unit_id})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    update_data = {
        "is_available": True,
        "lifecycle_status": "available",
        "relisted_at": now,
        "relisted_by": user.id,
        "relist_notes": notes,
        "updated_at": now
    }
    
    # Update rent if provided
    if rent is not None:
        update_data["rent"] = rent
        update_data["rent_updated_at"] = now
    
    # Clear unavailability fields
    update_data["unavailable_reason"] = None
    update_data["unavailable_confirmed_by"] = None
    update_data["unavailable_confirmed_at"] = None
    
    result = await db.units.update_one(
        {"id": unit_id},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        # Record status change
        status_change = {
            "id": str(uuid.uuid4()),
            "unit_id": unit_id,
            "old_status": unit.get('lifecycle_status', 'unavailable'),
            "new_status": "available",
            "source": "admin_relist",
            "changed_by": user.id,
            "reason": notes or "Re-listed by admin",
            "created_at": now
        }
        await db.status_changes.insert_one(status_change)
        
        # Clear any pending unavailability review for this unit
        await db.unavailability_reviews.update_many(
            {"unit_id": unit_id, "review_status": "pending"},
            {"$set": {"review_status": "relisted", "reviewed_at": now, "reviewed_by": user.id}}
        )
        
        logger.info(f"Unit {unit.get('unit_number')} re-listed by admin {user.email}")
        
        return {
            "message": f"Unit {unit.get('unit_number')} has been re-listed",
            "unit_id": unit_id,
            "new_rent": rent if rent else unit.get('rent')
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to update unit")


@router.post("/admin/units/bulk-relist")
async def bulk_relist_units(
    input: BulkRelistInput,
    user: User = Depends(require_admin)
):
    """
    Re-list multiple unavailable units at once.
    """
    now = datetime.now(timezone.utc).isoformat()
    relisted = []
    
    for unit_id in input.unit_ids:
        unit = await db.units.find_one({"id": unit_id})
        if not unit:
            continue
        
        result = await db.units.update_one(
            {"id": unit_id},
            {
                "$set": {
                    "is_available": True,
                    "lifecycle_status": "available",
                    "relisted_at": now,
                    "relisted_by": user.id,
                    "relist_notes": input.notes,
                    "updated_at": now,
                    "unavailable_reason": None,
                    "unavailable_confirmed_by": None,
                    "unavailable_confirmed_at": None
                }
            }
        )
        
        if result.modified_count > 0:
            relisted.append(unit.get('unit_number'))
            
            # Clear pending unavailability reviews
            await db.unavailability_reviews.update_many(
                {"unit_id": unit_id, "review_status": "pending"},
                {"$set": {"review_status": "relisted", "reviewed_at": now, "reviewed_by": user.id}}
            )
    
    return {
        "message": f"Re-listed {len(relisted)} units",
        "relisted_units": relisted
    }


# ============ REJECTED STAGING UNITS MANAGEMENT ============

@router.get("/admin/staging/rejected")
async def get_rejected_staging_units(
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """
    Get rejected staging units that can be reconsidered for listing.
    """
    units = await db.units_staging.find(
        {"review_status": "rejected"}, {"_id": 0}
    ).sort("reviewed_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with building info
    building_ids = list(set(u.get('building_id') for u in units if u.get('building_id')))
    buildings_map = {}
    if building_ids:
        buildings = await db.buildings.find(
            {"id": {"$in": building_ids}},
            {"_id": 0, "id": 1, "name": 1, "address": 1}
        ).to_list(len(building_ids))
        buildings_map = {b['id']: b for b in buildings}
    
    for unit in units:
        building = buildings_map.get(unit.get('building_id'), {})
        unit['building_name'] = building.get('name', 'Unknown')
        unit['building_address'] = building.get('address', 'Unknown')
    
    total = await db.units_staging.count_documents({"review_status": "rejected"})
    
    return {
        "items": units,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.put("/admin/staging/rejected/{staging_id}/reconsider")
async def reconsider_rejected_staging(
    staging_id: str,
    user: User = Depends(require_admin)
):
    """
    Move a rejected staging unit back to pending for reconsideration.
    """
    unit = await db.units_staging.find_one({"id": staging_id})
    if not unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    if unit.get('review_status') != 'rejected':
        raise HTTPException(status_code=400, detail="Unit is not in rejected status")
    
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db.units_staging.update_one(
        {"id": staging_id},
        {
            "$set": {
                "review_status": "pending",
                "reconsidered_at": now,
                "reconsidered_by": user.id,
                "updated_at": now
            },
            "$unset": {
                "rejection_reason": "",
                "rejected_by": "",
                "rejected_at": ""
            }
        }
    )
    
    if result.modified_count > 0:
        return {
            "message": f"Unit {unit.get('unit_number')} moved back to pending review",
            "staging_id": staging_id
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to update unit")



@router.put("/admin/staging/rejected/{staging_id}/approve-direct")
async def approve_rejected_directly(
    staging_id: str,
    input: ApproveRejectedInput = ApproveRejectedInput(),
    user: User = Depends(require_admin)
):
    """
    Directly approve a previously rejected staging unit to production.
    """
    staging_unit = await db.units_staging.find_one({"id": staging_id})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Prepare production unit data
    production_unit = {
        "id": str(uuid.uuid4()),
        "building_id": staging_unit.get('building_id'),
        "unit_number": staging_unit.get('unit_number'),
        "rent": input.rent if input.rent else staging_unit.get('rent'),
        "bedrooms": staging_unit.get('bedrooms'),
        "bathrooms": staging_unit.get('bathrooms'),
        "sqft": staging_unit.get('sqft'),
        "amenities": staging_unit.get('amenities', []),
        "images": staging_unit.get('images', []),
        "floor_plan_url": staging_unit.get('floor_plan_url'),
        "is_available": True,
        "lifecycle_status": "available",
        "source_url": staging_unit.get('source_url'),
        "crawler_source": staging_unit.get('crawler_source'),
        "created_at": now,
        "updated_at": now,
        "approved_from_rejected": True,
        "approved_by": user.id,
        "approved_at": now
    }
    
    # Insert to production
    await db.units.insert_one(production_unit)
    
    # Update staging record
    await db.units_staging.update_one(
        {"id": staging_id},
        {
            "$set": {
                "review_status": "approved",
                "approved_at": now,
                "approved_by": user.id,
                "production_unit_id": production_unit['id']
            }
        }
    )
    
    return {
        "message": f"Unit {staging_unit.get('unit_number')} approved and added to production",
        "production_unit_id": production_unit['id']
    }
