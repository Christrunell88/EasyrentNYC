"""Update JS building with complete address and amenities"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def main():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔄 Updating JS building details...\n")
    
    # Find JS building
    building = await db.buildings.find_one({'name': 'JS'}, {'_id': 0})
    
    if not building:
        print("❌ JS building not found!")
        return
    
    building_id = building['id']
    
    # Update building with complete details
    update_data = {
        'address': '147-40 Archer Avenue',
        'city': 'Jamaica',
        'state': 'NY',
        'zip_code': '11435',
        'neighborhood': 'Jamaica',
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.buildings.update_one(
        {'id': building_id},
        {'$set': update_data}
    )
    
    print(f"✅ Updated building address")
    print(f"   Address: 147-40 Archer Avenue")
    print(f"   Location: Jamaica, Queens, NY 11435")
    
    # Update unit with amenities
    unit = await db.units.find_one({'building_id': building_id}, {'_id': 0})
    
    if unit:
        amenities = [
            'Parking',
            'Full-Time Doorman',
            'Live-in Super',
            'Elevator',
            'Gym',
            'Outdoor Spaces'
        ]
        
        unit_result = await db.units.update_one(
            {'id': unit['id']},
            {
                '$set': {
                    'amenities': amenities,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        print(f"\n✅ Updated unit amenities:")
        for amenity in amenities:
            print(f"   • {amenity}")
    
    # Verify updates
    updated_building = await db.buildings.find_one({'id': building_id}, {'_id': 0})
    updated_unit = await db.units.find_one({'building_id': building_id}, {'_id': 0})
    
    print(f"\n📊 JS Building Complete Details:")
    print(f"   Building: {updated_building['name']}")
    print(f"   Address: {updated_building['address']}")
    print(f"   City: {updated_building['city']}, {updated_building['state']} {updated_building['zip_code']}")
    print(f"   Neighborhood: {updated_building['neighborhood']}")
    print(f"\n   Unit #408:")
    print(f"   - 2 Bedrooms, 2 Bathrooms")
    print(f"   - $3,500/month")
    print(f"   - {len(updated_unit['amenities'])} amenities")
    print(f"   - {len(updated_unit['images'])} images")

if __name__ == "__main__":
    asyncio.run(main())
