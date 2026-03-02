"""
Base scraper utilities and shared functionality

This module provides common utilities used by all scrapers:
- Browser automation (Playwright)
- HTML parsing helpers
- Data extraction utilities
"""

import re
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# Browser management
_browser_instance = None
_playwright_instance = None


async def get_browser():
    """Get or create a Playwright browser instance"""
    global _browser_instance, _playwright_instance
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    return p, browser


async def fetch_page_content(url: str, wait_for_iframe: str = None, timeout: int = 30000) -> Optional[str]:
    """
    Fetch page content using Playwright
    
    Args:
        url: The URL to fetch
        wait_for_iframe: If specified, look for an iframe containing this string
        timeout: Request timeout in milliseconds
    
    Returns:
        Page HTML content or None on error
    """
    content = None
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=timeout)
            await page.wait_for_timeout(3000)
            
            if wait_for_iframe:
                frames = page.frames
                for frame in frames:
                    if wait_for_iframe in frame.url:
                        logger.info(f"Found iframe: {frame.url}")
                        content = await frame.content()
                        break
            
            if not content:
                content = await page.content()
            
            await browser.close()
        finally:
            await p.stop()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
    
    return content


def parse_rent(text: str) -> float:
    """Extract rent amount from text (e.g., '$3,500/mo' -> 3500.0)"""
    if not text:
        return 0.0
    rent_match = re.search(r'\$?([0-9,]+)', text.replace(',', ''))
    if rent_match:
        return float(rent_match.group(1).replace(',', ''))
    return 0.0


def parse_bedrooms(text: str) -> int:
    """Extract bedroom count from text (e.g., '2 BR' -> 2, 'Studio' -> 0)"""
    if not text:
        return 0
    text_lower = text.lower()
    if 'studio' in text_lower:
        return 0
    bed_match = re.search(r'(\d+)', text)
    if bed_match:
        return int(bed_match.group(1))
    return 0


def parse_bathrooms(text: str) -> float:
    """Extract bathroom count from text (e.g., '1.5 BA' -> 1.5)"""
    if not text:
        return 1.0
    bath_match = re.search(r'(\d+(?:\.\d+)?)', text)
    if bath_match:
        return float(bath_match.group(1))
    return 1.0


def parse_sqft(text: str) -> Optional[int]:
    """Extract square footage from text"""
    if not text:
        return None
    sqft_match = re.search(r'(\d+)', text.replace(',', ''))
    if sqft_match:
        return int(sqft_match.group(1))
    return None


def create_unit_template() -> Dict[str, Any]:
    """Create a blank unit data template"""
    return {
        'unit_number': '',
        'rent': 0.0,
        'bedrooms': 0,
        'bathrooms': 1.0,
        'square_feet': None,
        'images': [],
        'amenities': [],
        'description': '',
        'available_date': 'Immediate',
        'raw_data': ''
    }


def normalize_unit_number(unit_number: str) -> str:
    """Normalize unit number for comparison"""
    if not unit_number:
        return ""
    normalized = re.sub(r'^(unit|apt|#|apartment|suite)\s*', '', unit_number.lower(), flags=re.IGNORECASE)
    normalized = re.sub(r'[^a-zA-Z0-9]', '', normalized)
    return normalized.upper()
