"""
Database Seeding Script for NoFeesApts.com
==========================================
This script seeds the production database with all buildings and units data.
It's designed to be idempotent - running it multiple times won't create duplicates.

Usage:
  python seed_database.py                    # Seed the database
  python seed_database.py --check            # Check current counts without seeding
  python seed_database.py --force            # Force re-seed (drops existing data)

Can also be triggered via API endpoint: POST /api/admin/seed-database
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
SEED_DATA_DIR = SCRIPT_DIR / "seed_data"

async def get_database():
    """Connect to MongoDB"""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

async def load_seed_data():
    """Load buildings and units from JSON files"""
    buildings_file = SEED_DATA_DIR / "buildings.json"
    units_file = SEED_DATA_DIR / "units.json"
    
    if not buildings_file.exists() or not units_file.exists():
        raise FileNotFoundError(f"Seed data files not found in {SEED_DATA_DIR}")
    
    with open(buildings_file, 'r') as f:
        buildings = json.load(f)
    
    with open(units_file, 'r') as f:
        units = json.load(f)
    
    return buildings, units

async def check_database_status(db):
    """Check current database counts"""
    buildings_count = await db.buildings.count_documents({})
    units_count = await db.units.count_documents({})
    return buildings_count, units_count

async def seed_database(force: bool = False):
    """
    Seed the database with buildings and units data.
    
    Args:
        force: If True, drops existing data before seeding.
               If False, only seeds if database is empty or has fewer records.
    
    Returns:
        dict with seeding results
    """
    db = await get_database()
    buildings_data, units_data = await load_seed_data()
    
    current_buildings, current_units = await check_database_status(db)
    
    result = {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "before": {
            "buildings": current_buildings,
            "units": current_units
        },
        "seed_data": {
            "buildings": len(buildings_data),
            "units": len(units_data)
        },
        "action": None,
        "after": None
    }
    
    # Determine if we should seed
    should_seed = force or current_buildings < len(buildings_data) or current_units < len(units_data)
    
    if not should_seed:
        result["action"] = "skipped"
        result["message"] = "Database already has sufficient data. Use --force to re-seed."
        result["after"] = result["before"]
        return result
    
    if force:
        result["action"] = "force_reseed"
        # Drop existing collections
        await db.buildings.drop()
        await db.units.drop()
    else:
        result["action"] = "seed"
    
    # Insert buildings (using upsert to avoid duplicates)
    buildings_inserted = 0
    for building in buildings_data:
        # Use the building's 'id' field as the unique identifier
        building_id = building.get('id')
        if building_id:
            update_result = await db.buildings.update_one(
                {"id": building_id},
                {"$set": building},
                upsert=True
            )
            if update_result.upserted_id or update_result.modified_count > 0:
                buildings_inserted += 1
    
    # Insert units (using upsert to avoid duplicates)
    units_inserted = 0
    for unit in units_data:
        # Use the unit's 'id' field as the unique identifier
        unit_id = unit.get('id')
        if unit_id:
            update_result = await db.units.update_one(
                {"id": unit_id},
                {"$set": unit},
                upsert=True
            )
            if update_result.upserted_id or update_result.modified_count > 0:
                units_inserted += 1
    
    # Create indexes for better query performance
    await db.buildings.create_index("id", unique=True)
    await db.buildings.create_index("neighborhood")
    await db.units.create_index("id", unique=True)
    await db.units.create_index("building_id")
    await db.units.create_index("rent")
    await db.units.create_index("bedrooms")
    await db.units.create_index([("neighborhood", 1), ("rent", 1)])
    
    # Get final counts
    final_buildings, final_units = await check_database_status(db)
    
    result["after"] = {
        "buildings": final_buildings,
        "units": final_units
    }
    result["inserted"] = {
        "buildings": buildings_inserted,
        "units": units_inserted
    }
    result["message"] = f"Successfully seeded {final_buildings} buildings and {final_units} units"
    
    return result

async def main():
    import sys
    
    force = "--force" in sys.argv
    check_only = "--check" in sys.argv
    
    db = await get_database()
    current_buildings, current_units = await check_database_status(db)
    
    print(f"\n{'='*50}")
    print("NoFeesApts.com Database Seeding Tool")
    print(f"{'='*50}")
    print(f"\nCurrent database status:")
    print(f"  Buildings: {current_buildings}")
    print(f"  Units: {current_units}")
    
    if check_only:
        buildings_data, units_data = await load_seed_data()
        print(f"\nSeed data available:")
        print(f"  Buildings: {len(buildings_data)}")
        print(f"  Units: {len(units_data)}")
        return
    
    print(f"\nSeeding database (force={force})...")
    result = await seed_database(force=force)
    
    print(f"\nResult: {result['action']}")
    print(f"  Before: {result['before']['buildings']} buildings, {result['before']['units']} units")
    print(f"  After:  {result['after']['buildings']} buildings, {result['after']['units']} units")
    print(f"\n{result['message']}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    asyncio.run(main())
