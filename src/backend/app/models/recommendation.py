import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=True)
    
    recommendation_type = Column(String(50), nullable=False) # REROUTE_SHIPMENT, CHANGE_CARRIER, REDEPLOY_FLEET, QUARANTINE_COLD_CHAIN, MONITOR_SHIPMENT, NO_ACTION
    priority = Column(String(20), default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    reason = Column(Text, nullable=False)
    affected_entity = Column(String(100), nullable=False)
    current_state = Column(Text, nullable=False)
    recommended_state = Column(Text, nullable=False)
    expected_benefit = Column(Text, nullable=False)
    
    cost_impact = Column(Float, default=0.0)
    time_impact_hours = Column(Float, default=0.0)
    risk_impact_points = Column(Integer, default=0) # e.g. -67 (reduces risk by 67 points)
    details = Column(Text, nullable=True) # JSON payload
    
    status = Column(String(30), default="PENDING") # PENDING, APPROVED, REJECTED, APPLIED
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    shipment = relationship("Shipment", back_populates="recommendations")

class RedeploymentAction(Base):
    __tablename__ = "redeployment_actions"

    id = Column(Integer, primary_key=True, index=True)
    fleet_asset_id = Column(Integer, ForeignKey("fleet_assets.id"), nullable=False)
    from_location = Column(String(150), nullable=False)
    to_location = Column(String(150), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(30), default="RECOMMENDED") # RECOMMENDED, APPROVED, IN_TRANSIT, COMPLETED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    fleet_asset = relationship("FleetAsset", back_populates="redeployment_actions")
