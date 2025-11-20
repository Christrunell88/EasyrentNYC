"""Script to re-crawl all buildings and update images"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from crawler import crawl_all_buildings

async def main():
    print("Starting re-crawl of all buildings...")
    await crawl_all_buildings()
    print("Re-crawl complete!")

if __name__ == "__main__":
    asyncio.run(main())
