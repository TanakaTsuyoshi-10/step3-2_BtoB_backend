from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Get database URL (either from DATABASE_URL or built from MySQL components)
database_url = settings.get_database_url()

# Driver-specific connect_args for robust Azure MySQL connection
connect_args = {}
if database_url.startswith("mysql+pymysql://"):
    # PyMySQL - recommended for Azure
    connect_args = {
        "charset": "utf8mb4",
        "connect_timeout": 8,  # Shorter timeout for faster failure detection
        "ssl": {"ssl_mode": "REQUIRED"}  # Azure MySQL requires SSL
    }
elif database_url.startswith("mysql+mysqlconnector://"):
    # MySQL Connector/Python
    connect_args = {
        "charset": "utf8mb4",
        "connection_timeout": 8,
        "ssl_disabled": False
    }
elif database_url.startswith("mysql+mysqldb://") or database_url.startswith("mysql://"):
    # MySQLdb/mysqlclient
    connect_args = {
        "charset": "utf8mb4", 
        "connect_timeout": 8,
        "ssl": {"ssl_mode": "REQUIRED"}
    }

# Add SSL certificate if available (but don't fail without it)
if settings.MYSQL_SSL_CA:
    if not os.path.isabs(settings.MYSQL_SSL_CA):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ssl_ca_path = os.path.join(project_root, settings.MYSQL_SSL_CA)
    else:
        ssl_ca_path = settings.MYSQL_SSL_CA
    
    if os.path.exists(ssl_ca_path):
        if "ssl" in connect_args:
            connect_args["ssl"]["ca"] = ssl_ca_path
        else:
            connect_args["ssl_ca"] = ssl_ca_path

engine = create_engine(
    database_url,
    pool_pre_ping=True,      # Test connections before use
    pool_recycle=280,        # Recycle connections before Azure timeout (5min)
    pool_size=5,             # Base connection pool size
    max_overflow=5,          # Additional connections under load
    connect_args=connect_args,
    future=True              # Use SQLAlchemy 2.0 style
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()