"""
7W21 (7 West 21st Street) scraper

Website: https://www.7w21.com/
Format: Rose NYC iframe-based availability
Location: Flatiron District, Manhattan
"""

from typing import List, Dict, Any
from .rosenyc_base import crawl_rosenyc_iframe


async def crawl(url: str) -> List[Dict[str, Any]]:
    """
    Crawl 7W21 availability page
    
    Uses Rose NYC iframe: https://www.rosenyc.com/availability/mgoublmo/
    """
    return await crawl_rosenyc_iframe(
        url='https://www.7w21.com/',
        building_name='7W21',
        description='7 West 21st Street - Flatiron District luxury apartment',
        direct_rosenyc_url='https://www.rosenyc.com/availability/mgoublmo/'
    )
