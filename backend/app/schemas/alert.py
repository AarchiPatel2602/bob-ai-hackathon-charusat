from pydantic import BaseModel
from typing import Optional
import datetime

class AlertOut(BaseModel):
    id: int
    user_id: int
    shipment_id: Optional[int] = None
    disruption_id: Optional[int] = None
    fleet_asset_id: Optional[int] = None
    severity: str
    alert_type: str
    title: str
    reason: str
    recommended_action: Optional[str] = None
    is_read: bool
    is_resolved: bool
    resolved_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
