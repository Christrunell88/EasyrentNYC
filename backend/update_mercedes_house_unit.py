"""Scrape and update images for Mercedes House unit 1617"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def main():
    # Scrape the unit page
    url = 'https://www.mercedeshouseny.com/one-bed?unit=1617'
    
    print(f"🔍 Scraping: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(5000)  # Wait for images to load
        
        content = await page.content()
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
                    src = 'https://www.mercedeshouseny.com' + src
                
                # Filter out logos, icons, tiny images
                if src.startswith('https://') and not any(x in src.lower() for x in ['logo', 'icon', 'favicon', 'sprite']):
                    # Include images from their CDN or site
                    if 'mercedeshouseny' in src or 'cloudinary' in src or 'imgix' in src:
                        all_images.append(src)
        
        # Also check for background images in style attributes
        for elem in soup.find_all(style=True):
            style = elem.get('style', '')
            import re
            bg_matches = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
            for bg_url in bg_matches:
                if bg_url.startswith('//'):
                    bg_url = 'https:' + bg_url
                elif bg_url.startswith('/'):
                    bg_url = 'https://www.mercedeshouseny.com' + bg_url
                
                if bg_url.startswith('https://') and 'mercedes' in bg_url.lower():
                    all_images.append(bg_url)
        
        # Remove duplicates
        seen = set()
        unique_images = []
        for img in all_images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        print(f"✅ Found {len(unique_images)} total images")
        print(f"\n📸 Images to store:\n")
        
        # Display the images we're storing
        for i, img in enumerate(unique_images[:12], 1):
            print(f"   {i}. {img[:90]}...")
        
        if len(unique_images) > 12:
            print(f"   ... and {len(unique_images) - 12} more images")
        
        # Update database
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Find Mercedes House building first
        building = await db.buildings.find_one({'name': 'Mercedes House'}, {'_id': 0})
        
        if not building:
            print("\n❌ Mercedes House building not found in database!")
            return
        
        # Find unit 1617
        unit = await db.units.find_one({
            'building_id': building['id'],
            'unit_number': '1617'
        }, {'_id': 0})
        
        if not unit:
            # Try to find any 1BR unit in Mercedes House
            print(f"\n⚠️ Unit 1617 not found. Searching for 1BR units in Mercedes House...")
            units = await db.units.find({
                'building_id': building['id'],
                'bedrooms': 1
            }, {'_id': 0}).to_list(10)
            
            if units:
                print(f"\nFound {len(units)} 1BR units in Mercedes House:")
                for u in units:
                    print(f"   - Unit {u['unit_number']}: ${u['rent']}")
                
                # Use the first 1BR unit
                unit = units[0]
                print(f"\n📍 Using unit: {unit['unit_number']}")
            else:
                print("\n❌ No 1BR units found in Mercedes House!")
                return
        
        print(f"\n🔄 Updating unit {unit['unit_number']} in database...")
        
        # Update the unit with real images
        result = await db.units.update_one(
            {'id': unit['id']},
            {
                '$set': {
                    'images': unique_images,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated unit {unit['unit_number']} with {len(unique_images)} images!")
            print(f"\n📊 Unit Details:")
            print(f"   - Unit Number: {unit['unit_number']}")
            print(f"   - Rent: ${unit['rent']}")
            print(f"   - Bedrooms: {unit['bedrooms']}")
            print(f"   - Bathrooms: {unit['bathrooms']}")
            print(f"   - Building: Mercedes House")
        else:
            print("⚠️ No changes made (images may already be up to date)")

if __name__ == "__main__":
    asyncio.run(main())
