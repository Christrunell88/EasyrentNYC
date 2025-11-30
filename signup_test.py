#!/usr/bin/env python3
"""
Signup Functionality Testing for NoFeesApts.com Production Site
Tests the signup endpoint thoroughly as requested in the review
"""

import requests
import sys
import json
from datetime import datetime
import time

class SignupTester:
    def __init__(self):
        self.base_url = "https://nofeesapts.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        timestamp = datetime.now().strftime('%H%M%S')
        self.test_email = f"testuser{timestamp}@example.com"
        self.test_name = "Test User"
        self.test_password = "TestPass123!"
        
        print(f"🔗 Testing signup on: {self.base_url}")
        print(f"📧 Test email: {self.test_email}")
        print("=" * 60)

    def log_test(self, name, success, details="", status_code=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if status_code:
                print(f"   Status Code: {status_code}")
            if details:
                print(f"   Details: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "status_code": status_code
        })

    def make_signup_request(self, email, password, name):
        """Make signup request and return response"""
        url = f"{self.api_url}/auth/signup"
        data = {
            "email": email,
            "password": password,
            "name": name
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            print(f"🔄 Making POST request to: {url}")
            print(f"📤 Request data: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, headers=headers, timeout=15)
            
            print(f"📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📥 Response Body: {json.dumps(response_json, indent=2)}")
            except:
                print(f"📥 Response Body (text): {response.text}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

    def test_valid_signup(self):
        """Test 1: Valid Signup Test"""
        print("\n🧪 Test 1: Valid Signup")
        print(f"Email: {self.test_email}")
        print(f"Password: {self.test_password}")
        print(f"Name: {self.test_name}")
        
        response = self.make_signup_request(self.test_email, self.test_password, self.test_name)
        
        if response is None:
            self.log_test("Valid Signup Test", False, "No response received")
            return False
        
        if response.status_code == 200:  # Backend returns 200, not 201
            try:
                result = response.json()
                if 'user' in result and result['user'].get('email') == self.test_email:
                    self.log_test("Valid Signup Test", True, 
                                f"User created successfully with ID: {result['user'].get('id')}", 
                                response.status_code)
                    return True
                else:
                    self.log_test("Valid Signup Test", False, 
                                "Response missing user data", response.status_code)
            except:
                self.log_test("Valid Signup Test", False, 
                            "Invalid JSON response", response.status_code)
        else:
            try:
                error_msg = response.json().get('detail', response.text)
            except:
                error_msg = response.text
            self.log_test("Valid Signup Test", False, error_msg, response.status_code)
        
        return False

    def test_duplicate_email(self):
        """Test 2: Duplicate Email Test"""
        print("\n🧪 Test 2: Duplicate Email")
        print(f"Attempting to signup again with same email: {self.test_email}")
        
        response = self.make_signup_request(self.test_email, self.test_password, self.test_name)
        
        if response is None:
            self.log_test("Duplicate Email Test", False, "No response received")
            return False
        
        if response.status_code == 400:
            try:
                result = response.json()
                if 'already' in result.get('detail', '').lower():
                    self.log_test("Duplicate Email Test", True, 
                                f"Correctly rejected duplicate email: {result.get('detail')}", 
                                response.status_code)
                    return True
                else:
                    self.log_test("Duplicate Email Test", False, 
                                f"Wrong error message: {result.get('detail')}", response.status_code)
            except:
                self.log_test("Duplicate Email Test", False, 
                            "Invalid JSON response", response.status_code)
        else:
            self.log_test("Duplicate Email Test", False, 
                        "Expected 400 error for duplicate email", response.status_code)
        
        return False

    def test_invalid_email(self):
        """Test 3: Invalid Email Test"""
        print("\n🧪 Test 3: Invalid Email")
        invalid_email = "invalid-email"
        print(f"Testing invalid email: {invalid_email}")
        
        response = self.make_signup_request(invalid_email, self.test_password, self.test_name)
        
        if response is None:
            self.log_test("Invalid Email Test", False, "No response received")
            return False
        
        if response.status_code == 422:
            self.log_test("Invalid Email Test", True, 
                        "Correctly rejected invalid email format", response.status_code)
            return True
        elif response.status_code == 400:
            # Some APIs return 400 for validation errors
            try:
                result = response.json()
                if 'email' in result.get('detail', '').lower() or 'valid' in result.get('detail', '').lower():
                    self.log_test("Invalid Email Test", True, 
                                f"Correctly rejected invalid email: {result.get('detail')}", 
                                response.status_code)
                    return True
            except:
                pass
            self.log_test("Invalid Email Test", False, 
                        "Wrong error for invalid email", response.status_code)
        else:
            self.log_test("Invalid Email Test", False, 
                        "Expected 422 validation error for invalid email", response.status_code)
        
        return False

    def test_weak_password(self):
        """Test 4: Weak Password Test"""
        print("\n🧪 Test 4: Weak Password")
        weak_password = "123"
        print(f"Testing weak password: {weak_password}")
        
        response = self.make_signup_request(f"test{int(time.time())}@example.com", weak_password, self.test_name)
        
        if response is None:
            self.log_test("Weak Password Test", False, "No response received")
            return False
        
        if response.status_code in [400, 422]:
            try:
                result = response.json()
                error_detail = result.get('detail', '').lower()
                if 'password' in error_detail:
                    self.log_test("Weak Password Test", True, 
                                f"Correctly rejected weak password: {result.get('detail')}", 
                                response.status_code)
                    return True
                else:
                    self.log_test("Weak Password Test", False, 
                                f"Wrong error message: {result.get('detail')}", response.status_code)
            except:
                self.log_test("Weak Password Test", False, 
                            "Invalid JSON response", response.status_code)
        else:
            self.log_test("Weak Password Test", False, 
                        "Expected 400/422 error for weak password", response.status_code)
        
        return False

    def test_missing_fields(self):
        """Test 5: Missing Fields Test"""
        print("\n🧪 Test 5: Missing Fields")
        
        # Test missing name
        print("Testing missing name field...")
        url = f"{self.api_url}/auth/signup"
        data = {
            "email": f"test{int(time.time())}@example.com",
            "password": self.test_password
            # name field missing
        }
        
        try:
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=15)
            
            if response.status_code == 422:
                self.log_test("Missing Name Field Test", True, 
                            "Correctly rejected missing name field", response.status_code)
            else:
                self.log_test("Missing Name Field Test", False, 
                            "Expected 422 validation error for missing name", response.status_code)
        except Exception as e:
            self.log_test("Missing Name Field Test", False, f"Request error: {e}")
        
        # Test missing password
        print("Testing missing password field...")
        data = {
            "email": f"test{int(time.time())+1}@example.com",
            "name": self.test_name
            # password field missing
        }
        
        try:
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=15)
            
            if response.status_code == 422:
                self.log_test("Missing Password Field Test", True, 
                            "Correctly rejected missing password field", response.status_code)
                return True
            else:
                self.log_test("Missing Password Field Test", False, 
                            "Expected 422 validation error for missing password", response.status_code)
        except Exception as e:
            self.log_test("Missing Password Field Test", False, f"Request error: {e}")
        
        return False

    def test_google_oauth_availability(self):
        """Test 6: Google OAuth Signup Availability"""
        print("\n🧪 Test 6: Google OAuth Availability")
        
        # Check if Google OAuth endpoint exists
        url = f"{self.api_url}/auth/google"
        
        try:
            response = requests.get(url, timeout=15)
            print(f"📥 Google OAuth endpoint status: {response.status_code}")
            
            if response.status_code == 404:
                self.log_test("Google OAuth Availability", False, 
                            "Google OAuth endpoint not implemented (404)", response.status_code)
            elif response.status_code in [200, 302, 401]:
                self.log_test("Google OAuth Availability", True, 
                            "Google OAuth endpoint exists", response.status_code)
                return True
            else:
                self.log_test("Google OAuth Availability", False, 
                            f"Unexpected response from Google OAuth endpoint", response.status_code)
        except Exception as e:
            self.log_test("Google OAuth Availability", False, f"Request error: {e}")
        
        return False

    def verify_database_state(self):
        """Test 7: Verify Database State (if possible)"""
        print("\n🧪 Test 7: Database Verification")
        
        # Try to login with the created user to verify it exists
        url = f"{self.api_url}/auth/login"
        data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        try:
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'session_token' in result or 'user' in result:
                    self.log_test("Database Verification (Login)", True, 
                                "User exists in database and can login", response.status_code)
                    return True
                else:
                    self.log_test("Database Verification (Login)", False, 
                                "Login response missing expected data", response.status_code)
            else:
                self.log_test("Database Verification (Login)", False, 
                            "Cannot login with created user", response.status_code)
        except Exception as e:
            self.log_test("Database Verification (Login)", False, f"Request error: {e}")
        
        return False

    def run_all_tests(self):
        """Run all signup tests"""
        print("🚀 Starting NoFeesApts.com Signup Testing")
        print("=" * 60)
        
        # Run all tests in sequence
        self.test_valid_signup()
        self.test_duplicate_email()
        self.test_invalid_email()
        self.test_weak_password()
        self.test_missing_fields()
        self.test_google_oauth_availability()
        self.verify_database_state()
        
        # Results Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All signup tests passed!")
            return 0
        else:
            print("❌ Some signup tests failed!")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']}: {result['details']}")
            return 1

def main():
    tester = SignupTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())