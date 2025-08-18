from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    devices = relationship("Device", back_populates="owner")
    energy_records = relationship("EnergyRecord", back_populates="user")
    employee = relationship("Employee", back_populates="user", uselist=False)
    reduction_records = relationship("ReductionRecord", back_populates="user")
    points_ledger = relationship("PointsLedger", back_populates="user")
    redemptions = relationship("Redemption", back_populates="user")