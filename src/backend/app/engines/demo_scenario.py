import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.fleet import FleetAsset
from backend.app.models.disruption import Disruption
from backend.app.models.carrier import Carrier
from backend.app.models.sensor import SensorReading
from backend.app.models.compliance import ComplianceProfile
from backend.app.models.recommendation import Recommendation, RedeploymentAction
from backend.app.models.alert import Alert
from backend.app.models.audit import AuditLog
from backend.app.engines.carrier_engine import ensure_default_carriers
from backend.app.engines.disruption_engine import analyze_disruption_impact
from backend.app.engines.risk_engine import calculate_shipment_risk
from backend.app.engines.cold_chain_engine import evaluate_temperature_severity
from backend.app.engines.alert_engine import (
    trigger_disruption_impact_alert,
    trigger_cold_chain_alert,
    trigger_idle_fleet_alert
)

def ensure_compliance_profiles(db: Session):
    """Ensure standard compliance profiles exist."""
    if db.query(ComplianceProfile).count() == 0:
        profiles = [
            ComplianceProfile(
                name="Demo Compliance Rules (Pharma)",
                cargo_type="Pharmaceuticals",
                min_temp=2.0,
                max_temp=8.0,
                warning_tolerance_minutes=15,
                major_tolerance_minutes=30,
                critical_temp_delta=2.0,
                regulatory_source="Demo Standard (Simulated WHO Annex 9)"
            ),
            ComplianceProfile(
                name="Deep Frozen Bio-Specimens",
                cargo_type="Vaccines",
                min_temp=-25.0,
                max_temp=-15.0,
                warning_tolerance_minutes=10,
                major_tolerance_minutes=20,
                critical_temp_delta=3.0,
                regulatory_source="Ultra-Cold Chain Protocol"
            ),
            ComplianceProfile(
                name="Perishable Food Freshness",
                cargo_type="Food",
                min_temp=0.0,
                max_temp=4.0,
                warning_tolerance_minutes=20,
                major_tolerance_minutes=45,
                critical_temp_delta=2.5,
                regulatory_source="Cold Storage Standard"
            )
        ]
        for p in profiles:
            db.add(p)
        db.commit()

def seed_demo_data(db: Session, user: User) -> Dict[str, int]:
    """
    Seeds 50+ realistic shipments, 15+ fleet assets, disruptions, and carrier relationships.
    """
    ensure_default_carriers(db)
    ensure_compliance_profiles(db)

    # Check if demo data already seeded for this user
    existing_count = db.query(Shipment).filter(Shipment.user_id == user.id, Shipment.is_demo == True).count()
    if existing_count >= 50:
        return {"shipments": existing_count, "fleet": db.query(FleetAsset).filter(FleetAsset.user_id == user.id).count()}

    now = datetime.datetime.utcnow()

    # 1. CORE HACKATHON HERO SHIPMENT: SH-1024
    sh_hero = Shipment(
        shipment_identifier="SH-1024",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai Port",
        carrier="Maersk Line",
        cargo_type="Vaccines",
        cargo_description="Pediatric mRNA & Lyophilized Vaccines (Temperature Critical)",
        cargo_value=620000.0,
        currency="USD",
        priority="HIGH",
        status="IN_TRANSIT",
        expected_departure=now - datetime.timedelta(days=1),
        expected_delivery=now + datetime.timedelta(days=7),
        cold_chain_enabled=True,
        minimum_temperature=2.0,
        maximum_temperature=8.0,
        required_fleet_type="Truck",
        required_capacity=10.0,
        capacity_unit="tons",
        is_demo=True
    )
    db.add(sh_hero)
    db.flush()

    # Hero Route Points: Mumbai -> Dubai -> Rotterdam
    route_points_hero = [
        ShipmentRoutePoint(shipment_id=sh_hero.id, sequence_order=1, location_name="Mumbai Port", status="CURRENT"),
        ShipmentRoutePoint(shipment_id=sh_hero.id, sequence_order=2, location_name="Dubai Port", status="PENDING"),
        ShipmentRoutePoint(shipment_id=sh_hero.id, sequence_order=3, location_name="Rotterdam Gateway", status="PENDING")
    ]
    for pt in route_points_hero:
        db.add(pt)

    # Hero initial normal sensor reading (4.5°C)
    initial_reading = SensorReading(
        shipment_id=sh_hero.id,
        temperature=4.5,
        humidity=52.0,
        battery_level=98.0,
        is_excursion=False,
        severity="NORMAL",
        timestamp=now - datetime.timedelta(minutes=30)
    )
    db.add(initial_reading)

    # 2. SEED ADDITIONAL REALISTIC SHIPMENTS (TOTAL > 50)
    shipment_templates = [
        ("SH-1001", "Singapore", "Hamburg", "Singapore Port", "CMA CGM Group", "Electronics", "Semiconductor Microchips", 850000.0, "CRITICAL", "IN_TRANSIT", False, None, None, "Container", 22.0),
        ("SH-1002", "Tokyo", "Los Angeles", "Pacific Lane 4", "MSC Mediterranean", "Machinery", "Robotic Assembly Units", 420000.0, "HIGH", "IN_TRANSIT", False, None, None, "Vessel", 45.0),
        ("SH-1003", "Antwerp", "New York", "Atlantic Hub", "Hapag-Lloyd", "Pharmaceuticals", "Monoclonal Antibodies", 730000.0, "CRITICAL", "IN_TRANSIT", True, 2.0, 8.0, "Container", 8.0),
        ("SH-1004", "Shanghai", "Rotterdam", "Malacca Strait", "Maersk Line", "Electronics", "Smartphone Lithium Assemblies", 980000.0, "HIGH", "IN_TRANSIT", False, None, None, "Container", 30.0),
        ("SH-1005", "Mumbai", "London", "Mumbai Sea Hub", "DHL Global Forwarding", "Textiles", "Premium Organic Cotton Garments", 85000.0, "MEDIUM", "IN_TRANSIT", False, None, None, "Truck", 14.0),
        ("SH-1006", "Dubai", "Chicago", "Midwest Express", "Kuehne + Nagel", "General Cargo", "Precision Industrial Valves", 115000.0, "LOW", "IN_TRANSIT", False, None, None, "Truck", 12.0),
        ("SH-1007", "Rotterdam", "Genoa", "Alps Transit", "MSC Mediterranean", "Chemicals", "Catalytic Polymers", 210000.0, "MEDIUM", "IN_TRANSIT", False, None, None, "Truck", 18.0),
        ("SH-1008", "Bergen", "Paris", "North Sea Lane", "Maersk Line", "Seafood", "Fresh Atlantic Salmon Fillets", 145000.0, "HIGH", "IN_TRANSIT", True, 0.0, 4.0, "Truck", 9.0),
        ("SH-1009", "Santos", "Rotterdam", "South Atlantic", "CMA CGM Group", "Food", "Specialty Arabica Coffee Beans", 190000.0, "LOW", "IN_TRANSIT", False, None, None, "Container", 25.0),
        ("SH-1010", "Busan", "Seattle", "North Pacific", "Hapag-Lloyd", "Electronics", "OLED Display Panels", 550000.0, "HIGH", "IN_TRANSIT", False, None, None, "Container", 16.0),
        ("SH-1011", "Mumbai", "Antwerp", "Nhava Sheva", "MSC Mediterranean", "Pharmaceuticals", "Active Pharmaceutical Ingredients", 340000.0, "HIGH", "IN_TRANSIT", True, 2.0, 8.0, "Truck", 10.0),
        ("SH-1012", "Frankfurt", "Tokyo", "Frankfurt CargoCity", "DHL Global Forwarding", "Pharmaceuticals", "Enzyme Solutions", 480000.0, "CRITICAL", "IN_TRANSIT", True, 2.0, 8.0, "Truck", 5.0),
        ("SH-1013", "Melbourne", "Singapore", "Timor Sea", "Maersk Line", "Food", "Chilled Grass-Fed Beef", 165000.0, "MEDIUM", "IN_TRANSIT", True, 0.0, 4.0, "Container", 15.0),
        ("SH-1014", "Shenzhen", "Dubai", "Indian Ocean Lane", "CMA CGM Group", "Electronics", "Enterprise Network Routers", 390000.0, "MEDIUM", "IN_TRANSIT", False, None, None, "Container", 18.0),
        ("SH-1015", "Mumbai", "Jeddah", "Mumbai Port Gate 3", "Maersk Line", "Food", "Processed Dairy and Butter", 95000.0, "MEDIUM", "IN_TRANSIT", True, 2.0, 8.0, "Truck", 11.0)
    ]

    # Generate 38 more realistic shipments programmatically to exceed 50+ total
    corridors = [
        ("Yokohama", "Rotterdam", "CMA CGM Group", "Machinery", 280000.0, False),
        ("Taipei", "Amsterdam", "DHL Global Forwarding", "Electronics", 620000.0, False),
        ("Munich", "Shanghai", "Hapag-Lloyd", "Automotive Parts", 310000.0, False),
        ("Basel", "Boston", "Kuehne + Nagel", "Pharmaceuticals", 890000.0, True),
        ("Sydney", "Tokyo", "Maersk Line", "Seafood", 175000.0, True),
        ("Bangkok", "Los Angeles", "MSC Mediterranean", "Food", 120000.0, False),
        ("Chennai", "Rotterdam", "Maersk Line", "Textiles", 95000.0, False),
        ("Dublin", "New York", "DHL Global Forwarding", "Pharmaceuticals", 740000.0, True),
        ("Helsinki", "Barcelona", "Hapag-Lloyd", "General Cargo", 65000.0, False),
        ("Kolkata", "Dubai", "MSC Mediterranean", "Machinery", 135000.0, False),
        ("Chicago", "Dallas", "Kuehne + Nagel", "Food", 82000.0, True),
        ("Toronto", "Vancouver", "Maersk Line", "Chemicals", 195000.0, False)
    ]

    seq_id = 2001
    for t in shipment_templates:
        sh = Shipment(
            shipment_identifier=t[0],
            user_id=user.id,
            origin=t[1],
            destination=t[2],
            current_location=t[3],
            carrier=t[4],
            cargo_type=t[5],
            cargo_description=t[6],
            cargo_value=t[7],
            priority=t[8],
            status=t[9],
            expected_departure=now - datetime.timedelta(days=2),
            expected_delivery=now + datetime.timedelta(days=5),
            cold_chain_enabled=t[10],
            minimum_temperature=t[11],
            maximum_temperature=t[12],
            required_fleet_type=t[13],
            required_capacity=t[14],
            capacity_unit="tons",
            is_demo=True
        )
        db.add(sh)

    for i in range(37):
        corr = corridors[i % len(corridors)]
        is_cc = corr[5]
        sh = Shipment(
            shipment_identifier=f"SH-{seq_id}",
            user_id=user.id,
            origin=corr[0],
            destination=corr[1],
            current_location=f"{corr[0]} Hub",
            carrier=corr[2],
            cargo_type=corr[3],
            cargo_description=f"Standard Commercial Batch {seq_id}",
            cargo_value=corr[4] + (i * 12500.0),
            priority="HIGH" if (i % 3 == 0) else "MEDIUM",
            status="IN_TRANSIT" if (i % 4 != 0) else "PLANNED",
            expected_departure=now - datetime.timedelta(days=1),
            expected_delivery=now + datetime.timedelta(days=6 + (i % 4)),
            cold_chain_enabled=is_cc,
            minimum_temperature=2.0 if is_cc else None,
            maximum_temperature=8.0 if is_cc else None,
            required_fleet_type="Truck" if (i % 2 == 0) else "Container",
            required_capacity=10.0 + (i % 15),
            capacity_unit="tons",
            is_demo=True
        )
        db.add(sh)
        seq_id += 1

    db.flush()

    # 3. SEED FLEET ASSETS (16 TOTAL, INCLUDING HERO ASSETS)
    # Required Hero Assets:
    # TRUCK-205: Ahmedabad, 10 tons, Refrigerated, Idle (8 hours)
    # TRUCK-204: Mumbai, 12 tons, Refrigerated, Available
    # TRUCK-310: Ahmedabad, 10 tons, Refrigerated, Available
    # TRUCK-450: Mumbai, 15 tons, Not refrigerated, Available
    fleet_records = [
        FleetAsset(asset_identifier="TRUCK-205", asset_type="Truck", current_location="Ahmedabad", capacity=10.0, capacity_unit="tons", is_refrigerated=True, status="IDLE", idle_since=now - datetime.timedelta(hours=8), user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-204", asset_type="Truck", current_location="Mumbai", capacity=12.0, capacity_unit="tons", is_refrigerated=True, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-310", asset_type="Truck", current_location="Ahmedabad", capacity=10.0, capacity_unit="tons", is_refrigerated=True, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-450", asset_type="Truck", current_location="Mumbai", capacity=15.0, capacity_unit="tons", is_refrigerated=False, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-101", asset_type="Truck", current_location="Rotterdam", capacity=14.0, capacity_unit="tons", is_refrigerated=True, status="IN_TRANSIT", current_assignment="SH-1004", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-102", asset_type="Truck", current_location="Hamburg", capacity=16.0, capacity_unit="tons", is_refrigerated=False, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="CONT-501", asset_type="Container", current_location="Singapore", capacity=24.0, capacity_unit="tons", is_refrigerated=True, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="CONT-502", asset_type="Container", current_location="Shanghai", capacity=28.0, capacity_unit="tons", is_refrigerated=False, status="IN_TRANSIT", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-808", asset_type="Truck", current_location="Dubai", capacity=12.0, capacity_unit="tons", is_refrigerated=True, status="IDLE", idle_since=now - datetime.timedelta(hours=14), user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="VESSEL-301", asset_type="Vessel", current_location="Antwerp", capacity=120.0, capacity_unit="tons", is_refrigerated=True, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-912", asset_type="Truck", current_location="Chicago", capacity=15.0, capacity_unit="tons", is_refrigerated=True, status="MAINTENANCE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="CONT-602", asset_type="Container", current_location="Tokyo", capacity=20.0, capacity_unit="tons", is_refrigerated=True, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-711", asset_type="Truck", current_location="Paris", capacity=8.0, capacity_unit="tons", is_refrigerated=True, status="IN_TRANSIT", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-304", asset_type="Truck", current_location="New York", capacity=18.0, capacity_unit="tons", is_refrigerated=False, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="VESSEL-402", asset_type="Vessel", current_location="Los Angeles", capacity=95.0, capacity_unit="tons", is_refrigerated=False, status="AVAILABLE", user_id=user.id, is_demo=True),
        FleetAsset(asset_identifier="TRUCK-605", asset_type="Truck", current_location="Singapore", capacity=10.0, capacity_unit="tons", is_refrigerated=True, status="IDLE", idle_since=now - datetime.timedelta(hours=6), user_id=user.id, is_demo=True)
    ]
    for f in fleet_records:
        db.add(f)

    # 4. SEED DISRUPTIONS (INCLUDING HERO MUMBAI PORT STRIKE)
    disruptions = [
        Disruption(
            name="Mumbai Port Strike",
            type="Port Strike",
            location="Mumbai Port",
            severity="HIGH",
            start_time=now - datetime.timedelta(hours=12),
            expected_duration_days=4.0,
            description="Dockworkers and crane operators commenced wildcat strike over wage renegotiations. Berth operations halted.",
            status="ACTIVE",
            creator_id=user.id,
            is_demo=True
        ),
        Disruption(
            name="Typhoon Malakas",
            type="Storm",
            location="South China Sea",
            severity="CRITICAL",
            start_time=now - datetime.timedelta(hours=24),
            expected_duration_days=3.0,
            description="Category 4 tropical cyclone causing sea swell heights over 9 meters. Vessel re-routing mandated.",
            status="ACTIVE",
            creator_id=user.id,
            is_demo=True
        ),
        Disruption(
            name="Suez Canal Bottleneck",
            type="Severe Weather",
            location="Suez Canal",
            severity="MEDIUM",
            start_time=now - datetime.timedelta(days=1),
            expected_duration_days=2.0,
            description="High desert crosswinds causing temporary maritime convoy spacing slowdowns.",
            status="ACTIVE",
            creator_id=user.id,
            is_demo=True
        )
    ]
    for d in disruptions:
        db.add(d)

    db.commit()

    # Initial risk calculations across seeded shipments
    all_shipments = db.query(Shipment).filter(Shipment.user_id == user.id).all()
    for s in all_shipments:
        calculate_shipment_risk(db, s)

    # Correlate initial disruptions
    for d in disruptions:
        analyze_disruption_impact(db, d)

    return {"shipments": len(all_shipments), "fleet": len(fleet_records), "disruptions": len(disruptions)}

def run_hackathon_demo_flow(db: Session, user: User) -> Dict[str, Any]:
    """
    Executes the complete 12-step end-to-end Hackathon demo scenario programmatically.
    Ensures SH-1024, TRUCK-205, and Mumbai Port Strike are in exact state and triggers:
    Disruption -> Impact -> Risk -> Alternatives -> Fleet -> Cold-Chain Excursion -> Alert -> AI Summary.
    """
    # 1. Ensure baseline data exists
    seed_demo_data(db, user)

    # 2. Retrieve hero shipment SH-1024
    hero_shipment = db.query(Shipment).filter(
        Shipment.user_id == user.id,
        Shipment.shipment_identifier == "SH-1024"
    ).first()

    # 3. Retrieve or activate Mumbai Port Strike
    port_strike = db.query(Disruption).filter(
        Disruption.creator_id == user.id,
        Disruption.name == "Mumbai Port Strike"
    ).first()
    if port_strike:
        port_strike.status = "ACTIVE"
        port_strike.severity = "HIGH"
        db.commit()
    
    # 4. Impact Analysis
    affected_shipments, value_at_risk = analyze_disruption_impact(db, port_strike)
    
    # 5. Calculate elevated risk for affected shipments
    calculate_shipment_risk(db, hero_shipment)
    
    # Trigger disruption alert for SH-1024
    d_alert = trigger_disruption_impact_alert(db, port_strike, hero_shipment)

    # 6. Fleet identification and redeployment recommendation
    truck_205 = db.query(FleetAsset).filter(
        FleetAsset.user_id == user.id,
        FleetAsset.asset_identifier == "TRUCK-205"
    ).first()
    if truck_205:
        truck_205.status = "IDLE"
        truck_205.idle_since = datetime.datetime.utcnow() - datetime.timedelta(hours=8)
        db.commit()
        trigger_idle_fleet_alert(db, user.id, truck_205, "Mumbai")

    # 7. Simulate Cold-Chain Excursion sequence: 4.2°C -> 5.1°C -> 7.8°C -> 8.4°C -> 9.1°C -> 9.7°C -> 10.2°C
    telemetry_sequence = [4.2, 5.1, 7.8, 8.4, 9.1, 9.7, 10.2]
    now = datetime.datetime.utcnow()
    
    # Clear older simulation points for hero shipment to give clean chart
    db.query(SensorReading).filter(SensorReading.shipment_id == hero_shipment.id).delete()
    db.commit()

    created_readings = []
    for idx, temp in enumerate(telemetry_sequence):
        t_stamp = now - datetime.timedelta(minutes=(len(telemetry_sequence) - 1 - idx) * 3)
        eval_res = evaluate_temperature_severity(temp, hero_shipment.minimum_temperature, hero_shipment.maximum_temperature)
        reading = SensorReading(
            shipment_id=hero_shipment.id,
            temperature=temp,
            humidity=55.0 + (idx * 1.5),
            battery_level=97.0 - (idx * 0.5),
            location_name=hero_shipment.current_location,
            is_excursion=eval_res["is_excursion"],
            severity=eval_res["severity"],
            timestamp=t_stamp
        )
        db.add(reading)
        created_readings.append(reading)
    db.commit()

    # 8. Re-evaluate Risk for SH-1024 with both Port Strike AND Excursion (Reaches 91 - 95 CRITICAL)
    score, level, reasons = calculate_shipment_risk(db, hero_shipment)

    # 9. Trigger Critical Cold-Chain Excursion Alert
    cc_alert = trigger_cold_chain_alert(
        db=db,
        shipment=hero_shipment,
        current_temp=10.2,
        peak_temp=10.2,
        duration_minutes=18.0,
        severity="CRITICAL"
    )

    # 10. Store Recommendations
    existing_rec = db.query(Recommendation).filter(
        Recommendation.shipment_id == hero_shipment.id,
        Recommendation.recommendation_type == "REROUTE_SHIPMENT"
    ).first()
    if not existing_rec:
        rec = Recommendation(
            shipment_id=hero_shipment.id,
            recommendation_type="REROUTE_SHIPMENT",
            priority="CRITICAL",
            reason="Exposed to active Mumbai Port Strike + Critical Cold-Chain Excursion (10.2°C). Rerouting via Colombo bypasses port gridlock.",
            affected_entity="SH-1024",
            current_state="Route: Mumbai -> Dubai -> Rotterdam (Risk: 91/100)",
            recommended_state="Route: Mumbai Feeder -> Colombo Hub -> Rotterdam (Projected Risk: 24/100)",
            expected_benefit="Bypasses 4-day strike, recovers cold-chain control, avoids $620,000 cargo loss.",
            cost_impact=8400.0,
            time_impact_hours=18.0,
            risk_impact_points=-67,
            status="PENDING"
        )
        db.add(rec)
        db.commit()

    # 11. Audit Log
    db.add(AuditLog(
        user_id=user.id,
        action="DEMO_SCENARIO_EXECUTED",
        entity_type="SYSTEM",
        entity_id="HACKATHON_DEMO",
        details="Executed end-to-end demo flow: Port Strike -> Affected Shipments -> Risk Spike -> Excursion Detection -> Colombo Reroute & Fleet Redeployment."
    ))
    db.commit()

    return {
        "scenario": "L2 Supply Chain Disruption & Fleet Optimizer Hackathon Scenario",
        "affected_shipment": {
            "identifier": hero_shipment.shipment_identifier,
            "cargo": hero_shipment.cargo_type,
            "value_usd": hero_shipment.cargo_value,
            "initial_risk": 15,
            "post_disruption_risk": 68,
            "final_excursion_risk": hero_shipment.risk_score,
            "risk_level": hero_shipment.risk_level,
            "reasons": reasons
        },
        "disruption": {
            "name": port_strike.name,
            "location": port_strike.location,
            "severity": port_strike.severity,
            "affected_count": len(affected_shipments),
            "cargo_value_at_risk": value_at_risk
        },
        "telemetry_simulated": telemetry_sequence,
        "peak_temperature": 10.2,
        "cold_chain_severity": "CRITICAL",
        "alerts_generated": [d_alert.title, cc_alert.title],
        "fleet_redeployment": {
            "asset": "TRUCK-205",
            "from": "Ahmedabad",
            "to": "Mumbai",
            "refrigerated": True
        },
        "recommended_route": "Alternative A (Transshipment via Colombo) - Risk 24 (+18h, +$8,400)",
        "status": "COMPLETED_SUCCESSFULLY"
    }
