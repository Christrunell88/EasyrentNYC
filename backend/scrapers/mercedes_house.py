"""
Mercedes House scraper

Website: https://www.mercedeshouseny.com/
Format: Custom HTML with unit info in text patterns
"""

import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import get_browser, create_unit_template

logger = logging.getLogger(__name__)


async def crawl(url: str) -> List[Dict[str, Any]]:
    """
    Crawl mercedeshouseny.com availability page
    
    Uses regex pattern matching on page text to extract unit info
    """
    units = []
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(5000)
            
            content = await page.content()
            await browser.close()
        finally:
            await p.stop()
        
        soup = BeautifulSoup(content, 'html.parser')
        all_text = soup.get_text()
        
        # Pattern: "Studio/X Bedroom #UNIT $RENT"
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
                
                if 'studio' in bedroom_type.lower():
                    bedrooms = 0
                else:
                    bed_match = re.search(r'(\d+)', bedroom_type)
                    bedrooms = int(bed_match.group(1)) if bed_match else 1
                
                unit_data = create_unit_template()
                unit_data.update({
                    'unit_number': unit_number,
                    'rent': rent,
                    'bedrooms': bedrooms,
                    'bathrooms': 1.0,
                    'description': f"{bedroom_type} apartment",
                    'raw_data': f"{bedroom_type}#{unit_number}|${rent}"
                })
                
                units.append(unit_data)
            
            except Exception as e:
                logger.error(f"Error parsing Mercedes unit: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error crawling Mercedes House: {e}")
    
    return units
