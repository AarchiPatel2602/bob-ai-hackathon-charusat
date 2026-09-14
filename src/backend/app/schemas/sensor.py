from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import datetime

class SensorReadingBase(BaseModel):
    temperature: float = Field(..., example=4.5)
    humidity: Optional[float] = Field(50.0, example=52.0)
    battery_level: Optional[float] = Field(95.0, example=98.0)
    location_name: Optional[str] = None
    timestamp: Optional[datetime.datetime] = None

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReadingOut(SensorReadingBase):
    id: int
    shipment_id: int
    is_excursion: bool
    severity: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class SensorSimulationRequest(BaseModel):
    mode: str = Field("normal", example="critical") # normal, warning, critical
    custom_temperature: Optional[float] = None

class ColdChainStatusOut(BaseModel):
    shipment_id: int
    shipment_identifier: str
    cold_chain_enabled: bool
    minimum_temperature: Optional[float]
    maximum_temperature: Optional[float]
    current_temperature: Optional[float]
    current_humidity: Optional[float]
    has_active_excursion: bool
    excursion_severity: str
    duration_minutes: float
    peak_temperature: Optional[float]
    predictive_analysis: Dict[str, Any]
    compliance_profile_name: str
    recent_readings: List[SensorReadingOut]
