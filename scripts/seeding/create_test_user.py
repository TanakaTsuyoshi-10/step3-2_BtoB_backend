#!/usr/bin/env python3
"""
Create test user for frontend development and testing
"""

import argparse
import requests
import sys
import time
from typing import Optional

class TestUserCreator:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = timeout
        
    def create_test_user(
        self,
        admin_email: str,
        admin_password: str,
        email: str = "testuser@example.com",
        password: str = "password123",
        full_name: str = "テストユーザー",
        company_id: int = 1,
        department: str = "テスト部",
        employee_code: str = "TEST001",
        max_retries: int = 3
    ) -> bool:
        """Create test user specifically for frontend testing"""
        
        print(f"🧪 Creating test user: {email}")
        
        # Get admin token
        admin_token = self._login(admin_email, admin_password)
        if not admin_token:
            print("❌ Failed to login as admin")
            return False
        
        # Check if user already exists and can login
        existing_token = self._login(email, password)
        if existing_token:
            print(f"✅ Test user already exists and can login: {email}")
            return self._verify_test_user_access(email, password)
        
        # Create user data
        user_data = {
            'email': email,
            'password': password,
            'full_name': full_name,
            'is_active': True,
            'is_superuser': False
        }
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}: Creating test user...")
                
                headers = {
                    'Authorization': f'Bearer {admin_token}',
                    'Content-Type': 'application/json'
                }
                
                create_response = self.session.post(
                    f"{self.base_url}/api/v1/users/",
                    json=user_data,
                    headers=headers
                )
                
                if create_response.status_code in [200, 201]:
                    user_info = create_response.json()
                    user_id = user_info.get('id')
                    print(f"✅ Test user created successfully: {email} (ID: {user_id})")
                    
                    # Note about employee record
                    print(f"ℹ️ Employee record needed for metrics API access:")
                    print(f"   User ID: {user_id}")
                    print(f"   Company ID: {company_id}")
                    print(f"   Department: {department}")
                    print(f"   Employee Code: {employee_code}")
                    
                    # Verify login works
                    time.sleep(1)
                    return self._verify_test_user_access(email, password)
                    
                elif create_response.status_code == 400:
                    error_detail = create_response.json().get('detail', 'Unknown error')
                    print(f"❌ User creation failed: {error_detail}")
                    
                    if 'already registered' in error_detail.lower():
                        print("ℹ️ User already exists, attempting login...")
                        return self._verify_test_user_access(email, password)
                    
                else:
                    print(f"❌ User creation failed: {create_response.status_code}")
                    print(f"Response: {create_response.text}")
                    
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"❌ Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
        print(f"❌ Failed to create test user after {max_retries} attempts")
        return False
    
    def _login(self, email: str, password: str) -> Optional[str]:
        """Attempt to login and return access token"""
        try:
            login_data = {
                'username': email,
                'password': password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/login/access-token",
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data=login_data
            )
            
            if response.status_code == 200:
                token = response.json()['access_token']
                return token
            else:
                return None
                
        except Exception as e:
            return None
    
    def _verify_test_user_access(self, email: str, password: str) -> bool:
        """Verify test user access for frontend testing"""
        print(f"🔍 Verifying test user access: {email}")
        
        token = self._login(email, password)
        if not token:
            print("❌ Test user login failed")
            return False
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Test user info access
            user_response = self.session.get(
                f"{self.base_url}/api/v1/users/me",
                headers=headers
            )
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                print(f"✅ Test user login successful: {user_info.get('email', 'N/A')}")
                print(f"   Full name: {user_info.get('full_name', 'N/A')}")
                print(f"   Active: {user_info.get('is_active', False)}")
                print(f"   Superuser: {user_info.get('is_superuser', False)}")
            else:
                print(f"❌ User info not accessible: {user_response.status_code}")
                return False
            
            # Test various API endpoints
            endpoints_to_test = [
                ('/api/v1/metrics/kpi', 'KPI Metrics'),
                ('/api/v1/devices', 'Devices'),
                ('/api/v1/energy-records', 'Energy Records'),
                ('/api/v1/points', 'Points'),
                ('/api/v1/rewards', 'Rewards')
            ]
            
            accessible_endpoints = []
            for endpoint, name in endpoints_to_test:
                try:
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        accessible_endpoints.append(name)
                        print(f"✅ {name} API accessible")
                    elif response.status_code == 403:
                        print(f"⚠️ {name} API requires employee record (403)")
                    elif response.status_code == 404:
                        print(f"⚠️ {name} API not found (404)")
                    else:
                        print(f"⚠️ {name} API response: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error testing {name} API: {e}")
            
            if accessible_endpoints:
                print(f"✅ Test user can access: {', '.join(accessible_endpoints)}")
            
            # Show frontend testing instructions
            print(f"\n🎯 Frontend Testing Instructions:")
            print(f"   URL: {self.base_url}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"   Test scenarios:")
            print(f"   - Login to dashboard")
            print(f"   - Navigate between pages")
            print(f"   - Check API error handling")
            print(f"   - Test responsive design")
            
            return True
            
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def create_frontend_test_suite(
        self,
        admin_email: str,
        admin_password: str,
        company_id: int = 1
    ) -> bool:
        """Create a suite of test users for comprehensive frontend testing"""
        
        test_users = [
            {
                'email': 'testuser@example.com',
                'password': 'password123',
                'full_name': 'テストユーザー',
                'department': 'テスト部',
                'employee_code': 'TEST001'
            },
            {
                'email': 'demo.employee@scope3holdings.co.jp',
                'password': 'demo123',
                'full_name': 'デモ社員',
                'department': '営業部',
                'employee_code': 'DEMO001'
            },
            {
                'email': 'frontend.test@example.com',
                'password': 'frontend123',
                'full_name': 'フロントエンドテスト',
                'department': '開発部',
                'employee_code': 'FRONT001'
            }
        ]
        
        print(f"🧪 Creating frontend test suite ({len(test_users)} users)...")
        
        success_count = 0
        for i, user in enumerate(test_users, 1):
            print(f"\n--- Test User {i}/{len(test_users)} ---")
            
            success = self.create_test_user(
                admin_email=admin_email,
                admin_password=admin_password,
                email=user['email'],
                password=user['password'],
                full_name=user['full_name'],
                company_id=company_id,
                department=user['department'],
                employee_code=user['employee_code']
            )
            
            if success:
                success_count += 1
            
            # Brief delay between creations
            if i < len(test_users):
                time.sleep(1)
        
        print(f"\n✅ Created {success_count}/{len(test_users)} test users successfully")
        
        if success_count > 0:
            print(f"\n🎯 Test Suite Ready!")
            print(f"   Use any of the created accounts for frontend testing")
            print(f"   All accounts use their respective passwords")
            print(f"   Recommended: testuser@example.com / password123")
        
        return success_count > 0

def main():
    parser = argparse.ArgumentParser(description='Create test user for frontend development')
    parser.add_argument('--url', default='https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net', 
                        help='Base URL for API')
    parser.add_argument('--admin-email', default='admin@example.com', 
                        help='Admin email for authentication')
    parser.add_argument('--admin-password', default='admin123', 
                        help='Admin password for authentication')
    parser.add_argument('--email', default='testuser@example.com', 
                        help='Test user email')
    parser.add_argument('--password', default='password123', 
                        help='Test user password')
    parser.add_argument('--full-name', default='テストユーザー', 
                        help='Test user full name')
    parser.add_argument('--company-id', type=int, default=1, 
                        help='Company ID')
    parser.add_argument('--department', default='テスト部', 
                        help='Department')
    parser.add_argument('--employee-code', default='TEST001', 
                        help='Employee code')
    parser.add_argument('--verify-only', action='store_true', 
                        help='Only verify existing test user')
    parser.add_argument('--test-suite', action='store_true', 
                        help='Create complete frontend test suite')
    parser.add_argument('--timeout', type=int, default=30, 
                        help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    creator = TestUserCreator(args.url, args.timeout)
    
    if args.test_suite:
        success = creator.create_frontend_test_suite(
            admin_email=args.admin_email,
            admin_password=args.admin_password,
            company_id=args.company_id
        )
    elif args.verify_only:
        success = creator._verify_test_user_access(args.email, args.password)
    else:
        success = creator.create_test_user(
            admin_email=args.admin_email,
            admin_password=args.admin_password,
            email=args.email,
            password=args.password,
            full_name=args.full_name,
            company_id=args.company_id,
            department=args.department,
            employee_code=args.employee_code
        )
    
    if success:
        print(f"\n✅ Test user operation completed successfully")
        if not args.test_suite:
            print(f"   Email: {args.email}")
            print(f"   Password: {args.password}")
        sys.exit(0)
    else:
        print(f"\n❌ Test user operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()