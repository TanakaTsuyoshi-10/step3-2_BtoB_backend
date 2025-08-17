from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from typing import Optional, List, Union
import json
import os
from urllib.parse import quote_plus


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Allow extra fields without validation error
    )
    
    PROJECT_NAME: str = "Energy Management System"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database - Legacy support
    DATABASE_URL: Optional[str] = None
    
    # MySQL - Individual components for Azure MySQL
    MYSQL_HOST: Optional[str] = None
    MYSQL_PORT: int = 3306
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_DATABASE: Optional[str] = None
    MYSQL_SSL_CA: Optional[str] = None
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Azure
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    
    # CORS - Support both ALLOWED_ORIGINS and BACKEND_CORS_ORIGINS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "https://localhost:3000",
        "https://app-002-gen10-step3-2-node-oshima2.azurewebsites.net"
    ]
    BACKEND_CORS_ORIGINS: Optional[Union[str, List[str]]] = None
    
    # First superuser for initial setup
    FIRST_SUPERUSER_EMAIL: Optional[str] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None
    
    @field_validator('ALLOWED_ORIGINS', 'BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            if v.startswith('[') and v.endswith(']'):
                try:
                    # Try to parse as JSON array
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Try comma-separated values
            return [origin.strip().strip('"\'') for origin in v.split(',') if origin.strip()]
        return v
    
    def get_cors_origins(self) -> List[str]:
        """Get the final CORS origins list, preferring BACKEND_CORS_ORIGINS if set"""
        if self.BACKEND_CORS_ORIGINS:
            return self.BACKEND_CORS_ORIGINS if isinstance(self.BACKEND_CORS_ORIGINS, list) else [self.BACKEND_CORS_ORIGINS]
        return self.ALLOWED_ORIGINS
    
    def get_database_url(self) -> str:
        """Build MySQL connection URL from individual components or use DATABASE_URL"""
        # If DATABASE_URL is set, use it (legacy support)
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Build from individual MySQL components
        if not all([self.MYSQL_HOST, self.MYSQL_USER, self.MYSQL_PASSWORD, self.MYSQL_DATABASE]):
            raise ValueError(
                "Either DATABASE_URL or all MySQL components (MYSQL_HOST, MYSQL_USER, "
                "MYSQL_PASSWORD, MYSQL_DATABASE) must be provided"
            )
        
        # URL encode password to handle special characters
        encoded_password = quote_plus(self.MYSQL_PASSWORD)
        
        # Build base URL without SSL parameters (SSL handled via connect_args)
        db_url = f"mysql+pymysql://{self.MYSQL_USER}:{encoded_password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        
        return db_url


settings = Settings()