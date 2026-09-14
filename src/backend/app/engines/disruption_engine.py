from typing import List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.disruption import Disruption

def is_location_match(disruption_location: str, target_location: str) -> bool:
    """Check if disruption location intersects target location (case-insensitive fuzzy substring)."""
    if not disruption_location or not target_location:
        return False
    d_loc = disruption_location.lower().strip()
    t_loc = target_location.lower().strip()
    
    # Direct containment
    if d_loc in t_loc or t_loc in d_loc:
        return True
        
    # Split into key tokens (e.g. "Mumbai Port" -> "mumbai", "port")
    d_tokens = set(d_loc.replace(",", " ").replace("-", " ").split())
    t_tokens = set(t_loc.replace(",", " ").replace("-", " ").split())
    
    # Common geographic keywords that signify match
    significant_tokens = (d_tokens & t_tokens) - {"port", "terminal", "station", "junction", "city", "sea", "canal", "road"}
    return len(significant_tokens) > 0

def shipment_is_affected(shipment: Shipment, disruption: Disruption) -> Tuple[bool, str]:
    """
    Determine if a shipment is affected by a disruption.
    Returns (is_affected, reason).
    """
    if disruption.status != "ACTIVE":
        return False, ""

    # Carrier failure check
    if disruption.type == "Carrier Failure":
        if disruption.location.lower() in shipment.carrier.lower() or shipment.carrier.lower() in disruption.location.lower():
            return True, f"Carrier failure affecting assigned carrier {shipment.carrier}"

    # Origin match
    if is_location_match(disruption.location, shipment.origin):
        return True, f"Disruption at shipment origin: {shipment.origin}"

    # Destination match
    if is_location_match(disruption.location, shipment.destination):
        return True, f"Disruption at shipment destination: {shipment.destination}"

    # Current location match
    if is_location_match(disruption.location, shipment.current_location):
        return True, f"Disruption at current transit location: {shipment.current_location}"

    # Route points match
    for pt in shipment.route_points:
        if is_location_match(disruption.location, pt.location_name):
            return True, f"Disruption along route waypoint: {pt.location_name}"

    return False, ""

def analyze_disruption_impact(db: Session, disruption: Disruption) -> Tuple[List[Shipment], float]:
    """
    Find all shipments affected by a disruption, update disruption stats, and return affected shipments and total cargo value at risk.
    """
    user_shipments = db.query(Shipment).filter(Shipment.user_id == disruption.creator_id).all()
    affected_shipments = []
    total_value_at_risk = 0.0

    for shipment in user_shipments:
        affected, reason = shipment_is_affected(shipment, disruption)
        if affected:
            affected_shipments.append(shipment)
            total_value_at_risk += shipment.cargo_value

    disruption.affected_shipments_count = len(affected_shipments)
    disruption.cargo_value_at_risk = round(total_value_at_risk, 2)
    db.commit()

    return affected_shipments, total_value_at_risk
