#!/usr/bin/env python3
"""
Debug Azure MySQL credentials and connection details
"""

import os
import socket
from app.core.config import settings

def debug_credentials():
    """Debug connection credentials and network connectivity"""
    
    print("🔍 Azure MySQL Connection Debug")
    print("=" * 50)
    
    # Display credentials (password masked)
    print("📋 Credentials Analysis:")
    print(f"   MYSQL_HOST: '{settings.MYSQL_HOST}'")
    print(f"   MYSQL_PORT: {settings.MYSQL_PORT}")
    print(f"   MYSQL_USER: '{settings.MYSQL_USER}'")
    print(f"   MYSQL_PASSWORD: {'*' * len(settings.MYSQL_PASSWORD) if settings.MYSQL_PASSWORD else 'None'}")
    print(f"   MYSQL_DATABASE: '{settings.MYSQL_DATABASE}'")
    print()
    
    # Check for whitespace issues
    print("🔍 Whitespace Analysis:")
    for field_name in ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_DATABASE']:
        value = getattr(settings, field_name)
        if value:
            original_len = len(value)
            stripped_len = len(value.strip())
            if original_len != stripped_len:
                print(f"   ⚠️  {field_name} has whitespace (original: {original_len}, stripped: {stripped_len})")
            else:
                print(f"   ✅ {field_name} looks clean")
    
    # Check password length and characters
    if settings.MYSQL_PASSWORD:
        password = settings.MYSQL_PASSWORD
        print(f"   🔑 Password length: {len(password)}")
        print(f"   🔑 Password starts with: '{password[0]}'")
        print(f"   🔑 Password ends with: '{password[-1]}'")
        
        # Check for special characters that might need encoding
        special_chars = set('@#$%^&*()+=[]{}|\\:";\'<>?,./`~')
        password_special = set(password) & special_chars
        if password_special:
            print(f"   🔑 Special characters in password: {sorted(password_special)}")
        else:
            print("   🔑 No special characters in password")
    print()
    
    # Test network connectivity
    print("🌐 Network Connectivity Test:")
    try:
        # Test DNS resolution
        import socket
        ip = socket.gethostbyname(settings.MYSQL_HOST)
        print(f"   ✅ DNS resolution: {settings.MYSQL_HOST} -> {ip}")
        
        # Test port connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((settings.MYSQL_HOST, settings.MYSQL_PORT))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {settings.MYSQL_PORT} is accessible")
        else:
            print(f"   ❌ Port {settings.MYSQL_PORT} is not accessible (error code: {result})")
            
    except Exception as e:
        print(f"   ❌ Network test failed: {e}")
    print()
    
    # Show generated database URL (password masked)
    print("🔗 Generated Database URL:")
    try:
        db_url = settings.get_database_url()
        # Mask password in URL for display
        if settings.MYSQL_PASSWORD:
            masked_url = db_url.replace(settings.MYSQL_PASSWORD, '***')
        else:
            masked_url = db_url
        print(f"   {masked_url}")
    except Exception as e:
        print(f"   ❌ Error generating URL: {e}")
    print()
    
    # Check .env file directly
    print("📄 .env File Analysis:")
    env_path = "/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        mysql_lines = [line for line in lines if line.strip().startswith('MYSQL_')]
        for line in mysql_lines:
            if 'PASSWORD' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    print(f"   {parts[0]}={'*' * len(parts[1].strip())}")
            else:
                print(f"   {line.strip()}")
    else:
        print("   ❌ .env file not found")

if __name__ == "__main__":
    debug_credentials()