from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class DateRangeModel(BaseModel):
    """Date range model for API responses"""
    from_date: date = None
    to_date: date = None


class KPIResponse(BaseModel):
    """KPI metrics response for dashboard overview cards"""
    company_id: int
    range: DateRangeModel
    active_users: int
    electricity_total_kwh: float
    gas_total_m3: float
    co2_reduction_total_kg: float


class MonthlyUsageItem(BaseModel):
    """Monthly usage data item"""
    month: int
    electricity_kwh: float
    gas_m3: float


class MonthlyUsageResponse(BaseModel):
    """Monthly usage response for bar chart"""
    company_id: int
    year: int
    months: List[MonthlyUsageItem]


class Co2TrendItem(BaseModel):
    """CO2 trend data point"""
    period: str  # YYYY-MM format
    co2_kg: float


class Co2TrendResponse(BaseModel):
    """CO2 reduction trend response for line chart"""
    company_id: int
    points: List[Co2TrendItem]


class UsageData(BaseModel):
    """Usage data for current/previous comparison"""
    electricity_kwh: float
    gas_m3: float


class YoyUsageResponse(BaseModel):
    """Year-over-year usage comparison response for horizontal bar chart"""
    company_id: int
    month: str  # YYYY-MM format
    current: UsageData
    previous: UsageData
    delta: UsageData