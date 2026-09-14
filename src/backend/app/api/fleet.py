from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.fleet import FleetAsset
from backend.app.models.recommendation import RedeploymentAction
from backend.app.models.audit import AuditLog
from backend.app.schemas.fleet import (
    FleetAssetCreate,
    FleetAssetUpdate,
    FleetAssetOut,
    FleetUtilisationOut,
    FleetRedeploymentRecommendationOut
)
from backend.app.api.deps import get_current_user
from backend.app.engines.fleet_engine import (
    calculate_fleet_utilisation,
    find_idle_assets,
    generate_fleet_redeployment_recommendations
)

router = APIRouter(prefix="/fleet", tags=["fleet"])

@router.get("", response_model=List[FleetAssetOut])
def list_fleet(
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    refrigerated_only: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(FleetAsset).filter(FleetAsset.user_id == current_user.id)
    if asset_type and asset_type.upper() != "ALL":
        query = query.filter(FleetAsset.asset_type.ilike(f"%{asset_type}%"))
    if status and status.upper() != "ALL":
        query = query.filter(FleetAsset.status == status.upper())
    if location:
        query = query.filter(FleetAsset.current_location.ilike(f"%{location}%"))
    if refrigerated_only:
        query = query.filter(FleetAsset.is_refrigerated == True)
    return query.order_by(FleetAsset.created_at.desc()).all()

@router.post("", response_model=FleetAssetOut)
def create_asset(
    asset_in: FleetAssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.datetime.utcnow()
    idle_time = now if asset_in.status.upper() == "IDLE" else None

    asset = FleetAsset(
        asset_identifier=asset_in.asset_identifier,
        asset_type=asset_in.asset_type,
        current_location=asset_in.current_location,
        capacity=asset_in.capacity,
        capacity_unit=asset_in.capacity_unit,
        is_refrigerated=asset_in.is_refrigerated,
        status=asset_in.status,
        idle_since=idle_time,
        current_assignment=asset_in.current_assignment,
        user_id=current_user.id,
        is_demo=False
    )
    db.add(asset)
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id,
        action="FLEET_ASSET_CREATED",
        entity_type="FLEET_ASSET",
        entity_id=asset.asset_identifier,
        details=f"Added asset {asset.asset_identifier} ({asset.asset_type}, {asset.capacity} {asset.capacity_unit}) at {asset.current_location}"
    ))
    db.commit()
    db.refresh(asset)
    return asset

@router.get("/utilisation", response_model=FleetUtilisationOut)
def get_fleet_utilisation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return calculate_fleet_utilisation(db, current_user.id)

@router.get("/idle")
def get_idle_fleet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return find_idle_assets(db, current_user.id)

@router.get("/recommendations", response_model=List[FleetRedeploymentRecommendationOut])
def get_fleet_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return generate_fleet_redeployment_recommendations(db, current_user.id)

@router.post("/recommendations/{asset_id}/approve")
def approve_redeployment(
    asset_id: int,
    target_destination: Optional[str] = "Mumbai",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(FleetAsset).filter(
        FleetAsset.id == asset_id,
        FleetAsset.user_id == current_user.id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Fleet asset not found")

    prev_loc = asset.current_location
    prev_status = asset.status

    # Update asset state to IN_TRANSIT repositioning
    asset.status = "IN_TRANSIT"
    asset.current_assignment = f"Repositioning to {target_destination}"
    asset.idle_since = None
    asset.updated_at = datetime.datetime.utcnow()

    # Record redeployment action
    action = RedeploymentAction(
        fleet_asset_id=asset.id,
        from_location=prev_loc,
        to_location=target_destination,
        reason=f"Redeployment approved to support surge demand and mitigate supply chain disruption.",
        status="IN_TRANSIT"
    )
    db.add(action)

    # Record Audit Log
    db.add(AuditLog(
        user_id=current_user.id,
        action="FLEET_REDEPLOYMENT_APPROVED",
        entity_type="FLEET_ASSET",
        entity_id=asset.asset_identifier,
        details=f"Approved redeployment of {asset.asset_identifier} from {prev_loc} to {target_destination}."
    ))
    db.commit()

    updated_util = calculate_fleet_utilisation(db, current_user.id)
    return {
        "status": "APPROVED",
        "message": f"Fleet asset {asset.asset_identifier} redeployment from {prev_loc} to {target_destination} approved.",
        "asset": {
            "id": asset.id,
            "identifier": asset.asset_identifier,
            "status": asset.status,
            "assignment": asset.current_assignment
        },
        "fleet_utilisation": updated_util
    }

@router.get("/{asset_id}", response_model=FleetAssetOut)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(FleetAsset).filter(
        FleetAsset.id == asset_id,
        FleetAsset.user_id == current_user.id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Fleet asset not found")
    return asset

@router.put("/{asset_id}", response_model=FleetAssetOut)
def update_asset(
    asset_id: int,
    asset_in: FleetAssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(FleetAsset).filter(
        FleetAsset.id == asset_id,
        FleetAsset.user_id == current_user.id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Fleet asset not found")

    update_data = asset_in.dict(exclude_unset=True)
    if "status" in update_data and update_data["status"].upper() == "IDLE" and asset.status != "IDLE":
        asset.idle_since = datetime.datetime.utcnow()

    for field, val in update_data.items():
        setattr(asset, field, val)

    asset.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(asset)
    return asset

@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset = db.query(FleetAsset).filter(
        FleetAsset.id == asset_id,
        FleetAsset.user_id == current_user.id
    ).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Fleet asset not found")

    ident = asset.asset_identifier
    db.delete(asset)
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id,
        action="FLEET_ASSET_DELETED",
        entity_type="FLEET_ASSET",
        entity_id=ident,
        details=f"Deleted fleet asset {ident}"
    ))
    db.commit()
    return {"status": "success", "message": f"Asset {ident} deleted"}
