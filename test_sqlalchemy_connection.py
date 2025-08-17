#!/usr/bin/env python3
"""
Test SQLAlchemy connection with corrected username
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.database import engine as app_engine

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection using the app configuration"""
    
    print("🔧 Testing SQLAlchemy Connection")
    print("=" * 50)
    
    # Test with the app's engine
    print("🧪 Testing with application engine")
    print("-" * 30)
    
    try:
        with app_engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT 1 as test")).fetchone()
            print(f"   ✅ Basic connectivity: {result[0]}")
            
            # Get version
            version_result = conn.execute(text("SELECT VERSION() as version")).fetchone()
            print(f"   📊 MySQL Version: {version_result[0]}")
            
            # Check SSL status
            ssl_result = conn.execute(text("SHOW STATUS LIKE 'Ssl_cipher'")).fetchone()
            print(f"   🔐 SSL Cipher: {ssl_result[1] if ssl_result and ssl_result[1] else 'Not active'}")
            
            # Check current user
            user_result = conn.execute(text("SELECT USER() as current_user")).fetchone()
            print(f"   👤 Connected as: {user_result[0]}")
            
            # Check current database
            db_result = conn.execute(text("SELECT DATABASE() as current_db")).fetchone()
            print(f"   📂 Current database: {db_result[0]}")
            
            # Check existing tables
            tables_result = conn.execute(text("SHOW TABLES")).fetchall()
            print(f"   📋 Existing tables: {len(tables_result)} found")
            for table in tables_result:
                print(f"      - {table[0]}")
        
        print("   ✅ SQLAlchemy connection successful!")
        return True
        
    except Exception as e:
        print(f"   ❌ SQLAlchemy connection failed: {str(e)}")
        return False

def test_database_url_generation():
    """Test the database URL generation"""
    
    print("\n🔗 Testing Database URL Generation")
    print("=" * 50)
    
    try:
        db_url = settings.get_database_url()
        # Mask password for display
        if settings.MYSQL_PASSWORD:
            masked_url = db_url.replace(settings.MYSQL_PASSWORD, '***')
        else:
            masked_url = db_url
        
        print(f"   📋 Generated URL: {masked_url}")
        
        # Test creating engine with generated URL
        test_engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "charset": "utf8mb4",
                "connect_timeout": 60,
            }
        )
        
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            print(f"   ✅ Engine creation and connection successful: {result[0]}")
        
        test_engine.dispose()
        return True
        
    except Exception as e:
        print(f"   ❌ URL generation or connection failed: {str(e)}")
        return False

def test_session_creation():
    """Test session creation and basic operations"""
    
    print("\n📊 Testing Session Creation")
    print("=" * 50)
    
    try:
        from app.db.database import SessionLocal
        
        # Create a session
        db = SessionLocal()
        
        # Test basic query
        result = db.execute(text("SELECT 1 as test")).fetchone()
        print(f"   ✅ Session query successful: {result[0]}")
        
        # Test connection info
        user_result = db.execute(text("SELECT USER()")).fetchone()
        print(f"   👤 Session user: {user_result[0]}")
        
        db_result = db.execute(text("SELECT DATABASE()")).fetchone()
        print(f"   📂 Session database: {db_result[0]}")
        
        db.close()
        print("   ✅ Session creation and cleanup successful!")
        return True
        
    except Exception as e:
        print(f"   ❌ Session creation failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 SQLAlchemy Connection Test Suite")
    print("=" * 60)
    
    print(f"📋 Configuration Summary:")
    print(f"   MySQL Host: {settings.MYSQL_HOST}")
    print(f"   MySQL Port: {settings.MYSQL_PORT}")
    print(f"   MySQL User: {settings.MYSQL_USER}")
    print(f"   MySQL Database: {settings.MYSQL_DATABASE}")
    print(f"   SSL Certificate: {settings.MYSQL_SSL_CA}")
    print()
    
    # Test SQLAlchemy connection
    sqlalchemy_success = test_sqlalchemy_connection()
    
    # Test URL generation
    url_success = test_database_url_generation()
    
    # Test session creation
    session_success = test_session_creation()
    
    print(f"\n🎯 Test Results Summary:")
    print(f"✅ SQLAlchemy Engine: {'PASS' if sqlalchemy_success else 'FAIL'}")
    print(f"✅ URL Generation: {'PASS' if url_success else 'FAIL'}")
    print(f"✅ Session Creation: {'PASS' if session_success else 'FAIL'}")
    
    if all([sqlalchemy_success, url_success, session_success]):
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ SQLAlchemy is ready for Alembic migrations")
        print(f"✅ Database connection is fully configured")
    else:
        print(f"\n❌ Some tests failed - check configuration")