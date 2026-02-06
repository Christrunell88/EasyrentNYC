"""
Test Suite for Database Access Control Layer
=============================================
Verifies that:
1. Crawler role is BLOCKED from writing to production collections (units, buildings)
2. Admin role CAN write to production collections
3. Crawler CAN write to staging collections
4. E2E flow works: crawl -> stage -> approve -> promote
"""

import pytest
import asyncio
import sys
import os
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# Import modules under test
from db_access_control import (
    DatabaseAccessControl,
    WriteSource,
    UnauthorizedWriteError,
    get_access_control,
    init_access_control
)


# Setup MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']


class TestDatabaseAccessControl:
    """Test suite for Database Access Control"""
    
    @pytest.fixture
    async def db(self):
        """Get database connection"""
        client = AsyncIOMotorClient(mongo_url)
        database = client[db_name]
        yield database
        client.close()
    
    @pytest.fixture
    async def access_control(self, db):
        """Get access control instance"""
        return init_access_control(db)
    
    # ============ TEST 1: Crawler BLOCKED from production writes ============
    
    @pytest.mark.asyncio
    async def test_crawler_blocked_from_production_units(self, db, access_control):
        """
        Test that crawler role is BLOCKED from writing to production 'units' collection.
        Expected: UnauthorizedWriteError raised
        """
        test_document = {
            'id': str(uuid.uuid4()),
            'building_id': 'test-building',
            'unit_number': 'TEST-1',
            'rent': 3000,
            'bedrooms': 2,
            'bathrooms': 1
        }
        
        with pytest.raises(UnauthorizedWriteError) as exc_info:
            await access_control.staging_write(
                collection='units',  # Production collection - should be blocked!
                operation='insert',
                document=test_document,
                crawler_source='test_crawler'
            )
        
        assert 'units' in str(exc_info.value)
        assert 'staging' in str(exc_info.value).lower()
        print("✅ TEST PASSED: Crawler blocked from writing to 'units' collection")
    
    @pytest.mark.asyncio
    async def test_crawler_blocked_from_production_buildings(self, db, access_control):
        """
        Test that crawler role is BLOCKED from writing to production 'buildings' collection.
        Expected: UnauthorizedWriteError raised
        """
        test_document = {
            'id': str(uuid.uuid4()),
            'name': 'Test Building',
            'address': '123 Test St',
            'neighborhood': 'Test',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'source_url': 'https://test.com'
        }
        
        with pytest.raises(UnauthorizedWriteError) as exc_info:
            await access_control.staging_write(
                collection='buildings',  # Production collection - should be blocked!
                operation='insert',
                document=test_document,
                crawler_source='test_crawler'
            )
        
        assert 'buildings' in str(exc_info.value)
        assert 'staging' in str(exc_info.value).lower()
        print("✅ TEST PASSED: Crawler blocked from writing to 'buildings' collection")
    
    # ============ TEST 2: Crawler CAN write to staging collections ============
    
    @pytest.mark.asyncio
    async def test_crawler_can_write_to_units_staging(self, db, access_control):
        """
        Test that crawler CAN write to 'units_staging' collection.
        Expected: Success
        """
        test_id = str(uuid.uuid4())
        test_document = {
            'id': test_id,
            'building_id': 'test-building',
            'unit_number': 'TEST-STAGING-1',
            'rent': 2500,
            'bedrooms': 1,
            'bathrooms': 1,
            'review_status': 'pending'
        }
        
        result = await access_control.staging_write(
            collection='units_staging',  # Staging collection - should be allowed
            operation='insert',
            document=test_document,
            crawler_source='test_crawler'
        )
        
        assert result is not None
        assert result.get('inserted_id') == test_id
        
        # Verify it was actually inserted
        inserted = await db.units_staging.find_one({'id': test_id})
        assert inserted is not None
        
        # Cleanup
        await db.units_staging.delete_one({'id': test_id})
        print("✅ TEST PASSED: Crawler can write to 'units_staging' collection")
    
    @pytest.mark.asyncio
    async def test_crawler_can_write_to_buildings_staging(self, db, access_control):
        """
        Test that crawler CAN write to 'buildings_staging' collection.
        Expected: Success
        """
        test_id = str(uuid.uuid4())
        test_document = {
            'id': test_id,
            'name': 'Test Staging Building',
            'address': '456 Staging Ave',
            'neighborhood': 'Test',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10002',
            'source_url': 'https://staging-test.com',
            'review_status': 'pending'
        }
        
        result = await access_control.staging_write(
            collection='buildings_staging',  # Staging collection - should be allowed
            operation='insert',
            document=test_document,
            crawler_source='test_crawler'
        )
        
        assert result is not None
        assert result.get('inserted_id') == test_id
        
        # Verify it was actually inserted
        inserted = await db.buildings_staging.find_one({'id': test_id})
        assert inserted is not None
        
        # Cleanup
        await db.buildings_staging.delete_one({'id': test_id})
        print("✅ TEST PASSED: Crawler can write to 'buildings_staging' collection")
    
    # ============ TEST 3: Admin CAN write to production ============
    
    @pytest.mark.asyncio
    async def test_admin_can_write_to_production_units(self, db, access_control):
        """
        Test that admin role (via authorized_production_write) CAN write to 'units' collection.
        Expected: Success
        """
        test_id = str(uuid.uuid4())
        test_document = {
            'id': test_id,
            'building_id': 'test-building-admin',
            'unit_number': 'ADMIN-TEST-1',
            'rent': 3500,
            'bedrooms': 2,
            'bathrooms': 1.5,
            'is_available': True
        }
        
        result = await access_control.authorized_production_write(
            collection='units',
            operation='insert',
            source=WriteSource.ADMIN_APPROVAL,
            user_id='test-admin-user',
            document=test_document
        )
        
        assert result is not None
        assert result.get('inserted_id') == test_id
        
        # Verify it was actually inserted
        inserted = await db.units.find_one({'id': test_id})
        assert inserted is not None
        assert inserted['unit_number'] == 'ADMIN-TEST-1'
        
        # Cleanup
        await db.units.delete_one({'id': test_id})
        print("✅ TEST PASSED: Admin can write to 'units' collection")
    
    @pytest.mark.asyncio
    async def test_admin_can_write_to_production_buildings(self, db, access_control):
        """
        Test that admin role (via authorized_production_write) CAN write to 'buildings' collection.
        Expected: Success
        """
        test_id = str(uuid.uuid4())
        test_document = {
            'id': test_id,
            'name': 'Admin Test Building',
            'address': '789 Admin Blvd',
            'neighborhood': 'Admin Test',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10003',
            'source_url': 'https://admin-test.com'
        }
        
        result = await access_control.authorized_production_write(
            collection='buildings',
            operation='insert',
            source=WriteSource.ADMIN_APPROVAL,
            user_id='test-admin-user',
            document=test_document
        )
        
        assert result is not None
        assert result.get('inserted_id') == test_id
        
        # Verify it was actually inserted
        inserted = await db.buildings.find_one({'id': test_id})
        assert inserted is not None
        assert inserted['name'] == 'Admin Test Building'
        
        # Cleanup
        await db.buildings.delete_one({'id': test_id})
        print("✅ TEST PASSED: Admin can write to 'buildings' collection")
    
    # ============ TEST 4: Admin requires user_id ============
    
    @pytest.mark.asyncio
    async def test_admin_approval_requires_user_id(self, db, access_control):
        """
        Test that admin approval write requires a user_id.
        Expected: UnauthorizedWriteError raised
        """
        test_document = {
            'id': str(uuid.uuid4()),
            'building_id': 'test',
            'unit_number': 'TEST',
            'rent': 1000
        }
        
        with pytest.raises(UnauthorizedWriteError) as exc_info:
            await access_control.authorized_production_write(
                collection='units',
                operation='insert',
                source=WriteSource.ADMIN_APPROVAL,
                user_id='',  # Empty user_id - should fail
                document=test_document
            )
        
        assert 'user_id' in str(exc_info.value).lower()
        print("✅ TEST PASSED: Admin approval requires valid user_id")
    
    # ============ TEST 5: Collection type checks ============
    
    @pytest.mark.asyncio
    async def test_is_production_collection(self, db, access_control):
        """
        Test that is_production_collection correctly identifies production collections.
        """
        assert access_control.is_production_collection('units') == True
        assert access_control.is_production_collection('buildings') == True
        assert access_control.is_production_collection('units_staging') == False
        assert access_control.is_production_collection('buildings_staging') == False
        assert access_control.is_production_collection('users') == False
        print("✅ TEST PASSED: Production collection identification works")
    
    @pytest.mark.asyncio
    async def test_is_staging_collection(self, db, access_control):
        """
        Test that is_staging_collection correctly identifies staging collections.
        """
        assert access_control.is_staging_collection('units_staging') == True
        assert access_control.is_staging_collection('buildings_staging') == True
        assert access_control.is_staging_collection('units') == False
        assert access_control.is_staging_collection('buildings') == False
        print("✅ TEST PASSED: Staging collection identification works")


class TestCrawlerProductionWriteBlocker:
    """Test suite for Crawler Production Write Blocker in crawler.py"""
    
    @pytest.mark.asyncio
    async def test_crawler_blocker_direct_import(self):
        """
        Test the CrawlerProductionWriteBlocker directly from crawler.py
        """
        from crawler import CrawlerProductionWriteBlocker
        
        # Should raise for production collections
        with pytest.raises((UnauthorizedWriteError, PermissionError)):
            CrawlerProductionWriteBlocker.check_collection('units', 'insert')
        
        with pytest.raises((UnauthorizedWriteError, PermissionError)):
            CrawlerProductionWriteBlocker.check_collection('buildings', 'insert')
        
        # Should NOT raise for staging collections
        CrawlerProductionWriteBlocker.check_collection('units_staging', 'insert')
        CrawlerProductionWriteBlocker.check_collection('buildings_staging', 'insert')
        
        print("✅ TEST PASSED: CrawlerProductionWriteBlocker works correctly")
    
    @pytest.mark.asyncio
    async def test_blocked_production_functions(self):
        """
        Test that legacy production write functions are blocked.
        """
        from crawler import (
            insert_unit_to_production,
            insert_building_to_production,
            update_production_unit,
            update_production_building
        )
        
        # All these should raise PermissionError
        with pytest.raises(PermissionError):
            await insert_unit_to_production({'id': 'test'})
        
        with pytest.raises(PermissionError):
            await insert_building_to_production({'id': 'test'})
        
        with pytest.raises(PermissionError):
            await update_production_unit({'id': 'test'})
        
        with pytest.raises(PermissionError):
            await update_production_building({'id': 'test'})
        
        print("✅ TEST PASSED: Legacy production write functions are blocked")


class TestPromotionServiceAuthorization:
    """Test suite for Promotion Service Authorization"""
    
    @pytest.fixture
    async def db(self):
        """Get database connection"""
        client = AsyncIOMotorClient(mongo_url)
        database = client[db_name]
        yield database
        client.close()
    
    @pytest.mark.asyncio
    async def test_promotion_service_uses_admin_authorization(self, db):
        """
        Test that promotion service correctly uses ADMIN_APPROVAL source.
        """
        from promotion_service import PromotionService, get_promotion_service
        
        # Initialize promotion service
        service = get_promotion_service(db)
        
        # Verify it has access control
        assert service._access_control is not None
        
        print("✅ TEST PASSED: Promotion service has access control initialized")
    
    @pytest.mark.asyncio
    async def test_promotion_service_e2e_flow(self, db):
        """
        Test E2E flow: create staging unit -> promote to production
        """
        from promotion_service import PromotionService, get_promotion_service
        from datetime import datetime, timezone
        
        service = get_promotion_service(db)
        
        # Create a test building in production (required for unit)
        test_building_id = str(uuid.uuid4())
        test_building = {
            'id': test_building_id,
            'name': 'E2E Test Building',
            'address': '123 E2E Test St',
            'neighborhood': 'E2E Test',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'source_url': 'https://e2e-test.com',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.buildings.insert_one(test_building)
        
        # Create a staging unit
        staging_unit_id = str(uuid.uuid4())
        staging_unit = {
            'id': staging_unit_id,
            'building_id': test_building_id,
            'unit_number': 'E2E-1',
            'rent': 2800,
            'bedrooms': 2,
            'bathrooms': 1,
            'is_available': True,
            'review_status': 'pending',
            'crawler_source': 'e2e-test',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units_staging.insert_one(staging_unit)
        
        # Promote the unit
        result = await service.promote_unit(
            staged_unit=staging_unit,
            approved_by='test-admin-e2e'
        )
        
        # Verify promotion result
        assert result is not None
        assert result['action'] == 'created'
        assert result['production_id'] is not None
        
        # Verify unit exists in production
        production_unit = await db.units.find_one({'id': result['production_id']})
        assert production_unit is not None
        assert production_unit['unit_number'] == 'E2E-1'
        assert production_unit['rent'] == 2800
        assert production_unit['is_verified'] == True
        
        # Cleanup
        await db.units.delete_one({'id': result['production_id']})
        await db.units_staging.delete_one({'id': staging_unit_id})
        await db.buildings.delete_one({'id': test_building_id})
        # Clean up price_changes and status_changes
        await db.price_changes.delete_many({'unit_id': result['production_id']})
        await db.status_changes.delete_many({'unit_id': result['production_id']})
        
        print("✅ TEST PASSED: E2E promotion flow works correctly")


# ============ Run tests directly ============

async def run_all_tests():
    """Run all tests manually (without pytest)"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    print("\n" + "="*60)
    print("DATABASE ACCESS CONTROL TEST SUITE")
    print("="*60 + "\n")
    
    # Connect to database
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Initialize access control
    access_control = init_access_control(db)
    
    passed = 0
    failed = 0
    
    # Test 1: Crawler blocked from production units
    print("\n--- Test 1: Crawler blocked from production units ---")
    try:
        test_doc = {'id': str(uuid.uuid4()), 'unit_number': 'TEST'}
        await access_control.staging_write(
            collection='units',
            operation='insert',
            document=test_doc,
            crawler_source='test'
        )
        print("❌ FAILED: Should have raised UnauthorizedWriteError")
        failed += 1
    except (UnauthorizedWriteError, PermissionError) as e:
        print(f"✅ PASSED: Correctly blocked with error: {str(e)[:80]}...")
        passed += 1
    
    # Test 2: Crawler blocked from production buildings
    print("\n--- Test 2: Crawler blocked from production buildings ---")
    try:
        test_doc = {'id': str(uuid.uuid4()), 'name': 'TEST'}
        await access_control.staging_write(
            collection='buildings',
            operation='insert',
            document=test_doc,
            crawler_source='test'
        )
        print("❌ FAILED: Should have raised UnauthorizedWriteError")
        failed += 1
    except (UnauthorizedWriteError, PermissionError) as e:
        print(f"✅ PASSED: Correctly blocked with error: {str(e)[:80]}...")
        passed += 1
    
    # Test 3: Crawler CAN write to units_staging
    print("\n--- Test 3: Crawler can write to units_staging ---")
    try:
        test_id = str(uuid.uuid4())
        test_doc = {'id': test_id, 'unit_number': 'STAGING-TEST', 'review_status': 'pending'}
        result = await access_control.staging_write(
            collection='units_staging',
            operation='insert',
            document=test_doc,
            crawler_source='test'
        )
        assert result.get('inserted_id') == test_id
        # Cleanup
        await db.units_staging.delete_one({'id': test_id})
        print("✅ PASSED: Successfully wrote to units_staging")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # Test 4: Crawler CAN write to buildings_staging
    print("\n--- Test 4: Crawler can write to buildings_staging ---")
    try:
        test_id = str(uuid.uuid4())
        test_doc = {'id': test_id, 'name': 'STAGING-TEST', 'review_status': 'pending'}
        result = await access_control.staging_write(
            collection='buildings_staging',
            operation='insert',
            document=test_doc,
            crawler_source='test'
        )
        assert result.get('inserted_id') == test_id
        # Cleanup
        await db.buildings_staging.delete_one({'id': test_id})
        print("✅ PASSED: Successfully wrote to buildings_staging")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # Test 5: Admin CAN write to production units
    print("\n--- Test 5: Admin can write to production units ---")
    try:
        test_id = str(uuid.uuid4())
        test_doc = {'id': test_id, 'unit_number': 'ADMIN-TEST', 'rent': 3000}
        result = await access_control.authorized_production_write(
            collection='units',
            operation='insert',
            source=WriteSource.ADMIN_APPROVAL,
            user_id='test-admin',
            document=test_doc
        )
        assert result.get('inserted_id') == test_id
        # Verify
        inserted = await db.units.find_one({'id': test_id})
        assert inserted is not None
        # Cleanup
        await db.units.delete_one({'id': test_id})
        print("✅ PASSED: Admin successfully wrote to production units")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # Test 6: Admin CAN write to production buildings
    print("\n--- Test 6: Admin can write to production buildings ---")
    try:
        test_id = str(uuid.uuid4())
        test_doc = {'id': test_id, 'name': 'ADMIN-TEST', 'address': '123 Admin St'}
        result = await access_control.authorized_production_write(
            collection='buildings',
            operation='insert',
            source=WriteSource.ADMIN_APPROVAL,
            user_id='test-admin',
            document=test_doc
        )
        assert result.get('inserted_id') == test_id
        # Verify
        inserted = await db.buildings.find_one({'id': test_id})
        assert inserted is not None
        # Cleanup
        await db.buildings.delete_one({'id': test_id})
        print("✅ PASSED: Admin successfully wrote to production buildings")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # Test 7: Admin requires user_id
    print("\n--- Test 7: Admin approval requires user_id ---")
    try:
        test_doc = {'id': str(uuid.uuid4()), 'unit_number': 'TEST'}
        await access_control.authorized_production_write(
            collection='units',
            operation='insert',
            source=WriteSource.ADMIN_APPROVAL,
            user_id='',  # Empty user_id
            document=test_doc
        )
        print("❌ FAILED: Should have raised UnauthorizedWriteError")
        failed += 1
    except UnauthorizedWriteError as e:
        print(f"✅ PASSED: Correctly required user_id: {str(e)[:60]}...")
        passed += 1
    
    # Test 8: CrawlerProductionWriteBlocker
    print("\n--- Test 8: CrawlerProductionWriteBlocker direct test ---")
    try:
        from crawler import CrawlerProductionWriteBlocker
        
        # Should raise for production
        try:
            CrawlerProductionWriteBlocker.check_collection('units', 'insert')
            print("❌ FAILED: Should have raised for 'units'")
            failed += 1
        except (UnauthorizedWriteError, PermissionError):
            # Should NOT raise for staging
            CrawlerProductionWriteBlocker.check_collection('units_staging', 'insert')
            CrawlerProductionWriteBlocker.check_collection('buildings_staging', 'insert')
            print("✅ PASSED: CrawlerProductionWriteBlocker works correctly")
            passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        failed += 1
    
    # Test 9: E2E Promotion Flow
    print("\n--- Test 9: E2E Promotion Flow ---")
    try:
        from promotion_service import get_promotion_service
        from datetime import datetime, timezone
        
        service = get_promotion_service(db)
        
        # Create test building
        test_building_id = str(uuid.uuid4())
        await db.buildings.insert_one({
            'id': test_building_id,
            'name': 'E2E Test',
            'address': '123 E2E St',
            'neighborhood': 'Test',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'source_url': 'https://test.com',
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Create staging unit
        staging_unit = {
            'id': str(uuid.uuid4()),
            'building_id': test_building_id,
            'unit_number': 'E2E-1',
            'rent': 2500,
            'bedrooms': 1,
            'bathrooms': 1,
            'is_available': True,
            'review_status': 'pending',
            'crawler_source': 'e2e-test',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units_staging.insert_one(staging_unit)
        
        # Promote
        result = await service.promote_unit(staging_unit, 'test-admin-e2e')
        
        assert result['action'] == 'created'
        assert result['production_id'] is not None
        
        # Verify in production
        prod_unit = await db.units.find_one({'id': result['production_id']})
        assert prod_unit is not None
        assert prod_unit['unit_number'] == 'E2E-1'
        
        # Cleanup
        await db.units.delete_one({'id': result['production_id']})
        await db.units_staging.delete_one({'id': staging_unit['id']})
        await db.buildings.delete_one({'id': test_building_id})
        await db.price_changes.delete_many({'unit_id': result['production_id']})
        await db.status_changes.delete_many({'unit_id': result['production_id']})
        
        print("✅ PASSED: E2E promotion flow works correctly")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    client.close()
    
    return passed, failed


if __name__ == '__main__':
    # Run tests
    passed, failed = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)
