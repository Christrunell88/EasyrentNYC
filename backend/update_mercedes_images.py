"""
Update Mercedes House units with curated interior images
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Curated high-quality images for Mercedes House from Vision Expert
MERCEDES_HOUSE_IMAGES = [
    "https://images.unsplash.com/photo-1638454668466-e8dbd5462f20?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHxsdXh1cnklMjBhcGFydG1lbnQlMjBpbnRlcmlvcnxlbnwwfHx8fDE3NjQwMTkxMDN8MA&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1556020685-ae41abfc9365?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwyfHxsdXh1cnklMjBhcGFydG1lbnQlMjBpbnRlcmlvcnxlbnwwfHx8fDE3NjQwMTkxMDN8MA&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1512914890251-2f96a9b0bbe2?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwzfHxsdXh1cnklMjBhcGFydG1lbnQlMjBpbnRlcmlvcnxlbnwwfHx8fDE3NjQwMTkxMDN8MA&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1556912167-f556f1f39fdf?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBraXRjaGVufGVufDB8fHx8MTc2NDAxOTEwOXww&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1600489000022-c2086d79f9d4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwyfHxtb2Rlcm4lMjBraXRjaGVufGVufDB8fHx8MTc2NDAxOTEwOXww&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1628745277862-bc0b2d68c50c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHw0fHxtb2Rlcm4lMjBraXRjaGVufGVufDB8fHx8MTc2NDAxOTEwOXww&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1649429710616-dad56ce9a076?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzV8MHwxfHNlYXJjaHwxfHxhcGFydG1lbnQlMjBsaXZpbmclMjByb29tJTIwY2l0eSUyMHZpZXd8ZW58MHx8fHwxNzY0MDE5MTE2fDA&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1760611655728-f5f0279ed611?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzV8MHwxfHNlYXJjaHwzfHxhcGFydG1lbnQlMjBsaXZpbmclMjByb29tJTIwY2l0eSUyMHZpZXd8ZW58MHx8fHwxNzY0MDE5MTE2fDA&ixlib=rb-4.1.0&q=85",
    "https://images.pexels.com/photos/34887637/pexels-photo-34887637.jpeg",
    "https://images.pexels.com/photos/2724749/pexels-photo-2724749.jpeg"
]

async def update_mercedes_house_images():
    """Update all Mercedes House units with curated images"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("="*80)
    print("🏢 Mercedes House Image Update")
    print("="*80)
    print()
    
    # Find Mercedes House building
    building = await db.buildings.find_one(
        {"name": {"$regex": "Mercedes House", "$options": "i"}},
        {"_id": 0}
    )
    
    if not building:
        print("❌ Mercedes House building not found in database")
        client.close()
        return
    
    print(f"✅ Found building: {building['name']}")
    print(f"   Building ID: {building['id']}")
    print()
    
    # Find all units for Mercedes House
    units = await db.units.find(
        {"building_id": building['id']},
        {"_id": 0}
    ).to_list(100)
    
    print(f"📊 Found {len(units)} Mercedes House units")
    print()
    
    # Update each unit with a diverse set of images
    updated_count = 0
    
    for idx, unit in enumerate(units):
        unit_id = unit['id']
        unit_number = unit.get('unit_number', 'N/A')
        
        # Assign 3-4 different images per unit for variety
        # Rotate through the image pool so each unit gets different combinations
        start_idx = (idx * 3) % len(MERCEDES_HOUSE_IMAGES)
        unit_images = [
            MERCEDES_HOUSE_IMAGES[start_idx],
            MERCEDES_HOUSE_IMAGES[(start_idx + 1) % len(MERCEDES_HOUSE_IMAGES)],
            MERCEDES_HOUSE_IMAGES[(start_idx + 2) % len(MERCEDES_HOUSE_IMAGES)],
            MERCEDES_HOUSE_IMAGES[(start_idx + 5) % len(MERCEDES_HOUSE_IMAGES)]
        ]
        
        # Update the unit
        result = await db.units.update_one(
            {"id": unit_id},
            {"$set": {"images": unit_images}}
        )
        
        if result.modified_count > 0:
            updated_count += 1
            print(f"✅ Updated Unit {unit_number} (ID: {unit_id})")
            print(f"   Added {len(unit_images)} images")
        else:
            print(f"⚠️  Unit {unit_number} - no changes made")
        
        print()
    
    print("="*80)
    print(f"🎉 Update Complete!")
    print(f"   Total units updated: {updated_count}/{len(units)}")
    print("="*80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_mercedes_house_images())
