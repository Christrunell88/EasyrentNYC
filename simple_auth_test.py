#!/usr/bin/env python3
"""
Simple Authentication Testing for NoFeesApts.com Live Site
"""

import requests
import json

def test_auth_endpoints():
    base_url = "https://nofeesapts.com/api"
    
    print("🚀 Testing NoFeesApts.com Authentication Endpoints")
    print("=" * 60)
    
    results = []
    
    # Test 1: Login with invalid credentials
    print("\n1. Testing Login with Invalid Credentials")
    try:
        response = requests.post(f"{base_url}/auth/login", 
                               json={"email": "chris.trunell@gmail.com", "password": "wrongpass"},
                               timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 401:
            results.append("✅ Login error handling works correctly")
        else:
            results.append(f"❌ Login error handling - expected 401, got {response.status_code}")
    except Exception as e:
        results.append(f"❌ Login test failed: {e}")
    
    # Test 2: Non-existent user login
    print("\n2. Testing Login with Non-existent User")
    try:
        response = requests.post(f"{base_url}/auth/login", 
                               json={"email": "nonexistent@example.com", "password": "anypass"},
                               timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 401:
            results.append("✅ Non-existent user handling works correctly")
        else:
            results.append(f"❌ Non-existent user handling - expected 401, got {response.status_code}")
    except Exception as e:
        results.append(f"❌ Non-existent user test failed: {e}")
    
    # Test 3: Google OAuth endpoint
    print("\n3. Testing Google OAuth Endpoint")
    try:
        response = requests.get(f"{base_url}/auth/google", allow_redirects=False, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 404:
            results.append("❌ Google OAuth endpoint not implemented (404)")
        elif response.status_code in [301, 302, 307, 308]:
            location = response.headers.get('Location', '')
            if 'google' in location.lower():
                results.append(f"✅ Google OAuth redirects correctly to: {location}")
            else:
                results.append(f"❌ Google OAuth redirects but not to Google: {location}")
        else:
            results.append(f"❌ Google OAuth unexpected response: {response.status_code}")
    except Exception as e:
        results.append(f"❌ Google OAuth test failed: {e}")
    
    # Test 4: Password reset
    print("\n4. Testing Password Reset")
    try:
        response = requests.post(f"{base_url}/auth/forgot-password", 
                               json={"email": "chris.trunell@gmail.com"},
                               timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'message' in data:
                results.append("✅ Password reset endpoint working correctly")
            else:
                results.append("❌ Password reset response missing message")
        else:
            results.append(f"❌ Password reset - expected 200, got {response.status_code}")
    except Exception as e:
        results.append(f"❌ Password reset test failed: {e}")
    
    # Test 5: Get user info (unauthenticated)
    print("\n5. Testing Get User Info (Unauthenticated)")
    try:
        response = requests.get(f"{base_url}/auth/me", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 401:
            results.append("✅ Auth/me correctly requires authentication")
        else:
            results.append(f"❌ Auth/me - expected 401, got {response.status_code}")
    except Exception as e:
        results.append(f"❌ Get user info test failed: {e}")
    
    # Test 6: Logout
    print("\n6. Testing Logout")
    try:
        response = requests.post(f"{base_url}/auth/logout", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'message' in data:
                results.append("✅ Logout endpoint working correctly")
            else:
                results.append("❌ Logout response missing message")
        else:
            results.append(f"❌ Logout - expected 200, got {response.status_code}")
    except Exception as e:
        results.append(f"❌ Logout test failed: {e}")
    
    # Test 7: CORS headers
    print("\n7. Testing CORS Headers")
    try:
        response = requests.get(f"{base_url}/auth/me", timeout=10)
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        cors_credentials = response.headers.get('Access-Control-Allow-Credentials')
        
        print(f"   CORS Origin: {cors_origin}")
        print(f"   CORS Credentials: {cors_credentials}")
        
        if cors_origin:
            results.append(f"✅ CORS configured: Origin={cors_origin}, Credentials={cors_credentials}")
        else:
            results.append("❌ No CORS headers found - may cause frontend issues")
    except Exception as e:
        results.append(f"❌ CORS test failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 AUTHENTICATION TEST RESULTS:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for result in results:
        print(result)
        if result.startswith("✅"):
            passed += 1
    
    print(f"\n📈 Summary: {passed}/{total} tests passed")
    
    # Critical issues
    critical_issues = []
    for result in results:
        if "not implemented" in result or "404" in result:
            critical_issues.append("Missing Google OAuth endpoint")
        elif "CORS" in result and "❌" in result:
            critical_issues.append("CORS configuration issues")
        elif "Server error" in result or "500" in result:
            critical_issues.append("Server errors detected")
    
    if critical_issues:
        print("\n🚨 CRITICAL ISSUES:")
        for issue in set(critical_issues):  # Remove duplicates
            print(f"  - {issue}")
    
    return passed == total

if __name__ == "__main__":
    success = test_auth_endpoints()
    exit(0 if success else 1)