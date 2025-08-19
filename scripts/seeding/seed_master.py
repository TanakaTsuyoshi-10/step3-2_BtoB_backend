#!/usr/bin/env python3
"""
Master seeding script that orchestrates the complete seeding process
Combines API-based user creation with database-level data generation
"""

import argparse
import subprocess
import sys
import os
import time
from typing import List, Dict, Any

class MasterSeeder:
    def __init__(self, base_url: str = "https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net"):
        self.base_url = base_url
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
    def run_complete_seeding(
        self,
        admin_email: str = "admin@example.com",
        admin_password: str = "admin123",
        company_id: int = 1,
        user_count: int = 20,
        create_test_suite: bool = True,
        clear_first: bool = False
    ) -> bool:
        """Run complete seeding process"""
        
        print("🚀 Starting complete seeding process...")
        print(f"   URL: {self.base_url}")
        print(f"   Company ID: {company_id}")
        print(f"   Users to create: {user_count}")
        print(f"   Test suite: {create_test_suite}")
        print(f"   Clear first: {clear_first}")
        
        try:
            # Step 1: Safety check
            if not self._check_safety():
                return False
            
            # Step 2: Clear existing data if requested
            if clear_first:
                if not self._clear_demo_data(company_id):
                    print("⚠️ Clear operation failed, continuing anyway...")
            
            # Step 3: Create/verify admin user
            if not self._create_admin_user(admin_email, admin_password, company_id):
                print("❌ Admin user creation/verification failed")
                return False
            
            # Step 4: Create test users for frontend
            if create_test_suite:
                if not self._create_test_suite(admin_email, admin_password, company_id):
                    print("⚠️ Test suite creation failed, continuing anyway...")
            
            # Step 5: Create demo data in database
            if not self._seed_database(company_id, user_count):
                print("❌ Database seeding failed")
                return False
            
            # Step 6: Verification
            if not self._verify_seeding():
                print("⚠️ Verification had issues, but seeding may have succeeded")
            
            print("\n🎉 Complete seeding process finished!")
            self._print_success_summary(admin_email, admin_password)
            return True
            
        except Exception as e:
            print(f"❌ Master seeding error: {e}")
            return False
    
    def _check_safety(self) -> bool:
        """Check safety requirements"""
        if not os.environ.get('SEED_ALLOW'):
            print("❌ Safety check failed: SEED_ALLOW environment variable not set")
            print("   Use: export SEED_ALLOW=1")
            return False
        
        print("✅ Safety check passed")
        return True
    
    def _create_admin_user(self, email: str, password: str, company_id: int) -> bool:
        """Create admin user via API"""
        print("\n🔧 Step: Creating/verifying admin user...")
        
        script_path = os.path.join(self.script_dir, "create_admin.py")
        cmd = [
            sys.executable, script_path,
            "--url", self.base_url,
            "--email", email,
            "--password", password,
            "--company-id", str(company_id)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Admin user ready")
                return True
            else:
                print(f"❌ Admin user creation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Admin user creation timed out")
            return False
        except Exception as e:
            print(f"❌ Admin user creation error: {e}")
            return False
    
    def _create_test_suite(self, admin_email: str, admin_password: str, company_id: int) -> bool:
        """Create test user suite"""
        print("\n🧪 Step: Creating test user suite...")
        
        script_path = os.path.join(self.script_dir, "create_test_user.py")
        cmd = [
            sys.executable, script_path,
            "--url", self.base_url,
            "--admin-email", admin_email,
            "--admin-password", admin_password,
            "--company-id", str(company_id),
            "--test-suite"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ Test suite created")
                return True
            else:
                print(f"⚠️ Test suite creation had issues: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️ Test suite creation timed out")
            return False
        except Exception as e:
            print(f"⚠️ Test suite creation error: {e}")
            return False
    
    def _seed_database(self, company_id: int, user_count: int) -> bool:
        """Seed database with demo data"""
        print("\n🌱 Step: Seeding database...")
        
        script_path = os.path.join(self.script_dir, "seed_database.py")
        cmd = [
            sys.executable, script_path,
            "--action", "seed",
            "--company-id", str(company_id),
            "--user-count", str(user_count),
            "--months-back", "12",
            "--devices-per-user", "2"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Database seeding completed")
                return True
            else:
                print(f"❌ Database seeding failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Database seeding timed out")
            return False
        except Exception as e:
            print(f"❌ Database seeding error: {e}")
            return False
    
    def _clear_demo_data(self, company_id: int) -> bool:
        """Clear existing demo data"""
        print("\n🧹 Step: Clearing existing demo data...")
        
        script_path = os.path.join(self.script_dir, "seed_database.py")
        cmd = [
            sys.executable, script_path,
            "--action", "clear",
            "--company-id", str(company_id),
            "--confirm-clear"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Demo data cleared")
                return True
            else:
                print(f"⚠️ Demo data clearing had issues: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️ Demo data clearing timed out")
            return False
        except Exception as e:
            print(f"⚠️ Demo data clearing error: {e}")
            return False
    
    def _verify_seeding(self) -> bool:
        """Verify seeding was successful"""
        print("\n🔍 Step: Verifying seeding...")
        
        # Test admin login
        script_path = os.path.join(self.script_dir, "create_admin.py")
        cmd = [
            sys.executable, script_path,
            "--url", self.base_url,
            "--verify-only"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Admin verification passed")
            else:
                print(f"⚠️ Admin verification issues: {result.stderr}")
            
            # Test user login
            script_path = os.path.join(self.script_dir, "create_test_user.py")
            cmd = [
                sys.executable, script_path,
                "--url", self.base_url,
                "--verify-only"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Test user verification passed")
            else:
                print(f"⚠️ Test user verification issues: {result.stderr}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Verification error: {e}")
            return False
    
    def _print_success_summary(self, admin_email: str, admin_password: str):
        """Print success summary with credentials"""
        print("\n" + "="*60)
        print("🎉 SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"🌐 Application URL: {self.base_url}")
        print("\n📋 Available Accounts:")
        print(f"   🔑 Admin: {admin_email} / {admin_password}")
        print(f"   🧪 Test User: testuser@example.com / password123")
        print(f"   👥 Demo Users: demo.user001@scope3holdings.co.jp / demo123")
        print(f"        (and many more demo.user002, demo.user003, etc.)")
        print("\n📊 Data Generated:")
        print(f"   • Realistic energy consumption data (12 months)")
        print(f"   • Points and rankings based on energy savings")
        print(f"   • Sample rewards and achievements")
        print(f"   • Multiple devices per user")
        print("\n🎯 Testing Instructions:")
        print(f"   1. Login to dashboard with any account above")
        print(f"   2. Check KPI cards show realistic metrics")
        print(f"   3. Verify charts display historical data")
        print(f"   4. Test navigation between all 7 tabs")
        print(f"   5. Verify responsive design on different screen sizes")
        print("\n🚀 Next Steps:")
        print(f"   • The application is ready for frontend testing")
        print(f"   • Metrics API should return real data")
        print(f"   • Dashboard should display meaningful charts")
        print(f"   • All user accounts are ready to use")
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Master seeding script')
    parser.add_argument('--url', default='https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net',
                        help='Base URL for API')
    parser.add_argument('--admin-email', default='admin@example.com',
                        help='Admin email')
    parser.add_argument('--admin-password', default='admin123',
                        help='Admin password')
    parser.add_argument('--company-id', type=int, default=1,
                        help='Company ID')
    parser.add_argument('--user-count', type=int, default=20,
                        help='Number of demo users to create')
    parser.add_argument('--no-test-suite', action='store_true',
                        help='Skip test suite creation')
    parser.add_argument('--clear-first', action='store_true',
                        help='Clear existing demo data first')
    
    args = parser.parse_args()
    
    seeder = MasterSeeder(args.url)
    
    success = seeder.run_complete_seeding(
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        company_id=args.company_id,
        user_count=args.user_count,
        create_test_suite=not args.no_test_suite,
        clear_first=args.clear_first
    )
    
    if success:
        sys.exit(0)
    else:
        print("\n❌ Master seeding process failed")
        sys.exit(1)

if __name__ == "__main__":
    main()