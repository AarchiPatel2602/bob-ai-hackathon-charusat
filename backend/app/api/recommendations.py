from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.recommendation import Recommendation
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.alert import Alert
from backend.app.models.audit import AuditLog
from backend.app.schemas.recommendation import RecommendationOut
from backend.app.api.deps import get_current_user
from backend.app.engines.risk_engine import get_risk_level
from backend.app.engines.route_engine import generate_alternative_routes
import json

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("", response_model=List[RecommendationOut])
def list_recommendations(
    shipment_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Recommendation).join(Shipment, Recommendation.shipment_id == Shipment.id, isouter=True)
    if shipment_id:
        query = query.filter(Recommendation.shipment_id == shipment_id)
    if status and status.upper() != "ALL":
        query = query.filter(Recommendation.status == status.upper())
    return query.order_by(Recommendation.created_at.desc()).all()

@router.post("/{recommendation_id}/approve", response_model=RecommendationOut)
def approve_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.status = "APPROVED"
    rec.approved_at = datetime.datetime.utcnow()

    # If linked to a reroute recommendation, update the shipment's active route in the database
    if rec.shipment_id and rec.recommendation_type == "REROUTE_SHIPMENT":
        shipment = db.query(Shipment).filter(Shipment.id == rec.shipment_id).first()
        if shipment:
            waypoints = []
            if rec.details:
                try:
                    parsed = json.loads(rec.details)
                    if isinstance(parsed, dict) and "waypoints" in parsed:
                        waypoints = parsed["waypoints"]
                    elif isinstance(parsed, list):
                        waypoints = parsed
                except Exception:
                    pass

            if not waypoints:
                # Infer from recommended_state or route engine
                state_text = (rec.recommended_state or "").lower()
                if "colombo" in state_text:
                    waypoints = ["Mumbai Feeder", "Colombo Maritime Hub", "Suez Canal Bypass", "Rotterdam Port"]
                elif "singapore" in state_text:
                    waypoints = ["Mumbai", "Singapore Port", "Cape Route", "Rotterdam Port"]
                elif "frankfurt" in state_text:
                    waypoints = ["Mumbai International Cargo", "Frankfurt Logistics Hub", "Rotterdam Overland"]
                elif "->" in rec.recommended_state:
                    clean = rec.recommended_state.split("(")[0].replace("Route:", "").strip()
                    waypoints = [part.strip() for part in clean.split("->") if part.strip()]
                else:
                    alts = generate_alternative_routes(shipment)
                    if alts and "waypoints" in alts[0]:
                        waypoints = alts[0]["waypoints"]
                    else:
                        waypoints = [shipment.origin, "Colombo Maritime Hub", shipment.destination]

            # Update route points in DB
            db.query(ShipmentRoutePoint).filter(ShipmentRoutePoint.shipment_id == shipment.id).delete()
            for idx, wp in enumerate(waypoints):
                db.add(ShipmentRoutePoint(
                    shipment_id=shipment.id,
                    sequence_order=idx + 1,
                    location_name=wp,
                    status="CURRENT" if idx == 0 else "PENDING"
                ))

            # Update risk
            new_risk = max(10, shipment.risk_score + rec.risk_impact_points) if rec.risk_impact_points < 0 else 24
            shipment.risk_score = new_risk
            shipment.risk_level = get_risk_level(new_risk)
            bypass_info = ", ".join(waypoints[1:-1]) if len(waypoints) > 2 else waypoints[0]
            shipment.risk_reasons = f"Approved reroute: Diverting via {bypass_info}. Disruption bypassed. Operational risk mitigated to {new_risk}/100."
            if shipment.status in ["CRITICAL", "AT_RISK"]:
                shipment.status = "IN_TRANSIT"
            shipment.updated_at = datetime.datetime.utcnow()

            # Mark linked disruption impact alerts as resolved & read
            alerts = db.query(Alert).filter(
                Alert.shipment_id == shipment.id,
                Alert.alert_type == "DISRUPTION_IMPACT",
                Alert.is_resolved == False
            ).all()
            for a in alerts:
                a.is_resolved = True
                a.is_read = True
                a.resolved_at = datetime.datetime.utcnow()

    # Log in audit log as required by prompt: "Reroute recommendation approved"
    db.add(AuditLog(
        user_id=current_user.id,
        action="RECOMMENDATION_APPROVED",
        entity_type="RECOMMENDATION",
        entity_id=str(rec.id),
        details=f"Reroute recommendation approved for {rec.affected_entity}. Action: {rec.recommended_state}"
    ))
    db.commit()
    db.refresh(rec)
    return rec
