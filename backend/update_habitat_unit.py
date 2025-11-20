"""Scrape and update images for The Habitat unit PIHFKB0D"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from uuid import uuid4
import re

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def main():
    # Scrape the unit page
    url = 'https://manhattanskyline.com/buildings/kips-bay/the-habitat/apartment-pihfkb0d'
    
    print(f"🔍 Scraping: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        
        # Also extract unit details from the page
        title = await page.title()
        print(f"Page title: {title}")
        
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
        
        # Check if Habitat building exists
        building = await db.buildings.find_one({'name': 'Habitat'}, {'_id': 0})
        
        if not building:
            print("\n⚠️ Habitat building not found in database!")
            print("🏗️ Creating new building entry...")
            
            # Create building entry
            building_id = str(uuid4())
            building = {
                'id': building_id,
                'name': 'Habitat',
                'address': '154 East 29th Street',
                'city': 'New York',
                'state': 'NY',
                'zip_code': '10016',
                'neighborhood': 'Kips Bay',
                'source_url': 'https://manhattanskyline.com/buildings/kips-bay/the-habitat',
                'last_crawled': datetime.now(timezone.utc).isoformat()
            }
            
            await db.buildings.insert_one(building)
            print(f"✅ Created Habitat building (ID: {building_id})")
        else:
            building_id = building['id']
            print(f"\n✅ Found Habitat building (ID: {building_id})")
        
        # Find or create unit PIHFKB0D
        unit = await db.units.find_one({'unit_number': 'PIHFKB0D'}, {'_id': 0})
        
        if not unit:
            print("⚠️ Unit PIHFKB0D not found in database!")
            print("🏢 Creating new unit entry...")
            
            # Try to extract unit details from page
            text_content = soup.get_text()
            
            # Extract rent
            rent = 0.0
            rent_match = re.search(r'\$([0-9,]+)', text_content)
            if rent_match:
                rent = float(rent_match.group(1).replace(',', ''))
            
            # Extract bedrooms
            bedrooms = 1  # Default
            bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', text_content, re.I)
            if bed_match:
                bedrooms = int(bed_match.group(1))
            elif re.search(r'studio', text_content, re.I):
                bedrooms = 0
            
            # Extract bathrooms
            bathrooms = 1.0
            bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', text_content, re.I)
            if bath_match:
                bathrooms = float(bath_match.group(1))
            
            print(f"   Detected: {bedrooms}BR, {bathrooms}BA, ${rent}/month")
            
            # Create unit entry
            unit_id = str(uuid4())
            unit = {
                'id': unit_id,
                'building_id': building_id,
                'unit_number': 'PIHFKB0D',
                'rent': rent,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'square_feet': None,
                'available_date': 'Immediate',
                'amenities': [],
                'description': '',
                'images': final_images,
                'is_available': True,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            await db.units.insert_one(unit)
            print(f"✅ Created unit PIHFKB0D with {len(final_images)} images!")
        else:
            print(f"✅ Found unit PIHFKB0D")
            print(f"🔄 Updating unit with new images...")
            
            # Update the unit with real images
            result = await db.units.update_one(
                {'id': unit['id']},
                {
                    '$set': {
                        'images': final_images,
                        'is_available': True,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Successfully updated unit PIHFKB0D with {len(final_images)} images!")
        
        print(f"\n📊 Unit Details:")
        print(f"   - Unit Number: PIHFKB0D")
        print(f"   - Rent: ${unit['rent']}")
        print(f"   - Bedrooms: {unit['bedrooms']}")
        print(f"   - Bathrooms: {unit['bathrooms']}")
        print(f"   - Building: Habitat")
        print(f"   - Location: Kips Bay, New York")

if __name__ == "__main__":
    asyncio.run(main())
