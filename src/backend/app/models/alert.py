import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=True)
    disruption_id = Column(Integer, ForeignKey("disruptions.id", ondelete="SET NULL"), nullable=True)
    fleet_asset_id = Column(Integer, ForeignKey("fleet_assets.id", ondelete="SET NULL"), nullable=True)
    
    severity = Column(String(20), default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    alert_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    owner = relationship("User", back_populates="alerts")
    shipment = relationship("Shipment", back_populates="alerts")
    disruption = relationship("Disruption", back_populates="alerts")
    fleet_asset = relationship("FleetAsset")
