from fastapi import Depends, HTTPException, status
from app.auth.deps import get_current_user
from app.models.user import User


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """管理者権限チェック"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user