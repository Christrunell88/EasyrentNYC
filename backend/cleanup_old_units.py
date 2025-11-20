"""Clean up old placeholder units and keep only units with real images or proper unit numbers"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def main():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Cleaning up old placeholder units...")
    
    # Delete units with generic auto-generated names (Unit-0BR-X, Unit-1BR-X, etc.) 
    # AND with Unsplash placeholder images
    result = await db.units.delete_many({
        'unit_number': {'$regex': '^Unit-[0-9]BR-[0-9]+$'},
        'images.0': {'$regex': 'unsplash'}
    })
    
    print(f"Deleted {result.deleted_count} old placeholder units with generic names")
    
    # Also remove old units with no images at all
    result2 = await db.units.delete_many({
        'unit_number': {'$regex': '^Unit-[0-9]BR-[0-9]+$'},
        '$or': [
            {'images': []},
            {'images': {'$exists': False}}
        ]
    })
    
    print(f"Deleted {result2.deleted_count} old units with generic names and no images")
    
    # Count remaining units
    total = await db.units.count_documents({})
    with_images = await db.units.count_documents({'images.0': {'$exists': True}})
    with_real_images = await db.units.count_documents({
        'images.0': {'$exists': True, '$regex': '^((?!unsplash).)*$'}
    })
    
    print(f"\nRemaining units: {total}")
    print(f"Units with images: {with_images}")
    print(f"Units with real images: {with_real_images}")

if __name__ == "__main__":
    asyncio.run(main())
