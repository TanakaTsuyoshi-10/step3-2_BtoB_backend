from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Get clean database URI - single source of truth
database_url = settings.sqlalchemy_uri_clean

# Driver-specific connect_args for robust Azure MySQL connection
connect_args = {}
if database_url.startswith("mysql+pymysql://"):
    # PyMySQL - recommended for Azure
    connect_args = {
        "charset": "utf8mb4",
        "connect_timeout": 8,
        "ssl": {"ssl_mode": "REQUIRED"}
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

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=280,
    pool_size=5,
    max_overflow=10,
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