from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.schemas.user import User


async def get_user_company_id(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> int:
    """Get company_id for the current user"""
    
    # Superusers can access any company data - return default company ID
    if current_user.is_superuser:
        # Get first available company ID for superuser access
        company_result = db.execute(text("SELECT id FROM companies LIMIT 1")).fetchone()
        if company_result:
            return company_result[0]
        else:
            # Create a default company if none exists
            db.execute(text("INSERT INTO companies (name, created_at, updated_at) VALUES ('Default Company', NOW(), NOW())"))
            db.commit()
            new_company_result = db.execute(text("SELECT LAST_INSERT_ID()")).fetchone()
            return new_company_result[0] if new_company_result else 1
    
    result = db.execute(
        text("SELECT company_id FROM employees WHERE user_id = :user_id"),
        {"user_id": current_user.id}
    ).fetchone()
    
    if not result or result[0] is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ユーザーは会社に所属していません"
        )
    
    return result[0]