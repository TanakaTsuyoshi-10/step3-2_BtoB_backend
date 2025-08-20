#!/usr/bin/env python3
"""
Test only the configuration without database connection
"""

from seed_config import config

def test_config():
    print("🧪 Testing seed configuration...")
    
    print(f"Company: {config.company_name} (ID: {config.company_id})")
    print(f"Users: {config.user_count} total, {config.active_user_count} active")
    print(f"API Base: {config.api_base_url}")
    
    # Test data generation
    electricity_data = config.get_monthly_electricity_data()
    print(f"Electricity data: {len(electricity_data)} months, range: {min(electricity_data):.1f}-{max(electricity_data):.1f} kWh")
    
    gas_data = config.get_monthly_gas_data()
    print(f"Gas data: {len(gas_data)} months, range: {min(gas_data):.1f}-{max(gas_data):.1f} m³")
    
    co2_data = config.get_monthly_co2_data()
    print(f"CO2 data: {len(co2_data)} months, range: {min(co2_data):.1f}-{max(co2_data):.1f} kg")
    
    # Test user data
    users_data = config.get_users_data()
    print(f"User data: {len(users_data)} users")
    
    # Test point data
    point_data = config.get_point_data()
    print(f"Point data: {len(point_data)} point records")
    
    # Test rewards
    rewards_data = config.get_rewards_data()
    print(f"Rewards data: {len(rewards_data)} rewards")
    
    print("✅ Configuration test passed!")
    return True

if __name__ == "__main__":
    test_config()