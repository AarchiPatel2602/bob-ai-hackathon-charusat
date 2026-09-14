import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.user import User
from backend.app.models.shipment import Shipment
from backend.app.models.disruption import Disruption
from backend.app.models.fleet import FleetAsset
from backend.app.models.sensor import SensorReading
from backend.app.engines.ai_service import answer_supply_chain_query

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    user = User(
        email="demo@routewise.io",
        hashed_password="hashed_password",
        full_name="Ayush Vyas",
        role="Lead Logistics Director"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Add sample shipments
    s1 = Shipment(
        shipment_identifier="SH-1024",
        user_id=user.id,
        origin="Mumbai",
        destination="Rotterdam",
        current_location="Mumbai Port",
        carrier="Maersk Line",
        cargo_type="Vaccines",
        cargo_value=620000.0,
        priority="HIGH",
        status="IN_TRANSIT",
        cold_chain_enabled=True,
        minimum_temperature=2.0,
        maximum_temperature=8.0,
        risk_score=95,
        risk_level="CRITICAL"
    )
    s2 = Shipment(
        shipment_identifier="SH-1025",
        user_id=user.id,
        origin="Singapore",
        destination="Hamburg",
        current_location="Singapore Port",
        carrier="CMA CGM",
        cargo_type="Electronics",
        cargo_value=120000.0,
        priority="MEDIUM",
        status="IN_TRANSIT",
        cold_chain_enabled=False,
        risk_score=20,
        risk_level="LOW"
    )
    session.add_all([s1, s2])
    session.commit()

    # Add disruption
    d1 = Disruption(
        name="Mumbai Port Strike",
        type="PORT_STRIKE",
        location="Mumbai Port",
        severity="HIGH",
        expected_duration_days=4,
        status="ACTIVE",
        creator_id=user.id
    )
    session.add(d1)
    session.commit()

    # Add idle fleet
    f1 = FleetAsset(
        asset_identifier="TRUCK-205",
        asset_type="Truck",
        current_location="Ahmedabad",
        capacity=10.0,
        capacity_unit="tons",
        status="IDLE",
        is_refrigerated=True,
        idle_since=datetime.datetime.utcnow() - datetime.timedelta(hours=8),
        user_id=user.id
    )
    session.add(f1)
    session.commit()

    # Add sensor readings for SH-1024 showing thermal excursion
    sr1 = SensorReading(
        shipment_id=s1.id,
        temperature=8.4,
        humidity=65.0,
        battery_level=92.0,
        is_excursion=True,
        severity="CRITICAL"
    )
    session.add(sr1)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_chat_at_risk_query(db_session):
    user = db_session.query(User).first()
    res = await answer_supply_chain_query("Which shipments are currently at risk?", db_session, user)
    assert res is not None
    assert "answer" in res
    assert "SH-1024" in res["answer"]
    assert res["severity"] == "HIGH"
    assert len(res["suggested_queries"]) > 0

@pytest.mark.asyncio
async def test_chat_urgent_query(db_session):
    user = db_session.query(User).first()
    res = await answer_supply_chain_query("Which shipment is most urgent?", db_session, user)
    assert "SH-1024" in res["answer"]
    assert res["severity"] == "CRITICAL"
    assert "Vaccines" in res["finding"]

@pytest.mark.asyncio
async def test_chat_why_at_risk_query(db_session):
    user = db_session.query(User).first()
    res = await answer_supply_chain_query("Why is shipment SH-1024 at risk?", db_session, user)
    assert "SH-1024" in res["answer"]
    assert "Mumbai Port Strike" in res["evidence"]
    assert "recommendation" in res or "recommended_action" in res

@pytest.mark.asyncio
async def test_chat_cold_chain_query(db_session):
    user = db_session.query(User).first()
    res = await answer_supply_chain_query("Which cold-chain shipment has exceeded its temperature range?", db_session, user)
    assert "SH-1024" in res["answer"]
    assert "Thermal" in res["answer"] or "Cold-Chain" in res["answer"]

@pytest.mark.asyncio
async def test_chat_fleet_idle_query(db_session):
    user = db_session.query(User).first()
    res = await answer_supply_chain_query("Which fleet assets are currently idle?", db_session, user)
    assert "TRUCK-205" in res["answer"]
    assert "Ahmedabad" in res["answer"]

@pytest.mark.asyncio
async def test_chat_summary_query(db_session):
    user = db_session.query(User).first()
    res = await answer_supply_chain_query("Summarize today's supply-chain risks.", db_session, user)
    assert "Global Operations Briefing" in res["answer"] or "RouteWise AI" in res["answer"]
