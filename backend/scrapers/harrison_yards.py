"""
Harrison Yards scraper

Website: https://www.harrisonyards.com/
Format: RealPage/LeaseStar widget with rpfp-card elements
"""

import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import get_browser, create_unit_template

logger = logging.getLogger(__name__)


async def crawl(url: str) -> List[Dict[str, Any]]:
    """
    Crawl harrisonyards.com availability page
    
    Uses RealPage/LeaseStar widget with rpfp-card elements
    """
    units = []
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(8000)
            
            try:
                await page.wait_for_selector('.rpfp-card, .rpfp-card-details', timeout=5000)
            except Exception:
                logger.warning("Floor plan cards did not load in time, proceeding anyway")
            
            content = await page.content()
            await browser.close()
        finally:
            await p.stop()
        
        soup = BeautifulSoup(content, 'html.parser')
        floor_plan_cards = soup.find_all('div', class_=re.compile(r'rpfp-card', re.I))
        
        logger.info(f"Found {len(floor_plan_cards)} floor plan cards")
        
        for card in floor_plan_cards:
            try:
                unit_data = create_unit_template()
                unit_data['raw_data'] = str(card)
                
                text = card.get_text(separator=' ', strip=True)
                
                # Extract price
                price_elem = card.find(['span', 'div'], class_=re.compile(r'price|rent|rate', re.I))
                if price_elem:
                    rent_match = re.search(r'\$([0-9,]+)', price_elem.get_text())
                    if rent_match:
                        unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                else:
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
                
                # Extract unit number
                unit_num_elem = card.find(['span', 'div'], class_=re.compile(r'unit|name|title', re.I))
                if unit_num_elem:
                    unit_text = unit_num_elem.get_text(strip=True)
                    unit_match = re.search(r'([A-Z0-9-]+)', unit_text)
                    if unit_match:
                        unit_data['unit_number'] = unit_match.group(1)
                
                # Generate unit number if not found
                if not unit_data['unit_number']:
                    bed_type = "Studio" if unit_data['bedrooms'] == 0 else f"{unit_data['bedrooms']}BR"
                    unit_data['unit_number'] = f"{bed_type}-{len(units)+1}"
                
                # Extract images
                images = card.find_all('img')
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/') and not src.startswith('http'):
                            src = 'https://harrisonyards.com' + src
                        
                        if src.startswith('https://') and not any(x in src.lower() for x in ['icon', 'logo', 'spinner', 'browser']):
                            if src not in unit_data['images']:
                                unit_data['images'].append(src)
                
                # Check for background images in style
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
                
                if unit_data['rent'] > 0:
                    units.append(unit_data)
                    logger.info(f"Found Harrison Yards unit: {unit_data['unit_number']} - ${unit_data['rent']} - {len(unit_data['images'])} images")
            
            except Exception as e:
                logger.error(f"Error parsing Harrison Yards card: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error crawling Harrison Yards: {e}")
    
    return units
