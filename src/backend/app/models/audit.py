import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from backend.app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False) # e.g. REROUTE_APPROVED, REDEPLOYMENT_APPROVED, ALERT_RESOLVED
    entity_type = Column(String(50), nullable=False) # SHIPMENT, FLEET_ASSET, ALERT, RECOMMENDATION, DISRUPTION
    entity_id = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
