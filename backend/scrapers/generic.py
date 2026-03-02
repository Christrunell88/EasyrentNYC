"""
Generic site scraper

This is a fallback scraper for sites that don't have a specific implementation.
It attempts to parse availability data from:
1. Tables with common headers (unit, rent, bedroom, etc.)
2. Div-based listings with common class names
3. iframes that might contain availability data
"""

import re
import logging
from typing import List, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from .base import get_browser, create_unit_template

logger = logging.getLogger(__name__)


async def crawl(url: str) -> List[Dict[str, Any]]:
    """
    Generic crawler that attempts to extract unit data from any site
    
    Tries multiple strategies:
    1. Look for iframes with availability data
    2. Parse table-based listings
    3. Parse div-based listings
    """
    units = []
    content = None
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(5000)
            
            # Check for iframes
            frames = page.frames
            iframe_content = None
            for frame in frames:
                if frame.url != 'about:blank' and 'google' not in frame.url and frame.url != url:
                    try:
                        iframe_content = await frame.content()
                        logger.info(f"Using iframe content from: {frame.url}")
                        break
                    except Exception:
                        continue
            
            content = iframe_content if iframe_content else await page.content()
            await browser.close()
        finally:
            await p.stop()
        
        if not content:
            return units
        
        soup = BeautifulSoup(content, 'html.parser')
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Strategy 1: Try table-based parsing
        units = _parse_tables(soup, base_url)
        
        # Strategy 2: If no units from tables, try div-based parsing
        if not units:
            units = _parse_divs(soup, base_url)
    
    except Exception as e:
        logger.error(f"Error crawling site: {e}")
    
    return units


def _parse_tables(soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
    """Parse units from HTML tables"""
    units = []
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        if len(rows) < 2:
            continue
        
        header_row = rows[0]
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        # Check if this looks like a unit table
        if not any(h in headers for h in ['unit', 'rent', 'bedroom', 'bed', 'price']):
            continue
        
        for row in rows[1:]:
            try:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                
                unit_data = create_unit_template()
                unit_data['raw_data'] = str(row)
                
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
                
                # Extract images
                unit_data['images'] = _extract_images(row, base_url)
                
                if unit_data['rent'] > 0:
                    if not unit_data['unit_number']:
                        unit_data['unit_number'] = f"Unit-{len(units)+1}"
                    units.append(unit_data)
            
            except Exception as e:
                logger.error(f"Error parsing table row: {e}")
                continue
    
    return units


def _parse_divs(soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
    """Parse units from div-based layouts"""
    units = []
    
    # Look for common listing container patterns
    listing_containers = soup.find_all(
        ['div', 'article', 'li'],
        class_=re.compile(r'unit|apartment|listing|availability|property|floor|plan|residence', re.I)
    )
    
    for container in listing_containers:
        try:
            unit_data = create_unit_template()
            unit_data['raw_data'] = str(container)[:1000]
            
            text = container.get_text(separator=' ', strip=True)
            
            # Extract rent
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
            
            # Extract unit number
            unit_match = re.search(r'(?:unit|apt|#)\s*([A-Z0-9-]+)', text, re.I)
            if unit_match:
                unit_data['unit_number'] = unit_match.group(1)
            else:
                unit_data['unit_number'] = f"Unit-{len(units)+1}"
            
            # Extract images
            unit_data['images'] = _extract_images(container, base_url)
            
            # Extract description
            desc_elem = container.find(['p', 'div'], class_=re.compile(r'desc|detail|info', re.I))
            if desc_elem:
                unit_data['description'] = desc_elem.get_text(strip=True)[:500]
            
            if unit_data['rent'] > 0:
                units.append(unit_data)
        
        except Exception as e:
            logger.error(f"Error parsing unit: {e}")
            continue
    
    return units


def _extract_images(element, base_url: str) -> List[str]:
    """Extract image URLs from an HTML element"""
    images = []
    
    for img in element.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
        if src:
            src = _normalize_url(src, base_url)
            if src and not any(x in src for x in ['logo', 'icon', 'sprite']):
                images.append(src)
    
    return images


def _normalize_url(src: str, base_url: str) -> str:
    """Normalize a URL to be absolute"""
    if not src:
        return None
    
    if src.startswith('//'):
        return 'https:' + src
    elif src.startswith('/') and not src.startswith('http'):
        return base_url + src
    elif src.startswith('http'):
        return src
    
    return None
