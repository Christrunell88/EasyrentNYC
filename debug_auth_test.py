#!/usr/bin/env python3
"""
Debug Authentication Testing for OAuth and Login functionality
"""

import requests
import json
from datetime import datetime

def test_auth_endpoints():
    base_url = "http://localhost:8001/api"
    
    print("🔍 Debug Authentication Testing")
    print(f"🔗 Testing against: {base_url}")
    print("=" * 60)
    
    # Test 1: Unauthenticated access
    print("\n1. Testing unauthenticated access to /auth/me")
    try:
        response = requests.get(f"{base_url}/auth/me", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 401:
            print("   ✅ Correctly returns 401 for unauthenticated access")
        else:
            print("   ❌ Expected 401 for unauthenticated access")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Admin login
    print("\n2. Testing admin login (placesfirm@gmail.com)")
    admin_data = {
        "email": "placesfirm@gmail.com",
        "password": "Checkers080/?"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=admin_data, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            admin_token = result.get('session_token')
            user_data = result.get('user', {})
            is_admin = user_data.get('is_admin', False)
            
            if admin_token and is_admin:
                print("   ✅ Admin login successful")
                
                # Test session validation
                print("\n3. Testing session validation with admin token")
                headers = {'Authorization': f'Bearer {admin_token}'}
                response = requests.get(f"{base_url}/auth/me", headers=headers, timeout=5)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
                if response.status_code == 200:
                    print("   ✅ Session validation successful")
                else:
                    print("   ❌ Session validation failed")
                    
            else:
                print("   ❌ Admin login failed - missing token or admin privileges")
        else:
            print("   ❌ Admin login failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Regular user login
    print("\n4. Testing regular user login (chris.trunell@gmail.com)")
    user_data = {
        "email": "chris.trunell@gmail.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=user_data, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            user_token = result.get('session_token')
            user_info = result.get('user', {})
            is_admin = user_info.get('is_admin', False)
            
            if user_token and not is_admin:
                print("   ✅ Regular user login successful")
            else:
                print("   ❌ Regular user login failed - missing token or unexpected admin privileges")
        else:
            print("   ❌ Regular user login failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: New user signup
    print("\n5. Testing new user signup")
    timestamp = datetime.now().strftime('%H%M%S')
    signup_data = {
        "email": f"testuser_{timestamp}@example.com",
        "password": "testpass123",
        "name": "Test User"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/signup", json=signup_data, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            signup_token = result.get('session_token')
            user_info = result.get('user', {})
            
            if signup_token and user_info:
                print("   ✅ User signup successful with auto-login")
                
                # Test duplicate signup
                print("\n6. Testing duplicate email signup")
                response = requests.post(f"{base_url}/auth/signup", json=signup_data, timeout=5)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
                if response.status_code == 400:
                    print("   ✅ Duplicate email correctly rejected")
                else:
                    print("   ❌ Duplicate email not properly handled")
                    
                # Test logout
                print("\n7. Testing logout functionality")
                headers = {'Authorization': f'Bearer {signup_token}'}
                response = requests.post(f"{base_url}/auth/logout", headers=headers, timeout=5)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
                if response.status_code == 200:
                    print("   ✅ Logout successful")
                    
                    # Verify session is cleared
                    response = requests.get(f"{base_url}/auth/me", headers=headers, timeout=5)
                    print(f"   Post-logout /auth/me status: {response.status_code}")
                    if response.status_code == 401:
                        print("   ✅ Session properly cleared after logout")
                    else:
                        print("   ❌ Session not properly cleared after logout")
                else:
                    print("   ❌ Logout failed")
            else:
                print("   ❌ User signup failed - missing token or user data")
        else:
            print("   ❌ User signup failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Google OAuth endpoint
    print("\n8. Testing Google OAuth endpoint")
    try:
        response = requests.get(f"{base_url}/auth/google", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 404:
            print("   ❌ Google OAuth endpoint not implemented")
        elif response.status_code in [200, 302, 307]:
            print("   ✅ Google OAuth endpoint available")
        else:
            print(f"   ⚠️  Unexpected status for Google OAuth endpoint")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: OAuth session validation
    print("\n9. Testing OAuth session validation")
    try:
        headers = {'X-Session-ID': 'invalid_test_session_123'}
        response = requests.post(f"{base_url}/auth/session", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 400:
            print("   ✅ Invalid session_id correctly rejected")
        else:
            print("   ⚠️  Unexpected response for invalid session_id")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Debug testing completed")

if __name__ == "__main__":
    test_auth_endpoints()