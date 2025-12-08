"""
Script to add Malt Drive building and apartment listing to database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

load_dotenv('/app/backend/.env')

async def add_listing():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Building data
    building_id = str(uuid.uuid4())
    building = {
        "id": building_id,
        "name": "Malt Drive Modern Apartments",
        "address": "2-21 Malt Drive",
        "neighborhood": "Long Island City",
        "city": "New York",
        "state": "NY",
        "zip_code": "11101",  # Hunter's Point South, LIC
        "source_url": "https://maltdrive.com",
        "latitude": 40.7420,  # Hunter's Point South coordinates
        "longitude": -73.9580,
        "last_crawled": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Unit data
    unit_id = str(uuid.uuid4())
    
    # Image URLs from the listing
    image_urls = [
        "https://maltdrive.com/wp-content/uploads/2025/07/2-21-malt-800x600-2.avif",
        "https://maltdrive.com/wp-content/uploads/2025/05/2-21-malt-800x600-110.avif",
        "https://maltdrive.com/wp-content/uploads/2025/05/2-21-malt-800x600-117.avif",
        "https://maltdrive.com/wp-content/uploads/2025/07/2-21-malt-800x600-22.avif",
        "https://maltdrive.com/wp-content/uploads/2025/07/2-21-malt-800x600-23.avif",
        "https://maltdrive.com/wp-content/uploads/2025/05/2-21-malt-800x600-14.avif",
        "https://maltdrive.com/wp-content/uploads/2025/05/2-21-malt-800x600-118.avif",
        "https://maltdrive.com/wp-content/uploads/2025/05/2-21-malt-800x600-111.avif",
        "https://maltdrive.com/wp-content/uploads/2025/05/2-21-malt-800x600-15.avif",
        "https://maltdrive.com/wp-content/uploads/2025/05/2-21-malt-800x600-12.avif"
    ]
    
    # Amenities from the listing
    amenities = [
        "Northern Exposure",
        "High Ceiling (14+ Ft)",
        "Linear Kitchen",
        "In-Unit Washer/Dryer",
        "Solar Shades",
        "Ample Closet Space",
        "Rooftop Pool",
        "Sundeck",
        "Fitness Center",
        "Lounge/Party Room",
        "On-Site Parking",
        "Hunter's Point South Park Access",
        "Waterfront Location"
    ]
    
    description = """Must-See Loft-Like Studio, 1 Bath Apartment Featuring Soaring High Ceilings (14+ Ft), a Beautiful Linear Kitchen, In-Home Washer/Dryer, Ample Closet Space, and Northern Exposure.

Located in Hunter's Point South, one of Long Island City's most desirable waterfront neighborhoods. The building features modern apartments with premium amenities including a rooftop pool, sundeck, fitness center, and easy access to Hunter's Point South Park.

Special Offer: Up to 3 months free on 24-month lease + 1 month OP. Half month security deposit for well-qualified applicants.

Gross Rent: $3,610/month
Net Effective Rent: $3,159/month (with concessions)"""
    
    unit = {
        "id": unit_id,
        "building_id": building_id,
        "unit_number": "205",
        "rent": 3610.0,  # Gross rent
        "bedrooms": 0,  # Studio
        "bathrooms": 1.0,
        "square_feet": None,  # Not specified
        "available_date": "Available Now",
        "amenities": amenities,
        "images": image_urls,
        "description": description,
        "is_available": True,
        "latitude": 40.7420,
        "longitude": -73.9580,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Insert building
        await db.buildings.insert_one(building)
        print(f"✅ Building added successfully!")
        print(f"   Building ID: {building_id}")
        print(f"   Name: {building['name']}")
        print(f"   Address: {building['address']}")
        print(f"   Neighborhood: {building['neighborhood']}")
        print(f"   Source URL: {building['source_url']}")
        
        # Insert unit
        await db.units.insert_one(unit)
        print(f"\n✅ Unit added successfully!")
        print(f"   Unit ID: {unit_id}")
        print(f"   Unit: #{unit['unit_number']}")
        print(f"   Rent: ${unit['rent']:,.0f}/month (Gross)")
        print(f"   Net Effective: $3,159/month (with concessions)")
        print(f"   Type: Studio")
        print(f"   Bathrooms: {unit['bathrooms']}")
        print(f"   Images: {len(unit['images'])} photos")
        print(f"   Amenities: {len(unit['amenities'])} features")
        print(f"   Special: High Ceilings (14+ Ft), In-Unit W/D, Rooftop Pool")
        
        # Get total counts
        total_buildings = await db.buildings.count_documents({})
        total_units = await db.units.count_documents({})
        
        print(f"\n📊 Database Stats:")
        print(f"   Total Buildings: {total_buildings}")
        print(f"   Total Units: {total_units}")
        
        print(f"\n🔄 Crawler Configuration:")
        print(f"   ⚠️  This is a NEW building source (maltdrive.com)")
        print(f"   📝 TODO: Add maltdrive.com to the crawler configuration")
        print(f"   🌐 Building URL: https://maltdrive.com")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(add_listing())
