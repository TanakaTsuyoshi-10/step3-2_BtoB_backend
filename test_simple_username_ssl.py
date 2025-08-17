#!/usr/bin/env python3
"""
Test simple username format with proper SSL configuration
"""

import pymysql
import ssl
from app.core.config import settings

def test_simple_username_with_ssl():
    """Test simple username format with various SSL configurations"""
    
    print("🔐 Testing Simple Username with SSL")
    print("=" * 50)
    
    host = settings.MYSQL_HOST
    port = settings.MYSQL_PORT
    password = settings.MYSQL_PASSWORD
    database = settings.MYSQL_DATABASE
    
    # Simple username without @server suffix
    username = "tech0gen10student"
    
    print(f"📋 Testing username: '{username}'")
    print(f"📋 Host: {host}")
    print(f"📋 Database: {database}")
    print()
    
    # SSL configurations to test
    ssl_configs = [
        {
            "name": "SSL with certificate verification",
            "config": {
                "ssl_ca": "/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend/app/certs/DigiCertGlobalRootG2.crt",
                "ssl_disabled": False
            }
        },
        {
            "name": "SSL without certificate verification",
            "config": {
                "ssl_disabled": False,
                "ssl_verify_cert": False,
                "ssl_verify_identity": False
            }
        },
        {
            "name": "SSL with CERT_NONE equivalent",
            "config": {
                "ssl_disabled": False
            }
        }
    ]
    
    for ssl_config in ssl_configs:
        print(f"🧪 Testing: {ssl_config['name']}")
        print("-" * 40)
        
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database,
                connect_timeout=30,
                **ssl_config['config']
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT USER() as current_user")
                user_info = cursor.fetchone()
                
                cursor.execute("SELECT VERSION() as version")
                version = cursor.fetchone()
                
                cursor.execute("SELECT DATABASE() as current_db")
                current_db = cursor.fetchone()
                
                cursor.execute("SHOW STATUS LIKE 'Ssl_cipher'")
                ssl_status = cursor.fetchone()
                
                cursor.execute("SELECT CONNECTION_ID() as connection_id")
                conn_id = cursor.fetchone()
            
            connection.close()
            
            print(f"   ✅ SUCCESS!")
            print(f"   👤 Connected as: {user_info[0]}")
            print(f"   📊 MySQL Version: {version[0]}")
            print(f"   📂 Database: {current_db[0]}")
            print(f"   🔐 SSL Cipher: {ssl_status[1] if ssl_status and ssl_status[1] else 'Not active'}")
            print(f"   🔗 Connection ID: {conn_id[0]}")
            print()
            print(f"🎉 WORKING CONFIGURATION FOUND!")
            print(f"✅ Username: '{username}'")
            print(f"✅ SSL Config: {ssl_config['name']}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
        
        print()
    
    return False

def test_mysql_client_simple_username():
    """Test simple username with MySQL client"""
    
    print("🔧 Testing Simple Username with MySQL Client")
    print("=" * 50)
    
    import subprocess
    
    host = settings.MYSQL_HOST
    password = settings.MYSQL_PASSWORD
    database = settings.MYSQL_DATABASE
    username = "tech0gen10student"
    
    mysql_client = "/opt/homebrew/opt/mysql-client@8.4/bin/mysql"
    
    # Test with SSL required
    print(f"🧪 MySQL Client Test: '{username}' with SSL")
    print("-" * 40)
    
    try:
        cmd = [
            mysql_client,
            "-h", host,
            "-u", username,
            f"-p{password}",
            "-D", database,
            "--ssl-mode=REQUIRED",
            "--ssl-ca=/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend/app/certs/DigiCertGlobalRootG2.crt",
            "-e", "SELECT USER() as current_user, VERSION() as version, CONNECTION_ID() as conn_id;"
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
            return True
        else:
            print(f"   ❌ Failed:")
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    print(f"      {line}")
                    
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("🚀 Testing Simple Username Format with SSL")
    print("=" * 60)
    
    # Test PyMySQL
    pymysql_success = test_simple_username_with_ssl()
    
    # Test MySQL client
    if not pymysql_success:
        mysql_client_success = test_mysql_client_simple_username()
    
    if pymysql_success:
        print(f"\n🎯 SOLUTION: Update .env to use simple username")
        print(f"MYSQL_USER=tech0gen10student")
    else:
        print(f"\n❌ Simple username format also failed")
        print(f"This suggests the issue is with credentials or firewall rules")