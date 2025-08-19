#!/usr/bin/env python3
"""
Unit tests for metrics API endpoints
Tests all four metrics endpoints with various scenarios
"""

import requests
import json
from datetime import date, datetime
import time

# Configuration
API_BASE = "http://localhost:8000/api/v1"
TEST_USER = {
    "username": "admin@example.com",
    "password": "StrongP@ssw0rd!"
}

def get_auth_token():
    """Get authentication token for testing"""
    print("🔐 Getting authentication token...")
    
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    
    response = requests.post(
        f"{API_BASE}/login/access-token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Authentication successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_kpi_endpoint(headers):
    """Test KPI metrics endpoint"""
    print("\n📊 Testing KPI metrics endpoint...")
    
    # Test default parameters
    response = requests.get(f"{API_BASE}/metrics/kpi", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ KPI endpoint working")
        print(f"   Company ID: {data.get('company_id')}")
        print(f"   Active Users: {data.get('active_users')}")
        print(f"   Electricity Total: {data.get('electricity_total_kwh')} kWh")
        print(f"   Gas Total: {data.get('gas_total_m3')} m³")
        print(f"   CO2 Reduction: {data.get('co2_reduction_total_kg')} kg")
        return True
    else:
        print(f"❌ KPI endpoint failed: {response.text}")
        return False

def test_monthly_usage_endpoint(headers):
    """Test monthly usage endpoint"""
    print("\n📈 Testing monthly usage endpoint...")
    
    current_year = datetime.now().year
    response = requests.get(
        f"{API_BASE}/metrics/monthly-usage",
        params={"year": current_year},
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Monthly usage endpoint working")
        print(f"   Company ID: {data.get('company_id')}")
        print(f"   Year: {data.get('year')}")
        print(f"   Months data: {len(data.get('months', []))} entries")
        
        # Show sample month data
        if data.get('months'):
            sample_month = data['months'][0]
            print(f"   Sample (Month {sample_month.get('month')}): "
                  f"{sample_month.get('electricity_kwh')} kWh, "
                  f"{sample_month.get('gas_m3')} m³")
        return True
    else:
        print(f"❌ Monthly usage endpoint failed: {response.text}")
        return False

def test_co2_trend_endpoint(headers):
    """Test CO2 trend endpoint"""
    print("\n📉 Testing CO2 trend endpoint...")
    
    response = requests.get(
        f"{API_BASE}/metrics/co2-trend",
        params={"interval": "month"},
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ CO2 trend endpoint working")
        print(f"   Company ID: {data.get('company_id')}")
        print(f"   Data Points: {len(data.get('points', []))} entries")
        
        # Show sample data point
        if data.get('points'):
            sample_point = data['points'][0]
            print(f"   Sample: {sample_point.get('period')} - {sample_point.get('co2_kg')} kg CO2")
        return True
    else:
        print(f"❌ CO2 trend endpoint failed: {response.text}")
        return False

def test_yoy_usage_endpoint(headers):
    """Test year-over-year usage endpoint"""
    print("\n📊 Testing year-over-year usage endpoint...")
    
    current_month = datetime.now().strftime("%Y-%m")
    response = requests.get(
        f"{API_BASE}/metrics/yoy-usage",
        params={"month": current_month},
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ YoY usage endpoint working")
        print(f"   Company ID: {data.get('company_id')}")
        print(f"   Month: {data.get('month')}")
        
        current = data.get('current', {})
        previous = data.get('previous', {})
        delta = data.get('delta', {})
        
        print(f"   Current: {current.get('electricity_kwh')} kWh, {current.get('gas_m3')} m³")
        print(f"   Previous: {previous.get('electricity_kwh')} kWh, {previous.get('gas_m3')} m³")
        print(f"   Delta: {delta.get('electricity_kwh')} kWh, {delta.get('gas_m3')} m³")
        return True
    else:
        print(f"❌ YoY usage endpoint failed: {response.text}")
        return False

def test_error_scenarios(headers):
    """Test error scenarios"""
    print("\n⚠️ Testing error scenarios...")
    
    # Test invalid company access
    response = requests.get(
        f"{API_BASE}/metrics/kpi",
        params={"company_id": 999},  # Non-existent company
        headers=headers
    )
    
    if response.status_code == 403:
        print("✅ Proper access control - forbidden company access rejected")
    else:
        print(f"❌ Access control failed: {response.status_code}")
    
    # Test invalid date ranges
    response = requests.get(
        f"{API_BASE}/metrics/kpi",
        params={"from_date": "2025-12-31", "to_date": "2025-01-01"},  # Invalid range
        headers=headers
    )
    
    print(f"   Invalid date range test: {response.status_code}")
    return True

def run_all_tests():
    """Run all metrics API tests"""
    print("🧪 Starting Metrics API Tests")
    print("=" * 50)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Run all endpoint tests
    tests = [
        test_kpi_endpoint,
        test_monthly_usage_endpoint,
        test_co2_trend_endpoint,
        test_yoy_usage_endpoint,
        test_error_scenarios
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func(headers)
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️ Some tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)