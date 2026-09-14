from pydantic import BaseModel
from typing import Optional
import datetime

class RecommendationOut(BaseModel):
    id: int
    shipment_id: Optional[int] = None
    recommendation_type: str
    priority: str
    reason: str
    affected_entity: str
    current_state: str
    recommended_state: str
    expected_benefit: str
    cost_impact: float
    time_impact_hours: float
    risk_impact_points: int
    details: Optional[str] = None
    status: str
    approved_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class RedeploymentActionOut(BaseModel):
    id: int
    fleet_asset_id: int
    from_location: str
    to_location: str
    reason: str
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
