from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    name: str
    device_type: str
    model: Optional[str] = None
    serial_number: Optional[str] = None
    capacity: Optional[float] = None
    efficiency: Optional[float] = None
    location: Optional[str] = None
    is_active: bool = True
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    capacity: Optional[float] = None
    efficiency: Optional[float] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None


class DeviceInDBBase(DeviceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class Device(DeviceInDBBase):
    pass