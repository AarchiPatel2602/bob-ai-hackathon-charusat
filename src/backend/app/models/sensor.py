import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from backend.app.database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, default=50.0)
    battery_level = Column(Float, default=95.0)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    location_name = Column(String(150), nullable=True)
    
    is_excursion = Column(Boolean, default=False)
    severity = Column(String(20), default="NORMAL") # NORMAL, WARNING, MAJOR, CRITICAL
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    shipment = relationship("Shipment", back_populates="sensor_readings")
