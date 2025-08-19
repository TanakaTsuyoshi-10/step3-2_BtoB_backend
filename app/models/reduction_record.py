from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class ReductionRecord(Base):
    __tablename__ = "reduction_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    energy_type = Column(Enum('electricity', 'gas', name='energy_type_enum'), nullable=False)
    usage = Column(Float, nullable=False, comment='実際の使用量')
    baseline = Column(Float, nullable=False, comment='ベースライン使用量')
    reduced_co2_kg = Column(Float, nullable=False, comment='削減されたCO2量(kg)')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reduction_records")