from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class RoutePointBase(BaseModel):
    location_name: str
    sequence_order: int = 0
    estimated_arrival: Optional[datetime.datetime] = None
    status: Optional[str] = "PENDING"

class RoutePointCreate(RoutePointBase):
    pass

class RoutePointOut(RoutePointBase):
    id: int
    shipment_id: int

    class Config:
        from_attributes = True

class ShipmentBase(BaseModel):
    shipment_identifier: str = Field(..., example="SH-1024")
    origin: str = Field(..., example="Mumbai")
    destination: str = Field(..., example="Rotterdam")
    current_location: str = Field(..., example="Mumbai Port")
    carrier: str = Field(..., example="Maersk Line")
    cargo_type: str = Field(..., example="Vaccines")
    cargo_description: Optional[str] = Field(None, example="Pediatric mRNA vaccines")
    cargo_value: float = Field(..., example=620000.0)
    currency: str = "USD"
    priority: str = "HIGH"
    status: str = "IN_TRANSIT"
    expected_departure: Optional[datetime.datetime] = None
    expected_delivery: Optional[datetime.datetime] = None
    cold_chain_enabled: bool = False
    minimum_temperature: Optional[float] = None
    maximum_temperature: Optional[float] = None
    required_fleet_type: str = "Truck"
    required_capacity: float = 10.0
    capacity_unit: str = "tons"

class ShipmentCreate(ShipmentBase):
    route_points: Optional[List[RoutePointCreate]] = None

class ShipmentUpdate(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    current_location: Optional[str] = None
    carrier: Optional[str] = None
    cargo_type: Optional[str] = None
    cargo_description: Optional[str] = None
    cargo_value: Optional[float] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    cold_chain_enabled: Optional[bool] = None
    minimum_temperature: Optional[float] = None
    maximum_temperature: Optional[float] = None
    required_fleet_type: Optional[str] = None
    required_capacity: Optional[float] = None

class ShipmentOut(ShipmentBase):
    id: int
    user_id: int
    risk_score: int
    risk_level: str
    risk_reasons: Optional[str] = None
    is_demo: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    route_points: List[RoutePointOut] = []

    class Config:
        from_attributes = True
