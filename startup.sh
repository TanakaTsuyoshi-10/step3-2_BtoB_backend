#!/bin/bash

# Azure App Service startup script for FastAPI application

echo "Starting Azure App Service deployment..."

# Set environment variables for Python
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH

# Change to application directory
cd /home/site/wwwroot

# Wait for database to be ready (optional, but recommended)
echo "Waiting for database connection..."
python -c "
import time
import sys
from app.core.config import settings
from app.db.database import engine
from sqlalchemy import text

max_retries = 30
for i in range(max_retries):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database connection successful!')
        break
    except Exception as e:
        print(f'Database connection attempt {i+1}/{max_retries} failed: {e}')
        if i < max_retries - 1:
            time.sleep(2)
        else:
            print('Failed to connect to database after maximum retries')
            sys.exit(1)
"

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "Database migration failed"
    exit 1
fi

echo "Database migrations completed successfully"

# Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn \
    --bind=0.0.0.0:8000 \
    --workers=4 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --timeout=120 \
    --keepalive=2 \
    --max-requests=1000 \
    --max-requests-jitter=100 \
    --preload \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    app.main:app