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
    
    base_url = "https://nofeesapts.com"
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get all units with more details for better sitemap
    units = await db.units.find(
        {"is_available": True}, 
        {"_id": 0, "id": 1, "updated_at": 1, "building": 1, "images": 1}
    ).to_list(2000)
    
    # Get all buildings for location pages
    buildings = await db.buildings.find({}, {"_id": 0, "city": 1, "neighborhood": 1, "state": 1}).to_list(1000)
    
    # Extract unique cities and neighborhoods
    cities = set()
    neighborhoods = set()
    states = set()
    for building in buildings:
        if building.get('city'):
            cities.add(building['city'].lower().replace(' ', '-'))
        if building.get('neighborhood'):
            neighborhoods.add(building['neighborhood'].lower().replace(' ', '-'))
        if building.get('state'):
            states.add(building['state'].lower())
    
    client.close()
    
    # Build sitemap XML
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    sitemap_xml += '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
    
    # Static pages with high priority
    static_pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': '/dashboard', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/fee-free-finds', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/blog', 'priority': '0.8', 'changefreq': 'weekly'},
        {'url': '/faq', 'priority': '0.7', 'changefreq': 'monthly'},
        {'url': '/auth', 'priority': '0.5', 'changefreq': 'monthly'},
    ]
    
    # Blog posts (hardcoded slugs for now)
    blog_posts = [
        '/blog/guide-to-no-fee-apartments',
        '/blog/best-neighborhoods',
        '/blog/apartment-checklist',
        '/blog/ultimate-guide-no-fee-apartments-nyc-2025',
        '/blog/hidden-costs-nyc-rentals',
        '/blog/best-neighborhoods-young-professionals-2025',
        '/blog/no-fee-apartments-jersey-city-2025',
        '/blog/first-apartment-nyc-checklist',
        '/blog/nyc-rental-market-trends-2025',
    ]
    
    # Key location pages (always include these with high priority)
    key_locations = [
        'manhattan', 'brooklyn', 'queens', 'long-island-city', 'williamsburg',
        'jersey-city', 'hoboken', 'harrison', 'weehawken', 'bronx',
        'upper-west-side', 'upper-east-side', 'downtown-brooklyn', 'astoria',
        'financial-district', 'tribeca', 'dumbo', 'greenpoint', 'park-slope'
    ]
    
    for page in static_pages:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}{page["url"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{today}</lastmod>\n'
        sitemap_xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    
    # Blog posts
    for post_url in blog_posts:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}{post_url}</loc>\n'
        sitemap_xml += f'    <lastmod>{today}</lastmod>\n'
        sitemap_xml += '    <changefreq>monthly</changefreq>\n'
        sitemap_xml += '    <priority>0.7</priority>\n'
        sitemap_xml += '  </url>\n'
    
    # Unit detail pages with images for rich results
    for unit in units:
        unit_id = unit.get("id")
        last_mod = unit.get("updated_at", today)
        if isinstance(last_mod, str) and 'T' in last_mod:
            last_mod = last_mod.split('T')[0]
        else:
            last_mod = today
            
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}/unit/{unit_id}</loc>\n'
        sitemap_xml += f'    <lastmod>{last_mod}</lastmod>\n'
        sitemap_xml += '    <changefreq>weekly</changefreq>\n'
        sitemap_xml += '    <priority>0.8</priority>\n'
        
        # Add images for image sitemap
        images = unit.get("images", [])
        for idx, img_url in enumerate(images[:5]):  # Limit to 5 images per page
            if img_url and img_url.startswith('http'):
                sitemap_xml += '    <image:image>\n'
                sitemap_xml += f'      <image:loc>{img_url}</image:loc>\n'
                sitemap_xml += f'      <image:title>Apartment photo {idx + 1}</image:title>\n'
                sitemap_xml += '    </image:image>\n'
        
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
        if location and len(location) > 2:  # Skip very short names
            sitemap_xml += '  <url>\n'
            sitemap_xml += f'    <loc>{base_url}/location/{location}</loc>\n'
            sitemap_xml += f'    <lastmod>{today}</lastmod>\n'
            sitemap_xml += '    <changefreq>weekly</changefreq>\n'
            sitemap_xml += '    <priority>0.7</priority>\n'
            sitemap_xml += '  </url>\n'
    
    # State-level pages for NJ and PA
    for state in ['nj', 'pa', 'ny']:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}/location/{state}</loc>\n'
        sitemap_xml += f'    <lastmod>{today}</lastmod>\n'
        sitemap_xml += '    <changefreq>daily</changefreq>\n'
        sitemap_xml += '    <priority>0.85</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    # Save to frontend public directory
    sitemap_path = '/app/frontend/public/sitemap.xml'
    with open(sitemap_path, 'w') as f:
        f.write(sitemap_xml)
    
    total_urls = len(static_pages) + len(blog_posts) + len(units) + len(key_locations) + len(all_locations) + 3
    
    print(f"✅ Sitemap generated successfully!")
    print(f"📊 Statistics:")
    print(f"   - Static pages: {len(static_pages)}")
    print(f"   - Blog posts: {len(blog_posts)}")
    print(f"   - Unit pages: {len(units)}")
    print(f"   - Key location pages: {len(key_locations)}")
    print(f"   - Dynamic location pages: {len(all_locations)}")
    print(f"   - State pages: 3")
    print(f"   - Total URLs: {total_urls}")
    print(f"📁 Saved to: {sitemap_path}")
    
    return sitemap_xml

if __name__ == "__main__":
    asyncio.run(generate_sitemap())
