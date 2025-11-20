"""Scrape and update images for 60 Water unit 719"""
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
    url = 'https://www.twotreesny.com/apartments/60-water/studio/719'
    
    print(f"🔍 Scraping: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(5000)  # Wait longer for Two Trees site to load
        
        content = await page.content()
        
        # Also extract unit details from the page
        title = await page.title()
        print(f"Page title: {title}")
        
        await browser.close()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all images - need to wait for JS-loaded content
        # Two Trees uses Nestio for property management, images are from nestiostatic.com
        all_images = []
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
            if src:
                # Clean up URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.twotreesny.com' + src
                
                # Filter out logos, icons, SVGs
                if src.startswith('https://') and not any(x in src.lower() for x in ['logo', 'icon', 'favicon', '.svg']):
                    # Include images from Nestio CDN (actual unit photos) or other image hosts
                    if 'nestiostatic.com' in src or 'cloudinary' in src or 'imgix' in src or '.jpg' in src or '.png' in src:
                        all_images.append(src)
        
        # Also check for background images in style attributes
        for elem in soup.find_all(style=True):
            style = elem.get('style', '')
            bg_matches = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
            for bg_url in bg_matches:
                if bg_url.startswith('//'):
                    bg_url = 'https:' + bg_url
                elif bg_url.startswith('/'):
                    bg_url = 'https://www.twotreesny.com' + bg_url
                
                if bg_url.startswith('https://') and 'twotrees' in bg_url.lower():
                    all_images.append(bg_url)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in all_images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        print(f"✅ Found {len(unique_images)} total images")
        print(f"\n📸 Storing {len(unique_images)} images for this unit\n")
        
        # Display the images we're storing
        for i, img in enumerate(unique_images[:10], 1):
            print(f"   {i}. {img[:90]}...")
        
        if len(unique_images) > 10:
            print(f"   ... and {len(unique_images) - 10} more images")
        
        # Update database
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Check if 60 Water building exists
        building = await db.buildings.find_one({'name': '60 Water'}, {'_id': 0})
        
        if not building:
            print("\n⚠️ 60 Water building not found in database!")
            print("🏗️ Creating new building entry...")
            
            # Create building entry
            building_id = str(uuid4())
            building = {
                'id': building_id,
                'name': '60 Water',
                'address': '60 Water Street',
                'city': 'Brooklyn',
                'state': 'NY',
                'zip_code': '11201',
                'neighborhood': 'DUMBO',
                'source_url': 'https://www.twotreesny.com/apartments/60-water',
                'last_crawled': datetime.now(timezone.utc).isoformat()
            }
            
            await db.buildings.insert_one(building)
            print(f"✅ Created 60 Water building (ID: {building_id})")
        else:
            building_id = building['id']
            print(f"\n✅ Found 60 Water building (ID: {building_id})")
        
        # Find or create unit 719
        unit = await db.units.find_one({'unit_number': '719', 'building_id': building_id}, {'_id': 0})
        
        if not unit:
            print("⚠️ Unit 719 not found in database!")
            print("🏢 Creating new unit entry...")
            
            # Try to extract unit details from page
            text_content = soup.get_text()
            
            # Extract rent
            rent = 0.0
            rent_match = re.search(r'\$([0-9,]+)', text_content)
            if rent_match:
                rent = float(rent_match.group(1).replace(',', ''))
            
            # This is a studio based on URL
            bedrooms = 0  # Studio
            bathrooms = 1.0
            
            # Try to find bathroom count
            bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', text_content, re.I)
            if bath_match:
                bathrooms = float(bath_match.group(1))
            
            print(f"   Detected: Studio (0BR), {bathrooms}BA, ${rent}/month")
            
            # Create unit entry
            unit_id = str(uuid4())
            unit = {
                'id': unit_id,
                'building_id': building_id,
                'unit_number': '719',
                'rent': rent,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'square_feet': None,
                'available_date': 'Immediate',
                'amenities': [],
                'description': '',
                'images': unique_images,
                'is_available': True,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            await db.units.insert_one(unit)
            print(f"✅ Created unit 719 with {len(unique_images)} images!")
        else:
            print(f"✅ Found unit 719")
            print(f"🔄 Updating unit with new images...")
            
            # Update the unit with real images
            result = await db.units.update_one(
                {'id': unit['id']},
                {
                    '$set': {
                        'images': unique_images,
                        'is_available': True,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Successfully updated unit 719 with {len(unique_images)} images!")
        
        print(f"\n📊 Unit Details:")
        print(f"   - Unit Number: 719")
        print(f"   - Rent: ${unit['rent']}")
        print(f"   - Bedrooms: {unit['bedrooms']} (Studio)")
        print(f"   - Bathrooms: {unit['bathrooms']}")
        print(f"   - Building: 60 Water")
        print(f"   - Location: DUMBO, Brooklyn")

if __name__ == "__main__":
    asyncio.run(main())
