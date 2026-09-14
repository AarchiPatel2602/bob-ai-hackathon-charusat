import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class FleetAsset(Base):
    __tablename__ = "fleet_assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_identifier = Column(String(50), index=True, nullable=False)
    asset_type = Column(String(50), default="Truck") # Truck, Container, Vessel, Air Cargo
    current_location = Column(String(150), nullable=False)
    capacity = Column(Float, nullable=False, default=10.0)
    capacity_unit = Column(String(20), default="tons")
    is_refrigerated = Column(Boolean, default=False)
    status = Column(String(50), default="AVAILABLE") # AVAILABLE, IN_TRANSIT, IDLE, MAINTENANCE
    idle_since = Column(DateTime, nullable=True)
    current_assignment = Column(String(100), nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="fleet_assets")
    redeployment_actions = relationship("RedeploymentAction", back_populates="fleet_asset", cascade="all, delete-orphan")
