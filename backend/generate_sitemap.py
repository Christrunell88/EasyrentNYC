"""
Generate XML Sitemap for NoFeesApts.com
Run this periodically to update the sitemap with current listings
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

async def generate_sitemap():
    """Generate sitemap.xml with all public URLs"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    base_url = "https://rent-without-fee.preview.emergentagent.com"
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get all units
    units = await db.units.find({}, {"_id": 0, "id": 1}).to_list(1000)
    
    # Get all buildings for location pages
    buildings = await db.buildings.find({}, {"_id": 0, "city": 1, "neighborhood": 1}).to_list(1000)
    
    # Extract unique cities and neighborhoods
    cities = set()
    neighborhoods = set()
    for building in buildings:
        if building.get('city'):
            cities.add(building['city'].lower().replace(' ', '-'))
        if building.get('neighborhood'):
            neighborhoods.add(building['neighborhood'].lower().replace(' ', '-'))
    
    client.close()
    
    # Build sitemap XML
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Static pages
    static_pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': '/dashboard', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/auth', 'priority': '0.5', 'changefreq': 'monthly'},
        {'url': '/favorites', 'priority': '0.6', 'changefreq': 'weekly'},
    ]
    
    # Key location pages (always include these)
    key_locations = [
        'manhattan', 'brooklyn', 'queens', 'long-island-city', 'williamsburg',
        'jersey-city', 'hoboken', 'harrison', 'weehawken', 'bronx'
    ]
    
    for page in static_pages:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}{page["url"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{today}</lastmod>\n'
        sitemap_xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    
    # Unit detail pages
    for unit in units:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}/unit/{unit["id"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{today}</lastmod>\n'
        sitemap_xml += '    <changefreq>weekly</changefreq>\n'
        sitemap_xml += '    <priority>0.8</priority>\n'
        sitemap_xml += '  </url>\n'
    
    # Location pages - Key locations (high priority)
    for location in key_locations:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}/location/{location}</loc>\n'
        sitemap_xml += f'    <lastmod>{today}</lastmod>\n'
        sitemap_xml += '    <changefreq>daily</changefreq>\n'
        sitemap_xml += '    <priority>0.9</priority>\n'
        sitemap_xml += '  </url>\n'
    
    # Dynamic location pages from database
    all_locations = cities.union(neighborhoods) - set(key_locations)
    for location in all_locations:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}/location/{location}</loc>\n'
        sitemap_xml += f'    <lastmod>{today}</lastmod>\n'
        sitemap_xml += '    <changefreq>weekly</changefreq>\n'
        sitemap_xml += '    <priority>0.7</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    # Save to frontend public directory
    sitemap_path = '/app/frontend/public/sitemap.xml'
    with open(sitemap_path, 'w') as f:
        f.write(sitemap_xml)
    
    print(f"✅ Sitemap generated successfully!")
    print(f"📊 Statistics:")
    print(f"   - Static pages: {len(static_pages)}")
    print(f"   - Unit pages: {len(units)}")
    print(f"   - Key location pages: {len(key_locations)}")
    print(f"   - Dynamic location pages: {len(cities.union(neighborhoods) - set(key_locations))}")
    print(f"   - Total URLs: {len(static_pages) + len(units) + len(key_locations) + len(cities.union(neighborhoods) - set(key_locations))}")
    print(f"📁 Saved to: {sitemap_path}")

if __name__ == "__main__":
    asyncio.run(generate_sitemap())
