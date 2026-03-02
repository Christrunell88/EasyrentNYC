"""
Rivercourt NYC scraper

Website: https://www.rentrivercourtnyc.com/
Format: Rose NYC iframe-based availability
Location: Long Island City, Queens
"""

from typing import List, Dict, Any
from .rosenyc_base import crawl_rosenyc_iframe


async def crawl(url: str) -> List[Dict[str, Any]]:
    """
    Crawl Rivercourt NYC availability page
    
    Uses Rose NYC iframe: https://www.rosenyc.com/availability/mgpelfdh/
    """
    return await crawl_rosenyc_iframe(
        url=url,
        building_name='Rivercourt',
        description='Rivercourt - Long Island City luxury apartment',
        direct_rosenyc_url='https://www.rosenyc.com/availability/mgpelfdh/'
    )
