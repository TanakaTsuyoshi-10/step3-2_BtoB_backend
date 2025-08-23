# app/api/v1/endpoints/debug.py
import os
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy import text
from app.db.database import SessionLocal

router = APIRouter(tags=["_debug"])

def require_debug_token(x_debug_token: Optional[str] = Header(default=None)):
    expected = os.getenv("DEBUG_TOKEN")
    if not expected or x_debug_token != expected:
        raise HTTPException(status_code=403, detail="forbidden")
    return True

@router.get("/_debug/outbound-ips")
def outbound_ips(_: bool = Depends(require_debug_token)):
    """Get Azure App Service outbound IPs for MySQL firewall configuration"""
    ips = os.getenv("WEBSITE_OUTBOUND_IPS")
    arr = ips.split(",") if ips else []
    return {"WEBSITE_OUTBOUND_IPS": arr}

@router.get("/_debug/db-health")  
def db_health(_: bool = Depends(require_debug_token)):
    """Test database connectivity"""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"db_ok": True}
    except Exception as e:
        return {"db_ok": False, "error": str(e)[:400]}