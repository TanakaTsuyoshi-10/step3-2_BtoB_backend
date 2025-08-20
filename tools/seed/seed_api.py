#!/usr/bin/env python3
"""
API-based seeding for user and energy data
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
try:
    from .seed_config import config
except ImportError:
    from seed_config import config

class APISeedClient:
    """Client for seeding data via API"""
    
    def __init__(self):
        self.base_url = config.api_base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.admin_token: Optional[str] = None
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin and store token"""
        try:
            print("🔐 Authenticating as admin...")
            
            login_data = {
                'username': config.admin_email,
                'password': config.admin_password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/login/access-token",
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data['access_token']
                print(f"✅ Admin authentication successful")
                return True
            else:
                print(f"❌ Admin authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.admin_token:
            raise ValueError("Not authenticated. Call authenticate_admin() first.")
        
        return {
            'Authorization': f'Bearer {self.admin_token}',
            'Content-Type': 'application/json'
        }
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a user via API"""
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(user_data['email'])
            if existing_user:
                print(f"ℹ️ User already exists: {user_data['email']}")
                return existing_user
            
            # Create new user
            create_data = {
                'email': user_data['email'],
                'password': user_data['password'],
                'full_name': user_data['full_name'],
                'is_active': user_data['is_active'],
                'is_superuser': False
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/users/",
                headers=self._get_auth_headers(),
                json=create_data
            )
            
            if response.status_code in [200, 201]:
                user_info = response.json()
                print(f"✅ User created: {user_data['email']} (ID: {user_info.get('id')})")
                return user_info
            else:
                print(f"❌ User creation failed for {user_data['email']}: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating user {user_data['email']}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (if endpoint exists)"""
        try:
            # Try to get user list and find by email
            response = self.session.get(
                f"{self.base_url}/api/v1/users/",
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user.get('email') == email:
                        return user
            
            return None
            
        except Exception:
            # If users endpoint doesn't exist or fails, return None
            return None
    
    def create_users_batch(self, users_data: List[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """Create multiple users"""
        print(f"👥 Creating {len(users_data)} users...")
        
        created_users = []
        for i, user_data in enumerate(users_data, 1):
            print(f"Creating user {i}/{len(users_data)}: {user_data['email']}")
            
            user = self.create_user(user_data)
            created_users.append(user)
            
            # Brief delay to avoid rate limiting
            if i < len(users_data):
                time.sleep(0.5)
        
        success_count = len([u for u in created_users if u is not None])
        print(f"✅ Created {success_count}/{len(users_data)} users")
        
        return created_users
    
    def verify_metrics_apis(self) -> Dict[str, bool]:
        """Verify that metrics APIs are accessible"""
        print("🔍 Verifying metrics APIs...")
        
        endpoints = {
            'kpi': '/api/v1/metrics/kpi',
            'monthly_usage': f'/api/v1/metrics/monthly-usage?year={config.current_year}',
            'co2_trend': '/api/v1/metrics/co2-trend?interval=month',
            'yoy_usage': f'/api/v1/metrics/yoy-usage?month={config.current_year}-{config.current_month:02d}'
        }
        
        results = {}
        
        for name, endpoint in endpoints.items():
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=self._get_auth_headers()
                )
                
                results[name] = response.status_code == 200
                
                if response.status_code == 200:
                    print(f"✅ {name}: 200 OK")
                else:
                    print(f"❌ {name}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {name}: Error - {e}")
                results[name] = False
        
        return results
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics data for verification"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/metrics/kpi",
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            print(f"Error getting current metrics: {e}")
            return {}
    
    def test_user_authentication(self, email: str, password: str) -> bool:
        """Test if a user can authenticate"""
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
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def verify_created_users(self, users_data: List[Dict[str, Any]]) -> int:
        """Verify that created users can authenticate"""
        print("🔍 Verifying user authentication...")
        
        success_count = 0
        for user_data in users_data[:5]:  # Test first 5 users
            if self.test_user_authentication(user_data['email'], user_data['password']):
                success_count += 1
                print(f"✅ {user_data['email']}: Auth OK")
            else:
                print(f"❌ {user_data['email']}: Auth failed")
        
        print(f"✅ {success_count}/5 users can authenticate")
        return success_count

# Convenience functions
def seed_users_via_api() -> bool:
    """Seed users via API"""
    client = APISeedClient()
    
    if not client.authenticate_admin():
        return False
    
    users_data = config.get_users_data()
    created_users = client.create_users_batch(users_data)
    
    # Verify some users can authenticate
    auth_count = client.verify_created_users(users_data)
    
    return auth_count > 0

def verify_api_endpoints() -> Dict[str, bool]:
    """Verify API endpoints are working"""
    client = APISeedClient()
    
    if not client.authenticate_admin():
        return {}
    
    return client.verify_metrics_apis()

def get_current_api_metrics() -> Dict[str, Any]:
    """Get current metrics from API"""
    client = APISeedClient()
    
    if not client.authenticate_admin():
        return {}
    
    return client.get_current_metrics()