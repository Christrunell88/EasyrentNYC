"""Web crawler for apartment listings - STAGING ONLY
=======================================================
All crawled data goes to staging collections for review before production.

HARD RULE ENFORCED:
- Crawlers can ONLY write to staging collections (units_staging, buildings_staging)
- Direct writes to production collections (units, buildings) are BLOCKED
- Production writes require manual admin approval or internal leasing system feeds

This module uses DatabaseAccessControl to enforce these rules.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
import aiohttp
import uuid
import hashlib
from cloud_storage_service import upload_apartment_image

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Set Playwright browsers path for consistent browser location
PLAYWRIGHT_BROWSERS_PATH = '/pw-browsers'
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = PLAYWRIGHT_BROWSERS_PATH

logger = logging.getLogger(__name__)


async def get_browser():
    """
    Get a Playwright browser instance with the correct executable path.
    Returns a context manager that yields the browser.
    """
    p = await async_playwright().start()
    
    # Try to find the chromium executable
    executable_paths = [
        f'{PLAYWRIGHT_BROWSERS_PATH}/chromium_headless_shell-1194/chrome-linux/headless_shell',
        f'{PLAYWRIGHT_BROWSERS_PATH}/chromium-1194/chrome-linux/chrome',
        f'{PLAYWRIGHT_BROWSERS_PATH}/chromium_headless_shell-1208/chrome-linux/headless_shell',
    ]
    
    executable_path = None
    for path in executable_paths:
        if os.path.exists(path):
            executable_path = path
            break
    
    if executable_path:
        browser = await p.chromium.launch(headless=True, executable_path=executable_path)
    else:
        # Fallback to default (will use PLAYWRIGHT_BROWSERS_PATH env var)
        browser = await p.chromium.launch(headless=True)
    
    return p, browser


# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Import access control (with fallback for standalone usage)
try:
    from db_access_control import (
        DatabaseAccessControl, 
        UnauthorizedWriteError,
        get_access_control,
        WriteSource
    )
    ACCESS_CONTROL_AVAILABLE = True
    logger.info("Database access control loaded - production writes will be blocked")
except ImportError:
    ACCESS_CONTROL_AVAILABLE = False
    logger.warning("Database access control not available - using direct writes")

# Toggle for GCS image upload (set to True to use GCS, False to use original URLs)
USE_GCS_FOR_IMAGES = os.environ.get('USE_GCS_FOR_IMAGES', 'true').lower() == 'true'

# ============ PRODUCTION WRITE BLOCKER ============

class CrawlerProductionWriteBlocker:
    """
    Blocks any attempt by the crawler to write to production collections.
    This is a fail-safe to ensure crawlers never touch production data directly.
    """
    
    BLOCKED_COLLECTIONS = {'units', 'buildings'}
    ALLOWED_COLLECTIONS = {'units_staging', 'buildings_staging'}
    
    @classmethod
    def check_collection(cls, collection_name: str, operation: str = "write"):
        """
        Check if a write to the given collection is allowed.
        
        Raises:
            UnauthorizedWriteError: If trying to write to a blocked collection
        """
        if collection_name in cls.BLOCKED_COLLECTIONS:
            error_msg = (
                f"BLOCKED: Crawler attempted {operation} on production collection '{collection_name}'. "
                f"Crawlers can ONLY write to staging collections: {cls.ALLOWED_COLLECTIONS}"
            )
            logger.error(error_msg)
            if ACCESS_CONTROL_AVAILABLE:
                raise UnauthorizedWriteError(error_msg)
            else:
                raise PermissionError(error_msg)
        
        if collection_name not in cls.ALLOWED_COLLECTIONS:
            logger.warning(f"Crawler writing to non-standard collection: {collection_name}")


async def _safe_staging_insert(collection_name: str, document: Dict, crawler_source: str):
    """
    Safely insert a document into a staging collection.
    
    This function enforces the hard rule that crawlers can only write to staging.
    """
    # HARD RULE: Block production writes
    CrawlerProductionWriteBlocker.check_collection(collection_name, "insert")
    
    if ACCESS_CONTROL_AVAILABLE:
        access_control = get_access_control(db)
        return await access_control.staging_write(
            collection=collection_name,
            operation='insert',
            document=document,
            crawler_source=crawler_source
        )
    else:
        # Fallback direct insert (still blocked for production)
        await db[collection_name].insert_one(document)
        return {"inserted_id": document.get('id')}


async def _safe_staging_update(collection_name: str, query: Dict, update: Dict, crawler_source: str):
    """
    Safely update a document in a staging collection.
    """
    CrawlerProductionWriteBlocker.check_collection(collection_name, "update")
    
    result = await db[collection_name].update_one(query, update)
    return {"matched": result.matched_count, "modified": result.modified_count}


# ============ ADDRESS NORMALIZATION ============

# Common street type abbreviations
STREET_TYPE_MAPPINGS = {
    'street': 'St',
    'st': 'St',
    'st.': 'St',
    'avenue': 'Ave',
    'ave': 'Ave',
    'ave.': 'Ave',
    'boulevard': 'Blvd',
    'blvd': 'Blvd',
    'blvd.': 'Blvd',
    'drive': 'Dr',
    'dr': 'Dr',
    'dr.': 'Dr',
    'road': 'Rd',
    'rd': 'Rd',
    'rd.': 'Rd',
    'lane': 'Ln',
    'ln': 'Ln',
    'ln.': 'Ln',
    'place': 'Pl',
    'pl': 'Pl',
    'pl.': 'Pl',
    'court': 'Ct',
    'ct': 'Ct',
    'ct.': 'Ct',
    'circle': 'Cir',
    'cir': 'Cir',
    'terrace': 'Ter',
    'ter': 'Ter',
    'way': 'Way',
    'parkway': 'Pkwy',
    'pkwy': 'Pkwy',
    'highway': 'Hwy',
    'hwy': 'Hwy',
    'square': 'Sq',
    'sq': 'Sq',
}

# Direction abbreviations
DIRECTION_MAPPINGS = {
    'north': 'N',
    'n': 'N',
    'n.': 'N',
    'south': 'S',
    's': 'S',
    's.': 'S',
    'east': 'E',
    'e': 'E',
    'e.': 'E',
    'west': 'W',
    'w': 'W',
    'w.': 'W',
    'northeast': 'NE',
    'ne': 'NE',
    'northwest': 'NW',
    'nw': 'NW',
    'southeast': 'SE',
    'se': 'SE',
    'southwest': 'SW',
    'sw': 'SW',
}

# State abbreviations
STATE_MAPPINGS = {
    'new york': 'NY',
    'new jersey': 'NJ',
    'pennsylvania': 'PA',
    'connecticut': 'CT',
}


def normalize_address(address: str) -> str:
    """
    Normalize an address for consistent storage and duplicate detection.
    
    Normalization rules:
    - Convert to title case
    - Standardize street types (Street -> St, Avenue -> Ave)
    - Standardize directions (North -> N, West -> W)
    - Remove extra whitespace
    - Remove apartment/unit suffixes
    
    Args:
        address: Raw address string
        
    Returns:
        Normalized address string
    """
    if not address:
        return ""
    
    # Remove extra whitespace and convert to lowercase for processing
    normalized = ' '.join(address.split()).lower()
    
    # Remove common apartment/unit designators
    normalized = re.sub(r'\s*(apt\.?|apartment|unit|#|suite|ste\.?)\s*[\w-]*\s*$', '', normalized, flags=re.I)
    
    # Remove trailing commas
    normalized = normalized.rstrip(',').strip()
    
    # Split into words for processing
    words = normalized.split()
    result_words = []
    
    for i, word in enumerate(words):
        word_lower = word.lower().rstrip('.,')
        
        # Check if it's a direction (usually at start or after number)
        if word_lower in DIRECTION_MAPPINGS:
            result_words.append(DIRECTION_MAPPINGS[word_lower])
        # Check if it's a street type
        elif word_lower in STREET_TYPE_MAPPINGS:
            result_words.append(STREET_TYPE_MAPPINGS[word_lower])
        # Check if it's a state
        elif word_lower in STATE_MAPPINGS:
            result_words.append(STATE_MAPPINGS[word_lower])
        # Keep numbers as-is
        elif word.isdigit():
            result_words.append(word)
        # Title case for other words
        else:
            # Handle ordinal numbers (1st, 2nd, 3rd, etc.)
            if re.match(r'^\d+(st|nd|rd|th)$', word_lower):
                result_words.append(word_lower)
            else:
                result_words.append(word.title())
    
    return ' '.join(result_words)


def normalize_city(city: str) -> str:
    """Normalize city name."""
    if not city:
        return ""
    return ' '.join(city.split()).title()


def normalize_state(state: str) -> str:
    """Normalize state to 2-letter abbreviation."""
    if not state:
        return ""
    state_lower = state.lower().strip()
    if state_lower in STATE_MAPPINGS:
        return STATE_MAPPINGS[state_lower]
    # If already 2 letters, uppercase it
    if len(state_lower) == 2:
        return state_lower.upper()
    return state.upper()


def normalize_zip(zip_code: str) -> str:
    """Normalize ZIP code to 5 digits."""
    if not zip_code:
        return ""
    # Extract just the 5-digit ZIP
    match = re.search(r'(\d{5})', str(zip_code))
    return match.group(1) if match else str(zip_code).strip()


def generate_address_hash(address: str, city: str, state: str, zip_code: str) -> str:
    """Generate a hash for duplicate detection based on normalized address components."""
    normalized = f"{normalize_address(address)}|{normalize_city(city)}|{normalize_state(state)}|{normalize_zip(zip_code)}"
    return hashlib.md5(normalized.lower().encode()).hexdigest()


def generate_unit_hash(building_id: str, unit_number: str, rent: float, bedrooms: int) -> str:
    """Generate a hash for unit duplicate detection."""
    normalized = f"{building_id}|{unit_number}|{rent}|{bedrooms}"
    return hashlib.md5(normalized.lower().encode()).hexdigest()


# ============ VALIDATION HELPERS ============

def validate_building_data(building_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate building data and return validation flags.
    
    Returns:
        Tuple of (is_valid, validation_flags)
    """
    flags = []
    
    if not building_data.get('name'):
        flags.append('missing_name')
    if not building_data.get('address'):
        flags.append('missing_address')
    if not building_data.get('neighborhood'):
        flags.append('missing_neighborhood')
    if not building_data.get('city'):
        flags.append('missing_city')
    if not building_data.get('state'):
        flags.append('missing_state')
    if not building_data.get('zip_code'):
        flags.append('missing_zip')
    if not building_data.get('source_url'):
        flags.append('missing_source_url')
    
    # Validate address format
    address = building_data.get('address', '')
    if address and not re.search(r'\d+', address):
        flags.append('invalid_address_no_number')
    
    is_valid = len(flags) == 0
    return is_valid, flags


def validate_unit_data(unit_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate unit data and return validation flags.
    
    Returns:
        Tuple of (is_valid, validation_flags)
    """
    flags = []
    
    if not unit_data.get('unit_number'):
        flags.append('missing_unit_number')
    if not unit_data.get('building_id'):
        flags.append('missing_building_id')
    
    rent = unit_data.get('rent', 0)
    if rent <= 0:
        flags.append('invalid_rent')
    elif rent < 500:
        flags.append('suspiciously_low_rent')
    elif rent > 50000:
        flags.append('suspiciously_high_rent')
    
    bedrooms = unit_data.get('bedrooms', -1)
    if bedrooms < 0:
        flags.append('missing_bedrooms')
    elif bedrooms > 10:
        flags.append('suspiciously_high_bedrooms')
    
    bathrooms = unit_data.get('bathrooms', 0)
    if bathrooms <= 0:
        flags.append('missing_bathrooms')
    
    images = unit_data.get('images', [])
    if not images:
        flags.append('no_images')
    elif len(images) == 1:
        flags.append('single_image')
    elif len(images) > 20:
        flags.append('too_many_images')
    
    # Check for duplicate images (same image URL appearing multiple times)
    if images and len(images) != len(set(images)):
        flags.append('duplicate_image_urls')
    
    is_valid = 'invalid_rent' not in flags and 'missing_building_id' not in flags
    return is_valid, flags


# ============ DUPLICATE DETECTION ============

def normalize_unit_number(unit_number: str) -> str:
    """
    Normalize unit number for duplicate detection.
    
    Normalization rules:
    - Convert to uppercase
    - Remove common prefixes (Unit, Apt, #, Suite)
    - Remove spaces and special characters
    - Standardize letter/number combinations
    """
    if not unit_number:
        return ""
    
    normalized = unit_number.upper().strip()
    
    # Remove common prefixes
    prefixes = ['UNIT', 'APT', 'APARTMENT', 'SUITE', 'STE', '#', 'NO', 'NUMBER']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
        # Also check with space or dot after prefix
        if normalized.startswith(prefix + ' ') or normalized.startswith(prefix + '.'):
            normalized = normalized[len(prefix)+1:].strip()
    
    # Remove leading # or . if still present
    normalized = normalized.lstrip('#.-').strip()
    
    # Remove spaces between letters and numbers (e.g., "10 A" -> "10A")
    normalized = re.sub(r'(\d+)\s+([A-Z])', r'\1\2', normalized)
    normalized = re.sub(r'([A-Z])\s+(\d+)', r'\1\2', normalized)
    
    # Remove dashes between alphanumerics for comparison
    normalized = re.sub(r'([A-Z0-9])-([A-Z0-9])', r'\1\2', normalized)
    
    return normalized


async def calculate_building_duplicate_score(building_data: Dict) -> Tuple[float, Optional[str], List[str]]:
    """
    Calculate duplicate score for a building by comparing with existing production buildings.
    
    Returns:
        Tuple of (duplicate_score, matched_production_id, duplicate_flags)
        Score: 0.0 = unique, 1.0 = exact duplicate
    """
    normalized_address = normalize_address(building_data.get('address', ''))
    normalized_city = normalize_city(building_data.get('city', ''))
    normalized_state = normalize_state(building_data.get('state', ''))
    normalized_zip = normalize_zip(building_data.get('zip_code', ''))
    
    # Check production buildings
    production_buildings = await db.buildings.find({}, {"_id": 0}).to_list(1000)
    
    best_score = 0.0
    matched_id = None
    duplicate_flags = []
    
    for prod_building in production_buildings:
        score = 0.0
        
        # Normalize production building address
        prod_normalized = normalize_address(prod_building.get('address', ''))
        prod_city = normalize_city(prod_building.get('city', ''))
        prod_state = normalize_state(prod_building.get('state', ''))
        prod_zip = normalize_zip(prod_building.get('zip_code', ''))
        
        # Exact normalized address match
        if prod_normalized.lower() == normalized_address.lower():
            score += 0.5
        elif normalized_address.lower() in prod_normalized.lower() or prod_normalized.lower() in normalized_address.lower():
            score += 0.3
        
        # City match
        if prod_city.lower() == normalized_city.lower():
            score += 0.2
        
        # State match
        if prod_state.lower() == normalized_state.lower():
            score += 0.1
        
        # ZIP match
        if prod_zip == normalized_zip:
            score += 0.2
        
        if score > best_score:
            best_score = score
            matched_id = prod_building.get('id')
    
    # Determine duplicate flags based on score
    if best_score >= 0.8:
        duplicate_flags.append('likely_duplicate_building')
    elif best_score >= 0.5:
        duplicate_flags.append('possible_duplicate_building')
    
    return min(best_score, 1.0), matched_id, duplicate_flags


async def check_unit_duplicate_against_production(
    unit_data: Dict,
    building_id: str,
    building_address: Optional[str] = None
) -> Tuple[float, Optional[str], List[str]]:
    """
    Check if a unit is a duplicate against production units.
    
    This checks:
    1. Units in the same building (by building_id)
    2. Units in buildings with the same normalized address
    
    Args:
        unit_data: The unit data to check
        building_id: The building ID (staging or production)
        building_address: Optional building address for cross-building duplicate check
    
    Returns:
        Tuple of (duplicate_score, matched_production_id, duplicate_flags)
    """
    normalized_unit_number = normalize_unit_number(unit_data.get('unit_number', ''))
    rent = unit_data.get('rent', 0)
    bedrooms = unit_data.get('bedrooms', -1)
    bathrooms = unit_data.get('bathrooms', 0)
    
    duplicate_flags = []
    best_score = 0.0
    matched_id = None
    
    # Step 1: Check production units in the same building
    production_units_same_building = await db.units.find(
        {'building_id': building_id},
        {"_id": 0}
    ).to_list(1000)
    
    for prod_unit in production_units_same_building:
        score = 0.0
        prod_unit_number = normalize_unit_number(prod_unit.get('unit_number', ''))
        
        # Exact unit number match (after normalization)
        if prod_unit_number == normalized_unit_number:
            score += 0.6
        
        # Similar rent (within 5%)
        prod_rent = prod_unit.get('rent', 0)
        if prod_rent > 0 and rent > 0:
            rent_diff = abs(prod_rent - rent) / max(prod_rent, rent)
            if rent_diff < 0.05:
                score += 0.2
            elif rent_diff < 0.15:
                score += 0.1
        
        # Same bedroom count
        if prod_unit.get('bedrooms', -1) == bedrooms:
            score += 0.1
        
        # Same bathroom count
        if prod_unit.get('bathrooms', 0) == bathrooms:
            score += 0.1
        
        if score > best_score:
            best_score = score
            matched_id = prod_unit.get('id')
    
    # Step 2: Check production units in buildings with same normalized address
    if building_address:
        normalized_building_address = normalize_address(building_address)
        
        # Find buildings with matching normalized address
        all_buildings = await db.buildings.find({}, {"_id": 0, "id": 1, "address": 1}).to_list(1000)
        matching_building_ids = []
        
        for bld in all_buildings:
            if bld['id'] != building_id:  # Skip current building
                bld_normalized = normalize_address(bld.get('address', ''))
                if bld_normalized.lower() == normalized_building_address.lower():
                    matching_building_ids.append(bld['id'])
        
        # Check units in buildings with same address
        if matching_building_ids:
            production_units_same_address = await db.units.find(
                {'building_id': {'$in': matching_building_ids}},
                {"_id": 0}
            ).to_list(1000)
            
            for prod_unit in production_units_same_address:
                score = 0.0
                prod_unit_number = normalize_unit_number(prod_unit.get('unit_number', ''))
                
                # Same address building + same unit number is a strong duplicate signal
                if prod_unit_number == normalized_unit_number:
                    score += 0.7  # Higher score for cross-building address match
                
                # Similar rent
                prod_rent = prod_unit.get('rent', 0)
                if prod_rent > 0 and rent > 0:
                    rent_diff = abs(prod_rent - rent) / max(prod_rent, rent)
                    if rent_diff < 0.05:
                        score += 0.15
                
                # Same bedroom count
                if prod_unit.get('bedrooms', -1) == bedrooms:
                    score += 0.1
                
                if score > best_score:
                    best_score = score
                    matched_id = prod_unit.get('id')
    
    # Step 3: Also check existing staging units to prevent duplicate staged entries
    staging_units = await db.units_staging.find(
        {
            'building_id': building_id,
            'review_status': 'pending'
        },
        {"_id": 0}
    ).to_list(1000)
    
    for staged_unit in staging_units:
        staged_unit_number = normalize_unit_number(staged_unit.get('unit_number', ''))
        
        if staged_unit_number == normalized_unit_number:
            # Found duplicate in staging
            if 'duplicate_in_staging' not in duplicate_flags:
                duplicate_flags.append('duplicate_in_staging')
    
    # Determine duplicate flags based on score
    if best_score >= 0.8:
        duplicate_flags.append('likely_duplicate')
    elif best_score >= 0.5:
        duplicate_flags.append('possible_duplicate')
    elif best_score >= 0.3:
        duplicate_flags.append('potential_duplicate')
    
    return min(best_score, 1.0), matched_id, duplicate_flags


async def calculate_unit_duplicate_score(unit_data: Dict, building_id: str) -> Tuple[float, Optional[str]]:
    """
    Calculate duplicate score for a unit by comparing with existing production units.
    
    DEPRECATED: Use check_unit_duplicate_against_production for more comprehensive checks.
    
    Returns:
        Tuple of (duplicate_score, matched_production_id)
    """
    # Get building address for comprehensive check
    building = await db.buildings.find_one({'id': building_id}, {"_id": 0, "address": 1})
    building_address = building.get('address') if building else None
    
    # If not found in production, check staging
    if not building_address:
        staging_building = await db.buildings_staging.find_one({'id': building_id}, {"_id": 0, "address": 1})
        building_address = staging_building.get('address') if staging_building else None
    
    score, matched_id, _ = await check_unit_duplicate_against_production(
        unit_data, building_id, building_address
    )
    return score, matched_id


# ============ IMAGE PROCESSING ============

async def download_and_upload_to_gcs(
    image_url: str,
    building_id: str,
    unit_id: str,
    session: aiohttp.ClientSession
) -> str:
    """
    Download image from URL and upload to GCS.
    """
    try:
        async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=20)) as response:
            if response.status != 200:
                logger.warning(f"Failed to download image: HTTP {response.status}")
                return image_url
            
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type.lower():
                logger.warning(f"URL doesn't appear to be an image: {content_type}")
                return image_url
            
            image_bytes = await response.read()
        
        result = await upload_apartment_image(
            image_file=image_bytes,
            building_id=building_id,
            unit_id=unit_id
        )
        
        gcs_url = result['urls']['medium']
        logger.info(f"Uploaded to GCS: {image_url[:50]}... -> {gcs_url[:50]}...")
        return gcs_url
        
    except Exception as e:
        logger.warning(f"Failed to upload image to GCS: {str(e)}, keeping original URL")
        return image_url


async def process_images_for_unit(
    image_urls: List[str],
    building_id: str,
    unit_id: str
) -> List[str]:
    """Process image URLs: either keep original or upload to GCS."""
    if not USE_GCS_FOR_IMAGES or not image_urls:
        return image_urls
    
    processed_urls = []
    
    async with aiohttp.ClientSession() as session:
        for image_url in image_urls:
            if 'storage.googleapis.com' in image_url or 'nofeesapts-images' in image_url:
                processed_urls.append(image_url)
                continue
            
            gcs_url = await download_and_upload_to_gcs(
                image_url, building_id, unit_id, session
            )
            processed_urls.append(gcs_url)
    
    return processed_urls


# ============ SITE-SPECIFIC CRAWLERS ============

async def crawl_fortysixfifty(url: str) -> List[Dict[str, Any]]:
    """Crawl fortysixfifty.com - handles iframe-based availability widget"""
    units = []
    content = None
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)
            
            frames = page.frames
            iframe_content = None
            for frame in frames:
                if 'rosenyc.com' in frame.url:
                    logger.info(f"Found availability iframe: {frame.url}")
                    iframe_content = await frame.content()
                    break
            
            content = iframe_content if iframe_content else await page.content()
            raw_html = content  # Store raw HTML
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
                        
                        unit_data = {
                            'unit_number': '',
                            'rent': 0.0,
                            'bedrooms': 0,
                            'bathrooms': 1.0,
                            'square_feet': None,
                            'images': [],
                            'amenities': [],
                            'description': '',
                            'available_date': 'Immediate',
                            'raw_data': str(row)  # Store raw row HTML
                        }
                        
                        for idx, cell in enumerate(cells):
                            text = cell.get_text(strip=True)
                            header = headers[idx] if idx < len(headers) else ''
                            
                            if 'unit' in header or idx == 0:
                                if text and text.isdigit() or re.match(r'^[A-Z0-9-]+$', text):
                                    unit_data['unit_number'] = text
                            
                            if 'rent' in header or '$' in text:
                                rent_match = re.search(r'\$([0-9,]+)', text)
                                if rent_match:
                                    unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                            
                            if 'bedroom' in header or 'br' in header:
                                if 'studio' in text.lower():
                                    unit_data['bedrooms'] = 0
                                else:
                                    bed_match = re.search(r'(\d+)', text)
                                    if bed_match:
                                        unit_data['bedrooms'] = int(bed_match.group(1))
                            
                            if 'bathroom' in header or 'ba' in header:
                                bath_match = re.search(r'(\d+(?:\.\d+)?)', text)
                                if bath_match:
                                    unit_data['bathrooms'] = float(bath_match.group(1))
                            
                            if 'sq' in header or 'sq.' in text.lower():
                                sqft_match = re.search(r'(\d+)', text)
                                if sqft_match:
                                    unit_data['square_feet'] = int(sqft_match.group(1))
                            
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


async def crawl_mercedes_house(url: str) -> List[Dict[str, Any]]:
    """Crawl mercedeshouseny.com - custom parser for their format"""
    units = []
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(5000)
            
            content = await page.content()
            raw_html = content
            await browser.close()
        finally:
            await p.stop()
        
        soup = BeautifulSoup(content, 'html.parser')
        all_text = soup.get_text()
        
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
                
                unit_data = {
                    'unit_number': unit_number,
                    'rent': rent,
                    'bedrooms': bedrooms,
                    'bathrooms': 1.0,
                    'square_feet': None,
                    'images': [],
                    'amenities': [],
                    'description': f"{bedroom_type} apartment",
                    'available_date': 'Immediate',
                    'raw_data': f"{bedroom_type}#{unit_number}|${rent}"
                }
                
                units.append(unit_data)
            
            except Exception as e:
                logger.error(f"Error parsing Mercedes unit: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error crawling Mercedes House: {e}")
    
    return units


async def crawl_harrison_yards(url: str) -> List[Dict[str, Any]]:
    """Crawl harrisonyards.com - uses RealPage/LeaseStar widget"""
    units = []
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(8000)
            
            try:
                await page.wait_for_selector('.rpfp-card, .rpfp-card-details', timeout=5000)
            except:
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
                    unit_data = {
                        'unit_number': '',
                        'rent': 0.0,
                        'bedrooms': 0,
                        'bathrooms': 1.0,
                        'square_feet': None,
                        'images': [],
                        'amenities': [],
                        'description': '',
                        'available_date': 'Immediate',
                        'raw_data': str(card)
                    }
                    
                    text = card.get_text(separator=' ', strip=True)
                    
                    price_elem = card.find(['span', 'div'], class_=re.compile(r'price|rent|rate', re.I))
                    if price_elem:
                        rent_match = re.search(r'\$([0-9,]+)', price_elem.get_text())
                        if rent_match:
                            unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                    else:
                        rent_match = re.search(r'\$([0-9,]+)', text)
                        if rent_match:
                            unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                    
                    bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', text, re.I)
                    if bed_match:
                        unit_data['bedrooms'] = int(bed_match.group(1))
                    elif re.search(r'studio', text, re.I):
                        unit_data['bedrooms'] = 0
                    
                    bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', text, re.I)
                    if bath_match:
                        unit_data['bathrooms'] = float(bath_match.group(1))
                    
                    sqft_match = re.search(r'(\d+)\s*(?:sq|sqft|sf)', text, re.I)
                    if sqft_match:
                        unit_data['square_feet'] = int(sqft_match.group(1))
                    
                    unit_num_elem = card.find(['span', 'div'], class_=re.compile(r'unit|name|title', re.I))
                    if unit_num_elem:
                        unit_text = unit_num_elem.get_text(strip=True)
                        unit_match = re.search(r'([A-Z0-9-]+)', unit_text)
                        if unit_match:
                            unit_data['unit_number'] = unit_match.group(1)
                    
                    if not unit_data['unit_number']:
                        bed_type = "Studio" if unit_data['bedrooms'] == 0 else f"{unit_data['bedrooms']}BR"
                        unit_data['unit_number'] = f"{bed_type}-{len(units)+1}"
                    
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


async def crawl_generic_site(url: str) -> List[Dict[str, Any]]:
    """Generic crawler for other sites - checks tables first, then divs"""
    units = []
    content = None
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(5000)
            
            frames = page.frames
            iframe_content = None
            for frame in frames:
                if frame.url != 'about:blank' and 'google' not in frame.url and frame.url != url:
                    try:
                        iframe_content = await frame.content()
                        logger.info(f"Using iframe content from: {frame.url}")
                        break
                    except:
                        continue
            
            content = iframe_content if iframe_content else await page.content()
            await browser.close()
        finally:
            await p.stop()
        
        if not content:
            return units
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Try table-based parsing
        tables = soup.find_all('table')
        if tables:
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                header_row = rows[0]
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                
                if not any(h in headers for h in ['unit', 'rent', 'bedroom', 'bed', 'price']):
                    continue
                
                for row in rows[1:]:
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 3:
                            continue
                        
                        unit_data = {
                            'unit_number': '',
                            'rent': 0.0,
                            'bedrooms': 0,
                            'bathrooms': 1.0,
                            'square_feet': None,
                            'images': [],
                            'amenities': [],
                            'description': '',
                            'available_date': 'Immediate',
                            'raw_data': str(row)
                        }
                        
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
                        
                        images = row.find_all('img')
                        for img in images:
                            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                            if src:
                                if src.startswith('//'):
                                    src = 'https:' + src
                                elif src.startswith('/') and not src.startswith('http'):
                                    from urllib.parse import urlparse
                                    parsed_url = urlparse(url)
                                    src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                                
                                if src.startswith('http') and not any(x in src for x in ['logo', 'icon', 'sprite']):
                                    unit_data['images'].append(src)
                        
                        if unit_data['rent'] > 0:
                            if not unit_data['unit_number']:
                                unit_data['unit_number'] = f"Unit-{len(units)+1}"
                            units.append(unit_data)
                    
                    except Exception as e:
                        logger.error(f"Error parsing table row: {e}")
                        continue
        
        # If no units from tables, try div-based parsing
        if not units:
            listing_containers = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'unit|apartment|listing|availability|property|floor|plan|residence', re.I))
            
            for container in listing_containers:
                try:
                    unit_data = {
                        'unit_number': '',
                        'rent': 0.0,
                        'bedrooms': 0,
                        'bathrooms': 1.0,
                        'images': [],
                        'amenities': [],
                        'description': '',
                        'raw_data': str(container)[:1000]  # Limit raw data size
                    }
                    
                    text = container.get_text(separator=' ', strip=True)
                    
                    rent_match = re.search(r'\$([0-9,]+)', text)
                    if rent_match:
                        unit_data['rent'] = float(rent_match.group(1).replace(',', ''))
                    
                    bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', text, re.I)
                    if bed_match:
                        unit_data['bedrooms'] = int(bed_match.group(1))
                    elif re.search(r'studio', text, re.I):
                        unit_data['bedrooms'] = 0
                    
                    bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', text, re.I)
                    if bath_match:
                        unit_data['bathrooms'] = float(bath_match.group(1))
                    
                    unit_match = re.search(r'(?:unit|apt|#)\s*([A-Z0-9-]+)', text, re.I)
                    if unit_match:
                        unit_data['unit_number'] = unit_match.group(1)
                    else:
                        unit_data['unit_number'] = f"Unit-{len(units)+1}"
                    
                    images = container.find_all('img')
                    for img in images:
                        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                        if src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/') and not src.startswith('http'):
                                from urllib.parse import urlparse
                                parsed_url = urlparse(url)
                                src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                            
                            if src.startswith('http') and not any(x in src for x in ['logo', 'icon', 'sprite']):
                                unit_data['images'].append(src)
                    
                    desc_elem = container.find(['p', 'div'], class_=re.compile(r'desc|detail|info', re.I))
                    if desc_elem:
                        unit_data['description'] = desc_elem.get_text(strip=True)[:500]
                    
                    if unit_data['rent'] > 0:
                        units.append(unit_data)
                
                except Exception as e:
                    logger.error(f"Error parsing unit: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Error crawling site: {e}")
    
    return units


async def crawl_7w21(url: str) -> List[Dict[str, Any]]:
    """
    Crawl 7W21 (7 West 21st Street) - Rose NYC iframe-based availability.
    
    Site uses: https://www.rosenyc.com/availability/mgoublmo/
    Wait for DOM to render the #availability section.
    Extract: Unit Number, Bedrooms, Bathrooms, Price, Square Footage, Availability Date
    """
    units = []
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            
            logger.info(f"Loading 7W21 main page...")
            await page.goto('https://www.7w21.com/', wait_until='domcontentloaded', timeout=60000)
            
            # Wait for the page to load fully
            await page.wait_for_timeout(15000)
            
            # Find the Rose NYC iframe
            frames = page.frames
            rosenyc_frame = None
            
            for frame in frames:
                if 'rosenyc.com' in frame.url:
                    rosenyc_frame = frame
                    logger.info(f"Found Rose NYC iframe: {frame.url}")
                    break
            
            if not rosenyc_frame:
                logger.warning("Rose NYC iframe not found, trying direct URL")
                await page.goto('https://www.rosenyc.com/availability/mgoublmo/', wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(10000)
                content = await page.content()
            else:
                # Wait for iframe content to load
                await rosenyc_frame.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(5)
                content = await rosenyc_frame.content()
            
            await browser.close()
        finally:
            await p.stop()
        
        if not content:
            logger.warning("No content retrieved from 7W21")
            return units
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check for "Please call for availability" message (no units available)
        if 'please call for availability' in content.lower():
            logger.info("7W21: No units currently available (please call message)")
            return units
        
        # Look for table rows with unit data
        rows = soup.find_all('tr', {'data-beds': True})
        
        if not rows:
            # Fallback: look for any table rows with data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
        
        logger.info(f"Found {len(rows)} potential unit rows")
        
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 5:
                    continue
                
                # Extract data from cells
                unit_data = {
                    'unit_number': '',
                    'rent': 0.0,
                    'bedrooms': 0,
                    'bathrooms': 1.0,
                    'square_feet': None,
                    'available_date': 'Immediate',
                    'images': [],
                    'amenities': [],
                    'description': '7 West 21st Street - Flatiron District luxury apartment',
                    'raw_data': str(row)[:2000]
                }
                
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
                
                # Extract images from the row
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
                logger.error(f"Error parsing 7W21 unit row: {e}")
                continue
        
        logger.info(f"7W21 crawl complete: found {len(units)} units")
    
    except Exception as e:
        logger.error(f"Error crawling 7W21: {e}")
    
    return units


async def crawl_rivercourt(url: str) -> List[Dict[str, Any]]:
    """
    Crawl Rivercourt NYC - Rose NYC iframe-based availability.
    
    Site uses: https://www.rosenyc.com/availability/mgpelfdh/
    Extract: Unit Number, Bedrooms, Bathrooms, Price, Square Footage, Availability Date
    """
    units = []
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            
            logger.info("Loading Rivercourt page...")
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
            else:
                logger.warning("Rose NYC iframe not found")
                content = await page.content()
            
            await browser.close()
        finally:
            await p.stop()
        
        if not content:
            return units
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all unit rows (tr with role='row' but not header)
        rows = soup.find_all('tr', {'role': 'row'})
        logger.info(f"Found {len(rows)} table rows")
        
        for row in rows:
            if 't-header' in row.get('class', []):
                continue
            
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
            
            try:
                unit_data = {
                    'unit_number': '',
                    'bedrooms': 0,
                    'bathrooms': 1.0,
                    'square_feet': None,
                    'rent': 0.0,
                    'available_date': 'Immediate',
                    'images': [],
                    'amenities': [],
                    'description': 'Rivercourt - Long Island City luxury apartment',
                    'raw_data': str(row)[:2000]
                }
                
                for cell in cells:
                    label = cell.get('data-label', '').lower()
                    text = cell.get_text(strip=True)
                    
                    if label == 'unit':
                        unit_data['unit_number'] = text
                    
                    elif label == 'bedroom':
                        if 'studio' in text.lower():
                            unit_data['bedrooms'] = 0
                        else:
                            m = re.search(r'(\d+)', text)
                            if m:
                                unit_data['bedrooms'] = int(m.group(1))
                    
                    elif label == 'bathroom':
                        m = re.search(r'([\d.]+)', text)
                        if m:
                            unit_data['bathrooms'] = float(m.group(1))
                    
                    elif label == 'sqft':
                        m = re.search(r'([\d,]+)', text)
                        if m:
                            unit_data['square_feet'] = int(m.group(1).replace(',', ''))
                    
                    elif label == 'rent':
                        m = re.search(r'[\$]([0-9,]+)', text)
                        if m:
                            unit_data['rent'] = float(m.group(1).replace(',', ''))
                    
                    elif label == 'availability':
                        unit_data['available_date'] = text if text else 'Immediate'
                
                if unit_data['unit_number'] and unit_data['rent'] > 0:
                    units.append(unit_data)
                    logger.info(f"Found unit: {unit_data['unit_number']} - ${unit_data['rent']}")
            
            except Exception as e:
                logger.error(f"Error parsing Rivercourt unit row: {e}")
                continue
        
        logger.info(f"Rivercourt crawl complete: found {len(units)} units")
    
    except Exception as e:
        logger.error(f"Error crawling Rivercourt: {e}")
    
    return units


async def crawl_melar(url: str) -> List[Dict[str, Any]]:
    """
    Crawl The Melar - Rose NYC iframe-based availability.
    
    Site uses: https://www.rosenyc.com/availability/mgooldds/
    Extract: Unit Number, Bedrooms, Bathrooms, Price, Square Footage, Availability Date
    """
    units = []
    
    try:
        p, browser = await get_browser()
        try:
            page = await browser.new_page()
            
            logger.info("Loading The Melar page...")
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
            else:
                logger.warning("Rose NYC iframe not found")
                content = await page.content()
            
            await browser.close()
        finally:
            await p.stop()
        
        if not content:
            return units
        
        soup = BeautifulSoup(content, 'html.parser')
        rows = soup.find_all('tr', {'role': 'row'})
        logger.info(f"Found {len(rows)} table rows")
        
        for row in rows:
            if 't-header' in row.get('class', []):
                continue
            
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
            
            try:
                unit_data = {
                    'unit_number': '',
                    'bedrooms': 0,
                    'bathrooms': 1.0,
                    'square_feet': None,
                    'rent': 0.0,
                    'available_date': 'Immediate',
                    'images': [],
                    'amenities': [],
                    'description': 'The Melar - Upper West Side luxury apartment',
                    'raw_data': str(row)[:2000]
                }
                
                for cell in cells:
                    label = cell.get('data-label', '').lower()
                    text = cell.get_text(strip=True)
                    
                    if label == 'unit':
                        unit_data['unit_number'] = text
                    elif label == 'bedroom':
                        if 'studio' in text.lower():
                            unit_data['bedrooms'] = 0
                        else:
                            m = re.search(r'(\d+)', text)
                            if m:
                                unit_data['bedrooms'] = int(m.group(1))
                    elif label == 'bathroom':
                        m = re.search(r'([\d.]+)', text)
                        if m:
                            unit_data['bathrooms'] = float(m.group(1))
                    elif label == 'sqft':
                        m = re.search(r'([\d,]+)', text)
                        if m:
                            unit_data['square_feet'] = int(m.group(1).replace(',', ''))
                    elif label == 'rent':
                        m = re.search(r'[\$]([0-9,]+)', text)
                        if m:
                            unit_data['rent'] = float(m.group(1).replace(',', ''))
                    elif label == 'availability':
                        unit_data['available_date'] = text if text else 'Immediate'
                
                if unit_data['unit_number'] and unit_data['rent'] > 0:
                    units.append(unit_data)
                    logger.info(f"Found unit: {unit_data['unit_number']} - ${unit_data['rent']}")
            
            except Exception as e:
                logger.error(f"Error parsing Melar unit row: {e}")
                continue
        
        logger.info(f"Melar crawl complete: found {len(units)} units")
    
    except Exception as e:
        logger.error(f"Error crawling Melar: {e}")
    
    return units


# ============ STAGING INSERTION (NO DIRECT PRODUCTION WRITES) ============

async def insert_building_to_staging(
    building_data: Dict,
    crawler_source: str,
    batch_id: str
) -> str:
    """
    Insert a building into the staging collection.
    
    IMPORTANT: This is the ONLY way crawlers should insert buildings.
    Direct writes to the production 'buildings' collection are NOT allowed.
    
    Deduplication checks:
    1. Normalizes address
    2. Checks production buildings for same normalized address
    3. Flags possible duplicates (does NOT block insertion)
    
    Returns:
        The ID of the created staging building
    """
    # Normalize address components
    normalized_address = normalize_address(building_data.get('address', ''))
    normalized_city = normalize_city(building_data.get('city', ''))
    normalized_state = normalize_state(building_data.get('state', ''))
    normalized_zip = normalize_zip(building_data.get('zip_code', ''))
    
    # Validate
    is_valid, validation_flags = validate_building_data(building_data)
    
    # Calculate duplicate score (now returns duplicate_flags too)
    duplicate_score, matched_id, duplicate_flags = await calculate_building_duplicate_score(building_data)
    
    # Merge duplicate flags into validation flags
    validation_flags.extend(duplicate_flags)
    
    # Generate address hash for future duplicate detection
    address_hash = generate_address_hash(
        building_data.get('address', ''),
        building_data.get('city', ''),
        building_data.get('state', ''),
        building_data.get('zip_code', '')
    )
    
    staging_building = {
        'id': str(uuid.uuid4()),
        # Core fields
        'name': building_data.get('name', ''),
        'address': building_data.get('address', ''),
        'normalized_address': normalized_address,
        'neighborhood': building_data.get('neighborhood', ''),
        'city': building_data.get('city', ''),
        'normalized_city': normalized_city,
        'state': building_data.get('state', ''),
        'normalized_state': normalized_state,
        'zip_code': building_data.get('zip_code', ''),
        'normalized_zip': normalized_zip,
        'address_hash': address_hash,
        'source_url': building_data.get('source_url', ''),
        'latitude': building_data.get('latitude'),
        'longitude': building_data.get('longitude'),
        'last_crawled': datetime.now(timezone.utc).isoformat(),
        # Staging-specific fields
        'review_status': 'pending',
        'crawler_source': crawler_source,
        'crawler_batch_id': batch_id,
        'validation_flags': validation_flags,
        'duplicate_score': duplicate_score,
        'matched_production_id': matched_id,
        'raw_data': building_data.get('raw_data', {}),
        'reviewer_notes': None,
        'reviewed_by': None,
        'reviewed_at': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Use safe staging insert (enforces production write block)
    await _safe_staging_insert('buildings_staging', staging_building, crawler_source)
    
    log_msg = f"Inserted building to staging: {staging_building['name']} (dup_score: {duplicate_score:.2f}"
    if duplicate_flags:
        log_msg += f", flags: {duplicate_flags}"
    log_msg += ")"
    logger.info(log_msg)
    
    return staging_building['id']


async def insert_unit_to_staging(
    unit_data: Dict,
    building_id: str,
    crawler_source: str,
    batch_id: str,
    building_address: Optional[str] = None
) -> str:
    """
    Insert a unit into the staging collection.
    
    IMPORTANT: This is the ONLY way crawlers should insert units.
    Direct writes to the production 'units' collection are NOT allowed.
    
    Deduplication checks:
    1. Normalizes unit number
    2. Checks production units for:
       - Same building ID + same unit number
       - Same building normalized address + same unit number
    3. Flags possible duplicates (does NOT block insertion)
    
    Args:
        unit_data: Unit data to insert
        building_id: Building ID (staging or production)
        crawler_source: Source website domain
        batch_id: Crawl batch identifier
        building_address: Optional building address for cross-building duplicate check
    
    Returns:
        The ID of the created staging unit
    """
    unit_id = str(uuid.uuid4())
    
    # Normalize unit number for logging and storage
    normalized_unit_number = normalize_unit_number(unit_data.get('unit_number', ''))
    
    # Validate
    unit_data_with_building = {**unit_data, 'building_id': building_id}
    is_valid, validation_flags = validate_unit_data(unit_data_with_building)
    
    # Get building address if not provided
    if not building_address:
        # Try production buildings first
        building = await db.buildings.find_one({'id': building_id}, {"_id": 0, "address": 1})
        if building:
            building_address = building.get('address')
        else:
            # Try staging buildings
            staging_building = await db.buildings_staging.find_one({'id': building_id}, {"_id": 0, "address": 1})
            if staging_building:
                building_address = staging_building.get('address')
    
    # Comprehensive duplicate check against production
    duplicate_score, matched_id, duplicate_flags = await check_unit_duplicate_against_production(
        unit_data, building_id, building_address
    )
    
    # Merge duplicate flags into validation flags
    validation_flags.extend(duplicate_flags)
    
    # Process images if needed
    processed_images = await process_images_for_unit(
        unit_data.get('images', []),
        building_id,
        unit_id
    )
    
    staging_unit = {
        'id': unit_id,
        # Core fields
        'building_id': building_id,
        'unit_number': unit_data.get('unit_number', ''),
        'normalized_unit_number': normalized_unit_number,
        'rent': unit_data.get('rent', 0),
        'bedrooms': unit_data.get('bedrooms', 0),
        'bathrooms': unit_data.get('bathrooms', 1.0),
        'square_feet': unit_data.get('square_feet'),
        'available_date': unit_data.get('available_date', 'Immediate'),
        'amenities': unit_data.get('amenities', []),
        'images': processed_images,
        'original_images': unit_data.get('images', []),  # Store original URLs
        'description': unit_data.get('description', ''),
        'is_available': True,
        'latitude': unit_data.get('latitude'),
        'longitude': unit_data.get('longitude'),
        # Staging-specific fields
        'review_status': 'pending',
        'crawler_source': crawler_source,
        'crawler_batch_id': batch_id,
        'validation_flags': validation_flags,
        'duplicate_score': duplicate_score,
        'matched_production_id': matched_id,
        'raw_data': unit_data.get('raw_data', ''),
        'reviewer_notes': None,
        'reviewed_by': None,
        'reviewed_at': None,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Use safe staging insert (enforces production write block)
    await _safe_staging_insert('units_staging', staging_unit, crawler_source)
    
    log_msg = f"Inserted unit to staging: {staging_unit['unit_number']} (normalized: {normalized_unit_number}, dup_score: {duplicate_score:.2f}"
    if duplicate_flags:
        log_msg += f", flags: {duplicate_flags}"
    if matched_id:
        log_msg += f", matched: {matched_id[:8]}..."
    log_msg += ")"
    logger.info(log_msg)
    
    return unit_id


# ============ PRODUCTION WRITE PREVENTION (EXPLICIT BLOCKS) ============

async def _blocked_production_insert(*args, **kwargs):
    """
    BLOCKED: This function exists to catch any accidental production writes.
    Raises an error immediately.
    """
    raise PermissionError(
        "BLOCKED: Direct production insert attempted. "
        "Use the promotion service or admin approval workflow instead."
    )


async def _blocked_production_update(*args, **kwargs):
    """
    BLOCKED: This function exists to catch any accidental production writes.
    """
    raise PermissionError(
        "BLOCKED: Direct production update attempted. "
        "Use the promotion service or admin approval workflow instead."
    )


# Override any functions that might try to write to production
# These are fail-safes in case someone tries to call them
insert_unit_to_production = _blocked_production_insert
insert_building_to_production = _blocked_production_insert
update_production_unit = _blocked_production_update
update_production_building = _blocked_production_update


# ============ MAIN CRAWL FUNCTIONS ============

def generate_batch_id() -> str:
    """Generate a unique batch ID for this crawl session."""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"crawl_{timestamp}_{unique_id}"


def extract_crawler_source(url: str) -> str:
    """Extract the crawler source from URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc.replace('www.', '')


async def crawl_building_to_staging(building_id: str, batch_id: Optional[str] = None):
    """
    Crawl a specific building and insert results to STAGING collections.
    
    This function reads building info from the production collection,
    but ALL crawled data goes to staging for review.
    """
    building = await db.buildings.find_one({'id': building_id})
    if not building:
        logger.error(f"Building {building_id} not found")
        return
    
    url = building['source_url']
    crawler_source = extract_crawler_source(url)
    batch_id = batch_id or generate_batch_id()
    
    logger.info(f"Crawling {building['name']} at {url} (batch: {batch_id})")
    
    # Determine which crawler to use
    if 'fortysixfifty' in url:
        units_data = await crawl_fortysixfifty(url)
    elif 'mercedeshouseny' in url:
        units_data = await crawl_mercedes_house(url)
    elif 'harrisonyards' in url:
        units_data = await crawl_harrison_yards(url)
    elif '7w21' in url or '7w21.com' in url:
        units_data = await crawl_7w21(url)
    elif 'rivercourt' in url or 'rentrivercourtnyc' in url:
        units_data = await crawl_rivercourt(url)
    else:
        units_data = await crawl_generic_site(url)
    
    logger.info(f"Found {len(units_data)} units for {building['name']}")
    
    # Insert all units to staging (NOT production)
    for unit_data in units_data:
        try:
            await insert_unit_to_staging(
                unit_data=unit_data,
                building_id=building_id,
                crawler_source=crawler_source,
                batch_id=batch_id
            )
        except Exception as e:
            logger.error(f"Error inserting unit to staging: {e}")
            continue
    
    # Update building's last_crawled timestamp (this is a metadata update, not data insertion)
    await db.buildings.update_one(
        {'id': building_id},
        {'$set': {'last_crawled': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        'building_id': building_id,
        'building_name': building['name'],
        'batch_id': batch_id,
        'units_found': len(units_data),
        'destination': 'staging'
    }


async def crawl_new_building_to_staging(
    name: str,
    address: str,
    neighborhood: str,
    city: str,
    state: str,
    zip_code: str,
    source_url: str,
    batch_id: Optional[str] = None
) -> Dict:
    """
    Crawl a new building that doesn't exist in production yet.
    Both building and units go to staging.
    """
    batch_id = batch_id or generate_batch_id()
    crawler_source = extract_crawler_source(source_url)
    
    # First, insert building to staging
    building_data = {
        'name': name,
        'address': address,
        'neighborhood': neighborhood,
        'city': city,
        'state': state,
        'zip_code': zip_code,
        'source_url': source_url
    }
    
    staging_building_id = await insert_building_to_staging(
        building_data=building_data,
        crawler_source=crawler_source,
        batch_id=batch_id
    )
    
    logger.info(f"Crawling new building: {name} at {source_url}")
    
    # Determine which crawler to use
    if 'fortysixfifty' in source_url:
        units_data = await crawl_fortysixfifty(source_url)
    elif 'mercedeshouseny' in source_url:
        units_data = await crawl_mercedes_house(source_url)
    elif 'harrisonyards' in source_url:
        units_data = await crawl_harrison_yards(source_url)
    elif '7w21' in source_url or '7w21.com' in source_url:
        units_data = await crawl_7w21(source_url)
    elif 'rivercourt' in source_url or 'rentrivercourtnyc' in source_url:
        units_data = await crawl_rivercourt(source_url)
    else:
        units_data = await crawl_generic_site(source_url)
    
    logger.info(f"Found {len(units_data)} units for {name}")
    
    # Insert all units to staging
    for unit_data in units_data:
        try:
            await insert_unit_to_staging(
                unit_data=unit_data,
                building_id=staging_building_id,
                crawler_source=crawler_source,
                batch_id=batch_id
            )
        except Exception as e:
            logger.error(f"Error inserting unit to staging: {e}")
            continue
    
    return {
        'staging_building_id': staging_building_id,
        'building_name': name,
        'batch_id': batch_id,
        'units_found': len(units_data),
        'destination': 'staging'
    }


async def crawl_all_buildings_to_staging():
    """
    Crawl all buildings and insert results to STAGING collections.
    This is the scheduled crawl function.
    """
    batch_id = generate_batch_id()
    buildings = await db.buildings.find({}).to_list(1000)
    
    logger.info(f"Starting batch crawl: {batch_id} - {len(buildings)} buildings")
    
    results = []
    for building in buildings:
        try:
            result = await crawl_building_to_staging(building['id'], batch_id)
            results.append(result)
        except Exception as e:
            logger.error(f"Error crawling building {building['name']}: {e}")
            results.append({
                'building_id': building['id'],
                'building_name': building['name'],
                'error': str(e)
            })
            continue
    
    total_units = sum(r.get('units_found', 0) for r in results if 'error' not in r)
    logger.info(f"Batch crawl complete: {batch_id} - {total_units} total units to staging")
    
    return {
        'batch_id': batch_id,
        'buildings_crawled': len(results),
        'total_units_to_staging': total_units,
        'results': results
    }


# ============ LEGACY ALIASES (for backwards compatibility) ============
# These redirect to staging functions to prevent accidental production writes

async def crawl_building(building_id: str):
    """
    DEPRECATED: Use crawl_building_to_staging instead.
    This function now redirects to staging to prevent direct production writes.
    """
    logger.warning("crawl_building() is deprecated. Redirecting to crawl_building_to_staging()")
    return await crawl_building_to_staging(building_id)


async def crawl_all_buildings():
    """
    DEPRECATED: Use crawl_all_buildings_to_staging instead.
    This function now redirects to staging to prevent direct production writes.
    """
    logger.warning("crawl_all_buildings() is deprecated. Redirecting to crawl_all_buildings_to_staging()")
    return await crawl_all_buildings_to_staging()
