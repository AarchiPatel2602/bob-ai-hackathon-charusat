from pydantic import BaseModel, Field
from typing import Optional
import datetime

class FleetAssetBase(BaseModel):
    asset_identifier: str = Field(..., example="TRUCK-205")
    asset_type: str = Field("Truck", example="Truck")
    current_location: str = Field(..., example="Ahmedabad")
    capacity: float = Field(..., example=10.0)
    capacity_unit: str = Field("tons", example="tons")
    is_refrigerated: bool = Field(False, example=True)
    status: str = Field("AVAILABLE", example="IDLE") # AVAILABLE, IN_TRANSIT, IDLE, MAINTENANCE
    idle_since: Optional[datetime.datetime] = None
    current_assignment: Optional[str] = None

class FleetAssetCreate(FleetAssetBase):
    pass

class FleetAssetUpdate(BaseModel):
    asset_type: Optional[str] = None
    current_location: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    is_refrigerated: Optional[bool] = None
    status: Optional[str] = None
    current_assignment: Optional[str] = None

class FleetAssetOut(FleetAssetBase):
    id: int
    user_id: int
    is_demo: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class FleetUtilisationOut(BaseModel):
    total_assets: int
    available_assets: int
    in_transit_assets: int
    idle_assets: int
    maintenance_assets: int
    total_capacity_tons: float
    active_capacity_tons: float
    idle_capacity_tons: float
    maintenance_capacity_tons: float
    current_utilisation_pct: float
    projected_utilisation_pct: float
    improvement_pct: float

class FleetRedeploymentRecommendationOut(BaseModel):
    asset_id: int
    asset_identifier: str
    asset_type: str
    from_location: str
    to_location: str
    capacity: float
    capacity_unit: str
    is_refrigerated: bool
    reason: str
    priority: str
    current_utilisation_pct: float
    projected_utilisation_pct: float
    estimated_transit_hours: float
    status: str
