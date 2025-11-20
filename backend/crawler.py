"""Web crawler for apartment listings"""
import logging
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def crawl_fortysixfifty(url: str) -> List[Dict[str, Any]]:
    """Crawl fortysixfifty.com - handles iframe-based availability widget"""
    units = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for iframe to load
            await page.wait_for_timeout(3000)
            
            # Look for rosenyc iframe (common availability widget)
            frames = page.frames
            iframe_content = None
            for frame in frames:
                if 'rosenyc.com' in frame.url:
                    logger.info(f"Found availability iframe: {frame.url}")
                    iframe_content = await frame.content()
                    break
            
            # Use iframe content if found, otherwise use main page
            content = iframe_content if iframe_content else await page.content()
            await browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Parse table-based availability widget (rosenyc.com format)
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # Check if first row has availability headers
                header_row = rows[0]
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                
                # Skip if not an availability table
                if not any(h in headers for h in ['unit', 'rent', 'bedroom']):
                    continue
                
                # Parse data rows
                for row in rows[1:]:
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 4:
                            continue
                        
                        unit_data = {
                            'unit_number': '',
                            'rent': 0.0,
                            'bedrooms': 0,
                            'bathrooms': 1.0,
                            'square_feet': None,
                            'images': [],
                            'amenities': [],
                            'description': '',
                            'available_date': 'Immediate'
                        }
                        
                        # Map cells to data based on headers
                        for idx, cell in enumerate(cells):
                            text = cell.get_text(strip=True)
                            header = headers[idx] if idx < len(headers) else ''
                            
                            # Unit number
                            if 'unit' in header or idx == 0:
                                if text and text.isdigit() or re.match(r'^[A-Z0-9-]+$', text):
                                    unit_data['unit_number'] = text
                            
                            # Rent
                            if 'rent' in header or '$' in text:
                                rent_match = re.search(r'\$([0-9,]+)', text)
                                if rent_match:
                                    unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                            
                            # Bedrooms
                            if 'bedroom' in header or 'br' in header:
                                if 'studio' in text.lower():
                                    unit_data['bedrooms'] = 0
                                else:
                                    bed_match = re.search(r'(\d+)', text)
                                    if bed_match:
                                        unit_data['bedrooms'] = int(bed_match.group(1))
                            
                            # Bathrooms
                            if 'bathroom' in header or 'ba' in header:
                                bath_match = re.search(r'(\d+(?:\.\d+)?)', text)
                                if bath_match:
                                    unit_data['bathrooms'] = float(bath_match.group(1))
                            
                            # Square feet
                            if 'sq' in header or 'sq.' in text.lower():
                                sqft_match = re.search(r'(\d+)', text)
                                if sqft_match:
                                    unit_data['square_feet'] = int(sqft_match.group(1))
                            
                            # Availability date
                            if 'availability' in header:
                                if text and text != 'Immediate':
                                    unit_data['available_date'] = text
                        
                        # Only add if we have minimum required data
                        if unit_data['unit_number'] and unit_data['rent'] > 0:
                            units.append(unit_data)
                    
                    except Exception as e:
                        logger.error(f"Error parsing row: {e}")
                        continue
    
    except Exception as e:
        logger.error(f"Error crawling fortysixfifty: {e}")
    
    return units

async def crawl_mercedes_house(url: str) -> List[Dict[str, Any]]:
    """Crawl mercedeshouseny.com - custom parser for their format"""
    units = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for dynamic content to load
            await page.wait_for_timeout(5000)
            
            content = await page.content()
            await browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            all_text = soup.get_text()
            
            # Mercedes House uses pattern: "Bedroom Type#UnitNumber|$Price"
            # Examples: "Studio#2004|$3817", "1 Bedroom#1617|$4331"
            pattern = re.findall(
                r'(Studio|[\d]+\s*Bedroom[s]?)[^\d#]*#?(\d+)[^\d\$]*\$([0-9,]+)',
                all_text,
                re.I
            )
            
            for match in pattern:
                try:
                    bedroom_type = match[0].strip()
                    unit_number = match[1].strip()
                    rent = float(match[2].replace(',', ''))
                    
                    # Parse bedroom count
                    if 'studio' in bedroom_type.lower():
                        bedrooms = 0
                    else:
                        bed_match = re.search(r'(\d+)', bedroom_type)
                        bedrooms = int(bed_match.group(1)) if bed_match else 1
                    
                    unit_data = {
                        'unit_number': unit_number,
                        'rent': rent,
                        'bedrooms': bedrooms,
                        'bathrooms': 1.0,  # Default, not specified
                        'square_feet': None,
                        'images': [],
                        'amenities': [],
                        'description': f"{bedroom_type} apartment",
                        'available_date': 'Immediate'
                    }
                    
                    units.append(unit_data)
                
                except Exception as e:
                    logger.error(f"Error parsing Mercedes unit: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Error crawling Mercedes House: {e}")
    
    return units

async def crawl_twotrees(url: str) -> List[Dict[str, Any]]:
    """Crawl twotreesny.com"""
    units = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            content = await page.content()
            await browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            listing_containers = soup.find_all(['div', 'article'], class_=re.compile(r'unit|apartment|listing|availability', re.I))
            
            for container in listing_containers:
                try:
                    unit_data = {
                        'unit_number': '',
                        'rent': 0.0,
                        'bedrooms': 0,
                        'bathrooms': 1.0,
                        'images': [],
                        'amenities': [],
                        'description': ''
                    }
                    
                    text = container.get_text(separator=' ', strip=True)
                    
                    rent_match = re.search(r'\$([0-9,]+)', text)
                    if rent_match:
                        unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                    
                    bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', text, re.I)
                    if bed_match:
                        unit_data['bedrooms'] = int(bed_match.group(1))
                    elif re.search(r'studio', text, re.I):
                        unit_data['bedrooms'] = 0
                    
                    bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', text, re.I)
                    if bath_match:
                        unit_data['bathrooms'] = float(bath_match.group(1))
                    
                    unit_match = re.search(r'(?:unit|apt|#)\s*([A-Z0-9-]+)', text, re.I)
                    if unit_match:
                        unit_data['unit_number'] = unit_match.group(1)
                    
                    images = container.find_all('img')
                    for img in images:
                        src = img.get('src') or img.get('data-src')
                        if src and 'http' in src:
                            unit_data['images'].append(src)
                    
                    if unit_data['rent'] > 0:
                        units.append(unit_data)
                
                except Exception as e:
                    logger.error(f"Error parsing unit: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Error crawling twotrees: {e}")
    
    return units

async def crawl_harrison_yards(url: str) -> List[Dict[str, Any]]:
    """Crawl harrisonyards.com - uses RealPage/LeaseStar widget"""
    units = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for the floor plan widget to fully load
            await page.wait_for_timeout(8000)
            
            # Wait for specific floor plan elements to be visible
            try:
                await page.wait_for_selector('.rpfp-card, .rpfp-card-details', timeout=5000)
            except:
                logger.warning("Floor plan cards did not load in time, proceeding anyway")
            
            content = await page.content()
            await browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all floor plan cards - RealPage uses specific structure
            floor_plan_cards = soup.find_all('div', class_=re.compile(r'rpfp-card', re.I))
            
            logger.info(f"Found {len(floor_plan_cards)} floor plan cards")
            
            for card in floor_plan_cards:
                try:
                    unit_data = {
                        'unit_number': '',
                        'rent': 0.0,
                        'bedrooms': 0,
                        'bathrooms': 1.0,
                        'square_feet': None,
                        'images': [],
                        'amenities': [],
                        'description': '',
                        'available_date': 'Immediate'
                    }
                    
                    text = card.get_text(separator=' ', strip=True)
                    
                    # Extract rent - look for price in specific elements
                    price_elem = card.find(['span', 'div'], class_=re.compile(r'price|rent|rate', re.I))
                    if price_elem:
                        rent_match = re.search(r'\$([0-9,]+)', price_elem.get_text())
                        if rent_match:
                            unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                    else:
                        # Fallback to text search
                        rent_match = re.search(r'\$([0-9,]+)', text)
                        if rent_match:
                            unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                    
                    # Extract bedrooms
                    bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', text, re.I)
                    if bed_match:
                        unit_data['bedrooms'] = int(bed_match.group(1))
                    elif re.search(r'studio', text, re.I):
                        unit_data['bedrooms'] = 0
                    
                    # Extract bathrooms
                    bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', text, re.I)
                    if bath_match:
                        unit_data['bathrooms'] = float(bath_match.group(1))
                    
                    # Extract square feet
                    sqft_match = re.search(r'(\d+)\s*(?:sq|sqft|sf)', text, re.I)
                    if sqft_match:
                        unit_data['square_feet'] = int(sqft_match.group(1))
                    
                    # Extract unit number - look in data attributes or specific elements
                    unit_num_elem = card.find(['span', 'div'], class_=re.compile(r'unit|name|title', re.I))
                    if unit_num_elem:
                        unit_text = unit_num_elem.get_text(strip=True)
                        unit_match = re.search(r'([A-Z0-9-]+)', unit_text)
                        if unit_match:
                            unit_data['unit_number'] = unit_match.group(1)
                    
                    if not unit_data['unit_number']:
                        # Generate unit number based on bedroom count
                        bed_type = "Studio" if unit_data['bedrooms'] == 0 else f"{unit_data['bedrooms']}BR"
                        unit_data['unit_number'] = f"{bed_type}-{len(units)+1}"
                    
                    # Extract images - look in multiple places
                    # 1. Direct img tags
                    images = card.find_all('img')
                    for img in images:
                        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                        if src:
                            # Clean up URL
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/') and not src.startswith('http'):
                                src = 'https://harrisonyards.com' + src
                            
                            # Include images from LeaseStar API or other valid sources, exclude icons/logos
                            if src.startswith('https://') and not any(x in src.lower() for x in ['icon', 'logo', 'spinner', 'browser']):
                                if src not in unit_data['images']:
                                    unit_data['images'].append(src)
                    
                    # 2. Check for background images in style attributes
                    for elem in card.find_all(style=re.compile(r'background-image')):
                        style = elem.get('style', '')
                        bg_match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                        if bg_match:
                            src = bg_match.group(1)
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/') and not src.startswith('http'):
                                src = 'https://harrisonyards.com' + src
                            
                            if src.startswith('https://') and 'myleasestar.com' in src:
                                if src not in unit_data['images']:
                                    unit_data['images'].append(src)
                    
                    # Only add if we have minimum data
                    if unit_data['rent'] > 0:
                        units.append(unit_data)
                        logger.info(f"Found Harrison Yards unit: {unit_data['unit_number']} - ${unit_data['rent']} - {len(unit_data['images'])} images")
                
                except Exception as e:
                    logger.error(f"Error parsing Harrison Yards card: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Error crawling Harrison Yards: {e}")
    
    return units

async def crawl_generic_site(url: str) -> List[Dict[str, Any]]:
    """Generic crawler for other sites - checks tables first, then divs"""
    units = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for dynamic content
            await page.wait_for_timeout(5000)
            
            # Check for iframes first
            frames = page.frames
            iframe_content = None
            for frame in frames:
                if frame.url != 'about:blank' and 'google' not in frame.url and frame.url != url:
                    try:
                        iframe_content = await frame.content()
                        logger.info(f"Using iframe content from: {frame.url}")
                        break
                    except:
                        continue
            
            content = iframe_content if iframe_content else await page.content()
            await browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # First try table-based parsing
            tables = soup.find_all('table')
            if tables:
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) < 2:
                        continue
                    
                    header_row = rows[0]
                    headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                    
                    if not any(h in headers for h in ['unit', 'rent', 'bedroom', 'bed', 'price']):
                        continue
                    
                    for row in rows[1:]:
                        try:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) < 3:
                                continue
                            
                            unit_data = {
                                'unit_number': '',
                                'rent': 0.0,
                                'bedrooms': 0,
                                'bathrooms': 1.0,
                                'square_feet': None,
                                'images': [],
                                'amenities': [],
                                'description': '',
                                'available_date': 'Immediate'
                            }
                            
                            for idx, cell in enumerate(cells):
                                text = cell.get_text(strip=True)
                                header = headers[idx] if idx < len(headers) else ''
                                
                                if 'unit' in header or idx == 0:
                                    if text and (text.isdigit() or re.match(r'^[A-Z0-9-]+$', text)):
                                        unit_data['unit_number'] = text
                                
                                if 'rent' in header or 'price' in header or '$' in text:
                                    rent_match = re.search(r'\$([0-9,]+)', text)
                                    if rent_match:
                                        unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                                
                                if 'bedroom' in header or 'bed' in header or 'br' in header:
                                    if 'studio' in text.lower():
                                        unit_data['bedrooms'] = 0
                                    else:
                                        bed_match = re.search(r'(\d+)', text)
                                        if bed_match:
                                            unit_data['bedrooms'] = int(bed_match.group(1))
                                
                                if 'bathroom' in header or 'bath' in header or 'ba' in header:
                                    bath_match = re.search(r'(\d+(?:\.\d+)?)', text)
                                    if bath_match:
                                        unit_data['bathrooms'] = float(bath_match.group(1))
                            
                            # Extract images from table row
                            images = row.find_all('img')
                            for img in images:
                                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                                if src:
                                    if src.startswith('//'):
                                        src = 'https:' + src
                                    elif src.startswith('/') and not src.startswith('http'):
                                        from urllib.parse import urlparse
                                        parsed_url = urlparse(url)
                                        src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                                    
                                    if src.startswith('http') and not any(x in src for x in ['logo', 'icon', 'sprite']):
                                        unit_data['images'].append(src)
                            
                            if unit_data['rent'] > 0:
                                if not unit_data['unit_number']:
                                    unit_data['unit_number'] = f"Unit-{len(units)+1}"
                                units.append(unit_data)
                        
                        except Exception as e:
                            logger.error(f"Error parsing table row: {e}")
                            continue
            
            # If no units from tables, try div-based parsing
            if not units:
                listing_containers = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'unit|apartment|listing|availability|property|floor|plan|residence', re.I))
                
                for container in listing_containers:
                    try:
                        unit_data = {
                            'unit_number': '',
                            'rent': 0.0,
                            'bedrooms': 0,
                            'bathrooms': 1.0,
                            'images': [],
                            'amenities': [],
                            'description': ''
                        }
                        
                        text = container.get_text(separator=' ', strip=True)
                        
                        rent_match = re.search(r'\$([0-9,]+)', text)
                        if rent_match:
                            unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                        
                        bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', text, re.I)
                        if bed_match:
                            unit_data['bedrooms'] = int(bed_match.group(1))
                        elif re.search(r'studio', text, re.I):
                            unit_data['bedrooms'] = 0
                        
                        bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', text, re.I)
                        if bath_match:
                            unit_data['bathrooms'] = float(bath_match.group(1))
                        
                        unit_match = re.search(r'(?:unit|apt|#)\s*([A-Z0-9-]+)', text, re.I)
                        if unit_match:
                            unit_data['unit_number'] = unit_match.group(1)
                        else:
                            # Generate unit number if not found
                            unit_data['unit_number'] = f"Unit-{len(units)+1}"
                        
                        images = container.find_all('img')
                        for img in images:
                            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                            if src:
                                # Clean up URL
                                if src.startswith('//'):
                                    src = 'https:' + src
                                elif src.startswith('/') and not src.startswith('http'):
                                    from urllib.parse import urlparse
                                    parsed_url = urlparse(url)
                                    src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                                
                                # Only add valid image URLs
                                if src.startswith('http') and not any(x in src for x in ['logo', 'icon', 'sprite']):
                                    unit_data['images'].append(src)
                        
                        # Get description
                        desc_elem = container.find(['p', 'div'], class_=re.compile(r'desc|detail|info', re.I))
                        if desc_elem:
                            unit_data['description'] = desc_elem.get_text(strip=True)[:500]
                        
                        if unit_data['rent'] > 0:
                            units.append(unit_data)
                    
                    except Exception as e:
                        logger.error(f"Error parsing unit: {e}")
                        continue
    
    except Exception as e:
        logger.error(f"Error crawling site: {e}")
    
    return units

async def crawl_building(building_id: str):
    """Crawl a specific building and update units"""
    building = await db.buildings.find_one({'id': building_id})
    if not building:
        logger.error(f"Building {building_id} not found")
        return
    
    url = building['source_url']
    logger.info(f"Crawling {building['name']} at {url}")
    
    # Determine which crawler to use based on URL
    if 'fortysixfifty' in url:
        units_data = await crawl_fortysixfifty(url)
    elif 'mercedeshouseny' in url:
        units_data = await crawl_mercedes_house(url)
    elif 'twotrees' in url:
        units_data = await crawl_twotrees(url)
    elif 'harrisonyards' in url:
        units_data = await crawl_harrison_yards(url)
    else:
        units_data = await crawl_generic_site(url)
    
    logger.info(f"Found {len(units_data)} units for {building['name']}")
    
    # Update or create units
    for unit_data in units_data:
        # Check if unit exists
        existing = await db.units.find_one({
            'building_id': building_id,
            'unit_number': unit_data['unit_number']
        })
        
        if existing:
            # Update existing unit
            update_data = {
                'rent': unit_data['rent'],
                'bedrooms': unit_data['bedrooms'],
                'bathrooms': unit_data['bathrooms'],
                'images': unit_data['images'],
                'amenities': unit_data['amenities'],
                'description': unit_data.get('description', ''),
                'is_available': True,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            await db.units.update_one(
                {'id': existing['id']},
                {'$set': update_data}
            )
        else:
            # Create new unit
            import uuid
            new_unit = {
                'id': str(uuid.uuid4()),
                'building_id': building_id,
                'unit_number': unit_data['unit_number'],
                'rent': unit_data['rent'],
                'bedrooms': unit_data['bedrooms'],
                'bathrooms': unit_data['bathrooms'],
                'images': unit_data['images'],
                'amenities': unit_data['amenities'],
                'description': unit_data.get('description', ''),
                'is_available': True,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            await db.units.insert_one(new_unit)
    
    # Update building last_crawled
    await db.buildings.update_one(
        {'id': building_id},
        {'$set': {'last_crawled': datetime.now(timezone.utc).isoformat()}}
    )

async def crawl_all_buildings():
    """Crawl all buildings"""
    buildings = await db.buildings.find({}).to_list(1000)
    logger.info(f"Crawling {len(buildings)} buildings")
    
    for building in buildings:
        try:
            await crawl_building(building['id'])
        except Exception as e:
            logger.error(f"Error crawling building {building['name']}: {e}")
            continue
