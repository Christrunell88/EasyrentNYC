"""
Promotion Service for NoFeesApts.com
====================================
Handles moving approved staged listings into production with:
- Smart duplicate detection and updates
- Price change history tracking
- Status change history tracking
- Full audit trail

AUTHORIZATION:
This service is authorized to write to production collections because:
1. It is triggered ONLY by manual admin approval
2. All writes are logged and audited
3. It uses the WriteSource.ADMIN_APPROVAL authorization
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

logger = logging.getLogger(__name__)

# Import access control for authorized production writes
try:
    from db_access_control import (
        DatabaseAccessControl,
        WriteSource,
        get_access_control,
        init_access_control
    )
    ACCESS_CONTROL_AVAILABLE = True
except ImportError:
    ACCESS_CONTROL_AVAILABLE = False
    logger.warning("Access control not available - using direct writes")


class PromotionService:
    """
    Service for promoting staged listings to production.
    
    AUTHORIZED SOURCE: WriteSource.ADMIN_APPROVAL
    
    Promotion rules:
    - If production unit exists → update price/status only
    - If not → create new production unit
    - Preserve history: price_changes, status_changes
    
    This service is the ONLY authorized way for listings to move
    from staging to production (except for internal leasing feeds).
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._access_control = None
        if ACCESS_CONTROL_AVAILABLE:
            self._access_control = get_access_control(db)
    
    async def _authorized_production_insert(
        self,
        collection: str,
        document: Dict,
        user_id: str
    ):
        """
        Insert a document to production with proper authorization.
        """
        if ACCESS_CONTROL_AVAILABLE and self._access_control:
            return await self._access_control.authorized_production_write(
                collection=collection,
                operation='insert',
                source=WriteSource.ADMIN_APPROVAL,
                user_id=user_id,
                document=document
            )
        else:
            # Fallback for testing without access control
            await self.db[collection].insert_one(document)
            logger.info(f"Production insert (no access control): {collection}")
            return {"inserted_id": document.get('id')}
    
    async def _authorized_production_update(
        self,
        collection: str,
        document_id: str,
        updates: Dict,
        user_id: str
    ):
        """
        Update a document in production with proper authorization.
        """
        if ACCESS_CONTROL_AVAILABLE and self._access_control:
            updates['id'] = document_id
            return await self._access_control.authorized_production_write(
                collection=collection,
                operation='update',
                source=WriteSource.ADMIN_APPROVAL,
                user_id=user_id,
                document=updates
            )
        else:
            # Fallback for testing
            result = await self.db[collection].update_one(
                {"id": document_id},
                {"$set": updates}
            )
            return {"matched": result.matched_count, "modified": result.modified_count}
    
    async def find_matching_production_unit(
        self,
        building_id: str,
        unit_number: str,
        normalized_unit_number: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find a matching production unit by building and unit number.
        
        Checks:
        1. Exact unit number match
        2. Normalized unit number match
        """
        query = {
            "building_id": building_id,
            "$or": [
                {"unit_number": unit_number}
            ]
        }
        
        if normalized_unit_number:
            query["$or"].append({"unit_number": normalized_unit_number})
        
        return await self.db.units.find_one(query, {"_id": 0})
    
    async def find_matching_production_building(
        self,
        building_id: str,
        normalized_address: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find a matching production building.
        
        Checks:
        1. Exact ID match
        2. Normalized address match (for cross-reference)
        """
        # First try exact ID match
        building = await self.db.buildings.find_one({"id": building_id}, {"_id": 0})
        if building:
            return building
        
        # If not found and we have a normalized address, try that
        if normalized_address:
            building = await self.db.buildings.find_one(
                {"normalized_address": normalized_address},
                {"_id": 0}
            )
            if building:
                return building
        
        return None
    
    async def record_price_change(
        self,
        unit_id: str,
        old_price: float,
        new_price: float,
        source: str,
        changed_by: Optional[str] = None
    ) -> Dict:
        """
        Record a price change in the unit's history.
        """
        price_change = {
            "id": str(uuid.uuid4()),
            "unit_id": unit_id,
            "old_price": old_price,
            "new_price": new_price,
            "change_amount": new_price - old_price,
            "change_percent": ((new_price - old_price) / old_price * 100) if old_price > 0 else 0,
            "source": source,
            "changed_by": changed_by,
            "changed_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.price_changes.insert_one(price_change)
        logger.info(f"Recorded price change for unit {unit_id}: ${old_price} -> ${new_price}")
        
        return price_change
    
    async def record_status_change(
        self,
        unit_id: str,
        old_status: bool,
        new_status: bool,
        source: str,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Record a status change (availability) in the unit's history.
        """
        status_change = {
            "id": str(uuid.uuid4()),
            "unit_id": unit_id,
            "old_status": "available" if old_status else "unavailable",
            "new_status": "available" if new_status else "unavailable",
            "source": source,
            "reason": reason,
            "changed_by": changed_by,
            "changed_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.status_changes.insert_one(status_change)
        logger.info(f"Recorded status change for unit {unit_id}: {status_change['old_status']} -> {status_change['new_status']}")
        
        return status_change
    
    async def get_unit_price_history(self, unit_id: str, limit: int = 50) -> List[Dict]:
        """Get price change history for a unit."""
        history = await self.db.price_changes.find(
            {"unit_id": unit_id},
            {"_id": 0}
        ).sort("changed_at", -1).limit(limit).to_list(limit)
        return history
    
    async def get_unit_status_history(self, unit_id: str, limit: int = 50) -> List[Dict]:
        """Get status change history for a unit."""
        history = await self.db.status_changes.find(
            {"unit_id": unit_id},
            {"_id": 0}
        ).sort("changed_at", -1).limit(limit).to_list(limit)
        return history
    
    async def promote_unit(
        self,
        staged_unit: Dict,
        approved_by: str,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Promote a staged unit to production.
        
        If production unit exists:
        - Update price if changed
        - Update status if changed
        - Record changes in history
        
        If production unit doesn't exist:
        - Create new production unit
        
        Returns:
            Dict with promotion results
        """
        building_id = staged_unit["building_id"]
        unit_number = staged_unit["unit_number"]
        normalized_unit_number = staged_unit.get("normalized_unit_number")
        staging_id = staged_unit["id"]
        
        result = {
            "staging_id": staging_id,
            "unit_number": unit_number,
            "action": None,
            "production_id": None,
            "changes": [],
            "building_created": False,
            "promoted_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Step 1: Ensure building exists in production
        production_building = await self.find_matching_production_building(
            building_id,
            staged_unit.get("building_normalized_address")
        )
        
        if not production_building:
            # Try to get building from staging
            staged_building = await self.db.buildings_staging.find_one(
                {"id": building_id},
                {"_id": 0}
            )
            
            if staged_building:
                # Create production building
                production_building_id = str(uuid.uuid4())
                production_building = {
                    "id": production_building_id,
                    "name": staged_building["name"],
                    "address": staged_building["address"],
                    "normalized_address": staged_building.get("normalized_address"),
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
                    "verified_by": approved_by,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db.buildings.insert_one(production_building)
                
                # Update staging building
                await self.db.buildings_staging.update_one(
                    {"id": building_id},
                    {
                        "$set": {
                            "review_status": "promoted",
                            "matched_production_id": production_building_id,
                            "reviewed_by": approved_by,
                            "reviewed_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                building_id = production_building_id
                result["building_created"] = True
                logger.info(f"Created production building {production_building_id} from staging")
            else:
                raise ValueError(f"Building {building_id} not found in production or staging")
        else:
            building_id = production_building["id"]
        
        # Step 2: Check if production unit exists
        existing_unit = await self.find_matching_production_unit(
            building_id,
            unit_number,
            normalized_unit_number
        )
        
        if existing_unit:
            # UPDATE existing production unit
            result["action"] = "updated"
            result["production_id"] = existing_unit["id"]
            
            updates = {}
            
            # Check price change
            old_price = existing_unit.get("rent", 0)
            new_price = staged_unit.get("rent", 0)
            
            if old_price != new_price and new_price > 0:
                updates["rent"] = new_price
                await self.record_price_change(
                    unit_id=existing_unit["id"],
                    old_price=old_price,
                    new_price=new_price,
                    source=staged_unit.get("crawler_source", "staging"),
                    changed_by=approved_by
                )
                result["changes"].append({
                    "field": "rent",
                    "old": old_price,
                    "new": new_price
                })
            
            # Check status change
            old_status = existing_unit.get("is_available", True)
            new_status = staged_unit.get("is_available", True)
            
            if old_status != new_status:
                updates["is_available"] = new_status
                await self.record_status_change(
                    unit_id=existing_unit["id"],
                    old_status=old_status,
                    new_status=new_status,
                    source=staged_unit.get("crawler_source", "staging"),
                    changed_by=approved_by,
                    reason="Updated from staging promotion"
                )
                result["changes"].append({
                    "field": "is_available",
                    "old": old_status,
                    "new": new_status
                })
            
            # Update other fields if they've changed
            update_fields = [
                "square_feet", "available_date", "amenities", 
                "images", "description", "bathrooms"
            ]
            
            for field in update_fields:
                staged_value = staged_unit.get(field)
                existing_value = existing_unit.get(field)
                
                if staged_value is not None and staged_value != existing_value:
                    # Only update if staged value is meaningful
                    if field == "images" and not staged_value:
                        continue  # Don't clear images
                    if field == "amenities" and not staged_value:
                        continue  # Don't clear amenities
                    
                    updates[field] = staged_value
                    result["changes"].append({
                        "field": field,
                        "old": existing_value,
                        "new": staged_value
                    })
            
            # Apply updates
            if updates:
                updates["updated_at"] = datetime.now(timezone.utc).isoformat()
                updates["last_staged_update"] = staging_id
                
                await self.db.units.update_one(
                    {"id": existing_unit["id"]},
                    {"$set": updates}
                )
                
                logger.info(f"Updated production unit {existing_unit['id']} with {len(result['changes'])} changes")
            else:
                result["changes"].append({"field": "none", "message": "No changes detected"})
        
        else:
            # CREATE new production unit
            result["action"] = "created"
            production_unit_id = str(uuid.uuid4())
            result["production_id"] = production_unit_id
            
            production_unit = {
                "id": production_unit_id,
                "building_id": building_id,
                "unit_number": unit_number,
                "rent": staged_unit.get("rent", 0),
                "bedrooms": staged_unit.get("bedrooms", 0),
                "bathrooms": staged_unit.get("bathrooms", 1.0),
                "square_feet": staged_unit.get("square_feet"),
                "available_date": staged_unit.get("available_date", "Immediate"),
                "amenities": staged_unit.get("amenities", []),
                "images": staged_unit.get("images", []),
                "description": staged_unit.get("description", ""),
                "is_available": staged_unit.get("is_available", True),
                "is_featured": False,
                "latitude": staged_unit.get("latitude"),
                "longitude": staged_unit.get("longitude"),
                # Verification
                "is_verified": True,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "verified_by": approved_by,
                # Source metadata
                "crawler_source": staged_unit.get("crawler_source", ""),
                "crawler_batch_id": staged_unit.get("crawler_batch_id", ""),
                "original_staging_id": staging_id,
                # Timestamps
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.units.insert_one(production_unit)
            
            # Record initial price in history
            if production_unit["rent"] > 0:
                await self.record_price_change(
                    unit_id=production_unit_id,
                    old_price=0,
                    new_price=production_unit["rent"],
                    source=staged_unit.get("crawler_source", "staging"),
                    changed_by=approved_by
                )
            
            # Record initial status
            await self.record_status_change(
                unit_id=production_unit_id,
                old_status=False,  # Didn't exist before
                new_status=production_unit["is_available"],
                source=staged_unit.get("crawler_source", "staging"),
                changed_by=approved_by,
                reason="Initial creation from staging"
            )
            
            logger.info(f"Created new production unit {production_unit_id}")
        
        # Step 3: Update staging record
        await self.db.units_staging.update_one(
            {"id": staging_id},
            {
                "$set": {
                    "review_status": "approved",
                    "matched_production_id": result["production_id"],
                    "promotion_action": result["action"],
                    "reviewer_notes": notes,
                    "reviewed_by": approved_by,
                    "reviewed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return result
    
    async def promote_batch(
        self,
        staging_ids: List[str],
        approved_by: str,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Promote multiple staged units to production.
        
        Returns:
            Summary of promotion results
        """
        results = {
            "total": len(staging_ids),
            "created": 0,
            "updated": 0,
            "failed": 0,
            "details": []
        }
        
        for staging_id in staging_ids:
            try:
                # Get staged unit
                staged_unit = await self.db.units_staging.find_one(
                    {"id": staging_id},
                    {"_id": 0}
                )
                
                if not staged_unit:
                    results["failed"] += 1
                    results["details"].append({
                        "staging_id": staging_id,
                        "status": "failed",
                        "reason": "Not found"
                    })
                    continue
                
                if staged_unit.get("review_status") == "approved":
                    results["details"].append({
                        "staging_id": staging_id,
                        "status": "skipped",
                        "reason": "Already approved"
                    })
                    continue
                
                # Promote
                result = await self.promote_unit(staged_unit, approved_by, notes)
                
                if result["action"] == "created":
                    results["created"] += 1
                elif result["action"] == "updated":
                    results["updated"] += 1
                
                results["details"].append({
                    "staging_id": staging_id,
                    "status": "success",
                    "action": result["action"],
                    "production_id": result["production_id"],
                    "changes_count": len(result["changes"])
                })
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "staging_id": staging_id,
                    "status": "failed",
                    "reason": str(e)
                })
                logger.error(f"Failed to promote {staging_id}: {e}")
        
        return results


# Singleton instance creator
_promotion_service: Optional[PromotionService] = None

def get_promotion_service(db: AsyncIOMotorDatabase) -> PromotionService:
    """Get or create the promotion service instance."""
    global _promotion_service
    if _promotion_service is None:
        _promotion_service = PromotionService(db)
    return _promotion_service
