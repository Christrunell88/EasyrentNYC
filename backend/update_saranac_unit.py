"""Scrape and update images for The Saranac unit NNMXGNYA"""
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
    url = 'https://manhattanskyline.com/buildings/tribeca/saranac/apartment-nnmxgnya'
    
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
                
                # Filter out logos, icons
                if src.startswith('https://') and not any(x in src.lower() for x in ['logo', 'icon', 'favicon']):
                    if 'storage' in src:
                        all_images.append(src)
        
        # Remove duplicates
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
        final_images = unit_images + building_images[:3]  # Unit images + max 3 building images
        
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
        
        # Find The Saranac unit NNMXGNYA
        unit = await db.units.find_one({'unit_number': 'NNMXGNYA'}, {'_id': 0})
        
        if not unit:
            print("\n❌ Unit NNMXGNYA not found in database!")
            return
        
        print(f"\n🔄 Updating unit NNMXGNYA in database...")
        
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
            print(f"✅ Successfully updated unit NNMXGNYA with {len(final_images)} images!")
            print(f"\n📊 Unit Details:")
            print(f"   - Unit Number: {unit['unit_number']}")
            print(f"   - Rent: ${unit['rent']}")
            print(f"   - Bedrooms: {unit['bedrooms']}")
            print(f"   - Bathrooms: {unit['bathrooms']}")
            print(f"   - Building: The Saranac")
        else:
            print("⚠️ No changes made (images may already be up to date)")

if __name__ == "__main__":
    asyncio.run(main())
