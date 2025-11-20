"""Test Harrison Yards crawler"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from crawler import crawl_harrison_yards

async def main():
    url = 'https://harrisonyards.com/floor-plans.aspx'
    print(f"Testing crawler for: {url}\n")
    
    units = await crawl_harrison_yards(url)
    
    print(f"Found {len(units)} units\n")
    
    for i, unit in enumerate(units[:5], 1):
        print(f"Unit {i}:")
        print(f"  Unit Number: {unit['unit_number']}")
        print(f"  Rent: ${unit['rent']}")
        print(f"  Bedrooms: {unit['bedrooms']}")
        print(f"  Bathrooms: {unit['bathrooms']}")
        print(f"  Images: {len(unit['images'])}")
        if unit['images']:
            for img_url in unit['images'][:2]:
                print(f"    - {img_url}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
