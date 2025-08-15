from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    device_type = Column(String(100), nullable=False)  # 'solar_panel', 'battery', 'inverter', 'meter'
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), unique=True, nullable=True)
    capacity = Column(Float, nullable=True)  # kW or kWh
    efficiency = Column(Float, nullable=True)  # percentage
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    installation_date = Column(DateTime(timezone=True), nullable=True)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="devices")
    energy_records = relationship("EnergyRecord", back_populates="device")