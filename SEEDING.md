# Demo Data Seeding Guide

This guide explains how to safely generate and manage demo data for the BtoB Energy Management System dashboard visualization.

## 🚨 Safety First

**IMPORTANT**: These scripts include multiple safety measures to prevent accidental data corruption:

1. **Environment Variable Guard**: Scripts only run when `SEED_ALLOW=1` is set
2. **Company Isolation**: Data is scoped by company_id to prevent cross-contamination
3. **Transaction Safety**: Operations use transactions with rollback on failure
4. **Schema Validation**: Automatic Alembic migration check before seeding

## 📋 Overview

The seeding system generates realistic dummy data including:

- **Companies**: SCOPE3_HOLDINGS (ID: 1), TECH0_INC (ID: 2)
- **Users**: 200 per company with Japanese names and realistic email addresses
- **Devices**: Electric and gas meters (1-2 per user)
- **Reduction Records**: 12 months of energy usage with seasonality and YoY trends
- **Points System**: Automatic point calculation based on CO₂ reduction achievements
- **Rewards & Redemptions**: Sample rewards catalog and user redemption history
- **Reports**: Quarterly/annual CO₂ reduction reports

## 🏗️ Data Characteristics

### Seasonality Patterns
- **Electricity**: Higher usage in summer (cooling) and winter (heating)
- **Gas**: Higher usage in winter (heating)
- **Random Variation**: ±15% noise to simulate real-world fluctuations

### Year-over-Year Trends
- **Primary Trend**: 3-12% reduction from previous year
- **Outliers**: 10% of users show 0-5% increase (realistic for growing operations)

### CO₂ Calculations
- **Electricity**: 0.441 kg-CO₂/kWh
- **Gas**: 2.23 kg-CO₂/m³
- **Points**: 1 point per 1 kg CO₂ reduced

### Company Boundaries
- All data is strictly isolated by `company_id`
- Users can only see data from their own company
- APIs enforce company-based access control

## 🛠️ Installation & Setup

### Prerequisites

1. **Database**: MySQL/MariaDB running with existing schema
2. **Environment**: FastAPI backend environment set up
3. **Dependencies**: All required Python packages installed
4. **Migrations**: Alembic schema up to date (automatic check included)

### Local Environment

```bash
cd /Users/tanakatsuyoshi/Desktop/アプリ開発/step3-2_BtoB_backend

# Set safety flag
export SEED_ALLOW=1

# Run seeding with default parameters
python -m app.seeds.seed_demo

# Run with custom parameters
python -m app.seeds.seed_demo --users 150 --months 18 --seed 123
```

### Azure Kudu Console

```bash
cd /home/site/wwwroot

# Set Python path
export PYTHONPATH="/home/site/wwwroot/.python_packages/lib/site-packages:$PYTHONPATH"

# Set safety flag (IMPORTANT: Do not add to App Settings!)
export SEED_ALLOW=1

# Run seeding
python3 -m app.seeds.seed_demo --company-codes SCOPE3_HOLDINGS,TECH0_INC --users 200 --months 12
```

## 📖 Usage Guide

### Seeding Script (`seed_demo.py`)

#### Basic Usage
```bash
export SEED_ALLOW=1
python -m app.seeds.seed_demo
```

#### Advanced Options
```bash
python -m app.seeds.seed_demo \
  --company-codes SCOPE3_HOLDINGS,TECH0_INC \
  --users 200 \
  --months 12 \
  --seed 42 \
  --replace
```

#### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--company-codes` | `SCOPE3_HOLDINGS,TECH0_INC` | Comma-separated company codes |
| `--users` | `200` | Number of users per company |
| `--months` | `12` | Number of months of historical data |
| `--seed` | `42` | Random seed for reproducible results |
| `--replace` | `False` | Replace existing data (delete first) |

#### Output Example
```
[2025-08-19 17:15:23] INFO: ✅ SEED_ALLOW=1 confirmed. Proceeding with seeding.
[2025-08-19 17:15:24] INFO: ✅ Database schema is up to date.
[2025-08-19 17:15:24] INFO: 🏢 Seeding data for SCOPE3_HOLDINGS (ID: 1)
[2025-08-19 17:15:25] INFO: 👥 Creating 200 users for SCOPE3_HOLDINGS...
[2025-08-19 17:15:28] INFO: ⚡ Creating devices...
[2025-08-19 17:15:30] INFO: 📊 Creating reduction records...
[2025-08-19 17:15:35] INFO: 💰 Creating points ledger...
[2025-08-19 17:15:37] INFO: 🎉 SEEDING COMPLETED SUCCESSFULLY!
[2025-08-19 17:15:37] INFO: 📊 Summary:
[2025-08-19 17:15:37] INFO:    Companies: 2
[2025-08-19 17:15:37] INFO:    Users: 400
[2025-08-19 17:15:37] INFO:    Devices: 600
[2025-08-19 17:15:37] INFO:    Reduction Records: 19200
[2025-08-19 17:15:37] INFO:    Duration: 14.2 seconds
```

### Cleanup Script (`clear_demo.py`)

#### Basic Usage
```bash
export SEED_ALLOW=1
python -m app.seeds.clear_demo
```

#### Dry Run (Recommended First)
```bash
python -m app.seeds.clear_demo --dry-run
```

#### Full Cleanup
```bash
python -m app.seeds.clear_demo --include-rewards
```

#### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--company-codes` | `SCOPE3_HOLDINGS,TECH0_INC` | Companies to clear |
| `--include-rewards` | `False` | Also clear global rewards |
| `--dry-run` | `False` | Show what would be deleted |

## ✅ Validation & Testing

### Automatic API Validation

The seeding script automatically validates the generated data by testing all metrics APIs:

1. **KPI Metrics** (`/api/v1/metrics/kpi`)
2. **Monthly Usage** (`/api/v1/metrics/monthly-usage`)
3. **CO₂ Trend** (`/api/v1/metrics/co2-trend`)
4. **Year-over-Year** (`/api/v1/metrics/yoy-usage`)

### Manual Dashboard Verification

After seeding, verify the dashboard displays data:

1. **Production URL**: https://app-002-gen10-step3-2-node-oshima2.azurewebsites.net/dashboard
2. **Local URL**: http://localhost:3000/dashboard

Expected dashboard elements:
- ✅ 4 KPI cards with non-zero values
- ✅ Monthly usage bar chart (12 months)
- ✅ CO₂ reduction line chart
- ✅ Year-over-year comparison chart

### Company Isolation Test

To verify company boundaries:

1. Log in as user from SCOPE3_HOLDINGS
2. Verify only SCOPE3_HOLDINGS data is visible
3. Log in as user from TECH0_INC
4. Verify only TECH0_INC data is visible

## ⚠️ Important Warnings

### Production Safety

1. **Never add SEED_ALLOW to App Settings** - Only use temporarily in console
2. **Always run dry-run first** when clearing data
3. **Backup data** before any seeding operation
4. **Test in staging** before production seeding

### Known Limitations

1. **No Company Model**: Companies are identified by integer IDs only
2. **Fixed CO₂ Factors**: Using standard Japanese emission factors
3. **Simplified Seasonality**: Basic seasonal patterns, not region-specific
4. **Demo Users Only**: All users have same password: "password123"

### Troubleshooting

#### Common Issues

**"SEED_ALLOW=1 not set"**
```bash
export SEED_ALLOW=1  # Must be set in same terminal session
```

**"Can't connect to MySQL"**
```bash
# Check database connection in .env file
cat .env | grep MYSQL
```

**"Alembic upgrade warning"**
```bash
# Manually run Alembic if needed
alembic upgrade head
```

**"API validation failed"**
```bash
# Check if backend server is running
curl http://localhost:8000/health
```

#### Log Analysis

All operations produce detailed logs with timestamps:
- `INFO`: Normal operations
- `WARN`: Non-fatal warnings
- `ERROR`: Fatal errors requiring attention

## 📊 Expected Results

After successful seeding with default parameters:

### Database Records
- **Users**: 400 total (200 per company)
- **Employees**: 400 total
- **Devices**: ~600 total (1-2 per user)
- **Reduction Records**: ~19,200 total (2 energy types × 12 months × 2 years × 400 users)
- **Points Entries**: ~4,800 total (12 months × 400 users)
- **Rewards**: 10 global rewards
- **Redemptions**: ~130 total (30% of users)

### Metrics API Responses
- **Active Users**: 200 per company
- **Electricity Usage**: 50,000-200,000 kWh per company per month
- **Gas Usage**: 8,000-40,000 m³ per company per month
- **CO₂ Reduction**: 15,000-60,000 kg per company (total)

### Dashboard Visualization
- **KPI Cards**: Show aggregated values for current month
- **Bar Chart**: 12 months of electricity/gas usage
- **Line Chart**: CO₂ reduction trend over time
- **Comparison Chart**: Current vs previous year usage

## 🔧 Maintenance

### Regular Tasks

1. **Monthly Data Refresh**: Re-run seeding to add current month data
2. **Performance Monitoring**: Check dashboard load times with full dataset
3. **Data Cleanup**: Remove old test data before major updates

### Schema Updates

When database schema changes:

1. Update models in `app/models/`
2. Create Alembic migration
3. Update seeding scripts if needed
4. Test with `--dry-run` first

---

## 📞 Support

For issues with seeding:

1. Check this documentation
2. Review log messages for specific errors
3. Test with `--dry-run` to understand impact
4. Verify `SEED_ALLOW=1` is set correctly

**Remember**: These scripts are designed for demo data only. Never run against production data without explicit approval and backup procedures.