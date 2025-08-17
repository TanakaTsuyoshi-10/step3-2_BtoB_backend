#!/usr/bin/env python3
"""
Test different Azure MySQL username formats and connection methods
"""

import pymysql
import subprocess
import os
from app.core.config import settings

def test_username_formats():
    """Test different Azure MySQL username formats"""
    
    print("🔍 Testing Azure MySQL Username Formats")
    print("=" * 60)
    
    # Get original settings
    host = settings.MYSQL_HOST
    port = settings.MYSQL_PORT
    password = settings.MYSQL_PASSWORD
    database = settings.MYSQL_DATABASE
    
    # Extract server name from host
    server_name = host.split('.')[0]  # rdbs-002-gen10-step3-2-oshima2
    base_username = "tech0gen10student"
    
    # Different username formats to try
    username_formats = [
        f"{base_username}@{server_name}",  # Current format
        f"{base_username}",                # Without server suffix
        f"{base_username}@{host}",         # With full host
        f"{base_username}@{server_name}.mysql.database.azure.com",  # Alternative format
    ]
    
    print(f"📋 Testing against server: {host}")
    print(f"📋 Base username: {base_username}")
    print(f"📋 Server name extracted: {server_name}")
    print()
    
    for i, username in enumerate(username_formats, 1):
        print(f"🧪 Test {i}: Username format '{username}'")
        print("-" * 40)
        
        try:
            # Test PyMySQL connection
            connection = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database,
                ssl_disabled=False,
                connect_timeout=30
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT USER() as current_user, CONNECTION_ID() as connection_id")
                user_info = cursor.fetchone()
                
                cursor.execute("SELECT VERSION() as version")
                version = cursor.fetchone()
                
                cursor.execute("SELECT DATABASE() as current_db")
                current_db = cursor.fetchone()
            
            connection.close()
            
            print(f"   ✅ SUCCESS!")
            print(f"   👤 Connected as: {user_info[0]}")
            print(f"   🔗 Connection ID: {user_info[1]}")
            print(f"   📊 MySQL Version: {version[0]}")
            print(f"   📂 Database: {current_db[0]}")
            print()
            print(f"🎉 WORKING USERNAME FORMAT: '{username}'")
            return username
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
        
        print()
    
    print("❌ None of the username formats worked!")
    return None

def test_mysql_client_formats():
    """Test different formats with MySQL command line client"""
    
    print("\n🔧 Testing MySQL Command Line Client Formats")
    print("=" * 60)
    
    # Get settings
    host = settings.MYSQL_HOST
    password = settings.MYSQL_PASSWORD
    database = settings.MYSQL_DATABASE
    server_name = host.split('.')[0]
    base_username = "tech0gen10student"
    
    username_formats = [
        f"{base_username}@{server_name}",
        f"{base_username}",
        f"{base_username}@{host}",
    ]
    
    mysql_client = "/opt/homebrew/opt/mysql-client@8.4/bin/mysql"
    
    for i, username in enumerate(username_formats, 1):
        print(f"🧪 MySQL Client Test {i}: '{username}'")
        print("-" * 40)
        
        try:
            cmd = [
                mysql_client,
                "-h", host,
                "-u", username,
                f"-p{password}",
                "-D", database,
                "--ssl-mode=REQUIRED",
                "-e", "SELECT USER() as current_user, VERSION() as version;"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"   ✅ SUCCESS!")
                print(f"   📊 Output:")
                for line in result.stdout.strip().split('\n'):
                    print(f"      {line}")
                print()
                print(f"🎉 WORKING MySQL CLIENT FORMAT: '{username}'")
                return username
            else:
                print(f"   ❌ Failed:")
                for line in result.stderr.strip().split('\n'):
                    if line.strip():
                        print(f"      {line}")
                        
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        print()
    
    return None

def get_current_ip():
    """Get current public IP address"""
    try:
        import urllib.request
        response = urllib.request.urlopen('https://httpbin.org/ip', timeout=10)
        import json
        data = json.loads(response.read().decode())
        return data['origin']
    except:
        return "Unable to determine"

def main():
    """Main diagnostic function"""
    
    print("🚀 Azure MySQL Connection Diagnostic Suite")
    print("=" * 60)
    
    # Show current IP
    current_ip = get_current_ip()
    print(f"📍 Your current public IP: {current_ip}")
    print(f"📍 Error shows connection from: 133.175.153.156")
    if current_ip != "133.175.153.156" and current_ip != "Unable to determine":
        print("⚠️  IP addresses don't match - this might indicate a proxy/NAT")
    print()
    
    # Test PyMySQL formats
    working_username = test_username_formats()
    
    # Test MySQL client formats
    if not working_username:
        working_username = test_mysql_client_formats()
    
    if working_username:
        print(f"\n🎯 SOLUTION FOUND!")
        print(f"✅ Working username format: '{working_username}'")
        print(f"\n📝 Update your .env file:")
        print(f"MYSQL_USER={working_username}")
    else:
        print(f"\n❌ NO WORKING FORMATS FOUND")
        print(f"\n🔧 Possible solutions:")
        print(f"1. Check Azure MySQL firewall rules for IP: 133.175.153.156")
        print(f"2. Verify user permissions in Azure MySQL")
        print(f"3. Contact Azure administrator to confirm username format")
        print(f"4. Check if user exists: SHOW GRANTS FOR 'username'@'%';")

if __name__ == "__main__":
    main()