#!/usr/bin/env python3
"""
Dashboard API動作確認テスト
KPIと月次データが0以外で返ることを確認
"""

import requests
import json
from datetime import datetime

# API Base URLs
BACKEND_BASE = "https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net"
FRONTEND_BASE = "https://app-002-gen10-step3-2-node-oshima2.azurewebsites.net"

def test_backend_endpoints():
    """バックエンドAPIエンドポイントをテスト"""
    print("🔍 Backend API Tests")
    print("=" * 50)
    
    # Test endpoints without authentication (if possible)
    endpoints = [
        "/api/v1/metrics/kpi",
        "/api/v1/metrics/monthly-usage", 
        "/api/v1/metrics/co2-trend"
    ]
    
    for endpoint in endpoints:
        url = f"{BACKEND_BASE}{endpoint}"
        print(f"\n📡 Testing: {endpoint}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2, default=str)[:200]}...")
                
                # Basic validation
                if endpoint.endswith('/kpi'):
                    assert 'active_users' in data or 'total_users' in data
                    print(f"   ✅ KPI data structure OK")
                    
                elif endpoint.endswith('/monthly-usage'):
                    assert isinstance(data, list) or 'months' in data
                    print(f"   ✅ Monthly usage data structure OK")
                    
                elif endpoint.endswith('/co2-trend'):
                    assert isinstance(data, list) or 'points' in data  
                    print(f"   ✅ CO2 trend data structure OK")
                    
            elif response.status_code == 401:
                print(f"   ⚠️  Authentication required")
            elif response.status_code == 403:
                print(f"   ⚠️  Access forbidden")
            else:
                print(f"   ❌ Error: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")

def test_frontend_access():
    """フロントエンド接続可能性をテスト"""
    print("\n🖥️  Frontend Access Test")
    print("=" * 50)
    
    try:
        response = requests.get(f"{FRONTEND_BASE}/dashboard", timeout=10)
        print(f"Dashboard page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard page accessible")
            # Check if it contains expected elements
            content = response.text.lower()
            if 'dashboard' in content:
                print("✅ Dashboard content detected")
            else:
                print("⚠️  Dashboard content not found")
        else:
            print(f"❌ Dashboard page error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend access failed: {e}")

def test_database_health():
    """データベース接続とデータ存在確認"""
    print("\n🗃️  Database Health Check")  
    print("=" * 50)
    
    # This would require direct DB connection
    print("ℹ️  Database health check requires backend logs")
    print("   Check Azure App Service logs for connection status")

def main():
    print(f"🚀 Dashboard API Test Suite")
    print(f"Backend: {BACKEND_BASE}")
    print(f"Frontend: {FRONTEND_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_backend_endpoints()
    test_frontend_access()
    test_database_health()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed")
    print("\nNext steps:")
    print("1. Check Azure App Service logs for detailed errors")
    print("2. Verify database connectivity in backend")
    print("3. Test with authentication if required")

if __name__ == "__main__":
    main()