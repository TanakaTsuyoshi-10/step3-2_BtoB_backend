# Seeding Scripts Documentation

This directory contains consolidated seeding scripts for the BtoBtoC energy management system. All scripts include proper error handling, retry logic, and safety measures.

## 🚀 Quick Start

### Complete Seeding (Recommended)

```bash
# Navigate to project root (正規パス)
cd "/Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend"

# Set safety environment variable
export SEED_ALLOW=1

# Run complete seeding process
python scripts/seeding/seed_master.py --url "https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net"
```

### Individual Script Examples

```bash
# Create admin user
python scripts/seeding/create_admin.py \
  --url "https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net" \
  --email "admin@example.com" \
  --password "admin123"

# Create test users
python scripts/seeding/create_test_user.py \
  --url "https://app-002-gen10-step3-2-py-oshima2.azurewebsites.net" \
  --test-suite

# Seed database with demo data
python scripts/seeding/seed_database.py \
  --action seed \
  --company-id 1 \
  --user-count 20
```

This will create:
- Admin user with proper permissions
- Test users for frontend development
- 20 demo users with realistic data
- 12 months of historical energy data
- Points, rankings, and rewards

### Available Accounts After Seeding

- **Admin**: `admin@example.com` / `admin123`
- **Test User**: `testuser@example.com` / `password123`
- **Demo Users**: `demo.user001@scope3holdings.co.jp` / `demo123` (and more)

## 📁 Scripts Overview

### 1. Master Script

**`seed_master.py`** - Orchestrates the complete seeding process

```bash
# Complete seeding with default settings
python scripts/seeding/seed_master.py

# Custom settings
python scripts/seeding/seed_master.py \
  --url "https://your-app.azurewebsites.net" \
  --company-id 1 \
  --user-count 50 \
  --clear-first
```

**Options:**
- `--url`: API base URL (default: production URL)
- `--admin-email`: Admin email (default: admin@example.com)
- `--admin-password`: Admin password (default: admin123)
- `--company-id`: Target company ID (default: 1)
- `--user-count`: Number of demo users (default: 20)
- `--no-test-suite`: Skip test user creation
- `--clear-first`: Clear existing demo data first

### 2. API-Based User Creation

**`create_admin.py`** - Create admin user with superuser privileges

```bash
# Create admin with defaults
python scripts/seeding/create_admin.py

# Custom admin
python scripts/seeding/create_admin.py \
  --email "admin@company.com" \
  --password "secure123" \
  --company-id 2

# Verify existing admin
python scripts/seeding/create_admin.py --verify-only
```

**`create_employee.py`** - Create employee users via admin API

```bash
# Create single employee
python scripts/seeding/create_employee.py \
  --email "employee@company.com" \
  --full-name "田中太郎" \
  --department "営業部" \
  --employee-code "EMP001"

# Verify existing employee
python scripts/seeding/create_employee.py \
  --email "employee@company.com" \
  --verify-only

# Batch creation from JSON
python scripts/seeding/create_employee.py --batch-file employees.json
```

**`create_test_user.py`** - Create test users for frontend development

```bash
# Create test user with defaults
python scripts/seeding/create_test_user.py

# Create complete test suite
python scripts/seeding/create_test_user.py --test-suite

# Custom test user
python scripts/seeding/create_test_user.py \
  --email "test@example.com" \
  --password "test123" \
  --full-name "テストユーザー"
```

### 3. Database-Level Seeding

**`seed_database.py`** - Direct database seeding with realistic data

```bash
# Seed complete dataset
python scripts/seeding/seed_database.py \
  --action seed \
  --company-id 1 \
  --user-count 20 \
  --months-back 12

# Clear demo data
python scripts/seeding/seed_database.py \
  --action clear \
  --company-id 1 \
  --confirm-clear
```

**Options:**
- `--action`: `seed` or `clear`
- `--company-id`: Target company ID
- `--user-count`: Number of demo users to create
- `--months-back`: Months of historical data
- `--devices-per-user`: Devices per user (default: 2)
- `--confirm-clear`: Required for clear action

## 🔒 Safety Features

### Environment Variable Guard

All scripts require the `SEED_ALLOW` environment variable:

```bash
export SEED_ALLOW=1
```

This prevents accidental execution in production environments.

### Company Isolation

All operations are scoped to specific company IDs to prevent cross-company data contamination.

### Transaction Safety

Database operations use transactions with automatic rollback on errors.

### Retry Logic

API operations include exponential backoff retry logic for network resilience.

## 📊 Generated Data

### Realistic Energy Data

- **Seasonality**: Higher consumption in winter/summer
- **Daily Variation**: Random daily fluctuations
- **Device Types**: Smart meters, HVAC, lighting systems
- **CO2 Calculations**: Accurate conversion factors

### Points and Achievements

- Based on energy reduction percentages
- Monthly achievement tracking
- Realistic point values (10 points per 1% reduction)

### Rankings

- Calculated from total user points
- Company-scoped rankings
- Historical period tracking

### Rewards

- Sample eco-friendly rewards
- Point-based redemption system
- Company-specific reward catalogs

## 🔧 Troubleshooting

### Common Issues

**403 Forbidden Errors**
- User lacks employee record for company association
- Run admin user creation to fix permissions

**Email Validation Errors**
- Use domains without underscores
- Example: `@scope3holdings.co.jp` instead of `@scope3_holdings.co.jp`

**Database Connection Errors**
- Verify environment variables are set
- Check database server availability

**API Timeout Errors**
- Increase timeout with `--timeout` parameter
- Check network connectivity

### Debug Mode

For detailed debugging, run scripts individually and check outputs:

```bash
# Enable Python debugging
export PYTHONPATH=/path/to/project
python -v scripts/seeding/script_name.py
```

### Verification

After seeding, verify the results:

```bash
# Verify admin access
python scripts/seeding/create_admin.py --verify-only

# Verify test user access
python scripts/seeding/create_test_user.py --verify-only

# Check database counts
python -c "
from app.db.database import SessionLocal
from app.models import User, Employee, Device, EnergyRecord
db = SessionLocal()
print(f'Users: {db.query(User).count()}')
print(f'Employees: {db.query(Employee).count()}')
print(f'Devices: {db.query(Device).count()}')
print(f'Energy Records: {db.query(EnergyRecord).count()}')
db.close()
"
```

## 🌐 Production Deployment

### Environment Setup

```bash
# Production environment variables
export SEED_ALLOW=1
export MYSQL_HOST="your-mysql-host"
export MYSQL_USER="your-mysql-user"
export MYSQL_PASSWORD="your-mysql-password"
export MYSQL_DATABASE="your-database"
export SECRET_KEY="your-secret-key"
```

### GitHub Actions Integration

The scripts can be integrated into GitHub Actions workflows:

```yaml
name: Seed Production Data
on:
  workflow_dispatch:

jobs:
  seed:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - run: pip install -r requirements.txt
    - run: |
        export SEED_ALLOW=1
        python scripts/seeding/seed_master.py
      env:
        MYSQL_HOST: ${{ secrets.MYSQL_HOST }}
        MYSQL_USER: ${{ secrets.MYSQL_USER }}
        MYSQL_PASSWORD: ${{ secrets.MYSQL_PASSWORD }}
        MYSQL_DATABASE: ${{ secrets.MYSQL_DATABASE }}
        SECRET_KEY: ${{ secrets.SECRET_KEY }}
```

### Database Migration

Before seeding, ensure database is properly migrated:

```bash
# Run migrations
alembic upgrade head

# Then run seeding
export SEED_ALLOW=1
python scripts/seeding/seed_master.py
```

## 📈 Performance Considerations

### Batch Processing

- Database operations are batched for efficiency
- Progress indicators for long operations
- Memory-efficient data generation

### Network Optimization

- Connection pooling with requests.Session()
- Configurable timeouts
- Retry logic with exponential backoff

### Resource Limits

- Default limits: 20 users, 12 months data
- Configurable via command line parameters
- Monitor database storage usage

## 🔄 Maintenance

### Regular Cleanup

```bash
# Clear old demo data monthly
export SEED_ALLOW=1
python scripts/seeding/seed_database.py \
  --action clear \
  --company-id 1 \
  --confirm-clear

# Re-seed with fresh data
python scripts/seeding/seed_master.py --clear-first
```

### Monitoring

Monitor seeding operations:

- Check log outputs for errors
- Monitor database size growth
- Verify API response times
- Check user login success rates

## 📞 Support

For issues with the seeding scripts:

1. Check the troubleshooting section above
2. Verify environment variables are set correctly
3. Run individual scripts to isolate problems
4. Check database connectivity and permissions

The scripts are designed to be robust and provide detailed error messages to help with diagnosis.