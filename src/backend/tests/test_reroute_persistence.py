import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.user import User
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.recommendation import Recommendation
from backend.app.models.alert import Alert
from backend.app.api.shipments import approve_shipment_reroute, get_shipment
from backend.app.api.recommendations import approve_recommendation
from backend.app.api.alerts import resolve_alert

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_engine():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def setup_data(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()

    user = User(
        email="operator@supplyguard.io",
        hashed_password="pw_hash_test_value",
        full_name="Operations Lead",
        role="Dispatcher"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    shipment = Shipment(
        shipment_identifier="SH-PERSIST-101",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai Port",
        carrier="Maersk Line",
        cargo_type="Vaccines",
        cargo_value=620000.0,
        priority="HIGH",
        status="AT_RISK",
        risk_score=91,
        risk_level="CRITICAL",
        cold_chain_enabled=True,
        minimum_temperature=2.0,
        maximum_temperature=8.0
    )
    session.add(shipment)
    session.commit()
    session.refresh(shipment)

    # Original Route: Mumbai -> Dubai -> Rotterdam
    orig_points = [
        ShipmentRoutePoint(shipment_id=shipment.id, sequence_order=1, location_name="Mumbai Port", status="CURRENT"),
        ShipmentRoutePoint(shipment_id=shipment.id, sequence_order=2, location_name="Dubai Port", status="PENDING"),
        ShipmentRoutePoint(shipment_id=shipment.id, sequence_order=3, location_name="Rotterdam Gateway", status="PENDING")
    ]
    for pt in orig_points:
        session.add(pt)

    # Recommendation: Divert via Colombo
    rec = Recommendation(
        shipment_id=shipment.id,
        recommendation_type="REROUTE_SHIPMENT",
        priority="CRITICAL",
        reason="Port strike avoidance",
        affected_entity="SH-PERSIST-101",
        current_state="Route: Mumbai -> Dubai -> Rotterdam (Risk: 91/100)",
        recommended_state="Route: Mumbai Feeder -> Colombo Hub -> Rotterdam (Projected Risk: 24/100)",
        expected_benefit="Saves $620k cargo",
        cost_impact=8400.0,
        time_impact_hours=18.0,
        risk_impact_points=-67,
        status="PENDING"
    )
    session.add(rec)

    # Alert: Port Strike impact
    alert = Alert(
        user_id=user.id,
        shipment_id=shipment.id,
        alert_type="DISRUPTION_IMPACT",
        severity="HIGH",
        title="Shipment Affected: Mumbai Port Strike",
        reason="Exposed to berth stoppage",
        recommended_action="Approve Colombo reroute",
        is_read=False,
        is_resolved=False
    )
    session.add(alert)
    session.commit()

    user_id = user.id
    shipment_id = shipment.id
    rec_id = rec.id
    alert_id = alert.id
    session.close()

    return {
        "engine": db_engine,
        "user_id": user_id,
        "shipment_id": shipment_id,
        "rec_id": rec_id,
        "alert_id": alert_id
    }

# TEST A: Create/find shipment -> Persist original route -> Approve alternative -> Create NEW database session -> Assert active route = alternative route
def test_a_reroute_persistence_in_new_session(setup_data):
    engine = setup_data["engine"]
    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Session 1: Approve alternative route
    session1 = SessionMaker()
    user = session1.query(User).filter(User.id == setup_data["user_id"]).first()
    
    colombo_waypoints = ["Mumbai Feeder", "Colombo Maritime Hub", "Suez Canal Bypass", "Rotterdam Port"]
    approve_shipment_reroute(
        shipment_id=setup_data["shipment_id"],
        payload={"waypoints": colombo_waypoints, "projected_risk_score": 24, "route_name": "Alternative A (Colombo)"},
        db=session1,
        current_user=user
    )
    session1.close()

    # Session 2: NEW database session (simulates fresh browser refresh F5)
    session2 = SessionMaker()
    fresh_shipment = session2.query(Shipment).filter(Shipment.id == setup_data["shipment_id"]).first()
    assert fresh_shipment is not None
    assert len(fresh_shipment.route_points) == 4
    
    route_locations = [pt.location_name for pt in fresh_shipment.route_points]
    assert route_locations == colombo_waypoints, f"Expected {colombo_waypoints}, got {route_locations}"
    assert fresh_shipment.risk_score == 24
    assert fresh_shipment.risk_level == "LOW"
    session2.close()

# TEST B: Approve reroute -> Fetch recommendation from fresh DB session -> Assert status = APPROVED
def test_b_recommendation_status_approved(setup_data):
    engine = setup_data["engine"]
    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Session 1: Call approve_recommendation
    session1 = SessionMaker()
    user = session1.query(User).filter(User.id == setup_data["user_id"]).first()
    approve_recommendation(recommendation_id=setup_data["rec_id"], db=session1, current_user=user)
    session1.close()

    # Session 2: Fresh DB session query
    session2 = SessionMaker()
    fresh_rec = session2.query(Recommendation).filter(Recommendation.id == setup_data["rec_id"]).first()
    assert fresh_rec is not None
    assert fresh_rec.status == "APPROVED"
    assert fresh_rec.approved_at is not None

    # Also check the shipment route points were updated by approving recommendation
    fresh_shipment = session2.query(Shipment).filter(Shipment.id == setup_data["shipment_id"]).first()
    pts = [p.location_name for p in fresh_shipment.route_points]
    assert "Colombo" in pts[1] or "Colombo" in pts[0]
    session2.close()

# TEST C: Refresh shipment through API -> Assert new route still exists
def test_c_get_shipment_api_returns_persisted_route(setup_data):
    engine = setup_data["engine"]
    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session1 = SessionMaker()
    user = session1.query(User).filter(User.id == setup_data["user_id"]).first()
    colombo_waypoints = ["Mumbai Feeder", "Colombo Maritime Hub", "Suez Canal Bypass", "Rotterdam Port"]
    approve_shipment_reroute(
        shipment_id=setup_data["shipment_id"],
        payload={"waypoints": colombo_waypoints, "projected_risk_score": 24},
        db=session1,
        current_user=user
    )
    session1.close()

    # Call get_shipment API endpoint with a fresh session
    session_api = SessionMaker()
    user_api = session_api.query(User).filter(User.id == setup_data["user_id"]).first()
    shipment_out = get_shipment(shipment_id=setup_data["shipment_id"], db=session_api, current_user=user_api)
    
    assert shipment_out.id == setup_data["shipment_id"]
    pts = [pt.location_name for pt in shipment_out.route_points]
    assert pts == colombo_waypoints
    session_api.close()

# TEST D: Resolve alert -> Create new database session -> Assert alert status = RESOLVED and is_read = True
def test_d_alert_resolution_persistence(setup_data):
    engine = setup_data["engine"]
    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Session 1: Resolve alert
    session1 = SessionMaker()
    user = session1.query(User).filter(User.id == setup_data["user_id"]).first()
    resolve_alert(alert_id=setup_data["alert_id"], db=session1, current_user=user)
    session1.close()

    # Session 2: Fresh DB session
    session2 = SessionMaker()
    fresh_alert = session2.query(Alert).filter(Alert.id == setup_data["alert_id"]).first()
    assert fresh_alert is not None
    assert fresh_alert.is_resolved is True
    assert fresh_alert.is_read is True
    assert fresh_alert.resolved_at is not None
    session2.close()
