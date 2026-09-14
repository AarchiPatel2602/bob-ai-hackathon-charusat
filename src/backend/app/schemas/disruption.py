from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class DisruptionBase(BaseModel):
    name: str = Field(..., example="Mumbai Port Strike")
    type: str = Field(..., example="Port Strike")
    location: str = Field(..., example="Mumbai Port")
    severity: str = Field("HIGH", example="HIGH")
    start_time: Optional[datetime.datetime] = None
    expected_duration_days: float = Field(3.0, example=4.0)
    description: Optional[str] = Field(None, example="Port workers have started a wildcat strike.")
    status: str = Field("ACTIVE", example="ACTIVE")

class DisruptionCreate(DisruptionBase):
    pass

class DisruptionUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    severity: Optional[str] = None
    expected_duration_days: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None

class DisruptionOut(DisruptionBase):
    id: int
    creator_id: int
    affected_shipments_count: int
    cargo_value_at_risk: float
    is_demo: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class DisruptionImpactOut(BaseModel):
    disruption_id: int
    disruption_name: str
    affected_shipments_count: int
    cargo_value_at_risk: float
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    cold_chain_count: int
    affected_shipments: List[dict]
