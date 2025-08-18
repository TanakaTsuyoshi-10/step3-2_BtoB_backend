from typing import Any, List, Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_active_user
from app.db.database import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user import user_service

router = APIRouter()


@router.post("/", response_model=User)
def create_user(
    *,
    db: Annotated[Session, Depends(get_db)],
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = user_service.create(db, obj_in=user_in)
    return user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    password: str = None,
    full_name: str = None,
    email: str = None,
) -> Any:
    """
    Update own user.
    """
    current_user_data = UserUpdate(**current_user.__dict__)
    if password is not None:
        current_user_data.password = password
    if full_name is not None:
        current_user_data.full_name = full_name
    if email is not None:
        current_user_data.email = email
    user = user_service.update(db, db_obj=current_user, obj_in=current_user_data)
    return user


@router.get("/me", response_model=User)
def read_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Get current user.
    """
    return current_user