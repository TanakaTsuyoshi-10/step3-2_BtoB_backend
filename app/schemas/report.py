from typing import List, Optional
from pydantic import BaseModel, validator
from datetime import date, datetime
from decimal import Decimal

from app.models.report import MethodologyEnum, StatusEnum, ScopeEnum


class ReportItemBase(BaseModel):
    site_name: str
    device_name: str
    scope: ScopeEnum
    amount_kg: Decimal


class ReportItemCreate(ReportItemBase):
    pass


class ReportItemUpdate(ReportItemBase):
    pass


class ReportItem(ReportItemBase):
    id: str
    report_id: str

    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    name: str
    period_start: date
    period_end: date
    methodology: MethodologyEnum
    notes: Optional[str] = None

    @validator('period_end')
    def validate_period(cls, v, values):
        if 'period_start' in values and v <= values['period_start']:
            raise ValueError('period_end must be after period_start')
        return v


class ReportCreate(ReportBase):
    items: List[ReportItemCreate] = []


class ReportUpdate(ReportBase):
    items: List[ReportItemCreate] = []


class ReportSummary(BaseModel):
    """一覧用のサマリー"""
    id: str
    name: str
    period_start: date
    period_end: date
    total_reduction_kg: Decimal
    status: StatusEnum
    created_by: str
    created_at: datetime

    @property
    def total_reduction_tonnes(self) -> float:
        """kg を t に変換（小数1桁）"""
        return round(float(self.total_reduction_kg) / 1000, 1)

    class Config:
        from_attributes = True


class Report(ReportBase):
    id: str
    company_id: Optional[str] = None
    scope1_reduction_kg: Decimal
    scope2_reduction_kg: Decimal
    scope3_reduction_kg: Decimal
    total_reduction_kg: Decimal
    status: StatusEnum
    created_by: str
    created_at: datetime
    updated_at: datetime
    items: List[ReportItem] = []

    @property
    def total_reduction_tonnes(self) -> float:
        """kg を t に変換（小数1桁）"""
        return round(float(self.total_reduction_kg) / 1000, 1)

    class Config:
        from_attributes = True


class ReportExportRequest(BaseModel):
    format: str  # pdf or csv

    @validator('format')
    def validate_format(cls, v):
        if v not in ['pdf', 'csv']:
            raise ValueError('format must be pdf or csv')
        return v