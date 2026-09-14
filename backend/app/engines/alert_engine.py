import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.alert import Alert
from backend.app.models.shipment import Shipment
from backend.app.models.disruption import Disruption
from backend.app.models.fleet import FleetAsset

def create_or_update_alert(
    db: Session,
    user_id: int,
    alert_type: str,
    severity: str,
    title: str,
    reason: str,
    recommended_action: str,
    shipment_id: Optional[int] = None,
    disruption_id: Optional[int] = None,
    fleet_asset_id: Optional[int] = None
) -> Alert:
    """
    Creates an alert or updates existing active alert to avoid redundant duplicates.
    """
    query = db.query(Alert).filter(
        Alert.user_id == user_id,
        Alert.alert_type == alert_type,
        Alert.is_resolved == False
    )

    if shipment_id:
        query = query.filter(Alert.shipment_id == shipment_id)
    if disruption_id:
        query = query.filter(Alert.disruption_id == disruption_id)
    if fleet_asset_id:
        query = query.filter(Alert.fleet_asset_id == fleet_asset_id)

    existing = query.first()
    if existing:
        existing.severity = severity
        existing.title = title
        existing.reason = reason
        existing.recommended_action = recommended_action
        existing.is_read = False
        existing.created_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    new_alert = Alert(
        user_id=user_id,
        shipment_id=shipment_id,
        disruption_id=disruption_id,
        fleet_asset_id=fleet_asset_id,
        severity=severity,
        alert_type=alert_type,
        title=title,
        reason=reason,
        recommended_action=recommended_action,
        is_read=False,
        is_resolved=False
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert

def trigger_disruption_impact_alert(db: Session, disruption: Disruption, shipment: Shipment) -> Alert:
    """Generates an impact alert when a disruption hits a shipment."""
    return create_or_update_alert(
        db=db,
        user_id=shipment.user_id,
        alert_type="DISRUPTION_IMPACT",
        severity=disruption.severity,
        title=f"Shipment Affected: {disruption.name}",
        reason=f"Shipment {shipment.shipment_identifier} ({shipment.cargo_type}, value: ${shipment.cargo_value:,.2f}) is exposed to {disruption.name} at {disruption.location}.",
        recommended_action="Review alternative route and carrier recommendations. Consider rerouting or fleet redeployment.",
        shipment_id=shipment.id,
        disruption_id=disruption.id
    )

def trigger_cold_chain_alert(
    db: Session,
    shipment: Shipment,
    current_temp: float,
    peak_temp: float,
    duration_minutes: float,
    severity: str
) -> Alert:
    """Generates cold-chain excursion alert."""
    title = f"{severity} Cold-Chain Excursion" if severity == "CRITICAL" else f"Cold-Chain Temperature {severity}"
    return create_or_update_alert(
        db=db,
        user_id=shipment.user_id,
        alert_type="COLD_CHAIN_EXCURSION" if severity in ["CRITICAL", "MAJOR"] else "COLD_CHAIN_WARNING",
        severity=severity,
        title=title,
        reason=f"Shipment {shipment.shipment_identifier}: Temperature reached {current_temp:.1f}°C (Peak: {peak_temp:.1f}°C) over {duration_minutes:.0f} minutes outside allowed bounds [{shipment.minimum_temperature}°C - {shipment.maximum_temperature}°C].",
        recommended_action="Quarantine shipment upon arrival / initiate cold-chain quality audit according to configured compliance profile.",
        shipment_id=shipment.id
    )

def trigger_idle_fleet_alert(db: Session, user_id: int, asset: FleetAsset, target_hub: str) -> Alert:
    """Generates alert for idle fleet redeployment opportunity."""
    return create_or_update_alert(
        db=db,
        user_id=user_id,
        alert_type="FLEET_IDLE",
        severity="MEDIUM",
        title=f"Idle Fleet Asset: {asset.asset_identifier}",
        reason=f"{asset.asset_identifier} ({asset.asset_type}, {asset.capacity} {asset.capacity_unit}) is idle in {asset.current_location}. Surge demand detected in {target_hub}.",
        recommended_action=f"Approve redeployment of {asset.asset_identifier} from {asset.current_location} to {target_hub} to optimize utilization.",
        fleet_asset_id=asset.id
    )
