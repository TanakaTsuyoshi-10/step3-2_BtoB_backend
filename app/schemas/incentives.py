from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class DistributionSummary(BaseModel):
    """配布状況サマリー"""
    total_points: int
    total_employees: int
    average_points: float
    period_start: date
    period_end: date


class DepartmentDistribution(BaseModel):
    """部署別配布状況"""
    department: str
    total_points: int
    employee_count: int
    average_points: float


class EmployeeDistribution(BaseModel):
    """従業員別配布状況"""
    employee_id: int
    employee_name: str
    department: str
    total_points: int
    last_earned_date: Optional[datetime]


class DistributionResponse(BaseModel):
    """配布状況レスポンス"""
    summary: DistributionSummary
    departments: List[DepartmentDistribution]
    employees: List[EmployeeDistribution]


class RewardSummary(BaseModel):
    """景品サマリー"""
    id: int
    title: str
    description: Optional[str]
    category: str
    points_required: int
    stock: int
    active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RewardCreate(BaseModel):
    """景品作成"""
    title: str
    description: Optional[str]
    category: str
    points_required: int
    stock: int
    active: bool = True


class RewardUpdate(BaseModel):
    """景品更新"""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    points_required: Optional[int] = None
    stock: Optional[int] = None
    active: Optional[bool] = None


class RedemptionSummary(BaseModel):
    """交換実績サマリー"""
    total_redemptions: int
    total_points_used: int
    period_start: date
    period_end: date


class RewardPopularity(BaseModel):
    """景品人気度"""
    reward_id: int
    reward_title: str
    redemption_count: int
    percentage: float
    total_points_used: int


class RedemptionResponse(BaseModel):
    """交換実績レスポンス"""
    summary: RedemptionSummary
    popularity: List[RewardPopularity]