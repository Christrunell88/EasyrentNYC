"""Add JS building with unit #408 and user-uploaded images"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from uuid import uuid4

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def main():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🏢 Creating JS building...\n")
    
    # User-uploaded images
    images = [
        "https://customer-assets.emergentagent.com/job_zerofeeliving/artifacts/p70wzn8k_Living%20Kitchen%201.webp",
        "https://customer-assets.emergentagent.com/job_zerofeeliving/artifacts/xavjp3uq_Kitchen%201.webp",
        "https://customer-assets.emergentagent.com/job_zerofeeliving/artifacts/qzvkxeg1_bedroom%201.webp",
        "https://customer-assets.emergentagent.com/job_zerofeeliving/artifacts/v1dtdqj7_bath%201.webp",
        "https://customer-assets.emergentagent.com/job_zerofeeliving/artifacts/iubyhiwn_Studio%201.webp"
    ]
    
    print(f"📸 Using {len(images)} uploaded images")
    
    # Check if JS building exists
    building = await db.buildings.find_one({'name': 'JS'}, {'_id': 0})
    
    if not building:
        print("⚠️ JS building not found in database!")
        print("🏗️ Creating new building entry...")
        
        # Create building entry - you may want to update address details
        building_id = str(uuid4())
        building = {
            'id': building_id,
            'name': 'JS',
            'address': 'Address TBD',  # Update this with actual address
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',  # Update with actual zip
            'neighborhood': 'TBD',  # Update with actual neighborhood
            'source_url': '',
            'last_crawled': datetime.now(timezone.utc).isoformat()
        }
        
        await db.buildings.insert_one(building)
        print(f"✅ Created JS building (ID: {building_id})")
    else:
        building_id = building['id']
        print(f"✅ Found JS building (ID: {building_id})")
    
    # Create unit #408
    print("\n🏢 Creating Unit #408...")
    
    unit_id = str(uuid4())
    unit = {
        'id': unit_id,
        'building_id': building_id,
        'unit_number': '408',
        'rent': 3500.0,
        'bedrooms': 2,
        'bathrooms': 2.0,
        'square_feet': None,
        'available_date': 'Immediate',
        'amenities': [],
        'description': '',
        'images': images,
        'is_available': True,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.units.insert_one(unit)
    print(f"✅ Created Unit #408 with {len(images)} images!")
    
    print(f"\n📊 Unit Details:")
    print(f"   - Building: JS")
    print(f"   - Unit Number: 408")
    print(f"   - Bedrooms: 2")
    print(f"   - Bathrooms: 2")
    print(f"   - Rent: $3,500/month")
    print(f"   - Images: {len(images)} user-uploaded photos")
    print(f"\n⚠️  Note: Please update building address and neighborhood in the database")
    print(f"   Building ID: {building_id}")

if __name__ == "__main__":
    asyncio.run(main())
