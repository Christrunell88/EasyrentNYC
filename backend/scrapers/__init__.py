"""
NoFeesApts Web Scrapers

This package contains individual scraper modules for different apartment websites.
Each scraper module implements a `crawl(url)` async function that returns a list of unit dicts.

Usage:
    from scrapers import get_scraper, crawl_url
    
    # Get scraper by URL
    scraper = get_scraper(url)
    units = await scraper.crawl(url)
    
    # Or use the unified interface
    units = await crawl_url(url)

Supported websites:
    - fortysixfifty.com (4650 Center Blvd)
    - mercedeshouseny.com (Mercedes House)
    - harrisonyards.com (Harrison Yards)
    - 7w21.com (7 West 21st)
    - rentrivercourtnyc.com (Rivercourt)
    - themelar.com (The Melar)
    - Generic sites (fallback parser)
"""

from typing import List, Dict, Any, Optional
import logging

# Import individual scrapers
from . import fortysixfifty
from . import mercedes_house
from . import harrison_yards
from . import seven_w21
from . import rivercourt
from . import melar
from . import generic
from .base import create_unit_template, normalize_unit_number

logger = logging.getLogger(__name__)

# Scraper registry - maps URL patterns to scraper modules
SCRAPER_REGISTRY = {
    'fortysixfifty': fortysixfifty,
    'mercedeshouseny': mercedes_house,
    'harrisonyards': harrison_yards,
    '7w21': seven_w21,
    'rivercourt': rivercourt,
    'rentrivercourtnyc': rivercourt,
    'melar': melar,
    'themelar': melar,
}


def get_scraper(url: str):
    """
    Get the appropriate scraper module for a URL
    
    Args:
        url: The URL to scrape
        
    Returns:
        The scraper module or None if no specific scraper found
    """
    url_lower = url.lower()
    
    for pattern, scraper in SCRAPER_REGISTRY.items():
        if pattern in url_lower:
            logger.info(f"Using {pattern} scraper for {url}")
            return scraper
    
    logger.info(f"No specific scraper for {url}, using generic scraper")
    return generic


async def crawl_url(url: str) -> List[Dict[str, Any]]:
    """
    Crawl a URL using the appropriate scraper
    
    Args:
        url: The URL to scrape
        
    Returns:
        List of unit dictionaries
    """
    scraper = get_scraper(url)
    return await scraper.crawl(url)


__all__ = [
    'get_scraper',
    'crawl_url',
    'create_unit_template',
    'normalize_unit_number',
    'SCRAPER_REGISTRY',
]
