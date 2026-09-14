from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import datetime

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.shipment import Shipment
from backend.app.models.disruption import Disruption
from backend.app.models.alert import Alert
from backend.app.models.audit import AuditLog
from backend.app.models.sensor import SensorReading
from backend.app.models.fleet import FleetAsset
from backend.app.schemas.dashboard import DashboardSummaryOut, CriticalAttentionItem, LiveActivityItem
from backend.app.api.deps import get_current_user
from backend.app.engines.fleet_engine import calculate_fleet_utilisation
from backend.app.engines.location_service import geocode_location

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Shipments
    user_shipments = db.query(Shipment).filter(Shipment.user_id == current_user.id).all()
    active_count = len([s for s in user_shipments if s.status != "DELIVERED"])
    at_risk_count = len([s for s in user_shipments if s.risk_level in ["HIGH", "CRITICAL"] and s.status != "DELIVERED"])
    critical_count = len([s for s in user_shipments if s.risk_level == "CRITICAL" and s.status != "DELIVERED"])

    # Disruptions & Value at risk
    active_disruptions = db.query(Disruption).filter(
        Disruption.creator_id == current_user.id,
        Disruption.status == "ACTIVE"
    ).all()
    disruption_count = len(active_disruptions)
    
    # Calculate cargo value at risk across at-risk shipments
    at_risk_shipments = [s for s in user_shipments if s.risk_level in ["HIGH", "CRITICAL"] and s.status != "DELIVERED"]
    total_val_at_risk = sum(s.cargo_value for s in at_risk_shipments)

    # Fleet Utilisation
    fleet_metrics = calculate_fleet_utilisation(db, current_user.id)
    fleet_util_pct = fleet_metrics["current_utilisation_pct"]

    # Cold chain alerts
    cold_chain_alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.alert_type.in_(["COLD_CHAIN_EXCURSION", "COLD_CHAIN_WARNING"]),
        Alert.is_resolved == False
    ).count()

    # Critical Attention List (Ranked by Risk Score & Value)
    sorted_critical = sorted(
        [s for s in user_shipments if s.risk_score >= 60],
        key=lambda s: (s.risk_score, s.cargo_value),
        reverse=True
    )[:6]

    crit_items = []
    for s in sorted_critical:
        latest_sensor = db.query(SensorReading).filter(
            SensorReading.shipment_id == s.id
        ).order_by(SensorReading.timestamp.desc()).first()
        
        reasons = s.risk_reasons.split("\n")[0] if s.risk_reasons else f"Elevated Risk: {s.risk_score}/100"
        crit_items.append(CriticalAttentionItem(
            shipment_id=s.id,
            shipment_identifier=s.shipment_identifier,
            origin_destination=f"{s.origin} → {s.destination}",
            cargo_type=s.cargo_type,
            cargo_value=s.cargo_value,
            risk_score=s.risk_score,
            risk_level=s.risk_level,
            reason=reasons,
            has_cold_chain=s.cold_chain_enabled,
            current_temp=latest_sensor.temperature if latest_sensor else None
        ))

    # Live Activity Feed (Aggregated from alerts and audits)
    recent_alerts = db.query(Alert).filter(Alert.user_id == current_user.id).order_by(Alert.created_at.desc()).limit(10).all()
    recent_audits = db.query(AuditLog).filter(AuditLog.user_id == current_user.id).order_by(AuditLog.timestamp.desc()).limit(10).all()

    activity_items = []
    for a in recent_alerts:
        activity_items.append({
            "id": f"alert-{a.id}",
            "time": a.created_at,
            "title": a.title,
            "subtitle": a.reason[:90] + ("..." if len(a.reason) > 90 else ""),
            "severity": a.severity,
            "entity_type": "ALERT"
        })
    for aud in recent_audits:
        activity_items.append({
            "id": f"audit-{aud.id}",
            "time": aud.timestamp,
            "title": aud.action.replace("_", " ").title(),
            "subtitle": aud.details[:90] if aud.details else "",
            "severity": "INFO",
            "entity_type": aud.entity_type
        })

    # Sort chronological descending
    activity_items.sort(key=lambda x: x["time"], reverse=True)
    activity_out = [
        LiveActivityItem(
            id=item["id"],
            time_str=item["time"].strftime("%H:%M:%S") if (datetime.datetime.utcnow() - item["time"]).total_seconds() < 86400 else item["time"].strftime("%b %d %H:%M"),
            title=item["title"],
            subtitle=item["subtitle"],
            severity=item["severity"],
            entity_type=item["entity_type"]
        ) for item in activity_items[:8]
    ]

    return DashboardSummaryOut(
        active_shipments=active_count,
        at_risk_shipments=at_risk_count,
        critical_shipments=critical_count,
        active_disruptions=disruption_count,
        cargo_value_at_risk=round(total_val_at_risk, 2),
        fleet_utilisation_pct=fleet_util_pct,
        cold_chain_alerts_count=cold_chain_alerts,
        critical_attention=crit_items,
        recent_activity=activity_out
    )

@router.get("/critical", response_model=List[CriticalAttentionItem])
def get_critical_attention(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    summary = get_dashboard_summary(db, current_user)
    return summary.critical_attention

@router.get("/activity", response_model=List[LiveActivityItem])
def get_activity_feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    summary = get_dashboard_summary(db, current_user)
    return summary.recent_activity

@router.get("/map")
def get_dashboard_map_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Active shipments with resolved coordinates
    user_shipments = db.query(Shipment).filter(
        Shipment.user_id == current_user.id,
        Shipment.status != "DELIVERED"
    ).all()

    shipment_items = []
    for s in user_shipments:
        orig = geocode_location(s.origin) or (18.9438, 72.8387)
        dest = geocode_location(s.destination) or (51.9244, 4.4777)
        curr = geocode_location(s.current_location) or orig

        points = []
        if s.route_points:
            tot = len(s.route_points)
            for pt in s.route_points:
                c = geocode_location(pt.location_name) or (0.0, 0.0)
                st_type = "ORIGIN" if pt.sequence_order == 1 else "DESTINATION" if pt.sequence_order == tot else "TRANSIT STOP"
                points.append({
                    "sequence_order": pt.sequence_order,
                    "location_name": pt.location_name,
                    "latitude": c[0],
                    "longitude": c[1],
                    "status": pt.status,
                    "stop_type": st_type
                })
        else:
            points = [
                {"sequence_order": 1, "location_name": s.origin, "latitude": orig[0], "longitude": orig[1], "status": "CURRENT", "stop_type": "ORIGIN"},
                {"sequence_order": 2, "location_name": s.destination, "latitude": dest[0], "longitude": dest[1], "status": "PENDING", "stop_type": "DESTINATION"}
            ]

        shipment_items.append({
            "id": s.id,
            "shipment_identifier": s.shipment_identifier,
            "origin": {"name": s.origin, "latitude": orig[0], "longitude": orig[1]},
            "destination": {"name": s.destination, "latitude": dest[0], "longitude": dest[1]},
            "current_location": {"name": s.current_location, "latitude": curr[0], "longitude": curr[1]},
            "carrier": s.carrier,
            "cargo_type": s.cargo_type,
            "cargo_value": s.cargo_value,
            "status": s.status,
            "risk_score": s.risk_score,
            "risk_level": s.risk_level,
            "cold_chain_enabled": s.cold_chain_enabled,
            "route_points": points,
            "coordinates": [[p["latitude"], p["longitude"]] for p in points]
        })

    # Active disruptions with coordinates
    active_disruptions = db.query(Disruption).filter(
        Disruption.creator_id == current_user.id,
        Disruption.status == "ACTIVE"
    ).all()
    disruption_items = []
    for d in active_disruptions:
        c = geocode_location(d.location) or (18.9488, 72.8524)
        disruption_items.append({
            "id": d.id,
            "name": d.name,
            "type": d.type,
            "location": d.location,
            "latitude": c[0],
            "longitude": c[1],
            "severity": d.severity,
            "description": d.description,
            "expected_duration_days": d.expected_duration_days,
            "affected_shipments_count": d.affected_shipments_count,
            "cargo_value_at_risk": d.cargo_value_at_risk
        })

    # Fleet assets with coordinates
    fleet_assets = db.query(FleetAsset).filter(FleetAsset.user_id == current_user.id).all()
    fleet_items = []
    for f in fleet_assets:
        c = geocode_location(f.current_location) or (23.0225, 72.5714)
        fleet_items.append({
            "id": f.id,
            "asset_identifier": f.asset_identifier,
            "asset_type": f.asset_type,
            "current_location": f.current_location,
            "latitude": c[0],
            "longitude": c[1],
            "capacity": f.capacity,
            "capacity_unit": f.capacity_unit,
            "is_refrigerated": f.is_refrigerated,
            "status": f.status,
            "is_recommended_redeployment": (f.asset_identifier == "TRUCK-205" and f.status == "IDLE")
        })

    return {
        "shipments": shipment_items,
        "disruptions": disruption_items,
        "fleet_assets": fleet_items
    }
