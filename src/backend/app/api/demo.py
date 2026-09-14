from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user
from backend.app.engines.demo_scenario import seed_demo_data, run_hackathon_demo_flow

router = APIRouter(prefix="/demo", tags=["demo"])

@router.post("/seed")
def seed_dataset(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = seed_demo_data(db, current_user)
    return {
        "status": "SEEDED",
        "message": "Demo scenario operational data successfully verified and seeded.",
        "counts": result
    }

@router.post("/run")
def trigger_hackathon_demo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    summary = run_hackathon_demo_flow(db, current_user)
    return summary
