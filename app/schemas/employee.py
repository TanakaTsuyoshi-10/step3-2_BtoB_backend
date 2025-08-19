from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmployeeBase(BaseModel):
    company_id: Optional[int] = None
    department: Optional[str] = None
    employee_code: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    user_id: int


class EmployeeUpdate(EmployeeBase):
    pass


class Employee(EmployeeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True