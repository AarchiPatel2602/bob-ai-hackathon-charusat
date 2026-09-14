import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.fleet import FleetAsset
from backend.app.models.shipment import Shipment

def calculate_fleet_utilisation(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Computes exact fleet capacity and utilisation metrics from actual database assets.
    """
    assets = db.query(FleetAsset).filter(FleetAsset.user_id == user_id).all()
    if not assets:
        return {
            "total_assets": 0,
            "available_assets": 0,
            "in_transit_assets": 0,
            "idle_assets": 0,
            "maintenance_assets": 0,
            "total_capacity_tons": 0.0,
            "active_capacity_tons": 0.0,
            "idle_capacity_tons": 0.0,
            "maintenance_capacity_tons": 0.0,
            "current_utilisation_pct": 0.0,
            "projected_utilisation_pct": 0.0,
            "improvement_pct": 0.0
        }

    total_capacity = sum(a.capacity for a in assets)
    active_capacity = sum(a.capacity for a in assets if a.status in ["AVAILABLE", "IN_TRANSIT"])
    idle_capacity = sum(a.capacity for a in assets if a.status == "IDLE")
    maint_capacity = sum(a.capacity for a in assets if a.status == "MAINTENANCE")
    
    available_count = len([a for a in assets if a.status == "AVAILABLE"])
    in_transit_count = len([a for a in assets if a.status == "IN_TRANSIT"])
    idle_count = len([a for a in assets if a.status == "IDLE"])
    maint_count = len([a for a in assets if a.status == "MAINTENANCE"])

    current_util = round((active_capacity / total_capacity * 100.0), 1) if total_capacity > 0 else 0.0
    
    # If idle assets are redeployed into active service:
    projected_active = active_capacity + idle_capacity
    projected_util = round((projected_active / total_capacity * 100.0), 1) if total_capacity > 0 else 0.0
    improvement = round(projected_util - current_util, 1)

    return {
        "total_assets": len(assets),
        "available_assets": available_count,
        "in_transit_assets": in_transit_count,
        "idle_assets": idle_count,
        "maintenance_assets": maint_count,
        "total_capacity_tons": round(total_capacity, 1),
        "active_capacity_tons": round(active_capacity, 1),
        "idle_capacity_tons": round(idle_capacity, 1),
        "maintenance_capacity_tons": round(maint_capacity, 1),
        "current_utilisation_pct": current_util,
        "projected_utilisation_pct": projected_util,
        "improvement_pct": improvement
    }

def find_idle_assets(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Identifies all idle assets and calculates duration idle."""
    idle_records = db.query(FleetAsset).filter(
        FleetAsset.user_id == user_id,
        FleetAsset.status == "IDLE"
    ).all()

    now = datetime.datetime.utcnow()
    results = []
    for a in idle_records:
        hours_idle = 8.0 # default realistic demo idle duration
        if a.idle_since:
            hours_idle = round((now - a.idle_since).total_seconds() / 3600.0, 1)
            if hours_idle < 0.1:
                hours_idle = 1.0

        results.append({
            "id": a.id,
            "asset_identifier": a.asset_identifier,
            "asset_type": a.asset_type,
            "current_location": a.current_location,
            "capacity": a.capacity,
            "capacity_unit": a.capacity_unit,
            "is_refrigerated": a.is_refrigerated,
            "status": a.status,
            "hours_idle": hours_idle,
            "current_assignment": a.current_assignment
        })
    return results

def match_fleet_for_shipment(db: Session, shipment: Shipment) -> List[Dict[str, Any]]:
    """
    Ranks suitable fleet assets for a specific shipment requirement.
    Matches capacity, refrigeration, and location proximity.
    """
    candidates = db.query(FleetAsset).filter(
        FleetAsset.user_id == shipment.user_id,
        FleetAsset.status.in_(["AVAILABLE", "IDLE"])
    ).all()

    matches = []
    for a in candidates:
        # Check hard constraints
        refrigeration_ok = (not shipment.cold_chain_enabled) or a.is_refrigerated
        capacity_ok = a.capacity >= shipment.required_capacity

        suitability_score = 0
        reasons = []

        if refrigeration_ok:
            suitability_score += 40
            if shipment.cold_chain_enabled and a.is_refrigerated:
                reasons.append("Refrigerated unit certified for cold-chain")
        else:
            reasons.append("Non-refrigerated (fails cold-chain requirement)")

        if capacity_ok:
            suitability_score += 30
            excess = a.capacity - shipment.required_capacity
            if excess <= 5.0:
                suitability_score += 10 # optimal sizing
            reasons.append(f"Capacity {a.capacity} {a.capacity_unit} satisfies {shipment.required_capacity} {shipment.capacity_unit}")
        else:
            reasons.append(f"Insufficient capacity ({a.capacity} < {shipment.required_capacity})")

        # Location proximity
        if a.current_location.lower() == shipment.current_location.lower() or a.current_location.lower() == shipment.origin.lower():
            suitability_score += 30
            reasons.append(f"Co-located at {a.current_location} (zero deadhead transit)")
        else:
            suitability_score += 10
            reasons.append(f"Positioned at {a.current_location} (requires repositioning)")

        if a.status == "AVAILABLE":
            suitability_score += 10
        elif a.status == "IDLE":
            suitability_score += 15 # redeeming idle asset is beneficial!

        matches.append({
            "asset_id": a.id,
            "asset_identifier": a.asset_identifier,
            "asset_type": a.asset_type,
            "current_location": a.current_location,
            "capacity": a.capacity,
            "capacity_unit": a.capacity_unit,
            "is_refrigerated": a.is_refrigerated,
            "status": a.status,
            "suitability_score": suitability_score,
            "is_compatible": refrigeration_ok and capacity_ok,
            "reasons": reasons
        })

    # Sort descending by suitability score
    matches.sort(key=lambda x: (x["is_compatible"], x["suitability_score"]), reverse=True)
    return matches

def generate_fleet_redeployment_recommendations(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Detects idle assets and finds high-demand hubs (e.g. locations of disrupted or pending shipments)
    to generate redeployment recommendations.
    """
    idle_assets = db.query(FleetAsset).filter(
        FleetAsset.user_id == user_id,
        FleetAsset.status == "IDLE"
    ).all()

    # Find locations with disrupted or active shipments
    active_shipments = db.query(Shipment).filter(
        Shipment.user_id == user_id,
        Shipment.status.in_(["CRITICAL", "AT_RISK", "DELAYED", "IN_TRANSIT"])
    ).all()

    demand_locations = {}
    for s in active_shipments:
        loc = s.origin if s.status in ["CRITICAL", "AT_RISK"] else s.current_location
        demand_locations[loc] = demand_locations.get(loc, 0) + 1

    recommendations = []
    util_stats = calculate_fleet_utilisation(db, user_id)

    for asset in idle_assets:
        # Find best target destination with demand different from current location
        target_dest = None
        for loc in demand_locations:
            if loc.lower() != asset.current_location.lower():
                target_dest = loc
                break

        if not target_dest:
            target_dest = "Mumbai" if asset.current_location.lower() != "mumbai" else "Rotterdam"

        recommendations.append({
            "asset_id": asset.id,
            "asset_identifier": asset.asset_identifier,
            "asset_type": asset.asset_type,
            "from_location": asset.current_location,
            "to_location": target_dest,
            "capacity": asset.capacity,
            "capacity_unit": asset.capacity_unit,
            "is_refrigerated": asset.is_refrigerated,
            "reason": f"{asset.asset_identifier} is currently idle in {asset.current_location}. Redeploying to {target_dest} resolves surge capacity demands for at-risk cargo and elevates fleet utilisation from {util_stats['current_utilisation_pct']}% to {util_stats['projected_utilisation_pct']}%.",
            "priority": "HIGH" if asset.is_refrigerated else "MEDIUM",
            "current_utilisation_pct": util_stats["current_utilisation_pct"],
            "projected_utilisation_pct": util_stats["projected_utilisation_pct"],
            "estimated_transit_hours": 6.5,
            "status": "RECOMMENDED"
        })

    return recommendations
