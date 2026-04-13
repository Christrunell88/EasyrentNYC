"""Admin staging routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
import uuid
import os
import shutil
import logging

from database import db
from models import (
    User, Building, Unit, BuildingStaging, UnitStaging,
    BuildingStagingInput, UnitStagingInput, StagingReviewInput,
    StagingUnitEditInput, StagingBulkReviewInput, BulkDeleteInput
)
from auth_utils import require_admin
from services import PROMOTION_SERVICE_AVAILABLE, promotion_service_functions

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/admin/staging/buildings")
async def get_staging_buildings(
    status: Optional[str] = Query(None, description="Filter by review_status: pending, approved, rejected"),
    batch_id: Optional[str] = Query(None, description="Filter by crawler_batch_id"),
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """Get all buildings in staging collection"""
    query = {}
    if status:
        query["review_status"] = status
    if batch_id:
        query["crawler_batch_id"] = batch_id
    
    buildings = await db.buildings_staging.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.buildings_staging.count_documents(query)
    
    return {
        "items": buildings,
        "total": total,
        "pending": await db.buildings_staging.count_documents({"review_status": "pending"}),
        "approved": await db.buildings_staging.count_documents({"review_status": "approved"}),
        "rejected": await db.buildings_staging.count_documents({"review_status": "rejected"})
    }

@router.get("/admin/staging/buildings/{building_id}")
async def get_staging_building(building_id: str, user: User = Depends(require_admin)):
    """Get a specific staging building by ID"""
    building = await db.buildings_staging.find_one({"id": building_id}, {"_id": 0})
    if not building:
        raise HTTPException(status_code=404, detail="Staging building not found")
    return building

@router.post("/admin/staging/buildings")
async def create_staging_building(
    building_input: BuildingStagingInput,
    user: User = Depends(require_admin)
):
    """Create a new building in staging"""
    building = BuildingStaging(
        name=building_input.name,
        address=building_input.address,
        neighborhood=building_input.neighborhood,
        city=building_input.city,
        state=building_input.state,
        zip_code=building_input.zip_code,
        source_url=building_input.source_url,
        latitude=building_input.latitude,
        longitude=building_input.longitude,
        crawler_source=building_input.crawler_source,
        crawler_batch_id=building_input.crawler_batch_id,
        validation_flags=building_input.validation_flags,
        duplicate_score=building_input.duplicate_score
    )
    
    await db.buildings_staging.insert_one(building.model_dump())
    return {"id": building.id, "message": "Staging building created"}

@router.put("/admin/staging/buildings/{building_id}/review")
async def review_staging_building(
    building_id: str,
    review: StagingReviewInput,
    user: User = Depends(require_admin)
):
    """Review a staging building (approve/reject)"""
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="review_status must be 'approved' or 'rejected'")
    
    result = await db.buildings_staging.update_one(
        {"id": building_id},
        {
            "$set": {
                "review_status": review.review_status,
                "reviewer_notes": review.reviewer_notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staging building not found")
    
    return {"message": f"Building {review.review_status}", "id": building_id}

@router.post("/admin/staging/buildings/{building_id}/promote")
async def promote_staging_building(
    building_id: str,
    user: User = Depends(require_admin)
):
    """Promote an approved staging building to production"""
    staging_building = await db.buildings_staging.find_one({"id": building_id}, {"_id": 0})
    if not staging_building:
        raise HTTPException(status_code=404, detail="Staging building not found")
    
    if staging_building.get("review_status") != "approved":
        raise HTTPException(status_code=400, detail="Building must be approved before promotion")
    
    # Create production building (exclude staging-specific fields)
    production_building = {
        "id": str(uuid.uuid4()),
        "name": staging_building["name"],
        "address": staging_building["address"],
        "neighborhood": staging_building["neighborhood"],
        "city": staging_building["city"],
        "state": staging_building["state"],
        "zip_code": staging_building["zip_code"],
        "source_url": staging_building["source_url"],
        "latitude": staging_building.get("latitude"),
        "longitude": staging_building.get("longitude"),
        "last_crawled": staging_building.get("last_crawled"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.buildings.insert_one(production_building)
    
    # Mark staging as promoted
    await db.buildings_staging.update_one(
        {"id": building_id},
        {"$set": {"review_status": "promoted", "matched_production_id": production_building["id"]}}
    )
    
    return {
        "message": "Building promoted to production",
        "staging_id": building_id,
        "production_id": production_building["id"]
    }

@router.delete("/admin/staging/buildings/{building_id}")
async def delete_staging_building(building_id: str, user: User = Depends(require_admin)):
    """Delete a staging building"""
    result = await db.buildings_staging.delete_one({"id": building_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staging building not found")
    return {"message": "Staging building deleted"}

# Units Staging Routes

@router.get("/admin/staging/units")
async def get_staging_units(
    status: Optional[str] = Query(None, description="Filter by review_status: pending, approved, rejected"),
    batch_id: Optional[str] = Query(None, description="Filter by crawler_batch_id"),
    building_id: Optional[str] = Query(None, description="Filter by building_id"),
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """Get all units in staging collection"""
    query = {}
    if status:
        query["review_status"] = status
    if batch_id:
        query["crawler_batch_id"] = batch_id
    if building_id:
        query["building_id"] = building_id
    
    units = await db.units_staging.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.units_staging.count_documents(query)
    
    return {
        "items": units,
        "total": total,
        "pending": await db.units_staging.count_documents({"review_status": "pending"}),
        "approved": await db.units_staging.count_documents({"review_status": "approved"}),
        "rejected": await db.units_staging.count_documents({"review_status": "rejected"})
    }

@router.get("/admin/staging/units/{unit_id}")
async def get_staging_unit(unit_id: str, user: User = Depends(require_admin)):
    """Get a specific staging unit by ID"""
    unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    return unit

@router.post("/admin/staging/units")
async def create_staging_unit(
    unit_input: UnitStagingInput,
    user: User = Depends(require_admin)
):
    """Create a new unit in staging"""
    unit = UnitStaging(
        building_id=unit_input.building_id,
        unit_number=unit_input.unit_number,
        rent=unit_input.rent,
        bedrooms=unit_input.bedrooms,
        bathrooms=unit_input.bathrooms,
        square_feet=unit_input.square_feet,
        available_date=unit_input.available_date,
        amenities=unit_input.amenities,
        images=unit_input.images,
        description=unit_input.description,
        is_available=unit_input.is_available,
        crawler_source=unit_input.crawler_source,
        crawler_batch_id=unit_input.crawler_batch_id,
        validation_flags=unit_input.validation_flags,
        duplicate_score=unit_input.duplicate_score
    )
    
    await db.units_staging.insert_one(unit.model_dump())
    return {"id": unit.id, "message": "Staging unit created"}

@router.put("/admin/staging/units/{unit_id}/review")
async def review_staging_unit(
    unit_id: str,
    review: StagingReviewInput,
    user: User = Depends(require_admin)
):
    """Review a staging unit (approve/reject)"""
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="review_status must be 'approved' or 'rejected'")
    
    result = await db.units_staging.update_one(
        {"id": unit_id},
        {
            "$set": {
                "review_status": review.review_status,
                "reviewer_notes": review.reviewer_notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    return {"message": f"Unit {review.review_status}", "id": unit_id}

@router.put("/admin/staging/units/{unit_id}/edit")
async def edit_staging_unit(
    unit_id: str,
    edit_data: StagingUnitEditInput,
    user: User = Depends(require_admin)
):
    """Edit staging unit details before approval (building, rent, etc.)"""
    # Verify the staging unit exists
    staging_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    # Build update dict with only provided fields
    update_data = {}
    
    if edit_data.building_id is not None:
        # Verify building exists
        building = await db.buildings.find_one({"id": edit_data.building_id}, {"_id": 0})
        if not building:
            raise HTTPException(status_code=400, detail="Invalid building_id - building not found")
        update_data["building_id"] = edit_data.building_id
        update_data["building_name"] = building.get("name")
        update_data["building_address"] = building.get("address")
    
    if edit_data.unit_number is not None:
        update_data["unit_number"] = edit_data.unit_number
        update_data["normalized_unit_number"] = edit_data.unit_number.strip().upper()
    
    if edit_data.rent is not None:
        update_data["rent"] = edit_data.rent
    
    if edit_data.bedrooms is not None:
        update_data["bedrooms"] = edit_data.bedrooms
    
    if edit_data.bathrooms is not None:
        update_data["bathrooms"] = edit_data.bathrooms
    
    if edit_data.square_feet is not None:
        update_data["square_feet"] = edit_data.square_feet
    
    if edit_data.available_date is not None:
        update_data["available_date"] = edit_data.available_date
    
    if edit_data.description is not None:
        update_data["description"] = edit_data.description
    
    if edit_data.images is not None:
        update_data["images"] = edit_data.images
        # Remove no_images flag if images are being added
        if edit_data.images and len(edit_data.images) > 0:
            await db.units_staging.update_one(
                {"id": unit_id},
                {"$pull": {"validation_flags": "no_images"}}
            )
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Add metadata
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["edited_by"] = user.id
    update_data["edited_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.units_staging.update_one(
        {"id": unit_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        return {"message": "No changes made", "id": unit_id}
    
    # Return updated unit
    updated_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    return {"message": "Unit updated", "id": unit_id, "unit": updated_unit}

@router.post("/admin/staging/units/{unit_id}/upload-images")
async def upload_staging_unit_images(
    unit_id: str,
    files: List[UploadFile] = File(...),
    user: User = Depends(require_admin)
):
    """Upload images for a staging unit"""
    # Verify unit exists
    staging_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    uploaded_urls = []
    upload_dir = Path(__file__).parent.parent / "uploads" / unit_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        if not file.content_type.startswith("image/"):
            continue
        
        # Generate unique filename
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4().hex[:12]}.{ext}"
        file_path = upload_dir / filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create URL path (relative to backend)
        image_url = f"/api/uploads/{unit_id}/{filename}"
        uploaded_urls.append(image_url)
    
    if not uploaded_urls:
        raise HTTPException(status_code=400, detail="No valid images uploaded")
    
    # Update the staging unit with new images (append to existing)
    existing_images = staging_unit.get("images", []) or []
    all_images = existing_images + uploaded_urls
    
    await db.units_staging.update_one(
        {"id": unit_id},
        {
            "$set": {
                "images": all_images,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$pull": {"validation_flags": "no_images"}
        }
    )
    
    return {
        "message": f"Uploaded {len(uploaded_urls)} images",
        "uploaded_urls": uploaded_urls,
        "total_images": len(all_images)
    }

@router.delete("/admin/staging/units/{unit_id}/images")
async def delete_staging_unit_image(
    unit_id: str,
    image_url: str = Query(...),
    user: User = Depends(require_admin)
):
    """Delete a specific image from a staging unit"""
    staging_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    existing_images = staging_unit.get("images", []) or []
    
    if image_url not in existing_images:
        raise HTTPException(status_code=404, detail="Image not found in unit")
    
    # Remove from list
    updated_images = [img for img in existing_images if img != image_url]
    
    # Delete file if it's a local upload
    if image_url.startswith("/api/uploads/"):
        file_path = Path(__file__).parent.parent / "uploads" / image_url.replace("/api/uploads/", "")
        if file_path.exists():
            file_path.unlink()
    
    # Update staging unit
    update_data = {
        "images": updated_images,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Re-add no_images flag if no images left
    if len(updated_images) == 0:
        await db.units_staging.update_one(
            {"id": unit_id},
            {"$addToSet": {"validation_flags": "no_images"}}
        )
    
    await db.units_staging.update_one(
        {"id": unit_id},
        {"$set": update_data}
    )
    
    return {"message": "Image deleted", "remaining_images": len(updated_images)}

@router.post("/admin/staging/units/{unit_id}/promote")
async def promote_staging_unit(
    unit_id: str,
    user: User = Depends(require_admin)
):
    """Promote an approved staging unit to production"""
    staging_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staging_unit:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    
    if staging_unit.get("review_status") != "approved":
        raise HTTPException(status_code=400, detail="Unit must be approved before promotion")
    
    # Check if unit already exists in production (same building + unit number)
    existing_unit = await db.units.find_one({
        "building_id": staging_unit["building_id"],
        "unit_number": staging_unit["unit_number"]
    }, {"_id": 0})
    
    if existing_unit:
        # Update existing production unit
        production_id = existing_unit["id"]
        update_data = {
            "rent": staging_unit["rent"],
            "bedrooms": staging_unit["bedrooms"],
            "bathrooms": staging_unit["bathrooms"],
            "square_feet": staging_unit.get("square_feet"),
            "available_date": staging_unit.get("available_date"),
            "amenities": staging_unit.get("amenities", []),
            "images": staging_unit.get("images", []) if staging_unit.get("images") else existing_unit.get("images", []),
            "description": staging_unit.get("description") or existing_unit.get("description"),
            "is_available": staging_unit.get("is_available", True),
            "latitude": staging_unit.get("latitude"),
            "longitude": staging_unit.get("longitude"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.units.update_one({"id": production_id}, {"$set": update_data})
        message = "Unit updated in production (existing unit found)"
    else:
        # Create new production unit
        production_id = str(uuid.uuid4())
        production_unit = {
            "id": production_id,
            "building_id": staging_unit["building_id"],
            "unit_number": staging_unit["unit_number"],
            "rent": staging_unit["rent"],
            "bedrooms": staging_unit["bedrooms"],
            "bathrooms": staging_unit["bathrooms"],
            "square_feet": staging_unit.get("square_feet"),
            "available_date": staging_unit.get("available_date"),
            "amenities": staging_unit.get("amenities", []),
            "images": staging_unit.get("images", []),
            "description": staging_unit.get("description"),
            "is_available": staging_unit.get("is_available", True),
            "is_featured": False,
            "latitude": staging_unit.get("latitude"),
            "longitude": staging_unit.get("longitude"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(production_unit)
        message = "Unit promoted to production (new unit created)"
    
    # Mark staging as promoted
    await db.units_staging.update_one(
        {"id": unit_id},
        {"$set": {"review_status": "promoted", "matched_production_id": production_id}}
    )
    
    return {
        "message": message,
        "staging_id": unit_id,
        "production_id": production_id
    }

@router.delete("/admin/staging/units/{unit_id}")
async def delete_staging_unit(unit_id: str, user: User = Depends(require_admin)):
    """Delete a staging unit"""
    result = await db.units_staging.delete_one({"id": unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staging unit not found")
    return {"message": "Staging unit deleted"}

# Bulk Operations for Staging

@router.post("/admin/staging/buildings/bulk-review")
async def bulk_review_staging_buildings(
    review: StagingBulkReviewInput,
    user: User = Depends(require_admin)
):
    """Bulk review multiple staging buildings"""
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="review_status must be 'approved' or 'rejected'")
    
    result = await db.buildings_staging.update_many(
        {"id": {"$in": review.ids}},
        {
            "$set": {
                "review_status": review.review_status,
                "reviewer_notes": review.reviewer_notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": f"{result.modified_count} buildings {review.review_status}",
        "modified_count": result.modified_count
    }

@router.post("/admin/staging/units/bulk-review")
async def bulk_review_staging_units(
    review: StagingBulkReviewInput,
    user: User = Depends(require_admin)
):
    """Bulk review multiple staging units"""
    if review.review_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="review_status must be 'approved' or 'rejected'")
    
    result = await db.units_staging.update_many(
        {"id": {"$in": review.ids}},
        {
            "$set": {
                "review_status": review.review_status,
                "reviewer_notes": review.reviewer_notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": f"{result.modified_count} units {review.review_status}",
        "modified_count": result.modified_count
    }

@router.get("/admin/staging/stats")
async def get_staging_stats(user: User = Depends(require_admin)):
    """Get staging collections statistics"""
    buildings_pending = await db.buildings_staging.count_documents({"review_status": "pending"})
    buildings_approved = await db.buildings_staging.count_documents({"review_status": "approved"})
    buildings_rejected = await db.buildings_staging.count_documents({"review_status": "rejected"})
    
    units_pending = await db.units_staging.count_documents({"review_status": "pending"})
    units_approved = await db.units_staging.count_documents({"review_status": "approved"})
    units_rejected = await db.units_staging.count_documents({"review_status": "rejected"})
    
    # Get unavailability review stats
    unavail_pending = await db.unavailability_reviews.count_documents({"review_status": "pending"})
    unavail_confirmed = await db.unavailability_reviews.count_documents({"review_status": "confirmed_unavailable"})
    unavail_false_positive = await db.unavailability_reviews.count_documents({"review_status": "false_positive"})
    
    # Get recent batch IDs
    recent_batches = await db.units_staging.distinct("crawler_batch_id")
    
    return {
        "buildings_staging": {
            "total": buildings_pending + buildings_approved + buildings_rejected,
            "pending": buildings_pending,
            "approved": buildings_approved,
            "rejected": buildings_rejected
        },
        "units_staging": {
            "total": units_pending + units_approved + units_rejected,
            "pending": units_pending,
            "approved": units_approved,
            "rejected": units_rejected
        },
        "unavailability_reviews": {
            "total": unavail_pending + unavail_confirmed + unavail_false_positive,
            "pending": unavail_pending,
            "confirmed_unavailable": unavail_confirmed,
            "false_positive": unavail_false_positive
        },
        "recent_batch_ids": recent_batches[-10:] if recent_batches else []
    }


# ============ UNAVAILABILITY REVIEW ROUTES ============
@router.get("/staging/units")
async def get_staging_units_for_approval(
    status: str = Query("pending", description="Filter by status: pending, approved, rejected"),
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    batch_id: Optional[str] = Query(None, description="Filter by crawler batch ID"),
    has_duplicates: Optional[bool] = Query(None, description="Filter by duplicate flag"),
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    user: User = Depends(require_admin)
):
    """
    Get staged units for approval review.
    
    Query params:
    - status: pending | approved | rejected
    - building_id: Filter by building
    - batch_id: Filter by crawl batch
    - has_duplicates: true to show only flagged duplicates
    """
    query = {"review_status": status}
    
    if building_id:
        query["building_id"] = building_id
    if batch_id:
        query["crawler_batch_id"] = batch_id
    if has_duplicates is True:
        query["validation_flags"] = {"$in": ["likely_duplicate", "possible_duplicate", "potential_duplicate"]}
    elif has_duplicates is False:
        query["validation_flags"] = {"$nin": ["likely_duplicate", "possible_duplicate", "potential_duplicate"]}
    
    # Get units with building info
    units = await db.units_staging.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with building names
    for unit in units:
        # Try production building first
        building = await db.buildings.find_one({"id": unit["building_id"]}, {"_id": 0, "name": 1, "address": 1})
        if not building:
            # Try staging building
            building = await db.buildings_staging.find_one({"id": unit["building_id"]}, {"_id": 0, "name": 1, "address": 1})
        
        unit["building_name"] = building.get("name", "Unknown") if building else "Unknown"
        unit["building_address"] = building.get("address", "") if building else ""
    
    total = await db.units_staging.count_documents(query)
    pending_count = await db.units_staging.count_documents({"review_status": "pending"})
    
    return {
        "items": units,
        "total": total,
        "pending_total": pending_count,
        "skip": skip,
        "limit": limit
    }


@router.post("/staging/approve/{unit_id}")
async def approve_staging_unit(
    unit_id: str,
    notes: Optional[str] = Query(None, description="Optional approval notes"),
    user: User = Depends(require_admin)
):
    """
    Approve a staged unit and move it to production.
    
    Process:
    1. Validate building exists in production (create if missing from staging)
    2. Check for duplicates in production (prevent double insertion)
    3. Move unit from staging to production
    4. Set is_verified = true
    5. Maintain source metadata
    6. Record approval timestamp
    """
    # Get the staged unit
    staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staged_unit:
        raise HTTPException(status_code=404, detail="Staged unit not found")
    
    if staged_unit.get("review_status") == "approved":
        raise HTTPException(status_code=400, detail="Unit already approved")
    
    building_id = staged_unit["building_id"]
    production_building_id = building_id
    
    # Step 1: Validate building exists in production
    production_building = await db.buildings.find_one({"id": building_id}, {"_id": 0})
    
    if not production_building:
        # Check if building exists in staging
        staged_building = await db.buildings_staging.find_one({"id": building_id}, {"_id": 0})
        
        if staged_building:
            # Create building in production from staging data
            production_building_id = str(uuid.uuid4())
            new_production_building = {
                "id": production_building_id,
                "name": staged_building["name"],
                "address": staged_building["address"],
                "neighborhood": staged_building["neighborhood"],
                "city": staged_building["city"],
                "state": staged_building["state"],
                "zip_code": staged_building["zip_code"],
                "source_url": staged_building["source_url"],
                "latitude": staged_building.get("latitude"),
                "longitude": staged_building.get("longitude"),
                "last_crawled": staged_building.get("last_crawled"),
                # Source metadata
                "crawler_source": staged_building.get("crawler_source", ""),
                "original_staging_id": building_id,
                "is_verified": True,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "verified_by": user.id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.buildings.insert_one(new_production_building)
            
            # Mark staging building as promoted
            await db.buildings_staging.update_one(
                {"id": building_id},
                {
                    "$set": {
                        "review_status": "promoted",
                        "matched_production_id": production_building_id,
                        "reviewed_by": user.id,
                        "reviewed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Auto-created production building {production_building_id} from staging {building_id}")
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Building {building_id} not found in production or staging. Cannot approve unit."
            )
    
    # Step 2: Check for duplicates in production
    # Use normalized unit number if available
    normalized_unit = staged_unit.get("normalized_unit_number", staged_unit["unit_number"])
    
    existing_unit = await db.units.find_one({
        "building_id": production_building_id,
        "$or": [
            {"unit_number": staged_unit["unit_number"]},
            {"unit_number": normalized_unit}
        ]
    }, {"_id": 0})
    
    action = "created"
    
    if existing_unit:
        # UPDATE existing production unit instead of rejecting
        production_unit_id = existing_unit["id"]
        update_data = {
            "rent": staged_unit["rent"],
            "bedrooms": staged_unit["bedrooms"],
            "bathrooms": staged_unit["bathrooms"],
            "square_feet": staged_unit.get("square_feet"),
            "available_date": staged_unit.get("available_date", existing_unit.get("available_date", "Immediate")),
            "amenities": staged_unit.get("amenities", existing_unit.get("amenities", [])),
            "images": staged_unit.get("images") if staged_unit.get("images") else existing_unit.get("images", []),
            "description": staged_unit.get("description") or existing_unit.get("description", ""),
            "is_available": staged_unit.get("is_available", True),
            "latitude": staged_unit.get("latitude") or existing_unit.get("latitude"),
            "longitude": staged_unit.get("longitude") or existing_unit.get("longitude"),
            # Update verification
            "is_verified": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verified_by": user.id,
            # Update source metadata
            "crawler_source": staged_unit.get("crawler_source", existing_unit.get("crawler_source", "")),
            "crawler_batch_id": staged_unit.get("crawler_batch_id", existing_unit.get("crawler_batch_id", "")),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.units.update_one({"id": production_unit_id}, {"$set": update_data})
        action = "updated"
        
        logger.info(f"Updated existing production unit {production_unit_id} from staging {unit_id}")
    else:
        # Step 3: Create NEW production unit
        production_unit_id = str(uuid.uuid4())
        production_unit = {
            "id": production_unit_id,
            "building_id": production_building_id,
            "unit_number": staged_unit["unit_number"],
            "rent": staged_unit["rent"],
            "bedrooms": staged_unit["bedrooms"],
            "bathrooms": staged_unit["bathrooms"],
            "square_feet": staged_unit.get("square_feet"),
            "available_date": staged_unit.get("available_date", "Immediate"),
            "amenities": staged_unit.get("amenities", []),
            "images": staged_unit.get("images", []),
            "description": staged_unit.get("description", ""),
            "is_available": staged_unit.get("is_available", True),
            "is_featured": False,
            "latitude": staged_unit.get("latitude"),
            "longitude": staged_unit.get("longitude"),
            # Verification flags
            "is_verified": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verified_by": user.id,
            # Source metadata
            "crawler_source": staged_unit.get("crawler_source", ""),
            "crawler_batch_id": staged_unit.get("crawler_batch_id", ""),
            "original_staging_id": unit_id,
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.units.insert_one(production_unit)
    
    # Step 4: Update staging unit status
    await db.units_staging.update_one(
        {"id": unit_id},
        {
            "$set": {
                "review_status": "approved",
                "matched_production_id": production_unit_id,
                "reviewer_notes": notes,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    logger.info(f"Approved staging unit {unit_id} -> production unit {production_unit_id}")
    
    return {
        "message": f"Unit approved and {'updated in' if action == 'updated' else 'moved to'} production",
        "staging_id": unit_id,
        "production_id": production_unit_id,
        "building_id": production_building_id,
        "unit_number": staged_unit["unit_number"],
        "action": action,
        "approved_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/staging/reject/{unit_id}")
async def reject_staging_unit(
    unit_id: str,
    reason: str = Query(..., description="Reason for rejection"),
    user: User = Depends(require_admin)
):
    """
    Reject a staged unit.
    
    The unit remains in staging with status='rejected' for audit purposes.
    """
    # Get the staged unit
    staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staged_unit:
        raise HTTPException(status_code=404, detail="Staged unit not found")
    
    if staged_unit.get("review_status") == "rejected":
        raise HTTPException(status_code=400, detail="Unit already rejected")
    
    if staged_unit.get("review_status") == "approved":
        raise HTTPException(status_code=400, detail="Cannot reject an already approved unit")
    
    # Update staging unit status
    await db.units_staging.update_one(
        {"id": unit_id},
        {
            "$set": {
                "review_status": "rejected",
                "reviewer_notes": reason,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    logger.info(f"Rejected staging unit {unit_id}: {reason}")
    
    return {
        "message": "Unit rejected",
        "staging_id": unit_id,
        "reason": reason,
        "rejected_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/staging/approve-batch")
async def approve_batch_staging_units(
    unit_ids: List[str] = Query(..., description="List of unit IDs to approve"),
    notes: Optional[str] = Query(None, description="Optional batch approval notes"),
    user: User = Depends(require_admin)
):
    """
    Approve multiple staged units in batch.
    
    Returns results for each unit (success or failure reason).
    """
    results = []
    approved_count = 0
    failed_count = 0
    
    for unit_id in unit_ids:
        try:
            # Get the staged unit
            staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
            if not staged_unit:
                results.append({"unit_id": unit_id, "status": "failed", "reason": "Not found"})
                failed_count += 1
                continue
            
            if staged_unit.get("review_status") == "approved":
                results.append({"unit_id": unit_id, "status": "skipped", "reason": "Already approved"})
                continue
            
            # Use the single approve endpoint logic
            building_id = staged_unit["building_id"]
            production_building_id = building_id
            
            # Check building
            production_building = await db.buildings.find_one({"id": building_id}, {"_id": 0})
            
            if not production_building:
                staged_building = await db.buildings_staging.find_one({"id": building_id}, {"_id": 0})
                if staged_building:
                    # Auto-create building
                    production_building_id = str(uuid.uuid4())
                    new_building = {
                        "id": production_building_id,
                        "name": staged_building["name"],
                        "address": staged_building["address"],
                        "neighborhood": staged_building["neighborhood"],
                        "city": staged_building["city"],
                        "state": staged_building["state"],
                        "zip_code": staged_building["zip_code"],
                        "source_url": staged_building["source_url"],
                        "latitude": staged_building.get("latitude"),
                        "longitude": staged_building.get("longitude"),
                        "crawler_source": staged_building.get("crawler_source", ""),
                        "original_staging_id": building_id,
                        "is_verified": True,
                        "verified_at": datetime.now(timezone.utc).isoformat(),
                        "verified_by": user.id,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.buildings.insert_one(new_building)
                    await db.buildings_staging.update_one(
                        {"id": building_id},
                        {"$set": {"review_status": "promoted", "matched_production_id": production_building_id}}
                    )
                else:
                    results.append({"unit_id": unit_id, "status": "failed", "reason": "Building not found"})
                    failed_count += 1
                    continue
            
            # Check for duplicates
            normalized_unit = staged_unit.get("normalized_unit_number", staged_unit["unit_number"])
            existing = await db.units.find_one({
                "building_id": production_building_id,
                "$or": [{"unit_number": staged_unit["unit_number"]}, {"unit_number": normalized_unit}]
            })
            
            if existing:
                await db.units_staging.update_one(
                    {"id": unit_id},
                    {"$set": {"review_status": "rejected", "reviewer_notes": f"Duplicate of {existing['id']}"}}
                )
                results.append({"unit_id": unit_id, "status": "rejected", "reason": f"Duplicate of {existing['id']}"})
                failed_count += 1
                continue
            
            # Create production unit
            production_unit_id = str(uuid.uuid4())
            production_unit = {
                "id": production_unit_id,
                "building_id": production_building_id,
                "unit_number": staged_unit["unit_number"],
                "rent": staged_unit["rent"],
                "bedrooms": staged_unit["bedrooms"],
                "bathrooms": staged_unit["bathrooms"],
                "square_feet": staged_unit.get("square_feet"),
                "available_date": staged_unit.get("available_date", "Immediate"),
                "amenities": staged_unit.get("amenities", []),
                "images": staged_unit.get("images", []),
                "description": staged_unit.get("description", ""),
                "is_available": True,
                "is_featured": False,
                "is_verified": True,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "verified_by": user.id,
                "crawler_source": staged_unit.get("crawler_source", ""),
                "crawler_batch_id": staged_unit.get("crawler_batch_id", ""),
                "original_staging_id": unit_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.units.insert_one(production_unit)
            await db.units_staging.update_one(
                {"id": unit_id},
                {
                    "$set": {
                        "review_status": "approved",
                        "matched_production_id": production_unit_id,
                        "reviewer_notes": notes,
                        "reviewed_by": user.id,
                        "reviewed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            results.append({
                "unit_id": unit_id,
                "status": "approved",
                "production_id": production_unit_id
            })
            approved_count += 1
            
        except Exception as e:
            results.append({"unit_id": unit_id, "status": "failed", "reason": str(e)})
            failed_count += 1
    
    return {
        "message": f"Batch approval complete: {approved_count} approved, {failed_count} failed",
        "approved_count": approved_count,
        "failed_count": failed_count,
        "results": results
    }


@router.post("/staging/reject-batch")
async def reject_batch_staging_units(
    unit_ids: List[str] = Query(..., description="List of unit IDs to reject"),
    reason: str = Query(..., description="Rejection reason"),
    user: User = Depends(require_admin)
):
    """
    Reject multiple staged units in batch.
    """
    result = await db.units_staging.update_many(
        {"id": {"$in": unit_ids}, "review_status": "pending"},
        {
            "$set": {
                "review_status": "rejected",
                "reviewer_notes": reason,
                "reviewed_by": user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": f"{result.modified_count} units rejected",
        "rejected_count": result.modified_count,
        "reason": reason
    }



@router.post("/admin/staging/units/bulk-delete")
async def bulk_delete_staging_units(
    input: BulkDeleteInput,
    user: User = Depends(require_admin)
):
    """
    Bulk delete staging units.
    """
    if not input.ids:
        raise HTTPException(status_code=400, detail="No unit IDs provided")
    
    result = await db.units_staging.delete_many({"id": {"$in": input.ids}})
    
    logger.info(f"Admin {user.email} bulk deleted {result.deleted_count} staging units")
    
    return {
        "message": f"{result.deleted_count} staging unit(s) deleted",
        "deleted_count": result.deleted_count
    }


@router.post("/admin/units/bulk-delete")
async def bulk_delete_production_units(
    input: BulkDeleteInput,
    user: User = Depends(require_admin)
):
    """
    Bulk delete production units.
    """
    if not input.ids:
        raise HTTPException(status_code=400, detail="No unit IDs provided")
    
    # Delete units
    result = await db.units.delete_many({"id": {"$in": input.ids}})
    
    # Also delete any associated favorites
    await db.favorites.delete_many({"unit_id": {"$in": input.ids}})
    
    logger.info(f"Admin {user.email} bulk deleted {result.deleted_count} production units")
    
    return {
        "message": f"{result.deleted_count} unit(s) deleted from production",
        "deleted_count": result.deleted_count
    }


@router.post("/admin/staging/units/bulk-approve")
async def bulk_approve_staging_units(
    input: BulkDeleteInput,  # Reusing the same input model (just needs ids)
    user: User = Depends(require_admin)
):
    """
    Bulk approve staging units and promote them to production.
    """
    if not input.ids:
        raise HTTPException(status_code=400, detail="No unit IDs provided")
    
    approved_count = 0
    errors = []
    
    for unit_id in input.ids:
        try:
            # Get the staged unit
            staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
            if not staged_unit:
                errors.append(f"Unit {unit_id} not found")
                continue
            
            if staged_unit.get("review_status") == "approved":
                errors.append(f"Unit {unit_id} already approved")
                continue
            
            # Get or create building
            building_id = staged_unit.get('building_id')
            if not building_id:
                # Try to find or create building from staging data
                building_name = staged_unit.get('building_name', 'Unknown Building')
                building_address = staged_unit.get('building_address', '')
                
                existing_building = await db.buildings.find_one({
                    '$or': [
                        {'name': building_name},
                        {'address': building_address}
                    ]
                }, {"_id": 0})
                
                if existing_building:
                    building_id = existing_building['id']
                else:
                    # Create new building
                    import uuid
                    building_id = str(uuid.uuid4())
                    new_building = {
                        'id': building_id,
                        'name': building_name,
                        'address': building_address,
                        'neighborhood': staged_unit.get('neighborhood', ''),
                        'city': staged_unit.get('city', 'New York'),
                        'state': staged_unit.get('state', 'NY'),
                        'images': staged_unit.get('building_images', []),
                        'amenities': staged_unit.get('amenities', []),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    await db.buildings.insert_one(new_building)
                    logger.info(f"Created new building: {building_name} ({building_id})")
            
            # Create production unit
            import uuid
            production_unit = {
                'id': str(uuid.uuid4()),
                'building_id': building_id,
                'unit_number': staged_unit.get('unit_number', 'N/A'),
                'rent': staged_unit.get('rent', 0),
                'bedrooms': staged_unit.get('bedrooms', 0),
                'bathrooms': staged_unit.get('bathrooms', 1),
                'sqft': staged_unit.get('sqft'),
                'images': staged_unit.get('images', []),
                'amenities': staged_unit.get('amenities', []),
                'is_available': True,
                'available_date': staged_unit.get('available_date'),
                'description': staged_unit.get('description', ''),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'promoted_from_staging': unit_id,
                'promoted_by': user.email,
                'promoted_at': datetime.now(timezone.utc).isoformat()
            }
            
            await db.units.insert_one(production_unit)
            
            # Mark staging unit as approved
            await db.units_staging.update_one(
                {"id": unit_id},
                {
                    "$set": {
                        "review_status": "approved",
                        "reviewed_by": user.email,
                        "reviewed_at": datetime.now(timezone.utc).isoformat(),
                        "production_unit_id": production_unit['id']
                    }
                }
            )
            
            approved_count += 1
            logger.info(f"Bulk approved unit {unit_id} -> production {production_unit['id']}")
            
        except Exception as e:
            logger.error(f"Error approving unit {unit_id}: {e}")
            errors.append(f"Unit {unit_id}: {str(e)}")
            continue
    
    logger.info(f"Admin {user.email} bulk approved {approved_count} staging units")
    
    return {
        "message": f"{approved_count} unit(s) approved and added to production",
        "approved_count": approved_count,
        "errors": errors if errors else None
    }

# ============ PROMOTION SERVICE ENDPOINTS ============

@router.post("/staging/promote/{unit_id}")
async def promote_staging_unit_via_service(
    unit_id: str,
    notes: Optional[str] = Query(None, description="Optional promotion notes"),
    user: User = Depends(require_admin)
):
    """
    Promote a staged unit to production using the promotion service.
    
    Promotion rules:
    - If production unit exists → update price/status only
    - If not → create new production unit
    - Preserves history: price_changes, status_changes
    """
    if not PROMOTION_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Promotion service not available")
    
    # Get the staged unit
    staged_unit = await db.units_staging.find_one({"id": unit_id}, {"_id": 0})
    if not staged_unit:
        raise HTTPException(status_code=404, detail="Staged unit not found")
    
    if staged_unit.get("review_status") == "approved":
        raise HTTPException(status_code=400, detail="Unit already approved/promoted")
    
    # Get promotion service
    promotion_service = promotion_service_functions['get_promotion_service'](db)
    
    try:
        result = await promotion_service.promote_unit(
            staged_unit=staged_unit,
            approved_by=user.id,
            notes=notes
        )
        
        return {
            "message": f"Unit {result['action']} successfully",
            "staging_id": result["staging_id"],
            "production_id": result["production_id"],
            "action": result["action"],
            "changes": result["changes"],
            "building_created": result["building_created"],
            "promoted_at": result["promoted_at"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Promotion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/staging/promote-batch")
async def promote_batch_staging_units(
    unit_ids: List[str] = Query(..., description="List of unit IDs to promote"),
    notes: Optional[str] = Query(None, description="Optional batch promotion notes"),
    user: User = Depends(require_admin)
):
    """
    Promote multiple staged units to production in batch.
    
    Returns results for each unit showing whether it was created or updated.
    """
    if not PROMOTION_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Promotion service not available")
    
    promotion_service = promotion_service_functions['get_promotion_service'](db)
    
    results = await promotion_service.promote_batch(
        staging_ids=unit_ids,
        approved_by=user.id,
        notes=notes
    )
    
    return {
        "message": f"Batch promotion complete: {results['created']} created, {results['updated']} updated, {results['failed']} failed",
        "total": results["total"],
        "created": results["created"],
        "updated": results["updated"],
        "failed": results["failed"],
        "details": results["details"]
    }



@router.post("/admin/staging/backfill-addresses")
async def backfill_staging_addresses(user: User = Depends(require_admin)):
    """
    Backfill missing addresses on staging units by looking up their parent building.
    Checks both staging buildings and live buildings collections.
    """
    # Get all live buildings
    live_buildings = await db.buildings.find({}, {'_id': 0, 'id': 1, 'name': 1, 'address': 1}).to_list(500)
    live_map = {b['id']: b for b in live_buildings}
    
    # Get all staging buildings
    staging_buildings = await db.buildings_staging.find({}, {'_id': 0, 'id': 1, 'name': 1, 'address': 1}).to_list(500)
    staging_map = {b['id']: b for b in staging_buildings}
    
    # Find staging units missing addresses
    missing_units = await db.units_staging.find({
        '$or': [
            {'building_address': ''},
            {'building_address': None},
            {'building_address': {'$exists': False}}
        ]
    }, {'_id': 0, 'id': 1, 'building_id': 1, 'building_name': 1}).to_list(5000)
    
    fixed = 0
    still_missing = 0
    
    for u in missing_units:
        bid = u.get('building_id', '')
        addr = None
        name = None
        
        if bid in live_map and live_map[bid].get('address'):
            addr = live_map[bid]['address']
            name = live_map[bid].get('name', '')
        elif bid in staging_map and staging_map[bid].get('address'):
            addr = staging_map[bid]['address']
            name = staging_map[bid].get('name', '')
        
        if addr:
            update_fields = {'building_address': addr}
            if name and not u.get('building_name'):
                update_fields['building_name'] = name
            await db.units_staging.update_one({'id': u['id']}, {'$set': update_fields})
            fixed += 1
        else:
            still_missing += 1
    
    return {
        'message': f'Backfilled {fixed} staging units with addresses. {still_missing} still missing (no parent building address found).',
        'total_checked': len(missing_units),
        'fixed': fixed,
        'still_missing': still_missing
    }
