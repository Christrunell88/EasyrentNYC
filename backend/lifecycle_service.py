"""
Unit Lifecycle Management Service for NoFeesApts.com
=====================================================
Handles automated lifecycle transitions for apartment units:

1. STALE Detection: Units not updated in 14 days get marked as "stale"
2. RENTED Tracking: Units marked as rented maintain history
3. PRICE HISTORY: All price changes are tracked in history.price_changes
4. NO AUTO-DELETE: Units are never automatically deleted

Lifecycle States:
- available: Unit is available for rent
- stale: Unit hasn't been updated in 14+ days (needs verification)
- rented: Unit has been rented out
- unavailable: Unit is temporarily unavailable

This service runs on a schedule and can also be triggered manually.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

logger = logging.getLogger(__name__)

# Lifecycle configuration
STALE_THRESHOLD_DAYS = 14
LIFECYCLE_STATUSES = ['available', 'stale', 'rented', 'unavailable']


class UnitLifecycleService:
    """
    Service for managing unit lifecycle transitions.
    
    Key behaviors:
    - Marks units as "stale" if not updated within STALE_THRESHOLD_DAYS
    - Tracks all price changes in price_changes collection
    - Tracks all status changes in status_changes collection
    - NEVER deletes units automatically
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # ============ STALE DETECTION ============
    
    async def check_and_mark_stale_units(self) -> Dict[str, Any]:
        """
        Check all units and mark those not updated in 14+ days as "stale".
        
        Returns:
            Summary of units marked as stale
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS)
        cutoff_iso = cutoff_date.isoformat()
        
        # Find units that:
        # 1. Are currently available
        # 2. Haven't been updated since cutoff date
        # 3. Are not already marked as stale or rented
        query = {
            'is_available': True,
            'lifecycle_status': {'$nin': ['stale', 'rented']},
            '$or': [
                {'updated_at': {'$lt': cutoff_iso}},
                {'updated_at': {'$exists': False}}
            ]
        }
        
        # Also handle units without lifecycle_status field
        # (for backwards compatibility)
        query_legacy = {
            'is_available': True,
            'lifecycle_status': {'$exists': False},
            '$or': [
                {'updated_at': {'$lt': cutoff_iso}},
                {'updated_at': {'$exists': False}}
            ]
        }
        
        units_to_mark = await self.db.units.find(
            {'$or': [query, query_legacy]},
            {"_id": 0, "id": 1, "unit_number": 1, "building_id": 1, "updated_at": 1}
        ).to_list(10000)
        
        marked_count = 0
        marked_units = []
        
        for unit in units_to_mark:
            try:
                # Record the status change
                await self._record_status_change(
                    unit_id=unit['id'],
                    old_status='available',
                    new_status='stale',
                    source='lifecycle_service',
                    reason=f'No update for {STALE_THRESHOLD_DAYS}+ days'
                )
                
                # Update the unit
                await self.db.units.update_one(
                    {'id': unit['id']},
                    {
                        '$set': {
                            'lifecycle_status': 'stale',
                            'stale_since': datetime.now(timezone.utc).isoformat(),
                            'lifecycle_updated_at': datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                marked_count += 1
                marked_units.append({
                    'id': unit['id'],
                    'unit_number': unit.get('unit_number'),
                    'last_updated': unit.get('updated_at')
                })
                
            except Exception as e:
                logger.error(f"Error marking unit {unit['id']} as stale: {e}")
                continue
        
        result = {
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'threshold_days': STALE_THRESHOLD_DAYS,
            'cutoff_date': cutoff_iso,
            'units_marked_stale': marked_count,
            'marked_units': marked_units[:50]  # Limit details in response
        }
        
        logger.info(f"Stale check complete: {marked_count} units marked as stale")
        return result
    
    # ============ RENTED STATUS ============
    
    async def mark_unit_as_rented(
        self,
        unit_id: str,
        rented_date: Optional[str] = None,
        notes: Optional[str] = None,
        changed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a unit as rented.
        
        Args:
            unit_id: The unit to mark
            rented_date: When the unit was rented (default: now)
            notes: Optional notes about the rental
            changed_by: User who made the change
            
        Returns:
            Result of the operation
        """
        unit = await self.db.units.find_one({'id': unit_id}, {"_id": 0})
        if not unit:
            return {'success': False, 'error': 'Unit not found'}
        
        old_status = unit.get('lifecycle_status', 'available')
        
        # Record the status change
        await self._record_status_change(
            unit_id=unit_id,
            old_status=old_status,
            new_status='rented',
            source='manual' if changed_by else 'system',
            changed_by=changed_by,
            reason=notes
        )
        
        # Update the unit
        update_data = {
            'is_available': False,
            'lifecycle_status': 'rented',
            'rented_at': rented_date or datetime.now(timezone.utc).isoformat(),
            'rented_notes': notes,
            'lifecycle_updated_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.units.update_one(
            {'id': unit_id},
            {'$set': update_data}
        )
        
        logger.info(f"Unit {unit_id} marked as rented")
        
        return {
            'success': True,
            'unit_id': unit_id,
            'previous_status': old_status,
            'new_status': 'rented',
            'rented_at': update_data['rented_at']
        }
    
    async def mark_unit_as_available(
        self,
        unit_id: str,
        rent: Optional[float] = None,
        available_date: Optional[str] = None,
        notes: Optional[str] = None,
        changed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a unit as available again (e.g., after being rented or stale).
        
        Args:
            unit_id: The unit to mark
            rent: New rent amount (if changed)
            available_date: When available (default: Immediate)
            notes: Optional notes
            changed_by: User who made the change
            
        Returns:
            Result of the operation
        """
        unit = await self.db.units.find_one({'id': unit_id}, {"_id": 0})
        if not unit:
            return {'success': False, 'error': 'Unit not found'}
        
        old_status = unit.get('lifecycle_status', 'unknown')
        old_rent = unit.get('rent', 0)
        
        # Record status change
        await self._record_status_change(
            unit_id=unit_id,
            old_status=old_status,
            new_status='available',
            source='manual' if changed_by else 'system',
            changed_by=changed_by,
            reason=notes
        )
        
        # Record price change if rent changed
        if rent is not None and rent != old_rent:
            await self._record_price_change(
                unit_id=unit_id,
                old_price=old_rent,
                new_price=rent,
                source='manual' if changed_by else 'system',
                changed_by=changed_by
            )
        
        # Update the unit
        update_data = {
            'is_available': True,
            'lifecycle_status': 'available',
            'available_date': available_date or 'Immediate',
            'lifecycle_updated_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            # Clear stale/rented metadata
            'stale_since': None,
            'rented_at': None,
            'rented_notes': None
        }
        
        if rent is not None:
            update_data['rent'] = rent
        
        await self.db.units.update_one(
            {'id': unit_id},
            {'$set': update_data}
        )
        
        logger.info(f"Unit {unit_id} marked as available")
        
        return {
            'success': True,
            'unit_id': unit_id,
            'previous_status': old_status,
            'new_status': 'available',
            'price_changed': rent is not None and rent != old_rent
        }
    
    # ============ PRICE TRACKING ============
    
    async def update_unit_price(
        self,
        unit_id: str,
        new_price: float,
        source: str = 'manual',
        changed_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a unit's price and record the change in history.
        
        Args:
            unit_id: The unit to update
            new_price: The new rent price
            source: Source of the change (manual, crawler, etc.)
            changed_by: User/system making the change
            reason: Optional reason for the change
            
        Returns:
            Result including price change details
        """
        unit = await self.db.units.find_one({'id': unit_id}, {"_id": 0})
        if not unit:
            return {'success': False, 'error': 'Unit not found'}
        
        old_price = unit.get('rent', 0)
        
        # Don't record if price hasn't actually changed
        if old_price == new_price:
            return {
                'success': True,
                'unit_id': unit_id,
                'price_changed': False,
                'message': 'Price unchanged'
            }
        
        # Record price change in history
        price_change = await self._record_price_change(
            unit_id=unit_id,
            old_price=old_price,
            new_price=new_price,
            source=source,
            changed_by=changed_by,
            reason=reason
        )
        
        # Update the unit
        await self.db.units.update_one(
            {'id': unit_id},
            {
                '$set': {
                    'rent': new_price,
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'lifecycle_updated_at': datetime.now(timezone.utc).isoformat(),
                    # Clear stale status if unit was stale
                    'lifecycle_status': 'available' if unit.get('lifecycle_status') == 'stale' else unit.get('lifecycle_status', 'available'),
                    'stale_since': None
                }
            }
        )
        
        logger.info(f"Unit {unit_id} price updated: ${old_price} -> ${new_price}")
        
        return {
            'success': True,
            'unit_id': unit_id,
            'price_changed': True,
            'old_price': old_price,
            'new_price': new_price,
            'change_amount': new_price - old_price,
            'change_percent': ((new_price - old_price) / old_price * 100) if old_price > 0 else 0,
            'price_change_id': price_change['id']
        }
    
    async def _record_price_change(
        self,
        unit_id: str,
        old_price: float,
        new_price: float,
        source: str,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a price change in the price_changes collection.
        """
        change_record = {
            'id': str(uuid.uuid4()),
            'unit_id': unit_id,
            'old_price': old_price,
            'new_price': new_price,
            'change_amount': new_price - old_price,
            'change_percent': ((new_price - old_price) / old_price * 100) if old_price > 0 else 0,
            'source': source,
            'changed_by': changed_by,
            'reason': reason,
            'changed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.price_changes.insert_one(change_record)
        
        logger.debug(f"Price change recorded for unit {unit_id}: ${old_price} -> ${new_price}")
        
        return change_record
    
    async def _record_status_change(
        self,
        unit_id: str,
        old_status: str,
        new_status: str,
        source: str,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a status change in the status_changes collection.
        """
        change_record = {
            'id': str(uuid.uuid4()),
            'unit_id': unit_id,
            'old_status': old_status,
            'new_status': new_status,
            'source': source,
            'changed_by': changed_by,
            'reason': reason,
            'changed_at': datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.status_changes.insert_one(change_record)
        
        logger.debug(f"Status change recorded for unit {unit_id}: {old_status} -> {new_status}")
        
        return change_record
    
    # ============ HISTORY QUERIES ============
    
    async def get_unit_price_history(
        self,
        unit_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get price change history for a unit.
        """
        history = await self.db.price_changes.find(
            {'unit_id': unit_id},
            {"_id": 0}
        ).sort('changed_at', -1).limit(limit).to_list(limit)
        
        return history
    
    async def get_unit_status_history(
        self,
        unit_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get status change history for a unit.
        """
        history = await self.db.status_changes.find(
            {'unit_id': unit_id},
            {"_id": 0}
        ).sort('changed_at', -1).limit(limit).to_list(limit)
        
        return history
    
    async def get_unit_full_history(
        self,
        unit_id: str
    ) -> Dict[str, Any]:
        """
        Get complete history for a unit (price + status changes).
        """
        price_history = await self.get_unit_price_history(unit_id)
        status_history = await self.get_unit_status_history(unit_id)
        
        # Get current unit data
        unit = await self.db.units.find_one({'id': unit_id}, {"_id": 0})
        
        return {
            'unit_id': unit_id,
            'current_status': unit.get('lifecycle_status', 'available') if unit else None,
            'current_rent': unit.get('rent') if unit else None,
            'price_changes': price_history,
            'status_changes': status_history,
            'total_price_changes': len(price_history),
            'total_status_changes': len(status_history)
        }
    
    # ============ LIFECYCLE STATS ============
    
    async def get_lifecycle_stats(self) -> Dict[str, Any]:
        """
        Get statistics about unit lifecycle statuses.
        """
        # Count by lifecycle status
        available_count = await self.db.units.count_documents({
            '$or': [
                {'lifecycle_status': 'available'},
                {'lifecycle_status': {'$exists': False}, 'is_available': True}
            ]
        })
        
        stale_count = await self.db.units.count_documents({'lifecycle_status': 'stale'})
        rented_count = await self.db.units.count_documents({'lifecycle_status': 'rented'})
        unavailable_count = await self.db.units.count_documents({'lifecycle_status': 'unavailable'})
        
        # Count units approaching stale threshold
        warning_cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS - 3)
        approaching_stale = await self.db.units.count_documents({
            'is_available': True,
            'lifecycle_status': {'$nin': ['stale', 'rented']},
            'updated_at': {'$lt': warning_cutoff.isoformat(), '$gt': (datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS)).isoformat()}
        })
        
        # Recent price changes (last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_price_changes = await self.db.price_changes.count_documents({
            'changed_at': {'$gt': week_ago.isoformat()}
        })
        
        # Recent status changes (last 7 days)
        recent_status_changes = await self.db.status_changes.count_documents({
            'changed_at': {'$gt': week_ago.isoformat()}
        })
        
        return {
            'lifecycle_counts': {
                'available': available_count,
                'stale': stale_count,
                'rented': rented_count,
                'unavailable': unavailable_count
            },
            'approaching_stale': approaching_stale,
            'stale_threshold_days': STALE_THRESHOLD_DAYS,
            'recent_activity': {
                'price_changes_7d': recent_price_changes,
                'status_changes_7d': recent_status_changes
            },
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    # ============ BULK OPERATIONS ============
    
    async def refresh_stale_units(
        self,
        unit_ids: List[str],
        changed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark multiple stale units as available again (after verification).
        """
        refreshed = 0
        errors = []
        
        for unit_id in unit_ids:
            try:
                result = await self.mark_unit_as_available(
                    unit_id=unit_id,
                    notes='Refreshed from stale status',
                    changed_by=changed_by
                )
                if result.get('success'):
                    refreshed += 1
                else:
                    errors.append({'unit_id': unit_id, 'error': result.get('error')})
            except Exception as e:
                errors.append({'unit_id': unit_id, 'error': str(e)})
        
        return {
            'refreshed_count': refreshed,
            'error_count': len(errors),
            'errors': errors[:10]  # Limit error details
        }
    
    async def bulk_mark_rented(
        self,
        unit_ids: List[str],
        changed_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark multiple units as rented.
        """
        marked = 0
        errors = []
        
        for unit_id in unit_ids:
            try:
                result = await self.mark_unit_as_rented(
                    unit_id=unit_id,
                    notes=notes,
                    changed_by=changed_by
                )
                if result.get('success'):
                    marked += 1
                else:
                    errors.append({'unit_id': unit_id, 'error': result.get('error')})
            except Exception as e:
                errors.append({'unit_id': unit_id, 'error': str(e)})
        
        return {
            'marked_rented_count': marked,
            'error_count': len(errors),
            'errors': errors[:10]
        }


# ============ SCHEDULER FUNCTION ============

async def run_stale_check(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Run the stale units check. Called by scheduler.
    """
    service = UnitLifecycleService(db)
    return await service.check_and_mark_stale_units()


# ============ SINGLETON ============

_lifecycle_service: Optional[UnitLifecycleService] = None


def get_lifecycle_service(db: AsyncIOMotorDatabase) -> UnitLifecycleService:
    """Get or create the lifecycle service instance."""
    global _lifecycle_service
    if _lifecycle_service is None:
        _lifecycle_service = UnitLifecycleService(db)
    return _lifecycle_service
