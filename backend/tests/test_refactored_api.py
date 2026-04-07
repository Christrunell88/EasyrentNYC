"""
Backend API Tests for NoFeesApts.com - Post-Refactoring Validation
Tests all major API endpoints after server.py was split into modular route files.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "placesfirm@gmail.com"
ADMIN_PASSWORD = "Checkers080/?"
USER_EMAIL = "chris.trunell@gmail.com"
USER_PASSWORD = "TestPass123!"


class TestPublicEndpoints:
    """Test public API endpoints that don't require authentication"""
    
    def test_get_buildings(self):
        """GET /api/buildings - returns list of buildings"""
        response = requests.get(f"{BASE_URL}/api/buildings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert 'id' in data[0]
            assert 'name' in data[0]
            print(f"✓ GET /api/buildings - returned {len(data)} buildings")
    
    def test_get_units(self):
        """GET /api/units - returns list of available units"""
        response = requests.get(f"{BASE_URL}/api/units?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert 'id' in data[0]
            assert 'rent' in data[0]
            assert 'bedrooms' in data[0]
            print(f"✓ GET /api/units - returned {len(data)} units")
    
    def test_get_units_with_filters(self):
        """GET /api/units with filters"""
        response = requests.get(f"{BASE_URL}/api/units?bedrooms=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned units should have 1 bedroom
        for unit in data:
            assert unit.get('bedrooms') == 1
        print(f"✓ GET /api/units with bedrooms filter - returned {len(data)} units")
    
    def test_get_public_stats(self):
        """GET /api/stats - returns public platform statistics"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert 'total_buildings' in data
        assert 'total_units' in data
        assert 'available_units' in data
        print(f"✓ GET /api/stats - buildings: {data['total_buildings']}, units: {data['total_units']}")
    
    def test_get_social_proof(self):
        """GET /api/social-proof - returns social proof metrics"""
        response = requests.get(f"{BASE_URL}/api/social-proof")
        assert response.status_code == 200
        data = response.json()
        assert 'total_users' in data
        assert 'total_units' in data
        assert 'total_subscribers' in data
        print(f"✓ GET /api/social-proof - users: {data['total_users']}, units: {data['total_units']}")
    
    def test_get_hero_units(self):
        """GET /api/units/hero-carousel - returns featured units for hero"""
        response = requests.get(f"{BASE_URL}/api/units/hero-carousel?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/units/hero-carousel - returned {len(data)} hero units")
    
    def test_get_recent_units(self):
        """GET /api/units/recent - returns recently added units"""
        response = requests.get(f"{BASE_URL}/api/units/recent?limit=6")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/units/recent - returned {len(data)} recent units")
    
    def test_get_recommendations(self):
        """GET /api/recommendations - returns smart filter recommendations"""
        response = requests.get(f"{BASE_URL}/api/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert 'recommendations' in data
        assert 'total_available' in data
        print(f"✓ GET /api/recommendations - {len(data['recommendations'])} recommendations")
    
    def test_get_neighborhoods(self):
        """GET /api/neighborhoods - returns all neighborhoods with stats"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert 'name' in data[0]
            assert 'count' in data[0]
        print(f"✓ GET /api/neighborhoods - returned {len(data)} neighborhoods")
    
    def test_get_services_status(self):
        """GET /api/services/status - returns external services status"""
        response = requests.get(f"{BASE_URL}/api/services/status")
        assert response.status_code == 200
        data = response.json()
        assert 'email_service' in data
        assert 'sms_service' in data
        assert 'calendar_service' in data
        print(f"✓ GET /api/services/status - email: {data['email_service']}, sms: {data['sms_service']}")


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """POST /api/auth/login - successful login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'user' in data
        assert 'session_token' in data
        assert data['user']['email'] == ADMIN_EMAIL
        assert data['user']['is_admin'] == True
        print(f"✓ POST /api/auth/login - admin login successful")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - fails with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print(f"✓ POST /api/auth/login - correctly rejects invalid credentials")
    
    def test_signup_and_login(self):
        """POST /api/auth/signup - creates new user"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "TestPass123!"
        
        # Signup
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={"email": test_email, "password": test_password, "name": "Test User"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'user' in data
        assert data['user']['email'] == test_email
        print(f"✓ POST /api/auth/signup - created user {test_email}")
        
        # Login with new user
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": test_password}
        )
        assert response.status_code == 200
        print(f"✓ New user can login successfully")
    
    def test_get_me_requires_auth(self):
        """GET /api/auth/me - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print(f"✓ GET /api/auth/me - correctly requires authentication")
    
    def test_get_me_with_session(self):
        """GET /api/auth/me - returns user with valid session"""
        # Login first
        session = requests.Session()
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.status_code == 200
        
        # Get me
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data['email'] == ADMIN_EMAIL
        print(f"✓ GET /api/auth/me - returns current user")


class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    @pytest.fixture(autouse=True)
    def admin_session(self):
        """Create authenticated admin session"""
        self.session = requests.Session()
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        yield
    
    def test_get_admin_stats(self):
        """GET /api/admin/stats - returns admin statistics"""
        response = self.session.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert 'total_buildings' in data
        assert 'total_units' in data
        assert 'total_users' in data
        assert 'total_contacts' in data
        assert 'total_subscribers' in data
        print(f"✓ GET /api/admin/stats - users: {data['total_users']}, contacts: {data['total_contacts']}")
    
    def test_get_admin_users(self):
        """GET /api/admin/users - returns all users"""
        response = self.session.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/admin/users - returned {len(data)} users")
    
    def test_get_admin_subscribers(self):
        """GET /api/admin/subscribers - returns email subscribers"""
        response = self.session.get(f"{BASE_URL}/api/admin/subscribers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/admin/subscribers - returned {len(data)} subscribers")
    
    def test_get_staging_units(self):
        """GET /api/admin/staging/units - returns staging units"""
        response = self.session.get(f"{BASE_URL}/api/admin/staging/units?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert 'pending' in data
        print(f"✓ GET /api/admin/staging/units - pending: {data['pending']}, total: {data['total']}")
    
    def test_get_staging_stats(self):
        """GET /api/admin/staging/stats - returns staging statistics"""
        response = self.session.get(f"{BASE_URL}/api/admin/staging/stats")
        assert response.status_code == 200
        data = response.json()
        assert 'buildings_staging' in data
        assert 'units_staging' in data
        assert 'unavailability_reviews' in data
        print(f"✓ GET /api/admin/staging/stats - units pending: {data['units_staging']['pending']}")
    
    def test_get_unavailability_reviews(self):
        """GET /api/admin/unavailability-reviews - returns unavailability reviews"""
        response = self.session.get(f"{BASE_URL}/api/admin/unavailability-reviews?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        print(f"✓ GET /api/admin/unavailability-reviews - total: {data['total']}")
    
    def test_get_unavailable_units(self):
        """GET /api/admin/units/unavailable - returns unavailable/rented units"""
        response = self.session.get(f"{BASE_URL}/api/admin/units/unavailable")
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        print(f"✓ GET /api/admin/units/unavailable - total: {data['total']}")
    
    def test_get_rejected_staging(self):
        """GET /api/admin/staging/rejected - returns rejected staging units"""
        response = self.session.get(f"{BASE_URL}/api/admin/staging/rejected")
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        print(f"✓ GET /api/admin/staging/rejected - total: {data['total']}")


class TestAuthenticatedUserEndpoints:
    """Test endpoints that require regular user authentication"""
    
    @pytest.fixture(autouse=True)
    def user_session(self):
        """Create authenticated user session"""
        self.session = requests.Session()
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": USER_EMAIL, "password": USER_PASSWORD}
        )
        if response.status_code != 200:
            # Create user if doesn't exist
            signup_response = self.session.post(
                f"{BASE_URL}/api/auth/signup",
                json={"email": USER_EMAIL, "password": USER_PASSWORD, "name": "Test User"}
            )
            if signup_response.status_code == 200:
                print(f"Created test user: {USER_EMAIL}")
            else:
                pytest.skip(f"Could not create/login test user: {signup_response.text}")
        yield
    
    def test_get_favorites(self):
        """GET /api/favorites - returns user's favorites"""
        response = self.session.get(f"{BASE_URL}/api/favorites")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/favorites - returned {len(data)} favorites")
    
    def test_get_saved_searches(self):
        """GET /api/saved-searches - returns user's saved searches"""
        response = self.session.get(f"{BASE_URL}/api/saved-searches")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/saved-searches - returned {len(data)} saved searches")
    
    def test_favorites_crud(self):
        """Test favorites add/remove flow"""
        # Get a unit to favorite
        units_response = requests.get(f"{BASE_URL}/api/units?limit=1")
        units = units_response.json()
        if not units:
            pytest.skip("No units available to test favorites")
        
        unit_id = units[0]['id']
        
        # Add to favorites
        add_response = self.session.post(f"{BASE_URL}/api/favorites/{unit_id}")
        assert add_response.status_code == 200
        print(f"✓ POST /api/favorites/{unit_id} - added to favorites")
        
        # Verify in favorites list
        list_response = self.session.get(f"{BASE_URL}/api/favorites")
        favorites = list_response.json()
        unit_ids = [f['unit']['id'] for f in favorites if f.get('unit')]
        assert unit_id in unit_ids
        print(f"✓ Verified unit in favorites list")
        
        # Remove from favorites
        remove_response = self.session.delete(f"{BASE_URL}/api/favorites/{unit_id}")
        assert remove_response.status_code == 200
        print(f"✓ DELETE /api/favorites/{unit_id} - removed from favorites")
    
    def test_saved_search_crud(self):
        """Test saved search create/toggle/delete flow"""
        # Create saved search
        search_data = {
            "name": f"Test Search {uuid.uuid4().hex[:6]}",
            "bedrooms": 1,
            "min_rent": 2000,
            "max_rent": 4000,
            "alert_frequency": "daily",
            "notify_email": True,
            "notify_sms": False
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/api/saved-searches",
            json=search_data
        )
        assert create_response.status_code == 200
        data = create_response.json()
        assert 'search' in data
        search_id = data['search']['id']
        print(f"✓ POST /api/saved-searches - created search {search_id}")
        
        # Toggle active status
        toggle_response = self.session.put(f"{BASE_URL}/api/saved-searches/{search_id}/toggle")
        assert toggle_response.status_code == 200
        print(f"✓ PUT /api/saved-searches/{search_id}/toggle - toggled status")
        
        # Delete saved search
        delete_response = self.session.delete(f"{BASE_URL}/api/saved-searches/{search_id}")
        assert delete_response.status_code == 200
        print(f"✓ DELETE /api/saved-searches/{search_id} - deleted search")


class TestContactEndpoints:
    """Test contact and subscription endpoints"""
    
    def test_subscribe_email(self):
        """POST /api/subscribe - subscribes email for alerts"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/subscribe",
            json={"email": test_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') == True
        print(f"✓ POST /api/subscribe - subscribed {test_email}")
    
    def test_subscribe_duplicate_email(self):
        """POST /api/subscribe - rejects duplicate email"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        # First subscription
        requests.post(f"{BASE_URL}/api/subscribe", json={"email": test_email})
        
        # Duplicate subscription
        response = requests.post(f"{BASE_URL}/api/subscribe", json={"email": test_email})
        assert response.status_code == 400
        print(f"✓ POST /api/subscribe - correctly rejects duplicate")


class TestUnitDetailEndpoints:
    """Test unit detail and related endpoints"""
    
    def test_get_unit_by_id(self):
        """GET /api/units/{unit_id} - returns unit details"""
        # Get a unit first
        units_response = requests.get(f"{BASE_URL}/api/units?limit=1")
        units = units_response.json()
        if not units:
            pytest.skip("No units available")
        
        unit_id = units[0]['id']
        response = requests.get(f"{BASE_URL}/api/units/{unit_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == unit_id
        assert 'building' in data
        print(f"✓ GET /api/units/{unit_id} - returned unit with building info")
    
    def test_get_unit_not_found(self):
        """GET /api/units/{unit_id} - returns 404 for non-existent unit"""
        response = requests.get(f"{BASE_URL}/api/units/non-existent-id")
        assert response.status_code == 404
        print(f"✓ GET /api/units/non-existent-id - correctly returns 404")
    
    def test_get_share_preview(self):
        """GET /api/share/{unit_id} - returns HTML share preview"""
        # Get a unit first
        units_response = requests.get(f"{BASE_URL}/api/units?limit=1")
        units = units_response.json()
        if not units:
            pytest.skip("No units available")
        
        unit_id = units[0]['id']
        response = requests.get(f"{BASE_URL}/api/share/{unit_id}")
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
        assert 'og:title' in response.text
        print(f"✓ GET /api/share/{unit_id} - returned HTML with OG tags")


class TestBuildingEndpoints:
    """Test building-related endpoints"""
    
    def test_get_building_by_id(self):
        """GET /api/buildings/{building_id} - returns building details"""
        # Get a building first
        buildings_response = requests.get(f"{BASE_URL}/api/buildings")
        buildings = buildings_response.json()
        if not buildings:
            pytest.skip("No buildings available")
        
        building_id = buildings[0]['id']
        response = requests.get(f"{BASE_URL}/api/buildings/{building_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == building_id
        print(f"✓ GET /api/buildings/{building_id} - returned building details")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
