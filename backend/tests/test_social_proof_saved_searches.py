"""
Test suite for Social Proof and Saved Searches features
Tests:
- GET /api/social-proof - Social proof data for landing page
- POST /api/saved-searches - Create saved search (authenticated)
- GET /api/saved-searches - Get user's saved searches (authenticated)
- PUT /api/saved-searches/{id}/toggle - Toggle search active/inactive
- DELETE /api/saved-searches/{id} - Delete a saved search
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "chris.trunell@gmail.com"
TEST_USER_PASSWORD = "TestPass123!"


class TestSocialProof:
    """Tests for social proof endpoint"""
    
    def test_social_proof_returns_data(self):
        """GET /api/social-proof should return social proof metrics"""
        response = requests.get(f"{BASE_URL}/api/social-proof")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify all expected fields are present
        assert 'signups_today' in data, "Missing signups_today field"
        assert 'signups_this_week' in data, "Missing signups_this_week field"
        assert 'total_users' in data, "Missing total_users field"
        assert 'inquiries_today' in data, "Missing inquiries_today field"
        assert 'active_searches' in data, "Missing active_searches field"
        assert 'total_units' in data, "Missing total_units field"
        assert 'total_subscribers' in data, "Missing total_subscribers field"
        assert 'generated_at' in data, "Missing generated_at field"
        
        # Verify data types
        assert isinstance(data['signups_today'], int), "signups_today should be int"
        assert isinstance(data['total_users'], int), "total_users should be int"
        assert isinstance(data['total_units'], int), "total_units should be int"
        
        # Verify reasonable values
        assert data['total_users'] >= 0, "total_users should be non-negative"
        assert data['total_units'] >= 0, "total_units should be non-negative"
        
        print(f"Social proof data: {data}")


class TestSavedSearches:
    """Tests for saved searches CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get session token before each test"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        self.session_token = login_response.json().get('session_token')
        self.headers = {
            "Authorization": f"Bearer {self.session_token}",
            "Content-Type": "application/json"
        }
        self.created_search_ids = []
        
        yield
        
        # Cleanup: delete any searches created during tests
        for search_id in self.created_search_ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/saved-searches/{search_id}",
                    headers=self.headers
                )
            except:
                pass
    
    def test_saved_searches_requires_auth(self):
        """GET /api/saved-searches should require authentication"""
        response = requests.get(f"{BASE_URL}/api/saved-searches")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_create_saved_search_requires_auth(self):
        """POST /api/saved-searches should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/saved-searches",
            json={"name": "Test Search", "alert_frequency": "daily"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_get_saved_searches_authenticated(self):
        """GET /api/saved-searches should return user's searches when authenticated"""
        response = requests.get(
            f"{BASE_URL}/api/saved-searches",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"User has {len(data)} saved searches")
    
    def test_create_saved_search(self):
        """POST /api/saved-searches should create a new saved search"""
        unique_name = f"TEST_Search_{uuid.uuid4().hex[:8]}"
        
        search_data = {
            "name": unique_name,
            "bedrooms": 1,
            "min_rent": 2000,
            "max_rent": 4000,
            "state": "NY",
            "alert_frequency": "daily"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/saved-searches",
            headers=self.headers,
            json=search_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'message' in data, "Response should contain message"
        assert 'search' in data, "Response should contain search object"
        assert data['search']['name'] == unique_name, "Search name should match"
        
        # Store for cleanup
        self.created_search_ids.append(data['search']['id'])
        
        print(f"Created saved search: {data['search']}")
    
    def test_create_saved_search_with_all_filters(self):
        """POST /api/saved-searches should accept all filter options"""
        unique_name = f"TEST_FullFilter_{uuid.uuid4().hex[:8]}"
        
        search_data = {
            "name": unique_name,
            "bedrooms": 2,
            "min_rent": 3000,
            "max_rent": 5000,
            "bathrooms": 1.5,
            "state": "NJ",
            "neighborhood": "Jersey City",
            "alert_frequency": "weekly"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/saved-searches",
            headers=self.headers,
            json=search_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        self.created_search_ids.append(data['search']['id'])
        
        # Verify the search was created by fetching it
        get_response = requests.get(
            f"{BASE_URL}/api/saved-searches",
            headers=self.headers
        )
        
        searches = get_response.json()
        created_search = next((s for s in searches if s['id'] == data['search']['id']), None)
        
        assert created_search is not None, "Created search should be in list"
        assert created_search['name'] == unique_name
        assert created_search['bedrooms'] == 2
        assert created_search['min_rent'] == 3000
        assert created_search['max_rent'] == 5000
        assert created_search['state'] == "NJ"
        
        print(f"Verified saved search with all filters: {created_search}")
    
    def test_toggle_saved_search(self):
        """PUT /api/saved-searches/{id}/toggle should toggle active status"""
        # First create a search
        unique_name = f"TEST_Toggle_{uuid.uuid4().hex[:8]}"
        
        create_response = requests.post(
            f"{BASE_URL}/api/saved-searches",
            headers=self.headers,
            json={"name": unique_name, "alert_frequency": "daily"}
        )
        
        assert create_response.status_code == 200
        search_id = create_response.json()['search']['id']
        self.created_search_ids.append(search_id)
        
        # Toggle the search (should disable it since default is active)
        toggle_response = requests.put(
            f"{BASE_URL}/api/saved-searches/{search_id}/toggle",
            headers=self.headers
        )
        
        assert toggle_response.status_code == 200, f"Expected 200, got {toggle_response.status_code}: {toggle_response.text}"
        
        data = toggle_response.json()
        assert 'message' in data, "Response should contain message"
        assert 'is_active' in data, "Response should contain is_active"
        
        first_toggle_state = data['is_active']
        print(f"After first toggle, is_active: {first_toggle_state}")
        
        # Toggle again to verify it switches back
        toggle_response2 = requests.put(
            f"{BASE_URL}/api/saved-searches/{search_id}/toggle",
            headers=self.headers
        )
        
        assert toggle_response2.status_code == 200
        data2 = toggle_response2.json()
        
        assert data2['is_active'] != first_toggle_state, "Toggle should switch the state"
        print(f"After second toggle, is_active: {data2['is_active']}")
    
    def test_delete_saved_search(self):
        """DELETE /api/saved-searches/{id} should delete the search"""
        # First create a search
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:8]}"
        
        create_response = requests.post(
            f"{BASE_URL}/api/saved-searches",
            headers=self.headers,
            json={"name": unique_name, "alert_frequency": "daily"}
        )
        
        assert create_response.status_code == 200
        search_id = create_response.json()['search']['id']
        
        # Delete the search
        delete_response = requests.delete(
            f"{BASE_URL}/api/saved-searches/{search_id}",
            headers=self.headers
        )
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert 'message' in data, "Response should contain message"
        
        # Verify it's deleted by trying to get it
        get_response = requests.get(
            f"{BASE_URL}/api/saved-searches",
            headers=self.headers
        )
        
        searches = get_response.json()
        deleted_search = next((s for s in searches if s['id'] == search_id), None)
        
        assert deleted_search is None, "Deleted search should not be in list"
        print(f"Successfully deleted search {search_id}")
    
    def test_delete_nonexistent_search(self):
        """DELETE /api/saved-searches/{id} should return 404 for non-existent search"""
        fake_id = str(uuid.uuid4())
        
        response = requests.delete(
            f"{BASE_URL}/api/saved-searches/{fake_id}",
            headers=self.headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_toggle_nonexistent_search(self):
        """PUT /api/saved-searches/{id}/toggle should return 404 for non-existent search"""
        fake_id = str(uuid.uuid4())
        
        response = requests.put(
            f"{BASE_URL}/api/saved-searches/{fake_id}/toggle",
            headers=self.headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestSavedSearchLimits:
    """Tests for saved search limits and validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get session token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        self.session_token = login_response.json().get('session_token')
        self.headers = {
            "Authorization": f"Bearer {self.session_token}",
            "Content-Type": "application/json"
        }
    
    def test_saved_search_requires_name(self):
        """POST /api/saved-searches should require a name"""
        response = requests.post(
            f"{BASE_URL}/api/saved-searches",
            headers=self.headers,
            json={"alert_frequency": "daily"}  # Missing name
        )
        
        # Should fail validation
        assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
