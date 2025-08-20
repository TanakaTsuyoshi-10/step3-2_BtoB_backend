#!/usr/bin/env python3
"""
Consolidated seed runner with idempotency
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

try:
    from .seed_config import config
    from .seed_api import seed_users_via_api, verify_api_endpoints, get_current_api_metrics
    from .seed_db import seed_database_direct, get_database_metrics
except ImportError:
    # Handle direct execution
    from seed_config import config
    from seed_api import seed_users_via_api, verify_api_endpoints, get_current_api_metrics
    from seed_db import seed_database_direct, get_database_metrics

class SeedRunner:
    """Main seed runner with comprehensive orchestration"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            'api_seeding': False,
            'database_seeding': False,
            'verification': False,
            'metrics_populated': False
        }
    
    def run_complete_seeding(self) -> bool:
        """Run complete seeding process with idempotency"""
        print("🌱 Starting comprehensive seeding process...")
        print(f"   Target: {config.company_name} (ID: {config.company_id})")
        print(f"   API Base: {config.api_base_url}")
        print(f"   Users: {config.user_count} total, {config.active_user_count} active")
        print("=" * 60)
        
        try:
            # Step 1: Seed users via API
            print("\n📋 Step 1: API-based user seeding")
            self.results['api_seeding'] = self._run_api_seeding()
            
            # Step 2: Seed database directly
            print("\n📋 Step 2: Database-level seeding")
            self.results['database_seeding'] = self._run_database_seeding()
            
            # Step 3: Verify APIs return data
            print("\n📋 Step 3: API endpoint verification")
            self.results['verification'] = self._verify_api_endpoints()
            
            # Step 4: Check metrics population
            print("\n📋 Step 4: Metrics data verification")
            self.results['metrics_populated'] = self._verify_metrics_populated()
            
            # Final summary
            self._print_final_summary()
            
            # Overall success if critical steps completed
            overall_success = (
                self.results['database_seeding'] and
                self.results['metrics_populated']
            )
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Seeding process failed: {e}")
            return False
    
    def _run_api_seeding(self) -> bool:
        """Run API-based seeding with retry logic"""
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            print(f"  Attempt {attempt}/{max_retries}: Creating users via API...")
            
            try:
                success = seed_users_via_api()
                
                if success:
                    print("  ✅ API seeding successful")
                    return True
                else:
                    print(f"  ⚠️ API seeding attempt {attempt} failed")
                    
            except Exception as e:
                print(f"  ❌ API seeding attempt {attempt} error: {e}")
            
            if attempt < max_retries:
                print(f"  ⏳ Waiting 5 seconds before retry...")
                time.sleep(5)
        
        print("  ⚠️ API seeding failed after all retries (continuing with database fallback)")
        return False
    
    def _run_database_seeding(self) -> bool:
        """Run database-level seeding"""
        try:
            print("  🗄️ Running database seeding...")
            success = seed_database_direct()
            
            if success:
                print("  ✅ Database seeding successful")
                return True
            else:
                print("  ❌ Database seeding failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Database seeding error: {e}")
            return False
    
    def _verify_api_endpoints(self) -> bool:
        """Verify API endpoints are accessible"""
        try:
            print("  🔍 Checking API endpoint accessibility...")
            
            api_results = verify_api_endpoints()
            
            if not api_results:
                print("  ❌ Could not verify API endpoints (authentication failed)")
                return False
            
            success_count = sum(1 for result in api_results.values() if result)
            total_count = len(api_results)
            
            print(f"  📊 API endpoints: {success_count}/{total_count} accessible")
            
            for endpoint, status in api_results.items():
                status_icon = "✅" if status else "❌"
                print(f"    {status_icon} {endpoint}")
            
            return success_count >= 2  # At least 2 endpoints should work
            
        except Exception as e:
            print(f"  ❌ API verification error: {e}")
            return False
    
    def _verify_metrics_populated(self) -> bool:
        """Verify that metrics APIs return meaningful data"""
        try:
            print("  📊 Verifying metrics data population...")
            
            # Get metrics from API
            api_metrics = get_current_api_metrics()
            
            # Get metrics from database
            db_metrics = get_database_metrics()
            
            if not api_metrics and not db_metrics:
                print("  ❌ No metrics data available from API or database")
                return False
            
            # Check API metrics
            if api_metrics:
                print("  📡 API Metrics:")
                kpi_populated = self._check_kpi_metrics(api_metrics)
            else:
                print("  ⚠️ API metrics not available")
                kpi_populated = False
            
            # Check database metrics
            if db_metrics:
                print("  🗄️ Database Metrics:")
                db_populated = self._check_kpi_metrics(db_metrics)
            else:
                print("  ⚠️ Database metrics not available")
                db_populated = False
            
            # Success if either API or database has populated data
            success = kpi_populated or db_populated
            
            if success:
                print("  ✅ Metrics are properly populated")
            else:
                print("  ❌ Metrics are not sufficiently populated")
            
            return success
            
        except Exception as e:
            print(f"  ❌ Metrics verification error: {e}")
            return False
    
    def _check_kpi_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Check if KPI metrics are populated with meaningful data"""
        required_fields = ['active_users', 'electricity_total_kwh', 'gas_total_m3', 'co2_reduction_total_kg']
        
        populated_count = 0
        
        for field in required_fields:
            value = metrics.get(field, 0)
            is_populated = value > 0
            
            status_icon = "✅" if is_populated else "❌"
            print(f"    {status_icon} {field}: {value}")
            
            if is_populated:
                populated_count += 1
        
        # Success if at least 3 out of 4 metrics are populated
        return populated_count >= 3
    
    def _print_final_summary(self):
        """Print comprehensive final summary"""
        duration = datetime.now() - self.start_time
        
        print("\n" + "=" * 60)
        print("🎯 SEEDING PROCESS SUMMARY")
        print("=" * 60)
        
        print(f"⏱️ Duration: {duration.total_seconds():.1f} seconds")
        print(f"🏢 Company: {config.company_name} (ID: {config.company_id})")
        print(f"🌐 API Base: {config.api_base_url}")
        
        print("\n📋 Process Results:")
        for step, result in self.results.items():
            status_icon = "✅" if result else "❌"
            step_name = step.replace('_', ' ').title()
            print(f"  {status_icon} {step_name}")
        
        success_count = sum(1 for result in self.results.values() if result)
        total_count = len(self.results)
        
        print(f"\n📊 Overall Success Rate: {success_count}/{total_count}")
        
        if self.results['metrics_populated']:
            print("\n🎉 SUCCESS: Frontend dashboards should now display data!")
            print("\n🔗 Next Steps:")
            print("   1. Visit the frontend dashboard")
            print("   2. Login with admin@example.com / admin123")
            print("   3. Verify KPI cards show non-zero values")
            print("   4. Check that charts display data trends")
        else:
            print("\n⚠️ PARTIAL SUCCESS: Some data was seeded but metrics may not be fully populated")
            print("\n🔧 Troubleshooting:")
            print("   1. Check API authentication")
            print("   2. Verify database connectivity")
            print("   3. Review error messages above")
        
        print("=" * 60)

def main():
    """Main entry point"""
    runner = SeedRunner()
    success = runner.run_complete_seeding()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()