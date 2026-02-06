"""
MongoDB Index Management for NoFeesApts.com
============================================
Creates and manages indexes for optimal query performance.

Run this script to ensure all indexes are created:
    python create_indexes.py

Indexes are also created automatically on server startup.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Index definitions
INDEXES = {
    # ============ UNITS (Production) ============
    'units': [
        {
            'keys': [('building_id', 1), ('unit_number', 1)],
            'name': 'idx_units_building_unit',
            'unique': True,
            'comment': 'Unique constraint on building + unit number'
        },
        {
            'keys': [('lifecycle_status', 1)],
            'name': 'idx_units_lifecycle_status',
            'comment': 'Filter by lifecycle status (available, stale, rented)'
        },
        {
            'keys': [('rent', 1)],
            'name': 'idx_units_rent',
            'comment': 'Price range queries'
        },
        {
            'keys': [('rent', -1)],
            'name': 'idx_units_rent_desc',
            'comment': 'Sort by price descending'
        },
        {
            'keys': [('is_available', 1)],
            'name': 'idx_units_available',
            'comment': 'Filter available units'
        },
        {
            'keys': [('bedrooms', 1)],
            'name': 'idx_units_bedrooms',
            'comment': 'Filter by bedroom count'
        },
        {
            'keys': [('original_staging_id', 1)],
            'name': 'idx_units_staging_id',
            'sparse': True,
            'comment': 'Link back to staging source'
        },
        {
            'keys': [('crawler_source', 1)],
            'name': 'idx_units_crawler_source',
            'sparse': True,
            'comment': 'Filter by crawler source'
        },
        {
            'keys': [('updated_at', -1)],
            'name': 'idx_units_updated_at',
            'comment': 'Sort by recently updated'
        },
        {
            'keys': [('is_featured', 1), ('is_available', 1)],
            'name': 'idx_units_featured_available',
            'comment': 'Featured listings query optimization'
        },
    ],
    
    # ============ UNITS STAGING ============
    'units_staging': [
        {
            'keys': [('review_status', 1)],
            'name': 'idx_staging_review_status',
            'comment': 'Filter by review status (pending, approved, rejected)'
        },
        {
            'keys': [('duplicate_score', -1)],
            'name': 'idx_staging_duplicate_score_desc',
            'comment': 'Sort by duplicate likelihood (high first)'
        },
        {
            'keys': [('normalized_unit_number', 1)],
            'name': 'idx_staging_normalized_unit',
            'comment': 'Duplicate detection by normalized unit number'
        },
        {
            'keys': [('building_id', 1), ('normalized_unit_number', 1)],
            'name': 'idx_staging_building_unit',
            'comment': 'Compound index for duplicate check'
        },
        {
            'keys': [('crawler_batch_id', 1)],
            'name': 'idx_staging_batch',
            'comment': 'Filter by crawl batch'
        },
        {
            'keys': [('review_status', 1), ('duplicate_score', -1)],
            'name': 'idx_staging_status_dup_score',
            'comment': 'Pending items sorted by duplicate likelihood'
        },
        {
            'keys': [('created_at', -1)],
            'name': 'idx_staging_created_at',
            'comment': 'Sort by newest first'
        },
    ],
    
    # ============ BUILDINGS (Production) ============
    'buildings': [
        {
            'keys': [('normalized_address', 1)],
            'name': 'idx_buildings_normalized_address',
            'sparse': True,
            'comment': 'Address-based duplicate detection'
        },
        {
            'keys': [('address', 1)],
            'name': 'idx_buildings_address',
            'comment': 'Address lookup'
        },
        {
            'keys': [('neighborhood', 1)],
            'name': 'idx_buildings_neighborhood',
            'comment': 'Filter by neighborhood'
        },
        {
            'keys': [('city', 1), ('state', 1)],
            'name': 'idx_buildings_city_state',
            'comment': 'Location-based filtering'
        },
        {
            'keys': [('location', '2dsphere')],
            'name': 'idx_buildings_location_geo',
            'sparse': True,
            'comment': 'Geospatial queries for map view'
        },
    ],
    
    # ============ BUILDINGS STAGING ============
    'buildings_staging': [
        {
            'keys': [('review_status', 1)],
            'name': 'idx_bldg_staging_review_status',
            'comment': 'Filter by review status'
        },
        {
            'keys': [('normalized_address', 1)],
            'name': 'idx_bldg_staging_normalized_addr',
            'sparse': True,
            'comment': 'Duplicate detection by address'
        },
        {
            'keys': [('duplicate_score', -1)],
            'name': 'idx_bldg_staging_dup_score',
            'comment': 'Sort by duplicate likelihood'
        },
        {
            'keys': [('address_hash', 1)],
            'name': 'idx_bldg_staging_addr_hash',
            'sparse': True,
            'comment': 'Fast hash-based duplicate lookup'
        },
    ],
    
    # ============ PRICE CHANGES (History) ============
    'price_changes': [
        {
            'keys': [('unit_id', 1), ('changed_at', -1)],
            'name': 'idx_price_changes_unit_date',
            'comment': 'Unit price history lookup'
        },
        {
            'keys': [('changed_at', -1)],
            'name': 'idx_price_changes_date',
            'comment': 'Recent price changes'
        },
    ],
    
    # ============ STATUS CHANGES (History) ============
    'status_changes': [
        {
            'keys': [('unit_id', 1), ('changed_at', -1)],
            'name': 'idx_status_changes_unit_date',
            'comment': 'Unit status history lookup'
        },
        {
            'keys': [('changed_at', -1)],
            'name': 'idx_status_changes_date',
            'comment': 'Recent status changes'
        },
        {
            'keys': [('new_status', 1)],
            'name': 'idx_status_changes_new_status',
            'comment': 'Filter by status type'
        },
    ],
    
    # ============ USER SESSIONS ============
    'user_sessions': [
        {
            'keys': [('session_token', 1)],
            'name': 'idx_sessions_token',
            'unique': True,
            'comment': 'Session lookup by token'
        },
        {
            'keys': [('user_id', 1)],
            'name': 'idx_sessions_user',
            'comment': 'User sessions lookup'
        },
        {
            'keys': [('expires_at', 1)],
            'name': 'idx_sessions_expires',
            'comment': 'Session expiration cleanup'
        },
    ],
    
    # ============ USERS ============
    'users': [
        {
            'keys': [('email', 1)],
            'name': 'idx_users_email',
            'unique': True,
            'comment': 'Email uniqueness and lookup'
        },
    ],
    
    # ============ FAVORITES ============
    'favorites': [
        {
            'keys': [('user_id', 1), ('unit_id', 1)],
            'name': 'idx_favorites_user_unit',
            'unique': True,
            'comment': 'Prevent duplicate favorites'
        },
        {
            'keys': [('user_id', 1)],
            'name': 'idx_favorites_user',
            'comment': 'User favorites lookup'
        },
    ],
    
    # ============ CONTACT REQUESTS ============
    'contact_requests': [
        {
            'keys': [('created_at', -1)],
            'name': 'idx_contacts_date',
            'comment': 'Recent contacts first'
        },
        {
            'keys': [('user_id', 1)],
            'name': 'idx_contacts_user',
            'comment': 'User contact history'
        },
        {
            'keys': [('unit_id', 1)],
            'name': 'idx_contacts_unit',
            'comment': 'Unit inquiry history'
        },
    ],
    
    # ============ WRITE AUDIT LOG ============
    'write_audit_log': [
        {
            'keys': [('timestamp', -1)],
            'name': 'idx_audit_timestamp',
            'comment': 'Recent audit entries'
        },
        {
            'keys': [('collection', 1), ('authorized', 1)],
            'name': 'idx_audit_collection_auth',
            'comment': 'Filter by collection and authorization status'
        },
        {
            'keys': [('user_id', 1)],
            'name': 'idx_audit_user',
            'sparse': True,
            'comment': 'User activity audit'
        },
    ],
}


async def create_indexes(db) -> dict:
    """
    Create all indexes defined in INDEXES.
    
    Returns:
        Summary of created indexes
    """
    results = {
        'created': [],
        'already_exists': [],
        'errors': []
    }
    
    for collection_name, indexes in INDEXES.items():
        logger.info(f"Creating indexes for collection: {collection_name}")
        collection = db[collection_name]
        
        for index_def in indexes:
            try:
                keys = index_def['keys']
                name = index_def['name']
                
                # Build index options
                options = {'name': name}
                if index_def.get('unique'):
                    options['unique'] = True
                if index_def.get('sparse'):
                    options['sparse'] = True
                if index_def.get('expireAfterSeconds'):
                    options['expireAfterSeconds'] = index_def['expireAfterSeconds']
                
                # Check if index already exists
                existing_indexes = await collection.index_information()
                if name in existing_indexes:
                    logger.debug(f"  Index {name} already exists")
                    results['already_exists'].append(f"{collection_name}.{name}")
                    continue
                
                # Create the index
                await collection.create_index(keys, **options)
                logger.info(f"  ✓ Created index: {name}")
                results['created'].append(f"{collection_name}.{name}")
                
            except Exception as e:
                error_msg = f"{collection_name}.{index_def.get('name', 'unknown')}: {str(e)}"
                logger.error(f"  ✗ Error creating index: {error_msg}")
                results['errors'].append(error_msg)
    
    return results


async def drop_all_indexes(db, except_id: bool = True) -> dict:
    """
    Drop all indexes (except _id if specified).
    Use with caution!
    
    Args:
        db: Database connection
        except_id: Keep the _id index (default True)
    
    Returns:
        Summary of dropped indexes
    """
    results = {'dropped': [], 'errors': []}
    
    for collection_name in INDEXES.keys():
        try:
            collection = db[collection_name]
            if except_id:
                # Get all index names except _id_
                existing = await collection.index_information()
                for index_name in existing:
                    if index_name != '_id_':
                        await collection.drop_index(index_name)
                        results['dropped'].append(f"{collection_name}.{index_name}")
                        logger.info(f"Dropped index: {collection_name}.{index_name}")
            else:
                await collection.drop_indexes()
                results['dropped'].append(f"{collection_name}.*")
                logger.info(f"Dropped all indexes: {collection_name}")
        except Exception as e:
            results['errors'].append(f"{collection_name}: {str(e)}")
    
    return results


async def get_index_stats(db) -> dict:
    """
    Get statistics about indexes across all collections.
    """
    stats = {}
    
    for collection_name in INDEXES.keys():
        try:
            collection = db[collection_name]
            indexes = await collection.index_information()
            stats[collection_name] = {
                'index_count': len(indexes),
                'indexes': list(indexes.keys())
            }
        except Exception as e:
            stats[collection_name] = {'error': str(e)}
    
    return stats


async def ensure_geospatial_field(db):
    """
    Ensure buildings have proper 'location' field for geospatial queries.
    Converts lat/lng to GeoJSON Point format if needed.
    """
    buildings = await db.buildings.find(
        {
            'latitude': {'$exists': True, '$ne': None},
            'longitude': {'$exists': True, '$ne': None},
            'location': {'$exists': False}
        },
        {"_id": 0, "id": 1, "latitude": 1, "longitude": 1}
    ).to_list(10000)
    
    updated = 0
    for building in buildings:
        try:
            location = {
                'type': 'Point',
                'coordinates': [building['longitude'], building['latitude']]  # GeoJSON is [lng, lat]
            }
            await db.buildings.update_one(
                {'id': building['id']},
                {'$set': {'location': location}}
            )
            updated += 1
        except Exception as e:
            logger.error(f"Error updating location for building {building['id']}: {e}")
    
    logger.info(f"Updated {updated} buildings with GeoJSON location field")
    return updated


async def main():
    """Run index creation"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("\n" + "="*60)
    print("MONGODB INDEX MANAGEMENT")
    print("="*60 + "\n")
    
    # Ensure geospatial fields are set up
    print("--- Preparing geospatial data ---")
    await ensure_geospatial_field(db)
    
    # Create indexes
    print("\n--- Creating indexes ---")
    results = await create_indexes(db)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Created: {len(results['created'])}")
    print(f"Already existed: {len(results['already_exists'])}")
    print(f"Errors: {len(results['errors'])}")
    
    if results['created']:
        print("\nNewly created indexes:")
        for idx in results['created']:
            print(f"  ✓ {idx}")
    
    if results['errors']:
        print("\nErrors:")
        for err in results['errors']:
            print(f"  ✗ {err}")
    
    # Get final stats
    print("\n--- Current index stats ---")
    stats = await get_index_stats(db)
    for collection, info in stats.items():
        if 'error' not in info:
            print(f"  {collection}: {info['index_count']} indexes")
    
    client.close()
    print("\n✓ Index management complete")


if __name__ == '__main__':
    asyncio.run(main())
