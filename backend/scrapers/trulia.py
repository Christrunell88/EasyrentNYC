"""
Trulia.com Apartment Scraper

Extracts apartment listings from Trulia rental pages.
Key data points: address, rent, bedrooms, bathrooms, images
"""

import re
import logging
from typing import List, Dict, Any
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from .base import get_browser, create_unit_template

logger = logging.getLogger(__name__)


async def crawl(url: str) -> List[Dict[str, Any]]:
    """
    Crawl a Trulia listing page to extract apartment data.
    
    Trulia URLs typically look like:
    - https://www.trulia.com/p/ny/new-york/507-w-28th-st-new-york-ny-10001--2023339251
    - https://www.trulia.com/building/...
    
    Returns:
        List of unit dictionaries with address, rent, beds, baths, images
    """
    units = []
    building_address = None
    building_name = None
    neighborhood = None
    city = None
    state = None
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            
            # Set a realistic user agent
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Scroll to load lazy content
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
            await page.wait_for_timeout(2000)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            await browser.close()
        finally:
            await p.stop()
        
        if not content:
            logger.warning("No content received from Trulia")
            return units
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract building/property address
        # Try multiple selectors for Trulia's address
        address_selectors = [
            'h1[data-testid="home-details-summary-headline"]',
            'h1.Text__TextBase-sc-1cait9d-0',
            'div[data-testid="home-details-summary-address"]',
            'span[data-testid="home-details-summary-city-state"]',
            'h1',  # Fallback to first h1
        ]
        
        for selector in address_selectors:
            address_elem = soup.select_one(selector)
            if address_elem:
                text = address_elem.get_text(strip=True)
                if text and len(text) > 5 and (',' in text or any(state in text for state in [' NY', ' NJ', ' PA'])):
                    building_address = text
                    logger.info(f"Found address: {building_address}")
                    break
        
        # Try to extract from URL if not found in page
        if not building_address:
            # Parse URL like: /p/ny/new-york/507-w-28th-st-new-york-ny-10001--2023339251
            url_match = re.search(r'/([a-z]{2})/([^/]+)/([^/]+?)(?:--|\?)', url)
            if url_match:
                state = url_match.group(1).upper()
                city = url_match.group(2).replace('-', ' ').title()
                address_slug = url_match.group(3).replace('-', ' ').title()
                # Clean up the address
                address_slug = re.sub(r'\s+\d+$', '', address_slug)  # Remove trailing numbers
                building_address = f"{address_slug}, {city}, {state}"
                logger.info(f"Extracted address from URL: {building_address}")
        
        # Extract city and state from address
        if building_address:
            # Parse "123 Main St, Brooklyn, NY 10001" format
            parts = building_address.split(',')
            if len(parts) >= 2:
                # Last part usually has state and zip
                state_zip = parts[-1].strip()
                state_match = re.search(r'(NY|NJ|PA|CT)', state_zip)
                if state_match:
                    state = state_match.group(1)
                
                # Second to last is usually city
                if len(parts) >= 2:
                    city = parts[-2].strip() if len(parts) > 2 else parts[-1].split()[0]
        
        # Extract neighborhood
        neighborhood_selectors = [
            'a[data-testid="home-details-summary-neighborhood"]',
            'div[class*="neighborhood"]',
            'span[class*="neighborhood"]',
        ]
        for selector in neighborhood_selectors:
            hood_elem = soup.select_one(selector)
            if hood_elem:
                neighborhood = hood_elem.get_text(strip=True)
                break
        
        # Extract building name (might be different from address)
        name_selectors = [
            'h1[data-testid="building-name"]',
            'div[data-testid="property-name"]',
        ]
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem:
                building_name = name_elem.get_text(strip=True)
                break
        
        if not building_name and building_address:
            # Use address as building name
            building_name = building_address.split(',')[0] if ',' in building_address else building_address
        
        # Extract all unit listings
        # Trulia uses various containers for rental units
        unit_selectors = [
            'div[data-testid="rental-unit-card"]',
            'div[class*="FloorPlanCard"]',
            'div[class*="UnitCard"]',
            'li[data-testid*="unit"]',
            'div[class*="unit-item"]',
            'div[class*="floor-plan"]',
        ]
        
        unit_containers = []
        for selector in unit_selectors:
            found = soup.select(selector)
            if found:
                unit_containers = found
                logger.info(f"Found {len(found)} units using selector: {selector}")
                break
        
        # If no specific unit containers, look for price patterns in the page
        if not unit_containers:
            # Look for any element with rent information
            all_elements = soup.find_all(['div', 'li', 'article'], class_=re.compile(r'.*', re.I))
            for elem in all_elements:
                text = elem.get_text(separator=' ', strip=True)
                # Check if it looks like a unit listing (has price and beds/baths)
                if re.search(r'\$[\d,]+', text) and re.search(r'\d+\s*(bed|br|bath|ba|studio)', text, re.I):
                    # Check it's not too long (avoid getting the whole page)
                    if len(text) < 500:
                        unit_containers.append(elem)
        
        # Parse each unit container
        for container in unit_containers:
            try:
                unit_data = create_unit_template()
                unit_data['raw_data'] = str(container)[:1000]
                
                text = container.get_text(separator=' ', strip=True)
                
                # Extract rent
                rent_match = re.search(r'\$([0-9,]+)', text)
                if rent_match:
                    rent_val = float(rent_match.group(1).replace(',', ''))
                    # Validate rent is reasonable (not a phone number, etc.)
                    if 500 < rent_val < 50000:
                        unit_data['rent'] = rent_val
                
                # Extract bedrooms
                if re.search(r'studio', text, re.I):
                    unit_data['bedrooms'] = 0
                else:
                    bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)s?', text, re.I)
                    if bed_match:
                        unit_data['bedrooms'] = int(bed_match.group(1))
                
                # Extract bathrooms
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)s?', text, re.I)
                if bath_match:
                    unit_data['bathrooms'] = float(bath_match.group(1))
                
                # Extract unit number
                unit_match = re.search(r'(?:unit|apt|#|apartment)\s*([A-Z0-9-]+)', text, re.I)
                if unit_match:
                    unit_data['unit_number'] = unit_match.group(1)
                
                # Extract square footage
                sqft_match = re.search(r'([\d,]+)\s*(?:sq\.?\s*ft\.?|sqft|square\s*feet)', text, re.I)
                if sqft_match:
                    unit_data['sqft'] = int(sqft_match.group(1).replace(',', ''))
                
                # Extract images from the container
                unit_data['images'] = _extract_images(container, url)
                
                # Add building info
                unit_data['building_address'] = building_address
                unit_data['building_name'] = building_name
                unit_data['neighborhood'] = neighborhood
                unit_data['city'] = city
                unit_data['state'] = state
                
                # Only add if we have valid rent
                if unit_data['rent'] and unit_data['rent'] > 0:
                    if not unit_data['unit_number']:
                        unit_data['unit_number'] = f"Unit-{len(units)+1}"
                    units.append(unit_data)
                    logger.info(f"Found unit: {unit_data['unit_number']} - ${unit_data['rent']}")
            
            except Exception as e:
                logger.error(f"Error parsing unit container: {e}")
                continue
        
        # If no units found but we have building info, create a placeholder
        if not units and building_address:
            # Try to extract main listing info from the page
            unit_data = create_unit_template()
            
            # Look for main price
            price_elem = soup.select_one('[data-testid="home-summary-price"], span[class*="price"]')
            if price_elem:
                rent_match = re.search(r'\$([0-9,]+)', price_elem.get_text())
                if rent_match:
                    unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
            
            # Look for beds/baths in the summary
            summary_text = soup.get_text(separator=' ')
            
            if re.search(r'studio', summary_text, re.I):
                unit_data['bedrooms'] = 0
            else:
                bed_match = re.search(r'(\d+)\s*(?:bed|br)s?', summary_text, re.I)
                if bed_match:
                    unit_data['bedrooms'] = int(bed_match.group(1))
            
            bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)s?', summary_text, re.I)
            if bath_match:
                unit_data['bathrooms'] = float(bath_match.group(1))
            
            # Get main images
            unit_data['images'] = _extract_images(soup, url)[:10]
            
            unit_data['building_address'] = building_address
            unit_data['building_name'] = building_name
            unit_data['neighborhood'] = neighborhood
            unit_data['city'] = city
            unit_data['state'] = state
            unit_data['unit_number'] = 'Main Listing'
            
            if unit_data['rent'] and unit_data['rent'] > 0:
                units.append(unit_data)
                logger.info(f"Created single listing from page: {building_address} - ${unit_data['rent']}")
        
        logger.info(f"Trulia crawl complete. Found {len(units)} units at {building_address}")
        
    except Exception as e:
        logger.error(f"Error crawling Trulia: {e}")
    
    return units


def _extract_images(element, base_url: str) -> List[str]:
    """Extract image URLs from an HTML element"""
    images = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    # Look for images in various attributes
    for img in element.find_all('img'):
        for attr in ['src', 'data-src', 'data-lazy-src', 'data-original', 'srcset']:
            src = img.get(attr)
            if src:
                # Handle srcset (take the largest)
                if ',' in src and 'w' in src:
                    srcset_parts = src.split(',')
                    # Get the last (usually largest) image
                    src = srcset_parts[-1].strip().split()[0]
                
                # Skip tiny images, icons, logos
                if any(x in src.lower() for x in ['logo', 'icon', 'sprite', '1x1', 'pixel', 'tracking']):
                    continue
                
                # Normalize URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = base + src
                elif not src.startswith('http'):
                    src = urljoin(base_url, src)
                
                if src not in images:
                    images.append(src)
    
    # Also look for background images in style attributes
    for elem in element.find_all(style=re.compile(r'background.*url')):
        style = elem.get('style', '')
        url_match = re.search(r'url\(["\']?([^"\')\s]+)["\']?\)', style)
        if url_match:
            src = url_match.group(1)
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = base + src
            if src not in images and 'logo' not in src.lower():
                images.append(src)
    
    return images
