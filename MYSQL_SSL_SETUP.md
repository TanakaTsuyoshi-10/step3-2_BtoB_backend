# Azure MySQL SSL Connection Setup

This document explains how to configure FastAPI to connect to Azure Database for MySQL using SSL certificates.

## 🔧 Configuration Complete

### ✅ What Has Been Set Up

1. **SSL Certificate**: Downloaded DigiCert Global Root G2 certificate to `app/certs/DigiCertGlobalRootG2.crt`
2. **Environment Variables**: Added MySQL configuration support in `.env`
3. **Database Configuration**: Updated `app/core/config.py` to build connection URLs with SSL
4. **Database Connection**: Modified `app/db/database.py` to use new configuration
5. **Alembic Integration**: Updated `alembic/env.py` to use new database URL builder
6. **Connection Test**: Created `test_mysql_connection.py` for verification

### 📋 Environment Variables Added

```bash
# Database - Azure Database for MySQL Flexible Server
MYSQL_HOST=rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com
MYSQL_PORT=3306
MYSQL_USER=youruser@rdbs-002-gen10-step3-2-oshima2
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=test_tanaka
MYSQL_SSL_CA=app/certs/DigiCertGlobalRootG2.crt
```

## 🔑 Required Steps to Complete Setup

### 1. Update Credentials in .env

Replace the placeholder values in `.env` with your actual Azure MySQL credentials:

```bash
MYSQL_USER=your_actual_username@rdbs-002-gen10-step3-2-oshima2
MYSQL_PASSWORD=your_actual_password
```

### 2. Verify Azure MySQL Firewall

Ensure your IP address is allowed in the Azure MySQL firewall rules:
- Go to Azure Portal → Your MySQL Server → Networking
- Add your current IP address to the firewall rules
- Or enable "Allow Azure services" if deploying to Azure

### 3. Test Connection

```bash
# Test the MySQL connection
python test_mysql_connection.py
```

### 4. Run Database Migrations

```bash
# Create database schema
alembic upgrade head
```

### 5. Start FastAPI Server

```bash
# Start the server
uvicorn app.main:app --reload
```

## 🔒 SSL Configuration Features

### Automatic SSL Certificate Handling
- Detects certificate file existence
- Generates appropriate SSL parameters
- Falls back gracefully if certificate not found

### Database URL Generation
The system automatically builds the MySQL connection URL with SSL parameters:

```python
# Example generated URL (password hidden):
mysql+pymysql://user:***@host:3306/db?ssl_ca=/path/to/cert&ssl_disabled=false
```

### Flexible Configuration
Supports both:
1. **Individual components** (recommended for Azure):
   ```bash
   MYSQL_HOST=...
   MYSQL_USER=...
   MYSQL_PASSWORD=...
   ```

2. **Legacy DATABASE_URL** (for compatibility):
   ```bash
   DATABASE_URL=mysql+pymysql://...
   ```

## 🧪 Connection Test Example

```bash
$ python test_mysql_connection.py

🚀 Azure MySQL Connection Test Suite
============================================================
📋 Configuration Summary:
   MySQL Host: rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com
   MySQL Port: 3306
   MySQL User: youruser@rdbs-002-gen10-step3-2-oshima2
   MySQL Database: test_tanaka
   SSL Certificate: app/certs/DigiCertGlobalRootG2.crt

🔧 MySQL Connection Test for Azure Database
==================================================
🔐 SSL Certificate: Found at /path/to/cert
   ✅ Certificate format appears valid

🔌 Testing database connection...
   ✅ Basic connection successful: (1,)
   🔐 SSL Connection: ACTIVE (Cipher: ECDHE-RSA-AES256-GCM-SHA384)
   📂 Current Database: test_tanaka
   📋 Existing tables: users, devices, energy_records
   🔖 MySQL Version: 8.0.21
   🖥️  Server Hostname: rdbs-002-gen10-step3-2-oshima2

✅ All connection tests passed!
```

## 🔧 API Usage Examples

### Basic Connection Test in Code

```python
from app.core.config import settings
from app.db.database import engine
from sqlalchemy import text

# Test connection
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Connection successful:", result.fetchone())
```

### Using in FastAPI Endpoints

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

@app.get("/test-db")
def test_database_connection(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT DATABASE() as current_db")).fetchone()
    return {"database": result[0], "status": "connected"}
```

### SSL Connection Verification

```python
from app.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check SSL status
    result = conn.execute(text("SHOW STATUS LIKE 'Ssl_cipher'")).fetchone()
    if result and result[1]:
        print(f"SSL Active: {result[1]}")
    else:
        print("SSL not active")
```

## 🚨 Troubleshooting

### Common Issues

1. **Access Denied Error**
   ```
   (1045, "Access denied for user 'user'@'ip' (using password: YES)")
   ```
   **Solution**: Check username, password, and firewall rules

2. **SSL Certificate Not Found**
   ```
   Warning: SSL certificate file not found at /path/to/cert
   ```
   **Solution**: Verify certificate file exists at specified path

3. **Connection Timeout**
   ```
   (2003, "Can't connect to MySQL server")
   ```
   **Solution**: Check firewall rules and network connectivity

### Verification Commands

```bash
# Check certificate exists
ls -la app/certs/DigiCertGlobalRootG2.crt

# Test basic connectivity (replace with your credentials)
mysql -h rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com -u user@server -p

# Check current working directory for relative paths
pwd
```

## 📊 FastAPI Integration Status

✅ **Ready for Use**
- SSL certificate properly configured
- Database URL builder working
- Alembic migrations ready
- Connection pooling configured
- Error handling implemented

The FastAPI application is now configured to securely connect to Azure Database for MySQL using SSL certificates. Update your credentials in the `.env` file and test the connection!