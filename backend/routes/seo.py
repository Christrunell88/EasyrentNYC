"""SEO routes - sitemap and robots.txt."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import logging

from database import db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sitemap.xml", response_class=PlainTextResponse)
async def get_sitemap():
    """Generate and serve dynamic sitemap.xml for SEO"""
    try:
        from sitemap_generator import generate_sitemap
        
        # Get all available units
        units = await db.units.find(
            {'is_available': True},
            {"_id": 0, "id": 1, "updated_at": 1, "created_at": 1}
        ).to_list(1000)
        
        # Get all buildings for location pages
        buildings = await db.buildings.find(
            {},
            {"_id": 0, "neighborhood": 1, "city": 1}
        ).to_list(1000)
        
        # Always use production URL for sitemap (SEO purposes)
        base_url = 'https://www.nofeesapts.com'
        
        # Generate sitemap
        sitemap_xml = generate_sitemap(units, buildings, base_url)
        
        logger.info(f"Sitemap generated with {len(units)} units and {len(buildings)} buildings")
        
        return PlainTextResponse(
            content=sitemap_xml,
            media_type="application/xml"
        )
    except Exception as e:
        logger.error(f"Error generating sitemap: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate sitemap")
