from sqlalchemy import Column, Integer, String, Date, DateTime, Enum
from sqlalchemy.sql import func
from app.db.database import Base


class ReportJob(Base):
    __tablename__ = "report_jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=True)
    range_start = Column(Date, nullable=False)
    range_end = Column(Date, nullable=False)
    granularity = Column(Enum('monthly', 'quarterly', 'yearly', name='granularity_enum'), nullable=False)
    status = Column(Enum('queued', 'done', 'failed', name='job_status_enum'), nullable=False, default='queued')
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())