import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from backend.app.database import Base

class Carrier(Base):
    __tablename__ = "carriers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(50), nullable=True)
    reliability_score = Column(Float, default=85.0) # 0 to 100
    average_transit_multiplier = Column(Float, default=1.0) # 1.0 is standard
    cost_index = Column(Float, default=100.0) # 100 base index
    cold_chain_certified = Column(Boolean, default=True)
    status = Column(String(50), default="ACTIVE") # ACTIVE, DISRUPTED
    supported_regions = Column(String(255), default="Global")
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
