from fastapi import APIRouter, Depends
from app.core.config import settings
from app.schemas.user import User
from app.auth.deps import get_current_user
import os

router = APIRouter(tags=["debug"])


@router.get("/debug/config")
def debug_config():
    """Debug endpoint to check configuration (development only)"""
    return {
        "secret_key_length": len(settings.SECRET_KEY),
        "secret_key_first_10": settings.SECRET_KEY[:10],
        "algorithm": settings.ALGORITHM,
        "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "project_name": settings.PROJECT_NAME,
        "project_version": settings.PROJECT_VERSION
    }


@router.get("/debug/env")
def debug_env():
    """Debug endpoint to check environment variables"""
    secret_key_env = os.environ.get('SECRET_KEY')
    return {
        "secret_key_env_exists": secret_key_env is not None,
        "secret_key_env_length": len(secret_key_env) if secret_key_env else 0,
        "secret_key_env_first_10": secret_key_env[:10] if secret_key_env else None
    }
