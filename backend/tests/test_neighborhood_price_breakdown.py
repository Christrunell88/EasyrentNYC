"""
Test suite for Neighborhood Price Breakdown feature
Tests the /api/neighborhoods/{slug} endpoint for price_breakdown data
including studio, one_bed, two_bed with doorman/elevator comparisons
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNeighborhoodPriceBreakdown:
    """Tests for neighborhood price breakdown feature"""
    
    def test_chelsea_returns_price_breakdown(self):
        """Chelsea neighborhood should return price_breakdown object"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        assert "price_breakdown" in data
        assert "studio" in data["price_breakdown"]
        assert "one_bed" in data["price_breakdown"]
        assert "two_bed" in data["price_breakdown"]
    
    def test_chelsea_price_breakdown_structure(self):
        """Chelsea price_breakdown should have correct structure for each bedroom type"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        pb = data["price_breakdown"]
        
        for br_type in ["studio", "one_bed", "two_bed"]:
            br_data = pb[br_type]
            # Check main fields
            assert "count" in br_data
            assert "avg_rent" in br_data
            assert "min_rent" in br_data
            assert "max_rent" in br_data
            # Check doorman fields
            assert "doorman" in br_data
            assert "no_doorman" in br_data
            assert "count" in br_data["doorman"]
            assert "avg_rent" in br_data["doorman"]
            assert "count" in br_data["no_doorman"]
            assert "avg_rent" in br_data["no_doorman"]
            # Check elevator fields
            assert "elevator" in br_data
            assert "no_elevator" in br_data
            assert "count" in br_data["elevator"]
            assert "avg_rent" in br_data["elevator"]
            assert "count" in br_data["no_elevator"]
            assert "avg_rent" in br_data["no_elevator"]
    
    def test_chelsea_has_doorman_data(self):
        """Chelsea should have doorman data (total_doorman > 0)"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        assert data["stats"]["total_doorman"] > 0
        assert data["stats"]["total_elevator"] > 0
    
    def test_chelsea_studio_avg_rent_valid(self):
        """Chelsea studio avg_rent should be a valid positive number"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        studio = data["price_breakdown"]["studio"]
        
        if studio["count"] > 0:
            assert studio["avg_rent"] > 0
            assert studio["min_rent"] > 0
            assert studio["max_rent"] >= studio["min_rent"]
    
    def test_long_island_city_returns_price_breakdown(self):
        """Long Island City should return price_breakdown object"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/long-island-city")
        assert response.status_code == 200
        
        data = response.json()
        assert "price_breakdown" in data
        assert data["name"] == "Long Island City"
    
    def test_long_island_city_elevator_data(self):
        """Long Island City should have elevator data"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/long-island-city")
        assert response.status_code == 200
        
        data = response.json()
        assert data["stats"]["total_elevator"] > 0
        
        # Check one_bed has elevator data
        one_bed = data["price_breakdown"]["one_bed"]
        if one_bed["elevator"]["count"] > 0:
            assert one_bed["elevator"]["avg_rent"] > 0
    
    def test_greenpoint_no_doorman_data(self):
        """Greenpoint should have no doorman data (edge case)"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/greenpoint")
        assert response.status_code == 200
        
        data = response.json()
        assert data["stats"]["total_doorman"] == 0
        assert data["stats"]["total_elevator"] == 0
        
        # All units should be in no_doorman category
        studio = data["price_breakdown"]["studio"]
        if studio["count"] > 0:
            assert studio["doorman"]["count"] == 0
            assert studio["no_doorman"]["count"] == studio["count"]
    
    def test_greenpoint_no_two_bed_data(self):
        """Greenpoint should handle no two_bed listings gracefully"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/greenpoint")
        assert response.status_code == 200
        
        data = response.json()
        two_bed = data["price_breakdown"]["two_bed"]
        
        assert two_bed["count"] == 0
        assert two_bed["avg_rent"] == 0
        assert two_bed["min_rent"] == 0
        assert two_bed["max_rent"] == 0
    
    def test_invalid_neighborhood_returns_404(self):
        """Invalid neighborhood slug should return 404"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/invalid-neighborhood-xyz")
        assert response.status_code == 404
    
    def test_financial_district_returns_data(self):
        """Financial District should return valid price_breakdown"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/financial-district")
        assert response.status_code == 200
        
        data = response.json()
        assert "price_breakdown" in data
        assert data["name"] == "Financial District"
    
    def test_tribeca_returns_data(self):
        """Tribeca should return valid price_breakdown"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/tribeca")
        assert response.status_code == 200
        
        data = response.json()
        assert "price_breakdown" in data
        assert data["name"] == "Tribeca"
    
    def test_midtown_west_returns_data(self):
        """Midtown West should return valid price_breakdown"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/midtown-west")
        assert response.status_code == 200
        
        data = response.json()
        assert "price_breakdown" in data
        assert data["name"] == "Midtown West"
    
    def test_price_breakdown_counts_match_stats(self):
        """Price breakdown counts should match stats totals"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        pb = data["price_breakdown"]
        stats = data["stats"]
        
        # Studio count should match
        assert pb["studio"]["count"] == stats["studios"]
        # One bed count should match
        assert pb["one_bed"]["count"] == stats["one_beds"]
        # Two bed count should be <= two_plus_beds (since two_bed is only 2BR, not 3+)
        assert pb["two_bed"]["count"] <= stats["two_plus_beds"]
    
    def test_doorman_no_doorman_counts_sum_to_total(self):
        """Doorman + no_doorman counts should sum to total count"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        pb = data["price_breakdown"]
        
        for br_type in ["studio", "one_bed", "two_bed"]:
            br_data = pb[br_type]
            total = br_data["count"]
            doorman_count = br_data["doorman"]["count"]
            no_doorman_count = br_data["no_doorman"]["count"]
            assert doorman_count + no_doorman_count == total, f"{br_type}: {doorman_count} + {no_doorman_count} != {total}"
    
    def test_elevator_no_elevator_counts_sum_to_total(self):
        """Elevator + no_elevator counts should sum to total count"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        pb = data["price_breakdown"]
        
        for br_type in ["studio", "one_bed", "two_bed"]:
            br_data = pb[br_type]
            total = br_data["count"]
            elevator_count = br_data["elevator"]["count"]
            no_elevator_count = br_data["no_elevator"]["count"]
            assert elevator_count + no_elevator_count == total, f"{br_type}: {elevator_count} + {no_elevator_count} != {total}"


class TestNeighborhoodStats:
    """Tests for neighborhood stats including total_doorman and total_elevator"""
    
    def test_stats_include_total_doorman(self):
        """Stats should include total_doorman field"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_doorman" in data["stats"]
        assert isinstance(data["stats"]["total_doorman"], int)
    
    def test_stats_include_total_elevator(self):
        """Stats should include total_elevator field"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_elevator" in data["stats"]
        assert isinstance(data["stats"]["total_elevator"], int)
    
    def test_stats_basic_fields(self):
        """Stats should include all basic fields"""
        response = requests.get(f"{BASE_URL}/api/neighborhoods/chelsea")
        assert response.status_code == 200
        
        data = response.json()
        stats = data["stats"]
        
        required_fields = [
            "total_units", "total_buildings", "avg_rent", 
            "min_rent", "max_rent", "studios", "one_beds", 
            "two_plus_beds", "total_doorman", "total_elevator"
        ]
        
        for field in required_fields:
            assert field in stats, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
