import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.user import User
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.disruption import Disruption
from backend.app.models.fleet import FleetAsset
from backend.app.api.shipments import get_shipment_map_data, approve_shipment_reroute
from backend.app.api.dashboard import get_dashboard_map_data
from backend.app.engines.location_service import geocode_location

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_setup():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    user = User(
        email="map_user@supplyguard.io",
        hashed_password="pw_hash_sample",
        full_name="Map Controller",
        role="Control Tower Lead"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # 1. Hero shipment
    sh1 = Shipment(
        shipment_identifier="SH-1024",
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
    session.add(sh1)
    session.commit()
    session.refresh(sh1)

    pts = [
        ShipmentRoutePoint(shipment_id=sh1.id, sequence_order=1, location_name="Mumbai Port", status="CURRENT"),
        ShipmentRoutePoint(shipment_id=sh1.id, sequence_order=2, location_name="Dubai Port", status="PENDING"),
        ShipmentRoutePoint(shipment_id=sh1.id, sequence_order=3, location_name="Rotterdam Gateway", status="PENDING")
    ]
    for p in pts:
        session.add(p)

    # 2. Shipment with unusual/unknown coordinates
    sh2 = Shipment(
        shipment_identifier="SH-UNKNOWN-99",
        user_id=user.id,
        origin="Remote Valley Depot",
        destination="Frontier Distribution Center",
        current_location="Remote Sector 7",
        carrier="Local Express",
        cargo_type="Dry Goods",
        cargo_value=15000.0,
        priority="LOW",
        status="IN_TRANSIT",
        risk_score=10,
        risk_level="LOW"
    )
    session.add(sh2)

    # 3. Disruption: Mumbai Port Strike
    disruption = Disruption(
        name="Mumbai Port Strike",
        type="Port Strike",
        location="Mumbai Port",
        severity="HIGH",
        expected_duration_days=4.0,
        description="Berth operations stopped",
        status="ACTIVE",
        creator_id=user.id
    )
    session.add(disruption)

    # 4. Fleet Assets: TRUCK-205 (Idle in Ahmedabad), TRUCK-204 (Available in Mumbai)
    f1 = FleetAsset(
        asset_identifier="TRUCK-205",
        asset_type="Truck",
        current_location="Ahmedabad",
        capacity=10.0,
        capacity_unit="tons",
        is_refrigerated=True,
        status="IDLE",
        user_id=user.id
    )
    f2 = FleetAsset(
        asset_identifier="TRUCK-204",
        asset_type="Truck",
        current_location="Mumbai",
        capacity=12.0,
        capacity_unit="tons",
        is_refrigerated=True,
        status="AVAILABLE",
        user_id=user.id
    )
    session.add(f1)
    session.add(f2)
    session.commit()

    user_id = user.id
    sh1_id = sh1.id
    sh2_id = sh2.id

    session.close()

    yield {
        "engine": engine,
        "user_id": user_id,
        "sh1_id": sh1_id,
        "sh2_id": sh2_id
    }

    Base.metadata.drop_all(bind=engine)

# 1. Shipment with coordinates returns map data
def test_map_data_with_coordinates(test_setup):
    Session = sessionmaker(bind=test_setup["engine"])
    db = Session()
    user = db.query(User).filter(User.id == test_setup["user_id"]).first()

    data = get_shipment_map_data(shipment_id=test_setup["sh1_id"], db=db, current_user=user)
    assert data["shipment_id"] == test_setup["sh1_id"]
    assert data["origin"]["name"] == "Mumbai"
    assert data["origin"]["latitude"] > 0
    assert data["origin"]["longitude"] > 0
    assert data["destination"]["name"] == "Rotterdam"
    assert data["current_location"]["name"] == "Mumbai Port"
    assert "active_route" in data
    assert len(data["active_route"]["points"]) == 3
    db.close()

# 2. Shipment with missing / custom coordinates does not crash
def test_map_data_unknown_coordinates_no_crash(test_setup):
    Session = sessionmaker(bind=test_setup["engine"])
    db = Session()
    user = db.query(User).filter(User.id == test_setup["user_id"]).first()

    data = get_shipment_map_data(shipment_id=test_setup["sh2_id"], db=db, current_user=user)
    assert data["shipment_id"] == test_setup["sh2_id"]
    assert "origin" in data
    assert "destination" in data
    assert isinstance(data["origin"]["latitude"], float)
    assert isinstance(data["destination"]["longitude"], float)
    db.close()

# 3. Multi-stop route returns all stops with sequence and stop types
def test_multi_stop_route_returns_all_stops(test_setup):
    Session = sessionmaker(bind=test_setup["engine"])
    db = Session()
    user = db.query(User).filter(User.id == test_setup["user_id"]).first()

    data = get_shipment_map_data(shipment_id=test_setup["sh1_id"], db=db, current_user=user)
    stops = data["active_route"]["points"]
    assert len(stops) == 3
    assert stops[0]["stop_type"] == "ORIGIN"
    assert stops[1]["stop_type"] == "TRANSIT STOP"
    assert stops[2]["stop_type"] == "DESTINATION"
    assert stops[1]["location_name"] == "Dubai Port"
    db.close()

# 4. Alternative route returns its route points
def test_alternative_routes_return_stops_and_coords(test_setup):
    Session = sessionmaker(bind=test_setup["engine"])
    db = Session()
    user = db.query(User).filter(User.id == test_setup["user_id"]).first()

    data = get_shipment_map_data(shipment_id=test_setup["sh1_id"], db=db, current_user=user)
    alts = data["alternative_routes"]
    assert len(alts) >= 2
    top_alt = alts[0]
    assert "stops" in top_alt
    assert len(top_alt["stops"]) >= 3
    assert "coordinates" in top_alt
    assert len(top_alt["coordinates"]) == len(top_alt["stops"])
    db.close()

# 5. Approved route becomes active route
def test_approved_route_becomes_active_route(test_setup):
    Session = sessionmaker(bind=test_setup["engine"])
    db = Session()
    user = db.query(User).filter(User.id == test_setup["user_id"]).first()

    colombo_waypoints = ["Mumbai Feeder", "Colombo Maritime Hub", "Suez Canal Bypass", "Rotterdam Port"]
    approve_shipment_reroute(
        shipment_id=test_setup["sh1_id"],
        payload={"waypoints": colombo_waypoints, "projected_risk_score": 24},
        db=db,
        current_user=user
    )

    data = get_shipment_map_data(shipment_id=test_setup["sh1_id"], db=db, current_user=user)
    active_points = data["active_route"]["points"]
    assert len(active_points) == 4
    assert [p["location_name"] for p in active_points] == colombo_waypoints
    assert active_points[1]["location_name"] == "Colombo Maritime Hub"
    assert active_points[1]["stop_type"] == "TRANSIT STOP"
    db.close()

# 6. Disruption information is included where relevant
def test_disruption_included_in_map_data(test_setup):
    Session = sessionmaker(bind=test_setup["engine"])
    db = Session()
    user = db.query(User).filter(User.id == test_setup["user_id"]).first()

    data = get_shipment_map_data(shipment_id=test_setup["sh1_id"], db=db, current_user=user)
    disruptions = data["disruptions"]
    assert len(disruptions) >= 1
    mumbai_strike = next((d for d in disruptions if "Mumbai" in d["name"]), None)
    assert mumbai_strike is not None
    assert mumbai_strike["is_intersecting"] is True
    assert mumbai_strike["severity"] == "HIGH"
    db.close()

# 7. Fleet map data returns valid assets and marks recommended redeployments
def test_fleet_map_data(test_setup):
    Session = sessionmaker(bind=test_setup["engine"])
    db = Session()
    user = db.query(User).filter(User.id == test_setup["user_id"]).first()

    data = get_shipment_map_data(shipment_id=test_setup["sh1_id"], db=db, current_user=user)
    fleet = data["fleet_assets"]
    assert len(fleet) == 2
    truck_205 = next((f for f in fleet if f["asset_identifier"] == "TRUCK-205"), None)
    assert truck_205 is not None
    assert truck_205["is_recommended_redeployment"] is True
    assert truck_205["current_location"] == "Ahmedabad"

    # Dashboard map endpoint
    dash_map = get_dashboard_map_data(db=db, current_user=user)
    assert "shipments" in dash_map
    assert "disruptions" in dash_map
    assert "fleet_assets" in dash_map
    assert len(dash_map["shipments"]) >= 2
    assert len(dash_map["disruptions"]) >= 1
    assert len(dash_map["fleet_assets"]) >= 2
    db.close()
