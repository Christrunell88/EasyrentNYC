#!/usr/bin/env python3
"""
Authentication Testing for NoFeesApts.com Live Site
Tests authentication endpoints specifically on https://nofeesapts.com
"""

import requests
import sys
import json

class LiveAuthTester:
    def __init__(self):
        self.base_url = "https://nofeesapts.com"
        self.api_url = f"{self.base_url}/api"
        self.session_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Known user credentials from request
        self.test_email = "chris.trunell@gmail.com"
        
    def log_test(self, name, success, details="", endpoint="", status_code=None):
        """Log test result with detailed information"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        
        if details:
            print(f"   {details}")
        if status_code:
            print(f"   Status: {status_code}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "endpoint": endpoint,
            "status_code": status_code
        })

    def make_request(self, method, endpoint, data=None, headers=None, allow_redirects=True):
        """Make HTTP request with proper error handling"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        
        # Set up headers
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        
        # Add auth token if available
        if self.session_token:
            req_headers['Authorization'] = f'Bearer {self.session_token}'
        
        try:
            print(f"🔗 {method} {url}")
            
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=15, allow_redirects=allow_redirects)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=15, allow_redirects=allow_redirects)
            
            print(f"   Response: {response.status_code}")
            return response
        except Exception as e:
            print(f"   Error: {e}")
            return None

    def test_login_error_handling(self):
        """Test login with invalid credentials"""
        print("\n🔐 Testing Login Error Handling")
        
        data = {
            "email": self.test_email,
            "password": "wrongpassword"
        }
        
        response = self.make_request('POST', 'auth/login', data)
        
        if response and response.status_code == 401:
            self.log_test(
                "Login Error Handling", 
                True, 
                "Correctly returns 401 for invalid credentials",
                "auth/login",
                response.status_code
            )
        else:
            status = response.status_code if response else "No response"
            self.log_test(
                "Login Error Handling", 
                False, 
                f"Expected 401, got {status}",
                "auth/login",
                status
            )

    def test_nonexistent_user_login(self):
        """Test login with non-existent user"""
        print("\n🔐 Testing Non-existent User Login")
        
        data = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
        
        response = self.make_request('POST', 'auth/login', data)
        
        if response and response.status_code == 401:
            self.log_test(
                "Non-existent User Login", 
                True, 
                "Correctly returns 401 for non-existent user",
                "auth/login",
                response.status_code
            )
        else:
            status = response.status_code if response else "No response"
            self.log_test(
                "Non-existent User Login", 
                False, 
                f"Expected 401, got {status}",
                "auth/login",
                status
            )

    def test_google_oauth(self):
        """Test Google OAuth endpoint"""
        print("\n🔐 Testing Google OAuth Endpoint")
        
        response = self.make_request('GET', 'auth/google', allow_redirects=False)
        
        if response:
            if response.status_code == 404:
                self.log_test(
                    "Google OAuth Endpoint", 
                    False, 
                    "Google OAuth endpoint not implemented (404)",
                    "auth/google",
                    response.status_code
                )
            elif response.status_code in [302, 301, 307, 308]:
                location = response.headers.get('Location', '')
                if 'google' in location.lower():
                    self.log_test(
                        "Google OAuth Endpoint", 
                        True, 
                        f"Redirects to Google: {location}",
                        "auth/google",
                        response.status_code
                    )
                else:
                    self.log_test(
                        "Google OAuth Endpoint", 
                        False, 
                        f"Redirects but not to Google: {location}",
                        "auth/google",
                        response.status_code
                    )
            else:
                self.log_test(
                    "Google OAuth Endpoint", 
                    False, 
                    f"Unexpected response: {response.status_code}",
                    "auth/google",
                    response.status_code
                )
        else:
            self.log_test(
                "Google OAuth Endpoint", 
                False, 
                "No response received",
                "auth/google"
            )

    def test_password_reset(self):
        """Test password reset functionality"""
        print("\n🔐 Testing Password Reset")
        
        data = {"email": self.test_email}
        
        response = self.make_request('POST', 'auth/forgot-password', data)
        
        if response and response.status_code == 200:
            try:
                result = response.json()
                if 'message' in result:
                    self.log_test(
                        "Password Reset", 
                        True, 
                        "Password reset endpoint working",
                        "auth/forgot-password",
                        response.status_code
                    )
                else:
                    self.log_test(
                        "Password Reset", 
                        False, 
                        "Response missing message field",
                        "auth/forgot-password",
                        response.status_code
                    )
            except:
                self.log_test(
                    "Password Reset", 
                    False, 
                    "Invalid JSON response",
                    "auth/forgot-password",
                    response.status_code
                )
        else:
            status = response.status_code if response else "No response"
            self.log_test(
                "Password Reset", 
                False, 
                f"Expected 200, got {status}",
                "auth/forgot-password",
                status
            )

    def test_session_management(self):
        """Test session management endpoints"""
        print("\n🔐 Testing Session Management")
        
        # Test /auth/me without authentication
        response = self.make_request('GET', 'auth/me')
        
        if response and response.status_code == 401:
            self.log_test(
                "Get User Info (Unauthenticated)", 
                True, 
                "Correctly requires authentication",
                "auth/me",
                response.status_code
            )
        else:
            status = response.status_code if response else "No response"
            self.log_test(
                "Get User Info (Unauthenticated)", 
                False, 
                f"Expected 401, got {status}",
                "auth/me",
                status
            )

    def test_logout(self):
        """Test logout functionality"""
        print("\n🔐 Testing Logout")
        
        response = self.make_request('POST', 'auth/logout')
        
        if response and response.status_code == 200:
            try:
                result = response.json()
                if 'message' in result:
                    self.log_test(
                        "Logout", 
                        True, 
                        "Logout endpoint working",
                        "auth/logout",
                        response.status_code
                    )
                else:
                    self.log_test(
                        "Logout", 
                        False, 
                        "Response missing message field",
                        "auth/logout",
                        response.status_code
                    )
            except:
                self.log_test(
                    "Logout", 
                    False, 
                    "Invalid JSON response",
                    "auth/logout",
                    response.status_code
                )
        else:
            status = response.status_code if response else "No response"
            self.log_test(
                "Logout", 
                False, 
                f"Expected 200, got {status}",
                "auth/logout",
                status
            )

    def test_cors_headers(self):
        """Test CORS configuration"""
        print("\n🔐 Testing CORS Headers")
        
        response = self.make_request('GET', 'auth/me')
        
        if response:
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_credentials = response.headers.get('Access-Control-Allow-Credentials')
            
            if cors_origin:
                self.log_test(
                    "CORS Headers", 
                    True, 
                    f"CORS configured: Origin={cors_origin}, Credentials={cors_credentials}",
                    "auth/me",
                    response.status_code
                )
            else:
                self.log_test(
                    "CORS Headers", 
                    False, 
                    "No CORS headers found - may cause frontend issues",
                    "auth/me",
                    response.status_code
                )
        else:
            self.log_test(
                "CORS Headers", 
                False, 
                "No response to check CORS headers",
                "auth/me"
            )

    def run_tests(self):
        """Run all authentication tests"""
        print("🚀 NoFeesApts.com Live Authentication Tests")
        print(f"🔗 Testing: {self.base_url}")
        print("=" * 60)
        
        # Run all tests
        self.test_login_error_handling()
        self.test_nonexistent_user_login()
        self.test_google_oauth()
        self.test_password_reset()
        self.test_session_management()
        self.test_logout()
        self.test_cors_headers()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} passed")
        
        # Show failures
        failures = [r for r in self.test_results if not r['success']]
        if failures:
            print("\n❌ Failed Tests:")
            for f in failures:
                print(f"  - {f['name']}: {f['details']}")
        
        # Critical issues
        critical = []
        for f in failures:
            if f['status_code'] == 404:
                critical.append(f"Missing endpoint: {f['endpoint']}")
            elif f['status_code'] and f['status_code'] >= 500:
                critical.append(f"Server error: {f['endpoint']}")
            elif 'cors' in f['name'].lower():
                critical.append("CORS configuration issues")
        
        if critical:
            print("\n🚨 Critical Issues:")
            for issue in critical:
                print(f"  - {issue}")
        
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    tester = LiveAuthTester()
    return tester.run_tests()

if __name__ == "__main__":
    sys.exit(main())