from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from enum import Enum


class EnergyType(str, Enum):
    electricity = "electricity"
    gas = "gas"


class ReductionRecordBase(BaseModel):
    date: date
    energy_type: EnergyType
    usage: float
    baseline: float
    reduced_co2_kg: float


class ReductionRecordCreate(ReductionRecordBase):
    user_id: int


class ReductionRecordUpdate(BaseModel):
    date: Optional[date] = None
    energy_type: Optional[EnergyType] = None
    usage: Optional[float] = None
    baseline: Optional[float] = None
    reduced_co2_kg: Optional[float] = None


class ReductionRecord(ReductionRecordBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True