from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RedemptionStatus(str, Enum):
    pending = "申請中"
    approved = "承認"
    rejected = "却下"
    shipped = "発送済"


# Rewards
class RewardBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    image_url: Optional[str] = None
    stock: int = 0
    points_required: int
    active: bool = True


class RewardCreate(RewardBase):
    pass


class RewardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    points_required: Optional[int] = None
    active: Optional[bool] = None


class Reward(RewardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Redemptions
class RedemptionBase(BaseModel):
    reward_id: int
    points_spent: int


class RedemptionCreate(RedemptionBase):
    pass


class RedemptionUpdate(BaseModel):
    status: RedemptionStatus


class Redemption(RedemptionBase):
    id: int
    user_id: int
    status: RedemptionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    reward: Optional[Reward] = None

    class Config:
        from_attributes = True


class RedemptionWithReward(Redemption):
    reward_title: str
    reward_category: str