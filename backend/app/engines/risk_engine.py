from typing import Tuple, List
from sqlalchemy.orm import Session
from backend.app.models.shipment import Shipment
from backend.app.models.disruption import Disruption
from backend.app.models.sensor import SensorReading
from backend.app.engines.disruption_engine import shipment_is_affected

def get_risk_level(score: int) -> str:
    """Normalize score (0-100) to standard operational risk bands."""
    if score >= 81:
        return "CRITICAL"
    elif score >= 61:
        return "HIGH"
    elif score >= 31:
        return "MEDIUM"
    else:
        return "LOW"

def calculate_shipment_risk(db: Session, shipment: Shipment) -> Tuple[int, str, List[str]]:
    """
    Deterministic risk calculation engine.
    Returns (risk_score, risk_level, reasons_list).
    """
    score = 0
    reasons = []

    # 1. Evaluate Disruption Exposure
    active_disruptions = db.query(Disruption).filter(
        Disruption.status == "ACTIVE",
        Disruption.creator_id == shipment.user_id
    ).all()

    max_disruption_severity_score = 0
    hit_disruptions = []

    for d in active_disruptions:
        affected, reason_text = shipment_is_affected(shipment, d)
        if affected:
            hit_disruptions.append(d)
            sev = d.severity.upper()
            d_score = 0
            if sev == "CRITICAL":
                d_score = 45
            elif sev == "HIGH":
                d_score = 35
            elif sev == "MEDIUM":
                d_score = 22
            else: # LOW
                d_score = 12
            
            if d.expected_duration_days >= 3.0:
                d_score += 5

            if d_score > max_disruption_severity_score:
                max_disruption_severity_score = d_score
            reasons.append(f"Exposed to active disruption: {d.name} ({d.severity} at {d.location}) - {reason_text}")

    score += max_disruption_severity_score

    # 2. Cargo Value Exposure (scaled higher if exposed to disruption)
    if hit_disruptions:
        if shipment.cargo_value >= 500000:
            score += 18
            reasons.append(f"High-value cargo (${shipment.cargo_value:,.2f}) exposed to operational disruption")
        elif shipment.cargo_value >= 100000:
            score += 12
            reasons.append(f"Significant cargo value (${shipment.cargo_value:,.2f}) at risk")
        elif shipment.cargo_value >= 25000:
            score += 6
        else:
            score += 2
    else:
        if shipment.cargo_value >= 500000:
            score += 5
        elif shipment.cargo_value >= 100000:
            score += 3
        else:
            score += 1

    # 3. Priority Weighting
    priority = (shipment.priority or "MEDIUM").upper()
    if priority == "CRITICAL":
        score += 8
        reasons.append("Shipment designated as CRITICAL priority")
    elif priority == "HIGH":
        score += 5
        reasons.append("Shipment designated as HIGH priority")
    elif priority == "MEDIUM":
        score += 2
    else:
        score += 0

    # 4. Status & Delay Indicator
    status = (shipment.status or "IN_TRANSIT").upper()
    if status == "DELAYED":
        score += 12
        reasons.append("Shipment is actively delayed behind expected schedule")
    elif status == "AT_RISK" or hit_disruptions:
        score += 6
    elif status == "IN_TRANSIT":
        score += 2

    # 5. Cold-Chain Sensitivity & Sensor Telemetry
    if shipment.cold_chain_enabled:
        score += 3 # baseline sensitivity
        
        # Check latest sensor readings for temperature excursions
        latest_reading = db.query(SensorReading).filter(
            SensorReading.shipment_id == shipment.id
        ).order_by(SensorReading.timestamp.desc()).first()

        if latest_reading and latest_reading.is_excursion:
            ex_sev = (latest_reading.severity or "WARNING").upper()
            if ex_sev == "CRITICAL":
                score += 27
                reasons.append(
                    f"CRITICAL cold-chain excursion: Current {latest_reading.temperature:.1f}°C breaches limit "
                    f"[{shipment.minimum_temperature}°C - {shipment.maximum_temperature}°C]"
                )
            elif ex_sev == "MAJOR":
                score += 18
                reasons.append(
                    f"MAJOR cold-chain excursion: Current {latest_reading.temperature:.1f}°C outside limit "
                    f"[{shipment.minimum_temperature}°C - {shipment.maximum_temperature}°C]"
                )
            elif ex_sev == "WARNING":
                score += 10
                reasons.append(
                    f"Cold-chain temperature warning: Current {latest_reading.temperature:.1f}°C near/breaching limit "
                    f"[{shipment.minimum_temperature}°C - {shipment.maximum_temperature}°C]"
                )

    # Bound score within [0, 100]
    score = max(0, min(100, score))
    level = get_risk_level(score)

    # Sync back into shipment entity
    shipment.risk_score = score
    shipment.risk_level = level
    shipment.risk_reasons = "\n".join(reasons) if reasons else "No active risk factors identified."
    
    # Auto-adjust shipment status if risk is elevated
    if score >= 81 and shipment.status not in ["DELIVERED", "CRITICAL"]:
        shipment.status = "CRITICAL"
    elif score >= 61 and shipment.status not in ["DELIVERED", "CRITICAL", "AT_RISK"]:
        shipment.status = "AT_RISK"
    elif score < 61 and shipment.status in ["CRITICAL", "AT_RISK"] and not hit_disruptions:
        shipment.status = "IN_TRANSIT"

    db.commit()
    return score, level, reasons
