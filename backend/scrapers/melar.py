"""
The Melar scraper

Website: https://www.themelar.com/
Format: Rose NYC iframe-based availability
Location: Upper West Side, Manhattan
"""

from typing import List, Dict, Any
from .rosenyc_base import crawl_rosenyc_iframe


async def crawl(url: str) -> List[Dict[str, Any]]:
    """
    Crawl The Melar availability page
    
    Uses Rose NYC iframe: https://www.rosenyc.com/availability/mgooldds/
    """
    return await crawl_rosenyc_iframe(
        url=url,
        building_name='The Melar',
        description='The Melar - Upper West Side luxury apartment',
        direct_rosenyc_url='https://www.rosenyc.com/availability/mgooldds/'
    )
