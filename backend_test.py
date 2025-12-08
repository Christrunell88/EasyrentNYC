#!/usr/bin/env python3
"""
Backend API Testing for NoFeeApts Application
Tests all API endpoints including authentication, CRUD operations, and admin functions
"""

import requests
import sys
import json
from datetime import datetime

class NoFeeAptsAPITester:
    def __init__(self, base_url="https://zerofeerentals.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.admin_session_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        self.test_user_email = f"testuser_{datetime.now().strftime('%H%M%S')}@example.com"
        self.test_user_name = "Test User"
        self.test_user_password = "testpass123"
        
        # Admin credentials from requirements
        self.admin_email = "admin@nofeesapts.com"
        self.admin_password = "admin123"
        
        self.created_building_id = None
        self.created_unit_id = None

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

    def make_request(self, method, endpoint, data=None, headers=None, use_admin=False):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        
        # Set up headers
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        
        # Add auth token if available
        token = self.admin_session_token if use_admin else self.session_token
        if token:
            req_headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=10)
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request error for {method} {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {method} {url}: {e}")
            return None

    def test_user_signup(self):
        """Test user signup"""
        data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "name": self.test_user_name
        }
        
        response = self.make_request('POST', 'auth/signup', data)
        
        if response and response.status_code == 200:
            result = response.json()
            if 'session_token' in result:
                self.session_token = result['session_token']
                self.log_test("User Signup", True, endpoint="auth/signup")
                return True
        
        self.log_test("User Signup", False, f"Status: {response.status_code if response else 'No response'}", "auth/signup")
        return False

    def test_user_login(self):
        """Test user login with email/password"""
        data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        response = self.make_request('POST', 'auth/login', data)
        
        if response and response.status_code == 200:
            result = response.json()
            if 'session_token' in result:
                self.session_token = result['session_token']
                self.log_test("User Login", True, endpoint="auth/login")
                return True
        
        self.log_test("User Login", False, f"Status: {response.status_code if response else 'No response'}", "auth/login")
        return False

    def test_admin_login(self):
        """Test admin login"""
        data = {
            "email": self.admin_email,
            "password": self.admin_password
        }
        
        response = self.make_request('POST', 'auth/login', data)
        
        if response and response.status_code == 200:
            result = response.json()
            if 'session_token' in result and result.get('user', {}).get('is_admin'):
                self.admin_session_token = result['session_token']
                self.log_test("Admin Login", True, endpoint="auth/login")
                return True
        
        self.log_test("Admin Login", False, f"Status: {response.status_code if response else 'No response'}", "auth/login")
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        response = self.make_request('GET', 'auth/me')
        
        if response and response.status_code == 200:
            result = response.json()
            if 'email' in result:
                self.log_test("Get Current User", True, endpoint="auth/me")
                return True
        
        self.log_test("Get Current User", False, f"Status: {response.status_code if response else 'No response'}", "auth/me")
        return False

    def test_get_buildings(self):
        """Test getting all buildings"""
        response = self.make_request('GET', 'buildings')
        
        if response and response.status_code == 200:
            buildings = response.json()
            if isinstance(buildings, list):
                self.log_test("Get Buildings", True, f"Found {len(buildings)} buildings", "buildings")
                return True
        
        self.log_test("Get Buildings", False, f"Status: {response.status_code if response else 'No response'}", "buildings")
        return False

    def test_get_units(self):
        """Test getting units with filters"""
        # Test basic units endpoint
        response = self.make_request('GET', 'units')
        
        if response and response.status_code == 200:
            units = response.json()
            if isinstance(units, list):
                self.log_test("Get Units", True, f"Found {len(units)} units", "units")
                
                # Test with filters
                response = self.make_request('GET', 'units?bedrooms=1&min_rent=1000&max_rent=5000')
                if response and response.status_code == 200:
                    filtered_units = response.json()
                    self.log_test("Get Units with Filters", True, f"Found {len(filtered_units)} filtered units", "units")
                    return True
        
        self.log_test("Get Units", False, f"Status: {response.status_code if response else 'No response'}", "units")
        return False

    def test_create_building(self):
        """Test creating a building (admin only)"""
        data = {
            "name": "Test Building",
            "address": "123 Test Street",
            "neighborhood": "Test Neighborhood",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "source_url": "https://example.com/test-building"
        }
        
        response = self.make_request('POST', 'buildings', data, use_admin=True)
        
        if response and response.status_code == 200:
            result = response.json()
            if 'id' in result:
                self.created_building_id = result['id']
                self.log_test("Create Building", True, endpoint="buildings")
                return True
        
        self.log_test("Create Building", False, f"Status: {response.status_code if response else 'No response'}", "buildings")
        return False

    def test_create_unit(self):
        """Test creating a unit (admin only)"""
        if not self.created_building_id:
            self.log_test("Create Unit", False, "No building ID available", "units")
            return False
        
        data = {
            "building_id": self.created_building_id,
            "unit_number": "1A",
            "rent": 2500.0,
            "bedrooms": 1,
            "bathrooms": 1.0,
            "square_feet": 800,
            "available_date": "Immediate",
            "amenities": ["Gym", "Pool"],
            "images": ["https://example.com/image1.jpg"],
            "description": "Test unit description"
        }
        
        response = self.make_request('POST', 'units', data, use_admin=True)
        
        if response and response.status_code == 200:
            result = response.json()
            if 'id' in result:
                self.created_unit_id = result['id']
                self.log_test("Create Unit", True, endpoint="units")
                return True
        
        self.log_test("Create Unit", False, f"Status: {response.status_code if response else 'No response'}", "units")
        return False

    def test_favorites(self):
        """Test favorites functionality"""
        if not self.created_unit_id:
            self.log_test("Test Favorites", False, "No unit ID available", "favorites")
            return False
        
        # Add to favorites
        response = self.make_request('POST', f'favorites/{self.created_unit_id}')
        
        if response and response.status_code == 200:
            # Get favorites
            response = self.make_request('GET', 'favorites')
            if response and response.status_code == 200:
                favorites = response.json()
                if isinstance(favorites, list):
                    self.log_test("Add to Favorites", True, endpoint="favorites")
                    
                    # Remove from favorites
                    response = self.make_request('DELETE', f'favorites/{self.created_unit_id}')
                    if response and response.status_code == 200:
                        self.log_test("Remove from Favorites", True, endpoint="favorites")
                        return True
        
        self.log_test("Test Favorites", False, f"Status: {response.status_code if response else 'No response'}", "favorites")
        return False

    def test_contact_submission(self):
        """Test contact form submission"""
        if not self.created_unit_id:
            self.log_test("Contact Submission", False, "No unit ID available", "contact")
            return False
        
        data = {
            "unit_id": self.created_unit_id,
            "name": "Test Contact",
            "email": "test@example.com",
            "phone": "555-1234",
            "message": "I'm interested in this unit"
        }
        
        response = self.make_request('POST', 'contact', data)
        
        if response and response.status_code == 200:
            self.log_test("Contact Submission", True, endpoint="contact")
            return True
        
        self.log_test("Contact Submission", False, f"Status: {response.status_code if response else 'No response'}", "contact")
        return False

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        # Test get users
        response = self.make_request('GET', 'admin/users', use_admin=True)
        
        if response and response.status_code == 200:
            users = response.json()
            if isinstance(users, list):
                self.log_test("Admin Get Users", True, f"Found {len(users)} users", "admin/users")
            else:
                self.log_test("Admin Get Users", False, "Invalid response format", "admin/users")
        else:
            self.log_test("Admin Get Users", False, f"Status: {response.status_code if response else 'No response'}", "admin/users")
        
        # Test get stats
        response = self.make_request('GET', 'admin/stats', use_admin=True)
        
        if response and response.status_code == 200:
            stats = response.json()
            if isinstance(stats, dict):
                self.log_test("Admin Get Stats", True, endpoint="admin/stats")
            else:
                self.log_test("Admin Get Stats", False, "Invalid response format", "admin/stats")
        else:
            self.log_test("Admin Get Stats", False, f"Status: {response.status_code if response else 'No response'}", "admin/stats")
        
        # Test get contact requests
        response = self.make_request('GET', 'contact', use_admin=True)
        
        if response and response.status_code == 200:
            contacts = response.json()
            if isinstance(contacts, list):
                self.log_test("Admin Get Contacts", True, f"Found {len(contacts)} contacts", "contact")
                return True
            else:
                self.log_test("Admin Get Contacts", False, "Invalid response format", "contact")
        else:
            self.log_test("Admin Get Contacts", False, f"Status: {response.status_code if response else 'No response'}", "contact")
        
        return False

    def test_logout(self):
        """Test logout functionality"""
        response = self.make_request('POST', 'auth/logout')
        
        if response and response.status_code == 200:
            self.log_test("Logout", True, endpoint="auth/logout")
            return True
        
        self.log_test("Logout", False, f"Status: {response.status_code if response else 'No response'}", "auth/logout")
        return False

    def cleanup(self):
        """Clean up test data"""
        if self.created_unit_id and self.admin_session_token:
            response = self.make_request('DELETE', f'units/{self.created_unit_id}', use_admin=True)
            if response and response.status_code == 200:
                print("✅ Cleaned up test unit")
        
        if self.created_building_id and self.admin_session_token:
            response = self.make_request('DELETE', f'buildings/{self.created_building_id}', use_admin=True)
            if response and response.status_code == 200:
                print("✅ Cleaned up test building")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting NoFeeApts Backend API Tests")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Authentication Tests
        print("\n📝 Authentication Tests")
        self.test_user_signup()
        self.test_get_current_user()
        self.test_user_login()  # Test login after signup
        self.test_admin_login()
        
        # Public Endpoints Tests
        print("\n🏢 Public Endpoints Tests")
        self.test_get_buildings()
        self.test_get_units()
        
        # Admin Tests
        print("\n👑 Admin Tests")
        self.test_create_building()
        self.test_create_unit()
        self.test_admin_endpoints()
        
        # User Features Tests
        print("\n❤️ User Features Tests")
        self.test_favorites()
        self.test_contact_submission()
        
        # Cleanup and Logout
        print("\n🧹 Cleanup Tests")
        self.test_logout()
        self.cleanup()
        
        # Results Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']}: {result['details']}")
            return 1

def main():
    tester = NoFeeAptsAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())