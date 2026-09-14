import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.app.database import Base

class ComplianceProfile(Base):
    __tablename__ = "compliance_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    cargo_type = Column(String(100), nullable=False)
    min_temp = Column(Float, nullable=False)
    max_temp = Column(Float, nullable=False)
    warning_tolerance_minutes = Column(Integer, default=15)
    major_tolerance_minutes = Column(Integer, default=30)
    critical_temp_delta = Column(Float, default=2.0) # > max + 2.0 is immediate critical
    regulatory_source = Column(String(255), default="Demo Compliance Rules (Configurable)")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
