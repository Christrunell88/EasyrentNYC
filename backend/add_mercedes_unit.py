"""Add Mercedes House Unit #1826 to database"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv

load_dotenv()

async def add_unit():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Get Mercedes House building
    building = await db.buildings.find_one({'id': 'building-mercedes-house'}, {'_id': 0})
    
    if not building:
        print("❌ Mercedes House building not found")
        return
    
    print(f"✅ Found building: {building['name']}")
    
    # Create new unit
    unit_id = str(uuid.uuid4())
    
    unit_data = {
        'id': unit_id,
        'building_id': 'building-mercedes-house',
        'unit_number': '1826',
        'rent': 4995.0,
        'bedrooms': 1,
        'bathrooms': 1.0,
        'square_feet': None,  # Not specified
        'floor': 18,
        'description': '''Rent-stabilized south-facing one-bedroom on a high floor, featuring floor-to-ceiling windows that flood the space with natural light.

The apartment features hardwood oak floors, LED track lighting, and solar shades. The kitchen includes GE Profile stainless steel appliances, white Italian glass cabinets, composite stone island with breakfast bar extension, and garbage disposal in the kitchen sink. A Bosch stackable washer dryer is also included within the residence for your convenience!

Mercedes House, New York's most important new residential development is changing the cityscape forever. From Two Trees Management Company and visionary architect Enrique Norten comes a luxury rental complex spiraling 29 stories above the city with unobstructed views of the Hudson River.

Residents of Mercedes House experience more than just a place to live. Extraordinary amenities include a state-of-the-art wellness center, health club with indoor and outdoor swimming pools, outdoor decks with BBQ grills, private Pilates room, bocce courts, yoga, spinning, indoor basketball, boxing room, outdoor movie theater, spa facilities, and on-site indoor parking.

Incentive: 1 Month OP (Owner Pays)
Lease Term: 12-24 months
Pet Policy: Pets Allowed
Available: December 9, 2025''',
        'amenities': [
            'Doorman',
            'Elevator',
            'Gym',
            'Swimming Pool',
            'Parking Available',
            'Pets Allowed',
            'Laundry in Unit',
            'Dishwasher',
            'Microwave',
            'Hardwood Floors',
            'Floor to Ceiling Windows',
            'Island Kitchen',
            'Outdoor Areas',
            'Bike Storage',
            'Live-In Super'
        ],
        'images': [
            'https://assets-img.nestiostatic.com/unit_photos/originals/eaaac89e759c3a89c9bbbe1b9a104bf0.jpg',
            # Additional images would go here if we could scrape them
        ],
        'is_available': True,
        'no_fee': True,  # Assuming this is a no-fee listing
        'lease_term_months': '12-24',
        'pets_allowed': True,
        'available_date': '2025-12-09',
        'incentives': '1 Month OP',
        'source_url': 'https://api.funnelleasing.com/p/listing/15/18613/10/70t-f61e00c3b72b31c488b8/',
        'listing_id': '18613',
        'posted_to_facebook': False,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Check if unit already exists
    existing = await db.units.find_one({
        'building_id': 'building-mercedes-house',
        'unit_number': '1826'
    })
    
    if existing:
        print(f"⚠️  Unit #1826 already exists. Updating...")
        await db.units.update_one(
            {'id': existing['id']},
            {'$set': unit_data}
        )
        print(f"✅ Updated unit: {existing['id']}")
    else:
        await db.units.insert_one(unit_data)
        print(f"✅ Created new unit: {unit_id}")
    
    print(f"\nUnit Details:")
    print(f"  Building: {building['name']}")
    print(f"  Unit #: 1826")
    print(f"  Rent: ${unit_data['rent']:,.0f}/month")
    print(f"  Bedrooms: {unit_data['bedrooms']}")
    print(f"  Bathrooms: {unit_data['bathrooms']}")
    print(f"  Floor: {unit_data['floor']}")
    print(f"  Amenities: {len(unit_data['amenities'])}")
    print(f"  Images: {len(unit_data['images'])}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_unit())
