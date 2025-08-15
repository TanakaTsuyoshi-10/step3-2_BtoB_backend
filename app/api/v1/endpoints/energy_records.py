from typing import Any, List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_active_user
from app.db.database import get_db
from app.schemas.energy_record import EnergyRecord, EnergyRecordCreate, EnergyRecordUpdate
from app.schemas.user import User
from app.services.energy_record import energy_record_service
from app.services.device import device_service

router = APIRouter()


@router.get("/", response_model=List[EnergyRecord])
def read_energy_records(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve energy records.
    """
    if start_date and end_date:
        records = energy_record_service.get_by_date_range(
            db, 
            user_id=current_user.id, 
            start_date=start_date, 
            end_date=end_date,
            device_id=device_id
        )
    elif device_id:
        # Verify device ownership
        device = device_service.get(db, id=device_id)
        if not device or device.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Device not found")
        records = energy_record_service.get_by_device(db, device_id=device_id, skip=skip, limit=limit)
    else:
        records = energy_record_service.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    
    return records


@router.post("/", response_model=EnergyRecord)
def create_energy_record(
    *,
    db: Session = Depends(get_db),
    record_in: EnergyRecordCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new energy record.
    """
    # Verify device ownership
    device = device_service.get(db, id=record_in.device_id)
    if not device or device.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Device not found")
    
    record = energy_record_service.create_with_user(db=db, obj_in=record_in, user_id=current_user.id)
    return record


@router.get("/daily-summary", response_model=dict)
def get_daily_summary(
    *,
    db: Session = Depends(get_db),
    date: date = Query(...),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get daily energy summary.
    """
    summary_date = datetime.combine(date, datetime.min.time())
    summary = energy_record_service.get_daily_summary(
        db, user_id=current_user.id, date=summary_date
    )
    return summary


@router.put("/{id}", response_model=EnergyRecord)
def update_energy_record(
    *,
    db: Session = Depends(get_db),
    id: int,
    record_in: EnergyRecordUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update an energy record.
    """
    record = energy_record_service.get(db=db, id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Energy record not found")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    record = energy_record_service.update(db=db, db_obj=record, obj_in=record_in)
    return record


@router.get("/{id}", response_model=EnergyRecord)
def read_energy_record(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get energy record by ID.
    """
    record = energy_record_service.get(db=db, id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Energy record not found")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return record


@router.delete("/{id}", response_model=EnergyRecord)
def delete_energy_record(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete an energy record.
    """
    record = energy_record_service.get(db=db, id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Energy record not found")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    record = energy_record_service.remove(db=db, id=id)
    return record