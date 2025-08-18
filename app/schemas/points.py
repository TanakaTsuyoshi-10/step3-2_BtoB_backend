from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RuleType(str, Enum):
    per_kg = "per_kg"
    rank_bonus = "rank_bonus"


# Point Rules
class PointRuleBase(BaseModel):
    name: str
    rule_type: RuleType
    value: float
    active: bool = True


class PointRuleCreate(PointRuleBase):
    pass


class PointRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[RuleType] = None
    value: Optional[float] = None
    active: Optional[bool] = None


class PointRule(PointRuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Points Ledger
class PointsLedgerBase(BaseModel):
    delta: int
    reason: str
    reference_id: Optional[int] = None
    balance_after: int


class PointsLedgerCreate(PointsLedgerBase):
    user_id: int


class PointsLedger(PointsLedgerBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Points Summary
class PointsSummary(BaseModel):
    current_balance: int
    total_earned: int
    total_spent: int
    this_month_earned: int


class RankingEntry(BaseModel):
    user_id: int
    user_name: str
    department: Optional[str]
    reduced_co2_kg: float
    rank: int
    points_earned: int