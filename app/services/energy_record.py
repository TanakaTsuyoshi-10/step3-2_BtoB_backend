from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.energy_record import EnergyRecord
from app.schemas.energy_record import EnergyRecordCreate, EnergyRecordUpdate


class EnergyRecordService:
    def get(self, db: Session, id: Any) -> Optional[EnergyRecord]:
        return db.query(EnergyRecord).filter(EnergyRecord.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[EnergyRecord]:
        return db.query(EnergyRecord).offset(skip).limit(limit).all()

    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[EnergyRecord]:
        return (
            db.query(EnergyRecord)
            .filter(EnergyRecord.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_device(
        self, db: Session, *, device_id: int, skip: int = 0, limit: int = 100
    ) -> List[EnergyRecord]:
        return (
            db.query(EnergyRecord)
            .filter(EnergyRecord.device_id == device_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date_range(
        self,
        db: Session,
        *,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        device_id: Optional[int] = None
    ) -> List[EnergyRecord]:
        query = db.query(EnergyRecord).filter(
            and_(
                EnergyRecord.user_id == user_id,
                EnergyRecord.timestamp >= start_date,
                EnergyRecord.timestamp <= end_date,
            )
        )
        if device_id:
            query = query.filter(EnergyRecord.device_id == device_id)
        return query.all()

    def get_daily_summary(
        self, db: Session, *, user_id: int, date: datetime
    ) -> Dict[str, Any]:
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        result = (
            db.query(
                func.sum(EnergyRecord.energy_produced).label("total_produced"),
                func.sum(EnergyRecord.energy_consumed).label("total_consumed"),
                func.sum(EnergyRecord.grid_import).label("total_grid_import"),
                func.sum(EnergyRecord.grid_export).label("total_grid_export"),
                func.avg(EnergyRecord.efficiency).label("avg_efficiency"),
            )
            .filter(
                and_(
                    EnergyRecord.user_id == user_id,
                    EnergyRecord.timestamp >= start_date,
                    EnergyRecord.timestamp < end_date,
                )
            )
            .first()
        )
        
        return {
            "date": date.date(),
            "total_produced": float(result.total_produced or 0),
            "total_consumed": float(result.total_consumed or 0),
            "total_grid_import": float(result.total_grid_import or 0),
            "total_grid_export": float(result.total_grid_export or 0),
            "avg_efficiency": float(result.avg_efficiency or 0),
        }

    def create_with_user(
        self, db: Session, *, obj_in: EnergyRecordCreate, user_id: int
    ) -> EnergyRecord:
        obj_in_data = obj_in.dict()
        db_obj = EnergyRecord(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: EnergyRecord,
        obj_in: Union[EnergyRecordUpdate, Dict[str, Any]]
    ) -> EnergyRecord:
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

    def remove(self, db: Session, *, id: int) -> EnergyRecord:
        obj = db.query(EnergyRecord).get(id)
        db.delete(obj)
        db.commit()
        return obj


energy_record_service = EnergyRecordService()