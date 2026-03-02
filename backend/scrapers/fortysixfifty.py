"""
Forty Six Fifty (4650 Center Blvd) scraper

Website: https://www.fortysixfifty.com/
Format: iframe-based availability widget from rosenyc.com
"""

import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import get_browser, create_unit_template, parse_rent, parse_bedrooms, parse_bathrooms, parse_sqft

logger = logging.getLogger(__name__)


async def crawl(url: str) -> List[Dict[str, Any]]:
    """
    Crawl fortysixfifty.com availability page
    
    Handles iframe-based availability widget from rosenyc.com
    """
    units = []
    content = None
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Look for rosenyc.com iframe
            frames = page.frames
            iframe_content = None
            for frame in frames:
                if 'rosenyc.com' in frame.url:
                    logger.info(f"Found availability iframe: {frame.url}")
                    iframe_content = await frame.content()
                    break
            
            content = iframe_content if iframe_content else await page.content()
            await browser.close()
        finally:
            await p.stop()
        
        if not content:
            return units
            
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            
            header_row = rows[0]
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            
            if not any(h in headers for h in ['unit', 'rent', 'bedroom']):
                continue
            
            for row in rows[1:]:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 4:
                        continue
                    
                    unit_data = create_unit_template()
                    unit_data['raw_data'] = str(row)
                    
                    for idx, cell in enumerate(cells):
                        text = cell.get_text(strip=True)
                        header = headers[idx] if idx < len(headers) else ''
                        
                        if 'unit' in header or idx == 0:
                            if text and (text.isdigit() or re.match(r'^[A-Z0-9-]+$', text)):
                                unit_data['unit_number'] = text
                        
                        if 'rent' in header or '$' in text:
                            unit_data['rent'] = parse_rent(text)
                        
                        if 'bedroom' in header or 'br' in header:
                            unit_data['bedrooms'] = parse_bedrooms(text)
                        
                        if 'bathroom' in header or 'ba' in header:
                            unit_data['bathrooms'] = parse_bathrooms(text)
                        
                        if 'sq' in header or 'sq.' in text.lower():
                            unit_data['square_feet'] = parse_sqft(text)
                        
                        if 'availability' in header:
                            if text and text != 'Immediate':
                                unit_data['available_date'] = text
                    
                    if unit_data['unit_number'] and unit_data['rent'] > 0:
                        units.append(unit_data)
                
                except Exception as e:
                    logger.error(f"Error parsing row: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Error crawling fortysixfifty: {e}")
    
    return units
