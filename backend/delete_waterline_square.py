"""Delete Waterline Square listings from database"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def main():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🗑️  Deleting Waterline Square listings...\n")
    
    # Find Waterline Square building
    building = await db.buildings.find_one({'name': 'Waterline Square'}, {'_id': 0})
    
    if not building:
        print("❌ Waterline Square building not found in database")
        return
    
    building_id = building['id']
    print(f"✅ Found Waterline Square building (ID: {building_id})")
    
    # Count units before deletion
    unit_count = await db.units.count_documents({'building_id': building_id})
    print(f"📊 Units to delete: {unit_count}")
    
    # Delete all units for this building
    result = await db.units.delete_many({'building_id': building_id})
    print(f"✅ Deleted {result.deleted_count} units")
    
    # Delete the building itself
    building_result = await db.buildings.delete_one({'id': building_id})
    print(f"✅ Deleted Waterline Square building")
    
    # Show updated counts
    print("\n📊 Updated Database Status:")
    total_buildings = await db.buildings.count_documents({})
    total_units = await db.units.count_documents({})
    units_with_real_images = await db.units.count_documents({
        'images.0': {'$exists': True, '$regex': '^((?!unsplash).)*$'}
    })
    
    print(f"   Total Buildings: {total_buildings}")
    print(f"   Total Units: {total_units}")
    print(f"   Units with Real Images: {units_with_real_images} ({units_with_real_images/total_units*100:.1f}%)")
    
    print("\n✅ Waterline Square successfully removed from database")

if __name__ == "__main__":
    asyncio.run(main())
