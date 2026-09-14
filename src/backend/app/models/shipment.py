import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_identifier = Column(String(50), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    origin = Column(String(150), nullable=False)
    destination = Column(String(150), nullable=False)
    current_location = Column(String(150), nullable=False)
    carrier = Column(String(100), nullable=False)
    cargo_type = Column(String(100), nullable=False)
    cargo_description = Column(String(255), nullable=True)
    cargo_value = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="USD")
    priority = Column(String(50), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="IN_TRANSIT") # PLANNED, IN_TRANSIT, DELAYED, DELIVERED, AT_RISK, CRITICAL
    
    expected_departure = Column(DateTime, nullable=True)
    expected_delivery = Column(DateTime, nullable=True)
    
    # Cold Chain specifications
    cold_chain_enabled = Column(Boolean, default=False)
    minimum_temperature = Column(Float, nullable=True) # e.g. 2.0
    maximum_temperature = Column(Float, nullable=True) # e.g. 8.0
    
    # Fleet requirements
    required_fleet_type = Column(String(50), default="Truck") # Truck, Container, Vessel, Air Cargo
    required_capacity = Column(Float, default=1.0)
    capacity_unit = Column(String(20), default="tons")
    
    # Computed Risk Fields
    risk_score = Column(Integer, default=0) # 0 - 100
    risk_level = Column(String(20), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    risk_reasons = Column(Text, nullable=True) # JSON or newline separated text
    
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="shipments")
    route_points = relationship("ShipmentRoutePoint", back_populates="shipment", cascade="all, delete-orphan", order_by="ShipmentRoutePoint.sequence_order")
    sensor_readings = relationship("SensorReading", back_populates="shipment", cascade="all, delete-orphan", order_by="SensorReading.timestamp.desc()")
    alerts = relationship("Alert", back_populates="shipment", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="shipment", cascade="all, delete-orphan")

class ShipmentRoutePoint(Base):
    __tablename__ = "shipment_route_points"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    sequence_order = Column(Integer, default=0)
    location_name = Column(String(150), nullable=False)
    estimated_arrival = Column(DateTime, nullable=True)
    status = Column(String(50), default="PENDING") # PASSED, CURRENT, PENDING

    shipment = relationship("Shipment", back_populates="route_points")
