"""
Migrate existing apartment images from external URLs to Google Cloud Storage.
This script downloads images from their current URLs and uploads them to GCS.
"""

import asyncio
import logging
import os
import sys
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv
from cloud_storage_service import upload_apartment_image
from typing import List, Dict

# Setup
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


async def download_image(session: aiohttp.ClientSession, url: str, timeout: int = 30) -> bytes:
    """
    Download image from URL.
    
    Args:
        session: aiohttp session
        url: Image URL
        timeout: Timeout in seconds
    
    Returns:
        Image bytes
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type.lower():
                    logger.warning(f"URL doesn't appear to be an image: {url} (type: {content_type})")
                    return None
                
                image_bytes = await response.read()
                logger.info(f"✅ Downloaded image from {url} ({len(image_bytes)} bytes)")
                return image_bytes
            else:
                logger.warning(f"Failed to download {url}: HTTP {response.status}")
                return None
    except asyncio.TimeoutError:
        logger.warning(f"Timeout downloading {url}")
        return None
    except Exception as e:
        logger.warning(f"Error downloading {url}: {str(e)}")
        return None


async def migrate_unit_images(unit: Dict, session: aiohttp.ClientSession, dry_run: bool = False) -> Dict:
    """
    Migrate all images for a single unit to GCS.
    
    Args:
        unit: Unit document from database
        session: aiohttp session
        dry_run: If True, only simulate migration
    
    Returns:
        Dictionary with migration results
    """
    unit_id = unit['id']
    building_id = unit['building_id']
    existing_images = unit.get('images', [])
    
    if not existing_images:
        return {
            'unit_id': unit_id,
            'status': 'skipped',
            'reason': 'no_images',
            'images_migrated': 0
        }
    
    logger.info(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating unit {unit_id}: {len(existing_images)} images")
    
    new_image_urls = []
    migrated_count = 0
    failed_count = 0
    
    for idx, image_url in enumerate(existing_images):
        logger.info(f"  Image {idx + 1}/{len(existing_images)}: {image_url[:80]}...")
        
        # Skip if already a GCS URL
        if 'storage.googleapis.com' in image_url or 'nofeesapts-images' in image_url:
            logger.info(f"  ✓ Already in GCS, keeping as-is")
            new_image_urls.append(image_url)
            continue
        
        if dry_run:
            logger.info(f"  [DRY RUN] Would download and upload to GCS")
            new_image_urls.append(image_url)  # Keep original in dry run
            migrated_count += 1
            continue
        
        # Download image
        image_bytes = await download_image(session, image_url)
        
        if not image_bytes:
            logger.warning(f"  ✗ Failed to download, keeping original URL")
            new_image_urls.append(image_url)
            failed_count += 1
            continue
        
        try:
            # Upload to GCS
            result = await upload_apartment_image(
                image_file=image_bytes,
                building_id=building_id,
                unit_id=unit_id,
                filename=f"image_{idx}"
            )
            
            # Use medium-sized image as the default
            gcs_url = result['urls']['medium']
            new_image_urls.append(gcs_url)
            migrated_count += 1
            
            logger.info(f"  ✅ Uploaded to GCS: {gcs_url}")
            
        except Exception as e:
            logger.error(f"  ✗ Failed to upload to GCS: {str(e)}")
            new_image_urls.append(image_url)  # Keep original URL on failure
            failed_count += 1
    
    # Update unit in database
    if not dry_run and new_image_urls != existing_images:
        await db.units.update_one(
            {'id': unit_id},
            {'$set': {'images': new_image_urls}}
        )
        logger.info(f"✅ Updated unit {unit_id} with {migrated_count} GCS URLs")
    
    return {
        'unit_id': unit_id,
        'status': 'success' if migrated_count > 0 else 'failed',
        'images_migrated': migrated_count,
        'images_failed': failed_count,
        'total_images': len(existing_images)
    }


async def migrate_all_images(dry_run: bool = False, limit: int = None):
    """
    Migrate all apartment images to GCS.
    
    Args:
        dry_run: If True, only simulate migration without actual changes
        limit: Optional limit on number of units to process
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Starting image migration to Google Cloud Storage")
    logger.info(f"{'='*80}\n")
    
    # Get all units with images
    query = {'images': {'$exists': True, '$ne': []}}
    units = await db.units.find(query, {"_id": 0}).to_list(limit if limit else 10000)
    
    total_units = len(units)
    logger.info(f"Found {total_units} units with images")
    
    if limit:
        units = units[:limit]
        logger.info(f"Processing first {len(units)} units (limit applied)")
    
    if not units:
        logger.info("No units with images found. Migration complete.")
        return
    
    # Create aiohttp session for downloading images
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        results = []
        
        for idx, unit in enumerate(units, 1):
            logger.info(f"\n[{idx}/{len(units)}] Processing unit {unit['id']}...")
            
            result = await migrate_unit_images(unit, session, dry_run)
            results.append(result)
            
            # Small delay to avoid overwhelming the servers
            await asyncio.sleep(0.5)
        
        # Summary
        logger.info(f"\n{'='*80}")
        logger.info(f"MIGRATION {'DRY RUN ' if dry_run else ''}SUMMARY")
        logger.info(f"{'='*80}")
        
        total_migrated = sum(r['images_migrated'] for r in results)
        total_failed = sum(r['images_failed'] for r in results)
        skipped = len([r for r in results if r['status'] == 'skipped'])
        
        logger.info(f"Units processed: {len(results)}")
        logger.info(f"Units skipped (no images): {skipped}")
        logger.info(f"Images migrated to GCS: {total_migrated}")
        logger.info(f"Images failed: {total_failed}")
        
        if dry_run:
            logger.info(f"\nThis was a DRY RUN. No changes were made to the database.")
            logger.info(f"Run without --dry-run to perform actual migration.")
        else:
            logger.info(f"\n✅ Migration complete! All images are now stored in Google Cloud Storage.")


if __name__ == "__main__":
    # Parse command line arguments
    dry_run = "--dry-run" in sys.argv
    limit = None
    
    for arg in sys.argv:
        if arg.startswith("--limit="):
            try:
                limit = int(arg.split("=")[1])
            except:
                pass
    
    # Run migration
    asyncio.run(migrate_all_images(dry_run=dry_run, limit=limit))
