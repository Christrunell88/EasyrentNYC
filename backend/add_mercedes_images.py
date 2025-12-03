"""Add uploaded images to Mercedes House Unit #1826"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def add_images():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # New image URLs (user uploaded + original)
    new_images = [
        'https://customer-assets.emergentagent.com/job_nofee-finder-1/artifacts/a0ses57e_Mercedes%201.jpg',
        'https://customer-assets.emergentagent.com/job_nofee-finder-1/artifacts/7bvbkwsc_Mercedes%202.jpg',
        'https://customer-assets.emergentagent.com/job_nofee-finder-1/artifacts/0wrqdovo_Mercedes%203.jpg',
        'https://customer-assets.emergentagent.com/job_nofee-finder-1/artifacts/f05g11e2_Mercedes%204.jpg',
        'https://assets-img.nestiostatic.com/unit_photos/originals/eaaac89e759c3a89c9bbbe1b9a104bf0.jpg'
    ]
    
    # Update the unit
    result = await db.units.update_one(
        {'unit_number': '1826', 'building_id': 'building-mercedes-house'},
        {
            '$set': {
                'images': new_images,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count > 0:
        print(f'✅ Successfully added {len(new_images)} images to Mercedes House Unit #1826')
        print(f'\nImage URLs added:')
        for i, img in enumerate(new_images, 1):
            filename = img.split('/')[-1].replace('%20', ' ')
            print(f'  {i}. {filename}')
        
        # Verify
        unit = await db.units.find_one(
            {'unit_number': '1826', 'building_id': 'building-mercedes-house'},
            {'_id': 0, 'id': 1, 'images': 1}
        )
        print(f'\n✅ Verified: Unit now has {len(unit["images"])} images')
        print(f'\nView listing: https://nofeesapts.com/unit/{unit["id"]}')
    else:
        print('❌ Failed to update unit')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_images())
