from pydantic import BaseModel
from typing import List, Optional

class CriticalAttentionItem(BaseModel):
    shipment_id: int
    shipment_identifier: str
    origin_destination: str
    cargo_type: str
    cargo_value: float
    risk_score: int
    risk_level: str
    reason: str
    has_cold_chain: bool
    current_temp: Optional[float] = None

class LiveActivityItem(BaseModel):
    id: str
    time_str: str
    title: str
    subtitle: str
    severity: str
    entity_type: str

class DashboardSummaryOut(BaseModel):
    active_shipments: int
    at_risk_shipments: int
    critical_shipments: int
    active_disruptions: int
    cargo_value_at_risk: float
    fleet_utilisation_pct: float
    cold_chain_alerts_count: int
    critical_attention: List[CriticalAttentionItem]
    recent_activity: List[LiveActivityItem]
