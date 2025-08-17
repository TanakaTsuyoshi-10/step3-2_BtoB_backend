#!/usr/bin/env python3
"""
Azure MySQL SSL Configuration Test Suite
Tests multiple SSL configurations to find working connection method
"""

import pymysql
import ssl
import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from app.core.config import settings

def test_ssl_configurations():
    """Test different SSL configurations for Azure MySQL"""
    
    print("🔐 Testing SSL Configurations for Azure MySQL")
    print("=" * 60)
    
    # Get connection parameters
    host = settings.MYSQL_HOST
    port = settings.MYSQL_PORT
    user = settings.MYSQL_USER
    password = settings.MYSQL_PASSWORD
    database = settings.MYSQL_DATABASE
    
    print(f"📋 Connection Parameters:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   User: {user}")
    print(f"   Database: {database}")
    print()
    
    # Test configurations
    configurations = [
        {
            "name": "1. SSL Required with Certificate Verification",
            "ssl": {
                "ssl_ca": "/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend/app/certs/DigiCertGlobalRootG2.crt",
                "ssl_disabled": False
            }
        },
        {
            "name": "2. SSL Required without Certificate Verification",
            "ssl": {
                "ssl_verify_cert": False,
                "ssl_verify_identity": False,
                "ssl_disabled": False
            }
        },
        {
            "name": "3. SSL with CERT_NONE verification",
            "ssl": {
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_disabled": False
            }
        },
        {
            "name": "4. SSL Required (Azure default)",
            "ssl": {
                "ssl_disabled": False
            }
        },
        {
            "name": "5. No SSL (should fail on Azure)",
            "ssl": {
                "ssl_disabled": True
            }
        }
    ]
    
    successful_configs = []
    
    for config in configurations:
        print(f"🧪 Testing: {config['name']}")
        print("-" * 50)
        
        try:
            # Test PyMySQL direct connection
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                **config['ssl']
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION() as version")
                version = cursor.fetchone()
                
                cursor.execute("SHOW STATUS LIKE 'Ssl_cipher'")
                ssl_status = cursor.fetchone()
                
                cursor.execute("SELECT DATABASE() as current_db")
                current_db = cursor.fetchone()
            
            connection.close()
            
            print(f"   ✅ Connection successful!")
            print(f"   📊 MySQL Version: {version[0]}")
            print(f"   🔐 SSL Status: {ssl_status[1] if ssl_status and ssl_status[1] else 'Not active'}")
            print(f"   📂 Database: {current_db[0]}")
            
            successful_configs.append(config)
            
        except Exception as e:
            print(f"   ❌ Connection failed: {str(e)}")
        
        print()
    
    # Test SQLAlchemy with successful configurations
    if successful_configs:
        print("🔧 Testing SQLAlchemy with successful configurations")
        print("=" * 60)
        
        for config in successful_configs:
            print(f"🧪 SQLAlchemy Test: {config['name']}")
            print("-" * 50)
            
            try:
                # Build connection URL with SSL parameters
                encoded_password = quote_plus(password)
                base_url = f"mysql+pymysql://{user}:{encoded_password}@{host}:{port}/{database}"
                
                # Add SSL parameters to URL
                ssl_params = []
                for key, value in config['ssl'].items():
                    if key == 'ssl_cert_reqs' and value == ssl.CERT_NONE:
                        ssl_params.append("ssl_cert_reqs=CERT_NONE")
                    elif key == 'ssl_verify_cert' and not value:
                        ssl_params.append("ssl_verify_cert=false")
                    elif key == 'ssl_verify_identity' and not value:
                        ssl_params.append("ssl_verify_identity=false")
                    elif key == 'ssl_ca' and value:
                        ssl_params.append(f"ssl_ca={value}")
                    elif key == 'ssl_disabled':
                        ssl_params.append(f"ssl_disabled={str(value).lower()}")
                
                if ssl_params:
                    db_url = base_url + "?" + "&".join(ssl_params)
                else:
                    db_url = base_url
                
                print(f"   📋 Connection URL: {db_url.replace(password, '***')}")
                
                # Test SQLAlchemy connection
                engine = create_engine(
                    db_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    connect_args={
                        "charset": "utf8mb4",
                        "connect_timeout": 60,
                    }
                )
                
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test")).fetchone()
                    version_result = conn.execute(text("SELECT VERSION() as version")).fetchone()
                    ssl_result = conn.execute(text("SHOW STATUS LIKE 'Ssl_cipher'")).fetchone()
                
                print(f"   ✅ SQLAlchemy connection successful!")
                print(f"   📊 Test query result: {result[0]}")
                print(f"   📊 MySQL Version: {version_result[0]}")
                print(f"   🔐 SSL Cipher: {ssl_result[1] if ssl_result and ssl_result[1] else 'Not active'}")
                
                engine.dispose()
                
            except Exception as e:
                print(f"   ❌ SQLAlchemy connection failed: {str(e)}")
            
            print()
    
    else:
        print("❌ No successful configurations found!")
        print("Please check:")
        print("1. Firewall rules in Azure MySQL")
        print("2. Username and password")
        print("3. SSL certificate configuration")

if __name__ == "__main__":
    test_ssl_configurations()