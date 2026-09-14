from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.alert import Alert
from backend.app.models.recommendation import Recommendation
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.audit import AuditLog
from backend.app.schemas.alert import AlertOut
from backend.app.api.deps import get_current_user
from backend.app.engines.risk_engine import get_risk_level
from backend.app.engines.route_engine import generate_alternative_routes
import json

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=List[AlertOut])
def list_alerts(
    severity: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert).filter(Alert.user_id == current_user.id)
    if severity and severity.upper() != "ALL":
        query = query.filter(Alert.severity == severity.upper())
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)

    return query.order_by(Alert.created_at.desc()).all()

@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert

@router.post("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    alert.is_read = True
    alert.resolved_at = datetime.datetime.utcnow()
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id,
        action="ALERT_RESOLVED",
        entity_type="ALERT",
        entity_id=str(alert.id),
        details=f"Alert resolved: '{alert.title}'"
    ))
    db.commit()
    db.refresh(alert)
    return alert

@router.post("/{alert_id}/approve")
def approve_alert_action(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    alert.is_read = True
    alert.resolved_at = datetime.datetime.utcnow()

    # If linked to a recommendation for the shipment, update the shipment's active route in the database
    if alert.shipment_id:
        shipment = db.query(Shipment).filter(Shipment.id == alert.shipment_id).first()
        rec = db.query(Recommendation).filter(
            Recommendation.shipment_id == alert.shipment_id,
            Recommendation.status == "PENDING"
        ).first()
        if rec:
            rec.status = "APPROVED"
            rec.approved_at = datetime.datetime.utcnow()

        if shipment:
            waypoints = []
            if rec and rec.details:
                try:
                    parsed = json.loads(rec.details)
                    if isinstance(parsed, dict) and "waypoints" in parsed:
                        waypoints = parsed["waypoints"]
                    elif isinstance(parsed, list):
                        waypoints = parsed
                except Exception:
                    pass

            if not waypoints:
                state_text = (rec.recommended_state if rec else "").lower()
                if "colombo" in state_text or ("mumbai" in shipment.origin.lower() and "rotterdam" in shipment.destination.lower()):
                    waypoints = ["Mumbai Feeder", "Colombo Maritime Hub", "Suez Canal Bypass", "Rotterdam Port"]
                elif "singapore" in state_text:
                    waypoints = ["Mumbai", "Singapore Port", "Cape Route", "Rotterdam Port"]
                elif "frankfurt" in state_text:
                    waypoints = ["Mumbai International Cargo", "Frankfurt Logistics Hub", "Rotterdam Overland"]
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
            new_risk = 24
            shipment.risk_score = new_risk
            shipment.risk_level = get_risk_level(new_risk)
            bypass_info = ", ".join(waypoints[1:-1]) if len(waypoints) > 2 else waypoints[0]
            shipment.risk_reasons = f"Approved reroute: Diverting via {bypass_info}. Disruption bypassed. Operational risk mitigated to {new_risk}/100."
            if shipment.status in ["CRITICAL", "AT_RISK"]:
                shipment.status = "IN_TRANSIT"
            shipment.updated_at = datetime.datetime.utcnow()

    db.add(AuditLog(
        user_id=current_user.id,
        action="RECOMMENDATION_APPROVED",
        entity_type="ALERT",
        entity_id=str(alert.id),
        details=f"Recommended action approved from alert: '{alert.title}'. Reroute recommendation approved and route points persisted."
    ))
    db.commit()

    return {
        "status": "APPROVED",
        "message": "Recommended action approved and logged. Operational state updated.",
        "alert_id": alert.id
    }
