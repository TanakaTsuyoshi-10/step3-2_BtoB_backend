#!/usr/bin/env python3
"""
Seed script for rewards and initial points
"""

import sys
import os
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.reward import Reward
from app.models.points_ledger import PointsLedger
from app.models.user import User
from app.models.employee import Employee


def seed_rewards_and_points():
    """Add sample rewards and give users initial points"""
    db = SessionLocal()
    
    try:
        # Create sample rewards
        rewards = [
            {
                "title": "Amazonギフトカード 500円",
                "description": "Amazon.co.jpで使える500円分のギフトカードです",
                "category": "ギフトカード",
                "points_required": 500,
                "stock": 50,
                "active": True,
                "image_url": "https://via.placeholder.com/200x150?text=Amazon+500"
            },
            {
                "title": "Starbucksカード 1000円",
                "description": "全国のスターバックスで使える1000円分のカードです",
                "category": "ギフトカード", 
                "points_required": 1000,
                "stock": 30,
                "active": True,
                "image_url": "https://via.placeholder.com/200x150?text=Starbucks+1000"
            },
            {
                "title": "エコバッグ",
                "description": "環境に優しいリサイクル素材のエコバッグ",
                "category": "エコグッズ",
                "points_required": 300,
                "stock": 100,
                "active": True,
                "image_url": "https://via.placeholder.com/200x150?text=Eco+Bag"
            },
            {
                "title": "USB充電器",
                "description": "スマートフォン・タブレット対応のUSB充電器",
                "category": "電子機器",
                "points_required": 800,
                "stock": 20,
                "active": True,
                "image_url": "https://via.placeholder.com/200x150?text=USB+Charger"
            },
            {
                "title": "コンビニギフト券 300円",
                "description": "セブンイレブン、ファミマ、ローソンで使える300円券",
                "category": "ギフトカード",
                "points_required": 300,
                "stock": 80,
                "active": True,
                "image_url": "https://via.placeholder.com/200x150?text=Convenience+300"
            },
            {
                "title": "プレミアムコーヒーセット",
                "description": "厳選されたコーヒー豆のセット（200g×3種類）",
                "category": "食品",
                "points_required": 1500,
                "stock": 15,
                "active": True,
                "image_url": "https://via.placeholder.com/200x150?text=Coffee+Set"
            }
        ]
        
        # Check if rewards already exist
        existing_rewards = db.query(Reward).count()
        if existing_rewards == 0:
            print("Creating sample rewards...")
            for reward_data in rewards:
                reward = Reward(**reward_data)
                db.add(reward)
            print(f"✅ Created {len(rewards)} rewards")
        else:
            print(f"ℹ️  {existing_rewards} rewards already exist, skipping...")
        
        # Give initial points to all users
        users = db.query(User).join(Employee).all()
        print(f"Found {len(users)} users")
        
        for user in users:
            # Check if user already has points
            existing_ledger = db.query(PointsLedger).filter(
                PointsLedger.user_id == user.id
            ).first()
            
            if not existing_ledger:
                # Give 5000 initial points
                initial_points = PointsLedger(
                    user_id=user.id,
                    delta=5000,
                    reason="初期ポイント付与",
                    reference_id=None,
                    balance_after=5000
                )
                db.add(initial_points)
                print(f"✅ Gave {user.email} 5000 initial points")
            else:
                print(f"ℹ️  User {user.email} already has points")
        
        db.commit()
        print("🎉 Seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Starting rewards and points seeding...")
    seed_rewards_and_points()