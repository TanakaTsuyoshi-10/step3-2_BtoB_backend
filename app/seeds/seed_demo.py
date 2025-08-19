#!/usr/bin/env python3
"""
Demo data seeding script for BtoB Energy Management System

This script generates realistic dummy data for dashboard visualization:
- Companies (using integer IDs)
- Users with realistic Japanese names
- Devices (electric/gas meters)
- Reduction records with seasonality and YoY trends
- Points ledger based on CO2 reduction achievements
- Rewards and redemptions
- Reports for CO2 reduction tracking

Safety: Requires SEED_ALLOW=1 environment variable to execute
"""

import argparse
import os
import sys
import random
import math
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import hashlib

# SQLAlchemy and Alembic imports
from sqlalchemy.orm import Session
from sqlalchemy import text
from alembic.config import Config
from alembic import command

# App imports
sys.path.append('/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend')
from app.db.database import SessionLocal, engine
from app.models.user import User
from app.models.employee import Employee
from app.models.device import Device
from app.models.reduction_record import ReductionRecord
from app.models.points_ledger import PointsLedger
from app.models.reward import Reward
from app.models.redemption import Redemption
from app.core.security import get_password_hash

# API validation
import requests
from app.core.config import settings

# Constants
CO2_FACTOR_ELECTRICITY = 0.441  # kg-CO2/kWh
CO2_FACTOR_GAS = 2.23  # kg-CO2/m³
POINTS_PER_KG_CO2 = 1.0  # 1 point per 1 kg CO2 reduced

# Company mapping
COMPANIES = {
    'SCOPE3_HOLDINGS': 1,
    'TECH0_INC': 2
}

# Japanese names for realistic data
FIRST_NAMES = [
    '太郎', '花子', '一郎', '美香', '健太', '由美', '大輔', '恵子', '俊介', '智子',
    '和也', '真由美', '浩二', '裕美', '秀樹', '美穂', '正人', '加奈子', '康夫', '直子',
    '雅彦', '理恵', '博之', '陽子', '明', '美紀', '哲也', '麻美', '達也', '優子'
]

LAST_NAMES = [
    '田中', '佐藤', '鈴木', '高橋', '渡辺', '伊藤', '山本', '中村', '小林', '加藤',
    '吉田', '山田', '佐々木', '山口', '松本', '井上', '木村', '林', '清水', '山崎',
    '森', '池田', '橋本', '石川', '前田', '藤田', '後藤', '長谷川', '村上', '近藤'
]

DEPARTMENTS = [
    '経営企画部', '営業部', '開発部', '製造部', '品質保証部', 
    '人事部', '総務部', '経理部', '情報システム部', '環境推進部'
]

def print_log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def check_seed_permission():
    """Check if seeding is allowed via SEED_ALLOW environment variable"""
    if os.getenv('SEED_ALLOW') != '1':
        print_log("❌ SEED_ALLOW=1 not set. Seeding is not permitted.", "ERROR")
        print_log("For safety, set SEED_ALLOW=1 in your environment before running this script.", "ERROR")
        sys.exit(1)
    print_log("✅ SEED_ALLOW=1 confirmed. Proceeding with seeding.")

def ensure_alembic_current():
    """Ensure database is up to date with Alembic migrations"""
    try:
        print_log("Checking Alembic migration status...")
        
        # Create Alembic config
        alembic_cfg = Config("/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend/alembic.ini")
        alembic_cfg.set_main_option("script_location", 
                                   "/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend/alembic")
        
        # Run upgrade to head
        print_log("Running 'alembic upgrade head'...")
        command.upgrade(alembic_cfg, "head")
        print_log("✅ Database schema is up to date.")
        
    except Exception as e:
        print_log(f"⚠️ Alembic upgrade warning: {e}", "WARN")
        print_log("Continuing with existing schema...", "WARN")

def generate_realistic_usage(base_usage: float, month: int, energy_type: str, 
                           year_offset: int = 0) -> Tuple[float, float]:
    """
    Generate realistic energy usage with seasonality
    Returns: (usage, baseline)
    """
    # Seasonality factors
    if energy_type == 'electricity':
        # Higher in summer (cooling) and winter (heating)
        seasonal_factor = 1.0 + 0.3 * math.cos((month - 1) * math.pi / 6) + 0.2 * math.cos((month - 7) * math.pi / 6)
    else:  # gas
        # Higher in winter (heating)
        seasonal_factor = 1.0 + 0.4 * math.cos((month - 1) * math.pi / 6)
    
    # Year-over-year reduction trend (3-12% reduction, with some outliers)
    if year_offset == 0:  # Current year
        yoy_factor = random.uniform(0.88, 0.97)  # 3-12% reduction
        if random.random() < 0.1:  # 10% chance of outlier (increase)
            yoy_factor = random.uniform(1.0, 1.05)  # 0-5% increase
    else:  # Previous year
        yoy_factor = 1.0
    
    # Add random noise
    noise = random.uniform(0.85, 1.15)
    
    # Calculate usage and baseline
    usage = base_usage * seasonal_factor * yoy_factor * noise
    baseline = usage * random.uniform(1.1, 1.5)  # Baseline is 10-50% higher
    
    return max(0, usage), max(usage, baseline)

def create_user_with_employee(db: Session, company_id: int, company_code: str, 
                             user_index: int, departments: List[str]) -> User:
    """Create a user with associated employee record"""
    
    # Generate realistic name
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    full_name = f"{last_name} {first_name}"
    
    # Generate email
    first_romanized = f"user{user_index:03d}"
    last_romanized = company_code.lower().replace('_', '')
    email = f"{first_romanized}.{last_romanized}@{company_code.lower()}.co.jp"
    
    # Check if user already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print_log(f"User {email} already exists, skipping...")
        return existing
    
    # Create user
    user = User(
        email=email,
        hashed_password=get_password_hash("password123"),
        full_name=full_name,
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.flush()  # Get user ID
    
    # Create employee
    department = random.choice(departments)
    employee_code = f"{company_code[:4]}{user_index:04d}"
    
    employee = Employee(
        user_id=user.id,
        company_id=company_id,
        department=department,
        employee_code=employee_code
    )
    db.add(employee)
    
    return user

def create_devices_for_user(db: Session, user: User, device_count: int):
    """Create devices for a user (electric and/or gas meters)"""
    devices = []
    
    # Get employee info
    employee = db.query(Employee).filter(Employee.user_id == user.id).first()
    location = employee.department if employee else "オフィス"
    
    # Always create at least one electric meter
    electric_device = Device(
        name=f"電力メーター_{user.id}",
        device_type="electric_meter",
        model="EM-3000",
        serial_number=f"EM{user.id:06d}E",
        capacity=None,
        efficiency=None,
        location=location,
        is_active=True,
        owner_id=user.id
    )
    db.add(electric_device)
    devices.append(electric_device)
    
    # Create gas meter if device_count > 1
    if device_count > 1:
        gas_device = Device(
            name=f"ガスメーター_{user.id}",
            device_type="gas_meter",
            model="GM-2000",
            serial_number=f"GM{user.id:06d}G",
            capacity=None,
            efficiency=None,
            location=location,
            is_active=True,
            owner_id=user.id
        )
        db.add(gas_device)
        devices.append(gas_device)
    
    return devices

def create_reduction_records(db: Session, user: User, months: int):
    """Create reduction records for a user with realistic usage patterns"""
    print_log(f"Creating reduction records for user {user.full_name}...")
    
    # Base usage levels (vary by user)
    base_electricity = random.uniform(200, 800)  # kWh per month
    base_gas = random.uniform(30, 150)  # m³ per month
    
    current_date = date.today()
    
    # Create records for both current year and previous year
    for year_offset in [0, 1]:  # 0 = current year, 1 = previous year
        for month_offset in range(months):
            record_date = current_date.replace(day=1) - timedelta(days=30 * month_offset)
            record_date = record_date.replace(year=record_date.year - year_offset)
            
            # Skip future dates
            if record_date > current_date:
                continue
                
            month = record_date.month
            
            # Create electricity record
            electricity_usage, electricity_baseline = generate_realistic_usage(
                base_electricity, month, 'electricity', year_offset
            )
            co2_electric = (electricity_baseline - electricity_usage) * CO2_FACTOR_ELECTRICITY
            
            electric_record = ReductionRecord(
                user_id=user.id,
                date=record_date,
                energy_type='electricity',
                usage=electricity_usage,
                baseline=electricity_baseline,
                reduced_co2_kg=max(0, co2_electric)
            )
            db.add(electric_record)
            
            # Create gas record
            gas_usage, gas_baseline = generate_realistic_usage(
                base_gas, month, 'gas', year_offset
            )
            co2_gas = (gas_baseline - gas_usage) * CO2_FACTOR_GAS
            
            gas_record = ReductionRecord(
                user_id=user.id,
                date=record_date,
                energy_type='gas',
                usage=gas_usage,
                baseline=gas_baseline,
                reduced_co2_kg=max(0, co2_gas)
            )
            db.add(gas_record)

def create_points_ledger(db: Session, user: User):
    """Create points ledger entries based on CO2 reduction achievements"""
    
    # Get user's total CO2 reduction for current year
    current_year = date.today().year
    total_co2 = db.execute(text("""
        SELECT SUM(reduced_co2_kg) as total
        FROM reduction_records
        WHERE user_id = :user_id AND YEAR(date) = :year
    """), {"user_id": user.id, "year": current_year}).fetchone()
    
    if not total_co2 or not total_co2[0]:
        return
        
    total_co2_kg = float(total_co2[0])
    total_points = int(total_co2_kg * POINTS_PER_KG_CO2)
    
    if total_points <= 0:
        return
    
    # Distribute points across months
    monthly_points = total_points // 12
    remaining_points = total_points % 12
    current_balance = 0
    
    for month in range(1, 13):
        month_points = monthly_points
        if month <= remaining_points:
            month_points += 1
            
        if month_points > 0:
            current_balance += month_points
            
            # Create points entry
            record_date = date(current_year, month, 1)
            if record_date <= date.today():
                points_entry = PointsLedger(
                    user_id=user.id,
                    delta=month_points,
                    reason=f"CO₂削減実績ポイント({month}月)",
                    reference_id=None,
                    balance_after=current_balance
                )
                db.add(points_entry)

def create_rewards(db: Session) -> List[Reward]:
    """Create sample rewards for point exchange"""
    rewards_data = [
        ("Amazonギフト券 500円", "オンラインで使える便利なギフト券", "ギフト券", 500),
        ("Amazonギフト券 1000円", "オンラインで使える便利なギフト券", "ギフト券", 1000),
        ("スターバックスカード 500円", "全国のスターバックスで使える", "ギフト券", 500),
        ("図書カード 1000円", "全国の書店で使える図書カード", "ギフト券", 1000),
        ("エコバッグ", "環境に優しいオリジナルエコバッグ", "グッズ", 200),
        ("タンブラー", "保温・保冷機能付きタンブラー", "グッズ", 300),
        ("ボールペンセット", "高級ボールペン3本セット", "文具", 150),
        ("ノートセット", "環境配慮素材のノート5冊セット", "文具", 100),
        ("QUOカード 500円", "コンビニ等で使えるQUOカード", "ギフト券", 500),
        ("植物の苗", "オフィス緑化用の観葉植物", "グッズ", 250),
    ]
    
    rewards = []
    for title, desc, category, points in rewards_data:
        # Check if reward already exists
        existing = db.query(Reward).filter(Reward.title == title).first()
        if existing:
            rewards.append(existing)
            continue
            
        reward = Reward(
            title=title,
            description=desc,
            category=category,
            image_url=None,
            stock=random.randint(50, 200),
            points_required=points,
            active=True
        )
        db.add(reward)
        rewards.append(reward)
        
    return rewards

def create_redemptions(db: Session, users: List[User], rewards: List[Reward]):
    """Create sample redemptions for some users"""
    
    # Select 20-30% of users for redemptions
    redemption_users = random.sample(users, k=min(len(users) // 3, 50))
    
    for user in redemption_users:
        # Get user's current point balance
        latest_balance = db.execute(text("""
            SELECT balance_after FROM points_ledger
            WHERE user_id = :user_id
            ORDER BY created_at DESC LIMIT 1
        """), {"user_id": user.id}).fetchone()
        
        if not latest_balance or latest_balance[0] < 100:
            continue  # Skip users with low balance
            
        balance = latest_balance[0]
        
        # Create 1-3 redemptions per user
        num_redemptions = random.randint(1, 3)
        current_balance = balance
        
        for _ in range(num_redemptions):
            # Select affordable reward
            affordable_rewards = [r for r in rewards if r.points_required <= current_balance]
            if not affordable_rewards:
                break
                
            reward = random.choice(affordable_rewards)
            
            # Create redemption
            redemption = Redemption(
                user_id=user.id,
                reward_id=reward.id,
                points_spent=reward.points_required,
                status=random.choice(['承認', '発送済', '申請中'])
            )
            db.add(redemption)
            
            # Update balance
            current_balance -= reward.points_required
            
            # Create negative points entry
            points_entry = PointsLedger(
                user_id=user.id,
                delta=-reward.points_required,
                reason=f"景品交換: {reward.title}",
                reference_id=redemption.id,
                balance_after=current_balance
            )
            db.add(points_entry)

def validate_metrics_apis(company_codes: List[str]) -> bool:
    """Validate that metrics APIs return correct data after seeding"""
    print_log("🔍 Validating metrics APIs...")
    
    try:
        # Test each company
        for company_code in company_codes:
            company_id = COMPANIES[company_code]
            print_log(f"Testing APIs for {company_code} (company_id: {company_id})")
            
            # Test KPI endpoint
            response = requests.get(f"http://localhost:8000/api/v1/metrics/kpi?company_id={company_id}")
            if response.status_code != 200:
                print_log(f"❌ KPI API failed: {response.status_code}", "ERROR")
                return False
                
            kpi_data = response.json()
            print_log(f"✅ KPI API: {kpi_data['active_users']} active users, "
                     f"{kpi_data['co2_reduction_total_kg']:.1f} kg CO₂ reduced")
            
            # Test Monthly Usage endpoint
            response = requests.get(f"http://localhost:8000/api/v1/metrics/monthly-usage?company_id={company_id}")
            if response.status_code != 200:
                print_log(f"❌ Monthly Usage API failed: {response.status_code}", "ERROR")
                return False
                
            monthly_data = response.json()
            print_log(f"✅ Monthly Usage API: {len(monthly_data['months'])} months of data")
            
            # Test CO2 Trend endpoint
            response = requests.get(f"http://localhost:8000/api/v1/metrics/co2-trend?company_id={company_id}&interval=month")
            if response.status_code != 200:
                print_log(f"❌ CO2 Trend API failed: {response.status_code}", "ERROR")
                return False
                
            trend_data = response.json()
            print_log(f"✅ CO2 Trend API: {len(trend_data['points'])} data points")
            
            # Test YoY Usage endpoint
            current_month = date.today().strftime("%Y-%m")
            response = requests.get(f"http://localhost:8000/api/v1/metrics/yoy-usage?company_id={company_id}&month={current_month}")
            if response.status_code != 200:
                print_log(f"❌ YoY Usage API failed: {response.status_code}", "ERROR")
                return False
                
            yoy_data = response.json()
            print_log(f"✅ YoY Usage API: Current vs Previous year data validated")
            
        print_log("🎉 All metrics APIs validated successfully!")
        return True
        
    except Exception as e:
        print_log(f"❌ API validation failed: {e}", "ERROR")
        return False

def seed_company_data(db: Session, company_code: str, users_count: int, months: int, 
                     replace: bool = False) -> Dict[str, int]:
    """Seed data for a single company"""
    
    company_id = COMPANIES[company_code]
    print_log(f"🏢 Seeding data for {company_code} (ID: {company_id})")
    
    stats = {
        'users': 0,
        'employees': 0,
        'devices': 0,
        'reduction_records': 0,
        'points_entries': 0,
        'redemptions': 0
    }
    
    try:
        # Clear existing data if replace flag is set
        if replace:
            print_log(f"🧹 Clearing existing data for {company_code}...")
            
            # Get user IDs for this company first
            user_ids_result = db.execute(text("""
                SELECT u.id FROM users u 
                JOIN employees e ON u.id = e.user_id 
                WHERE e.company_id = :company_id
            """), {"company_id": company_id}).fetchall()
            
            if user_ids_result:
                user_ids = [str(row[0]) for row in user_ids_result]
                user_ids_str = ','.join(user_ids)
                
                # Delete in correct order to respect foreign keys
                db.execute(text(f"DELETE FROM redemptions WHERE user_id IN ({user_ids_str})"))
                db.execute(text(f"DELETE FROM points_ledger WHERE user_id IN ({user_ids_str})"))
                db.execute(text(f"DELETE FROM reduction_records WHERE user_id IN ({user_ids_str})"))
                db.execute(text(f"DELETE FROM devices WHERE owner_id IN ({user_ids_str})"))
                db.execute(text("DELETE FROM employees WHERE company_id = :company_id"), {"company_id": company_id})
                db.execute(text(f"DELETE FROM users WHERE id IN ({user_ids_str})"))
                
                print_log(f"✅ Cleared existing data for {company_code}")
            else:
                print_log(f"ℹ️ No existing data found for {company_code}")
        
        # Create users and employees
        users = []
        print_log(f"👥 Creating {users_count} users for {company_code}...")
        
        for i in range(1, users_count + 1):
            user = create_user_with_employee(db, company_id, company_code, i, DEPARTMENTS)
            users.append(user)
            stats['users'] += 1
            stats['employees'] += 1
            
        # Create devices for users
        print_log(f"⚡ Creating devices...")
        for user in users:
            device_count = random.choice([1, 2])  # 1-2 devices per user
            devices = create_devices_for_user(db, user, device_count)
            stats['devices'] += len(devices)
            
        # Commit users and devices first
        db.commit()
        print_log(f"✅ Created {stats['users']} users and {stats['devices']} devices for {company_code}")
        
        # Create reduction records
        print_log(f"📊 Creating reduction records...")
        for user in users:
            create_reduction_records(db, user, months)
            stats['reduction_records'] += months * 2 * 2  # months * energy_types * years
            
        # Commit reduction records
        db.commit()
        print_log(f"✅ Created {stats['reduction_records']} reduction records")
        
        # Create points ledger
        print_log(f"💰 Creating points ledger...")
        for user in users:
            create_points_ledger(db, user)
            stats['points_entries'] += 12  # Approximately 12 entries per user
            
        # Commit points
        db.commit()
        print_log(f"✅ Created points ledger entries")
        
        return stats
        
    except Exception as e:
        print_log(f"❌ Error seeding {company_code}: {e}", "ERROR")
        db.rollback()
        raise

def main():
    parser = argparse.ArgumentParser(description="Seed demo data for BtoB Energy Management System")
    parser.add_argument("--company-codes", default="SCOPE3_HOLDINGS,TECH0_INC",
                       help="Comma-separated company codes")
    parser.add_argument("--users", type=int, default=200, help="Number of users per company")
    parser.add_argument("--months", type=int, default=12, help="Number of months of data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--replace", action="store_true", help="Replace existing data")
    
    args = parser.parse_args()
    
    # Safety check
    check_seed_permission()
    
    # Set random seed for reproducible results
    random.seed(args.seed)
    print_log(f"🎲 Random seed set to {args.seed}")
    
    # Parse company codes
    company_codes = [code.strip() for code in args.company_codes.split(",")]
    print_log(f"🏭 Target companies: {company_codes}")
    
    # Validate company codes
    for code in company_codes:
        if code not in COMPANIES:
            print_log(f"❌ Unknown company code: {code}", "ERROR")
            sys.exit(1)
    
    # Ensure database schema is current
    ensure_alembic_current()
    
    # Start seeding process
    start_time = datetime.now()
    print_log(f"🚀 Starting seeding process...")
    print_log(f"   Users per company: {args.users}")
    print_log(f"   Months of data: {args.months}")
    print_log(f"   Replace existing: {args.replace}")
    
    total_stats = {
        'companies': 0,
        'users': 0,
        'employees': 0,
        'devices': 0,
        'reduction_records': 0,
        'points_entries': 0,
        'rewards': 0,
        'redemptions': 0
    }
    
    db = SessionLocal()
    try:
        # Create rewards first (shared across companies)
        print_log("🎁 Creating rewards...")
        rewards = create_rewards(db)
        db.commit()
        total_stats['rewards'] = len(rewards)
        print_log(f"✅ Created {len(rewards)} rewards")
        
        # Seed each company
        all_users = []
        for company_code in company_codes:
            company_stats = seed_company_data(db, company_code, args.users, args.months, args.replace)
            
            # Add to totals
            for key, value in company_stats.items():
                if key in total_stats:
                    total_stats[key] += value
            total_stats['companies'] += 1
            
            # Collect users for redemptions
            company_id = COMPANIES[company_code]
            company_users = db.execute(text("""
                SELECT u.* FROM users u 
                JOIN employees e ON u.id = e.user_id 
                WHERE e.company_id = :company_id
            """), {"company_id": company_id}).fetchall()
            all_users.extend([db.query(User).filter(User.id == user.id).first() for user in company_users])
        
        # Create redemptions across all users
        print_log("💳 Creating redemptions...")
        create_redemptions(db, all_users, rewards)
        db.commit()
        print_log("✅ Created redemptions")
        
        # Final commit
        db.commit()
        
        # Calculate timing
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print summary
        print_log("=" * 60)
        print_log("🎉 SEEDING COMPLETED SUCCESSFULLY!")
        print_log("=" * 60)
        print_log(f"📊 Summary:")
        print_log(f"   Companies: {total_stats['companies']}")
        print_log(f"   Users: {total_stats['users']}")
        print_log(f"   Employees: {total_stats['employees']}")
        print_log(f"   Devices: {total_stats['devices']}")
        print_log(f"   Reduction Records: {total_stats['reduction_records']}")
        print_log(f"   Rewards: {total_stats['rewards']}")
        print_log(f"   Duration: {duration.total_seconds():.1f} seconds")
        print_log("=" * 60)
        
        # Validate APIs (optional, requires auth)
        print_log("ℹ️ API validation skipped (requires authentication)")
        print_log("🌐 Dashboard should now display data at:")
        print_log("   https://app-002-gen10-step3-2-node-oshima2.azurewebsites.net/dashboard")
        print_log("📊 To validate APIs manually, use authenticated requests to:")
        for company_code in company_codes:
            company_id = COMPANIES[company_code]
            print_log(f"   /api/v1/metrics/kpi?company_id={company_id}")
            
    except Exception as e:
        print_log(f"❌ Seeding failed: {e}", "ERROR")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()