#!/usr/bin/env python3
"""
Seed configuration management for dummy data generation
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class SeedConfig:
    """Configuration for seeding operations"""
    
    def __init__(self):
        # Environment variables
        self.api_base_url = os.getenv('API_BASE_URL', 'https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net')
        self.database_url = os.getenv('MYSQL_URL', self._build_mysql_url())
        
        # Company settings
        self.company_id = 1  # SCOPE3_HOLDINGS
        self.company_name = "SCOPE3_HOLDINGS"
        
        # Admin user settings
        self.admin_email = "admin@example.com"
        self.admin_password = "admin123"
        
        # Data generation settings
        self.user_count = 15
        self.active_user_count = 8
        self.months_back = 12
        
        # Current date for calculations
        self.current_date = datetime.now()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month
        
    def _build_mysql_url(self) -> str:
        """Build MySQL URL from environment variables"""
        host = os.getenv('MYSQL_HOST', 'localhost')
        user = os.getenv('MYSQL_USER', 'root')
        password = os.getenv('MYSQL_PASSWORD', '')
        database = os.getenv('MYSQL_DATABASE', 'energy_db')
        
        return f"mysql+mysqlconnector://{user}:{password}@{host}:3306/{database}"
    
    def get_monthly_electricity_data(self) -> List[float]:
        """Get 12 months of electricity data (kWh)"""
        # [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
        base_data = [1850, 1920, 2100, 2050, 1980, 1650, 1800, 2000, 1700, 1600, 1550, 1400]
        
        # Adjust for current month position
        current_month_index = self.current_month - 1
        
        # Rotate data so current month is at the end
        rotated_data = base_data[current_month_index+1:] + base_data[:current_month_index+1]
        
        return rotated_data
    
    def get_monthly_gas_data(self) -> List[float]:
        """Get 12 months of gas data (m³)"""
        base_data = [90, 95, 100, 98, 105, 82, 88, 92, 85, 83, 84, 81]
        
        # Adjust for current month position
        current_month_index = self.current_month - 1
        rotated_data = base_data[current_month_index+1:] + base_data[:current_month_index+1]
        
        return rotated_data
    
    def get_monthly_co2_data(self) -> List[float]:
        """Get 12 months of CO2 reduction data (kg)"""
        base_data = [430, 438, 445, 452, 460, 448, 455, 462, 470, 471, 474, 480]
        
        # Adjust for current month position
        current_month_index = self.current_month - 1
        rotated_data = base_data[current_month_index+1:] + base_data[:current_month_index+1]
        
        return rotated_data
    
    def get_previous_year_data(self) -> Dict[str, List[float]]:
        """Get previous year data for YoY comparison (higher usage = reduction achieved)"""
        current_electricity = self.get_monthly_electricity_data()
        current_gas = self.get_monthly_gas_data()
        
        # Previous year data should be higher to show reduction
        prev_electricity = [x * 1.15 for x in current_electricity]  # 15% higher
        prev_gas = [x * 1.12 for x in current_gas]  # 12% higher
        
        return {
            'electricity': prev_electricity,
            'gas': prev_gas
        }
    
    def get_date_range_for_month(self, year: int, month: int) -> tuple:
        """Get start and end dates for a given month"""
        start_date = datetime(year, month, 1)
        
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
        return start_date, end_date
    
    def get_users_data(self) -> List[Dict[str, Any]]:
        """Get user data for seeding"""
        users = []
        departments = ["営業部", "開発部", "マーケティング部", "人事部", "総務部", "経理部", "製造部", "品質管理部"]
        
        for i in range(1, self.user_count + 1):
            user_data = {
                'email': f"employee{i:03d}@scope3holdings.co.jp",
                'password': "demo123",
                'full_name': f"社員{i:03d}",
                'department': departments[(i-1) % len(departments)],
                'employee_code': f"EMP{i:03d}",
                'is_active': i <= self.active_user_count
            }
            users.append(user_data)
        
        return users
    
    def get_point_data(self) -> List[Dict[str, Any]]:
        """Get point data for seeding"""
        point_data = []
        
        for i in range(1, self.user_count + 1):
            # Generate points for each user with varying amounts
            base_points = 100 + (i * 50)
            variations = [0.8, 1.0, 1.2, 0.9, 1.1, 0.95]
            
            for month_offset in range(6):  # Last 6 months
                date = self.current_date - timedelta(days=month_offset * 30)
                points = int(base_points * variations[month_offset])
                
                point_data.append({
                    'user_email': f"employee{i:03d}@scope3holdings.co.jp",
                    'points': points,
                    'reason': f"月間エネルギー削減達成 ({date.strftime('%Y年%m月')})",
                    'earned_at': date
                })
        
        return point_data
    
    def get_rewards_data(self) -> List[Dict[str, Any]]:
        """Get reward data for seeding"""
        return [
            {
                'reward_name': 'エコバッグ',
                'points_required': 100,
                'description': '環境に優しいリサイクル素材のエコバッグ',
                'is_active': True
            },
            {
                'reward_name': 'コーヒー券',
                'points_required': 150,
                'description': '社内カフェで使用できるコーヒー券',
                'is_active': True
            },
            {
                'reward_name': '図書券',
                'points_required': 300,
                'description': '本やe-bookの購入に使える図書券',
                'is_active': True
            },
            {
                'reward_name': '観葉植物',
                'points_required': 250,
                'description': 'デスクに置ける小さな観葉植物',
                'is_active': True
            },
            {
                'reward_name': 'ギフトカード',
                'points_required': 500,
                'description': '汎用ギフトカード（5000円分）',
                'is_active': True
            }
        ]
    
    def get_device_types(self) -> List[tuple]:
        """Get device types for seeding"""
        return [
            ("スマートメーター", "電力"),
            ("ガスメーター", "ガス"), 
            ("エアコン", "電力"),
            ("照明システム", "電力"),
            ("ガス給湯器", "ガス"),
            ("冷蔵庫", "電力"),
            ("暖房器具", "ガス")
        ]

# Global config instance
config = SeedConfig()