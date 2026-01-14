"""Add 20 Park Avenue building and its units to the database"""
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
    
    print("🏢 Adding 20 Park Avenue building...\n")
    
    # Building data
    building_id = str(uuid4())
    building = {
        'id': building_id,
        'name': '20 Park Avenue',
        'address': '20 Park Avenue',
        'city': 'New York',
        'state': 'NY',
        'zip_code': '10016',
        'neighborhood': 'Murray Hill',
        'source_url': 'https://www.stonehengenyc.com/buildings/20-park',
        'latitude': 40.7464,  # Murray Hill approximate coordinates
        'longitude': -73.9805,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'last_crawled': datetime.now(timezone.utc).isoformat()
    }
    
    # Check if building already exists
    existing_building = await db.buildings.find_one({'name': '20 Park Avenue'})
    if existing_building:
        building_id = existing_building['id']
        print(f"✅ Building already exists (ID: {building_id})")
    else:
        await db.buildings.insert_one(building)
        print(f"✅ Created building: 20 Park Avenue (ID: {building_id})")
    
    # Building amenities (shared by all units)
    building_amenities = [
        "Fitness Center",
        "Full-time Doorman",
        "On-site Laundry Room",
        "Elevator",
        "Pet Friendly",
        "Business Center",
        "Children's Playroom",
        "Private Courtyard",
        "Billiards Room",
        "On-site Parking",
        "Gym with Peleton Bike",
        "Private Outdoor Space",
        "Member's Lounge",
        "Rooftop Sundeck"
    ]
    
    # Unit 1: 012G - 3BR/3BA
    unit_012G_images = [
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb6a2_01.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb6a8_03.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb69c_04.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb6b0_06.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb69f_07.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb6a5_08.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb6b3_09.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb6b6_10.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb696_12.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb6b9_15.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb690_16.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083e1539315bd4bdb693_17.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083f1539315bd4bdb6bc_19.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083f1539315bd4bdb6c2_20.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/6932083f1539315bd4bdb6bf_21.webp"
    ]
    
    # Check if unit 012G already exists
    existing_012G = await db.units.find_one({'building_id': building_id, 'unit_number': '012G'})
    if not existing_012G:
        unit_012G = {
            'id': str(uuid4()),
            'building_id': building_id,
            'unit_number': '012G',
            'rent': 11595.0,
            'bedrooms': 3,
            'bathrooms': 3.0,
            'square_feet': 1485,
            'available_date': 'Immediate',
            'amenities': building_amenities + ["In-home Washer/Dryer", "High Beamed Ceilings", "En Suite Bath"],
            'description': 'This rarely available true 3 bedroom 3 bathroom residence features beautiful condo level renovations with high beamed ceilings and great natural light. The primary bedroom includes an en suite bath and ample closet space. There is also an in home washer/dryer.',
            'images': unit_012G_images,
            'is_available': True,
            'is_featured': False,
            'latitude': 40.7464,
            'longitude': -73.9805,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(unit_012G)
        print(f"✅ Created Unit 012G: 3BR/3BA - $11,595/month")
    else:
        print(f"⚠️ Unit 012G already exists")
    
    # Unit 2: 017B - 1BR/1BA
    unit_017B_images = [
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968a0fe12387b5706050_20%20Park%20Avenue%20-%20017B%201.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968a5d7c9250f0f8a292_20%20Park%20Avenue%20-%20017B%202.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968ad08b97b3c5674472_20%20Park%20Avenue%20-%20017B%203.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968a8af3e280eff89051_20%20Park%20Avenue%20-%20017B%204.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e96892fab314ce2f14d71_20%20Park%20Avenue%20-%20017B%205.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968ac61b34c81eeef0a1_20%20Park%20Avenue%20-%20017B%206.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968abde9cc8d7379b7ab_20%20Park%20Avenue%20-%20017B%207.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968a719a2c5ff40de7bb_20%20Park%20Avenue%20-%20017B%208.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968a1d72b06bdf00a5ef_20%20Park%20Avenue%20-%20017B%209.webp",
        "https://cdn.prod.website-files.com/661f3aa60ea0bc1c374869b6/692e968a8de2b577e420e302_20%20Park%20Avenue%20-%20017B%2010.webp"
    ]
    
    # Check if unit 017B already exists
    existing_017B = await db.units.find_one({'building_id': building_id, 'unit_number': '017B'})
    if not existing_017B:
        unit_017B = {
            'id': str(uuid4()),
            'building_id': building_id,
            'unit_number': '017B',
            'rent': 6695.0,
            'bedrooms': 1,
            'bathrooms': 1.0,
            'square_feet': 936,
            'available_date': 'Immediate',
            'amenities': building_amenities + ["Private Terrace", "City Views", "Open Kitchen"],
            'description': 'This stunning and spacious one-bedroom apartment boasts modern renovations, an open kitchen and an excellent and adaptable flow. Best of all is the large-fabulous terrace with clear city views.',
            'images': unit_017B_images,
            'is_available': True,
            'is_featured': False,
            'latitude': 40.7464,
            'longitude': -73.9805,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        await db.units.insert_one(unit_017B)
        print(f"✅ Created Unit 017B: 1BR/1BA - $6,695/month")
    else:
        print(f"⚠️ Unit 017B already exists")
    
    # Summary
    print("\n📊 Summary:")
    print(f"   Building: 20 Park Avenue, Murray Hill, NY 10016")
    print(f"   Unit 012G: 3BR/3BA, 1485 sqft, $11,595/month")
    print(f"   Unit 017B: 1BR/1BA, 936 sqft, $6,695/month")
    
    # Get total count
    total_units = await db.units.count_documents({})
    total_buildings = await db.buildings.count_documents({})
    print(f"\n📈 Database totals: {total_buildings} buildings, {total_units} units")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
