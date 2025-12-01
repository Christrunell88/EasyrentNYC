#!/usr/bin/env python3
"""
Final Authentication Test - Core Functionality Verification
"""

import requests
import json
import time

def test_core_auth_flows():
    """Test the core authentication flows that matter most"""
    
    print("🚀 Final Authentication Test - Core Flows")
    print("=" * 50)
    
    results = []
    
    # 1. Test Admin Login
    print("\n1. Testing Admin Login...")
    try:
        response = requests.post(
            "https://nofeesapts.com/api/auth/login",
            json={"email": "placesfirm@gmail.com", "password": "Checkers080/?"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            admin_token = data.get('session_token')
            print("✅ Admin login successful")
            results.append(("Admin Login", True, f"Token: {admin_token[:20]}..."))
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            results.append(("Admin Login", False, f"Status: {response.status_code}"))
            admin_token = None
    except Exception as e:
        print(f"❌ Admin login error: {e}")
        results.append(("Admin Login", False, str(e)))
        admin_token = None
    
    # 2. Test Session Validation
    if admin_token:
        print("\n2. Testing Session Validation...")
        try:
            response = requests.get(
                "https://nofeesapts.com/api/auth/me",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Session valid for: {data.get('email')}")
                results.append(("Session Validation", True, f"User: {data.get('email')}"))
            else:
                print(f"❌ Session validation failed: {response.status_code}")
                results.append(("Session Validation", False, f"Status: {response.status_code}"))
        except Exception as e:
            print(f"❌ Session validation error: {e}")
            results.append(("Session Validation", False, str(e)))
    
    # 3. Test Admin Endpoints
    if admin_token:
        print("\n3. Testing Admin Endpoints...")
        try:
            response = requests.get(
                "https://nofeesapts.com/api/admin/stats",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Admin stats: {data.get('total_users')} users, {data.get('total_units')} units")
                results.append(("Admin Endpoints", True, f"Users: {data.get('total_users')}, Units: {data.get('total_units')}"))
            else:
                print(f"❌ Admin endpoints failed: {response.status_code}")
                results.append(("Admin Endpoints", False, f"Status: {response.status_code}"))
        except Exception as e:
            print(f"❌ Admin endpoints error: {e}")
            results.append(("Admin Endpoints", False, str(e)))
    
    # 4. Test User Signup
    print("\n4. Testing User Signup...")
    test_email = f"finaltest{int(time.time())}@example.com"
    try:
        response = requests.post(
            "https://nofeesapts.com/api/auth/signup",
            json={"email": test_email, "password": "TestPass123!", "name": "Final Test User"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            user_token = data.get('session_token')
            print(f"✅ User signup successful: {test_email}")
            results.append(("User Signup", True, f"Email: {test_email}"))
        else:
            print(f"❌ User signup failed: {response.status_code}")
            results.append(("User Signup", False, f"Status: {response.status_code}"))
            user_token = None
    except Exception as e:
        print(f"❌ User signup error: {e}")
        results.append(("User Signup", False, str(e)))
        user_token = None
    
    # 5. Test User Login
    if user_token:
        print("\n5. Testing User Login...")
        try:
            response = requests.post(
                "https://nofeesapts.com/api/auth/login",
                json={"email": test_email, "password": "TestPass123!"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User login successful")
                results.append(("User Login", True, f"Email: {test_email}"))
            else:
                print(f"❌ User login failed: {response.status_code}")
                results.append(("User Login", False, f"Status: {response.status_code}"))
        except Exception as e:
            print(f"❌ User login error: {e}")
            results.append(("User Login", False, str(e)))
    
    # 6. Test Password Reset
    print("\n6. Testing Password Reset...")
    try:
        response = requests.post(
            "https://nofeesapts.com/api/auth/forgot-password",
            json={"email": "chris.trunell@gmail.com"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Password reset: {data.get('message')}")
            results.append(("Password Reset", True, data.get('message')))
        else:
            print(f"❌ Password reset failed: {response.status_code}")
            results.append(("Password Reset", False, f"Status: {response.status_code}"))
    except Exception as e:
        print(f"❌ Password reset error: {e}")
        results.append(("Password Reset", False, str(e)))
    
    # 7. Test Protected Routes
    print("\n7. Testing Protected Routes...")
    try:
        response = requests.get("https://nofeesapts.com/api/auth/me", timeout=10)
        if response.status_code == 401:
            print("✅ Protected routes require authentication")
            results.append(("Protected Routes", True, "Returns 401 without auth"))
        else:
            print(f"❌ Protected routes should return 401: {response.status_code}")
            results.append(("Protected Routes", False, f"Status: {response.status_code}"))
    except Exception as e:
        print(f"❌ Protected routes error: {e}")
        results.append(("Protected Routes", False, str(e)))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FINAL AUTHENTICATION TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, details in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL AUTHENTICATION TESTS PASSED!")
        return 0
    else:
        print("⚠️  Some authentication tests failed")
        return 1

if __name__ == "__main__":
    exit(test_core_auth_flows())