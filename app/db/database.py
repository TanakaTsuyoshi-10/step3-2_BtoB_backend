from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Get database URL (either from DATABASE_URL or built from MySQL components)
database_url = settings.get_database_url()

# Build connect_args with SSL configuration for SQLAlchemy
connect_args = {
    "charset": "utf8mb4",
    "connect_timeout": 60,
    "read_timeout": 30,
    "write_timeout": 30,
}

# Add SSL configuration to connect_args
if settings.MYSQL_SSL_CA:
    # Convert relative path to absolute path for SSL certificate
    if not os.path.isabs(settings.MYSQL_SSL_CA):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ssl_ca_path = os.path.join(project_root, settings.MYSQL_SSL_CA)
    else:
        ssl_ca_path = settings.MYSQL_SSL_CA
    
    # Check if certificate file exists
    if os.path.exists(ssl_ca_path):
        connect_args.update({
            "ssl_ca": ssl_ca_path,
            "ssl_disabled": False,
        })
    else:
        # Force SSL even without certificate
        connect_args.update({
            "ssl_disabled": False,
        })
else:
    # Force SSL for Azure MySQL
    connect_args.update({
        "ssl_disabled": False,
    })

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()