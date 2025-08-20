#!/usr/bin/env python3
"""
Production seeding script to be run via GitHub Actions or Kudu
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append('/home/site/wwwroot')

def run_production_seeding():
    """Run seeding in production environment"""
    print(f"🌱 Starting production seeding at {datetime.now()}")
    
    try:
        # Import seeding modules
        from tools.seed.seed_db import seed_database_direct, get_database_metrics
        
        print("📦 Modules imported successfully")
        
        # Run database seeding
        print("🗄️ Running database seeding...")
        success = seed_database_direct()
        
        if success:
            print("✅ Database seeding completed successfully")
            
            # Verify metrics
            print("🔍 Verifying seeded data...")
            metrics = get_database_metrics()
            
            if metrics:
                print("📊 Metrics verification:")
                for key, value in metrics.items():
                    print(f"   {key}: {value}")
            
            return True
        else:
            print("❌ Database seeding failed")
            return False
            
    except Exception as e:
        print(f"❌ Production seeding error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_production_seeding()
    sys.exit(0 if success else 1)