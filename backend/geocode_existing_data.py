"""
Script to geocode all existing buildings and units in the database.
Run this once to populate lat/lng for existing data.
"""

import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from geocoding_service import geocode_building, batch_geocode_buildings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'test_database')


async def geocode_all_buildings():
    """Geocode all buildings in the database"""
    
    logger.info("Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Get all buildings without coordinates
        buildings = await db.buildings.find(
            {
                "$or": [
                    {"latitude": None},
                    {"longitude": None},
                    {"latitude": {"$exists": False}},
                    {"longitude": {"$exists": False}}
                ]
            },
            {"_id": 0}
        ).to_list(1000)
        
        logger.info(f"Found {len(buildings)} buildings without coordinates")
        
        if not buildings:
            logger.info("✅ All buildings already have coordinates!")
            return
        
        # Geocode buildings
        coords_map = await batch_geocode_buildings(buildings, batch_size=10)
        
        # Update database
        updated_count = 0
        for building_id, (lat, lng) in coords_map.items():
            result = await db.buildings.update_one(
                {"id": building_id},
                {"$set": {
                    "latitude": lat,
                    "longitude": lng
                }}
            )
            if result.modified_count > 0:
                updated_count += 1
        
        logger.info(f"✅ Updated {updated_count} buildings with coordinates")
        
        # Now update units with building coordinates
        logger.info("Updating units with building coordinates...")
        units_updated = 0
        
        # Get all buildings with coordinates
        buildings_with_coords = await db.buildings.find(
            {
                "latitude": {"$exists": True, "$ne": None},
                "longitude": {"$exists": True, "$ne": None}
            },
            {"_id": 0, "id": 1, "latitude": 1, "longitude": 1}
        ).to_list(1000)
        
        # Update units for each building
        for building in buildings_with_coords:
            result = await db.units.update_many(
                {"building_id": building["id"]},
                {"$set": {
                    "latitude": building["latitude"],
                    "longitude": building["longitude"]
                }}
            )
            units_updated += result.modified_count
        
        logger.info(f"✅ Updated {units_updated} units with coordinates")
        
        # Print summary
        print("\n" + "="*60)
        print("GEOCODING SUMMARY")
        print("="*60)
        print(f"Buildings geocoded: {len(coords_map)}")
        print(f"Buildings updated in DB: {updated_count}")
        print(f"Units updated in DB: {units_updated}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error during geocoding: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    print("Starting geocoding process...")
    print("This may take several minutes depending on the number of buildings.")
    print("Please wait...\n")
    
    asyncio.run(geocode_all_buildings())
    
    print("\n✅ Geocoding complete!")
