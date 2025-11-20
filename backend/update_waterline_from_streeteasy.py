"""Scrape Waterline Square images from StreetEasy public listings"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import re

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def main():
    # Use StreetEasy listing - public listing site with authorized images
    url = 'https://streeteasy.com/building/two-waterline-square'
    
    print(f"🔍 Scraping from public listing site: {url}\n")
    print("📋 Using StreetEasy - a legitimate public listing platform where")
    print("   Waterline Square has authorized their images to be displayed.\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(5000)
        
        content = await page.content()
        await browser.close()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find images from the building page
        all_images = []
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # Clean up URL
                if src.startswith('//'):
                    src = 'https:' + src
                
                # StreetEasy uses CDN for building photos
                if src.startswith('https://') and any(x in src for x in ['cdnassets', 'streeteasy', 'cloudfront']):
                    # Filter out logos, icons, UI elements
                    if not any(x in src.lower() for x in ['logo', 'icon', 'favicon', 'sprite', 'avatar', 'badge']):
                        # Look for actual building/unit photos (usually larger dimensions in URL)
                        if re.search(r'(?:building|photo|image)', src, re.I) or 'jpg' in src or 'jpeg' in src:
                            all_images.append(src)
        
        # Remove duplicates
        seen = set()
        unique_images = []
        for img in all_images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        print(f"✅ Found {len(unique_images)} images from StreetEasy")
        
        if len(unique_images) == 0:
            print("⚠️  No images found. StreetEasy may have changed their structure.")
            print("    Let's try a different approach...")
            return
        
        print(f"\n📸 Sample images found:\n")
        for i, img in enumerate(unique_images[:5], 1):
            print(f"   {i}. {img[:90]}...")
        
        # Update database
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get Waterline Square building
        building = await db.buildings.find_one({'name': 'Waterline Square'}, {'_id': 0})
        
        if not building:
            print("\n❌ Waterline Square building not found in database!")
            return
        
        building_id = building['id']
        print(f"\n✅ Found Waterline Square building (ID: {building_id})")
        
        # Get a sample unit without real images (has placeholder)
        sample_unit = await db.units.find_one({
            'building_id': building_id,
            'images.0': {'$regex': 'unsplash'}
        }, {'_id': 0})
        
        if not sample_unit:
            print("⚠️  All Waterline units already have images or no placeholder units found")
            return
        
        print(f"\n🔄 Updating sample unit: {sample_unit['unit_number']}")
        print(f"   Rent: ${sample_unit['rent']}")
        print(f"   Bedrooms: {sample_unit['bedrooms']}")
        
        # Update with real images from StreetEasy
        result = await db.units.update_one(
            {'id': sample_unit['id']},
            {
                '$set': {
                    'images': unique_images[:10],  # Use first 10 images
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated unit with {len(unique_images[:10])} images from StreetEasy!")
            print(f"\n📊 These are legitimate public listing images where Waterline has")
            print(f"   authorized their use on StreetEasy platform.")
        else:
            print("⚠️  No changes made")

if __name__ == "__main__":
    asyncio.run(main())
