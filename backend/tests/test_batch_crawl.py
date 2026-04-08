"""
Test suite for Batch Crawl and Image Upload features
Tests:
- POST /api/admin/batch-crawl/start - Start batch crawl
- GET /api/admin/batch-crawl/status/{job_id} - Get batch crawl status
- POST /api/admin/batch-crawl/cancel/{job_id} - Cancel batch crawl
- POST /api/admin/batch-crawl/start - 409 if already running
- POST /api/admin/staging/units/{unit_id}/upload-images - Image upload
"""
import pytest
import requests
import os
import time
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "placesfirm@gmail.com"
ADMIN_PASSWORD = "Checkers080/?"


class TestBatchCrawlFeature:
    """Tests for the Batch Crawl All feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as admin and get session token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.status_code} - {login_response.text}")
        
        login_data = login_response.json()
        self.session_token = login_data.get("session_token")
        
        if not self.session_token:
            pytest.skip("No session_token in login response")
        
        # Set session token as cookie
        self.session.cookies.set("session_token", self.session_token)
        
        yield
        
        # Cleanup: Try to cancel any running batch crawl
        if hasattr(self, 'job_id') and self.job_id:
            try:
                self.session.post(f"{BASE_URL}/api/admin/batch-crawl/cancel/{self.job_id}")
            except:
                pass
    
    def test_start_batch_crawl_returns_job_id(self):
        """Test POST /api/admin/batch-crawl/start returns job_id"""
        response = self.session.post(f"{BASE_URL}/api/admin/batch-crawl/start")
        
        # Should return 200 or 409 (if already running)
        assert response.status_code in [200, 409], f"Unexpected status: {response.status_code} - {response.text}"
        
        data = response.json()
        
        if response.status_code == 200:
            # Verify response structure
            assert "job_id" in data, "Response should contain job_id"
            assert "total_companies" in data, "Response should contain total_companies"
            assert "message" in data, "Response should contain message"
            
            # Verify job_id format
            assert data["job_id"].startswith("batch-"), f"job_id should start with 'batch-': {data['job_id']}"
            
            # Verify total_companies is 29
            assert data["total_companies"] == 29, f"Expected 29 companies, got {data['total_companies']}"
            
            self.job_id = data["job_id"]
            print(f"✓ Batch crawl started with job_id: {self.job_id}")
        else:
            # 409 means another batch is running
            assert "detail" in data, "409 response should have detail"
            print(f"✓ Batch crawl returned 409 (already running): {data['detail']}")
    
    def test_get_batch_crawl_status(self):
        """Test GET /api/admin/batch-crawl/status/{job_id} returns progress"""
        # First start a batch crawl
        start_response = self.session.post(f"{BASE_URL}/api/admin/batch-crawl/start")
        
        if start_response.status_code == 409:
            # Another batch is running, try to get its status from the error message
            detail = start_response.json().get("detail", "")
            # Extract job_id from message like "Batch crawl already in progress (job: batch-xxxxxxxx)"
            if "job:" in detail:
                job_id = detail.split("job:")[1].strip().rstrip(")")
            else:
                pytest.skip("Cannot determine running job_id from 409 response")
        else:
            assert start_response.status_code == 200, f"Failed to start batch: {start_response.text}"
            job_id = start_response.json()["job_id"]
        
        self.job_id = job_id
        
        # Wait a moment for the job to start
        time.sleep(2)
        
        # Get status
        status_response = self.session.get(f"{BASE_URL}/api/admin/batch-crawl/status/{job_id}")
        
        assert status_response.status_code == 200, f"Status check failed: {status_response.status_code} - {status_response.text}"
        
        data = status_response.json()
        
        # Verify response structure
        assert "job_id" in data, "Status should contain job_id"
        assert "status" in data, "Status should contain status"
        assert "total" in data, "Status should contain total"
        assert "completed" in data, "Status should contain completed"
        assert "results" in data, "Status should contain results array"
        
        # Verify status values
        assert data["status"] in ["queued", "running", "completed", "cancelled"], f"Invalid status: {data['status']}"
        assert data["total"] == 29, f"Expected total=29, got {data['total']}"
        assert isinstance(data["results"], list), "results should be a list"
        
        print(f"✓ Batch crawl status: {data['status']}, completed: {data['completed']}/{data['total']}")
    
    def test_cancel_batch_crawl(self):
        """Test POST /api/admin/batch-crawl/cancel/{job_id} cancels running job"""
        # First start a batch crawl
        start_response = self.session.post(f"{BASE_URL}/api/admin/batch-crawl/start")
        
        if start_response.status_code == 409:
            detail = start_response.json().get("detail", "")
            if "job:" in detail:
                job_id = detail.split("job:")[1].strip().rstrip(")")
            else:
                pytest.skip("Cannot determine running job_id from 409 response")
        else:
            assert start_response.status_code == 200, f"Failed to start batch: {start_response.text}"
            job_id = start_response.json()["job_id"]
        
        self.job_id = job_id
        
        # Wait for job to start running
        time.sleep(2)
        
        # Cancel the job
        cancel_response = self.session.post(f"{BASE_URL}/api/admin/batch-crawl/cancel/{job_id}")
        
        # Should return 200 or 400 (if not running)
        assert cancel_response.status_code in [200, 400], f"Cancel failed: {cancel_response.status_code} - {cancel_response.text}"
        
        data = cancel_response.json()
        
        if cancel_response.status_code == 200:
            assert "message" in data, "Cancel response should have message"
            assert "job_id" in data, "Cancel response should have job_id"
            print(f"✓ Batch crawl cancelled: {data['message']}")
        else:
            # Job might have already completed
            print(f"✓ Cancel returned 400 (job not running): {data.get('detail', data)}")
    
    def test_batch_crawl_409_when_already_running(self):
        """Test POST /api/admin/batch-crawl/start returns 409 if already running"""
        # Start first batch crawl
        first_response = self.session.post(f"{BASE_URL}/api/admin/batch-crawl/start")
        
        if first_response.status_code == 200:
            self.job_id = first_response.json()["job_id"]
            
            # Wait a moment
            time.sleep(1)
            
            # Try to start another batch crawl
            second_response = self.session.post(f"{BASE_URL}/api/admin/batch-crawl/start")
            
            assert second_response.status_code == 409, f"Expected 409, got {second_response.status_code}"
            
            data = second_response.json()
            assert "detail" in data, "409 response should have detail"
            assert "already in progress" in data["detail"].lower(), f"Unexpected detail: {data['detail']}"
            
            print(f"✓ Second batch crawl correctly returned 409: {data['detail']}")
        else:
            # First request already got 409, which means a batch is already running
            assert first_response.status_code == 409, f"Unexpected status: {first_response.status_code}"
            print("✓ Batch crawl already running, 409 returned correctly")
    
    def test_batch_crawl_status_404_for_invalid_job(self):
        """Test GET /api/admin/batch-crawl/status/{job_id} returns 404 for invalid job"""
        response = self.session.get(f"{BASE_URL}/api/admin/batch-crawl/status/invalid-job-id-12345")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "404 response should have detail"
        
        print(f"✓ Invalid job_id correctly returned 404: {data['detail']}")


class TestImageUploadFeature:
    """Tests for the Image Upload feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as admin and get session token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.status_code} - {login_response.text}")
        
        login_data = login_response.json()
        self.session_token = login_data.get("session_token")
        
        if not self.session_token:
            pytest.skip("No session_token in login response")
        
        # Set session token as cookie
        self.session.cookies.set("session_token", self.session_token)
    
    def test_image_upload_to_staging_unit(self):
        """Test POST /api/admin/staging/units/{unit_id}/upload-images"""
        # First, get a staging unit to upload images to
        units_response = self.session.get(f"{BASE_URL}/api/admin/staging/units?limit=1")
        
        if units_response.status_code != 200:
            pytest.skip(f"Failed to get staging units: {units_response.text}")
        
        units_data = units_response.json()
        items = units_data.get("items", [])
        
        if not items:
            pytest.skip("No staging units available for image upload test")
        
        unit_id = items[0]["id"]
        
        # Create a test image (1x1 pixel PNG)
        # PNG header for a 1x1 red pixel
        test_image_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        # Upload the image - use list format for multiple files parameter
        files = [
            ('files', ('test_image.png', io.BytesIO(test_image_data), 'image/png'))
        ]
        
        # Create a new session without Content-Type header for multipart upload
        upload_session = requests.Session()
        upload_session.cookies.set("session_token", self.session_token)
        
        upload_response = upload_session.post(
            f"{BASE_URL}/api/admin/staging/units/{unit_id}/upload-images",
            files=files
        )
        
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.status_code} - {upload_response.text}"
        
        data = upload_response.json()
        
        # Verify response structure
        assert "message" in data, "Response should contain message"
        assert "uploaded_urls" in data, "Response should contain uploaded_urls"
        assert "total_images" in data, "Response should contain total_images"
        
        # Verify uploaded URL format
        assert len(data["uploaded_urls"]) > 0, "Should have at least one uploaded URL"
        uploaded_url = data["uploaded_urls"][0]
        assert uploaded_url.startswith("/api/uploads/"), f"URL should start with /api/uploads/: {uploaded_url}"
        assert unit_id in uploaded_url, f"URL should contain unit_id: {uploaded_url}"
        
        print(f"✓ Image uploaded successfully: {uploaded_url}")
        
        # Verify the image is accessible
        full_url = f"{BASE_URL}{uploaded_url}"
        image_response = self.session.get(full_url)
        
        assert image_response.status_code == 200, f"Image not accessible: {image_response.status_code}"
        assert image_response.headers.get("content-type", "").startswith("image/"), "Response should be an image"
        
        print(f"✓ Uploaded image is accessible at: {full_url}")
    
    def test_image_upload_404_for_invalid_unit(self):
        """Test POST /api/admin/staging/units/{unit_id}/upload-images returns 404 for invalid unit"""
        test_image_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = [
            ('files', ('test_image.png', io.BytesIO(test_image_data), 'image/png'))
        ]
        
        # Create a new session without Content-Type header for multipart upload
        upload_session = requests.Session()
        upload_session.cookies.set("session_token", self.session_token)
        
        response = upload_session.post(
            f"{BASE_URL}/api/admin/staging/units/invalid-unit-id-12345/upload-images",
            files=files
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "404 response should have detail"
        
        print(f"✓ Invalid unit_id correctly returned 404: {data['detail']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
