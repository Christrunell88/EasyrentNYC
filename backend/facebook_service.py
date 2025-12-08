"""
Facebook Graph API service for posting apartment listings to Facebook Business Page.
"""

import httpx
import json
import logging
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class FacebookService:
    """Service for interacting with Facebook Graph API."""
    
    def __init__(self):
        """Initialize the Facebook API service with credentials."""
        self.page_id = os.environ.get('FACEBOOK_PAGE_ID')
        self.access_token = os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN')
        self.api_version = os.environ.get('FACEBOOK_API_VERSION', 'v20.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        if not self.page_id or not self.access_token:
            logger.warning("Facebook credentials not configured")
    
    def _get_common_params(self) -> Dict[str, str]:
        """Get common parameters for all API requests."""
        return {"access_token": self.access_token}
    
    async def post_with_single_photo(
        self,
        message: str,
        photo_url: str,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post content with a single photo to the Facebook page.
        Downloads the image first if it's not from a well-known CDN.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Check if we need to download the image first
            needs_download = (
                'customer-assets.emergentagent.com' in photo_url or
                'emergentagent.com' in photo_url
            )
            
            if needs_download:
                # Download the image to memory
                try:
                    logger.info(f"Downloading image from {photo_url}")
                    img_response = await client.get(photo_url, timeout=30.0)
                    img_response.raise_for_status()
                    image_data = img_response.content
                    
                    # Determine content type
                    content_type = img_response.headers.get('content-type', 'image/jpeg')
                    
                    # Upload as multipart/form-data
                    endpoint = f"{self.base_url}/{self.page_id}/photos"
                    params = self._get_common_params()
                    
                    files = {
                        'source': ('image.jpg', image_data, content_type)
                    }
                    data = {
                        'message': message,
                        'published': True
                    }
                    
                    response = await client.post(
                        endpoint,
                        files=files,
                        data=data,
                        params=params
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    if "error" in result:
                        raise Exception(f"Facebook API error: {result['error'].get('message', 'Unknown error')}")
                    
                    logger.info(f"Posted photo successfully (downloaded). Post ID: {result.get('post_id')}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Failed to download and post image: {str(e)}")
                    raise Exception(f"Failed to download and post image: {str(e)}")
            else:
                # Use URL method for well-known CDNs (GCS, Unsplash, etc.)
                payload = {
                    "message": message,
                    "url": photo_url,
                    "published": True,
                }
                
                if link:
                    payload["link"] = link
                
                endpoint = f"{self.base_url}/{self.page_id}/photos"
                params = self._get_common_params()
                
                try:
                    response = await client.post(
                        endpoint,
                        data=payload,
                        params=params
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if "error" in data:
                        raise Exception(f"Facebook API error: {data['error'].get('message', 'Unknown error')}")
                    
                    logger.info(f"Posted photo successfully. Post ID: {data.get('post_id')}")
                    return data
                    
                except httpx.HTTPError as e:
                    logger.error(f"HTTP error posting to Facebook: {str(e)}")
                    raise Exception(f"Failed to post to Facebook: {str(e)}")
    
    async def upload_photo_for_later_use(
        self,
        photo_url: str
    ) -> Dict[str, Any]:
        """Upload a photo without publishing it immediately."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "url": photo_url,
                "published": False,
                "temporary": True,
            }
            
            endpoint = f"{self.base_url}/{self.page_id}/photos"
            params = self._get_common_params()
            
            try:
                response = await client.post(
                    endpoint,
                    data=payload,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"Facebook API error: {data['error'].get('message', 'Unknown error')}")
                
                logger.info(f"Uploaded photo successfully. Photo ID: {data.get('id')}")
                return data
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error uploading photo: {str(e)}")
                raise Exception(f"Failed to upload photo: {str(e)}")
    
    async def post_with_multiple_photos(
        self,
        message: str,
        photo_urls: List[str],
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post content with multiple photos to the Facebook page."""
        try:
            # Step 1: Upload all photos without publishing
            photo_ids = []
            for photo_url in photo_urls[:10]:  # Limit to 10 photos
                photo_data = await self.upload_photo_for_later_use(photo_url)
                photo_ids.append(photo_data["id"])
            
            # Step 2: Create a feed post with references to all uploaded photos
            attached_media = [
                {"media_fbid": photo_id} for photo_id in photo_ids
            ]
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "message": message,
                    "attached_media": json.dumps(attached_media),
                    "published": True,
                }
                
                if link:
                    payload["link"] = link
                
                endpoint = f"{self.base_url}/{self.page_id}/feed"
                params = self._get_common_params()
                
                response = await client.post(
                    endpoint,
                    data=payload,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"Facebook API error: {data['error'].get('message', 'Unknown error')}")
                
                logger.info(f"Posted multiple photos successfully. Post ID: {data.get('id')}")
                return data
                
        except Exception as e:
            logger.error(f"Error in multi-photo post: {str(e)}")
            raise
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete a previously posted post."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            endpoint = f"{self.base_url}/{post_id}"
            params = self._get_common_params()
            
            try:
                response = await client.delete(
                    endpoint,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"Failed to delete post: {data['error'].get('message', 'Unknown error')}")
                
                return data.get("success", True)
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error deleting post: {str(e)}")
                raise Exception(f"Failed to delete post: {str(e)}")
