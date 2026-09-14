import sys
import os

# Ensure backend package in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.user import User
from backend.app.api.deps import get_password_hash
from backend.app.engines.demo_scenario import seed_demo_data

def main():
    print("[INIT] Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if demo user exists
        demo_user = db.query(User).filter(User.email == "demo@supplyguard.io").first()
        if not demo_user:
            print("[USER] Creating demo user: demo@supplyguard.io / SupplyGuard2026!")
            demo_user = User(
                email="demo@supplyguard.io",
                hashed_password=get_password_hash("SupplyGuard2026!"),
                full_name="Sarah Chen",
                role="Director of Global Logistics",
                organization="SupplyGuard Global Operations"
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

        print("[SEED] Seeding 50+ shipments, fleet assets, and disruptions...")
        res = seed_demo_data(db, demo_user)
        print(f"[DONE] Seeding complete: {res}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
