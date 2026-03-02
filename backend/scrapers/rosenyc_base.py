"""
Rose NYC iframe-based scrapers

Many NYC luxury buildings use Rose NYC (rosenyc.com) for their availability widget.
This module provides a base class and specific implementations for:
- 7W21 (7 West 21st Street)
- Rivercourt (Long Island City)
- The Melar (Upper West Side)
"""

import re
import asyncio
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import get_browser, create_unit_template

logger = logging.getLogger(__name__)


async def crawl_rosenyc_iframe(url: str, building_name: str, description: str, direct_rosenyc_url: str = None) -> List[Dict[str, Any]]:
    """
    Generic crawler for Rose NYC iframe-based availability pages
    
    Args:
        url: Main building website URL
        building_name: Name of the building for logging
        description: Description to add to unit data
        direct_rosenyc_url: Direct URL to Rose NYC availability page (fallback)
    
    Returns:
        List of unit dictionaries
    """
    units = []
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            
            logger.info(f"Loading {building_name} page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(15000)
            
            # Find the Rose NYC iframe
            frames = page.frames
            rosenyc_frame = None
            
            for frame in frames:
                if 'rosenyc.com' in frame.url:
                    rosenyc_frame = frame
                    logger.info(f"Found Rose NYC iframe: {frame.url}")
                    break
            
            if rosenyc_frame:
                await rosenyc_frame.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(5)
                content = await rosenyc_frame.content()
            elif direct_rosenyc_url:
                logger.warning("Rose NYC iframe not found, trying direct URL")
                await page.goto(direct_rosenyc_url, wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(10000)
                content = await page.content()
            else:
                logger.warning("Rose NYC iframe not found")
                content = await page.content()
            
            await browser.close()
        finally:
            await p.stop()
        
        if not content:
            return units
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check for "Please call for availability" message
        if 'please call for availability' in content.lower():
            logger.info(f"{building_name}: No units currently available (please call message)")
            return units
        
        # Look for table rows with unit data
        rows = soup.find_all('tr', {'data-beds': True})
        
        if not rows:
            # Fallback: look for rows with role='row'
            rows = soup.find_all('tr', {'role': 'row'})
        
        if not rows:
            # Fallback: look in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
        
        logger.info(f"Found {len(rows)} potential unit rows")
        
        for row in rows:
            # Skip header rows
            if 't-header' in row.get('class', []):
                continue
            
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
            
            try:
                unit_data = create_unit_template()
                unit_data['description'] = description
                unit_data['raw_data'] = str(row)[:2000]
                
                for cell in cells:
                    label = cell.get('data-label', '').lower()
                    text = cell.get_text(strip=True)
                    
                    if 'unit' in label or 'apt' in label:
                        unit_data['unit_number'] = text
                    
                    elif 'bedroom' in label or 'bed' in label:
                        if 'studio' in text.lower():
                            unit_data['bedrooms'] = 0
                        else:
                            bed_match = re.search(r'(\d+)', text)
                            if bed_match:
                                unit_data['bedrooms'] = int(bed_match.group(1))
                    
                    elif 'bathroom' in label or 'bath' in label:
                        bath_match = re.search(r'(\d+(?:\.\d+)?)', text)
                        if bath_match:
                            unit_data['bathrooms'] = float(bath_match.group(1))
                    
                    elif 'rent' in label or 'price' in label or '$' in text:
                        rent_match = re.search(r'\$([0-9,]+)', text)
                        if rent_match:
                            unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                    
                    elif 'sqft' in label or 'sq' in label:
                        sqft_match = re.search(r'([0-9,]+)', text)
                        if sqft_match:
                            unit_data['square_feet'] = int(sqft_match.group(1).replace(',', ''))
                    
                    elif 'availability' in label or 'available' in label:
                        unit_data['available_date'] = text or 'Immediate'
                
                # Also try to get bedrooms from data attribute
                beds_attr = row.get('data-beds')
                if beds_attr and not unit_data['bedrooms']:
                    try:
                        unit_data['bedrooms'] = int(beds_attr)
                    except:
                        pass
                
                # Extract images from mfp-image links
                images = row.find_all('a', class_='mfp-image')
                for img_link in images:
                    href = img_link.get('href')
                    if href and href.startswith('http'):
                        unit_data['images'].append(href)
                
                if unit_data['rent'] > 0:
                    if not unit_data['unit_number']:
                        unit_data['unit_number'] = f"Unit-{len(units)+1}"
                    units.append(unit_data)
                    logger.info(f"Found unit: {unit_data['unit_number']} - ${unit_data['rent']}")
            
            except Exception as e:
                logger.error(f"Error parsing {building_name} unit row: {e}")
                continue
        
        logger.info(f"{building_name} crawl complete: found {len(units)} units")
    
    except Exception as e:
        logger.error(f"Error crawling {building_name}: {e}")
    
    return units
