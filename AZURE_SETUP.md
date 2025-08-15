# Azure Database Setup Guide

This guide helps you connect to the existing Azure Database for MySQL and run the initial migration.

## Database Information

- **Server**: rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com
- **Database**: test_tanaka
- **Portal URL**: https://portal.azure.com/#@admintech0jp.onmicrosoft.com/resource/subscriptions/9b680e6d-e5a6-4381-aad5-a30afcbc8459/resourceGroups/rg-001-gen10/providers/Microsoft.DBforMySQL/flexibleServers/rdbs-002-gen10-step3-2-oshima2/overview

## Setup Steps

### 1. Get Database Credentials

From the Azure Portal, you'll need:
- **Username**: Usually `admin` or similar (check in Azure Portal)
- **Password**: The password set when the database was created

### 2. Update Environment Configuration

Edit the `.env` file in the backend directory:

```bash
# Replace YOUR_USERNAME and YOUR_PASSWORD with actual credentials
DATABASE_URL=mysql+pymysql://YOUR_USERNAME:YOUR_PASSWORD@rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com:3306/test_tanaka?ssl_disabled=false
```

### 3. Test Database Connection

```bash
# Install dependencies first
pip install -r requirements.txt

# Test connection with Python
python -c "
from app.db.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1 as test')
        print('✅ Database connection successful!')
        print(f'Test result: {result.fetchone()}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### 4. Run Database Migrations

```bash
# Run Alembic migrations to create the schema
alembic upgrade head
```

This will create the following tables:
- `users` - User authentication and profiles
- `devices` - Energy devices (solar panels, batteries, etc.)
- `energy_records` - Time-series energy data

### 5. Verify Schema Creation

You can verify the tables were created by connecting to the database:

```bash
# Using MySQL command line (if available)
mysql -h rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com -u YOUR_USERNAME -p test_tanaka

# Or use Python to check
python -c "
from app.db.database import engine
with engine.connect() as conn:
    result = conn.execute('SHOW TABLES')
    tables = [row[0] for row in result]
    print('📊 Created tables:', tables)
"
```

### 6. Start the API Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Troubleshooting

### Connection Issues

1. **SSL Certificate Error**
   ```bash
   # Try with SSL disabled
   DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?ssl_disabled=true
   ```

2. **Firewall Issues**
   - Check Azure Portal firewall settings
   - Add your IP address to allowed IPs
   - Ensure "Allow Azure services" is enabled

3. **Authentication Error**
   - Verify username and password in Azure Portal
   - Check if the user has access to the specific database

### Migration Issues

1. **Table Already Exists**
   ```bash
   # If tables already exist, mark current state
   alembic stamp head
   ```

2. **Migration Conflicts**
   ```bash
   # Reset migrations and recreate
   alembic downgrade base
   alembic upgrade head
   ```

## Azure Portal Access

You can monitor and manage your database through the Azure Portal:
[https://portal.azure.com/#@admintech0jp.onmicrosoft.com/resource/subscriptions/9b680e6d-e5a6-4381-aad5-a30afcbc8459/resourceGroups/rg-001-gen10/providers/Microsoft.DBforMySQL/flexibleServers/rdbs-002-gen10-step3-2-oshima2/overview](https://portal.azure.com/#@admintech0jp.onmicrosoft.com/resource/subscriptions/9b680e6d-e5a6-4381-aad5-a30afcbc8459/resourceGroups/rg-001-gen10/providers/Microsoft.DBforMySQL/flexibleServers/rdbs-002-gen10-step3-2-oshima2/overview)

From here you can:
- View connection strings
- Manage firewall rules
- Monitor database performance
- Access server logs

## Next Steps

After successful database setup:

1. **Test API Endpoints**
   - Register a new user via `/docs`
   - Test authentication endpoints
   - Create sample devices and energy records

2. **Connect Frontend**
   - Ensure frontend `.env.local` points to backend
   - Start frontend with `npm run dev`
   - Test full application flow

3. **Production Deployment**
   - Update production environment variables
   - Deploy to Azure App Service
   - Configure CORS for production frontend URL