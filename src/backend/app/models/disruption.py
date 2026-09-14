import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Disruption(Base):
    __tablename__ = "disruptions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=False) # Port Strike, Port Closure, Storm, Flood, Severe Weather, Road Closure, Rail Disruption, Geopolitical Crisis, Carrier Failure, Other
    location = Column(String(150), nullable=False)
    severity = Column(String(50), default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    expected_duration_days = Column(Float, default=3.0)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE") # ACTIVE, RESOLVED
    
    affected_shipments_count = Column(Integer, default=0)
    cargo_value_at_risk = Column(Float, default=0.0)
    
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    creator = relationship("User", back_populates="disruptions")
    alerts = relationship("Alert", back_populates="disruption", cascade="all, delete-orphan")
