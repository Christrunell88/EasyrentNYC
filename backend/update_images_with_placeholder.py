"""Update units to use 'Pics Coming Soon' placeholder for unverified images"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Placeholder image URL - generic living room with "Pics Coming Soon" overlay
PLACEHOLDER_IMAGE = "https://images.unsplash.com/photo-1556912173-46c336c7fd55?w=800&q=80"  # Generic modern living room

# Harrison Yards building ID - keep these real images
HARRISON_YARDS_ID = "b589a50a-b78d-461d-bee6-68d47073a514"

async def main():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔄 Updating images with 'Pics Coming Soon' placeholder...")
    
    # Get all units
    all_units = await db.units.find({}, {'_id': 0, 'id': 1, 'building_id': 1, 'unit_number': 1, 'images': 1}).to_list(1000)
    
    updated_count = 0
    kept_real_count = 0
    no_change_count = 0
    
    for unit in all_units:
        unit_id = unit['id']
        building_id = unit['building_id']
        current_images = unit.get('images', [])
        
        # Keep Harrison Yards real images (from myleasestar.com)
        if building_id == HARRISON_YARDS_ID:
            has_real_images = any('myleasestar.com' in img for img in current_images)
            if has_real_images:
                kept_real_count += 1
                continue
        
        # Check if unit has Unsplash placeholders or unverified images
        needs_placeholder = False
        
        if not current_images:
            needs_placeholder = True
        elif any('unsplash' in img for img in current_images):
            needs_placeholder = True
        elif building_id != HARRISON_YARDS_ID:
            # For non-Harrison Yards, replace any images with placeholder
            # since we can't verify they're unit-specific
            if current_images:
                needs_placeholder = True
        
        if needs_placeholder:
            # Update to placeholder
            await db.units.update_one(
                {'id': unit_id},
                {
                    '$set': {
                        'images': [PLACEHOLDER_IMAGE],
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            updated_count += 1
            print(f"  ✓ Updated {unit['unit_number']} (Building: {building_id[:20]}...)")
        else:
            no_change_count += 1
    
    print(f"\n✅ Update Complete!")
    print(f"   Updated with placeholder: {updated_count} units")
    print(f"   Kept verified real images: {kept_real_count} units (Harrison Yards)")
    print(f"   No change needed: {no_change_count} units")
    
    # Summary by building
    print(f"\n📊 Summary by Building:")
    buildings = await db.buildings.find({}, {'_id': 0, 'id': 1, 'name': 1}).to_list(10)
    
    for bldg in buildings:
        total = await db.units.count_documents({'building_id': bldg['id']})
        with_placeholder = await db.units.count_documents({
            'building_id': bldg['id'],
            'images': [PLACEHOLDER_IMAGE]
        })
        with_real = await db.units.count_documents({
            'building_id': bldg['id'],
            'images.0': {'$regex': 'myleasestar.com'}
        })
        
        status = "Placeholders" if with_placeholder > 0 else ("Real Images" if with_real > 0 else "Mixed")
        print(f"   {bldg['name']}: {total} units - {status}")

if __name__ == "__main__":
    asyncio.run(main())
