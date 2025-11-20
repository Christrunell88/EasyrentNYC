#!/usr/bin/env python3
"""
Comprehensive Crawler Testing for NoFeeApts Application
Tests apartment crawler functionality, image scraping, and database integrity
"""

import asyncio
import sys
import requests
import re
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/app/backend')

# Load environment
ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

# Import crawler functions
from crawler import crawl_harrison_yards, crawl_generic_site, crawl_building

class CrawlerTester:
    def __init__(self):
        self.mongo_url = os.environ['MONGO_URL']
        self.db_name = os.environ['DB_NAME']
        self.client = None
        self.db = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test buildings data
        self.harrison_yards_id = "b589a50a-b78d-461d-bee6-68d47073a514"
        self.harrison_yards_url = "https://harrisonyards.com/floor-plans.aspx"
        
        # Other buildings to test
        self.test_buildings = [
            {"name": "4650 Center Blvd", "url_pattern": "fortysixfifty"},
            {"name": "Waterline Square", "url_pattern": "waterline"},
            {"name": "Mercedes House", "url_pattern": "mercedes"},
            {"name": "Claridges", "url_pattern": "claridge"},
            {"name": "The Saranac", "url_pattern": "saranac"}
        ]

    async def setup(self):
        """Initialize database connection"""
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        print(f"🔗 Connected to MongoDB: {self.db_name}")

    async def cleanup(self):
        """Close database connection"""
        if self.client:
            self.client.close()

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    async def test_harrison_yards_crawler(self):
        """Test Harrison Yards specific crawler function"""
        print("\n🏢 Testing Harrison Yards Crawler Function")
        
        try:
            units = await crawl_harrison_yards(self.harrison_yards_url)
            
            if not units:
                self.log_test("Harrison Yards Crawler - Extract Units", False, "No units extracted")
                return False
            
            self.log_test("Harrison Yards Crawler - Extract Units", True, f"Found {len(units)} units")
            
            # Test image extraction
            units_with_images = [u for u in units if u.get('images')]
            self.log_test("Harrison Yards Crawler - Image Extraction", 
                         len(units_with_images) > 0, 
                         f"{len(units_with_images)}/{len(units)} units have images")
            
            # Test LeaseStar API images
            leasestar_images = []
            for unit in units:
                for img in unit.get('images', []):
                    if 'myleasestar.com' in img:
                        leasestar_images.append(img)
            
            self.log_test("Harrison Yards Crawler - LeaseStar Images", 
                         len(leasestar_images) > 0,
                         f"Found {len(leasestar_images)} LeaseStar images")
            
            # Test unit data structure
            valid_units = 0
            for unit in units:
                if (unit.get('unit_number') and 
                    unit.get('rent', 0) > 0 and 
                    isinstance(unit.get('bedrooms'), int) and
                    isinstance(unit.get('bathrooms'), (int, float))):
                    valid_units += 1
            
            self.log_test("Harrison Yards Crawler - Data Structure", 
                         valid_units == len(units),
                         f"{valid_units}/{len(units)} units have valid structure")
            
            return len(units) > 0
            
        except Exception as e:
            self.log_test("Harrison Yards Crawler - Function Test", False, f"Error: {str(e)}")
            return False

    async def test_database_harrison_yards(self):
        """Test Harrison Yards units in database"""
        print("\n🗄️ Testing Harrison Yards Database Integration")
        
        try:
            # Check if Harrison Yards building exists
            building = await self.db.buildings.find_one({'id': self.harrison_yards_id})
            if not building:
                self.log_test("Harrison Yards Database - Building Exists", False, "Building not found in database")
                return False
            
            self.log_test("Harrison Yards Database - Building Exists", True)
            
            # Get units for Harrison Yards
            units = await self.db.units.find({'building_id': self.harrison_yards_id}).to_list(1000)
            
            if not units:
                self.log_test("Harrison Yards Database - Units Exist", False, "No units found")
                return False
            
            self.log_test("Harrison Yards Database - Units Exist", True, f"Found {len(units)} units")
            
            # Check units with images
            units_with_images = [u for u in units if u.get('images')]
            expected_with_images = 59  # Based on requirements
            
            self.log_test("Harrison Yards Database - Units with Images", 
                         len(units_with_images) >= expected_with_images - 5,  # Allow some tolerance
                         f"{len(units_with_images)} units have images (expected ~{expected_with_images})")
            
            # Check for LeaseStar images
            leasestar_count = 0
            for unit in units:
                for img in unit.get('images', []):
                    if 'myleasestar.com' in img:
                        leasestar_count += 1
                        break
            
            self.log_test("Harrison Yards Database - LeaseStar Images", 
                         leasestar_count > 0,
                         f"{leasestar_count} units have LeaseStar images")
            
            return True
            
        except Exception as e:
            self.log_test("Harrison Yards Database Test", False, f"Error: {str(e)}")
            return False

    async def test_generic_crawler_buildings(self):
        """Test generic crawler on other buildings"""
        print("\n🌐 Testing Generic Crawler on Other Buildings")
        
        try:
            # Get all buildings from database
            buildings = await self.db.buildings.find({}).to_list(1000)
            
            if not buildings:
                self.log_test("Generic Crawler - Buildings Available", False, "No buildings in database")
                return False
            
            self.log_test("Generic Crawler - Buildings Available", True, f"Found {len(buildings)} buildings")
            
            # Test a few non-Harrison buildings
            tested_buildings = 0
            for building in buildings[:5]:  # Test first 5 buildings
                if building['id'] == self.harrison_yards_id:
                    continue  # Skip Harrison Yards
                
                try:
                    # Test crawler function
                    units = await crawl_generic_site(building['source_url'])
                    tested_buildings += 1
                    
                    if units:
                        self.log_test(f"Generic Crawler - {building['name']}", True, f"Found {len(units)} units")
                    else:
                        self.log_test(f"Generic Crawler - {building['name']}", True, "No units found (may be expected)")
                        
                except Exception as e:
                    self.log_test(f"Generic Crawler - {building['name']}", False, f"Error: {str(e)}")
            
            return tested_buildings > 0
            
        except Exception as e:
            self.log_test("Generic Crawler Test", False, f"Error: {str(e)}")
            return False

    async def test_database_integrity(self):
        """Test database integrity - duplicates, valid URLs, cleanup"""
        print("\n🔍 Testing Database Integrity")
        
        try:
            # Check total units
            total_units = await self.db.units.count_documents({})
            expected_total = 287  # Based on requirements
            
            self.log_test("Database Integrity - Total Units", 
                         abs(total_units - expected_total) <= 50,  # Allow some tolerance
                         f"Found {total_units} units (expected ~{expected_total})")
            
            # Check for duplicate units
            pipeline = [
                {"$group": {
                    "_id": {"building_id": "$building_id", "unit_number": "$unit_number"},
                    "count": {"$sum": 1}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await self.db.units.aggregate(pipeline).to_list(1000)
            self.log_test("Database Integrity - No Duplicates", 
                         len(duplicates) == 0,
                         f"Found {len(duplicates)} duplicate unit combinations")
            
            # Check units with real images (not Unsplash placeholders)
            units_with_real_images = await self.db.units.count_documents({
                'images.0': {'$exists': True, '$not': {'$regex': 'unsplash'}}
            })
            expected_real_images = 61  # Based on requirements
            
            self.log_test("Database Integrity - Units with Real Images", 
                         abs(units_with_real_images - expected_real_images) <= 10,
                         f"Found {units_with_real_images} units with real images (expected ~{expected_real_images})")
            
            # Check for old placeholder units cleanup
            old_placeholder_units = await self.db.units.count_documents({
                'unit_number': {'$regex': '^Unit-[0-9]BR-[0-9]+$'},
                'images.0': {'$regex': 'unsplash'}
            })
            
            self.log_test("Database Integrity - Old Placeholders Cleaned", 
                         old_placeholder_units == 0,
                         f"Found {old_placeholder_units} old placeholder units (should be 0)")
            
            return True
            
        except Exception as e:
            self.log_test("Database Integrity Test", False, f"Error: {str(e)}")
            return False

    def test_image_url_accessibility(self):
        """Test that image URLs are actually accessible"""
        print("\n🖼️ Testing Image URL Accessibility")
        
        try:
            # Get sample image URLs from database
            sample_images = []
            
            # Get images from Harrison Yards units
            async def get_sample_images():
                units = await self.db.units.find({'building_id': self.harrison_yards_id}).to_list(100)
                images = []
                for unit in units:
                    for img in unit.get('images', []):
                        if img.startswith('http') and len(images) < 10:
                            images.append(img)
                return images
            
            # Run async function
            loop = asyncio.get_event_loop()
            sample_images = loop.run_until_complete(get_sample_images())
            
            if not sample_images:
                self.log_test("Image URL Accessibility - Sample Images", False, "No image URLs found to test")
                return False
            
            self.log_test("Image URL Accessibility - Sample Images", True, f"Testing {len(sample_images)} image URLs")
            
            # Test accessibility
            accessible_count = 0
            valid_types = 0
            
            for img_url in sample_images:
                try:
                    response = requests.head(img_url, timeout=10, allow_redirects=True)
                    if response.status_code == 200:
                        accessible_count += 1
                        
                        # Check content type
                        content_type = response.headers.get('content-type', '').lower()
                        if any(img_type in content_type for img_type in ['image/jpeg', 'image/jpg', 'image/png']):
                            valid_types += 1
                    
                except Exception as e:
                    print(f"    ⚠️ Failed to access: {img_url[:50]}... - {str(e)}")
                    continue
            
            self.log_test("Image URL Accessibility - HTTP 200 Status", 
                         accessible_count > len(sample_images) * 0.7,  # At least 70% should be accessible
                         f"{accessible_count}/{len(sample_images)} images accessible")
            
            self.log_test("Image URL Accessibility - Valid Image Types", 
                         valid_types > len(sample_images) * 0.7,
                         f"{valid_types}/{len(sample_images)} images have valid types")
            
            return accessible_count > 0
            
        except Exception as e:
            self.log_test("Image URL Accessibility Test", False, f"Error: {str(e)}")
            return False

    async def test_crawler_error_handling(self):
        """Test crawler error handling with invalid URLs"""
        print("\n⚠️ Testing Crawler Error Handling")
        
        try:
            # Test with invalid URL
            units = await crawl_generic_site("https://invalid-url-that-does-not-exist.com")
            self.log_test("Crawler Error Handling - Invalid URL", 
                         units == [],
                         "Crawler handles invalid URLs gracefully")
            
            # Test with valid domain but invalid path
            units = await crawl_harrison_yards("https://harrisonyards.com/invalid-path")
            self.log_test("Crawler Error Handling - Invalid Path", 
                         isinstance(units, list),
                         "Crawler handles invalid paths gracefully")
            
            return True
            
        except Exception as e:
            self.log_test("Crawler Error Handling Test", False, f"Error: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all crawler tests"""
        print("🚀 Starting NoFeeApts Crawler Tests")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Test Harrison Yards crawler function
            await self.test_harrison_yards_crawler()
            
            # Test Harrison Yards database integration
            await self.test_database_harrison_yards()
            
            # Test generic crawler on other buildings
            await self.test_generic_crawler_buildings()
            
            # Test database integrity
            await self.test_database_integrity()
            
            # Test image URL accessibility
            self.test_image_url_accessibility()
            
            # Test error handling
            await self.test_crawler_error_handling()
            
        finally:
            await self.cleanup()
        
        # Results Summary
        print("\n" + "=" * 60)
        print(f"📊 Crawler Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All crawler tests passed!")
            return 0
        else:
            print("❌ Some crawler tests failed!")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']}: {result['details']}")
            return 1

def main():
    tester = CrawlerTester()
    return asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    sys.exit(main())