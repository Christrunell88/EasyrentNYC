"""
Google Cloud Storage service for apartment image management.
Handles upload, optimization, and serving of images.
"""

import os
import io
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from google.cloud import storage
from PIL import Image
import uuid

logger = logging.getLogger(__name__)

# Configuration - use environment variables for deployment flexibility
BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "nofeesapts-images")
CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", str(Path(__file__).parent / "gcs-credentials.json"))

# Set credentials environment variable if not already set
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_PATH)

# Initialize client
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    logger.info(f"✅ Google Cloud Storage initialized: {BUCKET_NAME}")
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud Storage: {e}")
    storage_client = None
    bucket = None


# Image size configurations
IMAGE_SIZES = {
    "thumbnail": (300, 300),
    "medium": (800, 800),
    "large": (1600, 1600),
    "full": None  # Original size
}


def optimize_image(image: Image.Image, max_size: Optional[Tuple[int, int]] = None, quality: int = 85) -> io.BytesIO:
    """
    Optimize image: resize and compress.
    
    Args:
        image: PIL Image object
        max_size: Maximum dimensions (width, height), maintains aspect ratio
        quality: JPEG quality (1-100)
    
    Returns:
        BytesIO object containing optimized image
    """
    
    # Convert RGBA to RGB if necessary
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize if max_size specified
    if max_size:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save to BytesIO
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return output


async def upload_apartment_image(
    image_file: bytes,
    building_id: str,
    unit_id: Optional[str] = None,
    filename: Optional[str] = None
) -> dict:
    """
    Upload apartment image with automatic optimization and multiple sizes.
    
    Args:
        image_file: Image file bytes
        building_id: Building ID for organization
        unit_id: Optional unit ID for organization
        filename: Optional original filename
    
    Returns:
        Dictionary with URLs for different image sizes
    """
    
    if not storage_client or not bucket:
        raise Exception("Google Cloud Storage not initialized")
    
    try:
        # Generate unique ID for this image
        image_id = str(uuid.uuid4())
        
        # Determine folder structure
        if unit_id:
            folder = f"apartments/{building_id}/{unit_id}"
        else:
            folder = f"buildings/{building_id}"
        
        # Load image
        image = Image.open(io.BytesIO(image_file))
        
        # Upload different sizes
        urls = {}
        
        for size_name, dimensions in IMAGE_SIZES.items():
            # Optimize image
            if size_name == "full":
                optimized = optimize_image(image.copy(), quality=90)
            else:
                optimized = optimize_image(image.copy(), max_size=dimensions, quality=85)
            
            # Generate blob path
            blob_path = f"{folder}/{image_id}_{size_name}.jpg"
            blob = bucket.blob(blob_path)
            
            # Upload (bucket is configured with public access via IAM)
            blob.upload_from_file(optimized, content_type='image/jpeg')
            
            # Get public URL
            urls[size_name] = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
            
            logger.info(f"✅ Uploaded {size_name}: {blob_path}")
        
        return {
            "image_id": image_id,
            "urls": urls,
            "folder": folder
        }
        
    except Exception as e:
        logger.error(f"Image upload failed: {str(e)}")
        raise Exception(f"Image upload failed: {str(e)}")


async def delete_apartment_image(image_id: str, folder: str) -> bool:
    """
    Delete all sizes of an apartment image.
    
    Args:
        image_id: Image ID
        folder: Folder path (e.g., "apartments/building-id/unit-id")
    
    Returns:
        True if successful
    """
    
    if not storage_client or not bucket:
        raise Exception("Google Cloud Storage not initialized")
    
    try:
        deleted_count = 0
        
        for size_name in IMAGE_SIZES.keys():
            blob_path = f"{folder}/{image_id}_{size_name}.jpg"
            blob = bucket.blob(blob_path)
            
            if blob.exists():
                blob.delete()
                deleted_count += 1
                logger.info(f"✅ Deleted: {blob_path}")
        
        logger.info(f"Deleted {deleted_count} image sizes for {image_id}")
        return True
        
    except Exception as e:
        logger.error(f"Image deletion failed: {str(e)}")
        return False


async def list_building_images(building_id: str) -> List[str]:
    """
    List all images for a building.
    
    Args:
        building_id: Building ID
    
    Returns:
        List of image URLs (medium size)
    """
    
    if not storage_client or not bucket:
        return []
    
    try:
        prefix = f"buildings/{building_id}/"
        blobs = bucket.list_blobs(prefix=prefix)
        
        # Get only medium-sized images
        urls = []
        for blob in blobs:
            if "_medium.jpg" in blob.name:
                urls.append(blob.public_url)
        
        return urls
        
    except Exception as e:
        logger.error(f"Failed to list images: {str(e)}")
        return []


def get_image_url(image_id: str, folder: str, size: str = "medium") -> str:
    """
    Get public URL for an image.
    
    Args:
        image_id: Image ID
        folder: Folder path
        size: Size name (thumbnail, medium, large, full)
    
    Returns:
        Public URL
    """
    
    blob_path = f"{folder}/{image_id}_{size}.jpg"
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"


# Test function
if __name__ == "__main__":
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Credentials: {CREDENTIALS_PATH}")
    print(f"Storage client initialized: {storage_client is not None}")
    
    if bucket:
        print(f"✅ Bucket '{BUCKET_NAME}' is accessible")
    else:
        print(f"❌ Cannot access bucket '{BUCKET_NAME}'")
