"""
Geocoding service to convert addresses to latitude/longitude coordinates.
Uses Google Geocoding API with the Maps API key.
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Tuple
from urllib.parse import quote
import os

logger = logging.getLogger(__name__)

# Google Geocoding API endpoint
GOOGLE_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# Get API key from environment
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyC7JZ2Lgd1DwV04BtmrVDkWL6rdc-PHkVQ')

# Rate limiting: Google allows 50 requests per second
RATE_LIMIT_DELAY = 0.05  # seconds between requests


async def geocode_address(
    address: str, 
    city: str = None, 
    state: str = None, 
    zip_code: str = None
) -> Optional[Tuple[float, float]]:
    """
    Geocode an address to get latitude and longitude using Google Geocoding API.
    
    Args:
        address: Street address
        city: City name
        state: State name or abbreviation
        zip_code: ZIP code
    
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    
    # Build full address string
    address_parts = [address]
    if city:
        address_parts.append(city)
    if state:
        address_parts.append(state)
    if zip_code:
        address_parts.append(zip_code)
    
    full_address = ", ".join(filter(None, address_parts))
    
    try:
        # Add rate limiting delay
        await asyncio.sleep(RATE_LIMIT_DELAY)
        
        # Make request to Google Geocoding API
        params = {
            "address": full_address,
            "key": GOOGLE_MAPS_API_KEY,
            "region": "us"  # Bias results to United States
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                GOOGLE_GEOCODING_URL, 
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status != 200:
                    logger.error(f"Geocoding failed with status {response.status} for: {full_address}")
                    return None
                
                data = await response.json()
                
                if data.get("status") != "OK":
                    logger.warning(f"Geocoding status {data.get('status')} for: {full_address}")
                    return None
                
                if not data.get("results"):
                    logger.warning(f"No geocoding results for: {full_address}")
                    return None
                
                # Get first result
                result = data["results"][0]
                location = result["geometry"]["location"]
                lat = float(location["lat"])
                lng = float(location["lng"])
                
                logger.info(f"✅ Geocoded: {full_address} -> ({lat}, {lng})")
                return (lat, lng)
                
    except asyncio.TimeoutError:
        logger.error(f"Geocoding timeout for: {full_address}")
        return None
    except Exception as e:
        logger.error(f"Geocoding error for {full_address}: {str(e)}")
        return None


async def geocode_building(building: dict) -> Optional[Tuple[float, float]]:
    """
    Geocode a building using its address information.
    
    Args:
        building: Dictionary containing building data with address fields
    
    Returns:
        Tuple of (latitude, longitude) or None
    """
    
    return await geocode_address(
        address=building.get("address", ""),
        city=building.get("city", ""),
        state=building.get("state", ""),
        zip_code=building.get("zip_code", "")
    )


async def batch_geocode_buildings(buildings: list, batch_size: int = 10) -> dict:
    """
    Geocode multiple buildings with rate limiting.
    
    Args:
        buildings: List of building dictionaries
        batch_size: Number of buildings to process at once
    
    Returns:
        Dictionary mapping building IDs to (lat, lng) tuples
    """
    
    results = {}
    
    logger.info(f"Starting batch geocoding for {len(buildings)} buildings...")
    
    for i in range(0, len(buildings), batch_size):
        batch = buildings[i:i+batch_size]
        
        for building in batch:
            building_id = building.get("id")
            
            # Skip if already has coordinates
            if building.get("latitude") and building.get("longitude"):
                results[building_id] = (building["latitude"], building["longitude"])
                logger.info(f"Building {building_id} already has coordinates")
                continue
            
            coords = await geocode_building(building)
            
            if coords:
                results[building_id] = coords
            else:
                logger.warning(f"Failed to geocode building {building_id}: {building.get('address')}")
        
        # Progress update
        logger.info(f"Processed {min(i+batch_size, len(buildings))}/{len(buildings)} buildings")
    
    logger.info(f"✅ Batch geocoding complete. Successfully geocoded {len(results)} buildings.")
    
    return results


if __name__ == "__main__":
    # Test geocoding
    async def test():
        # Test address
        coords = await geocode_address(
            address="350 West 42nd Street",
            city="New York",
            state="NY",
            zip_code="10036"
        )
        print(f"Test result: {coords}")
    
    asyncio.run(test())
