"""Scrape Hoyt & Horn listings from Rose NYC"""
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
    # Scrape the building page
    url = 'https://www.rosenyc.com/rentals/hoyt-and-horn/'
    
    print(f"🔍 Scraping: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(5000)
        
        content = await page.content()
        
        # Also extract title
        title = await page.title()
        print(f"Page title: {title}")
        
        await browser.close()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find building images
        all_images = []
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
            if src:
                # Clean up URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.rosenyc.com' + src
                
                # Filter out logos, icons
                if src.startswith('https://') and not any(x in src.lower() for x in ['logo', 'icon', 'favicon', 'sprite']):
                    # Include images from Rose NYC CDN
                    if 'rosenyc' in src or 'cloudinary' in src or 'imgix' in src or '.jpg' in src or '.png' in src:
                        all_images.append(src)
        
        # Also check for background images
        for elem in soup.find_all(style=True):
            style = elem.get('style', '')
            bg_matches = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
            for bg_url in bg_matches:
                if bg_url.startswith('//'):
                    bg_url = 'https:' + bg_url
                elif bg_url.startswith('/'):
                    bg_url = 'https://www.rosenyc.com' + bg_url
                
                if bg_url.startswith('https://') and 'rosenyc' in bg_url:
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
        
        # Look for unit listings in the page
        text_content = soup.get_text()
        
        # Try to find available units info
        print(f"\n🔍 Analyzing page for unit listings...")
        
        # Look for common patterns: bedroom counts, prices, square footage
        unit_data_found = []
        
        # Search for price patterns
        prices = re.findall(r'\$([0-9,]+)', text_content)
        print(f"   Found {len(prices)} potential rent prices")
        
        # Search for bedroom info
        bedrooms_found = re.findall(r'(\d+)\s*(?:bed|br|bedroom)', text_content, re.I)
        studios_found = re.findall(r'studio', text_content, re.I)
        print(f"   Found {len(bedrooms_found)} bedroom mentions, {len(studios_found)} studio mentions")
        
        # Update database
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Check if Hoyt Horn building exists
        building = await db.buildings.find_one({'name': 'Hoyt Horn'}, {'_id': 0})
        
        if not building:
            print("\n⚠️ Hoyt Horn building not found in database!")
            print("🏗️ Creating new building entry...")
            
            # Create building entry
            building_id = str(uuid4())
            building = {
                'id': building_id,
                'name': 'Hoyt Horn',
                'address': '315 Hoyt Street',
                'city': 'Brooklyn',
                'state': 'NY',
                'zip_code': '11231',
                'neighborhood': 'Carroll Gardens',
                'source_url': 'https://www.rosenyc.com/rentals/hoyt-and-horn/',
                'last_crawled': datetime.now(timezone.utc).isoformat()
            }
            
            await db.buildings.insert_one(building)
            print(f"✅ Created Hoyt Horn building (ID: {building_id})")
        else:
            building_id = building['id']
            print(f"\n✅ Found Hoyt Horn building (ID: {building_id})")
        
        # Since the page structure may not show specific units, create a sample unit with building images
        print(f"\n📝 Creating sample unit with building images...")
        
        # Create a unit entry (using building images)
        unit_id = str(uuid4())
        unit_number = f"HOYT-{str(uuid4())[:8].upper()}"
        
        unit = {
            'id': unit_id,
            'building_id': building_id,
            'unit_number': unit_number,
            'rent': 3500.0,  # Placeholder - will need to update with actual rent
            'bedrooms': 1,
            'bathrooms': 1.0,
            'square_feet': None,
            'available_date': 'Immediate',
            'amenities': [],
            'description': 'Contact for details',
            'images': unique_images[:12] if unique_images else [],  # Use first 12 images
            'is_available': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.units.insert_one(unit)
        print(f"✅ Created sample unit {unit_number} with {len(unit['images'])} images")
        
        print(f"\n📊 Building Details:")
        print(f"   - Building: Hoyt Horn")
        print(f"   - Address: 315 Hoyt Street")
        print(f"   - Location: Carroll Gardens, Brooklyn")
        print(f"   - Sample Unit: {unit_number}")
        print(f"   - Images: {len(unit['images'])}")
        print(f"\n⚠️  Note: This is a placeholder unit. You may need to:")
        print(f"   1. Visit the Rose NYC site to get specific unit details")
        print(f"   2. Update rent price and bedroom/bathroom counts")
        print(f"   3. Add more specific units if available")

if __name__ == "__main__":
    asyncio.run(main())
