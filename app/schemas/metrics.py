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
    total_redemptions: int = 0
    total_points_spent: int = 0
    total_energy_saved: float = 0.0
    total_points_awarded: int = 0
    
    # Aliases for frontend compatibility
    @property
    def total_users(self) -> int:
        return self.active_users
    
    @property
    def total_co2_reduced(self) -> float:
        return self.co2_reduction_total_kg


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