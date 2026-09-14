from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.audit import AuditLog
from backend.app.models.disruption import Disruption
from backend.app.models.fleet import FleetAsset
from backend.app.models.sensor import SensorReading
from backend.app.models.recommendation import Recommendation
from backend.app.models.alert import Alert
from backend.app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentOut
from backend.app.api.deps import get_current_user
from backend.app.engines.risk_engine import calculate_shipment_risk, get_risk_level
from backend.app.engines.disruption_engine import shipment_is_affected
from backend.app.engines.route_engine import generate_alternative_routes
from backend.app.engines.carrier_engine import rank_alternative_carriers
from backend.app.engines.fleet_engine import match_fleet_for_shipment
from backend.app.engines.location_service import geocode_location, build_route_polyline

router = APIRouter(prefix="/shipments", tags=["shipments"])

@router.get("", response_model=List[ShipmentOut])
def list_shipments(
    search: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    cold_chain_only: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Shipment).filter(Shipment.user_id == current_user.id)

    if search:
        s_term = f"%{search.lower()}%"
        query = query.filter(
            (Shipment.shipment_identifier.ilike(s_term)) |
            (Shipment.origin.ilike(s_term)) |
            (Shipment.destination.ilike(s_term)) |
            (Shipment.cargo_type.ilike(s_term)) |
            (Shipment.carrier.ilike(s_term))
        )
    if status and status.upper() != "ALL":
        query = query.filter(Shipment.status == status.upper())
    if risk_level and risk_level.upper() != "ALL":
        query = query.filter(Shipment.risk_level == risk_level.upper())
    if cold_chain_only:
        query = query.filter(Shipment.cold_chain_enabled == True)

    return query.order_by(Shipment.created_at.desc()).all()

@router.post("", response_model=ShipmentOut)
def create_shipment(
    shipment_in: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = Shipment(
        shipment_identifier=shipment_in.shipment_identifier,
        user_id=current_user.id,
        origin=shipment_in.origin,
        destination=shipment_in.destination,
        current_location=shipment_in.current_location,
        carrier=shipment_in.carrier,
        cargo_type=shipment_in.cargo_type,
        cargo_description=shipment_in.cargo_description,
        cargo_value=shipment_in.cargo_value,
        currency=shipment_in.currency,
        priority=shipment_in.priority,
        status=shipment_in.status,
        expected_departure=shipment_in.expected_departure,
        expected_delivery=shipment_in.expected_delivery,
        cold_chain_enabled=shipment_in.cold_chain_enabled,
        minimum_temperature=shipment_in.minimum_temperature,
        maximum_temperature=shipment_in.maximum_temperature,
        required_fleet_type=shipment_in.required_fleet_type,
        required_capacity=shipment_in.required_capacity,
        capacity_unit=shipment_in.capacity_unit,
        is_demo=False
    )
    db.add(shipment)
    db.flush()

    # Route points
    if shipment_in.route_points:
        for idx, pt in enumerate(shipment_in.route_points):
            db.add(ShipmentRoutePoint(
                shipment_id=shipment.id,
                sequence_order=pt.sequence_order or (idx + 1),
                location_name=pt.location_name,
                estimated_arrival=pt.estimated_arrival,
                status=pt.status or "PENDING"
            ))
    else:
        # Default route points from origin and destination
        db.add(ShipmentRoutePoint(shipment_id=shipment.id, sequence_order=1, location_name=shipment.origin, status="CURRENT"))
        db.add(ShipmentRoutePoint(shipment_id=shipment.id, sequence_order=2, location_name=shipment.destination, status="PENDING"))

    db.commit()

    # Calculate initial risk deterministically
    calculate_shipment_risk(db, shipment)

    # Log audit
    db.add(AuditLog(
        user_id=current_user.id,
        action="SHIPMENT_CREATED",
        entity_type="SHIPMENT",
        entity_id=shipment.shipment_identifier,
        details=f"Created shipment {shipment.shipment_identifier} ({shipment.origin} -> {shipment.destination}, {shipment.cargo_type})"
    ))
    db.commit()
    db.refresh(shipment)
    return shipment

@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@router.put("/{shipment_id}", response_model=ShipmentOut)
def update_shipment(
    shipment_id: int,
    shipment_in: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    update_data = shipment_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shipment, field, value)

    shipment.updated_at = datetime.datetime.utcnow()
    db.commit()

    # Recalculate risk
    calculate_shipment_risk(db, shipment)
    db.refresh(shipment)
    return shipment

@router.delete("/{shipment_id}")
def delete_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    ident = shipment.shipment_identifier
    db.delete(shipment)
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id,
        action="SHIPMENT_DELETED",
        entity_type="SHIPMENT",
        entity_id=ident,
        details=f"Deleted shipment {ident}"
    ))
    db.commit()
    return {"status": "success", "message": f"Shipment {ident} deleted"}

@router.get("/{shipment_id}/risk")
def get_shipment_risk_breakdown(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    score, level, reasons = calculate_shipment_risk(db, shipment)
    return {
        "shipment_id": shipment.id,
        "shipment_identifier": shipment.shipment_identifier,
        "risk_score": score,
        "risk_level": level,
        "risk_reasons": reasons
    }

@router.get("/{shipment_id}/routes")
def get_shipment_route_alternatives(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    alternatives = generate_alternative_routes(shipment)
    return {
        "shipment_id": shipment.id,
        "shipment_identifier": shipment.shipment_identifier,
        "current_route": [pt.location_name for pt in shipment.route_points] or [shipment.origin, shipment.destination],
        "current_risk_score": shipment.risk_score,
        "current_risk_level": shipment.risk_level,
        "alternatives": alternatives
    }

@router.get("/{shipment_id}/carriers")
def get_shipment_carrier_alternatives(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    carriers = rank_alternative_carriers(db, shipment)
    return {
        "shipment_id": shipment.id,
        "current_carrier": shipment.carrier,
        "alternatives": carriers
    }

@router.get("/{shipment_id}/fleet-matches")
def get_shipment_fleet_matches(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    matches = match_fleet_for_shipment(db, shipment)
    return {
        "shipment_id": shipment.id,
        "required_fleet_type": shipment.required_fleet_type,
        "required_capacity": shipment.required_capacity,
        "cold_chain_required": shipment.cold_chain_enabled,
        "matches": matches
    }

@router.get("/{shipment_id}/map")
def get_shipment_map_data(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    origin_coords = geocode_location(shipment.origin) or (18.9438, 72.8387)
    dest_coords = geocode_location(shipment.destination) or (51.9244, 4.4777)
    curr_coords = geocode_location(shipment.current_location) or origin_coords

    # Active route points
    if shipment.route_points:
        active_points = []
        total_pts = len(shipment.route_points)
        for pt in shipment.route_points:
            pt_coords = geocode_location(pt.location_name) or (0.0, 0.0)
            stop_type = "ORIGIN" if pt.sequence_order == 1 else "DESTINATION" if pt.sequence_order == total_pts else "TRANSIT STOP"
            active_points.append({
                "sequence_order": pt.sequence_order,
                "location_name": pt.location_name,
                "latitude": pt_coords[0],
                "longitude": pt_coords[1],
                "status": pt.status,
                "stop_type": stop_type
            })
    else:
        active_points = [
            {"sequence_order": 1, "location_name": shipment.origin, "latitude": origin_coords[0], "longitude": origin_coords[1], "status": "CURRENT", "stop_type": "ORIGIN"},
            {"sequence_order": 2, "location_name": shipment.destination, "latitude": dest_coords[0], "longitude": dest_coords[1], "status": "PENDING", "stop_type": "DESTINATION"}
        ]

    # Alternatives from route engine
    raw_alternatives = generate_alternative_routes(shipment)
    structured_alternatives = []
    for alt in raw_alternatives:
        waypoints = alt.get("waypoints", [])
        stops = []
        total_wps = len(waypoints)
        for idx, wp in enumerate(waypoints):
            wp_coords = geocode_location(wp) or (0.0, 0.0)
            st_type = "ORIGIN" if idx == 0 else "DESTINATION" if idx == total_wps - 1 else "TRANSIT STOP"
            stops.append({
                "sequence_order": idx + 1,
                "location_name": wp,
                "latitude": wp_coords[0],
                "longitude": wp_coords[1],
                "stop_type": st_type
            })
        structured_alternatives.append({
            **alt,
            "stops": stops,
            "coordinates": [[s["latitude"], s["longitude"]] for s in stops]
        })

    # Active disruptions
    active_disruptions = db.query(Disruption).filter(
        Disruption.creator_id == current_user.id,
        Disruption.status == "ACTIVE"
    ).all()
    disruption_list = []
    for d in active_disruptions:
        d_coords = geocode_location(d.location) or (18.9488, 72.8524)
        is_hit, reason = shipment_is_affected(shipment, d)
        disruption_list.append({
            "id": d.id,
            "name": d.name,
            "type": d.type,
            "location": d.location,
            "latitude": d_coords[0],
            "longitude": d_coords[1],
            "severity": d.severity,
            "description": d.description,
            "expected_duration_days": d.expected_duration_days,
            "is_intersecting": is_hit,
            "impact_reason": reason
        })

    # Relevant fleet assets
    fleet_assets = db.query(FleetAsset).filter(FleetAsset.user_id == current_user.id).all()
    fleet_list = []
    for f in fleet_assets:
        f_coords = geocode_location(f.current_location) or (23.0225, 72.5714)
        is_candidate = (f.asset_identifier == "TRUCK-205" and f.status == "IDLE")
        fleet_list.append({
            "id": f.id,
            "asset_identifier": f.asset_identifier,
            "asset_type": f.asset_type,
            "current_location": f.current_location,
            "latitude": f_coords[0],
            "longitude": f_coords[1],
            "capacity": f.capacity,
            "capacity_unit": f.capacity_unit,
            "is_refrigerated": f.is_refrigerated,
            "status": f.status,
            "is_recommended_redeployment": is_candidate
        })

    # Cold chain latest sensor
    latest_sensor = None
    if shipment.cold_chain_enabled:
        latest_sensor = db.query(SensorReading).filter(
            SensorReading.shipment_id == shipment.id
        ).order_by(SensorReading.timestamp.desc()).first()

    return {
        "shipment_id": shipment.id,
        "shipment_identifier": shipment.shipment_identifier,
        "origin": {
            "name": shipment.origin,
            "latitude": origin_coords[0],
            "longitude": origin_coords[1]
        },
        "destination": {
            "name": shipment.destination,
            "latitude": dest_coords[0],
            "longitude": dest_coords[1]
        },
        "current_location": {
            "name": shipment.current_location,
            "latitude": curr_coords[0],
            "longitude": curr_coords[1]
        },
        "status": shipment.status,
        "risk_score": shipment.risk_score,
        "risk_level": shipment.risk_level,
        "carrier": shipment.carrier,
        "cargo_type": shipment.cargo_type,
        "cargo_value": shipment.cargo_value,
        "cold_chain_enabled": shipment.cold_chain_enabled,
        "current_temperature": latest_sensor.temperature if latest_sensor else None,
        "is_cold_chain_critical": latest_sensor.is_excursion if latest_sensor else False,
        "active_route": {
            "points": active_points,
            "coordinates": [[p["latitude"], p["longitude"]] for p in active_points]
        },
        "alternative_routes": structured_alternatives,
        "disruptions": disruption_list,
        "fleet_assets": fleet_list,
        "demo_simulation": {
            "enabled": True,
            "label": "Demo GPS Simulation"
        }
    }

@router.post("/{shipment_id}/approve-reroute", response_model=ShipmentOut)
def approve_shipment_reroute(
    shipment_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    payload = payload or {}
    waypoints = payload.get("waypoints")
    route_id = payload.get("route_id")
    route_name = payload.get("route_name")

    # If waypoints not provided, find by route_id or default to top alternative
    if not waypoints:
        alternatives = generate_alternative_routes(shipment)
        target_alt = None
        if route_id:
            target_alt = next((a for a in alternatives if a.get("id") == route_id), None)
        if not target_alt:
            target_alt = alternatives[0] if alternatives else None
        
        if target_alt:
            waypoints = target_alt.get("waypoints", [])
            route_name = route_name or target_alt.get("name")
            projected_risk = target_alt.get("projected_risk_score", 24)
        else:
            waypoints = [shipment.origin, "Colombo Maritime Hub", shipment.destination]
            projected_risk = 24
    else:
        projected_risk = payload.get("projected_risk_score", 24)

    # Persist the new route points to database
    db.query(ShipmentRoutePoint).filter(ShipmentRoutePoint.shipment_id == shipment.id).delete()
    for idx, wp in enumerate(waypoints):
        db.add(ShipmentRoutePoint(
            shipment_id=shipment.id,
            sequence_order=idx + 1,
            location_name=wp,
            status="CURRENT" if idx == 0 else "PENDING"
        ))

    # Update shipment risk and status
    shipment.risk_score = projected_risk
    shipment.risk_level = get_risk_level(projected_risk)
    bypass_info = ", ".join(waypoints[1:-1]) if len(waypoints) > 2 else waypoints[0]
    shipment.risk_reasons = f"Approved reroute: Diverting via {bypass_info}. Disruption bypassed. Operational risk mitigated to {projected_risk}/100."
    if shipment.status in ["CRITICAL", "AT_RISK"]:
        shipment.status = "IN_TRANSIT"
    shipment.updated_at = datetime.datetime.utcnow()

    # Mark recommendations as approved
    recs = db.query(Recommendation).filter(
        Recommendation.shipment_id == shipment.id,
        Recommendation.recommendation_type == "REROUTE_SHIPMENT"
    ).all()
    for r in recs:
        r.status = "APPROVED"
        r.approved_at = datetime.datetime.utcnow()

    # Mark active disruption impact alerts as resolved
    alerts = db.query(Alert).filter(
        Alert.shipment_id == shipment.id,
        Alert.alert_type == "DISRUPTION_IMPACT",
        Alert.is_resolved == False
    ).all()
    for a in alerts:
        a.is_resolved = True
        a.is_read = True
        a.resolved_at = datetime.datetime.utcnow()

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="REROUTE_APPROVED",
        entity_type="SHIPMENT",
        entity_id=shipment.shipment_identifier,
        details=f"Approved reroute for {shipment.shipment_identifier} via {bypass_info}. Active route points persisted."
    ))

    db.commit()
    db.refresh(shipment)
    return shipment
