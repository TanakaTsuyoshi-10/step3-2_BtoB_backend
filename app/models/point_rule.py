from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.db.database import Base


class PointRule(Base):
    __tablename__ = "point_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rule_type = Column(Enum('per_kg', 'rank_bonus', name='rule_type_enum'), nullable=False)
    value = Column(Float, nullable=False, comment='per_kg: CO2 1kg当たりのポイント, rank_bonus: 順位ボーナスポイント')
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())