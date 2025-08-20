#!/usr/bin/env python3
"""
Database direct seeding for energy, device, and point data
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
try:
    from .seed_config import config
except ImportError:
    from seed_config import config

class DatabaseSeeder:
    """Direct database seeding operations"""
    
    def __init__(self):
        self.session = SessionLocal()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
            print(f"❌ Transaction rolled back due to error: {exc_val}")
        else:
            self.session.commit()
            print("✅ Database transaction committed")
        self.session.close()
    
    def ensure_company_exists(self) -> bool:
        """Ensure target company exists"""
        company = self.session.query(Company).filter(Company.id == config.company_id).first()
        
        if not company:
            # Create company if it doesn't exist
            company = Company(
                id=config.company_id,
                company_name=config.company_name,
                industry="エネルギーマネジメント",
                address="東京都渋谷区"
            )
            self.session.add(company)
            self.session.flush()
            print(f"✅ Created company: {config.company_name}")
        else:
            print(f"✅ Company exists: {company.company_name}")
        
        return True
    
    def create_employee_records(self, users_data: List[Dict[str, Any]]) -> int:
        """Create employee records for existing users"""
        print("👥 Creating employee records...")
        
        created_count = 0
        
        for user_data in users_data:
            # Find user by email
            user = self.session.query(User).filter(User.email == user_data['email']).first()
            
            if not user:
                # Create user if not exists (fallback)
                user = User(
                    email=user_data['email'],
                    hashed_password=get_password_hash(user_data['password']),
                    full_name=user_data['full_name'],
                    is_active=user_data['is_active'],
                    is_superuser=False
                )
                self.session.add(user)
                self.session.flush()
                print(f"✅ Created user: {user_data['email']}")
            
            # Check if employee record exists
            employee = self.session.query(Employee).filter(Employee.user_id == user.id).first()
            
            if not employee:
                employee = Employee(
                    user_id=user.id,
                    company_id=config.company_id,
                    department=user_data['department'],
                    employee_code=user_data['employee_code']
                )
                self.session.add(employee)
                created_count += 1
                print(f"✅ Created employee: {user_data['employee_code']}")
        
        print(f"✅ Created {created_count} employee records")
        return created_count
    
    def create_devices_for_users(self) -> int:
        """Create devices for all company employees"""
        print("📱 Creating devices for users...")
        
        # Get all employees in the company
        employees = self.session.query(Employee).filter(
            Employee.company_id == config.company_id
        ).all()
        
        if not employees:
            print("❌ No employees found for device creation")
            return 0
        
        device_types = config.get_device_types()
        created_count = 0
        
        for employee in employees:
            user = self.session.query(User).filter(User.id == employee.user_id).first()
            if not user:
                continue
            
            # Create 2-3 devices per user
            devices_per_user = random.randint(2, 3)
            
            for i in range(devices_per_user):
                device_name, energy_type = random.choice(device_types)
                
                # Check if device already exists
                existing_device = self.session.query(Device).filter(
                    Device.user_id == user.id,
                    Device.device_name == f"{device_name}_{i+1}"
                ).first()
                
                if not existing_device:
                    device = Device(
                        user_id=user.id,
                        device_name=f"{device_name}_{i+1}",
                        device_type=device_name,
                        location=employee.department,
                        energy_type=energy_type,
                        is_active=True
                    )
                    self.session.add(device)
                    created_count += 1
        
        print(f"✅ Created {created_count} devices")
        return created_count
    
    def create_energy_records(self) -> int:
        """Create energy usage records for last 12 months"""
        print("⚡ Creating energy records...")
        
        # Get all active devices
        devices = self.session.query(Device).join(Employee).filter(
            Employee.company_id == config.company_id,
            Device.is_active == True
        ).all()
        
        if not devices:
            print("❌ No devices found for energy record creation")
            return 0
        
        electricity_data = config.get_monthly_electricity_data()
        gas_data = config.get_monthly_gas_data()
        co2_data = config.get_monthly_co2_data()
        
        # Previous year data for YoY comparison
        prev_year_data = config.get_previous_year_data()
        
        created_count = 0
        
        # Create records for current year (last 12 months)
        for month_offset in range(12):
            target_date = config.current_date - timedelta(days=month_offset * 30)
            target_year = target_date.year
            target_month = target_date.month
            
            # Use first day of month for consistency
            record_date = datetime(target_year, target_month, 1)
            
            month_index = (target_month - 1) % 12
            
            # Distribute total monthly usage across devices
            total_electricity = electricity_data[month_index]
            total_gas = gas_data[month_index]
            total_co2 = co2_data[month_index]
            
            electricity_devices = [d for d in devices if d.energy_type == "電力"]
            gas_devices = [d for d in devices if d.energy_type == "ガス"]
            
            # Create electricity records
            if electricity_devices:
                usage_per_device = total_electricity / len(electricity_devices)
                co2_per_device = total_co2 / len(electricity_devices)
                
                for device in electricity_devices:
                    # Check if record already exists
                    existing = self.session.query(EnergyRecord).filter(
                        EnergyRecord.device_id == device.id,
                        EnergyRecord.recorded_at == record_date
                    ).first()
                    
                    if not existing:
                        # Add some variation
                        variation = random.uniform(0.8, 1.2)
                        actual_usage = usage_per_device * variation
                        actual_co2 = co2_per_device * variation
                        
                        record = EnergyRecord(
                            device_id=device.id,
                            recorded_at=record_date,
                            usage=round(actual_usage, 2),
                            unit="kWh",
                            co2_emission=round(actual_co2, 3)
                        )
                        self.session.add(record)
                        created_count += 1
            
            # Create gas records
            if gas_devices:
                usage_per_device = total_gas / len(gas_devices)
                
                for device in gas_devices:
                    existing = self.session.query(EnergyRecord).filter(
                        EnergyRecord.device_id == device.id,
                        EnergyRecord.recorded_at == record_date
                    ).first()
                    
                    if not existing:
                        variation = random.uniform(0.8, 1.2)
                        actual_usage = usage_per_device * variation
                        
                        # CO2 factor for gas: 2.23 kg-CO2/m³
                        actual_co2 = actual_usage * 2.23
                        
                        record = EnergyRecord(
                            device_id=device.id,
                            recorded_at=record_date,
                            usage=round(actual_usage, 2),
                            unit="m³",
                            co2_emission=round(actual_co2, 3)
                        )
                        self.session.add(record)
                        created_count += 1
        
        # Create previous year records for YoY comparison
        prev_year = config.current_year - 1
        prev_electricity = prev_year_data['electricity']
        prev_gas = prev_year_data['gas']
        
        for month in range(1, 13):
            record_date = datetime(prev_year, month, 1)
            month_index = (month - 1) % 12
            
            # Create electricity records for previous year
            if electricity_devices:
                usage_per_device = prev_electricity[month_index] / len(electricity_devices)
                
                for device in electricity_devices[:3]:  # Limit to first 3 devices
                    existing = self.session.query(EnergyRecord).filter(
                        EnergyRecord.device_id == device.id,
                        EnergyRecord.recorded_at == record_date
                    ).first()
                    
                    if not existing:
                        variation = random.uniform(0.9, 1.1)
                        actual_usage = usage_per_device * variation
                        actual_co2 = actual_usage * 0.518  # CO2 factor for electricity
                        
                        record = EnergyRecord(
                            device_id=device.id,
                            recorded_at=record_date,
                            usage=round(actual_usage, 2),
                            unit="kWh",
                            co2_emission=round(actual_co2, 3)
                        )
                        self.session.add(record)
                        created_count += 1
            
            # Create gas records for previous year
            if gas_devices:
                usage_per_device = prev_gas[month_index] / len(gas_devices)
                
                for device in gas_devices[:2]:  # Limit to first 2 devices
                    existing = self.session.query(EnergyRecord).filter(
                        EnergyRecord.device_id == device.id,
                        EnergyRecord.recorded_at == record_date
                    ).first()
                    
                    if not existing:
                        variation = random.uniform(0.9, 1.1)
                        actual_usage = usage_per_device * variation
                        actual_co2 = actual_usage * 2.23
                        
                        record = EnergyRecord(
                            device_id=device.id,
                            recorded_at=record_date,
                            usage=round(actual_usage, 2),
                            unit="m³",
                            co2_emission=round(actual_co2, 3)
                        )
                        self.session.add(record)
                        created_count += 1
        
        print(f"✅ Created {created_count} energy records")
        return created_count
    
    def create_points_and_rankings(self) -> int:
        """Create point records and rankings"""
        print("🎯 Creating points and rankings...")
        
        # Get all company employees
        employees = self.session.query(Employee).filter(
            Employee.company_id == config.company_id
        ).all()
        
        if not employees:
            print("❌ No employees found for points creation")
            return 0
        
        point_data = config.get_point_data()
        created_count = 0
        
        for point_item in point_data:
            # Find user by email
            user = self.session.query(User).filter(
                User.email == point_item['user_email']
            ).first()
            
            if not user:
                continue
            
            # Check if point record already exists
            existing_point = self.session.query(Point).filter(
                Point.user_id == user.id,
                Point.earned_at == point_item['earned_at']
            ).first()
            
            if not existing_point:
                point = Point(
                    user_id=user.id,
                    company_id=config.company_id,
                    points=point_item['points'],
                    reason=point_item['reason'],
                    earned_at=point_item['earned_at']
                )
                self.session.add(point)
                created_count += 1
        
        # Create rankings based on total points
        self._create_rankings(employees)
        
        print(f"✅ Created {created_count} point records")
        return created_count
    
    def _create_rankings(self, employees: List[Employee]):
        """Create ranking records"""
        print("🏆 Creating rankings...")
        
        user_points = []
        
        for employee in employees:
            total_points = self.session.query(Point).filter(
                Point.user_id == employee.user_id
            ).with_entities(Point.points).all()
            
            total = sum(p[0] for p in total_points) if total_points else 0
            user_points.append((employee.user_id, total))
        
        # Sort by points descending
        user_points.sort(key=lambda x: x[1], reverse=True)
        
        # Create ranking records
        for rank, (user_id, points) in enumerate(user_points, 1):
            existing_ranking = self.session.query(Ranking).filter(
                Ranking.user_id == user_id,
                Ranking.company_id == config.company_id
            ).first()
            
            if existing_ranking:
                # Update existing ranking
                existing_ranking.rank = rank
                existing_ranking.total_points = points
            else:
                # Create new ranking
                ranking = Ranking(
                    user_id=user_id,
                    company_id=config.company_id,
                    rank=rank,
                    total_points=points,
                    period_start=config.current_date - timedelta(days=30),
                    period_end=config.current_date
                )
                self.session.add(ranking)
        
        print(f"✅ Updated rankings for {len(user_points)} users")
    
    def create_rewards(self) -> int:
        """Create reward records"""
        print("🎁 Creating rewards...")
        
        rewards_data = config.get_rewards_data()
        created_count = 0
        
        for reward_item in rewards_data:
            # Check if reward already exists
            existing_reward = self.session.query(Reward).filter(
                Reward.company_id == config.company_id,
                Reward.reward_name == reward_item['reward_name']
            ).first()
            
            if not existing_reward:
                reward = Reward(
                    company_id=config.company_id,
                    reward_name=reward_item['reward_name'],
                    points_required=reward_item['points_required'],
                    description=reward_item['description'],
                    is_active=reward_item['is_active']
                )
                self.session.add(reward)
                created_count += 1
        
        print(f"✅ Created {created_count} rewards")
        return created_count
    
    def verify_data_integrity(self) -> Dict[str, int]:
        """Verify that seeded data is correctly created"""
        print("🔍 Verifying data integrity...")
        
        counts = {
            'users': self.session.query(User).count(),
            'employees': self.session.query(Employee).filter(
                Employee.company_id == config.company_id
            ).count(),
            'devices': self.session.query(Device).join(Employee).filter(
                Employee.company_id == config.company_id
            ).count(),
            'energy_records': self.session.query(EnergyRecord).join(Device).join(Employee).filter(
                Employee.company_id == config.company_id
            ).count(),
            'points': self.session.query(Point).filter(
                Point.company_id == config.company_id
            ).count(),
            'rewards': self.session.query(Reward).filter(
                Reward.company_id == config.company_id
            ).count(),
            'rankings': self.session.query(Ranking).filter(
                Ranking.company_id == config.company_id
            ).count()
        }
        
        for entity, count in counts.items():
            print(f"📊 {entity}: {count}")
        
        return counts

# Convenience functions
def seed_database_direct() -> bool:
    """Seed database with all necessary data"""
    try:
        with DatabaseSeeder() as seeder:
            # 1. Ensure company exists
            seeder.ensure_company_exists()
            
            # 2. Create employee records (users should exist from API seeding)
            users_data = config.get_users_data()
            seeder.create_employee_records(users_data)
            
            # 3. Create devices
            seeder.create_devices_for_users()
            
            # 4. Create energy records
            seeder.create_energy_records()
            
            # 5. Create points and rankings
            seeder.create_points_and_rankings()
            
            # 6. Create rewards
            seeder.create_rewards()
            
            # 7. Verify data
            counts = seeder.verify_data_integrity()
            
            # Check if we have meaningful data
            success = (
                counts['employees'] >= 10 and
                counts['devices'] >= 20 and
                counts['energy_records'] >= 100 and
                counts['points'] >= 50
            )
            
            return success
            
    except Exception as e:
        print(f"❌ Database seeding failed: {e}")
        return False

def get_database_metrics() -> Dict[str, Any]:
    """Get metrics from database for verification"""
    try:
        with DatabaseSeeder() as seeder:
            # Get total energy usage for current month
            current_month_start = datetime(config.current_year, config.current_month, 1)
            
            electricity_total = seeder.session.query(EnergyRecord).join(Device).join(Employee).filter(
                Employee.company_id == config.company_id,
                EnergyRecord.unit == "kWh",
                EnergyRecord.recorded_at >= current_month_start
            ).with_entities(EnergyRecord.usage).all()
            
            gas_total = seeder.session.query(EnergyRecord).join(Device).join(Employee).filter(
                Employee.company_id == config.company_id,
                EnergyRecord.unit == "m³",
                EnergyRecord.recorded_at >= current_month_start
            ).with_entities(EnergyRecord.usage).all()
            
            co2_total = seeder.session.query(EnergyRecord).join(Device).join(Employee).filter(
                Employee.company_id == config.company_id,
                EnergyRecord.recorded_at >= current_month_start
            ).with_entities(EnergyRecord.co2_emission).all()
            
            active_users = seeder.session.query(Employee).filter(
                Employee.company_id == config.company_id
            ).count()
            
            return {
                'active_users': active_users,
                'electricity_total_kwh': sum(e[0] for e in electricity_total),
                'gas_total_m3': sum(g[0] for g in gas_total),
                'co2_reduction_total_kg': sum(c[0] for c in co2_total)
            }
            
    except Exception as e:
        print(f"Error getting database metrics: {e}")
        return {}