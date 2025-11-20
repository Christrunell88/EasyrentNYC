"""Add Meridia Linden 1001 from Apartments.com data"""
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
    # Scrape the Apartments.com listing
    url = 'https://www.apartments.com/meridia-linden-1001-linden-nj/rrjw213/'
    
    print(f"🔍 Scraping: {url}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            
            content = await page.content()
            
            # Look for images
            images = await page.query_selector_all('img[src*=".jpg"], img[src*=".jpeg"], img[src*=".png"]')
            
            image_urls = []
            for img in images:
                src = await img.get_attribute('src')
                if src and 'apartments.com' in src and not any(x in src.lower() for x in ['logo', 'icon', 'sprite', 'avatar']):
                    if src.startswith('//'):
                        src = 'https:' + src
                    image_urls.append(src)
            
            # Remove duplicates
            image_urls = list(dict.fromkeys(image_urls))
            
            print(f"✅ Found {len(image_urls)} images")
            
            if image_urls:
                for i, img in enumerate(image_urls[:5], 1):
                    print(f"   {i}. {img[:80]}...")
            
            await browser.close()
            
        except Exception as e:
            print(f"Error scraping: {e}")
            await browser.close()
            image_urls = []
    
    # Update database
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Create building
    building_id = str(uuid4())
    building = {
        'id': building_id,
        'name': 'Meridia Linden 1001',
        'address': '1001 Lower Road',
        'city': 'Linden',
        'state': 'NJ',
        'zip_code': '07036',
        'neighborhood': 'Linden',
        'source_url': url,
        'last_crawled': datetime.now(timezone.utc).isoformat()
    }
    
    await db.buildings.insert_one(building)
    print(f"\n✅ Created Meridia Linden 1001 building")
    print(f"   Address: 1001 Lower Road, Linden, NJ 07036")
    
    # If no images scraped, use a placeholder approach
    if not image_urls:
        print("\n⚠️  No images scraped from Apartments.com (protected site)")
        print("   Using placeholder - you can add real images later")
        # Use a generic placeholder
        image_urls = ["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800"]
    
    # Create units based on Apartments.com data
    amenities = [
        'Pet-Friendly',
        'Fitness Center',
        'Kitchen',
        'Heat Included',
        'Oven',
        'Tub/Shower'
    ]
    
    units_data = [
        {'unit_number': '1BR-A', 'bedrooms': 1, 'bathrooms': 1.0, 'rent': 1895.0},
        {'unit_number': '1BR-B', 'bedrooms': 1, 'bathrooms': 1.0, 'rent': 1995.0},
        {'unit_number': '2BR-A', 'bedrooms': 2, 'bathrooms': 1.0, 'rent': 2495.0},
        {'unit_number': '2BR-B', 'bedrooms': 2, 'bathrooms': 2.0, 'rent': 2595.0},
    ]
    
    print(f"\n🏢 Adding {len(units_data)} units...\n")
    
    for unit_data in units_data:
        unit = {
            'id': str(uuid4()),
            'building_id': building_id,
            'unit_number': unit_data['unit_number'],
            'rent': unit_data['rent'],
            'bedrooms': unit_data['bedrooms'],
            'bathrooms': unit_data['bathrooms'],
            'square_feet': None,
            'available_date': 'Immediate',
            'amenities': amenities,
            'description': '1 Month Free Special',
            'images': image_urls[:8] if image_urls else [],
            'is_available': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.units.insert_one(unit)
        bed_type = f"{unit_data['bedrooms']}BR"
        print(f"✅ Added Unit {unit_data['unit_number']}: {bed_type}, {unit_data['bathrooms']}BA, ${unit_data['rent']}/month")
    
    print(f"\n📊 Meridia Linden 1001 Summary:")
    print(f"   - Building: Meridia Linden 1001")
    print(f"   - Location: 1001 Lower Road, Linden, NJ 07036")
    print(f"   - Units: {len(units_data)} (1BR & 2BR)")
    print(f"   - Rent Range: $1,895 - $2,595/month")
    print(f"   - Special: 1 Month Free")
    print(f"   - Amenities: {len(amenities)}")

if __name__ == "__main__":
    asyncio.run(main())
