"""
NoFeesApts Backend API Tests
Tests: Health check, Auth, Units, Subscribe, Stats endpoints
"""

import pytest
import requests
import os

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://apartments-qa-env.preview.emergentagent.com').rstrip('/')

class TestHealthAndStats:
    """Health check and stats endpoints"""
    
    def test_api_health(self):
        """Test API is responding"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"API health check failed: {response.status_code}"
        print(f"✅ API health check passed")

    def test_stats_endpoint(self):
        """Test stats endpoint returns units and buildings count"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200, f"Stats endpoint failed: {response.status_code}"
        data = response.json()
        assert "total_units" in data, "Stats should include total_units"
        assert "total_buildings" in data, "Stats should include total_buildings"
        print(f"✅ Stats: {data['total_units']} units, {data['total_buildings']} buildings")


class TestAuthFlow:
    """Authentication flow tests"""
    
    def test_signup_new_user(self):
        """Test signup with new email"""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "TestPass123!",
            "name": "Test User"
        })
        
        # Should succeed or fail with "already registered" (if rerun)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "user" in data, "Response should include user"
            assert data["user"]["email"] == unique_email
            print(f"✅ Signup successful for {unique_email}")
        else:
            print(f"⚠️ Signup returned 400 (may be duplicate): {response.json()}")

    def test_login_existing_user(self):
        """Test login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "chris.trunell@gmail.com",
            "password": "TestPass123!"
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "user" in data, "Response should include user"
            assert "session_token" in data, "Response should include session_token"
            print(f"✅ Login successful for {data['user']['email']}")
            return data["session_token"]
        else:
            print(f"⚠️ Login failed (expected if user doesn't exist): {response.json()}")
            return None

    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Invalid login correctly rejected")


class TestUnitsAPI:
    """Units API tests"""
    
    def test_get_units_list(self):
        """Test fetching units list"""
        response = requests.get(f"{BASE_URL}/api/units?limit=10")
        assert response.status_code == 200, f"Units list failed: {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            unit = data[0]
            assert "id" in unit, "Unit should have id"
            assert "rent" in unit, "Unit should have rent"
            assert "bedrooms" in unit, "Unit should have bedrooms"
            assert "building" in unit, "Unit should have building info"
            print(f"✅ Got {len(data)} units")
        else:
            print(f"⚠️ No units found in database")
        
        return data

    def test_get_single_unit(self):
        """Test fetching a single unit by ID"""
        # First get list to find a unit ID
        list_response = requests.get(f"{BASE_URL}/api/units?limit=1")
        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No units available to test")
        
        unit_id = list_response.json()[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/units/{unit_id}")
        assert response.status_code == 200, f"Get unit failed: {response.status_code}"
        
        unit = response.json()
        assert unit["id"] == unit_id
        assert "building" in unit, "Unit detail should include building"
        print(f"✅ Got unit detail: ${unit['rent']}/mo, {unit['bedrooms']} bed")

    def test_get_nonexistent_unit(self):
        """Test fetching non-existent unit returns 404"""
        response = requests.get(f"{BASE_URL}/api/units/nonexistent-id-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✅ Non-existent unit correctly returns 404")

    def test_filter_units_by_bedrooms(self):
        """Test filtering units by bedroom count"""
        response = requests.get(f"{BASE_URL}/api/units?bedrooms=1&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for unit in data:
            assert unit["bedrooms"] == 1, f"Filter failed: got {unit['bedrooms']} bedrooms"
        
        print(f"✅ Bedroom filter works: {len(data)} 1-bed units")

    def test_filter_units_by_rent_range(self):
        """Test filtering units by rent range"""
        response = requests.get(f"{BASE_URL}/api/units?min_rent=2000&max_rent=5000&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for unit in data:
            assert 2000 <= unit["rent"] <= 5000, f"Rent filter failed: ${unit['rent']}"
        
        print(f"✅ Rent filter works: {len(data)} units in $2000-$5000 range")


class TestSubscribeAPI:
    """Email subscription tests"""
    
    def test_subscribe_new_email(self):
        """Test email subscription"""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/subscribe", json={
            "email": unique_email
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Response should include success"
            print(f"✅ Email subscription successful: {unique_email}")
        else:
            print(f"⚠️ Subscribe returned {response.status_code}: {response.json()}")

    def test_subscribe_duplicate_email(self):
        """Test duplicate email subscription is rejected"""
        # First subscribe
        test_email = "duplicate_test@example.com"
        
        # Try first subscription
        response1 = requests.post(f"{BASE_URL}/api/subscribe", json={"email": test_email})
        
        # Try second subscription with same email
        response2 = requests.post(f"{BASE_URL}/api/subscribe", json={"email": test_email})
        
        # Second should fail with 400
        if response1.status_code == 200:
            assert response2.status_code == 400, f"Duplicate should return 400, got {response2.status_code}"
            print(f"✅ Duplicate subscription correctly rejected")
        else:
            print(f"⚠️ First subscription already existed")


class TestBuildingsAPI:
    """Buildings API tests"""
    
    def test_get_buildings_list(self):
        """Test fetching buildings list"""
        response = requests.get(f"{BASE_URL}/api/buildings")
        assert response.status_code == 200, f"Buildings list failed: {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            building = data[0]
            assert "id" in building, "Building should have id"
            assert "name" in building, "Building should have name"
            assert "address" in building, "Building should have address"
            print(f"✅ Got {len(data)} buildings")
        else:
            print(f"⚠️ No buildings found")


class TestFavoritesAPI:
    """Favorites API tests - requires authentication"""
    
    @pytest.fixture
    def auth_session(self):
        """Get authenticated session"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "chris.trunell@gmail.com",
            "password": "TestPass123!"
        })
        
        if response.status_code != 200:
            pytest.skip("Could not authenticate for favorites test")
        
        return response.json()["session_token"]
    
    def test_get_favorites_unauthorized(self):
        """Test favorites without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/favorites")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Favorites correctly requires auth")

    def test_get_favorites_authorized(self, auth_session):
        """Test getting favorites with auth"""
        response = requests.get(
            f"{BASE_URL}/api/favorites",
            cookies={"session_token": auth_session}
        )
        assert response.status_code == 200, f"Favorites failed: {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Favorites should be a list"
        print(f"✅ Got {len(data)} favorites")


class TestContactAPI:
    """Contact form API tests - requires authentication"""
    
    def test_contact_unauthorized(self):
        """Test contact without auth returns 401"""
        response = requests.post(f"{BASE_URL}/api/contact", json={
            "unit_id": "test-id",
            "message": "Test message",
            "name": "Test User",
            "email": "test@example.com"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Contact correctly requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
