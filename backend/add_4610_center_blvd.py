"""Scrape and add 4610 Center Boulevard unit from TFC.com"""
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
    url = 'https://tfc.com/long-island-city-lic/luxury-no-fee-apartments/4610-center-blvd/apt/1920'
    
    print(f"🔍 Scraping: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(5000)
        
        content = await page.content()
        
        # Extract title for info
        title = await page.title()
        print(f"Page title: {title}")
        
        await browser.close()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all images
        all_images = []
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
            if src:
                # Clean up URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://tfc.com' + src
                
                # Filter out logos, icons
                if src.startswith('https://') and not any(x in src.lower() for x in ['logo', 'icon', 'favicon', 'sprite']):
                    # Include TFC images
                    if 'tfc.com' in src or 'cloudinary' in src or 'imgix' in src or '.jpg' in src or '.png' in src:
                        all_images.append(src)
        
        # Also check for background images
        for elem in soup.find_all(style=True):
            style = elem.get('style', '')
            bg_matches = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
            for bg_url in bg_matches:
                if bg_url.startswith('//'):
                    bg_url = 'https:' + bg_url
                elif bg_url.startswith('/'):
                    bg_url = 'https://tfc.com' + bg_url
                
                if bg_url.startswith('https://') and 'tfc' in bg_url.lower():
                    all_images.append(bg_url)
        
        # Remove duplicates
        seen = set()
        unique_images = []
        for img in all_images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        print(f"✅ Found {len(unique_images)} total images")
        
        if len(unique_images) > 0:
            print(f"\n📸 Sample images found:\n")
            for i, img in enumerate(unique_images[:8], 1):
                print(f"   {i}. {img[:90]}...")
        
        # Extract unit details from page text
        text_content = soup.get_text()
        
        # Extract rent
        rent = 0.0
        rent_match = re.search(r'\$([0-9,]+)', text_content)
        if rent_match:
            rent = float(rent_match.group(1).replace(',', ''))
        
        # Extract bedrooms
        bedrooms = 0
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
        
        print(f"\n📋 Detected unit details:")
        print(f"   Bedrooms: {bedrooms}")
        print(f"   Bathrooms: {bathrooms}")
        print(f"   Rent: ${rent}/month")
        
        # Update database
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Check if 4610 Center Boulevard building exists
        building = await db.buildings.find_one({'name': '4610 Center Boulevard'}, {'_id': 0})
        
        if not building:
            print("\n⚠️ 4610 Center Boulevard building not found in database!")
            print("🏗️ Creating new building entry...")
            
            # Create building entry
            building_id = str(uuid4())
            building = {
                'id': building_id,
                'name': '4610 Center Boulevard',
                'address': '4610 Center Boulevard',
                'city': 'Long Island City',
                'state': 'NY',
                'zip_code': '11109',
                'neighborhood': 'Long Island City',
                'source_url': 'https://tfc.com/long-island-city-lic/luxury-no-fee-apartments/4610-center-blvd',
                'last_crawled': datetime.now(timezone.utc).isoformat()
            }
            
            await db.buildings.insert_one(building)
            print(f"✅ Created 4610 Center Boulevard building (ID: {building_id})")
        else:
            building_id = building['id']
            print(f"\n✅ Found 4610 Center Boulevard building (ID: {building_id})")
        
        # Create unit 1920
        print(f"\n🏢 Creating Unit 1920...")
        
        unit_id = str(uuid4())
        unit = {
            'id': unit_id,
            'building_id': building_id,
            'unit_number': '1920',
            'rent': rent if rent > 0 else 3500.0,  # Use detected or default
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'square_feet': None,
            'available_date': 'Immediate',
            'amenities': [
                'No Fee',
                'Doorman',
                'Elevator',
                'Fitness Center',
                'Roof Deck',
                'Pool',
                'Concierge'
            ],
            'description': 'Luxury apartment in Long Island City with Manhattan views',
            'images': unique_images[:15] if unique_images else [],
            'is_available': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.units.insert_one(unit)
        print(f"✅ Created unit 1920 with {len(unit['images'])} images!")
        
        print(f"\n📊 Unit Details:")
        print(f"   - Unit Number: 1920")
        print(f"   - Rent: ${unit['rent']}")
        print(f"   - Bedrooms: {unit['bedrooms']}")
        print(f"   - Bathrooms: {unit['bathrooms']}")
        print(f"   - Building: 4610 Center Boulevard")
        print(f"   - Location: Long Island City, Queens")
        print(f"   - Images: {len(unit['images'])}")

if __name__ == "__main__":
    asyncio.run(main())
