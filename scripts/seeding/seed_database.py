#!/usr/bin/env python3
"""
Database-level seeding script with enhanced safety and realistic data generation
Consolidates and improves the existing seeding functionality
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import random

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.db.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.employee import Employee
from app.models.device import Device
from app.models.energy_record import EnergyRecord
from app.models.point import Point
from app.models.reward import Reward
from app.models.ranking import Ranking
from app.core.security import get_password_hash

class DatabaseSeeder:
    def __init__(self, company_id: Optional[int] = None):
        self.company_id = company_id
        self.session = None
        
    def __enter__(self):
        # Safety check
        if not os.environ.get('SEED_ALLOW'):
            raise RuntimeError("❌ SEED_ALLOW environment variable not set. Use: export SEED_ALLOW=1")
        
        self.session = SessionLocal()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                self.session.rollback()
                print(f"❌ Transaction rolled back due to error: {exc_val}")
            else:
                self.session.commit()
                print("✅ Transaction committed successfully")
            self.session.close()
    
    def seed_complete_dataset(
        self,
        company_id: int = 1,
        user_count: int = 20,
        months_back: int = 12,
        devices_per_user: int = 2
    ) -> bool:
        """Seed complete realistic dataset"""
        
        try:
            print(f"🌱 Starting complete dataset seeding...")
            print(f"   Company ID: {company_id}")
            print(f"   Users: {user_count}")
            print(f"   Historical months: {months_back}")
            print(f"   Devices per user: {devices_per_user}")
            
            # Verify company exists
            company = self.session.query(Company).filter(Company.id == company_id).first()
            if not company:
                print(f"❌ Company with ID {company_id} not found")
                return False
            
            print(f"✅ Company found: {company.company_name}")
            
            # Generate users and employees
            users = self._create_demo_users(user_count, company_id)
            if not users:
                return False
            
            # Generate devices for each user
            all_devices = []
            for user in users:
                devices = self._create_devices_for_user(user, devices_per_user)
                all_devices.extend(devices)
            
            if not all_devices:
                print("❌ Failed to create devices")
                return False
            
            # Generate realistic energy records
            self._create_energy_records(all_devices, months_back)
            
            # Generate points based on energy savings
            self._create_points_from_energy_records(users, company_id)
            
            # Generate rankings
            self._create_rankings(users, company_id)
            
            # Create sample rewards
            self._create_sample_rewards(company_id)
            
            print(f"✅ Complete dataset seeding successful!")
            print(f"   {len(users)} users created")
            print(f"   {len(all_devices)} devices created")
            print(f"   Energy records for {months_back} months")
            print(f"   Points and rankings generated")
            
            return True
            
        except Exception as e:
            print(f"❌ Seeding error: {e}")
            return False
    
    def _create_demo_users(self, count: int, company_id: int) -> List[User]:
        """Create demo users with employee records"""
        
        print(f"👥 Creating {count} demo users...")
        
        departments = ["営業部", "開発部", "マーケティング部", "人事部", "総務部", "経理部"]
        users = []
        
        for i in range(count):
            # Generate unique email
            email = f"demo.user{i+1:03d}@scope3holdings.co.jp"
            
            # Check if user already exists
            existing = self.session.query(User).filter(User.email == email).first()
            if existing:
                print(f"ℹ️ User already exists: {email}")
                users.append(existing)
                continue
            
            # Create user
            user = User(
                email=email,
                hashed_password=get_password_hash("demo123"),
                full_name=f"デモユーザー{i+1:03d}",
                is_active=True,
                is_superuser=False
            )
            self.session.add(user)
            self.session.flush()  # Get user ID
            
            # Create employee record
            employee = Employee(
                user_id=user.id,
                company_id=company_id,
                department=random.choice(departments),
                employee_code=f"DEMO{i+1:03d}"
            )
            self.session.add(employee)
            
            users.append(user)
            
            if (i + 1) % 10 == 0:
                print(f"   Created {i + 1}/{count} users...")
        
        print(f"✅ Created {len(users)} users")
        return users
    
    def _create_devices_for_user(self, user: User, device_count: int) -> List[Device]:
        """Create devices for a user"""
        
        # Get employee info
        employee = self.session.query(Employee).filter(Employee.user_id == user.id).first()
        location = employee.department if employee else "オフィス"
        
        device_types = [
            ("スマートメーター", "電力"),
            ("ガスメーター", "ガス"),
            ("エアコン", "電力"),
            ("照明システム", "電力"),
            ("ヒーター", "ガス")
        ]
        
        devices = []
        for i in range(device_count):
            device_name, energy_type = random.choice(device_types)
            
            device = Device(
                user_id=user.id,
                device_name=f"{device_name}_{i+1}",
                device_type=device_name,
                location=location,
                energy_type=energy_type,
                is_active=True
            )
            self.session.add(device)
            devices.append(device)
        
        return devices
    
    def _create_energy_records(self, devices: List[Device], months_back: int):
        """Create realistic energy records with seasonality"""
        
        print(f"⚡ Creating energy records for {months_back} months...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        # CO2 conversion factors
        ELECTRICITY_CO2_FACTOR = 0.518  # kg-CO2/kWh
        GAS_CO2_FACTOR = 2.23  # kg-CO2/m³
        
        record_count = 0
        for device in devices:
            current_date = start_date
            
            while current_date <= end_date:
                # Add seasonality (winter higher consumption)
                month = current_date.month
                seasonal_factor = 1.0
                if month in [12, 1, 2]:  # Winter
                    seasonal_factor = 1.4
                elif month in [6, 7, 8]:  # Summer
                    seasonal_factor = 1.2
                
                # Base consumption with some randomness
                if device.energy_type == "電力":
                    base_usage = random.uniform(5, 15) * seasonal_factor
                    unit = "kWh"
                    co2_factor = ELECTRICITY_CO2_FACTOR
                else:  # ガス
                    base_usage = random.uniform(2, 8) * seasonal_factor
                    unit = "m³"
                    co2_factor = GAS_CO2_FACTOR
                
                # Add daily variation
                daily_variation = random.uniform(0.8, 1.2)
                usage = base_usage * daily_variation
                
                # Calculate CO2
                co2_emission = usage * co2_factor
                
                record = EnergyRecord(
                    device_id=device.id,
                    recorded_at=current_date,
                    usage=round(usage, 2),
                    unit=unit,
                    co2_emission=round(co2_emission, 3)
                )
                self.session.add(record)
                record_count += 1
                
                # Move to next day
                current_date += timedelta(days=1)
        
        print(f"✅ Created {record_count} energy records")
    
    def _create_points_from_energy_records(self, users: List[User], company_id: int):
        """Create points based on energy reduction achievements"""
        
        print("🎯 Creating points from energy achievements...")
        
        point_count = 0
        for user in users:
            # Get user's devices
            devices = self.session.query(Device).filter(Device.user_id == user.id).all()
            
            if not devices:
                continue
            
            # Calculate monthly achievements
            for month_offset in range(6):  # Last 6 months
                target_date = datetime.now() - timedelta(days=month_offset * 30)
                
                # Simulate energy reduction achievement
                reduction_percent = random.uniform(5, 25)  # 5-25% reduction
                
                if reduction_percent > 10:  # Award points for >10% reduction
                    points_earned = int(reduction_percent * 10)  # 10 points per percent
                    
                    point = Point(
                        user_id=user.id,
                        company_id=company_id,
                        points=points_earned,
                        reason=f"月間エネルギー削減 {reduction_percent:.1f}% 達成",
                        earned_at=target_date
                    )
                    self.session.add(point)
                    point_count += 1
        
        print(f"✅ Created {point_count} point records")
    
    def _create_rankings(self, users: List[User], company_id: int):
        """Create ranking records"""
        
        print("🏆 Creating rankings...")
        
        # Calculate total points for each user
        user_points = []
        for user in users:
            total_points = self.session.query(Point).filter(
                Point.user_id == user.id
            ).with_entities(Point.points).all()
            
            total = sum(p[0] for p in total_points) if total_points else 0
            user_points.append((user, total))
        
        # Sort by points descending
        user_points.sort(key=lambda x: x[1], reverse=True)
        
        # Create ranking records
        for rank, (user, points) in enumerate(user_points, 1):
            ranking = Ranking(
                user_id=user.id,
                company_id=company_id,
                rank=rank,
                total_points=points,
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now()
            )
            self.session.add(ranking)
        
        print(f"✅ Created rankings for {len(user_points)} users")
    
    def _create_sample_rewards(self, company_id: int):
        """Create sample rewards"""
        
        print("🎁 Creating sample rewards...")
        
        rewards_data = [
            ("エコバッグ", 100, "環境に優しいエコバッグ"),
            ("コーヒー券", 50, "カフェで使えるコーヒー券"),
            ("図書券", 200, "本やマンガが買える図書券"),
            ("植物の苗", 150, "オフィスに飾れる観葉植物"),
            ("リサイクルノート", 75, "再生紙で作られたノート")
        ]
        
        for name, points_required, description in rewards_data:
            # Check if reward already exists
            existing = self.session.query(Reward).filter(
                Reward.company_id == company_id,
                Reward.reward_name == name
            ).first()
            
            if existing:
                continue
            
            reward = Reward(
                company_id=company_id,
                reward_name=name,
                points_required=points_required,
                description=description,
                is_active=True
            )
            self.session.add(reward)
        
        print(f"✅ Created sample rewards")
    
    def clear_demo_data(self, company_id: int, confirm: bool = False) -> bool:
        """Clear demo data for specified company"""
        
        if not confirm:
            print("❌ Clear operation requires explicit confirmation")
            return False
        
        try:
            print(f"🧹 Clearing demo data for company_id: {company_id}")
            
            # Get all demo users (emails starting with demo.)
            demo_users = self.session.query(User).filter(
                User.email.like('demo.%')
            ).all()
            
            if not demo_users:
                print("ℹ️ No demo users found")
                return True
            
            user_ids = [user.id for user in demo_users]
            print(f"Found {len(demo_users)} demo users to remove")
            
            # Delete in proper order (respecting foreign keys)
            # 1. Energy records
            devices = self.session.query(Device).filter(Device.user_id.in_(user_ids)).all()
            device_ids = [d.id for d in devices]
            
            if device_ids:
                energy_count = self.session.query(EnergyRecord).filter(
                    EnergyRecord.device_id.in_(device_ids)
                ).delete(synchronize_session=False)
                print(f"Deleted {energy_count} energy records")
            
            # 2. Devices
            device_count = self.session.query(Device).filter(
                Device.user_id.in_(user_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {device_count} devices")
            
            # 3. Points
            point_count = self.session.query(Point).filter(
                Point.user_id.in_(user_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {point_count} points")
            
            # 4. Rankings
            ranking_count = self.session.query(Ranking).filter(
                Ranking.user_id.in_(user_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {ranking_count} rankings")
            
            # 5. Employees
            employee_count = self.session.query(Employee).filter(
                Employee.user_id.in_(user_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {employee_count} employees")
            
            # 6. Users
            user_count = self.session.query(User).filter(
                User.id.in_(user_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {user_count} users")
            
            print("✅ Demo data cleared successfully")
            return True
            
        except Exception as e:
            print(f"❌ Clear error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Database seeding script with enhanced safety')
    parser.add_argument('--action', choices=['seed', 'clear'], required=True,
                        help='Action to perform')
    parser.add_argument('--company-id', type=int, default=1,
                        help='Company ID to seed data for')
    parser.add_argument('--user-count', type=int, default=20,
                        help='Number of demo users to create')
    parser.add_argument('--months-back', type=int, default=12,
                        help='Months of historical data to generate')
    parser.add_argument('--devices-per-user', type=int, default=2,
                        help='Number of devices per user')
    parser.add_argument('--confirm-clear', action='store_true',
                        help='Confirm data clearing (required for clear action)')
    
    args = parser.parse_args()
    
    # Safety check
    if not os.environ.get('SEED_ALLOW'):
        print("❌ Safety check failed: SEED_ALLOW environment variable not set")
        print("   Use: export SEED_ALLOW=1")
        sys.exit(1)
    
    try:
        with DatabaseSeeder() as seeder:
            if args.action == 'seed':
                success = seeder.seed_complete_dataset(
                    company_id=args.company_id,
                    user_count=args.user_count,
                    months_back=args.months_back,
                    devices_per_user=args.devices_per_user
                )
            else:  # clear
                success = seeder.clear_demo_data(
                    company_id=args.company_id,
                    confirm=args.confirm_clear
                )
            
            if success:
                print(f"\n✅ Database {args.action} operation completed successfully")
                sys.exit(0)
            else:
                print(f"\n❌ Database {args.action} operation failed")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()