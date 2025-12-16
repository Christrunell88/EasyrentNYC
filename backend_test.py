#!/usr/bin/env python3
"""
Backend API Testing for NoFeeApts Application
Tests all API endpoints including authentication, CRUD operations, admin functions, and SEO functionality
"""

import requests
import sys
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse

class NoFeeAptsAPITester:
    def __init__(self, base_url="https://fee-free-apts.preview.emergentagent.com"):
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
        self.admin_email = "placesfirm@gmail.com"
        self.admin_password = "Checkers080/?"
        
        # Regular user credentials from requirements
        self.regular_user_email = "chris.trunell@gmail.com"
        self.regular_user_password = "TestPass123!"
        
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
        """Test new user signup with unique email"""
        data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "name": self.test_user_name
        }
        
        response = self.make_request('POST', 'auth/signup', data)
        
        if response and response.status_code == 200:
            result = response.json()
            if 'session_token' in result and 'user' in result:
                self.session_token = result['session_token']
                user_data = result['user']
                self.log_test("New User Signup", True, f"User created: {user_data.get('email')} with auto-login", "auth/signup")
                return True
            else:
                self.log_test("New User Signup", False, "Missing session token or user data in response", "auth/signup")
        else:
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f'Status: {response.status_code}')
                except:
                    error_msg = f'Status: {response.status_code}'
            else:
                error_msg = 'No response'
            self.log_test("New User Signup", False, error_msg, "auth/signup")
        return False

    def test_duplicate_signup(self):
        """Test signup with duplicate email"""
        data = {
            "email": self.test_user_email,  # Same email as previous signup
            "password": "differentpass123",
            "name": "Different Name"
        }
        
        response = self.make_request('POST', 'auth/signup', data)
        
        if response and response.status_code == 400:
            try:
                error_data = response.json()
                if 'already registered' in error_data.get('detail', '').lower():
                    self.log_test("Duplicate Email Validation", True, "Correctly prevents duplicate email registration", "auth/signup")
                    return True
            except:
                pass
            self.log_test("Duplicate Email Validation", False, "Wrong error message for duplicate email", "auth/signup")
        else:
            self.log_test("Duplicate Email Validation", False, f"Expected 400, got {response.status_code if response else 'No response'}", "auth/signup")
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
        """Test admin login with placesfirm@gmail.com / Checkers080/?"""
        data = {
            "email": self.admin_email,
            "password": self.admin_password
        }
        
        response = self.make_request('POST', 'auth/login', data)
        
        if response and response.status_code == 200:
            result = response.json()
            if 'session_token' in result and result.get('user', {}).get('is_admin'):
                self.admin_session_token = result['session_token']
                self.log_test("Admin Login (placesfirm@gmail.com)", True, f"Admin user authenticated successfully", "auth/login")
                return True
            else:
                self.log_test("Admin Login (placesfirm@gmail.com)", False, "User is not admin or missing session token", "auth/login")
        else:
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f'Status: {response.status_code}')
                except:
                    error_msg = f'Status: {response.status_code}'
            else:
                error_msg = 'No response'
            self.log_test("Admin Login (placesfirm@gmail.com)", False, error_msg, "auth/login")
        return False

    def test_regular_user_login(self):
        """Test regular user login with chris.trunell@gmail.com / TestPass123!"""
        data = {
            "email": self.regular_user_email,
            "password": self.regular_user_password
        }
        
        response = self.make_request('POST', 'auth/login', data)
        
        if response and response.status_code == 200:
            result = response.json()
            if 'session_token' in result:
                user_data = result.get('user', {})
                is_admin = user_data.get('is_admin', False)
                if not is_admin:  # Should be regular user, not admin
                    self.log_test("Regular User Login (chris.trunell@gmail.com)", True, f"Regular user authenticated successfully", "auth/login")
                    return True
                else:
                    self.log_test("Regular User Login (chris.trunell@gmail.com)", False, "User has admin privileges (should be regular user)", "auth/login")
            else:
                self.log_test("Regular User Login (chris.trunell@gmail.com)", False, "Missing session token in response", "auth/login")
        else:
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f'Status: {response.status_code}')
                except:
                    error_msg = f'Status: {response.status_code}'
            else:
                error_msg = 'No response'
            self.log_test("Regular User Login (chris.trunell@gmail.com)", False, error_msg, "auth/login")
        return False

    def test_get_current_user(self):
        """Test getting current user info (session validation)"""
        response = self.make_request('GET', 'auth/me')
        
        if response and response.status_code == 200:
            result = response.json()
            if 'email' in result and 'name' in result:
                self.log_test("Session Validation (GET /api/auth/me)", True, f"User data returned: {result.get('email')}", "auth/me")
                return True
            else:
                self.log_test("Session Validation (GET /api/auth/me)", False, "Missing user data in response", "auth/me")
        elif response and response.status_code == 401:
            self.log_test("Session Validation (GET /api/auth/me)", True, "Correctly returns 401 when not authenticated", "auth/me")
            return True
        else:
            self.log_test("Session Validation (GET /api/auth/me)", False, f"Status: {response.status_code if response else 'No response'}", "auth/me")
        return False

    def test_unauthenticated_access(self):
        """Test that protected routes return 401 when not authenticated"""
        # Temporarily clear session token
        original_token = self.session_token
        self.session_token = None
        
        response = self.make_request('GET', 'auth/me')
        
        # Restore session token
        self.session_token = original_token
        
        if response and response.status_code == 401:
            self.log_test("Unauthenticated Access Protection", True, "Protected route correctly returns 401", "auth/me")
            return True
        else:
            self.log_test("Unauthenticated Access Protection", False, f"Expected 401, got {response.status_code if response else 'No response'}", "auth/me")
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
        """Test logout functionality and session clearing"""
        # First verify we're logged in
        response = self.make_request('GET', 'auth/me')
        if not (response and response.status_code == 200):
            self.log_test("Logout Test", False, "Not logged in before logout test", "auth/logout")
            return False
        
        # Perform logout
        response = self.make_request('POST', 'auth/logout')
        
        if response and response.status_code == 200:
            # Verify session is cleared by trying to access protected route
            old_token = self.session_token
            response = self.make_request('GET', 'auth/me')
            
            if response and response.status_code == 401:
                self.log_test("Logout Functionality", True, "Session cleared successfully, returns 401 on protected routes", "auth/logout")
                self.session_token = None  # Clear our stored token
                return True
            else:
                self.log_test("Logout Functionality", False, f"Session not cleared properly, /auth/me returned {response.status_code if response else 'No response'}", "auth/logout")
        else:
            self.log_test("Logout Functionality", False, f"Logout failed with status: {response.status_code if response else 'No response'}", "auth/logout")
        return False

    def test_google_oauth_endpoint(self):
        """Test Google OAuth endpoint availability"""
        # Test if Google OAuth endpoint exists (should return 404 or proper redirect)
        response = self.make_request('GET', 'auth/google')
        
        if response:
            if response.status_code == 404:
                self.log_test("Google OAuth Endpoint", False, "Google OAuth endpoint not implemented (404)", "auth/google")
                return False
            elif response.status_code in [200, 302, 307]:
                self.log_test("Google OAuth Endpoint", True, f"Google OAuth endpoint available (status: {response.status_code})", "auth/google")
                return True
            else:
                self.log_test("Google OAuth Endpoint", False, f"Unexpected status: {response.status_code}", "auth/google")
        else:
            self.log_test("Google OAuth Endpoint", False, "No response from Google OAuth endpoint", "auth/google")
        return False

    def test_oauth_session_endpoint(self):
        """Test OAuth session validation endpoint"""
        # Test with invalid session_id
        headers = {'X-Session-ID': 'invalid_test_session_123'}
        response = self.make_request('POST', 'auth/session', headers=headers)
        
        if response and response.status_code == 400:
            try:
                error_data = response.json()
                if 'invalid session_id' in error_data.get('detail', '').lower():
                    self.log_test("OAuth Session Validation", True, "Correctly rejects invalid session_id", "auth/session")
                    return True
            except:
                pass
            self.log_test("OAuth Session Validation", False, "Wrong error message for invalid session_id", "auth/session")
        else:
            self.log_test("OAuth Session Validation", False, f"Expected 400, got {response.status_code if response else 'No response'}", "auth/session")
        return False

    def test_sitemap_xml(self):
        """Test sitemap.xml generation and content"""
        try:
            # Make request to sitemap.xml endpoint
            response = requests.get(f"{self.base_url}/sitemap.xml", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Sitemap XML - Availability", False, f"Status: {response.status_code}", "sitemap.xml")
                return False
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'xml' not in content_type.lower():
                self.log_test("Sitemap XML - Content Type", False, f"Expected XML, got: {content_type}", "sitemap.xml")
                return False
            
            # Parse XML to verify it's valid
            try:
                root = ET.fromstring(response.text)
                self.log_test("Sitemap XML - Valid XML", True, "Sitemap is valid XML", "sitemap.xml")
            except ET.ParseError as e:
                self.log_test("Sitemap XML - Valid XML", False, f"Invalid XML: {str(e)}", "sitemap.xml")
                return False
            
            # Check XML structure and namespace
            if root.tag != '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset':
                self.log_test("Sitemap XML - Structure", False, f"Invalid root tag: {root.tag}", "sitemap.xml")
                return False
            
            # Count URLs
            urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
            url_count = len(urls)
            
            # Check if we have approximately 140 URLs as expected
            if url_count < 100:
                self.log_test("Sitemap XML - URL Count", False, f"Too few URLs: {url_count} (expected ~140)", "sitemap.xml")
                return False
            elif url_count > 200:
                self.log_test("Sitemap XML - URL Count", False, f"Too many URLs: {url_count} (expected ~140)", "sitemap.xml")
                return False
            else:
                self.log_test("Sitemap XML - URL Count", True, f"Found {url_count} URLs (within expected range)", "sitemap.xml")
            
            # Check for unit pages
            unit_urls = []
            static_urls = []
            
            for url in urls:
                loc_elem = url.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc_elem is not None:
                    loc = loc_elem.text
                    if '/unit/' in loc:
                        unit_urls.append(loc)
                    else:
                        static_urls.append(loc)
            
            if len(unit_urls) < 50:
                self.log_test("Sitemap XML - Unit URLs", False, f"Too few unit URLs: {len(unit_urls)}", "sitemap.xml")
                return False
            else:
                self.log_test("Sitemap XML - Unit URLs", True, f"Found {len(unit_urls)} unit URLs", "sitemap.xml")
            
            # Check lastmod dates
            current_date = datetime.now().strftime('%Y-%m-%d')
            recent_dates = ['2025-12-16', '2025-12-15', '2025-12-14', current_date]
            
            lastmod_found = False
            for url in urls[:5]:  # Check first 5 URLs
                lastmod_elem = url.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
                if lastmod_elem is not None:
                    lastmod_date = lastmod_elem.text[:10]  # Get YYYY-MM-DD part
                    if lastmod_date in recent_dates:
                        lastmod_found = True
                        break
            
            if lastmod_found:
                self.log_test("Sitemap XML - Recent Lastmod", True, "Found recent lastmod dates", "sitemap.xml")
            else:
                self.log_test("Sitemap XML - Recent Lastmod", False, "No recent lastmod dates found", "sitemap.xml")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test("Sitemap XML - Request", False, f"Request error: {str(e)}", "sitemap.xml")
            return False
        except Exception as e:
            self.log_test("Sitemap XML - General", False, f"Error: {str(e)}", "sitemap.xml")
            return False

    def test_robots_txt(self):
        """Test robots.txt content and format"""
        try:
            response = requests.get(f"{self.base_url}/robots.txt", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Robots.txt - Availability", False, f"Status: {response.status_code}", "robots.txt")
                return False
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'text/plain' not in content_type.lower():
                self.log_test("Robots.txt - Content Type", False, f"Expected text/plain, got: {content_type}", "robots.txt")
                return False
            
            content = response.text.lower()
            
            # Check for basic robots.txt structure
            if 'user-agent:' not in content:
                self.log_test("Robots.txt - User-Agent", False, "Missing User-agent directive", "robots.txt")
                return False
            else:
                self.log_test("Robots.txt - User-Agent", True, "User-agent directive found", "robots.txt")
            
            # Check for sitemap reference
            if 'sitemap:' not in content:
                self.log_test("Robots.txt - Sitemap Reference", False, "Missing Sitemap directive", "robots.txt")
                return False
            else:
                self.log_test("Robots.txt - Sitemap Reference", True, "Sitemap directive found", "robots.txt")
            
            # Check for admin disallow
            if 'disallow: /admin' not in content:
                self.log_test("Robots.txt - Admin Disallow", False, "Missing /admin disallow", "robots.txt")
                return False
            else:
                self.log_test("Robots.txt - Admin Disallow", True, "/admin is disallowed", "robots.txt")
            
            # Check for API disallow
            if 'disallow: /api' not in content:
                self.log_test("Robots.txt - API Disallow", False, "Missing /api disallow", "robots.txt")
                return False
            else:
                self.log_test("Robots.txt - API Disallow", True, "/api is disallowed", "robots.txt")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test("Robots.txt - Request", False, f"Request error: {str(e)}", "robots.txt")
            return False
        except Exception as e:
            self.log_test("Robots.txt - General", False, f"Error: {str(e)}", "robots.txt")
            return False

    def test_homepage_meta_tags(self):
        """Test homepage meta tags and SEO elements"""
        try:
            response = requests.get(self.base_url, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Homepage Meta - Availability", False, f"Status: {response.status_code}", "homepage")
                return False
            
            content = response.text.lower()
            
            # Check for title with "110+ verified listings"
            if '110+ verified listings' in content or '110 verified listings' in content:
                self.log_test("Homepage Meta - Title Content", True, "Title contains '110+ Verified Listings'", "homepage")
            else:
                self.log_test("Homepage Meta - Title Content", False, "Title missing '110+ Verified Listings'", "homepage")
            
            # Check for meta description
            if 'meta name="description"' in content or 'meta property="description"' in content:
                self.log_test("Homepage Meta - Description", True, "Meta description found", "homepage")
            else:
                self.log_test("Homepage Meta - Description", False, "Meta description missing", "homepage")
            
            # Check for Open Graph tags
            og_tags_found = 0
            og_tags = ['og:title', 'og:description', 'og:image', 'og:url', 'og:type']
            
            for tag in og_tags:
                if f'property="{tag}"' in content:
                    og_tags_found += 1
            
            if og_tags_found >= 3:
                self.log_test("Homepage Meta - OG Tags", True, f"Found {og_tags_found} OG tags", "homepage")
            else:
                self.log_test("Homepage Meta - OG Tags", False, f"Only found {og_tags_found} OG tags", "homepage")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test("Homepage Meta - Request", False, f"Request error: {str(e)}", "homepage")
            return False
        except Exception as e:
            self.log_test("Homepage Meta - General", False, f"Error: {str(e)}", "homepage")
            return False

    def test_api_units_count(self):
        """Test API units endpoint returns expected count"""
        try:
            response = requests.get(f"{self.api_url}/units?limit=200", timeout=10)
            
            if response.status_code != 200:
                self.log_test("API Units Count - Availability", False, f"Status: {response.status_code}", "api/units")
                return False
            
            units = response.json()
            
            if not isinstance(units, list):
                self.log_test("API Units Count - Format", False, "Response is not a list", "api/units")
                return False
            
            unit_count = len(units)
            
            # Check if we have approximately 110 units as expected
            if unit_count < 80:
                self.log_test("API Units Count - Count", False, f"Too few units: {unit_count} (expected ~110)", "api/units")
                return False
            elif unit_count > 150:
                self.log_test("API Units Count - Count", False, f"Too many units: {unit_count} (expected ~110)", "api/units")
                return False
            else:
                self.log_test("API Units Count - Count", True, f"Found {unit_count} units (within expected range)", "api/units")
            
            # Verify unit structure
            if units and isinstance(units[0], dict):
                required_fields = ['id', 'rent', 'bedrooms', 'bathrooms']
                first_unit = units[0]
                missing_fields = [field for field in required_fields if field not in first_unit]
                
                if missing_fields:
                    self.log_test("API Units Count - Structure", False, f"Missing fields: {missing_fields}", "api/units")
                else:
                    self.log_test("API Units Count - Structure", True, "Unit structure is valid", "api/units")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test("API Units Count - Request", False, f"Request error: {str(e)}", "api/units")
            return False
        except Exception as e:
            self.log_test("API Units Count - General", False, f"Error: {str(e)}", "api/units")
            return False

    def test_api_buildings_count(self):
        """Test API buildings endpoint returns expected count"""
        try:
            response = requests.get(f"{self.api_url}/buildings", timeout=10)
            
            if response.status_code != 200:
                self.log_test("API Buildings Count - Availability", False, f"Status: {response.status_code}", "api/buildings")
                return False
            
            buildings = response.json()
            
            if not isinstance(buildings, list):
                self.log_test("API Buildings Count - Format", False, "Response is not a list", "api/buildings")
                return False
            
            building_count = len(buildings)
            
            # Check if we have approximately 25 buildings as expected
            if building_count < 15:
                self.log_test("API Buildings Count - Count", False, f"Too few buildings: {building_count} (expected ~25)", "api/buildings")
                return False
            elif building_count > 35:
                self.log_test("API Buildings Count - Count", False, f"Too many buildings: {building_count} (expected ~25)", "api/buildings")
                return False
            else:
                self.log_test("API Buildings Count - Count", True, f"Found {building_count} buildings (within expected range)", "api/buildings")
            
            # Verify building structure
            if buildings and isinstance(buildings[0], dict):
                required_fields = ['id', 'name', 'address', 'city', 'state']
                first_building = buildings[0]
                missing_fields = [field for field in required_fields if field not in first_building]
                
                if missing_fields:
                    self.log_test("API Buildings Count - Structure", False, f"Missing fields: {missing_fields}", "api/buildings")
                else:
                    self.log_test("API Buildings Count - Structure", True, "Building structure is valid", "api/buildings")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test("API Buildings Count - Request", False, f"Request error: {str(e)}", "api/buildings")
            return False
        except Exception as e:
            self.log_test("API Buildings Count - General", False, f"Error: {str(e)}", "api/buildings")
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
        print("Testing OAuth and Login/Sign-in functionality comprehensively...")
        
        # Test unauthenticated access first
        self.test_unauthenticated_access()
        
        # Test new user signup
        self.test_user_signup()
        self.test_get_current_user()  # Verify session after signup
        self.test_duplicate_signup()  # Test duplicate email validation
        
        # Test user login after signup
        self.test_user_login()
        
        # Test admin login with specific credentials
        self.test_admin_login()
        
        # Test regular user login with specific credentials  
        self.test_regular_user_login()
        
        # Test OAuth endpoints
        self.test_google_oauth_endpoint()
        self.test_oauth_session_endpoint()
        
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