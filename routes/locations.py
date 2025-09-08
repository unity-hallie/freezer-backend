"""
Location management routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

import schemas, crud, models
from auth import get_current_user
from database import get_db
from middleware.auth import verify_location_access

# Create router for location endpoints
router = APIRouter(tags=["locations"])

# Location creation under households
@router.post("/households/{household_id}/locations", response_model=schemas.LocationResponse)
def create_location(
    household_id: int,
    location: schemas.LocationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    household = crud.get_household_by_id(db, household_id)
    if not household or not crud.is_household_member(db, household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Household not found")
    return crud.create_location(db=db, location=location, household_id=household_id)

# Get all locations in a household
@router.get("/households/{household_id}/locations", response_model=list[schemas.LocationResponse])
def get_household_locations(
    household_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not crud.is_household_member(db, household_id, current_user.id):
        raise HTTPException(status_code=404, detail="Household not found")
    return crud.get_household_locations(db, household_id)

# Get all user's locations across households
@router.get("/locations", response_model=list[schemas.LocationResponse])  
def get_user_locations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all locations from user's households"""
    return crud.get_user_locations(db, current_user.id)

# Individual location operations
@router.put("/locations/{location_id}", response_model=schemas.LocationResponse)
def update_location(
    location_id: int,
    location_update: schemas.LocationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_location_access(location_id, current_user, db)
    return crud.update_location(db, location_id, location_update)

@router.delete("/locations/{location_id}")
def delete_location(
    location_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_location_access(location_id, current_user, db)
    crud.delete_location(db, location_id)
    return {"message": "Location deleted successfully"}