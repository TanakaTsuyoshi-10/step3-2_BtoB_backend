# Energy Management System - Backend API

FastAPI-based REST API for the Energy Management System, providing comprehensive energy monitoring and device management capabilities.

## Features

- **RESTful API**: Complete CRUD operations for users, devices, and energy records
- **JWT Authentication**: Secure user authentication and authorization
- **Database Integration**: SQLAlchemy ORM with Azure Database for MySQL
- **Data Validation**: Pydantic schemas for request/response validation
- **Auto Documentation**: Swagger/OpenAPI documentation
- **Energy Analytics**: Production, consumption, and grid interaction tracking

## Technology Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations
- **Pydantic**: Data validation and serialization
- **python-jose**: JWT token handling
- **Passlib**: Password hashing
- **PyMySQL**: MySQL database connector

## Quick Start

### Prerequisites
- Python 3.11+
- Access to Azure Database for MySQL
- Virtual environment tool (venv)

### Installation

1. **Clone and setup**
   ```bash
   git clone https://github.com/TanakaTsuyoshi-10/step3-2_BtoB_backend.git
   cd step3-2_BtoB_backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## Database Configuration

### Azure Database for MySQL Setup

Update your `.env` file with the Azure MySQL connection string:

```bash
DATABASE_URL=mysql+pymysql://username:password@rdbs-002-gen10-step3-2-oshima2.mysql.database.azure.com:3306/test_tanaka?ssl_disabled=false
SECRET_KEY=your-secret-key-here
```

### Running Migrations

```bash
# Create a new migration (after model changes)
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

## API Documentation

### Authentication Endpoints
- `POST /api/v1/login/access-token` - User login
- `POST /api/v1/users/` - User registration
- `GET /api/v1/users/me` - Get current user profile

### Device Management
- `GET /api/v1/devices/` - List user devices
- `POST /api/v1/devices/` - Create new device
- `PUT /api/v1/devices/{id}` - Update device
- `DELETE /api/v1/devices/{id}` - Delete device

### Energy Records
- `GET /api/v1/energy-records/` - List energy records
- `POST /api/v1/energy-records/` - Create energy record
- `GET /api/v1/energy-records/daily-summary` - Get daily summary
- `PUT /api/v1/energy-records/{id}` - Update energy record

## Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API routes
│   │   ├── endpoints/    # Individual endpoint files
│   │   └── api.py        # Route aggregation
│   ├── auth/             # Authentication logic
│   ├── core/             # Core configurations
│   ├── db/               # Database connection
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py            # Alembic configuration
├── requirements.txt      # Python dependencies
└── .env.example          # Environment template
```

## Database Models

### User
- User authentication and profile management
- Relationships with devices and energy records

### Device
- Energy devices (solar panels, batteries, inverters)
- Device specifications and status tracking

### EnergyRecord
- Time-series energy data
- Production, consumption, and grid interaction metrics

## Development

### Adding New Features

1. **Create/Update Models**
   ```bash
   # Edit files in app/models/
   alembic revision --autogenerate -m "Add new model"
   alembic upgrade head
   ```

2. **Create Schemas**
   ```bash
   # Add Pydantic schemas in app/schemas/
   ```

3. **Implement Services**
   ```bash
   # Add business logic in app/services/
   ```

4. **Create API Endpoints**
   ```bash
   # Add routes in app/api/v1/endpoints/
   ```

### Testing

```bash
# Run tests (when test suite is available)
pytest

# Run with coverage
pytest --cov=app tests/
```

## Environment Variables

```bash
# Database
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?ssl_disabled=false

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - Use JSON string format for Azure compatibility
ALLOWED_ORIGINS=["http://localhost:3000","https://your-frontend.example.com"]
```

## Azure Deployment Fixes

### Recent Stability Improvements

This backend includes several fixes for Azure App Service deployment issues:

#### 1. Oryx Virtual Environment Path Fix
- **Problem**: Azure Oryx creates venv at `/tmp/<random>/antenv` instead of expected `/home/site/wwwroot/antenv`
- **Solution**: Updated startup command to use `python -m gunicorn` instead of hardcoded paths

#### 2. Dependencies and Module Import Fix
- **Problem**: Missing `uvicorn` module causing ModuleNotFoundError
- **Solution**: Updated `requirements.txt` with flexible version constraints:
  - `fastapi~=0.115`
  - `uvicorn[standard]~=0.30` 
  - `gunicorn~=21.2`

#### 3. ALLOWED_ORIGINS Type Compatibility
- **Problem**: Environment variable type mismatch between string and list
- **Solution**: Enhanced parser in `app/core/config.py` to handle both JSON strings and comma-separated values

#### 4. Production Startup Command
Azure App Service now uses this optimized startup command:
```bash
python -m gunicorn -k uvicorn.workers.UvicornWorker -w 1 --timeout 180 --graceful-timeout 30 --keep-alive 5 app.main:app --bind=0.0.0.0:${PORT:-8000}
```

#### 5. GitHub Actions Automation
- Automated deployment through GitHub Actions
- Azure CLI configuration for app settings
- Health check verification after deployment

### Local Development vs Production
- **Local**: `uvicorn app.main:app --reload`
- **Production**: `python -m gunicorn` with Uvicorn workers

## Deployment

### Azure App Service

1. **Create App Service**
   ```bash
   az webapp create \
     --resource-group your-rg \
     --plan your-plan \
     --name your-app-name \
     --runtime "PYTHON|3.11"
   ```

2. **Configure Environment Variables**
   ```bash
   az webapp config appsettings set \
     --resource-group your-rg \
     --name your-app-name \
     --settings DATABASE_URL="your-connection-string"
   ```

3. **Deploy**
   ```bash
   git push azure main
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.