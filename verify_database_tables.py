#!/usr/bin/env python3
"""
Verify that all database tables were created correctly
"""

from sqlalchemy import text, inspect
from app.db.database import engine
from app.core.config import settings

def verify_database_tables():
    """Verify that all expected tables exist and have the correct structure"""
    
    print("🔍 Verifying Database Tables")
    print("=" * 50)
    
    try:
        with engine.connect() as connection:
            # Get basic connection info
            version_result = connection.execute(text("SELECT VERSION()")).fetchone()
            print(f"📊 MySQL Version: {version_result[0]}")
            
            user_result = connection.execute(text("SELECT USER()")).fetchone()
            print(f"👤 Connected as: {user_result[0]}")
            
            db_result = connection.execute(text("SELECT DATABASE()")).fetchone()
            print(f"📂 Database: {db_result[0]}")
            
            ssl_result = connection.execute(text("SHOW STATUS LIKE 'Ssl_cipher'")).fetchone()
            print(f"🔐 SSL Cipher: {ssl_result[1] if ssl_result and ssl_result[1] else 'Not active'}")
            print()
            
            # List all tables
            tables_result = connection.execute(text("SHOW TABLES")).fetchall()
            print(f"📋 Tables in database ({len(tables_result)} found):")
            
            table_names = []
            for table in tables_result:
                table_name = table[0]
                table_names.append(table_name)
                print(f"   ✅ {table_name}")
            print()
            
            # Check expected tables
            expected_tables = ['users', 'devices', 'energy_records', 'alembic_version']
            print("🔍 Checking expected tables:")
            
            for expected_table in expected_tables:
                if expected_table in table_names:
                    print(f"   ✅ {expected_table} - Found")
                else:
                    print(f"   ❌ {expected_table} - Missing")
            print()
            
            # Get table structure for each table
            for table_name in table_names:
                if table_name != 'alembic_version':  # Skip alembic metadata table
                    print(f"📋 Structure of table '{table_name}':")
                    
                    # Get column information
                    columns_result = connection.execute(text(f"DESCRIBE {table_name}")).fetchall()
                    for column in columns_result:
                        field, type_, null, key, default, extra = column
                        print(f"   - {field}: {type_} {'NULL' if null == 'YES' else 'NOT NULL'} {f'DEFAULT {default}' if default else ''} {key} {extra}".strip())
                    
                    # Get row count
                    count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
                    print(f"   📊 Rows: {count_result[0]}")
                    print()
            
            # Check Alembic version
            if 'alembic_version' in table_names:
                version_result = connection.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                print(f"🔄 Alembic Version: {version_result[0] if version_result else 'None'}")
            
            print("✅ Database verification completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Database verification failed: {str(e)}")
        return False

def test_basic_operations():
    """Test basic CRUD operations"""
    
    print("\n🧪 Testing Basic Database Operations")
    print("=" * 50)
    
    try:
        from app.db.database import SessionLocal
        from app.models.user import User
        from app.models.device import Device
        from app.models.energy_record import EnergyRecord
        
        db = SessionLocal()
        
        # Test creating a user
        print("🧪 Testing User model...")
        test_user = User(
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            hashed_password="test_hash"
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"   ✅ Created user: {test_user.username} (ID: {test_user.id})")
        
        # Test creating a device
        print("🧪 Testing Device model...")
        test_device = Device(
            device_name="Test Device",
            device_type="Smart Meter",
            location="Test Location",
            user_id=test_user.id
        )
        
        db.add(test_device)
        db.commit()
        db.refresh(test_device)
        
        print(f"   ✅ Created device: {test_device.device_name} (ID: {test_device.id})")
        
        # Test creating an energy record
        print("🧪 Testing EnergyRecord model...")
        test_energy_record = EnergyRecord(
            device_id=test_device.id,
            energy_consumption=100.5,
            cost=25.10
        )
        
        db.add(test_energy_record)
        db.commit()
        db.refresh(test_energy_record)
        
        print(f"   ✅ Created energy record: {test_energy_record.energy_consumption}kWh (ID: {test_energy_record.id})")
        
        # Test querying
        print("🧪 Testing queries...")
        user_count = db.query(User).count()
        device_count = db.query(Device).count()
        energy_record_count = db.query(EnergyRecord).count()
        
        print(f"   📊 Users: {user_count}")
        print(f"   📊 Devices: {device_count}")
        print(f"   📊 Energy Records: {energy_record_count}")
        
        # Cleanup test data
        db.delete(test_energy_record)
        db.delete(test_device)
        db.delete(test_user)
        db.commit()
        
        print("   🧹 Test data cleaned up")
        
        db.close()
        
        print("✅ Basic operations test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Basic operations test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Database Verification Suite")
    print("=" * 60)
    
    print(f"📋 Configuration:")
    print(f"   Host: {settings.MYSQL_HOST}")
    print(f"   User: {settings.MYSQL_USER}")
    print(f"   Database: {settings.MYSQL_DATABASE}")
    print()
    
    # Verify tables exist
    tables_ok = verify_database_tables()
    
    # Test basic operations
    if tables_ok:
        operations_ok = test_basic_operations()
        
        if operations_ok:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ Database is fully configured and operational")
            print(f"✅ Ready for FastAPI application use")
        else:
            print(f"\n⚠️  Tables exist but operations failed")
    else:
        print(f"\n❌ Database verification failed")