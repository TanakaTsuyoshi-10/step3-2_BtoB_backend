from sqlalchemy import Column, String, DateTime, Date, Text, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.db.database import Base


class MethodologyEnum(str, enum.Enum):
    ghg_protocol = "ghg_protocol"
    internal = "internal"
    other = "other"


class StatusEnum(str, enum.Enum):
    draft = "draft"
    published = "published"


class ScopeEnum(str, enum.Enum):
    scope1 = "scope1"
    scope2 = "scope2"
    scope3 = "scope3"


class Report(Base):
    __tablename__ = "reports"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(255), nullable=True)  # 将来拡張用
    name = Column(String(255), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    methodology = Column(Enum(MethodologyEnum), nullable=False, default=MethodologyEnum.ghg_protocol)
    scope1_reduction_kg = Column(Numeric(15, 2), nullable=False, default=0)
    scope2_reduction_kg = Column(Numeric(15, 2), nullable=False, default=0)
    scope3_reduction_kg = Column(Numeric(15, 2), nullable=False, default=0)
    total_reduction_kg = Column(Numeric(15, 2), nullable=False, default=0)  # DB保存
    notes = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.draft)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    items = relationship("ReportItem", back_populates="report", cascade="all, delete-orphan")


class ReportItem(Base):
    __tablename__ = "report_items"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(CHAR(36), ForeignKey("reports.id"), nullable=False)
    site_name = Column(String(255), nullable=False)
    device_name = Column(String(255), nullable=False)
    scope = Column(Enum(ScopeEnum), nullable=False)
    amount_kg = Column(Numeric(15, 2), nullable=False)

    # Relationship
    report = relationship("Report", back_populates="items")