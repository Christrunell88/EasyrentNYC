"""Test script to post a listing to Facebook."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from facebook_service import FacebookService
import os
from dotenv import load_dotenv

load_dotenv()

async def test_post():
    # Get database connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Get a sample unit
    unit = await db.units.find_one(
        {'posted_to_facebook': {'$ne': True}},
        {'_id': 0}
    )
    
    if not unit:
        print("No unposted units found")
        return
    
    print(f"\n📋 Testing Facebook Post for Unit: {unit['id']}")
    print(f"   Address: {unit.get('address')}")
    print(f"   Rent: ${unit.get('rent')}")
    print(f"   Photos: {len(unit.get('images', []))}")
    
    # Format the listing
    message = f"{unit.get('unit_number', 'Apartment')} at {unit.get('address', 'Address')}\n\n"
    message += f"📍 {unit.get('city', '')}, {unit.get('state', '')} {unit.get('zip_code', '')}\n"
    message += f"💰 ${unit.get('rent', 0):,.0f}/month\n"
    message += f"🛏️ {unit.get('bedrooms', 0)} bed • 🛁 {unit.get('bathrooms', 0)} bath\n\n"
    
    if unit.get('amenities'):
        message += "✨ Amenities: " + ", ".join(unit['amenities'][:5]) + "\n\n"
    
    message += "✅ NO FEE APARTMENT\n\n"
    listing_url = f"https://nofeesapts.com/unit/{unit['id']}"
    message += f"🔗 View full listing: {listing_url}"
    
    photo_urls = unit.get('images', [])
    
    print(f"\n📝 Post Message:\n{message}\n")
    
    # Initialize Facebook service
    facebook_service = FacebookService()
    
    try:
        # Post to Facebook
        if len(photo_urls) == 0:
            print("❌ No photos available, using placeholder")
            result = await facebook_service.post_with_single_photo(
                message=message,
                photo_url="https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80",
                link=listing_url
            )
        elif len(photo_urls) == 1:
            print(f"📸 Posting with 1 photo")
            result = await facebook_service.post_with_single_photo(
                message=message,
                photo_url=photo_urls[0],
                link=listing_url
            )
        else:
            print(f"📸 Posting with {len(photo_urls)} photos")
            result = await facebook_service.post_with_multiple_photos(
                message=message,
                photo_urls=photo_urls,
                link=listing_url
            )
        
        post_id = result.get("id") or result.get("post_id")
        print(f"\n✅ SUCCESS! Posted to Facebook")
        print(f"   Post ID: {post_id}")
        
        # Mark as posted in database
        await db.units.update_one(
            {"id": unit['id']},
            {
                "$set": {
                    "posted_to_facebook": True,
                    "facebook_post_id": post_id
                }
            }
        )
        print(f"   ✅ Marked as posted in database")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_post())
