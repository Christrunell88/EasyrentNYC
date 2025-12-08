"""
Script to add 205 E 59 St building and apartment listing to database
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
        "name": "205 East 59 Street",
        "address": "205 East 59 Street",
        "neighborhood": "Upper East Side",
        "city": "New York",
        "state": "NY",
        "zip_code": "10022",
        "source_url": "https://manhattanskyline.com/buildings/upper-east-side/205-e-59-st",
        "latitude": 40.7615,  # Approximate coordinates for 205 E 59 St
        "longitude": -73.9656,
        "last_crawled": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Unit data
    unit_id = str(uuid.uuid4())
    
    # Image URLs from the listing
    image_urls = [
        "https://manhattanskyline.com/storage/_styles/multi-hero/misc/zZfNr5YNYZL3ZfsHGRJEE1dy70qCGHef9WPT2wyw.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/vUW04uLPg3LMljBUdFFbPyvxKkfaG48lxvtHAEAH.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/15CxTGyQnN96EpYg4FDJ0dVdZfvOswSNAoNCKAih.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/Dchcsf0v5vwO63fSDK6Rc8ULntEIxupKTyMM8cQR.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/eRtREjZOBn3fhY9vuQHf1PPpKsQAEM9s6Mps8FH5.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/BUYL919uPtoxCnNxQ2TF8bnOXlkHSJnoU41ucoSn.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/Gf72MZwANZhDwPGr4CGZlpByOc9GRb2MCiQJaByZ.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/pQXe6m5GXttnF3h79m77GepLXvZtRXrADipvoJzB.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/ZLtILv07De9HrFttpIrRe53HDTPf4mWu8vEXOtVX.jpeg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/BV4EJc4tZYmxIn3oeiQFIhsbDVRtNiY9MzRKDltt.jpg",
        "https://manhattanskyline.com/storage/_styles/multi-hero/unit/ajgnCiBoxzS0NwmEmnMV7rReuuPj5LXRoy2ulVAz.jpg"
    ]
    
    # Amenities from the listing
    amenities = [
        "Terrace",
        "Balcony",
        "Granite Countertops",
        "Modern floors",
        "Icemaker",
        "Marble Baths",
        "Microwave",
        "Double height ceilings",
        "Garbage Disposal",
        "Gas burning fireplace",
        "Shower stall",
        "Skylight",
        "Stainless Steel Appliances",
        "Walk in closet",
        "Washer dryer",
        "Doorman",
        "Elevator",
        "Fitness Center",
        "Landscaped and Furnished Roof Deck",
        "Laundry in Building",
        "Pet Friendly",
        "Puppy Park",
        "Resident Manager",
        "Storage Units",
        "Tenant Lounge"
    ]
    
    description = """SHOWINGS BY APPOINTMENT ONLY.

A masterfully-designed Penthouse three-bedroom, three and a half-bathroom loft-like home with 21-foot ceilings. Living room with dramatic floor-to-ceiling windows, a glowing gas fireplace, two-zone central air conditioning, washer/dryer, four sizable walk in closets, and double exposures. Stunning views of the 59th Street Bridge from the living room.

The windowed open kitchen features top-of-the-line Viking appliances, a skylight and garbage disposal. The Master bedroom has a private balcony, terrace, and allows for king sized furniture and spacious living. Master bathroom features separate stall shower, soaking tub and custom climate control.

The second bedroom is also generously sized and has two large closets and easy access to the second bath. This is a rental in one of the most desirable full-service, white-glove condominiums in Manhattan. Only three homes per floor provide an optimal level of intimacy and exclusivity.

Lifestyle and recreational amenities include 24-hour doorman and concierge, private storage, full floor fitness center, central laundry, sun-drenched garden terrace and a private puppy park."""
    
    unit = {
        "id": unit_id,
        "building_id": building_id,
        "unit_number": "Penthouse",
        "rent": 18500.0,
        "bedrooms": 3,
        "bathrooms": 3.5,
        "square_feet": None,  # Not specified in listing
        "available_date": "Available Now",
        "amenities": amenities,
        "images": image_urls,
        "description": description,
        "is_available": True,
        "latitude": 40.7615,
        "longitude": -73.9656,
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
        
        # Insert unit
        await db.units.insert_one(unit)
        print(f"\n✅ Unit added successfully!")
        print(f"   Unit ID: {unit_id}")
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
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(add_listing())
