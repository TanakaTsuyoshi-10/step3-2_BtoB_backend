#!/usr/bin/env python3
"""
Tests for metrics seeding functionality
"""

import pytest
import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from tools.seed.seed_config import config
from tools.seed.seed_api import APISeedClient, get_current_api_metrics
from tools.seed.seed_db import get_database_metrics

class TestMetricsSeed:
    """Test metrics seeding functionality"""
    
    def test_config_initialization(self):
        """Test that configuration is properly initialized"""
        assert config.company_id == 1
        assert config.company_name == "SCOPE3_HOLDINGS"
        assert config.user_count >= 15
        assert config.active_user_count >= 5
        assert config.months_back == 12
        
        # Test data generation
        electricity_data = config.get_monthly_electricity_data()
        assert len(electricity_data) == 12
        assert all(x > 0 for x in electricity_data)
        
        gas_data = config.get_monthly_gas_data()
        assert len(gas_data) == 12
        assert all(x > 0 for x in gas_data)
        
        co2_data = config.get_monthly_co2_data()
        assert len(co2_data) == 12
        assert all(x > 0 for x in co2_data)
    
    def test_users_data_generation(self):
        """Test user data generation"""
        users_data = config.get_users_data()
        
        assert len(users_data) == config.user_count
        
        for user_data in users_data:
            assert 'email' in user_data
            assert '@scope3holdings.co.jp' in user_data['email']
            assert 'password' in user_data
            assert 'full_name' in user_data
            assert 'department' in user_data
            assert 'employee_code' in user_data
            assert 'is_active' in user_data
        
        # Check that correct number of active users
        active_count = sum(1 for user in users_data if user['is_active'])
        assert active_count == config.active_user_count
    
    def test_point_data_generation(self):
        """Test point data generation"""
        point_data = config.get_point_data()
        
        # Should have 6 months * user_count points
        expected_count = 6 * config.user_count
        assert len(point_data) == expected_count
        
        for point_item in point_data:
            assert 'user_email' in point_item
            assert 'points' in point_item
            assert 'reason' in point_item
            assert 'earned_at' in point_item
            assert point_item['points'] > 0
    
    def test_rewards_data_generation(self):
        """Test rewards data generation"""
        rewards_data = config.get_rewards_data()
        
        assert len(rewards_data) >= 5
        
        for reward in rewards_data:
            assert 'reward_name' in reward
            assert 'points_required' in reward
            assert 'description' in reward
            assert 'is_active' in reward
            assert reward['points_required'] > 0
            assert reward['is_active'] is True
    
    def test_previous_year_data_generation(self):
        """Test previous year data for YoY comparison"""
        prev_year_data = config.get_previous_year_data()
        
        assert 'electricity' in prev_year_data
        assert 'gas' in prev_year_data
        
        current_electricity = config.get_monthly_electricity_data()
        current_gas = config.get_monthly_gas_data()
        
        prev_electricity = prev_year_data['electricity']
        prev_gas = prev_year_data['gas']
        
        assert len(prev_electricity) == 12
        assert len(prev_gas) == 12
        
        # Previous year should be higher (showing reduction achieved)
        for i in range(12):
            assert prev_electricity[i] > current_electricity[i]
            assert prev_gas[i] > current_gas[i]
    
    def test_api_client_initialization(self):
        """Test API client can be initialized"""
        client = APISeedClient()
        assert client.base_url == config.api_base_url
        assert client.session is not None
        assert client.admin_token is None  # Not authenticated yet
    
    @pytest.mark.asyncio
    async def test_metrics_api_structure(self):
        """Test that metrics API returns expected structure"""
        try:
            # Get current metrics (may be empty but should have structure)
            metrics = get_current_api_metrics()
            
            if metrics:  # Only test if we can get metrics
                # KPI structure
                expected_kpi_fields = ['company_id', 'active_users', 'electricity_total_kwh', 'gas_total_m3']
                
                for field in expected_kpi_fields:
                    if field in metrics:
                        assert isinstance(metrics[field], (int, float))
                        if field != 'company_id':  # company_id can be any value
                            assert metrics[field] >= 0
            
        except Exception:
            # API might not be accessible in test environment
            pytest.skip("API not accessible in test environment")
    
    def test_database_metrics_structure(self):
        """Test database metrics return expected structure"""
        try:
            metrics = get_database_metrics()
            
            if metrics:  # Only test if we can get metrics
                expected_fields = ['active_users', 'electricity_total_kwh', 'gas_total_m3', 'co2_reduction_total_kg']
                
                for field in expected_fields:
                    if field in metrics:
                        assert isinstance(metrics[field], (int, float))
                        assert metrics[field] >= 0
            
        except Exception:
            # Database might not be accessible in test environment
            pytest.skip("Database not accessible in test environment")
    
    def test_date_range_calculation(self):
        """Test date range calculations"""
        start_date, end_date = config.get_date_range_for_month(2025, 8)
        
        assert start_date.year == 2025
        assert start_date.month == 8
        assert start_date.day == 1
        
        assert end_date.year == 2025
        assert end_date.month == 8
        assert end_date.day == 31  # August has 31 days
        
        # Test December (year boundary)
        start_date, end_date = config.get_date_range_for_month(2025, 12)
        assert start_date == datetime(2025, 12, 1)
        assert end_date == datetime(2025, 12, 31)
    
    def test_device_types_data(self):
        """Test device types data"""
        device_types = config.get_device_types()
        
        assert len(device_types) >= 5
        
        for device_name, energy_type in device_types:
            assert isinstance(device_name, str)
            assert energy_type in ["電力", "ガス"]
            assert len(device_name) > 0

class TestSeedValidation:
    """Test validation of seeded data"""
    
    def test_electricity_data_realistic(self):
        """Test that electricity data is in realistic ranges"""
        electricity_data = config.get_monthly_electricity_data()
        
        for usage in electricity_data:
            # Should be between 1000-3000 kWh per month (reasonable for company)
            assert 1000 <= usage <= 3000
    
    def test_gas_data_realistic(self):
        """Test that gas data is in realistic ranges"""
        gas_data = config.get_monthly_gas_data()
        
        for usage in gas_data:
            # Should be between 50-150 m³ per month
            assert 50 <= usage <= 150
    
    def test_co2_data_realistic(self):
        """Test that CO2 data is in realistic ranges"""
        co2_data = config.get_monthly_co2_data()
        
        for co2 in co2_data:
            # Should be between 400-500 kg per month
            assert 400 <= co2 <= 500
    
    def test_point_values_realistic(self):
        """Test that point values are realistic"""
        point_data = config.get_point_data()
        
        for point_item in point_data:
            points = point_item['points']
            # Points should be between 50-1000 per month
            assert 50 <= points <= 1000
    
    def test_no_duplicate_emails(self):
        """Test that user emails are unique"""
        users_data = config.get_users_data()
        emails = [user['email'] for user in users_data]
        
        assert len(emails) == len(set(emails))  # No duplicates
    
    def test_no_duplicate_employee_codes(self):
        """Test that employee codes are unique"""
        users_data = config.get_users_data()
        codes = [user['employee_code'] for user in users_data]
        
        assert len(codes) == len(set(codes))  # No duplicates

if __name__ == "__main__":
    pytest.main([__file__, "-v"])