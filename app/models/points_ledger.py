from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class PointsLedger(Base):
    __tablename__ = "points_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    delta = Column(Integer, nullable=False, comment='ポイント増減（正=付与、負=消費）')
    reason = Column(String(200), nullable=False, comment='付与・消費理由')
    reference_id = Column(Integer, nullable=True, comment='関連する削減記録や交換記録のID')
    balance_after = Column(Integer, nullable=False, comment='処理後のポイント残高')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="points_ledger")