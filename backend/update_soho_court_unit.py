"""Scrape and update images for Soho Court unit 1KYT6SGK"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from uuid import uuid4

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def main():
    # Scrape the unit page
    url = 'https://manhattanskyline.com/buildings/soho/soho-court/apartment-1kyt6sgk'
    
    print(f"🔍 Scraping: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        await browser.close()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all images
        all_images = []
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # Clean up URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://manhattanskyline.com' + src
                
                # Filter out logos, icons, thumbnails
                if src.startswith('https://') and not any(x in src.lower() for x in ['logo', 'icon', 'favicon', 'thumb']):
                    # Only include storage URLs (actual photos)
                    if 'storage' in src or 'manhattanskyline.com' in src:
                        all_images.append(src)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in all_images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        # Prioritize unit images over building/neighborhood images
        unit_images = [img for img in unique_images if '/unit/' in img]
        building_images = [img for img in unique_images if '/building/' in img]
        
        # Use unit images first, then add some building images
        final_images = unit_images + building_images[:3]
        
        print(f"✅ Found {len(unique_images)} total images")
        print(f"   - {len(unit_images)} unit-specific images")
        print(f"   - {len(building_images)} building images")
        print(f"\n📸 Storing {len(final_images)} images for this unit\n")
        
        # Display the images we're storing
        for i, img in enumerate(final_images[:8], 1):
            img_type = "UNIT" if '/unit/' in img else "BUILDING"
            print(f"   {i}. [{img_type}] {img[:80]}...")
        
        # Update database
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Check if Soho Court building exists
        building = await db.buildings.find_one({'name': 'Soho Court'}, {'_id': 0})
        
        if not building:
            print("\n⚠️ Soho Court building not found in database!")
            print("🏗️ Creating new building entry...")
            
            # Create building entry
            building_id = str(uuid4())
            building = {
                'id': building_id,
                'name': 'Soho Court',
                'address': '301 Elizabeth Street',
                'city': 'New York',
                'state': 'NY',
                'zip_code': '10012',
                'neighborhood': 'SoHo',
                'source_url': 'https://manhattanskyline.com/buildings/soho/soho-court',
                'last_crawled': datetime.now(timezone.utc).isoformat()
            }
            
            await db.buildings.insert_one(building)
            print(f"✅ Created Soho Court building (ID: {building_id})")
        else:
            building_id = building['id']
            print(f"\n✅ Found Soho Court building (ID: {building_id})")
        
        # Find or create unit 1KYT6SGK
        unit = await db.units.find_one({'unit_number': '1KYT6SGK'}, {'_id': 0})
        
        if not unit:
            print("⚠️ Unit 1KYT6SGK not found in database!")
            print("🏢 Creating new unit entry...")
            
            # Create unit entry
            unit_id = str(uuid4())
            unit = {
                'id': unit_id,
                'building_id': building_id,
                'unit_number': '1KYT6SGK',
                'rent': 7350.0,
                'bedrooms': 2,
                'bathrooms': 2.0,
                'square_feet': None,
                'available_date': 'Immediate',
                'amenities': [],
                'description': '',
                'images': final_images,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            await db.units.insert_one(unit)
            print(f"✅ Created unit 1KYT6SGK with {len(final_images)} images!")
        else:
            print(f"✅ Found unit 1KYT6SGK")
            print(f"🔄 Updating unit with new images...")
            
            # Update the unit with real images
            result = await db.units.update_one(
                {'id': unit['id']},
                {
                    '$set': {
                        'images': final_images,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Successfully updated unit 1KYT6SGK with {len(final_images)} images!")
        
        print(f"\n📊 Unit Details:")
        print(f"   - Unit Number: 1KYT6SGK")
        print(f"   - Rent: $7,350")
        print(f"   - Bedrooms: 2")
        print(f"   - Bathrooms: 2")
        print(f"   - Building: Soho Court")
        print(f"   - Location: SoHo, New York")

if __name__ == "__main__":
    asyncio.run(main())
