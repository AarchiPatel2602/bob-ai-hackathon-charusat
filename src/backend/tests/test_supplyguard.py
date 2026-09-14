import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.user import User
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.disruption import Disruption
from backend.app.models.fleet import FleetAsset
from backend.app.models.carrier import Carrier
from backend.app.models.sensor import SensorReading
from backend.app.models.compliance import ComplianceProfile
from backend.app.models.recommendation import Recommendation
from backend.app.models.alert import Alert

from backend.app.engines.disruption_engine import shipment_is_affected, analyze_disruption_impact
from backend.app.engines.risk_engine import calculate_shipment_risk, get_risk_level
from backend.app.engines.route_engine import generate_alternative_routes
from backend.app.engines.carrier_engine import rank_alternative_carriers, ensure_default_carriers
from backend.app.engines.fleet_engine import (
    calculate_fleet_utilisation,
    find_idle_assets,
    match_fleet_for_shipment,
    generate_fleet_redeployment_recommendations
)
from backend.app.engines.cold_chain_engine import (
    evaluate_temperature_severity,
    analyze_excursion_run,
    calculate_predictive_breach
)
from backend.app.engines.alert_engine import (
    create_or_update_alert,
    trigger_disruption_impact_alert,
    trigger_cold_chain_alert
)

# In-memory SQLite for high-speed, isolated unit tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Create test user
    user = User(
        email="test_manager@supplyguard.io",
        hashed_password="hashed_pw_test",
        full_name="Alex Morgan",
        role="Senior Logistics Director"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

# 1. Shipment Creation Test
def test_shipment_creation(db_session):
    user = db_session.query(User).first()
    shipment = Shipment(
        shipment_identifier="SH-TEST-101",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai Port",
        carrier="Maersk Line",
        cargo_type="Vaccines",
        cargo_value=620000.0,
        priority="HIGH",
        cold_chain_enabled=True,
        minimum_temperature=2.0,
        maximum_temperature=8.0
    )
    db_session.add(shipment)
    db_session.commit()
    db_session.refresh(shipment)

    assert shipment.id is not None
    assert shipment.shipment_identifier == "SH-TEST-101"
    assert shipment.cargo_value == 620000.0
    assert shipment.cold_chain_enabled is True

# 2. Shipment Retrieval Test
def test_shipment_retrieval(db_session):
    user = db_session.query(User).first()
    shipment = Shipment(
        shipment_identifier="SH-RETRIEVE-1",
        user_id=user.id,
        origin="Singapore",
        destination="Hamburg",
        current_location="Singapore Port",
        carrier="CMA CGM",
        cargo_type="Electronics",
        cargo_value=850000.0
    )
    db_session.add(shipment)
    db_session.commit()

    retrieved = db_session.query(Shipment).filter(Shipment.shipment_identifier == "SH-RETRIEVE-1").first()
    assert retrieved is not None
    assert retrieved.origin == "Singapore"
    assert retrieved.destination == "Hamburg"

# 3. Disruption Creation Test
def test_disruption_creation(db_session):
    user = db_session.query(User).first()
    disruption = Disruption(
        name="Mumbai Port Strike",
        type="Port Strike",
        location="Mumbai Port",
        severity="HIGH",
        expected_duration_days=4.0,
        creator_id=user.id,
        status="ACTIVE"
    )
    db_session.add(disruption)
    db_session.commit()
    db_session.refresh(disruption)

    assert disruption.id is not None
    assert disruption.name == "Mumbai Port Strike"
    assert disruption.severity == "HIGH"
    assert disruption.status == "ACTIVE"

# 4. Affected Shipment Detection Test
def test_affected_shipment_detection(db_session):
    user = db_session.query(User).first()
    sh1 = Shipment(
        shipment_identifier="SH-AFFECTED-1",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai Port",
        carrier="Maersk",
        cargo_type="Vaccines",
        cargo_value=600000.0
    )
    sh2 = Shipment(
        shipment_identifier="SH-UNAFFECTED-2",
        user_id=user.id,
        origin="Tokyo",
        destination="Los Angeles",
        current_location="Pacific Lane",
        carrier="MSC",
        cargo_type="Machinery",
        cargo_value=200000.0
    )
    db_session.add_all([sh1, sh2])
    db_session.commit()

    disruption = Disruption(
        name="Mumbai Port Strike",
        type="Port Strike",
        location="Mumbai Port",
        severity="HIGH",
        creator_id=user.id,
        status="ACTIVE"
    )
    db_session.add(disruption)
    db_session.commit()

    affected_shipments, value_at_risk = analyze_disruption_impact(db_session, disruption)
    assert len(affected_shipments) == 1
    assert affected_shipments[0].shipment_identifier == "SH-AFFECTED-1"
    assert value_at_risk == 600000.0

# 5. Risk Calculation Test
def test_risk_calculation(db_session):
    user = db_session.query(User).first()
    shipment = Shipment(
        shipment_identifier="SH-RISK-1",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai Port",
        carrier="Maersk",
        cargo_type="Vaccines",
        cargo_value=620000.0,
        priority="HIGH",
        status="IN_TRANSIT",
        cold_chain_enabled=True,
        minimum_temperature=2.0,
        maximum_temperature=8.0
    )
    db_session.add(shipment)
    db_session.commit()

    # Initial risk with no disruption
    score_initial, level_initial, _ = calculate_shipment_risk(db_session, shipment)
    assert score_initial <= 30
    assert level_initial == "LOW"

    # Add active disruption
    disruption = Disruption(
        name="Mumbai Port Strike",
        type="Port Strike",
        location="Mumbai Port",
        severity="HIGH",
        expected_duration_days=4.0,
        creator_id=user.id,
        status="ACTIVE"
    )
    db_session.add(disruption)
    db_session.commit()

    score_disrupted, level_disrupted, reasons = calculate_shipment_risk(db_session, shipment)
    assert score_disrupted >= 61
    assert level_disrupted in ["HIGH", "CRITICAL"]
    assert any("Mumbai Port Strike" in r for r in reasons)

# 6. Alternative Route Generation Test
def test_route_recommendation(db_session):
    user = db_session.query(User).first()
    shipment = Shipment(
        shipment_identifier="SH-ROUTE-1",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai Port",
        carrier="Maersk Line",
        cargo_type="Vaccines",
        cargo_value=620000.0,
        cold_chain_enabled=True
    )
    routes = generate_alternative_routes(shipment, "Mumbai Port")
    assert len(routes) >= 2
    top_route = routes[0]
    assert "waypoints" in top_route
    assert "additional_cost_usd" in top_route
    assert "additional_time_hours" in top_route
    assert top_route["cold_chain_compatible"] is True

# 7. Carrier Ranking Test
def test_carrier_ranking(db_session):
    user = db_session.query(User).first()
    shipment = Shipment(
        shipment_identifier="SH-CARRIER-1",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai Port",
        carrier="Maersk Line",
        cargo_type="Pharmaceuticals",
        cargo_value=500000.0,
        cold_chain_enabled=True
    )
    ranked = rank_alternative_carriers(db_session, shipment)
    assert len(ranked) >= 2
    # Ensure badges are assigned
    tags = [c["tag"] for c in ranked if c["tag"]]
    assert "BEST OVERALL" in tags

# 8. Fleet Matching Test
def test_fleet_matching(db_session):
    user = db_session.query(User).first()
    # TRUCK-204: Mumbai, 12 tons, Refrigerated, Available
    # TRUCK-450: Mumbai, 15 tons, Not refrigerated
    t1 = FleetAsset(asset_identifier="TRUCK-204", asset_type="Truck", current_location="Mumbai", capacity=12.0, capacity_unit="tons", is_refrigerated=True, status="AVAILABLE", user_id=user.id)
    t2 = FleetAsset(asset_identifier="TRUCK-450", asset_type="Truck", current_location="Mumbai", capacity=15.0, capacity_unit="tons", is_refrigerated=False, status="AVAILABLE", user_id=user.id)
    db_session.add_all([t1, t2])
    db_session.commit()

    shipment = Shipment(
        shipment_identifier="SH-FLEET-1",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai",
        carrier="Maersk",
        cargo_type="Vaccines",
        cargo_value=620000.0,
        cold_chain_enabled=True,
        required_capacity=10.0,
        required_fleet_type="Truck"
    )
    matches = match_fleet_for_shipment(db_session, shipment)
    assert len(matches) == 2
    top_match = matches[0]
    assert top_match["asset_identifier"] == "TRUCK-204"
    assert top_match["is_compatible"] is True

# 9. Idle Fleet Detection Test
def test_idle_fleet_detection(db_session):
    user = db_session.query(User).first()
    t_idle = FleetAsset(asset_identifier="TRUCK-205", asset_type="Truck", current_location="Ahmedabad", capacity=10.0, capacity_unit="tons", is_refrigerated=True, status="IDLE", user_id=user.id)
    t_active = FleetAsset(asset_identifier="TRUCK-206", asset_type="Truck", current_location="Mumbai", capacity=10.0, capacity_unit="tons", is_refrigerated=True, status="AVAILABLE", user_id=user.id)
    db_session.add_all([t_idle, t_active])
    db_session.commit()

    idle_list = find_idle_assets(db_session, user.id)
    assert len(idle_list) == 1
    assert idle_list[0]["asset_identifier"] == "TRUCK-205"

    recs = generate_fleet_redeployment_recommendations(db_session, user.id)
    assert len(recs) >= 1
    assert recs[0]["asset_identifier"] == "TRUCK-205"

# 10. Cold-Chain Excursion Detection Test
def test_cold_chain_excursion_detection(db_session):
    res_normal = evaluate_temperature_severity(4.5, 2.0, 8.0)
    assert res_normal["is_excursion"] is False
    assert res_normal["severity"] == "NORMAL"

    res_excursion = evaluate_temperature_severity(10.2, 2.0, 8.0)
    assert res_excursion["is_excursion"] is True
    assert res_excursion["severity"] == "CRITICAL"

# 11. Severity Classification Test
def test_severity_classification():
    # Bounds: 2.0 to 8.0
    # Normal
    assert evaluate_temperature_severity(5.0, 2.0, 8.0)["severity"] == "NORMAL"
    # Borderline Warning
    assert evaluate_temperature_severity(7.8, 2.0, 8.0)["severity"] == "WARNING"
    # Major (1.0 to 1.9 above max)
    assert evaluate_temperature_severity(9.2, 2.0, 8.0)["severity"] == "MAJOR"
    # Critical (>= 2.0 above max)
    assert evaluate_temperature_severity(10.2, 2.0, 8.0)["severity"] == "CRITICAL"

# 12. Alert Creation Test
def test_alert_creation(db_session):
    user = db_session.query(User).first()
    alert = create_or_update_alert(
        db=db_session,
        user_id=user.id,
        alert_type="COLD_CHAIN_EXCURSION",
        severity="CRITICAL",
        title="CRITICAL COLD-CHAIN EXCURSION",
        reason="Peak temperature 10.2°C exceeds 8.0°C maximum limit.",
        recommended_action="Quarantine shipment upon arrival."
    )
    assert alert.id is not None
    assert alert.severity == "CRITICAL"
    assert alert.is_resolved is False

# 13. Recommendation Creation Test
def test_recommendation_creation(db_session):
    user = db_session.query(User).first()
    shipment = Shipment(
        shipment_identifier="SH-REC-1",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai",
        carrier="Maersk",
        cargo_type="Vaccines",
        cargo_value=620000.0
    )
    db_session.add(shipment)
    db_session.commit()

    rec = Recommendation(
        shipment_id=shipment.id,
        recommendation_type="REROUTE_SHIPMENT",
        priority="CRITICAL",
        reason="Mumbai Port Strike blocking standard maritime corridor",
        affected_entity="SH-REC-1",
        current_state="Mumbai -> Dubai -> Rotterdam",
        recommended_state="Mumbai -> Colombo -> Rotterdam",
        expected_benefit="Bypasses strike, reduces risk from 91 to 24",
        cost_impact=8400.0,
        time_impact_hours=18.0,
        risk_impact_points=-67,
        status="PENDING"
    )
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)

    assert rec.id is not None
    assert rec.status == "PENDING"
    assert rec.risk_impact_points == -67
