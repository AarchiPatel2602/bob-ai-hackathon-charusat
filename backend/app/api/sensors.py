from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import datetime

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.shipment import Shipment
from backend.app.models.sensor import SensorReading
from backend.app.models.compliance import ComplianceProfile
from backend.app.models.audit import AuditLog
from backend.app.schemas.sensor import (
    SensorReadingCreate,
    SensorReadingOut,
    SensorSimulationRequest,
    ColdChainStatusOut
)
from backend.app.api.deps import get_current_user
from backend.app.engines.cold_chain_engine import (
    evaluate_temperature_severity,
    analyze_excursion_run,
    calculate_predictive_breach
)
from backend.app.engines.risk_engine import calculate_shipment_risk
from backend.app.engines.alert_engine import trigger_cold_chain_alert

router = APIRouter(tags=["sensors"])

@router.get("/shipments/{shipment_id}/sensors", response_model=List[SensorReadingOut])
def get_sensor_readings(
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

    return db.query(SensorReading).filter(
        SensorReading.shipment_id == shipment.id
    ).order_by(SensorReading.timestamp.desc()).limit(50).all()

@router.post("/shipments/{shipment_id}/sensors", response_model=SensorReadingOut)
def record_sensor_reading(
    shipment_id: int,
    reading_in: SensorReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    min_t = shipment.minimum_temperature if shipment.minimum_temperature is not None else 2.0
    max_t = shipment.maximum_temperature if shipment.maximum_temperature is not None else 8.0

    eval_result = evaluate_temperature_severity(reading_in.temperature, min_t, max_t)

    reading = SensorReading(
        shipment_id=shipment.id,
        temperature=reading_in.temperature,
        humidity=reading_in.humidity,
        battery_level=reading_in.battery_level,
        location_name=reading_in.location_name or shipment.current_location,
        is_excursion=eval_result["is_excursion"],
        severity=eval_result["severity"],
        timestamp=reading_in.timestamp or datetime.datetime.utcnow()
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Recalculate risk
    calculate_shipment_risk(db, shipment)

    # If excursion detected, trigger alert
    if eval_result["is_excursion"]:
        all_readings = db.query(SensorReading).filter(
            SensorReading.shipment_id == shipment.id
        ).all()
        analytics = analyze_excursion_run(all_readings, min_t, max_t)
        trigger_cold_chain_alert(
            db=db,
            shipment=shipment,
            current_temp=reading.temperature,
            peak_temp=analytics["peak_temperature"] or reading.temperature,
            duration_minutes=analytics["duration_minutes"],
            severity=eval_result["severity"]
        )

    return reading

@router.post("/shipments/{shipment_id}/sensors/simulate")
def simulate_sensor_telemetry(
    shipment_id: int,
    sim_req: SensorSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.user_id == current_user.id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    min_t = shipment.minimum_temperature if shipment.minimum_temperature is not None else 2.0
    max_t = shipment.maximum_temperature if shipment.maximum_temperature is not None else 8.0

    mode = sim_req.mode.lower()
    if mode == "warning":
        temperatures = [6.8, 7.3, 7.8, 8.2]
    elif mode == "critical":
        temperatures = [7.8, 8.4, 9.1, 9.7, 10.2]
    else: # normal
        temperatures = [4.2, 4.4, 4.8, 4.5]

    if sim_req.custom_temperature is not None:
        temperatures = [sim_req.custom_temperature]

    now = datetime.datetime.utcnow()
    created = []

    for idx, temp in enumerate(temperatures):
        t_stamp = now - datetime.timedelta(minutes=(len(temperatures) - 1 - idx) * 3)
        eval_result = evaluate_temperature_severity(temp, min_t, max_t)
        reading = SensorReading(
            shipment_id=shipment.id,
            temperature=temp,
            humidity=52.0 + idx,
            battery_level=96.0 - (idx * 0.2),
            location_name=shipment.current_location,
            is_excursion=eval_result["is_excursion"],
            severity=eval_result["severity"],
            timestamp=t_stamp
        )
        db.add(reading)
        created.append(reading)

    db.commit()

    # Recalculate risk
    new_risk_score, new_risk_level, reasons = calculate_shipment_risk(db, shipment)

    # Check excursion analytics & trigger alert if excursion occurred
    all_readings = db.query(SensorReading).filter(
        SensorReading.shipment_id == shipment.id
    ).all()
    analytics = analyze_excursion_run(all_readings, min_t, max_t)

    alert_info = None
    if analytics["has_active_excursion"]:
        alert = trigger_cold_chain_alert(
            db=db,
            shipment=shipment,
            current_temp=temperatures[-1],
            peak_temp=analytics["peak_temperature"] or temperatures[-1],
            duration_minutes=analytics["duration_minutes"],
            severity=analytics["severity"]
        )
        alert_info = {"id": alert.id, "title": alert.title, "severity": alert.severity}

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="SENSOR_SIMULATION_TRIGGERED",
        entity_type="SHIPMENT",
        entity_id=shipment.shipment_identifier,
        details=f"Simulated {mode} IoT telemetry sequence: {temperatures}. Excursion: {analytics['has_active_excursion']}."
    ))
    db.commit()

    return {
        "status": "SIMULATION_APPLIED",
        "mode": mode,
        "readings_count": len(created),
        "latest_temperature": temperatures[-1],
        "has_active_excursion": analytics["has_active_excursion"],
        "excursion_severity": analytics["severity"],
        "duration_minutes": analytics["duration_minutes"],
        "peak_temperature": analytics["peak_temperature"],
        "updated_risk_score": new_risk_score,
        "updated_risk_level": new_risk_level,
        "alert_generated": alert_info
    }

@router.get("/shipments/{shipment_id}/cold-chain-status", response_model=ColdChainStatusOut)
def get_cold_chain_status(
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

    min_t = shipment.minimum_temperature if shipment.minimum_temperature is not None else 2.0
    max_t = shipment.maximum_temperature if shipment.maximum_temperature is not None else 8.0

    readings = db.query(SensorReading).filter(
        SensorReading.shipment_id == shipment.id
    ).order_by(SensorReading.timestamp.asc()).all()

    analytics = analyze_excursion_run(readings, min_t, max_t)
    predictive = calculate_predictive_breach(readings, min_t, max_t)

    latest_reading = readings[-1] if readings else None
    recent_out = [SensorReadingOut.from_orm(r) for r in readings[-15:]]

    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.cargo_type == shipment.cargo_type
    ).first()
    profile_name = profile.name if profile else "Demo Compliance Rules"

    return {
        "shipment_id": shipment.id,
        "shipment_identifier": shipment.shipment_identifier,
        "cold_chain_enabled": shipment.cold_chain_enabled,
        "minimum_temperature": min_t,
        "maximum_temperature": max_t,
        "current_temperature": latest_reading.temperature if latest_reading else None,
        "current_humidity": latest_reading.humidity if latest_reading else None,
        "has_active_excursion": analytics["has_active_excursion"],
        "excursion_severity": analytics["severity"],
        "duration_minutes": analytics["duration_minutes"],
        "peak_temperature": analytics["peak_temperature"],
        "predictive_analysis": predictive,
        "compliance_profile_name": profile_name,
        "recent_readings": recent_out
    }
