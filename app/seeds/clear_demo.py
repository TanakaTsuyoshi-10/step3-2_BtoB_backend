#!/usr/bin/env python3
"""
Demo data cleanup script for BtoB Energy Management System

This script safely removes dummy data created by seed_demo.py
Only removes data associated with the specified company codes

Safety: Requires SEED_ALLOW=1 environment variable to execute
"""

import argparse
import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

# App imports
sys.path.append('/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend')
from app.db.database import SessionLocal

# Company mapping
COMPANIES = {
    'SCOPE3_HOLDINGS': 1,
    'TECH0_INC': 2
}

def print_log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def check_seed_permission():
    """Check if seeding is allowed via SEED_ALLOW environment variable"""
    if os.getenv('SEED_ALLOW') != '1':
        print_log("❌ SEED_ALLOW=1 not set. Data clearing is not permitted.", "ERROR")
        print_log("For safety, set SEED_ALLOW=1 in your environment before running this script.", "ERROR")
        sys.exit(1)
    print_log("✅ SEED_ALLOW=1 confirmed. Proceeding with data cleanup.")

def get_deletion_counts(db: Session, company_id: int) -> dict:
    """Get counts of records that will be deleted for a company"""
    counts = {}
    
    # Count redemptions
    result = db.execute(text("""
        SELECT COUNT(*) FROM redemptions r 
        JOIN employees e ON r.user_id = e.user_id 
        WHERE e.company_id = :company_id
    """), {"company_id": company_id}).fetchone()
    counts['redemptions'] = result[0] if result else 0
    
    # Count points ledger
    result = db.execute(text("""
        SELECT COUNT(*) FROM points_ledger pl 
        JOIN employees e ON pl.user_id = e.user_id 
        WHERE e.company_id = :company_id
    """), {"company_id": company_id}).fetchone()
    counts['points_ledger'] = result[0] if result else 0
    
    # Count reduction records
    result = db.execute(text("""
        SELECT COUNT(*) FROM reduction_records rr 
        JOIN employees e ON rr.user_id = e.user_id 
        WHERE e.company_id = :company_id
    """), {"company_id": company_id}).fetchone()
    counts['reduction_records'] = result[0] if result else 0
    
    # Count devices
    result = db.execute(text("""
        SELECT COUNT(*) FROM devices d 
        JOIN employees e ON d.owner_id = e.user_id 
        WHERE e.company_id = :company_id
    """), {"company_id": company_id}).fetchone()
    counts['devices'] = result[0] if result else 0
    
    # Count users
    result = db.execute(text("""
        SELECT COUNT(*) FROM users u 
        JOIN employees e ON u.id = e.user_id 
        WHERE e.company_id = :company_id
    """), {"company_id": company_id}).fetchone()
    counts['users'] = result[0] if result else 0
    
    # Count employees
    result = db.execute(text("""
        SELECT COUNT(*) FROM employees 
        WHERE company_id = :company_id
    """), {"company_id": company_id}).fetchone()
    counts['employees'] = result[0] if result else 0
    
    return counts

def clear_company_data(db: Session, company_code: str, dry_run: bool = False) -> dict:
    """Clear data for a single company"""
    
    company_id = COMPANIES[company_code]
    print_log(f"🧹 {'[DRY RUN] ' if dry_run else ''}Clearing data for {company_code} (ID: {company_id})")
    
    # Get counts before deletion
    counts = get_deletion_counts(db, company_id)
    
    if all(count == 0 for count in counts.values()):
        print_log(f"ℹ️ No data found for {company_code}")
        return counts
    
    print_log(f"📊 Found data to delete:")
    for table, count in counts.items():
        if count > 0:
            print_log(f"   {table}: {count} records")
    
    if dry_run:
        print_log(f"🔍 DRY RUN: Would delete {sum(counts.values())} total records")
        return counts
    
    try:
        # Delete in correct order to respect foreign key constraints
        print_log("🗑️ Deleting redemptions...")
        result = db.execute(text("""
            DELETE r FROM redemptions r 
            JOIN employees e ON r.user_id = e.user_id 
            WHERE e.company_id = :company_id
        """), {"company_id": company_id})
        print_log(f"   Deleted {result.rowcount} redemptions")
        
        print_log("🗑️ Deleting points ledger...")
        result = db.execute(text("""
            DELETE pl FROM points_ledger pl 
            JOIN employees e ON pl.user_id = e.user_id 
            WHERE e.company_id = :company_id
        """), {"company_id": company_id})
        print_log(f"   Deleted {result.rowcount} points ledger entries")
        
        print_log("🗑️ Deleting reduction records...")
        result = db.execute(text("""
            DELETE rr FROM reduction_records rr 
            JOIN employees e ON rr.user_id = e.user_id 
            WHERE e.company_id = :company_id
        """), {"company_id": company_id})
        print_log(f"   Deleted {result.rowcount} reduction records")
        
        print_log("🗑️ Deleting devices...")
        result = db.execute(text("""
            DELETE d FROM devices d 
            JOIN employees e ON d.owner_id = e.user_id 
            WHERE e.company_id = :company_id
        """), {"company_id": company_id})
        print_log(f"   Deleted {result.rowcount} devices")
        
        print_log("🗑️ Deleting users...")
        result = db.execute(text("""
            DELETE u FROM users u 
            JOIN employees e ON u.id = e.user_id 
            WHERE e.company_id = :company_id
        """), {"company_id": company_id})
        print_log(f"   Deleted {result.rowcount} users")
        
        print_log("🗑️ Deleting employees...")
        result = db.execute(text("""
            DELETE FROM employees 
            WHERE company_id = :company_id
        """), {"company_id": company_id})
        print_log(f"   Deleted {result.rowcount} employees")
        
        print_log(f"✅ Successfully cleared data for {company_code}")
        return counts
        
    except Exception as e:
        print_log(f"❌ Error clearing {company_code}: {e}", "ERROR")
        db.rollback()
        raise

def clear_global_rewards(db: Session, dry_run: bool = False) -> int:
    """Clear rewards that are not company-specific"""
    
    print_log(f"🎁 {'[DRY RUN] ' if dry_run else ''}Clearing global rewards...")
    
    # Get count of rewards
    result = db.execute(text("SELECT COUNT(*) FROM rewards")).fetchone()
    reward_count = result[0] if result else 0
    
    if reward_count == 0:
        print_log("ℹ️ No rewards found")
        return 0
    
    print_log(f"📊 Found {reward_count} rewards to delete")
    
    if dry_run:
        print_log(f"🔍 DRY RUN: Would delete {reward_count} rewards")
        return reward_count
    
    try:
        result = db.execute(text("DELETE FROM rewards"))
        print_log(f"✅ Deleted {result.rowcount} rewards")
        return result.rowcount
        
    except Exception as e:
        print_log(f"❌ Error clearing rewards: {e}", "ERROR")
        db.rollback()
        raise

def main():
    parser = argparse.ArgumentParser(description="Clear demo data from BtoB Energy Management System")
    parser.add_argument("--company-codes", default="SCOPE3_HOLDINGS,TECH0_INC",
                       help="Comma-separated company codes to clear")
    parser.add_argument("--include-rewards", action="store_true",
                       help="Also clear global rewards")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be deleted without actually deleting")
    
    args = parser.parse_args()
    
    # Safety check
    check_seed_permission()
    
    # Parse company codes
    company_codes = [code.strip() for code in args.company_codes.split(",")]
    print_log(f"🎯 Target companies: {company_codes}")
    
    # Validate company codes
    for code in company_codes:
        if code not in COMPANIES:
            print_log(f"❌ Unknown company code: {code}", "ERROR")
            sys.exit(1)
    
    # Confirmation
    if not args.dry_run:
        print_log("⚠️ WARNING: This will permanently delete demo data!")
        response = input("Are you sure you want to continue? Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print_log("❌ Operation cancelled")
            sys.exit(0)
    
    # Start cleanup process
    start_time = datetime.now()
    print_log(f"🧹 {'[DRY RUN] ' if args.dry_run else ''}Starting cleanup process...")
    
    total_deleted = 0
    
    db = SessionLocal()
    try:
        # Clear each company
        for company_code in company_codes:
            counts = clear_company_data(db, company_code, args.dry_run)
            total_deleted += sum(counts.values())
        
        # Clear rewards if requested
        if args.include_rewards:
            reward_count = clear_global_rewards(db, args.dry_run)
            total_deleted += reward_count
        
        # Commit changes
        if not args.dry_run:
            db.commit()
        
        # Calculate timing
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print summary
        print_log("=" * 60)
        if args.dry_run:
            print_log("🔍 DRY RUN COMPLETED")
            print_log(f"Would delete {total_deleted} total records")
        else:
            print_log("🎉 CLEANUP COMPLETED SUCCESSFULLY!")
            print_log(f"Deleted {total_deleted} total records")
        print_log(f"Duration: {duration.total_seconds():.1f} seconds")
        print_log("=" * 60)
            
    except Exception as e:
        print_log(f"❌ Cleanup failed: {e}", "ERROR")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()