from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceService:
    def get(self, db: Session, id: Any) -> Optional[Device]:
        return db.query(Device).filter(Device.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        return db.query(Device).offset(skip).limit(limit).all()

    def get_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        return (
            db.query(Device)
            .filter(Device.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_owner(
        self, db: Session, *, obj_in: DeviceCreate, owner_id: int
    ) -> Device:
        obj_in_data = obj_in.dict()
        db_obj = Device(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Device, obj_in: Union[DeviceUpdate, Dict[str, Any]]
    ) -> Device:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Device:
        obj = db.query(Device).get(id)
        db.delete(obj)
        db.commit()
        return obj


device_service = DeviceService()