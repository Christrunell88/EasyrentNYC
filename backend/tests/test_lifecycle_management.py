"""
Test Suite for Unit Lifecycle Management
=========================================
Verifies:
1. Stale detection (units not updated in 14 days)
2. Rented status tracking
3. Price change history
4. Status change history
5. No auto-deletion
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

from lifecycle_service import UnitLifecycleService, get_lifecycle_service, STALE_THRESHOLD_DAYS

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']


async def run_lifecycle_tests():
    """Run all lifecycle management tests"""
    print("\n" + "="*60)
    print("UNIT LIFECYCLE MANAGEMENT TEST SUITE")
    print("="*60 + "\n")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    service = get_lifecycle_service(db)
    
    passed = 0
    failed = 0
    
    # ============ Test 1: Create test unit and mark as stale ============
    print("\n--- Test 1: Stale detection logic ---")
    try:
        # Create a test unit with old updated_at
        test_unit_id = str(uuid.uuid4())
        old_date = (datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS + 1)).isoformat()
        
        test_unit = {
            'id': test_unit_id,
            'building_id': 'test-building-lifecycle',
            'unit_number': 'LIFECYCLE-1',
            'rent': 2500,
            'bedrooms': 1,
            'bathrooms': 1,
            'is_available': True,
            'lifecycle_status': 'available',
            'updated_at': old_date,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(test_unit)
        
        # Run stale check
        result = await service.check_and_mark_stale_units()
        
        # Verify unit is now stale
        updated_unit = await db.units.find_one({'id': test_unit_id})
        assert updated_unit['lifecycle_status'] == 'stale', f"Expected 'stale', got '{updated_unit.get('lifecycle_status')}'"
        assert updated_unit.get('stale_since') is not None
        
        # Cleanup
        await db.units.delete_one({'id': test_unit_id})
        await db.status_changes.delete_many({'unit_id': test_unit_id})
        
        print(f"✅ PASSED: Unit correctly marked as stale after {STALE_THRESHOLD_DAYS}+ days")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # ============ Test 2: Mark unit as rented ============
    print("\n--- Test 2: Mark unit as rented ---")
    try:
        test_unit_id = str(uuid.uuid4())
        test_unit = {
            'id': test_unit_id,
            'building_id': 'test-building-lifecycle',
            'unit_number': 'LIFECYCLE-2',
            'rent': 3000,
            'bedrooms': 2,
            'bathrooms': 1,
            'is_available': True,
            'lifecycle_status': 'available',
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(test_unit)
        
        # Mark as rented
        result = await service.mark_unit_as_rented(
            unit_id=test_unit_id,
            notes='Rented to test tenant',
            changed_by='test-admin'
        )
        
        assert result['success'] == True
        assert result['new_status'] == 'rented'
        
        # Verify in database
        updated_unit = await db.units.find_one({'id': test_unit_id})
        assert updated_unit['lifecycle_status'] == 'rented'
        assert updated_unit['is_available'] == False
        assert updated_unit.get('rented_at') is not None
        
        # Verify status change was recorded
        status_change = await db.status_changes.find_one({'unit_id': test_unit_id, 'new_status': 'rented'})
        assert status_change is not None
        
        # Cleanup
        await db.units.delete_one({'id': test_unit_id})
        await db.status_changes.delete_many({'unit_id': test_unit_id})
        
        print("✅ PASSED: Unit correctly marked as rented with history")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # ============ Test 3: Price change tracking ============
    print("\n--- Test 3: Price change tracking ---")
    try:
        test_unit_id = str(uuid.uuid4())
        test_unit = {
            'id': test_unit_id,
            'building_id': 'test-building-lifecycle',
            'unit_number': 'LIFECYCLE-3',
            'rent': 2000,
            'bedrooms': 1,
            'bathrooms': 1,
            'is_available': True,
            'lifecycle_status': 'available',
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(test_unit)
        
        # Update price
        result = await service.update_unit_price(
            unit_id=test_unit_id,
            new_price=2200,
            source='test',
            changed_by='test-admin',
            reason='Market adjustment'
        )
        
        assert result['success'] == True
        assert result['price_changed'] == True
        assert result['old_price'] == 2000
        assert result['new_price'] == 2200
        
        # Verify price change was recorded
        price_changes = await service.get_unit_price_history(test_unit_id)
        assert len(price_changes) >= 1
        assert price_changes[0]['old_price'] == 2000
        assert price_changes[0]['new_price'] == 2200
        
        # Update price again
        await service.update_unit_price(
            unit_id=test_unit_id,
            new_price=2100,
            source='test',
            changed_by='test-admin',
            reason='Price reduction'
        )
        
        # Verify full history
        price_changes = await service.get_unit_price_history(test_unit_id)
        assert len(price_changes) >= 2
        
        # Cleanup
        await db.units.delete_one({'id': test_unit_id})
        await db.price_changes.delete_many({'unit_id': test_unit_id})
        
        print("✅ PASSED: Price changes correctly tracked in history")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # ============ Test 4: Mark available again (refresh) ============
    print("\n--- Test 4: Refresh stale unit to available ---")
    try:
        test_unit_id = str(uuid.uuid4())
        test_unit = {
            'id': test_unit_id,
            'building_id': 'test-building-lifecycle',
            'unit_number': 'LIFECYCLE-4',
            'rent': 2500,
            'bedrooms': 1,
            'bathrooms': 1,
            'is_available': True,
            'lifecycle_status': 'stale',
            'stale_since': datetime.now(timezone.utc).isoformat(),
            'updated_at': (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(test_unit)
        
        # Refresh (mark as available)
        result = await service.mark_unit_as_available(
            unit_id=test_unit_id,
            rent=2600,  # New price
            notes='Verified still available',
            changed_by='test-admin'
        )
        
        assert result['success'] == True
        assert result['new_status'] == 'available'
        assert result['price_changed'] == True
        
        # Verify in database
        updated_unit = await db.units.find_one({'id': test_unit_id})
        assert updated_unit['lifecycle_status'] == 'available'
        assert updated_unit['is_available'] == True
        assert updated_unit['rent'] == 2600
        assert updated_unit.get('stale_since') is None
        
        # Cleanup
        await db.units.delete_one({'id': test_unit_id})
        await db.status_changes.delete_many({'unit_id': test_unit_id})
        await db.price_changes.delete_many({'unit_id': test_unit_id})
        
        print("✅ PASSED: Stale unit correctly refreshed to available")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # ============ Test 5: Get lifecycle stats ============
    print("\n--- Test 5: Lifecycle statistics ---")
    try:
        stats = await service.get_lifecycle_stats()
        
        assert 'lifecycle_counts' in stats
        assert 'available' in stats['lifecycle_counts']
        assert 'stale' in stats['lifecycle_counts']
        assert 'rented' in stats['lifecycle_counts']
        assert 'stale_threshold_days' in stats
        assert stats['stale_threshold_days'] == STALE_THRESHOLD_DAYS
        
        print(f"✅ PASSED: Lifecycle stats: {stats['lifecycle_counts']}")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # ============ Test 6: Get full unit history ============
    print("\n--- Test 6: Full unit history ---")
    try:
        test_unit_id = str(uuid.uuid4())
        test_unit = {
            'id': test_unit_id,
            'building_id': 'test-building-lifecycle',
            'unit_number': 'LIFECYCLE-6',
            'rent': 3000,
            'bedrooms': 2,
            'bathrooms': 1,
            'is_available': True,
            'lifecycle_status': 'available',
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(test_unit)
        
        # Make some changes
        await service.update_unit_price(test_unit_id, 3100, 'test', 'admin')
        await service.mark_unit_as_rented(test_unit_id, notes='Test rental', changed_by='admin')
        
        # Get full history
        history = await service.get_unit_full_history(test_unit_id)
        
        assert history['unit_id'] == test_unit_id
        assert len(history['price_changes']) >= 1
        assert len(history['status_changes']) >= 1
        
        # Cleanup
        await db.units.delete_one({'id': test_unit_id})
        await db.price_changes.delete_many({'unit_id': test_unit_id})
        await db.status_changes.delete_many({'unit_id': test_unit_id})
        
        print(f"✅ PASSED: Full history retrieved: {history['total_price_changes']} price, {history['total_status_changes']} status changes")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # ============ Test 7: Verify no auto-deletion ============
    print("\n--- Test 7: Verify no auto-deletion ---")
    try:
        # Create a very old unit
        test_unit_id = str(uuid.uuid4())
        very_old_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        
        test_unit = {
            'id': test_unit_id,
            'building_id': 'test-building-lifecycle',
            'unit_number': 'LIFECYCLE-7',
            'rent': 2000,
            'bedrooms': 1,
            'bathrooms': 1,
            'is_available': True,
            'lifecycle_status': 'available',
            'updated_at': very_old_date,
            'created_at': very_old_date
        }
        await db.units.insert_one(test_unit)
        
        # Run stale check
        await service.check_and_mark_stale_units()
        
        # Verify unit still exists (just marked as stale, NOT deleted)
        unit = await db.units.find_one({'id': test_unit_id})
        assert unit is not None, "Unit should NOT be deleted!"
        assert unit['lifecycle_status'] == 'stale'
        
        # Cleanup
        await db.units.delete_one({'id': test_unit_id})
        await db.status_changes.delete_many({'unit_id': test_unit_id})
        
        print("✅ PASSED: Old unit marked as stale but NOT auto-deleted")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    client.close()
    return passed, failed


if __name__ == '__main__':
    passed, failed = asyncio.run(run_lifecycle_tests())
    exit(0 if failed == 0 else 1)
