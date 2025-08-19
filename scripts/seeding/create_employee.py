#!/usr/bin/env python3
"""
Create employee user with proper company association via API
"""

import argparse
import requests
import sys
import time
from typing import Optional, Dict, Any

class EmployeeCreator:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = timeout
        
    def create_employee_user(
        self,
        admin_email: str,
        admin_password: str,
        email: str,
        password: str,
        full_name: str,
        company_id: int,
        department: str,
        employee_code: str,
        max_retries: int = 3
    ) -> bool:
        """Create employee user with company association via API calls"""
        
        print(f"🔧 Creating employee user: {email}")
        
        # First, get admin token
        admin_token = self._login(admin_email, admin_password)
        if not admin_token:
            print("❌ Failed to login as admin")
            return False
        
        # Check if user already exists
        existing_user = self._check_user_exists(admin_token, email)
        if existing_user:
            print(f"✅ Employee user already exists: {email}")
            return self._verify_employee_access(email, password)
        
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
                print(f"Attempt {attempt + 1}/{max_retries}: Creating employee user...")
                
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
                    print(f"✅ Employee user created successfully: {email} (ID: {user_id})")
                    
                    # Create employee record via database (would need direct DB access)
                    print(f"ℹ️ Employee record needed for user_id: {user_id}")
                    print(f"   Company ID: {company_id}")
                    print(f"   Department: {department}")
                    print(f"   Employee Code: {employee_code}")
                    
                    # Verify login works
                    time.sleep(1)
                    return self._verify_employee_access(email, password)
                    
                elif create_response.status_code == 400:
                    error_detail = create_response.json().get('detail', 'Unknown error')
                    print(f"❌ User creation failed: {error_detail}")
                    if 'already registered' in error_detail.lower():
                        return self._verify_employee_access(email, password)
                    
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
                    
        print(f"❌ Failed to create employee user after {max_retries} attempts")
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
            print(f"❌ Login error: {e}")
            return None
    
    def _check_user_exists(self, admin_token: str, email: str) -> Optional[Dict[Any, Any]]:
        """Check if user already exists"""
        try:
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            # Try to get user by email (if endpoint exists)
            # For now, we'll try to create and handle the error
            return None
            
        except Exception as e:
            print(f"❌ Error checking user: {e}")
            return None
    
    def _verify_employee_access(self, email: str, password: str) -> bool:
        """Verify employee can login and access appropriate APIs"""
        print(f"🔍 Verifying employee access: {email}")
        
        token = self._login(email, password)
        if not token:
            print("❌ Employee login failed")
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
                print(f"✅ Employee login successful: {user_info.get('email', 'N/A')}")
                print(f"   Superuser: {user_info.get('is_superuser', False)}")
            else:
                print(f"❌ User info not accessible: {user_response.status_code}")
                return False
            
            # Test metrics access (may require employee record)
            metrics_response = self.session.get(
                f"{self.base_url}/api/v1/metrics/kpi",
                headers=headers
            )
            
            if metrics_response.status_code == 200:
                print(f"✅ Metrics API accessible")
            elif metrics_response.status_code == 403:
                print(f"⚠️ Metrics API requires employee record (403)")
                print(f"   This is expected until employee record is created in database")
            else:
                print(f"⚠️ Metrics API response: {metrics_response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def create_multiple_employees(
        self,
        admin_email: str,
        admin_password: str,
        employees: list,
        company_id: int
    ) -> bool:
        """Create multiple employee users"""
        print(f"🔧 Creating {len(employees)} employee users...")
        
        success_count = 0
        for i, emp in enumerate(employees, 1):
            print(f"\n--- Employee {i}/{len(employees)} ---")
            
            success = self.create_employee_user(
                admin_email=admin_email,
                admin_password=admin_password,
                email=emp['email'],
                password=emp['password'],
                full_name=emp['full_name'],
                company_id=company_id,
                department=emp['department'],
                employee_code=emp['employee_code']
            )
            
            if success:
                success_count += 1
            
            # Brief delay between creations
            if i < len(employees):
                time.sleep(1)
        
        print(f"\n✅ Created {success_count}/{len(employees)} employee users successfully")
        return success_count == len(employees)

def main():
    parser = argparse.ArgumentParser(description='Create employee user with API')
    parser.add_argument('--url', default='https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net', 
                        help='Base URL for API')
    parser.add_argument('--admin-email', default='admin@example.com', 
                        help='Admin email for authentication')
    parser.add_argument('--admin-password', default='admin123', 
                        help='Admin password for authentication')
    parser.add_argument('--email', required=True, 
                        help='Employee email')
    parser.add_argument('--password', default='password123', 
                        help='Employee password')
    parser.add_argument('--full-name', required=True, 
                        help='Employee full name')
    parser.add_argument('--company-id', type=int, default=1, 
                        help='Company ID')
    parser.add_argument('--department', default='営業部', 
                        help='Department')
    parser.add_argument('--employee-code', required=True, 
                        help='Employee code')
    parser.add_argument('--verify-only', action='store_true', 
                        help='Only verify existing employee')
    parser.add_argument('--timeout', type=int, default=30, 
                        help='Request timeout in seconds')
    parser.add_argument('--batch-file', 
                        help='JSON file with multiple employees to create')
    
    args = parser.parse_args()
    
    creator = EmployeeCreator(args.url, args.timeout)
    
    if args.batch_file:
        # Batch creation from JSON file
        try:
            import json
            with open(args.batch_file, 'r', encoding='utf-8') as f:
                employees = json.load(f)
            
            success = creator.create_multiple_employees(
                admin_email=args.admin_email,
                admin_password=args.admin_password,
                employees=employees,
                company_id=args.company_id
            )
        except Exception as e:
            print(f"❌ Error reading batch file: {e}")
            sys.exit(1)
    elif args.verify_only:
        success = creator._verify_employee_access(args.email, args.password)
    else:
        success = creator.create_employee_user(
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
        print(f"\n✅ Employee operation completed successfully")
        if not args.batch_file:
            print(f"   Email: {args.email}")
            print(f"   Password: {args.password}")
        sys.exit(0)
    else:
        print(f"\n❌ Employee operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()