#!/usr/bin/env python3
"""
Authentication Testing for NoFeesApts.com Live Site
Tests authentication endpoints specifically on https://nofeesapts.com
"""

import requests
import sys
import json
from datetime import datetime

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
        # We'll test without password first to see error handling
        
    def log_test(self, name, success, details="", endpoint="", status_code=None):
        """Log test result with detailed information"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   Error: {details}")
            if status_code:
                print(f"   Status Code: {status_code}")
        
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
            print(f"🔗 Testing {method} {url}")
            
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=15, allow_redirects=allow_redirects)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=15, allow_redirects=allow_redirects)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=15, allow_redirects=allow_redirects)
            elif method == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=15, allow_redirects=allow_redirects)
            
            print(f"   Response: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_data = response.json()
                    print(f"   Data: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Raw response: {response.text[:200]}...")
            else:
                print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
                if len(response.text) < 500:
                    print(f"   Response: {response.text}")
                else:
                    print(f"   Response length: {len(response.text)} chars")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"   Request error: {e}")
            return None
        except Exception as e:
            print(f"   Unexpected error: {e}")
            return None

    def test_login_with_valid_user(self):
        """Test login with known valid user email (without password to test error handling)"""
        print("\n🔐 Testing Login with Valid User Email (No Password)")
        
        data = {
            "email": self.test_email,
            "password": ""  # Empty password to test error handling
        }
        
        response = self.make_request('POST', 'auth/login', data)
        
        if response:
            if response.status_code == 401:
                self.log_test(
                    "Login Error Handling", 
                    True, 
                    "Correctly returns 401 for invalid credentials",
                    "auth/login",
                    response.status_code
                )
            else:
                self.log_test(
                    "Login Error Handling", 
                    False, 
                    f"Expected 401 but got {response.status_code}",
                    "auth/login",
                    response.status_code
                )
        else:
            self.log_test(
                "Login Error Handling", 
                False, 
                "No response received",
                "auth/login"
            )

    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        print("\n🔐 Testing Login with Non-existent User")
        
        data = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
        
        response = self.make_request('POST', 'auth/login', data)
        
        if response:
            if response.status_code == 401:
                self.log_test(
                    "Non-existent User Login", 
                    True, 
                    "Correctly returns 401 for non-existent user",
                    "auth/login",
                    response.status_code
                )
            else:
                self.log_test(
                    "Non-existent User Login", 
                    False, 
                    f"Expected 401 but got {response.status_code}",
                    "auth/login",
                    response.status_code
                )
        else:
            self.log_test(
                "Non-existent User Login", 
                False, 
                "No response received",
                "auth/login"
            )

    def test_google_oauth_redirect(self):
        """Test Google OAuth redirect endpoint"""
        print("\n🔐 Testing Google OAuth Redirect")
        
        response = self.make_request('GET', 'auth/google', allow_redirects=False)
        
        if response:
            if response.status_code == 404:
                self.log_test(
                    "Google OAuth Endpoint", 
                    False, 
                    "Google OAuth endpoint not found - needs to be implemented",
                    "auth/google",
                    response.status_code
                )
            elif response.status_code in [302, 301, 307, 308]:
                # Check if it's redirecting to Google
                location = response.headers.get('Location', '')
                if 'google' in location.lower() or 'oauth' in location.lower():
                    self.log_test(
                        "Google OAuth Redirect", 
                        True, 
                        f"Correctly redirects to: {location}",
                        "auth/google",
                        response.status_code
                    )
                else:
                    self.log_test(
                        "Google OAuth Redirect", 
                        False, 
                        f"Redirects but not to Google: {location}",
                        "auth/google",
                        response.status_code
                    )
            else:
                self.log_test(
                    "Google OAuth Redirect", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    "auth/google",
                    response.status_code
                )
        else:
            self.log_test(
                "Google OAuth Redirect", 
                False, 
                "No response received",
                "auth/google"
            )

    def test_forgot_password(self):
        """Test password reset functionality"""
        print("\n🔐 Testing Password Reset")
        
        data = {
            "email": self.test_email
        }
        
        response = self.make_request('POST', 'auth/forgot-password', data)
        
        if response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'message' in result:
                        self.log_test(
                            "Password Reset Request", 
                            True, 
                            f"Success: {result['message']}",
                            "auth/forgot-password",
                            response.status_code
                        )
                    else:
                        self.log_test(
                            "Password Reset Request", 
                            False, 
                            "Response missing message field",
                            "auth/forgot-password",
                            response.status_code
                        )
                except:
                    self.log_test(
                        "Password Reset Request", 
                        False, 
                        "Invalid JSON response",
                        "auth/forgot-password",
                        response.status_code
                    )
            else:
                self.log_test(
                    "Password Reset Request", 
                    False, 
                    f"Expected 200 but got {response.status_code}",
                    "auth/forgot-password",
                    response.status_code
                )
        else:
            self.log_test(
                "Password Reset Request", 
                False, 
                "No response received",
                "auth/forgot-password"
            )

    def test_session_management_unauthenticated(self):
        """Test session management without authentication"""
        print("\n🔐 Testing Session Management (Unauthenticated)")
        
        # Test /auth/me without authentication
        response = self.make_request('GET', 'auth/me')
        
        if response:
            if response.status_code == 401:
                self.log_test(
                    "Get User Info (Unauthenticated)", 
                    True, 
                    "Correctly returns 401 for unauthenticated request",
                    "auth/me",
                    response.status_code
                )
            else:
                self.log_test(
                    "Get User Info (Unauthenticated)", 
                    False, 
                    f"Expected 401 but got {response.status_code}",
                    "auth/me",
                    response.status_code
                )
        else:
            self.log_test(
                "Get User Info (Unauthenticated)", 
                False, 
                "No response received",
                "auth/me"
            )

    def test_logout_without_session(self):
        """Test logout without active session"""
        print("\n🔐 Testing Logout Without Session")
        
        response = self.make_request('POST', 'auth/logout')
        
        if response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'message' in result:
                        self.log_test(
                            "Logout Without Session", 
                            True, 
                            f"Success: {result['message']}",
                            "auth/logout",
                            response.status_code
                        )
                    else:
                        self.log_test(
                            "Logout Without Session", 
                            False, 
                            "Response missing message field",
                            "auth/logout",
                            response.status_code
                        )
                except:
                    self.log_test(
                        "Logout Without Session", 
                        False, 
                        "Invalid JSON response",
                        "auth/logout",
                        response.status_code
                    )
            else:
                self.log_test(
                    "Logout Without Session", 
                    False, 
                    f"Expected 200 but got {response.status_code}",
                    "auth/logout",
                    response.status_code
                )
        else:
            self.log_test(
                "Logout Without Session", 
                False, 
                "No response received",
                "auth/logout"
            )

    def test_cors_and_cookies(self):
        """Test CORS headers and cookie handling"""
        print("\n🔐 Testing CORS and Cookie Configuration")
        
        # Make a simple request to check CORS headers
        response = self.make_request('GET', 'auth/me')
        
        if response:
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            cors_configured = any(cors_headers.values())
            
            if cors_configured:
                self.log_test(
                    "CORS Configuration", 
                    True, 
                    f"CORS headers present: {cors_headers}",
                    "auth/me",
                    response.status_code
                )
            else:
                self.log_test(
                    "CORS Configuration", 
                    False, 
                    "No CORS headers found - may cause issues with frontend",
                    "auth/me",
                    response.status_code
                )
        else:
            self.log_test(
                "CORS Configuration", 
                False, 
                "No response received to check CORS",
                "auth/me"
            )

    def run_authentication_tests(self):
        """Run all authentication tests on live site"""
        print("🚀 Starting NoFeesApts.com Live Authentication Tests")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Test all authentication endpoints
        self.test_login_with_valid_user()
        self.test_login_nonexistent_user()
        self.test_google_oauth_redirect()
        self.test_forgot_password()
        self.test_session_management_unauthenticated()
        self.test_logout_without_session()
        self.test_cors_and_cookies()
        
        # Results Summary
        print("\n" + "=" * 70)
        print(f"📊 Authentication Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['name']} ({result['endpoint']})")
            if result['details']:
                print(f"    {result['details']}")
        
        # Critical issues summary
        critical_issues = []
        for result in self.test_results:
            if not result['success']:
                if 'not found' in result['details'].lower() or result['status_code'] == 404:
                    critical_issues.append(f"Missing endpoint: {result['endpoint']}")
                elif 'cors' in result['name'].lower():
                    critical_issues.append("CORS configuration issues")
                elif result['status_code'] and result['status_code'] >= 500:
                    critical_issues.append(f"Server error on {result['endpoint']}")
        
        if critical_issues:
            print("\n🚨 Critical Issues Found:")
            for issue in critical_issues:
                print(f"  - {issue}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All authentication tests passed!")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} authentication tests failed!")
            return 1

def main():
    tester = LiveAuthTester()
    return tester.run_authentication_tests()

if __name__ == "__main__":
    sys.exit(main())