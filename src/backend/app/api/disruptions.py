from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.disruption import Disruption
from backend.app.models.shipment import Shipment
from backend.app.models.recommendation import Recommendation
from backend.app.models.audit import AuditLog
from backend.app.schemas.disruption import DisruptionCreate, DisruptionUpdate, DisruptionOut, DisruptionImpactOut
from backend.app.api.deps import get_current_user
from backend.app.engines.disruption_engine import analyze_disruption_impact
from backend.app.engines.risk_engine import calculate_shipment_risk
from backend.app.engines.route_engine import generate_alternative_routes
from backend.app.engines.carrier_engine import rank_alternative_carriers
from backend.app.engines.fleet_engine import match_fleet_for_shipment
from backend.app.engines.alert_engine import trigger_disruption_impact_alert

router = APIRouter(prefix="/disruptions", tags=["disruptions"])

@router.get("", response_model=List[DisruptionOut])
def list_disruptions(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Disruption).filter(Disruption.creator_id == current_user.id)
    if status and status.upper() != "ALL":
        query = query.filter(Disruption.status == status.upper())
    if severity and severity.upper() != "ALL":
        query = query.filter(Disruption.severity == severity.upper())
    return query.order_by(Disruption.created_at.desc()).all()

@router.post("", response_model=DisruptionOut)
def report_disruption(
    disruption_in: DisruptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    disruption = Disruption(
        name=disruption_in.name,
        type=disruption_in.type,
        location=disruption_in.location,
        severity=disruption_in.severity,
        start_time=disruption_in.start_time or datetime.datetime.utcnow(),
        expected_duration_days=disruption_in.expected_duration_days,
        description=disruption_in.description,
        status=disruption_in.status,
        creator_id=current_user.id,
        is_demo=False
    )
    db.add(disruption)
    db.commit()
    db.refresh(disruption)

    # Immediately trigger full impact analysis pipeline
    run_impact_pipeline(db, disruption, current_user.id)

    db.add(AuditLog(
        user_id=current_user.id,
        action="DISRUPTION_REPORTED",
        entity_type="DISRUPTION",
        entity_id=disruption.name,
        details=f"Reported {disruption.name} ({disruption.severity}) at {disruption.location}. Impact analysis triggered."
    ))
    db.commit()
    db.refresh(disruption)
    return disruption

def run_impact_pipeline(db: Session, disruption: Disruption, user_id: int):
    """Executes the full 11-step impact analysis chain."""
    affected_shipments, total_val = analyze_disruption_impact(db, disruption)

    for shipment in affected_shipments:
        # Re-calculate shipment risk
        calculate_shipment_risk(db, shipment)

        # Trigger disruption alert
        trigger_disruption_impact_alert(db, disruption, shipment)

        # Generate route recommendations if none exists yet
        routes = generate_alternative_routes(shipment, disruption.location)
        if routes:
            best_route = routes[0]
            existing_rec = db.query(Recommendation).filter(
                Recommendation.shipment_id == shipment.id,
                Recommendation.recommendation_type == "REROUTE_SHIPMENT"
            ).first()

            if not existing_rec:
                rec = Recommendation(
                    shipment_id=shipment.id,
                    recommendation_type="REROUTE_SHIPMENT",
                    priority=disruption.severity,
                    reason=f"Current corridor exposed to {disruption.name} at {disruption.location}.",
                    affected_entity=shipment.shipment_identifier,
                    current_state=f"Current route via {disruption.location} (Risk: {shipment.risk_score}/100)",
                    recommended_state=f"{best_route['name']} (Projected Risk: {best_route['projected_risk_score']}/100)",
                    expected_benefit=f"Bypasses {disruption.location}, reduces risk by {shipment.risk_score - best_route['projected_risk_score']} points.",
                    cost_impact=best_route["additional_cost_usd"],
                    time_impact_hours=best_route["additional_time_hours"],
                    risk_impact_points=best_route["projected_risk_score"] - shipment.risk_score,
                    status="PENDING"
                )
                db.add(rec)
    db.commit()

@router.get("/{disruption_id}", response_model=DisruptionOut)
def get_disruption(
    disruption_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    disruption = db.query(Disruption).filter(
        Disruption.id == disruption_id,
        Disruption.creator_id == current_user.id
    ).first()
    if not disruption:
        raise HTTPException(status_code=404, detail="Disruption not found")
    return disruption

@router.put("/{disruption_id}", response_model=DisruptionOut)
def update_disruption(
    disruption_id: int,
    disruption_in: DisruptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    disruption = db.query(Disruption).filter(
        Disruption.id == disruption_id,
        Disruption.creator_id == current_user.id
    ).first()
    if not disruption:
        raise HTTPException(status_code=404, detail="Disruption not found")

    update_data = disruption_in.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(disruption, field, val)

    disruption.updated_at = datetime.datetime.utcnow()
    db.commit()

    # Re-run pipeline if updated
    run_impact_pipeline(db, disruption, current_user.id)
    db.refresh(disruption)
    return disruption

@router.post("/{disruption_id}/analyze", response_model=DisruptionImpactOut)
def trigger_analysis(
    disruption_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    disruption = db.query(Disruption).filter(
        Disruption.id == disruption_id,
        Disruption.creator_id == current_user.id
    ).first()
    if not disruption:
        raise HTTPException(status_code=404, detail="Disruption not found")

    run_impact_pipeline(db, disruption, current_user.id)
    affected_shipments, total_val = analyze_disruption_impact(db, disruption)

    crit = len([s for s in affected_shipments if s.risk_level == "CRITICAL"])
    high = len([s for s in affected_shipments if s.risk_level == "HIGH"])
    med = len([s for s in affected_shipments if s.risk_level == "MEDIUM"])
    low = len([s for s in affected_shipments if s.risk_level == "LOW"])
    cc = len([s for s in affected_shipments if s.cold_chain_enabled])

    return {
        "disruption_id": disruption.id,
        "disruption_name": disruption.name,
        "affected_shipments_count": len(affected_shipments),
        "cargo_value_at_risk": total_val,
        "critical_count": crit,
        "high_count": high,
        "medium_count": med,
        "low_count": low,
        "cold_chain_count": cc,
        "affected_shipments": [
            {
                "id": s.id,
                "identifier": s.shipment_identifier,
                "origin": s.origin,
                "destination": s.destination,
                "cargo_type": s.cargo_type,
                "cargo_value": s.cargo_value,
                "carrier": s.carrier,
                "risk_score": s.risk_score,
                "risk_level": s.risk_level,
                "cold_chain_enabled": s.cold_chain_enabled
            } for s in affected_shipments
        ]
    }
