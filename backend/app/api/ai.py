from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.shipment import Shipment
from backend.app.models.disruption import Disruption
from backend.app.api.deps import get_current_user
from backend.app.engines.disruption_engine import shipment_is_affected
from backend.app.engines.route_engine import generate_alternative_routes
from backend.app.engines.carrier_engine import rank_alternative_carriers
from backend.app.engines.fleet_engine import match_fleet_for_shipment
from backend.app.engines.ai_service import generate_ai_decision_support, answer_supply_chain_query
from backend.app.api.sensors import get_cold_chain_status

router = APIRouter(prefix="/ai", tags=["ai"])

class AIShipmentRecommendationRequest(BaseModel):
    shipment_id: int

@router.post("/shipment-recommendation")
async def get_ai_shipment_recommendation(
    req: AIShipmentRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == req.shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # 1. Gather active disruptions affecting this shipment
    active_disruptions = db.query(Disruption).filter(
        Disruption.status == "ACTIVE",
        Disruption.creator_id == current_user.id
    ).all()
    affecting_disruptions = []
    for d in active_disruptions:
        affected, r_text = shipment_is_affected(shipment, d)
        if affected:
            affecting_disruptions.append({
                "name": d.name,
                "location": d.location,
                "severity": d.severity,
                "type": d.type,
                "expected_duration_days": d.expected_duration_days,
                "reason": r_text
            })

    # 2. Alternatives
    routes = generate_alternative_routes(shipment, affecting_disruptions[0]["location"] if affecting_disruptions else "")
    carriers = rank_alternative_carriers(db, shipment)
    fleet_matches = match_fleet_for_shipment(db, shipment)

    # 3. Cold chain status
    cold_chain_status = {}
    if shipment.cold_chain_enabled:
        cc_status_obj = get_cold_chain_status(shipment.id, db, current_user)
        cold_chain_status = cc_status_obj

    # Build structured factual context
    context = {
        "shipment": {
            "id": shipment.id,
            "shipment_identifier": shipment.shipment_identifier,
            "origin": shipment.origin,
            "destination": shipment.destination,
            "current_location": shipment.current_location,
            "carrier": shipment.carrier,
            "cargo_type": shipment.cargo_type,
            "cargo_value": shipment.cargo_value,
            "priority": shipment.priority,
            "status": shipment.status,
            "min_temp": shipment.minimum_temperature,
            "max_temp": shipment.maximum_temperature,
            "risk_score": shipment.risk_score,
            "risk_level": shipment.risk_level
        },
        "disruptions": affecting_disruptions,
        "current_risk": shipment.risk_score,
        "route_alternatives": routes,
        "carrier_alternatives": carriers,
        "fleet_matches": fleet_matches,
        "cold_chain_status": cold_chain_status
    }

    result = await generate_ai_decision_support(context)
    return result


class AIChatRequest(BaseModel):
    query: str
    shipment_id: Optional[int] = None

@router.post("/chat")
async def chat_with_bob(
    req: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Conversational Copilot Endpoint: Answers natural language questions regarding
    supply-chain disruptions, at-risk shipments, cold-chain telemetry, idle fleet assets,
    and recommended mitigation actions.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    
    response = await answer_supply_chain_query(
        query=req.query,
        db=db,
        user=current_user,
        shipment_id=req.shipment_id
    )
    return response

