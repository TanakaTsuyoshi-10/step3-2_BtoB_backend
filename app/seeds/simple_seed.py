#!/usr/bin/env python3
"""
Simple demo data seeding script for dashboard testing
Creates minimal data to ensure dashboard displays are not empty
"""

import sys
import os
import random
from datetime import datetime, timedelta
from typing import List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User
from app.models.employee import Employee
from app.models.point import Point
from app.models.energy_record import EnergyRecord
from app.models.reward import Reward
from app.models.redemption import Redemption
from app.core.security import get_password_hash

def create_admin_user(db: Session):
    """Create admin user if not exists"""
    admin_email = "admin@example.com"
    admin = db.query(User).filter(User.email == admin_email).first()
    
    if not admin:
        admin = User(
            email=admin_email,
            hashed_password=get_password_hash("admin123"),
            full_name="システム管理者",
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        db.flush()
        print(f"Created admin user: {admin_email}")
    
    return admin

def create_sample_employees(db: Session, count: int = 10) -> List[User]:
    """Create sample employees"""
    users = []
    departments = ['営業部', '開発部', '総務部', '経理部', '人事部']
    
    for i in range(count):
        email = f"employee{i+1:02d}@example.com"
        existing = db.query(User).filter(User.email == email).first()
        
        if existing:
            users.append(existing)
            continue
            
        user = User(
            email=email,
            hashed_password=get_password_hash("password123"),
            full_name=f"従業員{i+1:02d}",
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.flush()
        
        # Create employee record
        employee = Employee(
            user_id=user.id,
            company_id=1,
            department=random.choice(departments),
            employee_code=f"EMP{i+1:04d}"
        )
        db.add(employee)
        users.append(user)
        
    return users

def create_sample_points(db: Session, users: List[User]):
    """Create sample point records"""
    for user in users:
        # Create points for the last 12 months
        for month_offset in range(12):
            earned_at = datetime.now() - timedelta(days=30 * month_offset)
            points_earned = random.randint(50, 500)
            
            point_record = Point(
                user_id=user.id,
                company_id=1,
                points=points_earned,
                reason=f"省エネ活動({earned_at.strftime('%Y年%m月')})",
                earned_at=earned_at
            )
            db.add(point_record)
            
            # Sometimes add negative points (usage)
            if random.random() < 0.3:  # 30% chance
                points_used = -random.randint(10, min(points_earned, 100))
                usage_record = Point(
                    user_id=user.id,
                    company_id=1,
                    points=points_used,
                    reason="景品交換",
                    earned_at=earned_at + timedelta(days=random.randint(1, 25))
                )
                db.add(usage_record)

def create_sample_energy_records(db: Session, users: List[User]):
    """Create sample energy consumption records"""
    for user in users:
        # Create energy records for the last 12 months
        for month_offset in range(12):
            record_date = datetime.now() - timedelta(days=30 * month_offset)
            
            # Electricity record
            electricity_record = EnergyRecord(
                user_id=user.id,
                device_id=None,  # No devices created in this simple seed
                energy_type="electricity",
                consumption=random.uniform(200, 800),
                recorded_at=record_date
            )
            db.add(electricity_record)
            
            # Gas record
            gas_record = EnergyRecord(
                user_id=user.id,
                device_id=None,
                energy_type="gas", 
                consumption=random.uniform(50, 200),
                recorded_at=record_date
            )
            db.add(gas_record)

def create_sample_rewards(db: Session) -> List[Reward]:
    """Create sample rewards"""
    rewards_data = [
        ("Amazonギフト券 500円", "オンラインで使える便利なギフト券", "ギフト券", 500),
        ("Amazonギフト券 1000円", "オンラインで使える便利なギフト券", "ギフト券", 1000),
        ("スターバックスカード 500円", "全国のスターバックスで使える", "ギフト券", 500),
        ("エコバッグ", "環境に優しいオリジナルエコバッグ", "グッズ", 200),
        ("タンブラー", "保温・保冷機能付きタンブラー", "グッズ", 300),
        ("ボールペンセット", "高級ボールペン3本セット", "文具", 150),
    ]
    
    rewards = []
    for title, description, category, points_required in rewards_data:
        existing = db.query(Reward).filter(Reward.title == title).first()
        if existing:
            rewards.append(existing)
            continue
            
        reward = Reward(
            title=title,
            description=description,
            category=category,
            image_url=None,
            stock=random.randint(50, 100),
            points_required=points_required,
            active=True
        )
        db.add(reward)
        rewards.append(reward)
        
    return rewards

def create_sample_redemptions(db: Session, users: List[User], rewards: List[Reward]):
    """Create sample redemptions"""
    # Create redemptions for some users
    sample_users = random.sample(users, min(5, len(users)))
    
    for user in sample_users:
        num_redemptions = random.randint(1, 2)
        for _ in range(num_redemptions):
            reward = random.choice(rewards)
            
            redemption = Redemption(
                user_id=user.id,
                reward_id=reward.id,
                points_spent=reward.points_required,
                status=random.choice(['申請中', '承認', '発送済'])
            )
            db.add(redemption)

def main():
    """Main seeding function"""
    print("Starting simple data seeding...")
    
    db = SessionLocal()
    try:
        # Create admin user
        admin = create_admin_user(db)
        
        # Create sample employees
        print("Creating sample employees...")
        employees = create_sample_employees(db, count=15)
        
        # Create sample points
        print("Creating sample points...")
        create_sample_points(db, employees)
        
        # Create sample energy records  
        print("Creating sample energy records...")
        create_sample_energy_records(db, employees)
        
        # Create sample rewards
        print("Creating sample rewards...")
        rewards = create_sample_rewards(db)
        
        # Create sample redemptions
        print("Creating sample redemptions...")
        create_sample_redemptions(db, employees, rewards)
        
        # Commit all changes
        db.commit()
        
        print("✅ Simple seeding completed successfully!")
        print(f"Created:")
        print(f"  - 1 admin user")
        print(f"  - {len(employees)} employee users") 
        print(f"  - {len(employees) * 12} months of point records")
        print(f"  - {len(employees) * 24} energy records") 
        print(f"  - {len(rewards)} rewards")
        print(f"Dashboard should now display sample data.")
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()