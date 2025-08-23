from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from typing import Optional, List, Union
import json
import os


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    PROJECT_NAME: str = "Energy Management System"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database - Single source of truth
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # JWT
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "fallback-secret-key-for-development-only-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Azure
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:3001",
        "https://localhost:3000",
        "https://localhost:3001", 
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
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [origin.strip().strip('"\'') for origin in v.split(',') if origin.strip()]
        return v
    
    def get_cors_origins(self) -> List[str]:
        """Get the final CORS origins list, preferring BACKEND_CORS_ORIGINS if set"""
        if self.BACKEND_CORS_ORIGINS:
            return self.BACKEND_CORS_ORIGINS if isinstance(self.BACKEND_CORS_ORIGINS, list) else [self.BACKEND_CORS_ORIGINS]
        return self.ALLOWED_ORIGINS
    
    @property
    def sqlalchemy_uri_clean(self) -> str:
        uri = (self.SQLALCHEMY_DATABASE_URI or "").strip()
        if not uri:
            raise ValueError("SQLALCHEMY_DATABASE_URI is required")
        return uri


settings = Settings()