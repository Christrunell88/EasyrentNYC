#!/usr/bin/env python3
"""
Anagram Columbus Circle Building and Units Testing
Tests the newly added "Anagram Columbus Circle" building and its specific units
"""

import requests
import sys
import json
from datetime import datetime

class AnagramColumbusCircleTester:
    def __init__(self):
        # Get backend URL from frontend .env
        self.backend_url = "https://nofee-apt-search.preview.emergentagent.com"
        self.api_url = f"{self.backend_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Expected building data
        self.expected_building = {
            "name": "Anagram Columbus Circle",
            "address": "1 West 60th Street",
            "neighborhood": "Upper West Side",
            "city": "New York",
            "state": "NY"
        }
        
        # Expected unit data
        self.expected_units = {
            "9a8c3ba5-60c3-48a0-89af-d6e691c04381": {
                "rent": 6500,
                "bedrooms": 0,  # studio
                "bathrooms": 1,
                "is_available": True,
                "unit_type": "Studio 02C"
            },
            "c350312e-9339-42da-8474-b02c04a575ae": {
                "rent": 11700,
                "bedrooms": 2,
                "bathrooms": 2,
                "is_available": True,
                "unit_type": "Two Bedroom 21B"
            }
        }
        
        self.anagram_building_id = None

    def log_test(self, name, success, details="", endpoint=""):
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
            "details": details,
            "endpoint": endpoint
        })

    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint}"
        
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=15)
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request error for {method} {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {method} {url}: {e}")
            return None

    def test_anagram_building_exists(self):
        """Test that Anagram Columbus Circle building exists with correct details"""
        response = self.make_request('GET', 'buildings')
        
        if not response or response.status_code != 200:
            self.log_test("Anagram Building Verification", False, 
                         f"Failed to get buildings list: {response.status_code if response else 'No response'}", 
                         "buildings")
            return False
        
        try:
            buildings = response.json()
            if not isinstance(buildings, list):
                self.log_test("Anagram Building Verification", False, "Buildings response is not a list", "buildings")
                return False
            
            # Find Anagram Columbus Circle building
            anagram_building = None
            for building in buildings:
                if building.get('name') == self.expected_building['name']:
                    anagram_building = building
                    self.anagram_building_id = building.get('id')
                    break
            
            if not anagram_building:
                self.log_test("Anagram Building Verification", False, 
                             f"Anagram Columbus Circle building not found in {len(buildings)} buildings", 
                             "buildings")
                return False
            
            # Verify building details
            errors = []
            for key, expected_value in self.expected_building.items():
                actual_value = anagram_building.get(key)
                if actual_value != expected_value:
                    errors.append(f"{key}: expected '{expected_value}', got '{actual_value}'")
            
            if errors:
                self.log_test("Anagram Building Verification", False, 
                             f"Building details mismatch: {'; '.join(errors)}", 
                             "buildings")
                return False
            
            self.log_test("Anagram Building Verification", True, 
                         f"Building found with correct details (ID: {self.anagram_building_id})", 
                         "buildings")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Anagram Building Verification", False, "Invalid JSON response", "buildings")
            return False
        except Exception as e:
            self.log_test("Anagram Building Verification", False, f"Error processing response: {str(e)}", "buildings")
            return False

    def test_studio_unit_02c(self):
        """Test Studio 02C unit (9a8c3ba5-60c3-48a0-89af-d6e691c04381)"""
        unit_id = "9a8c3ba5-60c3-48a0-89af-d6e691c04381"
        expected = self.expected_units[unit_id]
        
        response = self.make_request('GET', f'units/{unit_id}')
        
        if not response or response.status_code != 200:
            self.log_test("Studio 02C Unit Verification", False, 
                         f"Failed to get unit: {response.status_code if response else 'No response'}", 
                         f"units/{unit_id}")
            return False
        
        try:
            unit = response.json()
            
            # Verify unit details
            errors = []
            if unit.get('rent') != expected['rent']:
                errors.append(f"rent: expected ${expected['rent']}, got ${unit.get('rent')}")
            if unit.get('bedrooms') != expected['bedrooms']:
                errors.append(f"bedrooms: expected {expected['bedrooms']}, got {unit.get('bedrooms')}")
            if unit.get('bathrooms') != expected['bathrooms']:
                errors.append(f"bathrooms: expected {expected['bathrooms']}, got {unit.get('bathrooms')}")
            if unit.get('is_available') != expected['is_available']:
                errors.append(f"is_available: expected {expected['is_available']}, got {unit.get('is_available')}")
            
            # Verify building association
            building = unit.get('building')
            if not building:
                errors.append("building association missing")
            elif building.get('id') != self.anagram_building_id:
                errors.append(f"wrong building association: expected {self.anagram_building_id}, got {building.get('id')}")
            elif building.get('name') != self.expected_building['name']:
                errors.append(f"building name mismatch: expected '{self.expected_building['name']}', got '{building.get('name')}'")
            
            if errors:
                self.log_test("Studio 02C Unit Verification", False, 
                             f"Unit details mismatch: {'; '.join(errors)}", 
                             f"units/{unit_id}")
                return False
            
            self.log_test("Studio 02C Unit Verification", True, 
                         f"Studio unit verified: ${unit.get('rent')}/month, {unit.get('bedrooms')}BR/{unit.get('bathrooms')}BA, available={unit.get('is_available')}", 
                         f"units/{unit_id}")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Studio 02C Unit Verification", False, "Invalid JSON response", f"units/{unit_id}")
            return False
        except Exception as e:
            self.log_test("Studio 02C Unit Verification", False, f"Error processing response: {str(e)}", f"units/{unit_id}")
            return False

    def test_two_bedroom_unit_21b(self):
        """Test Two Bedroom 21B unit (c350312e-9339-42da-8474-b02c04a575ae)"""
        unit_id = "c350312e-9339-42da-8474-b02c04a575ae"
        expected = self.expected_units[unit_id]
        
        response = self.make_request('GET', f'units/{unit_id}')
        
        if not response or response.status_code != 200:
            self.log_test("Two Bedroom 21B Unit Verification", False, 
                         f"Failed to get unit: {response.status_code if response else 'No response'}", 
                         f"units/{unit_id}")
            return False
        
        try:
            unit = response.json()
            
            # Verify unit details
            errors = []
            if unit.get('rent') != expected['rent']:
                errors.append(f"rent: expected ${expected['rent']}, got ${unit.get('rent')}")
            if unit.get('bedrooms') != expected['bedrooms']:
                errors.append(f"bedrooms: expected {expected['bedrooms']}, got {unit.get('bedrooms')}")
            if unit.get('bathrooms') != expected['bathrooms']:
                errors.append(f"bathrooms: expected {expected['bathrooms']}, got {unit.get('bathrooms')}")
            if unit.get('is_available') != expected['is_available']:
                errors.append(f"is_available: expected {expected['is_available']}, got {unit.get('is_available')}")
            
            # Verify building association
            building = unit.get('building')
            if not building:
                errors.append("building association missing")
            elif building.get('id') != self.anagram_building_id:
                errors.append(f"wrong building association: expected {self.anagram_building_id}, got {building.get('id')}")
            elif building.get('name') != self.expected_building['name']:
                errors.append(f"building name mismatch: expected '{self.expected_building['name']}', got '{building.get('name')}'")
            
            if errors:
                self.log_test("Two Bedroom 21B Unit Verification", False, 
                             f"Unit details mismatch: {'; '.join(errors)}", 
                             f"units/{unit_id}")
                return False
            
            self.log_test("Two Bedroom 21B Unit Verification", True, 
                         f"Two bedroom unit verified: ${unit.get('rent')}/month, {unit.get('bedrooms')}BR/{unit.get('bathrooms')}BA, available={unit.get('is_available')}", 
                         f"units/{unit_id}")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Two Bedroom 21B Unit Verification", False, "Invalid JSON response", f"units/{unit_id}")
            return False
        except Exception as e:
            self.log_test("Two Bedroom 21B Unit Verification", False, f"Error processing response: {str(e)}", f"units/{unit_id}")
            return False

    def test_units_list_contains_columbus_circle(self):
        """Test that units list query contains both Columbus Circle units"""
        response = self.make_request('GET', 'units?limit=200')
        
        if not response or response.status_code != 200:
            self.log_test("Units List Query Verification", False, 
                         f"Failed to get units list: {response.status_code if response else 'No response'}", 
                         "units?limit=200")
            return False
        
        try:
            units = response.json()
            if not isinstance(units, list):
                self.log_test("Units List Query Verification", False, "Units response is not a list", "units?limit=200")
                return False
            
            # Find Columbus Circle units
            found_units = {}
            for unit in units:
                unit_id = unit.get('id')
                if unit_id in self.expected_units:
                    found_units[unit_id] = unit
            
            # Check if both units are found
            missing_units = []
            for expected_unit_id in self.expected_units.keys():
                if expected_unit_id not in found_units:
                    missing_units.append(expected_unit_id)
            
            if missing_units:
                self.log_test("Units List Query Verification", False, 
                             f"Missing Columbus Circle units in list: {missing_units}", 
                             "units?limit=200")
                return False
            
            # Verify building info is included for found units
            errors = []
            for unit_id, unit in found_units.items():
                building = unit.get('building')
                if not building:
                    errors.append(f"Unit {unit_id}: missing building info")
                elif building.get('name') != self.expected_building['name']:
                    errors.append(f"Unit {unit_id}: wrong building name '{building.get('name')}'")
            
            if errors:
                self.log_test("Units List Query Verification", False, 
                             f"Building info issues: {'; '.join(errors)}", 
                             "units?limit=200")
                return False
            
            self.log_test("Units List Query Verification", True, 
                         f"Both Columbus Circle units found in list of {len(units)} units with correct building info", 
                         "units?limit=200")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Units List Query Verification", False, "Invalid JSON response", "units?limit=200")
            return False
        except Exception as e:
            self.log_test("Units List Query Verification", False, f"Error processing response: {str(e)}", "units?limit=200")
            return False

    def run_all_tests(self):
        """Run all Anagram Columbus Circle tests"""
        print("🏢 Starting Anagram Columbus Circle Building and Units Testing")
        print(f"🔗 Testing against: {self.backend_url}")
        print("=" * 70)
        
        print("\n🏗️ Building Verification")
        building_success = self.test_anagram_building_exists()
        
        if building_success:
            print("\n🏠 Unit Verification")
            self.test_studio_unit_02c()
            self.test_two_bedroom_unit_21b()
            
            print("\n📋 Units List Verification")
            self.test_units_list_contains_columbus_circle()
        else:
            print("❌ Skipping unit tests - building not found")
        
        # Results Summary
        print("\n" + "=" * 70)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Anagram Columbus Circle tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']}: {result['details']}")
            return 1

def main():
    tester = AnagramColumbusCircleTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())