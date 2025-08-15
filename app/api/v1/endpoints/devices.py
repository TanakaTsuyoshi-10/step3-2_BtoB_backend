from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_active_user
from app.db.database import get_db
from app.schemas.device import Device, DeviceCreate, DeviceUpdate
from app.schemas.user import User
from app.services.device import device_service

router = APIRouter()


@router.get("/", response_model=List[Device])
def read_devices(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve devices.
    """
    devices = device_service.get_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return devices


@router.post("/", response_model=Device)
def create_device(
    *,
    db: Session = Depends(get_db),
    device_in: DeviceCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new device.
    """
    device = device_service.create_with_owner(db=db, obj_in=device_in, owner_id=current_user.id)
    return device


@router.put("/{id}", response_model=Device)
def update_device(
    *,
    db: Session = Depends(get_db),
    id: int,
    device_in: DeviceUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a device.
    """
    device = device_service.get(db=db, id=id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    device = device_service.update(db=db, db_obj=device, obj_in=device_in)
    return device


@router.get("/{id}", response_model=Device)
def read_device(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get device by ID.
    """
    device = device_service.get(db=db, id=id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return device


@router.delete("/{id}", response_model=Device)
def delete_device(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a device.
    """
    device = device_service.get(db=db, id=id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    device = device_service.remove(db=db, id=id)
    return device