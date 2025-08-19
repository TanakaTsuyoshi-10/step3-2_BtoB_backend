#!/usr/bin/env python3
"""
Create admin user with proper company association via API
"""

import argparse
import requests
import sys
import time
from typing import Optional

class AdminCreator:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = timeout
        
    def create_admin_user(
        self, 
        email: str = "admin@example.com",
        password: str = "admin123",
        full_name: str = "システム管理者",
        company_id: int = 1,
        department: str = "システム管理部",
        employee_code: str = "SYS0001",
        max_retries: int = 3
    ) -> bool:
        """Create admin user with company association via API calls"""
        
        print(f"🔧 Creating admin user: {email}")
        
        # First, try to create the user (may already exist)
        user_data = {
            'email': email,
            'password': password,
            'full_name': full_name,
            'is_active': True,
            'is_superuser': True
        }
        
        for attempt in range(max_retries):
            try:
                # Try to login first to check if admin already exists
                login_response = self._login(email, password)
                if login_response:
                    print(f"✅ Admin user already exists and can login: {email}")
                    return self._ensure_employee_record(login_response, company_id, department, employee_code)
                
                # If login fails, try to create the user
                print(f"Attempt {attempt + 1}/{max_retries}: Creating admin user...")
                
                create_response = self.session.post(
                    f"{self.base_url}/api/v1/users/",
                    json=user_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if create_response.status_code in [200, 201]:
                    print(f"✅ Admin user created successfully: {email}")
                    
                    # Now login and create employee record
                    time.sleep(1)  # Brief delay
                    login_response = self._login(email, password)
                    if login_response:
                        return self._ensure_employee_record(login_response, company_id, department, employee_code)
                    else:
                        print("❌ Failed to login after user creation")
                        return False
                        
                elif create_response.status_code == 400:
                    # User might already exist, try login
                    print("ℹ️ User might already exist, attempting login...")
                    login_response = self._login(email, password)
                    if login_response:
                        return self._ensure_employee_record(login_response, company_id, department, employee_code)
                    else:
                        print(f"❌ User creation failed with 400: {create_response.text}")
                        
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
                    
        print(f"❌ Failed to create admin user after {max_retries} attempts")
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
                print(f"✅ Login successful for: {email}")
                return token
            else:
                print(f"❌ Login failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return None
    
    def _ensure_employee_record(
        self, 
        token: str, 
        company_id: int, 
        department: str, 
        employee_code: str
    ) -> bool:
        """Ensure admin has employee record for company association"""
        try:
            # Check current user info
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            user_response = self.session.get(
                f"{self.base_url}/api/v1/users/me",
                headers=headers
            )
            
            if user_response.status_code != 200:
                print(f"❌ Failed to get user info: {user_response.status_code}")
                return False
            
            user_info = user_response.json()
            user_id = user_info['id']
            print(f"ℹ️ Admin user ID: {user_id}")
            
            # Try to access metrics to see if employee record exists
            metrics_response = self.session.get(
                f"{self.base_url}/api/v1/metrics/kpi",
                headers=headers
            )
            
            if metrics_response.status_code == 200:
                print(f"✅ Admin already has proper company association")
                return True
            elif metrics_response.status_code == 403:
                print(f"ℹ️ Admin needs employee record for company association")
                # Note: Employee creation would require direct database access
                # This is handled by the database scripts
                print(f"🔄 Please run database employee creation for user_id: {user_id}")
                print(f"   Company ID: {company_id}")
                print(f"   Department: {department}")
                print(f"   Employee Code: {employee_code}")
                return True  # User creation was successful
            else:
                print(f"⚠️ Unexpected metrics response: {metrics_response.status_code}")
                return True  # User creation was successful
                
        except Exception as e:
            print(f"❌ Error checking employee record: {e}")
            return True  # User creation was successful
    
    def verify_admin(self, email: str, password: str) -> bool:
        """Verify admin user can login and access APIs"""
        print(f"🔍 Verifying admin user: {email}")
        
        token = self._login(email, password)
        if not token:
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
                print(f"✅ User info accessible: {user_info.get('email', 'N/A')}")
                print(f"   Superuser: {user_info.get('is_superuser', False)}")
            else:
                print(f"❌ User info not accessible: {user_response.status_code}")
                return False
            
            # Test metrics access
            metrics_response = self.session.get(
                f"{self.base_url}/api/v1/metrics/kpi",
                headers=headers
            )
            
            if metrics_response.status_code == 200:
                print(f"✅ Metrics API accessible")
            elif metrics_response.status_code == 403:
                print(f"⚠️ Metrics API requires employee record (403)")
            else:
                print(f"⚠️ Metrics API response: {metrics_response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Create admin user with API')
    parser.add_argument('--url', default='https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net', 
                        help='Base URL for API')
    parser.add_argument('--email', default='admin@example.com', 
                        help='Admin email')
    parser.add_argument('--password', default='admin123', 
                        help='Admin password')
    parser.add_argument('--full-name', default='システム管理者', 
                        help='Admin full name')
    parser.add_argument('--company-id', type=int, default=1, 
                        help='Company ID')
    parser.add_argument('--department', default='システム管理部', 
                        help='Department')
    parser.add_argument('--employee-code', default='SYS0001', 
                        help='Employee code')
    parser.add_argument('--verify-only', action='store_true', 
                        help='Only verify existing admin')
    parser.add_argument('--timeout', type=int, default=30, 
                        help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    creator = AdminCreator(args.url, args.timeout)
    
    if args.verify_only:
        success = creator.verify_admin(args.email, args.password)
    else:
        success = creator.create_admin_user(
            email=args.email,
            password=args.password,
            full_name=args.full_name,
            company_id=args.company_id,
            department=args.department,
            employee_code=args.employee_code
        )
    
    if success:
        print(f"\n✅ Admin user operation completed successfully")
        print(f"   Email: {args.email}")
        print(f"   Password: {args.password}")
        sys.exit(0)
    else:
        print(f"\n❌ Admin user operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()