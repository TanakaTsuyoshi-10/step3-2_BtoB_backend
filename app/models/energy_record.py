from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class EnergyRecord(Base):
    __tablename__ = "energy_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    energy_produced = Column(Float, nullable=True)  # kWh
    energy_consumed = Column(Float, nullable=True)  # kWh
    energy_stored = Column(Float, nullable=True)  # kWh (battery)
    grid_import = Column(Float, nullable=True)  # kWh from grid
    grid_export = Column(Float, nullable=True)  # kWh to grid
    voltage = Column(Float, nullable=True)  # V
    current = Column(Float, nullable=True)  # A
    power = Column(Float, nullable=True)  # kW
    temperature = Column(Float, nullable=True)  # Celsius
    efficiency = Column(Float, nullable=True)  # percentage
    status = Column(String(50), nullable=True)  # 'normal', 'warning', 'error'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    device_id = Column(Integer, ForeignKey("devices.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    device = relationship("Device", back_populates="energy_records")
    user = relationship("User", back_populates="energy_records")