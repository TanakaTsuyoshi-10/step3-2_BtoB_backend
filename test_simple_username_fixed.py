#!/usr/bin/env python3
"""
Test simple username format with fixed SQL syntax
"""

import pymysql
import subprocess
from app.core.config import settings

def test_simple_username_fixed():
    """Test simple username with corrected SQL queries"""
    
    print("🔐 Testing Simple Username with Fixed SQL")
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
    
    print(f"🧪 Testing SSL with certificate verification")
    print("-" * 40)
    
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            ssl_ca="/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend/app/certs/DigiCertGlobalRootG2.crt",
            ssl_disabled=False,
            connect_timeout=30
        )
        
        with connection.cursor() as cursor:
            # Fixed SQL queries
            cursor.execute("SELECT USER()")
            user_info = cursor.fetchone()
            
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            
            cursor.execute("SHOW STATUS LIKE 'Ssl_cipher'")
            ssl_status = cursor.fetchone()
            
            cursor.execute("SELECT CONNECTION_ID()")
            conn_id = cursor.fetchone()
            
            # Test a simple table query
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
        
        connection.close()
        
        print(f"   ✅ CONNECTION SUCCESSFUL!")
        print(f"   👤 Connected as: {user_info[0]}")
        print(f"   📊 MySQL Version: {version[0]}")
        print(f"   📂 Database: {current_db[0]}")
        print(f"   🔐 SSL Cipher: {ssl_status[1] if ssl_status and ssl_status[1] else 'Not active'}")
        print(f"   🔗 Connection ID: {conn_id[0]}")
        print(f"   📋 Available tables: {len(tables)} tables found")
        for table in tables:
            print(f"      - {table[0]}")
        
        print()
        print(f"🎉 SUCCESS! Working configuration found:")
        print(f"✅ Username: tech0gen10student")
        print(f"✅ SSL: Required with certificate verification")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        return False

def test_mysql_client_fixed():
    """Test with MySQL client using fixed syntax"""
    
    print("\n🔧 Testing MySQL Client with Fixed Syntax")
    print("=" * 50)
    
    host = settings.MYSQL_HOST
    password = settings.MYSQL_PASSWORD
    database = settings.MYSQL_DATABASE
    username = "tech0gen10student"
    
    mysql_client = "/opt/homebrew/opt/mysql-client@8.4/bin/mysql"
    
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
            "-e", "SELECT USER(), VERSION(), CONNECTION_ID();"
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

def update_env_file():
    """Update .env file with correct username"""
    
    print("\n📝 Updating .env file with correct username")
    print("=" * 50)
    
    env_path = "/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend/.env"
    
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update MYSQL_USER line
    updated_lines = []
    for line in lines:
        if line.strip().startswith('MYSQL_USER='):
            updated_lines.append('MYSQL_USER=tech0gen10student\n')
            print(f"   ✅ Updated: MYSQL_USER=tech0gen10student")
        else:
            updated_lines.append(line)
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print("   📁 .env file updated successfully")

if __name__ == "__main__":
    print("🚀 Testing Simple Username with Fixed SQL Syntax")
    print("=" * 60)
    
    # Test PyMySQL with fixed syntax
    success = test_simple_username_fixed()
    
    if success:
        # Update .env file
        update_env_file()
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. ✅ Username format confirmed: tech0gen10student")
        print(f"2. ✅ SSL configuration working")
        print(f"3. ✅ .env file updated")
        print(f"4. 🔄 Ready to test SQLAlchemy connection")
        print(f"5. 🔄 Ready to run Alembic migrations")
    else:
        # Test MySQL client as fallback
        mysql_success = test_mysql_client_fixed()
        
        if mysql_success:
            update_env_file()
            print(f"\n🎯 MySQL client test successful - updating .env")
        else:
            print(f"\n❌ Both tests failed - check credentials and firewall rules")