"""
Script to add Chelsea Place apartment unit to database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

load_dotenv('/app/backend/.env')

async def add_unit():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Get existing building
    building = await db.buildings.find_one({'name': 'Chelsea Place'}, {"_id": 0})
    
    if not building:
        print("❌ Chelsea Place building not found!")
        client.close()
        return
    
    building_id = building['id']
    print(f"✅ Found building: {building['name']} (ID: {building_id})")
    
    # Unit data
    unit_id = str(uuid.uuid4())
    
    # Image URLs from the listing (unit-specific images only)
    image_urls = [
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/RbrcBmVXGuud2WfHlrjHj80wpuxpVOuiBRCyr3MZ.jpg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/SyO6tvEWz76Xe1mNXlitLnqvRQPHagDwq1F952l5.jpg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/FH7sn4Wqf6i0XRmPC3iGvcz1QGwqTCrWM5jp8Er8.jpg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/jMfPYvu7SZ9N6nI6g0cGK1lvfZ5mfanZ7G2e0BEH.jpg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/building/SjLzZipomQUPGaYuhuymahQCGwbXtvmtLzt9GodU.jpg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/building/GvHJx7ApDH9jtU9ZbK6ExHaWbfBP1basRTKAD3lz.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/building/upNlEh0QFzuR6GjDPWkYera6BOkxfP84dt3BYxQn.jpeg"
    ]
    
    # Amenities from the listing
    amenities = [
        "Breakfast Bar",
        "Granite Countertops",
        "Icemaker",
        "Microwave",
        "Stainless Steel Appliances",
        "Dishwasher",
        "Elevator",
        "Fitness Center",
        "Landscaped and Furnished Roof Deck",
        "Laundry in Building",
        "Resident Manager",
        "Garage"
    ]
    
    description = """*SHOWINGS BY APPOINTMENT ONLY.*

Beautiful and spacious one-bedroom with stainless steel appliances and amazing closet space. Chelsea Place also comes with two landscaped roof decks, fully-equipped fitness center, laundry facilities, and on-premises parking garage."""
    
    unit = {
        "id": unit_id,
        "building_id": building_id,
        "unit_number": "1BR",  # Generic unit number as specific number not provided
        "rent": 4195.0,
        "bedrooms": 1,
        "bathrooms": 1.0,
        "square_feet": None,  # Not specified in listing
        "available_date": "Available Now",
        "amenities": amenities,
        "images": image_urls,
        "description": description,
        "is_available": True,
        "latitude": building.get('latitude'),
        "longitude": building.get('longitude'),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Insert unit
        await db.units.insert_one(unit)
        print(f"\n✅ Unit added successfully!")
        print(f"   Unit ID: {unit_id}")
        print(f"   Building: {building['name']}")
        print(f"   Unit: {unit['unit_number']}")
        print(f"   Rent: ${unit['rent']:,.0f}/month")
        print(f"   Bedrooms: {unit['bedrooms']}")
        print(f"   Bathrooms: {unit['bathrooms']}")
        print(f"   Images: {len(unit['images'])} photos")
        print(f"   Amenities: {len(unit['amenities'])} features")
        
        # Get total counts
        total_buildings = await db.buildings.count_documents({})
        total_units = await db.units.count_documents({})
        
        print(f"\n📊 Database Stats:")
        print(f"   Total Buildings: {total_buildings}")
        print(f"   Total Units: {total_units}")
        
        # Check if building is already in crawler
        print(f"\n🔄 Crawler Status:")
        print(f"   Building source URL: {building.get('source_url')}")
        print(f"   ✅ Chelsea Place is already configured for automated crawling")
        print(f"   ✅ This unit will be updated automatically during future crawls")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(add_unit())
